"""
SAIVEX AI Engine — Deployment Safe Version

Do not hardcode API keys in this file.
Set your key in .env:

OPENROUTER_API_KEY=your-key-here
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

chat_histories = {}


def get_api_key():
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def trim_history(user_id, max_messages=24):
    if user_id not in chat_histories:
        return

    history = chat_histories[user_id]

    if len(history) > max_messages:
        system_prompt = history[0]
        recent = history[-(max_messages - 1):]
        chat_histories[user_id] = [system_prompt] + recent


def ask_ai(question, user_id="default", user_name="User", memories=""):
    api_key = get_api_key()

    if not api_key:
        return "OpenRouter API key is missing. Add OPENROUTER_API_KEY in your .env file."

    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {
                "role": "system",
                "content": f"""
You are SAIVEX.

You are a smart, friendly AI assistant.

The current user's name is {user_name}.

Always help this user personally and clearly.

User memories:
{memories}
"""
            }
        ]

    chat_histories[user_id].append(
        {
            "role": "user",
            "content": question
        }
    )

    trim_history(user_id)

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("SAIVEX_PUBLIC_URL", "http://127.0.0.1:5000"),
        "X-Title": "SAIVEX"
    }

    data = {
        "model": os.getenv("SAIVEX_DEFAULT_MODEL", "openai/gpt-4o-mini"),
        "messages": chat_histories[user_id],
        "max_tokens": int(os.getenv("SAIVEX_MAX_TOKENS", "1200"))
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=70)
        result = response.json()

        if "choices" not in result:
            print("AI API error:", result)
            return "Sorry, I could not connect to the AI server."

        answer = result["choices"][0]["message"]["content"]

        chat_histories[user_id].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        trim_history(user_id)

        return answer

    except Exception as error:
        print("AI request failed:", error)
        return "Something went wrong while connecting to the AI."
