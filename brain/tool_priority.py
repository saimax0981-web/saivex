from brain.intent_detector import detect_intent

def score_tools(message):
    intent = detect_intent(message)
    tools = {
        "chat": 10, "ppt": 0, "pdf": 0, "website": 0,
        "search": 0, "code": 0, "image": 0, "vision": 0,
        "document": 0, "file": 0, "memory": 0
    }
    if intent in tools:
        tools[intent] = 100
    return tools

def best_tool(message):
    scores = score_tools(message)
    return max(scores, key=scores.get)
