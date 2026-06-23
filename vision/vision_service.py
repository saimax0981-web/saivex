import os
import re
import base64
import urllib3
import requests
from PIL import Image, ImageStat

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VISION_MODEL = os.environ.get(
    "SAIVEX_VISION_MODEL",
    "qwen/qwen2.5-vl-72b-instruct"
)


def get_openrouter_key():
    key = os.environ.get("OPENROUTER_API_KEY")

    if key:
        return key

    try:
        import ai
        for name in ["OPENROUTER_API_KEY", "API_KEY", "OPENAI_API_KEY"]:
            value = getattr(ai, name, None)
            if value and "PASTE" not in value:
                return value
    except Exception:
        pass

    try:
        with open("ai.py", "r", encoding="utf-8") as file:
            text = file.read()

        match = re.search(
            r"(sk-or-[A-Za-z0-9_\-]+|sk-proj-[A-Za-z0-9_\-]+|sk-[A-Za-z0-9_\-]+)",
            text
        )

        if match:
            return match.group(1)
    except Exception:
        pass

    return ""


def image_to_base64(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def local_image_analysis(path, filename):
    image = Image.open(path).convert("RGB")
    width, height = image.size
    stat = ImageStat.Stat(image)
    r, g, b = stat.mean
    brightness = round((r + g + b) / 3, 2)

    if width > height:
        orientation = "landscape"
    elif height > width:
        orientation = "portrait"
    else:
        orientation = "square"

    dominant = "balanced"
    if r > g and r > b:
        dominant = "warm / red-golden tone"
    elif g > r and g > b:
        dominant = "green / natural tone"
    elif b > r and b > g:
        dominant = "blue / cool tone"

    return f"""Local image analysis:
File: {filename}
Resolution: {width} x {height}
Orientation: {orientation}
Brightness: {brightness}
Dominant tone: {dominant}

Note:
Real AI vision could not run, so this is the fallback analysis.
Check your OpenRouter API key, internet connection, model access, or credits.
"""


def analyze_image_with_ai(path, filename, user_question="Explain this image clearly."):
    api_key = get_openrouter_key()

    if not api_key:
        return local_image_analysis(path, filename)

    try:
        image = Image.open(path)
        image_format = image.format.lower() if image.format else "jpeg"

        if image_format == "jpg":
            image_format = "jpeg"

        image_base64 = image_to_base64(path)

        prompt = f"""
You are Saivex Vision, a multimodal AI assistant.

User request:
{user_question}

Analyze the uploaded image clearly.

Return:
1. Short title
2. Clear description
3. Main objects, people, or scene
4. Any visible text
5. If it is a screenshot, explain what is happening
6. If it is code, find possible errors
7. If it is math, solve it step by step
8. If it is a chart or graph, explain the trend
9. If it is historical or Kalinga-related, explain historical or cultural meaning
10. Useful suggestions

Do not identify real people by name.
"""

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Saivex Vision"
            },
            json={
                "model": VISION_MODEL,
                "max_tokens": 1200,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            },
            timeout=90,
            verify=False
        )

        data = response.json()

        if "choices" not in data:
            print("Vision API response:", data)
            return local_image_analysis(path, filename)

        return data["choices"][0]["message"]["content"]

    except Exception as error:
        print("Vision error:", error)
        return local_image_analysis(path, filename)


def answer_question_about_latest_image(image_analysis, question):
    api_key = get_openrouter_key()

    if not api_key:
        return f"""I can answer based on the stored image analysis.

Question:
{question}

Stored image context:
{image_analysis}
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Saivex Vision Chat"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "max_tokens": 800,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Saivex Vision Chat. Answer using the stored image analysis."
                    },
                    {
                        "role": "user",
                        "content": f"Image analysis:\n{image_analysis}\n\nUser question:\n{question}"
                    }
                ]
            },
            timeout=60,
            verify=False
        )

        data = response.json()

        if "choices" not in data:
            print("Vision chat API response:", data)
            return "I could not answer about the image right now."

        return data["choices"][0]["message"]["content"]

    except Exception as error:
        print("Vision chat error:", error)
        return "I could not answer about the image right now."