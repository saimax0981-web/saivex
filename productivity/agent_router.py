def detect_productivity_intent(message):
    q = message.lower().strip()

    if q.startswith("agent:") or q.startswith("plan:"):
        return "agent"

    if "create powerpoint" in q or "make powerpoint" in q or "create ppt" in q or "make ppt" in q:
        return "ppt"

    if "create pdf" in q or "make pdf" in q or "generate pdf" in q:
        return "pdf"

    if "create website" in q or "make website" in q or "build website" in q or "generate website" in q:
        return "website"

    if q.startswith("run code:") or q.startswith("execute code:"):
        return "code"

    if "create file" in q or "generate file" in q or "make document" in q:
        return "file"

    if q.startswith("search:") or q.startswith("search web:") or "search internet" in q or "latest" in q:
        return "search"

    if q.startswith("generate") or "generate image" in q or "create image" in q:
        return "image"

    return None


def extract_after_colon(message):
    if ":" in message:
        return message.split(":", 1)[1].strip()
    return message


def build_agent_plan(message):
    goal = extract_after_colon(message)

    return f"""⚡ Saivex Agent Mode

Goal:
{goal}

Plan:
1. Understand the user's goal clearly.
2. Decide which Saivex tool is needed.
3. Use the correct tool:
   • Search for latest information
   • Create PPT
   • Create PDF
   • Create website
   • Run code
   • Generate file
   • Generate image
   • Use memory and uploaded documents
4. Return the result with download links if a file is created.
5. Suggest the next useful step.

To directly use tools:
• create ppt about ...
• create pdf about ...
• create website for ...
• search: ...
• run code: print("Hello")
• generate image of ...
"""


def agent_decision(message):
    q = message.lower().strip()

    if "presentation" in q or "slides" in q:
        return "ppt"

    if "report" in q or "notes" in q or "pdf" in q:
        return "pdf"

    if "website" in q or "landing page" in q or "portfolio" in q:
        return "website"

    if "latest" in q or "news" in q or "today" in q or "current" in q:
        return "search"

    if "python" in q and ("run" in q or "execute" in q):
        return "code"

    if "image" in q or "wallpaper" in q or "poster" in q or "logo" in q:
        return "image"

    return "chat"
