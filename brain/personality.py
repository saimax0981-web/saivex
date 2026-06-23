def personality_for_intent(intent):
    if intent == "code":
        return "Act like a clear coding mentor."
    if intent == "ppt":
        return "Act like a professional presentation designer."
    if intent == "pdf":
        return "Act like a report writer and teacher."
    if intent == "website":
        return "Act like a modern web designer."
    if intent == "search":
        return "Act like a careful research assistant."
    if intent == "image":
        return "Act like a cinematic creative director."
    if intent == "vision":
        return "Act like a careful visual analyst."
    return "Act like Saivex, a friendly and powerful AI assistant."
