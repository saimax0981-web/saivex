import os
import json
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, url_for, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth

try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth
except Exception:
    firebase_admin = None
    credentials = None
    firebase_auth = None


from ai import ask_ai
from image_gen import generate_image
from file_reader import read_pdf, read_docx, read_txt

from productivity.agent_router import detect_productivity_intent, extract_after_colon
from productivity.ppt_generator import create_ppt
from productivity.pdf_generator import create_pdf
from productivity.website_generator import create_website
from productivity.code_executor import execute_python_code
from productivity.internet_search import search_internet
from productivity.file_generator import create_docx

from vision.vision_service import analyze_image_with_ai, answer_question_about_latest_image

from brain.router import route_message, is_smart_brain_request, brain_intro
from brain.memory_manager import extract_memory

from services.multi_model import ask_multi_model
from services.agent_engine import SaivexAgent
from services.payment_service import create_razorpay_order, verify_razorpay_signature, RAZORPAY_KEY_ID, PLANS
from voice.voice_engine import clean_for_speech, detect_voice_language, voice_personality_prompt
from core.brain2 import analyze as brain2_analyze, plan_text as brain2_plan_text, suggestions_text as brain2_suggestions_text, build_context_prompt


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SAIVEX_SECRET_KEY", "saivex-secret-key-change-later")
database_url = os.environ.get("DATABASE_URL", "sqlite:///saivex_stage3.db")


app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["IMAGE_UPLOAD_FOLDER"] = "static/generated/uploads"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

if os.environ.get("PRODUCTION") or os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

oauth = OAuth(app)

google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

if google_client_id and google_client_secret:
    oauth.register(
        name="google",
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"}
    )



# ======================
# FIREBASE PHONE AUTH SETUP
# ======================

firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID", "")
firebase_api_key = os.environ.get("FIREBASE_API_KEY", "")
firebase_auth_domain = os.environ.get("FIREBASE_AUTH_DOMAIN", "")
firebase_app_id = os.environ.get("FIREBASE_APP_ID", "")
firebase_messaging_sender_id = os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "")
firebase_storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET", "")

def init_firebase_admin():
    if firebase_admin is None:
        return False

    if firebase_admin._apps:
        return True

    service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")

    try:
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            return True

        firebase_admin.initialize_app()
        return True

    except Exception as error:
        print("Firebase Admin not initialized:", error)
        return False


def get_firebase_web_config():
    return {
        "apiKey": firebase_api_key,
        "authDomain": firebase_auth_domain,
        "projectId": firebase_project_id,
        "storageBucket": firebase_storage_bucket,
        "messagingSenderId": firebase_messaging_sender_id,
        "appId": firebase_app_id
    }


def phone_login_allowed_without_admin():
    return os.environ.get("SAIVEX_ALLOW_UNVERIFIED_PHONE", "1") == "1"



# ======================
# PLAN + PREMIUM HELPERS
# ======================

FREE_FEATURES = [
    "Unlimited AI chat",
    "Unlimited image generation",
    "Unlimited PPT generation",
    "Unlimited PDF generation",
    "Unlimited website generation",
    "Kalinga UI",
    "Agent mode",
    "Web search",
    "File upload"
]

PREMIUM_FEATURES = [
    "Everything in Free",
    "Code execution",
    "Voice conversations",
    "Wake mode",
    "Camera vision"
]


def current_subscription():
    if not current_user or not current_user.is_authenticated:
        return None

    sub = Subscription.query.filter_by(user_id=current_user.id, status="active").order_by(Subscription.id.desc()).first()

    if sub and sub.expires_at and sub.expires_at < datetime.utcnow():
        sub.status = "expired"
        db.session.commit()
        return None

    return sub


def is_premium_user():
    admin_email = os.environ.get("SAIVEX_ADMIN_EMAIL", "").lower().strip()
    if current_user and current_user.is_authenticated and admin_email and current_user.email.lower() == admin_email:
        return True

    sub = current_subscription()
    return sub is not None and sub.plan in ["premium_monthly", "premium_yearly", "premium"]


def premium_required_message(feature_name):
    return f"🔒 {feature_name} is available in SAIVEX Premium. Free plan includes unlimited chat, image/PPT/PDF/website generation, Kalinga UI, agent, web search, and file upload. Premium adds code, voice, wake, and camera."


# ======================
# DATABASE MODELS
# ======================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    is_email_verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False, default="New Chat")
    icon = db.Column(db.String(10), nullable=False, default="💬")
    folder = db.Column(db.String(50), nullable=False, default="General")
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False)
    sender = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, default="")
    file_url = db.Column(db.Text, default="")
    preview_url = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=False)


class UploadedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)


class UploadedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    analysis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    theme = db.Column(db.String(50), default="kalinga")
    voice_enabled = db.Column(db.Boolean, default=True)
    image_style = db.Column(db.String(50), default="cinematic")


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    plan = db.Column(db.String(50), default="free")
    status = db.Column(db.String(30), default="active")
    razorpay_order_id = db.Column(db.String(150), default="")
    razorpay_payment_id = db.Column(db.String(150), default="")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ======================
# PHASE 14 AUTH HELPERS
# ======================

def get_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def generate_token(email, purpose):
    serializer = get_serializer()
    return serializer.dumps(email, salt=purpose)


def verify_token(token, purpose, max_age=3600):
    serializer = get_serializer()
    try:
        return serializer.loads(token, salt=purpose, max_age=max_age)
    except Exception:
        return None


def safe_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def public_base_url():
    return os.environ.get("SAIVEX_PUBLIC_URL", "http://127.0.0.1:5000").rstrip("/")


def print_email_link(title, email, link):
    print("\n" + "=" * 60)
    print(title)
    print("To:", email)
    print("Link:", link)
    print("=" * 60 + "\n")




# ======================
# HELPERS
# ======================

def make_title(text):
    words = text.strip().replace("\n", " ").split()
    return " ".join(words[:6]).title()[:55] if words else "New Chat"


def classify_conversation(text):
    q = text.lower()
    if any(w in q for w in ["image", "photo", "picture", "vision", "upload image", "camera"]):
        return "👁️", "Vision"
    if any(w in q for w in ["agent", "task", "autonomous"]):
        return "🤖", "Agent"
    if any(w in q for w in ["voice", "speak", "talk"]):
        return "🎙️", "Voice"
    if any(w in q for w in ["ppt", "powerpoint", "presentation", "slides"]):
        return "📊", "Productivity"
    if any(w in q for w in ["website", "html", "css", "javascript", "portfolio"]):
        return "🌐", "Websites"
    if any(w in q for w in ["search", "internet", "latest", "news", "current"]):
        return "🔎", "Search"
    if any(w in q for w in ["code", "python", "error", "flask"]):
        return "💻", "Coding"
    if any(w in q for w in ["kalinga", "kharavela", "king", "empire", "history"]):
        return "👑", "Kalinga"
    if any(w in q for w in ["pdf", "document", "file", "docx"]):
        return "📄", "Documents"
    if any(w in q for w in ["generate", "logo", "wallpaper", "poster", "design"]):
        return "🎨", "Creative"
    return "💬", "General"


def get_or_create_conversation(conversation_id, first_message):
    conversation = get_conversation(conversation_id) if conversation_id else None
    if not conversation:
        conversation = create_conversation(first_message)
    if conversation.title == "New Chat":
        icon, folder = classify_conversation(first_message)
        conversation.title = make_title(first_message)
        conversation.icon = icon
        conversation.folder = folder
        db.session.commit()
    return conversation


def get_user_memories():
    memories = Memory.query.filter_by(user_id=current_user.id).all()
    return "\n".join([f"{m.key}: {m.value}" for m in memories])


def get_user_documents():
    text = ""
    documents = UploadedDocument.query.filter_by(user_id=current_user.id).all()
    for document in documents:
        text += f"\nDocument: {document.filename}\n{document.content[:4000]}\n"
    return text


def latest_image_analysis():
    image = UploadedImage.query.filter_by(user_id=current_user.id).order_by(UploadedImage.id.desc()).first()
    return image.analysis if image else ""


def save_memory(value):
    key = f"memory_{Memory.query.filter_by(user_id=current_user.id).count() + 1}"
    db.session.add(Memory(user_id=current_user.id, key=key, value=value))
    db.session.commit()


def create_conversation(first_message="New Chat"):
    icon, folder = classify_conversation(first_message)
    conversation = Conversation(
        user_id=current_user.id,
        title=make_title(first_message),
        icon=icon,
        folder=folder
    )
    db.session.add(conversation)
    db.session.commit()
    return conversation


def get_conversation(conversation_id):
    return Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()


def save_chat(conversation_id, sender, message, image="", file_url="", preview_url=""):
    message_row = ChatMessage(
        conversation_id=conversation_id,
        sender=sender,
        message=message,
        image=image,
        file_url=file_url,
        preview_url=preview_url
    )
    db.session.add(message_row)
    conversation = get_conversation(conversation_id)
    if conversation:
        conversation.updated_at = datetime.utcnow()
    db.session.commit()


def read_uploaded_file(path, filename):
    name = filename.lower()
    if name.endswith(".pdf"):
        return read_pdf(path)
    if name.endswith(".docx"):
        return read_docx(path)
    if name.endswith(".txt"):
        return read_txt(path)
    return ""


def file_to_url(path):
    return "/" + path.replace("\\", "/")



def get_recent_context(conversation_id, limit=12):
    messages = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.id.desc()).limit(limit).all()
    messages = list(reversed(messages))
    text = ""
    for msg in messages:
        text += f"{msg.sender}: {msg.message[:700]}\n"
    return text


def execute_brain2_tool(intent, question, style="cinematic", ratio="1:1"):
    if intent in ["ppt", "pdf", "website", "search", "code", "file"]:
        reply, file_url, preview_url = run_productivity_tool(question)
        return reply, "", file_url, preview_url

    if intent == "image":
        try:
            image_url = generate_image(question, style=style, ratio=ratio)
        except TypeError:
            image_url = generate_image(question)
        return f"🎨 Image generated in {style} style with {ratio} ratio.", image_url, "", ""

    if intent == "vision":
        image_context = latest_image_analysis()
        if image_context:
            return answer_question_about_latest_image(image_context, question), "", "", ""
        return "Please upload an image first using the 👁️ button or use Camera Vision.", "", "", ""

    if intent == "agent":
        goal = question.split(":", 1)[1].strip() if ":" in question else question
        agent = SaivexAgent(build_agent_tools())
        result = agent.run(goal)
        return result["plan"] + "\n\nResult:\n" + str(result["result"]), "", "", ""

    return None, "", "", ""

# ======================
# PRODUCTIVITY + AGENT TOOLS
# ======================

def run_productivity_tool(question):
    intent = detect_productivity_intent(question)

    if intent == "ppt":
        path = create_ppt(question)
        return "📊 PowerPoint generated successfully.", file_to_url(path), ""

    if intent == "pdf":
        title = make_title(question)
        content = ask_ai(f"Create a detailed report about: {question}", user_id=str(current_user.id), user_name=current_user.name, memories=get_user_memories())
        path = create_pdf(title, content)
        return "📄 PDF generated successfully.", file_to_url(path), ""

    if intent == "website":
        preview, download = create_website(question)
        return "🌐 Website generated successfully. You can preview or download it.", download, preview

    if intent == "code":
        if not is_premium_user():
            return premium_required_message("Code execution"), "", ""
        code = extract_after_colon(question)
        output = execute_python_code(code)
        return "💻 Code execution result:\n\n" + output, "", ""

    if intent == "file":
        content = ask_ai(f"Create useful document content for: {question}", user_id=str(current_user.id), user_name=current_user.name, memories=get_user_memories())
        path = create_docx(make_title(question), content)
        return "📁 File generated successfully.", file_to_url(path), ""

    if intent == "search":
        query = extract_after_colon(question)
        results = search_internet(query)
        summary = ask_ai(f"Summarize these web results clearly:\n\n{results}", user_id=str(current_user.id), user_name=current_user.name, memories=get_user_memories())
        return "🔎 Internet search summary:\n\n" + summary + "\n\nSources:\n" + results, "", ""

    return None, "", ""


def build_agent_tools():
    return {
        "ppt": lambda q: run_productivity_tool("create ppt about " + q)[0],
        "pdf": lambda q: run_productivity_tool("create pdf about " + q)[0],
        "website": lambda q: run_productivity_tool("create website for " + q)[0],
        "search": lambda q: run_productivity_tool("search: " + q)[0],
        "code": lambda q: run_productivity_tool("run code: " + q)[0],
        "image": lambda q: "Use normal chat: generate image of " + q,
        "vision": lambda q: answer_question_about_latest_image(latest_image_analysis(), q),
        "chat": lambda q: ask_ai(q, user_id=str(current_user.id), user_name=current_user.name, memories=get_user_memories())
    }


# ======================
# PAGE ROUTES
# ======================

@app.route("/")
@login_required
def home():
    return render_template("index.html", user=current_user, USER=current_user)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/settings")
@login_required
def settings():
    settings_row = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings_row:
        settings_row = UserSettings(user_id=current_user.id)
        db.session.add(settings_row)
        db.session.commit()
    return render_template("settings.html", user=current_user, settings=settings_row)



@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    name = request.form.get("name", "").strip()
    if name:
        current_user.name = name[:100]
        db.session.commit()
    return "<script>window.location='/profile'</script>"


@app.route("/update_settings", methods=["POST"])
@login_required
def update_settings():
    settings_row = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings_row:
        settings_row = UserSettings(user_id=current_user.id)
        db.session.add(settings_row)

    settings_row.theme = request.form.get("theme", "kalinga")
    settings_row.voice_enabled = request.form.get("voice_enabled") == "on"
    settings_row.image_style = request.form.get("image_style", "cinematic")

    db.session.commit()
    return "<script>window.location='/settings'</script>"


@app.route("/admin")
@login_required
def admin_dashboard():
    admin_email = os.environ.get("SAIVEX_ADMIN_EMAIL", "")
    if not admin_email:
        return "Set SAIVEX_ADMIN_EMAIL first.", 403
    if current_user.email != admin_email:
        return "Admin access only.", 403
    return render_template(
        "admin.html",
        users=User.query.count(),
        conversations=Conversation.query.count(),
        messages=ChatMessage.query.count(),
        memories=Memory.query.count(),
        documents=UploadedDocument.query.count(),
        images=UploadedImage.query.count(),
        premium_users=Subscription.query.filter_by(status="active").count() if "Subscription" in globals() else 0
    )


@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "app": "SAIVEX v1"})


# ======================
# AUTH ROUTES
# ======================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template("auth_message.html", title="Account Exists", message="Email already exists. Please login.", link="/login", link_text="Go to Login")

        ok, error = safe_password(password)
        if not ok:
            return render_template("auth_message.html", title="Weak Password", message=error, link="/signup", link_text="Try Again")

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            is_email_verified=True
        )

        db.session.add(user)
        db.session.commit()

        return render_template("auth_message.html", title="Account Created", message="Your SAIVEX account is ready. You can login now.", link="/login", link_text="Login")

    return render_template("signup.html")



@app.route("/login/google")
def login_google():
    if not google_client_id or not google_client_secret:
        return render_template(
            "auth_message.html",
            title="Google Login Not Ready",
            message="Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first. Then restart SAIVEX.",
            link="/login",
            link_text="Back to Login"
        )

    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/login/google/callback")
def google_callback():
    if not google_client_id or not google_client_secret:
        return render_template(
            "auth_message.html",
            title="Google Login Not Ready",
            message="Google OAuth keys are missing.",
            link="/login",
            link_text="Back to Login"
        )

    try:
        token = oauth.google.authorize_access_token()
        userinfo = oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo").json()

        email = userinfo.get("email", "").lower()
        name = userinfo.get("name", "SAIVEX User")

        if not email:
            return render_template(
                "auth_message.html",
                title="Google Login Failed",
                message="Google did not return an email address.",
                link="/login",
                link_text="Try Again"
            )

        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash("google-oauth-user"),
                is_email_verified=True
            )
            db.session.add(user)
            db.session.commit()

        login_user(user, remember=True)
        return "<script>window.location='/'</script>"

    except Exception as error:
        print("Google OAuth error:", error)
        return render_template(
            "auth_message.html",
            title="Google Login Error",
            message="Google login failed. Check your redirect URI and terminal error.",
            link="/login",
            link_text="Back to Login"
        )


@app.route("/login/apple")
def login_apple():
    return render_template(
        "auth_message.html",
        title="Apple Login Needs Apple Developer Setup",
        message="Sign in with Apple requires an Apple Developer account, Services ID, domain verification, and redirect URL setup. We will connect it after you create those credentials.",
        link="/login",
        link_text="Back to Login"
    )


@app.route("/login/phone")
def login_phone():
    firebase_config = get_firebase_web_config()

    if not firebase_api_key or not firebase_auth_domain or not firebase_project_id:
        return render_template(
            "auth_message.html",
            title="Firebase Phone Login Not Ready",
            message="Add FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID, FIREBASE_APP_ID, and FIREBASE_MESSAGING_SENDER_ID first. Then restart SAIVEX.",
            link="/login",
            link_text="Back to Login"
        )

    return render_template("phone_login.html", firebase_config=firebase_config)


@app.route("/phone_login_complete", methods=["POST"])
def phone_login_complete():
    data = request.get_json()
    id_token = data.get("idToken", "")
    fallback_phone = data.get("phone", "")

    phone_number = ""
    firebase_uid = ""

    if init_firebase_admin() and firebase_auth is not None:
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            phone_number = decoded.get("phone_number", "")
            firebase_uid = decoded.get("uid", "")
        except Exception as error:
            print("Firebase token verification failed:", error)
            return jsonify({"status": "error", "message": "Phone login verification failed. Check Firebase setup."}), 401

    elif phone_login_allowed_without_admin():
        phone_number = fallback_phone
        firebase_uid = "local_phone_" + phone_number.replace("+", "").replace(" ", "")
        print("WARNING: Using unverified local phone login fallback. Do not use this in production.")

    else:
        return jsonify({"status": "error", "message": "Firebase Admin is not configured."}), 500

    if not phone_number:
        return jsonify({"status": "error", "message": "Phone number not found."}), 400

    email = firebase_uid + "@phone.saivex.local"
    name = "Phone User " + phone_number[-4:]

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            name=name,
            email=email,
            password=generate_password_hash("firebase-phone-user"),
            is_email_verified=True
        )
        db.session.add(user)
        db.session.commit()

    login_user(user, remember=True)
    return jsonify({"status": "success", "redirect": "/"})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return "<script>window.location='/'</script>"

        return render_template("auth_message.html", title="Login Failed", message="Invalid email or password.", link="/login", link_text="Try Again")

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_token(email, "password-reset")
            link = public_base_url() + "/reset-password/" + token
            print_email_link("SAIVEX Password Reset", email, link)

        return render_template(
            "auth_message.html",
            title="Check Terminal",
            message="If this email exists, a reset link was generated in your VS Code terminal.",
            link="/login",
            link_text="Back to Login"
        )

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_token(token, "password-reset", max_age=3600)

    if not email:
        return render_template("auth_message.html", title="Invalid Link", message="This reset link is invalid or expired.", link="/forgot-password", link_text="Try Again")

    user = User.query.filter_by(email=email).first()

    if not user:
        return render_template("auth_message.html", title="Account Not Found", message="No account found for this reset link.", link="/signup", link_text="Create Account")

    if request.method == "POST":
        password = request.form["password"]
        ok, error = safe_password(password)

        if not ok:
            return render_template("auth_message.html", title="Weak Password", message=error, link=request.path, link_text="Try Again")

        user.password = generate_password_hash(password)
        db.session.commit()

        return render_template("auth_message.html", title="Password Updated", message="Your password has been changed.", link="/login", link_text="Login")

    return render_template("reset_password.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "<script>window.location='/login'</script>"




# ======================
# PRICING + PAYMENT ROUTES
# ======================

@app.route("/pricing")
@login_required
def pricing():
    return render_template(
        "pricing.html",
        user=current_user,
        is_premium=is_premium_user(),
        free_features=FREE_FEATURES,
        premium_features=PREMIUM_FEATURES,
        razorpay_key=RAZORPAY_KEY_ID
    )


@app.route("/create_payment_order", methods=["POST"])
@login_required
def create_payment_order():
    data = request.get_json() or {}
    plan_id = data.get("plan", "premium_monthly")

    order, error = create_razorpay_order(plan_id, user_id=current_user.id, email=current_user.email)

    if error:
        return jsonify({"status": "error", "message": str(error)}), 400

    return jsonify({
        "status": "success",
        "key": RAZORPAY_KEY_ID,
        "order": order,
        "plan": PLANS[plan_id]
    })


@app.route("/payment_success", methods=["POST"])
@login_required
def payment_success():
    data = request.get_json() or {}

    plan_id = data.get("plan", "premium_monthly")
    order_id = data.get("razorpay_order_id", "")
    payment_id = data.get("razorpay_payment_id", "")
    signature = data.get("razorpay_signature", "")

    if not verify_razorpay_signature(order_id, payment_id, signature):
        return jsonify({"status": "error", "message": "Payment verification failed."}), 400

    if plan_id not in PLANS:
        return jsonify({"status": "error", "message": "Invalid plan."}), 400

    days = PLANS[plan_id].get("days", 30)
    expires_at = datetime.utcnow() + timedelta(days=days)

    old_subs = Subscription.query.filter_by(user_id=current_user.id, status="active").all()
    for sub in old_subs:
        sub.status = "inactive"

    subscription = Subscription(
        user_id=current_user.id,
        plan=plan_id,
        status="active",
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        expires_at=expires_at
    )

    db.session.add(subscription)
    db.session.commit()

    return jsonify({"status": "success", "message": "SAIVEX Premium activated."})


@app.route("/my_plan")
@login_required
def my_plan():
    sub = current_subscription()
    return jsonify({
        "premium": is_premium_user(),
        "plan": sub.plan if sub else "free",
        "expires_at": sub.expires_at.isoformat() if sub and sub.expires_at else None,
        "free_features": FREE_FEATURES,
        "premium_features": PREMIUM_FEATURES
    })


# ======================
# DATA ROUTES
# ======================

@app.route("/conversations")
@login_required
def conversations():
    items = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.pinned.desc(), Conversation.updated_at.desc()).all()
    return jsonify([{"id": c.id, "title": c.title, "icon": c.icon, "folder": c.folder, "pinned": c.pinned} for c in items])


@app.route("/new_conversation", methods=["POST"])
@login_required
def new_conversation():
    conversation = create_conversation("New Chat")
    return jsonify({"id": conversation.id, "title": conversation.title, "icon": conversation.icon, "folder": conversation.folder, "pinned": conversation.pinned})


@app.route("/conversation/<int:conversation_id>")
@login_required
def conversation_messages(conversation_id):
    conversation = get_conversation(conversation_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    messages = ChatMessage.query.filter_by(conversation_id=conversation.id).order_by(ChatMessage.id.asc()).all()
    return jsonify({
        "conversation": {"id": conversation.id, "title": conversation.title, "icon": conversation.icon, "folder": conversation.folder, "pinned": conversation.pinned},
        "messages": [{"sender": m.sender, "message": m.message, "image": m.image, "file_url": m.file_url, "preview_url": m.preview_url} for m in messages]
    })


@app.route("/pin_conversation/<int:conversation_id>", methods=["POST"])
@login_required
def pin_conversation(conversation_id):
    conversation = get_conversation(conversation_id)
    if not conversation:
        return jsonify({"status": "not_found"})
    conversation.pinned = not conversation.pinned
    conversation.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "updated", "pinned": conversation.pinned})


@app.route("/delete_conversation/<int:conversation_id>", methods=["POST"])
@login_required
def delete_conversation(conversation_id):
    conversation = get_conversation(conversation_id)
    if not conversation:
        return jsonify({"status": "not_found"})
    ChatMessage.query.filter_by(conversation_id=conversation.id).delete()
    db.session.delete(conversation)
    db.session.commit()
    return jsonify({"status": "deleted"})


@app.route("/rename_conversation/<int:conversation_id>", methods=["POST"])
@login_required
def rename_conversation(conversation_id):
    conversation = get_conversation(conversation_id)
    if not conversation:
        return jsonify({"status": "not_found"})
    title = request.get_json().get("title", "").strip()
    if title:
        conversation.title = title[:120]
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
    return jsonify({"status": "renamed"})


@app.route("/memories")
@login_required
def memories():
    memories_list = Memory.query.filter_by(user_id=current_user.id).all()
    return jsonify([{"id": memory.id, "value": memory.value} for memory in memories_list])


@app.route("/delete_memory/<int:memory_id>", methods=["POST"])
@login_required
def delete_memory(memory_id):
    memory = Memory.query.filter_by(id=memory_id, user_id=current_user.id).first()
    if memory:
        db.session.delete(memory)
        db.session.commit()
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not_found"})


@app.route("/documents")
@login_required
def documents():
    docs = UploadedDocument.query.filter_by(user_id=current_user.id).all()
    return jsonify([{"id": doc.id, "filename": doc.filename} for doc in docs])


@app.route("/delete_document/<int:document_id>", methods=["POST"])
@login_required
def delete_document(document_id):
    document = UploadedDocument.query.filter_by(id=document_id, user_id=current_user.id).first()
    if document:
        db.session.delete(document)
        db.session.commit()
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not_found"})


# ======================
# UPLOAD ROUTES
# ======================

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        return jsonify({"reply": "No file uploaded.", "status": "error"})
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"reply": "No file selected.", "status": "error"})
    filename = secure_filename(file.filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    content = read_uploaded_file(path, filename)
    if content.strip() == "":
        return jsonify({"reply": "Sorry, I could not read this file. Please upload PDF, DOCX, or TXT.", "status": "error"})
    db.session.add(UploadedDocument(user_id=current_user.id, filename=filename, content=content))
    db.session.commit()
    return jsonify({"reply": f"📄 I have uploaded and read {filename}. You can now ask me questions about it.", "status": "success"})


@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    if "image" not in request.files:
        return jsonify({"reply": "No image uploaded.", "status": "error"})
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"reply": "No image selected.", "status": "error"})
    filename = secure_filename(file.filename)
    os.makedirs(app.config["IMAGE_UPLOAD_FOLDER"], exist_ok=True)
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    path = os.path.join(app.config["IMAGE_UPLOAD_FOLDER"], unique_name)
    file.save(path)
    user_question = request.form.get("question", "Explain this image clearly.")
    image_url = "/" + path.replace("\\", "/")
    analysis = analyze_image_with_ai(path, filename, user_question)
    uploaded_image = UploadedImage(user_id=current_user.id, filename=filename, image_url=image_url, analysis=analysis)
    db.session.add(uploaded_image)
    db.session.commit()
    conversation = create_conversation("Uploaded image vision analysis")
    save_chat(conversation.id, "user", f"Uploaded image: {filename}", image_url)
    save_chat(conversation.id, "saivex", analysis, image_url)
    return jsonify({"conversation_id": conversation.id, "reply": analysis, "image": image_url, "status": "success"})


@app.route("/upload_camera_image", methods=["POST"])
@login_required
def upload_camera_image():
    if not is_premium_user():
        return jsonify({"reply": premium_required_message("Camera vision"), "status": "premium_required"}), 402
    return upload_image()


# ======================
# AI ROUTES
# ======================

@app.route("/agent", methods=["POST"])
@login_required
def agent_mode():
    data = request.get_json()
    goal = data.get("goal", "")
    agent = SaivexAgent(build_agent_tools())
    result = agent.run(goal)
    reply = result["plan"] + "\n\nResult:\n" + str(result["result"])
    return jsonify({"reply": reply, "intent": result["intent"]})


@app.route("/voice_chat", methods=["POST"])
@login_required
def voice_chat():
    if not is_premium_user():
        return jsonify({"reply": premium_required_message("Voice conversations"), "status": "premium_required"}), 402
    data = request.get_json()
    message = data.get("message", "")
    reply = ask_multi_model(message, system_prompt="You are SAIVEX Voice. Reply shortly and naturally.", max_tokens=500)
    return jsonify({"reply": reply})


@app.route("/model_chat", methods=["POST"])
@login_required
def model_chat():
    data = request.get_json()
    message = data.get("message", "")
    model = data.get("model", None)
    reply = ask_multi_model(message, system_prompt="You are SAIVEX Multi-Model AI.", model=model, max_tokens=1200)
    return jsonify({"reply": reply})



@app.route("/voice_assistant", methods=["POST"])
@login_required
def voice_assistant():
    if not is_premium_user():
        return jsonify({
            "reply": premium_required_message("Voice conversations"),
            "speech": "Voice conversations are available in SAIVEX Premium.",
            "status": "premium_required",
            "image": "",
            "file_url": "",
            "preview_url": ""
        }), 402
    data = request.get_json()

    message = data.get("message", "").strip()
    style = data.get("style", "cinematic")
    ratio = data.get("ratio", "1:1")
    conversation_id = data.get("conversation_id")

    if not message:
        return jsonify({
            "conversation_id": conversation_id,
            "reply": "I didn't hear anything clearly.",
            "speech": "I didn't hear anything clearly.",
            "lang": "en-US",
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    conversation = get_or_create_conversation(conversation_id, message)
    save_chat(conversation.id, "user", "🎙️ " + message)

    lang = detect_voice_language(message)
    brain_result = brain2_analyze(message)

    # Voice assistant should be conversational first.
    if brain_result.intent == "casual":
        prompt = build_context_prompt(
            message,
            brain_result,
            memories=get_user_memories(),
            documents="",
            image_context="",
            recent_context=get_recent_context(conversation.id, 8)
        )

        reply = ask_multi_model(
            prompt,
            system_prompt=voice_personality_prompt(message),
            max_tokens=450
        )

        speech = clean_for_speech(reply)
        save_chat(conversation.id, "saivex", reply)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "speech": speech,
            "lang": lang,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Voice can still use SAIVEX tools.
    tool_reply, image_url, file_url, preview_url = execute_brain2_tool(brain_result.intent, message, style, ratio)

    if tool_reply:
        reply = tool_reply + brain2_suggestions_text(brain_result)
        speech = clean_for_speech(tool_reply)

        save_chat(conversation.id, "saivex", reply, image_url, file_url, preview_url)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "speech": speech,
            "lang": lang,
            "image": image_url,
            "file_url": file_url,
            "preview_url": preview_url
        })

    prompt = build_context_prompt(
        message,
        brain_result,
        memories=get_user_memories(),
        documents=get_user_documents(),
        image_context="",
        recent_context=get_recent_context(conversation.id, 12)
    )

    reply = ask_multi_model(
        prompt,
        system_prompt=voice_personality_prompt(message),
        max_tokens=650
    )

    speech = clean_for_speech(reply)
    save_chat(conversation.id, "saivex", reply)

    return jsonify({
        "conversation_id": conversation.id,
        "reply": reply,
        "speech": speech,
        "lang": lang,
        "image": "",
        "file_url": "",
        "preview_url": ""
    })



@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json()

    question = data["message"]
    q = question.lower().strip()
    style = data.get("style", "cinematic")
    ratio = data.get("ratio", "1:1")
    conversation_id = data.get("conversation_id")

    conversation = get_or_create_conversation(conversation_id, question)
    save_chat(conversation.id, "user", question)

    brain_result = brain2_analyze(question)

    # Friendly casual chat should never trigger vision or tools.
    if brain_result.intent == "casual":
        casual_prompt = build_context_prompt(
            question,
            brain_result,
            memories=get_user_memories(),
            documents="",
            image_context="",
            recent_context=get_recent_context(conversation.id, 8)
        )
        answer = ask_multi_model(
            casual_prompt,
            system_prompt="You are SAIVEX. Reply warmly, naturally, and briefly. Do not mention tools unless asked.",
            max_tokens=350
        )
        save_chat(conversation.id, "saivex", answer)
        return jsonify({
            "conversation_id": conversation.id,
            "reply": answer,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Brain/plan explanation mode
    if q.startswith("brain:") or q.startswith("plan:"):
        reply = brain2_plan_text(brain_result) + brain2_suggestions_text(brain_result)
        save_chat(conversation.id, "saivex", reply)
        return jsonify({"conversation_id": conversation.id, "reply": reply, "image": "", "file_url": "", "preview_url": ""})

    # Memory save
    if brain_result.intent == "memory_save":
        memory_text = extract_memory(question)
        if memory_text:
            save_memory(memory_text)
            reply = "Okay. I will remember that."
        else:
            reply = "Tell me what you want me to remember."
        save_chat(conversation.id, "saivex", reply)
        return jsonify({"conversation_id": conversation.id, "reply": reply, "image": "", "file_url": "", "preview_url": ""})

    # Memory read
    if brain_result.intent == "memory_read":
        memories = Memory.query.filter_by(user_id=current_user.id).all()
        reply = "I don't remember anything yet." if not memories else "I remember:\n" + "\n".join([f"• {m.value}" for m in memories])
        save_chat(conversation.id, "saivex", reply)
        return jsonify({"conversation_id": conversation.id, "reply": reply, "image": "", "file_url": "", "preview_url": ""})

    # Name memory
    if "my name is" in q:
        name = question.split("is")[-1].strip()
        current_user.name = name
        db.session.commit()
        reply = f"Okay {name}. I will remember your name."
        save_chat(conversation.id, "saivex", reply)
        return jsonify({"conversation_id": conversation.id, "reply": reply, "image": "", "file_url": "", "preview_url": ""})

    if "what is my name" in q:
        reply = f"Your name is {current_user.name}."
        save_chat(conversation.id, "saivex", reply)
        return jsonify({"conversation_id": conversation.id, "reply": reply, "image": "", "file_url": "", "preview_url": ""})

    # Execute direct Brain 2.0 tools.
    # Vision will only run if the user explicitly asks about an uploaded/current image.
    tool_reply, image_url, file_url, preview_url = execute_brain2_tool(brain_result.intent, question, style, ratio)

    if tool_reply:
        reply = tool_reply + brain2_suggestions_text(brain_result)
        save_chat(conversation.id, "saivex", reply, image_url, file_url, preview_url)
        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": image_url,
            "file_url": file_url,
            "preview_url": preview_url
        })

    # Continue mode
    if brain_result.intent == "continue":
        recent_context = get_recent_context(conversation.id, 18)
        prompt = build_context_prompt(
            question,
            brain_result,
            memories=get_user_memories(),
            documents=get_user_documents(),
            image_context="",
            recent_context=recent_context
        )
        answer = ask_multi_model(
            prompt,
            system_prompt="You are SAIVEX Brain 2.0. Continue the user's project intelligently.",
            max_tokens=1200
        )
        answer += brain2_suggestions_text(brain_result)
        save_chat(conversation.id, "saivex", answer)
        return jsonify({"conversation_id": conversation.id, "reply": answer, "image": "", "file_url": "", "preview_url": ""})

    # Normal AI chat
    # IMPORTANT: latest image context is NOT included here, so normal chat won't fall into image analysis.
    full_question = build_context_prompt(
        question,
        brain_result,
        memories=get_user_memories(),
        documents=get_user_documents(),
        image_context="",
        recent_context=get_recent_context(conversation.id, 18)
    )

    answer = ask_multi_model(
        full_question,
        system_prompt=brain_result.personality,
        max_tokens=1400
    )

    answer += brain2_suggestions_text(brain_result)

    save_chat(conversation.id, "saivex", answer)

    return jsonify({
        "conversation_id": conversation.id,
        "reply": answer,
        "image": "",
        "file_url": "",
        "preview_url": ""
    })


# ======================
# APP START
# ======================

with app.app_context():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static/generated", exist_ok=True)
    os.makedirs("static/generated/uploads", exist_ok=True)
    db.create_all()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("PRODUCTION") != "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
