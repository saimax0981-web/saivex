def extract_profile_memory(text):
    q = text.lower()
    memories = []
    if "my name is" in q or "i like" in q or "i love" in q:
        memories.append(text)
    if "my project" in q or "saivex" in q or "remember that" in q:
        memories.append(text.replace("remember that", "").strip())
    return [m for m in memories if m]


def summarize_memory(memories):
    if not memories:
        return "No long-term memory yet."
    return "Long-term memory summary:\n" + "\n".join([f"• {m}" for m in memories])
