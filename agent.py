def detect_agent_action(message):
    q = message.lower()

    if q.startswith("agent:"):
        return "agent"

    if q.startswith("generate") or "generate image" in q or "create image" in q:
        return "image"

    if "summarize uploaded" in q or "summarize document" in q or "summarize pdf" in q:
        return "document_summary"

    if "search web" in q or "internet search" in q:
        return "web_search"

    return "chat"


def build_agent_reply(message, user_name, memories_text, documents_text):
    q = message.lower()

    if q.startswith("agent:"):
        return f"""⚡ Saivex Agent Mode activated for {user_name}.

I can plan and complete multi-step tasks.

Available abilities:
• AI Chat
• Image Generation
• Document Reading
• Memory
• Kalinga Mode
• Coding Help
• Study Help
• Project Planning
• Internet Search foundation

Tell me one goal, and I will break it into clear steps."""

    if "summarize" in q and "document" in q:
        if documents_text.strip() == "":
            return "Upload a PDF, DOCX, or TXT first. Then I can summarize it."
        return "Document summary mode is ready. Ask: summarize uploaded document, explain simply, or give important points."

    if "what can you do" in q or "tools" in q:
        return """Saivex Stage 2 tools:

🎨 Image Studio
📄 Document Reader
🧠 Memory
🎤 Voice Input
🔊 Voice Reply
👑 Kalinga Mode
💻 Coding Helper
⚡ Agent Mode
📱 Mobile-friendly UI"""

    return None
