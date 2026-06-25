import os
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MODEL_MAP = {
    "fast": "openai/gpt-4o-mini",
    "smart": "openai/gpt-4.1",
    "creative": "google/gemini-2.0-flash-001",
    "coding": "anthropic/claude-3.5-sonnet",
    "free": "qwen/qwen-2.5-7b-instruct"
}


def get_openrouter_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key

    try:
        import ai
        for name in ["OPENROUTER_API_KEY", "API_KEY", "OPENAI_API_KEY"]:
            value = getattr(ai, name, None)
            if value:
                return value
    except Exception:
        pass

    try:
        with open("ai.py", "r", encoding="utf-8") as file:
            text = file.read()
        match = re.search(r"(sk-or-[A-Za-z0-9_\-]+|sk-proj-[A-Za-z0-9_\-]+|sk-[A-Za-z0-9_\-]+)", text)
        if match:
            return match.group(1)
    except Exception:
        pass

    return ""


def choose_model(message):
    q = message.lower()
    if any(w in q for w in ["code", "python", "javascript", "flask", "error", "debug"]):
        return MODEL_MAP["coding"]
    if any(w in q for w in ["creative", "story", "caption", "cinematic", "poster", "logo"]):
        return MODEL_MAP["creative"]
    if any(w in q for w in ["quick", "fast", "short"]):
        return MODEL_MAP["fast"]
    return os.environ.get("SAIVEX_DEFAULT_MODEL", MODEL_MAP["fast"])


def ask_multi_model(message, system_prompt="You are SAIVEX AI.", model=None, max_tokens=1200):
    api_key = get_openrouter_key()
    if not api_key:
        return "OpenRouter API key is missing. Add OPENROUTER_API_KEY."

    selected_model = model or choose_model(message)

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "SAIVEX v1"
            },
            json={
                "model": selected_model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            },
            timeout=70,
            verify=False
        )
        data = response.json()
        if "choices" not in data:
            print("Multi-model error:", data)
            return "Model request failed. Check terminal logs."
        return data["choices"][0]["message"]["content"]
    except Exception as error:
        print("Multi-model exception:", error)
        return "Multi-model AI failed. Check internet/API settings."
