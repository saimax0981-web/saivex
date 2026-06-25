"""
SAIVEX Brain 3.0 — lightweight production router.

This is a safe helper for future routing. Your current legacy_app.py can keep using Brain 2.0.
"""

def classify_task(message):
    q = message.lower().strip()

    if q.startswith("agent:") or "do this task" in q:
        return "agent"
    if "ppt" in q or "powerpoint" in q or "presentation" in q:
        return "ppt"
    if "pdf" in q or "report" in q:
        return "pdf"
    if "website" in q or "portfolio" in q or "landing page" in q:
        return "website"
    if "search" in q or "latest" in q or "current" in q:
        return "search"
    if "generate image" in q or "create image" in q or "wallpaper" in q or "poster" in q:
        return "image"
    if "uploaded image" in q or "explain image" in q or "screenshot" in q:
        return "vision"
    if "code" in q or "python" in q or "debug" in q:
        return "code"
    if q in ["hi", "hello", "hey", "how are you", "thanks", "thank you"]:
        return "casual"

    return "chat"


def make_execution_plan(message):
    task = classify_task(message)

    plans = {
        "agent": ["Understand goal", "Plan steps", "Choose tools", "Execute", "Return result"],
        "ppt": ["Research topic", "Create outline", "Generate unique slides", "Add references"],
        "pdf": ["Research topic", "Write sections", "Format PDF", "Add sources"],
        "website": ["Research topic", "Create sections", "Generate HTML/CSS/JS", "Zip files"],
        "search": ["Search web", "Rank information", "Summarize"],
        "image": ["Enhance prompt", "Generate image", "Return preview"],
        "vision": ["Use uploaded image", "Analyze content", "Answer"],
        "code": ["Understand task", "Run/generate code", "Explain"],
        "casual": ["Reply naturally"],
        "chat": ["Use context", "Answer clearly"]
    }

    return task, plans.get(task, plans["chat"])
