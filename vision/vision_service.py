
import os
import re
import base64
import urllib3
import requests
from PIL import Image, ImageStat

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VISION_MODEL = os.environ.get("SAIVEX_VISION_MODEL", "qwen/qwen2.5-vl-72b-instruct")


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


def compress_image_for_api(path):
    image = Image.open(path).convert("RGB")
    max_side = 1280
    width, height = image.size

    if max(width, height) > max_side:
        if width >= height:
            new_width = max_side
            new_height = int(height * (max_side / width))
        else:
            new_height = max_side
            new_width = int(width * (max_side / height))
        image = image.resize((new_width, new_height))

    temp_path = path + "_vision.jpg"
    image.save(temp_path, "JPEG", quality=82)
    return temp_path, "jpeg"


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

    return f"""I can see the image file, but the online Vision AI could not complete the analysis.

Local fallback details:
File: {filename}
Resolution: {width} x {height}
Orientation: {orientation}
Brightness: {brightness}
Dominant tone: {dominant}

To get ChatGPT-like image understanding:
1. Check OPENROUTER_API_KEY
2. Check model access/credits
3. Try a smaller image
4. Try setting SAIVEX_VISION_MODEL to another supported vision model
"""


def analyze_image_with_ai(path, filename, user_question="Explain this image clearly."):
    api_key = get_openrouter_key()
    if not api_key:
        return local_image_analysis(path, filename)

    try:
        compressed_path, image_format = compress_image_for_api(path)
        image_base64 = image_to_base64(compressed_path)

        prompt = f"""
You are SAIVEX Vision, a ChatGPT-like multimodal AI assistant.

User request:
{user_question}

Analyze the uploaded image deeply and naturally.

Rules:
- Do NOT identify real people by name.
- If a person is visible, describe them generally.
- If it is a screenshot, explain what the screen shows.
- If it has text, read and summarize the visible text.
- If it is a code screenshot, identify likely issues.
- If it is math, solve it step by step.
- If it is a chart or graph, explain the trend.
- If it is historical or Kalinga-related, explain cultural/historical meaning.
- Avoid boring metadata unless asked.

Return a helpful answer like ChatGPT Vision.
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
                "max_tokens": 900,
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

    if not image_analysis:
        return "Please upload an image first using the 👁️ button or Camera button."

    if not api_key:
        return f"""I can answer based on stored image context.

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
                "max_tokens": 700,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are SAIVEX Vision Chat. Answer only using the stored image analysis. Be clear and natural."
                    },
                    {
                        "role": "user",
                        "content": f"Stored image analysis:\\n{image_analysis}\\n\\nUser question:\\n{question}"
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
