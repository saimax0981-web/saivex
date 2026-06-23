import requests

API_KEY = "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"

chat_histories = {}


def ask_ai(question, user_id="default", user_name="User", memories=""):

    if user_id not in chat_histories:

        chat_histories[user_id] = [

            {
                "role": "system",
                "content": f"""
You are Saivex.

You are a smart AI assistant.

The current user's name is {user_name}.

Always greet and help this user personally.

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

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": chat_histories[user_id]
    }

    try:

        response = requests.post(url, headers=headers, json=data)

        result = response.json()

        if "choices" not in result:

            print(result)

            return "Sorry, I could not connect to the AI server."

        answer = result["choices"][0]["message"]["content"]

        chat_histories[user_id].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer

    except Exception as e:

        print(e)

        return "Something went wrong."