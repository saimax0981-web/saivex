
from brain.intent_detector import detect_intent

CASUAL_MESSAGES = {
    "hi", "hello", "hey", "hii", "hai", "yo", "good morning", "good afternoon",
    "good evening", "good night", "how are you", "how r u", "what's up", "sup",
    "thanks", "thank you", "ok", "okay", "nice", "great", "super", "cool"
}

VISION_TRIGGERS = [
    "explain image", "explain my image", "explain uploaded image", "explain this image",
    "what is in this image", "what's in this image", "describe image", "describe this image",
    "read image", "read this image", "ocr", "extract text", "text in image",
    "solve this image", "solve image", "analyze image", "analyze this image",
    "camera image", "uploaded image", "this screenshot", "screenshot",
    "chart in image", "graph in image", "handwriting", "diagram in image", "compare images",
]

IMAGE_GENERATION_TRIGGERS = [
    "generate image", "create image", "make image", "generate a image", "create a image",
    "generate picture", "create picture", "wallpaper", "poster", "logo design",
    "generate logo", "create logo"
]

def is_casual(message):
    q = message.lower().strip()
    if q in CASUAL_MESSAGES:
        return True
    if len(q.split()) <= 4 and any(x in q for x in ["hello", "hi", "how are you", "thanks", "thank you"]):
        return True
    return False

def wants_vision(message):
    q = message.lower().strip()
    return any(trigger in q for trigger in VISION_TRIGGERS)

def wants_image_generation(message):
    q = message.lower().strip()
    return any(trigger in q for trigger in IMAGE_GENERATION_TRIGGERS)

def detect_advanced_intent(message):
    q = message.lower().strip()

    if is_casual(q):
        return "casual"
    if q.startswith("agent:") or q.startswith("do this task:") or "autonomous" in q:
        return "agent"
    if wants_vision(q):
        return "vision"
    if wants_image_generation(q) or q.startswith("generate "):
        return "image"
    if any(x in q for x in ["create ppt", "make ppt", "presentation", "powerpoint", "slides"]):
        return "ppt"
    if any(x in q for x in ["create pdf", "make pdf", "pdf report", "notes pdf"]):
        return "pdf"
    if any(x in q for x in ["create website", "make website", "build website", "landing page", "portfolio website"]):
        return "website"
    if q.startswith("search:") or any(x in q for x in ["search internet", "search web", "latest news", "current news", "today news"]):
        return "search"
    if q.startswith("run code:") or q.startswith("execute code:") or "run this python" in q or "debug this" in q:
        return "code"
    if any(x in q for x in ["remember that", "remember this"]):
        return "memory_save"
    if any(x in q for x in ["what do you remember", "my memories", "remember about me"]):
        return "memory_read"
    if any(x in q for x in ["uploaded document", "my pdf", "my document", "summarize document", "explain pdf"]):
        return "document"
    if any(x in q for x in ["create file", "generate file", "make document", "create docx"]):
        return "file"
    if q in ["continue", "next", "what next", "continue project"]:
        return "continue"

    base_intent = detect_intent(message)
    if base_intent == "vision" and not wants_vision(q):
        return "chat"
    return base_intent or "chat"

def plan_for_intent(intent, message):
    plans = {
        "casual": ["Recognize friendly/casual message", "Reply naturally without tools"],
        "agent": ["Understand goal", "Break into steps", "Choose tools", "Execute and answer"],
        "ppt": ["Identify topic", "Create slides", "Return PPT"],
        "pdf": ["Identify topic", "Write report", "Return PDF"],
        "website": ["Understand purpose", "Generate website", "Return preview and ZIP"],
        "search": ["Search internet", "Summarize results", "Return sources"],
        "image": ["Improve prompt", "Generate image", "Return preview"],
        "vision": ["Use latest uploaded image", "Analyze image", "Answer clearly"],
        "code": ["Extract code", "Run safely", "Return result"],
        "memory_save": ["Extract memory", "Save memory", "Confirm"],
        "memory_read": ["Read memories", "Summarize"],
        "continue": ["Check recent context", "Continue project"],
        "chat": ["Understand question", "Use context", "Reply naturally"],
    }
    return plans.get(intent, plans["chat"])

def personality_for_intent(intent):
    mapping = {
        "casual": "You are SAIVEX, a warm friendly AI companion. Reply casually and naturally.",
        "agent": "You are SAIVEX Agent, a practical autonomous task executor.",
        "ppt": "You are a professional presentation designer.",
        "pdf": "You are a clear report writer and teacher.",
        "website": "You are a modern web designer and frontend expert.",
        "search": "You are a careful research assistant.",
        "image": "You are a cinematic creative director.",
        "vision": "You are SAIVEX Vision, a precise image understanding assistant.",
        "code": "You are a patient coding mentor.",
        "continue": "You are a project manager continuing the user's workflow.",
        "chat": "You are SAIVEX, a friendly and powerful Kalinga-themed AI assistant."
    }
    return mapping.get(intent, mapping["chat"])

def suggestions_for_intent(intent):
    mapping = {
        "casual": [],
        "agent": ["Continue this task", "Create a roadmap", "Make this into a document"],
        "ppt": ["Create PDF from this", "Generate images for slides", "Make it more professional"],
        "pdf": ["Create PPT from this", "Summarize it shorter", "Make student notes"],
        "website": ["Add animations", "Make it mobile-first", "Create a premium version"],
        "search": ["Create a report from results", "Make PPT from this", "Search deeper"],
        "image": ["Make it 16:9", "Create another version", "Create Instagram poster"],
        "vision": ["Extract text", "Explain simply", "Create notes from image"],
        "code": ["Fix errors", "Explain code", "Optimize it"],
        "continue": ["Move to next phase", "Generate full updated code", "Test this feature"],
        "chat": ["Create PPT", "Create PDF", "Search internet"],
    }
    return mapping.get(intent, mapping["chat"])

class Brain2Result:
    def __init__(self, intent, plan, personality, tool_name, suggestions):
        self.intent = intent
        self.plan = plan
        self.personality = personality
        self.tool_name = tool_name
        self.suggestions = suggestions

def analyze(message):
    intent = detect_advanced_intent(message)
    return Brain2Result(
        intent=intent,
        plan=plan_for_intent(intent, message),
        personality=personality_for_intent(intent),
        tool_name=intent,
        suggestions=suggestions_for_intent(intent)
    )

def plan_text(result):
    text = "🧠 SAIVEX Brain 2.0 Plan:\\n"
    for i, step in enumerate(result.plan, start=1):
        text += f"{i}. {step}\\n"
    return text

def suggestions_text(result):
    if not result.suggestions:
        return ""
    text = "\\n\\nSuggestions:\\n"
    for suggestion in result.suggestions:
        text += f"• {suggestion}\\n"
    return text

def build_context_prompt(user_question, brain_result, memories="", documents="", image_context="", recent_context=""):
    image_section = ""
    if brain_result.intent == "vision":
        image_section = f"\\nLatest image context:\\n{image_context}\\n"
    return f"""
You are SAIVEX Brain 2.0.

Personality:
{brain_result.personality}

Detected intent:
{brain_result.intent}

Plan:
{plan_text(brain_result)}

Recent conversation:
{recent_context}

User memories:
{memories}

Uploaded documents:
{documents}

{image_section}

User question:
{user_question}

Answer naturally, clearly, and helpfully.
"""
