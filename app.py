import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

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


app = Flask(__name__)

# ======================
# PHASE 8 PRODUCTION CONFIG
# ======================

app.config["SECRET_KEY"] = os.environ.get("SAIVEX_SECRET_KEY", "saivex-secret-key-change-later")
database_url = os.environ.get("DATABASE_URL", "sqlite:///saivex_stage3.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["IMAGE_UPLOAD_FOLDER"] = "static/generated/uploads"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

if os.environ.get("PRODUCTION") or os.environ.get("RENDER"):
    app.config["SESSION_COOKIE_SECURE"] = True

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ======================
# DATABASE MODELS
# ======================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)


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


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ======================
# HELPERS
# ======================

def make_title(text):
    words = text.strip().replace("\n", " ").split()
    return " ".join(words[:6]).title()[:55] if words else "New Chat"


def classify_conversation(text):
    q = text.lower()

    if any(w in q for w in ["image", "photo", "picture", "vision", "upload image"]):
        return "👁️", "Vision"

    if any(w in q for w in ["ppt", "powerpoint", "presentation", "slides"]):
        return "📊", "Productivity"

    if any(w in q for w in ["website", "html", "css", "javascript", "portfolio"]):
        return "🌐", "Websites"

    if any(w in q for w in ["search", "internet", "latest", "news", "current"]):
        return "🔎", "Search"

    if any(w in q for w in ["code", "python", "error", "flask", "javascript"]):
        return "💻", "Coding"

    if any(w in q for w in ["kalinga", "kharavela", "king", "empire", "history"]):
        return "👑", "Kalinga"

    if any(w in q for w in ["pdf", "document", "file", "docx"]):
        return "📄", "Documents"

    if any(w in q for w in ["generate", "logo", "wallpaper", "poster", "design"]):
        return "🎨", "Creative"

    return "💬", "General"


def get_or_create_conversation(conversation_id, first_message):
    conversation = None

    if conversation_id:
        conversation = get_conversation(conversation_id)

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
        text += f"\nDocument: {document.filename}\n"
        text += document.content[:4000]
        text += "\n"

    return text


def latest_image_analysis():
    image = UploadedImage.query.filter_by(user_id=current_user.id).order_by(UploadedImage.id.desc()).first()

    if image:
        return image.analysis

    return ""


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
    return Conversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first()


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


# ======================
# PRODUCTIVITY TOOLS
# ======================

def run_productivity_tool(question):
    intent = detect_productivity_intent(question)

    if intent == "ppt":
        path = create_ppt(question)
        return "📊 PowerPoint generated successfully.", file_to_url(path), ""

    if intent == "pdf":
        title = make_title(question)
        content = ask_ai(
            f"Create a detailed report about: {question}",
            user_id=str(current_user.id),
            user_name=current_user.name,
            memories=get_user_memories()
        )
        path = create_pdf(title, content)
        return "📄 PDF generated successfully.", file_to_url(path), ""

    if intent == "website":
        preview, download = create_website(question)
        return "🌐 Website generated successfully. You can preview or download it.", download, preview

    if intent == "code":
        code = extract_after_colon(question)
        output = execute_python_code(code)
        return "💻 Code execution result:\n\n" + output, "", ""

    if intent == "file":
        content = ask_ai(
            f"Create useful document content for: {question}",
            user_id=str(current_user.id),
            user_name=current_user.name,
            memories=get_user_memories()
        )
        path = create_docx(make_title(question), content)
        return "📁 File generated successfully.", file_to_url(path), ""

    if intent == "search":
        query = extract_after_colon(question)
        results = search_internet(query)
        summary = ask_ai(
            f"Summarize these web results clearly:\n\n{results}",
            user_id=str(current_user.id),
            user_name=current_user.name,
            memories=get_user_memories()
        )
        return "🔎 Internet search summary:\n\n" + summary + "\n\nSources:\n" + results, "", ""

    return None, "", ""


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


# ======================
# AUTH ROUTES
# ======================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        existing_user = User.query.filter_by(email=request.form["email"]).first()

        if existing_user:
            return "Email already exists. Please login."

        user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"])
        )

        db.session.add(user)
        db.session.commit()

        return "<script>window.location='/login'</script>"

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return "<script>window.location='/'</script>"

        return "Invalid email or password."

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "<script>window.location='/login'</script>"


# ======================
# CONVERSATION ROUTES
# ======================

@app.route("/conversations")
@login_required
def conversations():
    items = Conversation.query.filter_by(user_id=current_user.id).order_by(
        Conversation.pinned.desc(),
        Conversation.updated_at.desc()
    ).all()

    return jsonify([
        {
            "id": c.id,
            "title": c.title,
            "icon": c.icon,
            "folder": c.folder,
            "pinned": c.pinned
        }
        for c in items
    ])


@app.route("/new_conversation", methods=["POST"])
@login_required
def new_conversation():
    conversation = create_conversation("New Chat")

    return jsonify({
        "id": conversation.id,
        "title": conversation.title,
        "icon": conversation.icon,
        "folder": conversation.folder,
        "pinned": conversation.pinned
    })


@app.route("/conversation/<int:conversation_id>")
@login_required
def conversation_messages(conversation_id):
    conversation = get_conversation(conversation_id)

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    messages = ChatMessage.query.filter_by(conversation_id=conversation.id).order_by(ChatMessage.id.asc()).all()

    return jsonify({
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "icon": conversation.icon,
            "folder": conversation.folder,
            "pinned": conversation.pinned
        },
        "messages": [
            {
                "sender": m.sender,
                "message": m.message,
                "image": m.image,
                "file_url": m.file_url,
                "preview_url": m.preview_url
            }
            for m in messages
        ]
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


# ======================
# MEMORY ROUTES
# ======================

@app.route("/memories")
@login_required
def memories():
    memories_list = Memory.query.filter_by(user_id=current_user.id).all()

    return jsonify([
        {
            "id": memory.id,
            "value": memory.value
        }
        for memory in memories_list
    ])


@app.route("/delete_memory/<int:memory_id>", methods=["POST"])
@login_required
def delete_memory(memory_id):
    memory = Memory.query.filter_by(id=memory_id, user_id=current_user.id).first()

    if memory:
        db.session.delete(memory)
        db.session.commit()
        return jsonify({"status": "deleted"})

    return jsonify({"status": "not_found"})


# ======================
# DOCUMENT ROUTES
# ======================

@app.route("/documents")
@login_required
def documents():
    docs = UploadedDocument.query.filter_by(user_id=current_user.id).all()

    return jsonify([
        {
            "id": doc.id,
            "filename": doc.filename
        }
        for doc in docs
    ])


@app.route("/delete_document/<int:document_id>", methods=["POST"])
@login_required
def delete_document(document_id):
    document = UploadedDocument.query.filter_by(id=document_id, user_id=current_user.id).first()

    if document:
        db.session.delete(document)
        db.session.commit()
        return jsonify({"status": "deleted"})

    return jsonify({"status": "not_found"})


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
        return jsonify({
            "reply": "Sorry, I could not read this file. Please upload PDF, DOCX, or TXT.",
            "status": "error"
        })

    db.session.add(UploadedDocument(user_id=current_user.id, filename=filename, content=content))
    db.session.commit()

    return jsonify({
        "reply": f"📄 I have uploaded and read {filename}. You can now ask me questions about it.",
        "status": "success"
    })


# ======================
# IMAGE / VISION ROUTES
# ======================

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

    uploaded_image = UploadedImage(
        user_id=current_user.id,
        filename=filename,
        image_url=image_url,
        analysis=analysis
    )

    db.session.add(uploaded_image)
    db.session.commit()

    conversation = create_conversation("Uploaded image vision analysis")

    save_chat(conversation.id, "user", f"Uploaded image: {filename}", image_url)
    save_chat(conversation.id, "saivex", analysis, image_url)

    return jsonify({
        "conversation_id": conversation.id,
        "reply": analysis,
        "image": image_url,
        "status": "success"
    })


# ======================
# MAIN SMART CHAT ROUTE
# ======================

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

    brain_data = route_message(question)

    # Brain intro mode
    if is_smart_brain_request(question):
        reply = brain_intro(question) + brain_data["suggestions"]

        save_chat(conversation.id, "saivex", reply)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Memory save
    if brain_data["intent"] == "memory_save":
        memory_text = extract_memory(question)

        if memory_text:
            save_memory(memory_text)
            reply = "Okay. I will remember that."
        else:
            reply = "Tell me what you want me to remember."

        save_chat(conversation.id, "saivex", reply)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Memory read
    if brain_data["intent"] == "memory_read":
        memories = Memory.query.filter_by(user_id=current_user.id).all()

        if not memories:
            reply = "I don't remember anything yet."
        else:
            reply = "I remember:\n" + "\n".join([f"• {m.value}" for m in memories])

        save_chat(conversation.id, "saivex", reply)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Vision chat
    if brain_data["intent"] == "vision":
        image_context = latest_image_analysis()

        if image_context:
            answer = answer_question_about_latest_image(image_context, question)
        else:
            answer = "Please upload an image first using the 👁️ button. Then ask me about it."

        save_chat(conversation.id, "saivex", answer)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": answer,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Productivity tools
    productivity_reply, file_url, preview_url = run_productivity_tool(question)

    if productivity_reply:
        productivity_reply += brain_data["suggestions"]

        save_chat(conversation.id, "saivex", productivity_reply, "", file_url, preview_url)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": productivity_reply,
            "image": "",
            "file_url": file_url,
            "preview_url": preview_url
        })

    # Image generation
    if brain_data["intent"] == "image" or q.startswith("generate"):
        try:
            image_url = generate_image(question, style=style, ratio=ratio)
        except TypeError:
            image_url = generate_image(question)

        reply = f"🎨 Image generated in {style} style with {ratio} ratio."
        reply += brain_data["suggestions"]

        save_chat(conversation.id, "saivex", reply, image_url)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": image_url,
            "file_url": "",
            "preview_url": ""
        })

    # Name memory
    if "my name is" in q:
        name = question.split("is")[-1].strip()
        current_user.name = name
        db.session.commit()

        reply = f"Okay {name}. I will remember your name."

        save_chat(conversation.id, "saivex", reply)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    if "what is my name" in q:
        reply = f"Your name is {current_user.name}."

        save_chat(conversation.id, "saivex", reply)

        return jsonify({
            "conversation_id": conversation.id,
            "reply": reply,
            "image": "",
            "file_url": "",
            "preview_url": ""
        })

    # Final AI chat
    full_question = f"""
You are SAIVEX, a powerful Kalinga-themed AI assistant.

Brain intent:
{brain_data["intent"]}

Brain personality:
{brain_data["personality"]}

Brain plan:
{brain_data["plan"]}

User question:
{question}

User memories:
{get_user_memories()}

Uploaded documents:
{get_user_documents()}

Latest uploaded image analysis:
{latest_image_analysis()}

Answer naturally and helpfully.
"""

    answer = ask_ai(
        full_question,
        user_id=str(current_user.id),
        user_name=current_user.name,
        memories=get_user_memories()
    )

    answer += brain_data["suggestions"]

    save_chat(conversation.id, "saivex", answer)

    return jsonify({
        "conversation_id": conversation.id,
        "reply": answer,
        "image": "",
        "file_url": "",
        "preview_url": ""
    })



# ======================
# PHASE 8 ADMIN DASHBOARD
# ======================

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
        images=UploadedImage.query.count()
    )


@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "app": "SAIVEX"})


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