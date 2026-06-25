import os
import time
import requests

chat_histories = {}


DEFAULT_MODELS = [
    os.environ.get("SAIVEX_DEFAULT_MODEL", "openai/gpt-4o-mini"),
    "qwen/qwen-2.5-7b-instruct",
    "google/gemini-2.0-flash-001",
]


def get_api_key():
    # Main key name
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key

    # Backward-compatible names
    for env_name in ["SAIVEX_OPENROUTER_KEY", "OPENAI_API_KEY"]:
        key = os.environ.get(env_name, "").strip()
        if key:
            return key

    return ""


def trim_history(user_id, max_messages=24):
    if user_id not in chat_histories:
        return

    history = chat_histories[user_id]
    if len(history) > max_messages:
        system_prompt = history[0]
        recent = history[-(max_messages - 1):]
        chat_histories[user_id] = [system_prompt] + recent


def make_system_prompt(user_name="User", memories=""):
    return f"""
You are SAIVEX.

You are a powerful, friendly AI assistant with a Kalinga-inspired identity.

User name:
{user_name}

User memories:
{memories}

Behavior:
- For casual greetings, reply warmly and briefly.
- For coding, be step-by-step and practical.
- For school topics, explain simply.
- For SAIVEX project work, act like a professional software engineer.
- For PPT/PDF/Website requests, create structured content, not repeated content.
"""


def call_openrouter(messages, model, max_tokens=1200):
    api_key = get_api_key()

    if not api_key:
        return None, "OpenRouter API key is missing. Set OPENROUTER_API_KEY."

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("SAIVEX_PUBLIC_URL", "http://localhost:5000"),
                "X-Title": "SAIVEX"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens
            },
            timeout=70
        )

        data = response.json()

        if "choices" not in data:
            return None, f"AI API error: {data}"

        return data["choices"][0]["message"]["content"], None

    except Exception as error:
        return None, str(error)


def ask_ai(question, user_id="default", user_name="User", memories="", model=None, max_tokens=1200):
    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {
                "role": "system",
                "content": make_system_prompt(user_name=user_name, memories=memories)
            }
        ]

    chat_histories[user_id].append({"role": "user", "content": question})
    trim_history(user_id)

    models = [model] if model else DEFAULT_MODELS

    last_error = None

    for selected_model in models:
        if not selected_model:
            continue

        answer, error = call_openrouter(
            chat_histories[user_id],
            selected_model,
            max_tokens=max_tokens
        )

        if answer:
            chat_histories[user_id].append({"role": "assistant", "content": answer})
            trim_history(user_id)
            return answer

        last_error = error
        print("SAIVEX AI model failed:", selected_model, error)
        time.sleep(0.5)

    return "Sorry, I could not connect to the AI server. Check your API key, model, or internet connection."


def ask_ai_once(prompt, system_prompt="You are SAIVEX.", model=None, max_tokens=1200):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    models = [model] if model else DEFAULT_MODELS

    for selected_model in models:
        answer, error = call_openrouter(messages, selected_model, max_tokens=max_tokens)
        if answer:
            return answer
        print("SAIVEX one-shot model failed:", selected_model, error)

    return "AI request failed."
