def should_save_memory(message):
    q = message.lower()
    return q.startswith("remember that") or "remember this" in q

def extract_memory(message):
    q = message
    q = q.replace("remember that", "")
    q = q.replace("Remember that", "")
    q = q.replace("remember this", "")
    q = q.replace("Remember this", "")
    return q.strip()
