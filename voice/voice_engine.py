import re


def clean_for_speech(text):
    """
    Converts rich AI text into cleaner spoken text.
    """
    if not text:
        return ""

    text = re.sub(r"```[\s\S]*?```", "Code block omitted for speech.", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"#+\s*", "", text)
    text = re.sub(r"[-•]\s+", "", text)
    text = text.replace("SAIVEX", "Sai Vex")
    text = text.replace("PPT", "PowerPoint")
    text = text.replace("PDF", "P D F")
    text = text.replace("URL", "U R L")

    if len(text) > 900:
        text = text[:900] + " I shortened this for voice."

    return text.strip()


def detect_voice_language(message):
    """
    Simple language detection for browser speech.
    """
    telugu_chars = any("\u0c00" <= ch <= "\u0c7f" for ch in message)
    hindi_chars = any("\u0900" <= ch <= "\u097f" for ch in message)

    if telugu_chars:
        return "te-IN"

    if hindi_chars:
        return "hi-IN"

    return "en-US"


def voice_personality_prompt(message):
    lang = detect_voice_language(message)

    if lang == "te-IN":
        return "You are SAIVEX Voice. Reply naturally in simple Telugu mixed with English if helpful. Keep it short."

    if lang == "hi-IN":
        return "You are SAIVEX Voice. Reply naturally in simple Hindi mixed with English if helpful. Keep it short."

    return "You are SAIVEX Voice. Reply warmly, naturally, and briefly like a helpful AI assistant."
