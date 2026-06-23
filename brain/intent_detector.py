def detect_intent(message):
    q = message.lower().strip()

    if any(x in q for x in ["create ppt", "make ppt", "powerpoint", "presentation", "slides"]):
        return "ppt"
    if any(x in q for x in ["create pdf", "make pdf", "generate pdf", "pdf report", "make report"]):
        return "pdf"
    if any(x in q for x in ["create website", "make website", "build website", "generate website", "landing page", "portfolio website"]):
        return "website"
    if q.startswith("search:") or any(x in q for x in ["search internet", "search web", "latest", "today news", "current news"]):
        return "search"
    if q.startswith("run code:") or q.startswith("execute code:") or "run this python" in q:
        return "code"
    if any(x in q for x in ["generate image", "create image", "make image", "wallpaper", "poster", "logo design"]):
        return "image"
    if any(x in q for x in ["uploaded image", "this image", "explain image", "what is in image", "read image", "solve this image"]):
        return "vision"
    if q.startswith("remember that") or "remember this" in q:
        return "memory_save"
    if any(x in q for x in ["what do you remember", "my memories", "remember about me"]):
        return "memory_read"
    if any(x in q for x in ["uploaded document", "my pdf", "my document", "summarize document", "explain pdf"]):
        return "document"
    if any(x in q for x in ["create file", "generate file", "make document", "create docx"]):
        return "file"
    if q in ["continue", "next", "what next", "continue project"]:
        return "continue"
    return "chat"
