def create_plan(intent, message):
    plans = {
        "ppt": ["Understand presentation topic", "Create slide outline", "Generate PowerPoint file", "Return download link"],
        "pdf": ["Understand report topic", "Generate structured content", "Create PDF", "Return download link"],
        "website": ["Understand website purpose", "Generate HTML, CSS, and JS", "Create preview", "Return download ZIP"],
        "search": ["Search internet", "Collect top results", "Summarize clearly", "Return sources"],
        "image": ["Enhance image prompt", "Generate image", "Return image preview"],
        "vision": ["Use latest uploaded image", "Analyze image context", "Answer user question"],
        "code": ["Extract code", "Run safely", "Return output or error"],
        "chat": ["Understand question", "Use memory and context", "Reply naturally"],
        "continue": ["Find previous context", "Continue the current task", "Suggest next action"]
    }
    return plans.get(intent, plans["chat"])

def plan_text(intent, message):
    steps = create_plan(intent, message)
    text = "🧠 Saivex Brain Plan:\n"
    for i, step in enumerate(steps, start=1):
        text += f"{i}. {step}\n"
    return text
