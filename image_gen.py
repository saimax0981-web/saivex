import urllib.parse
import random

def improve_prompt(prompt, style="cinematic", ratio="1:1"):
    style_map = {
        "cinematic": "cinematic lighting, dramatic shadows, premium movie poster look",
        "realistic": "photorealistic, DSLR quality, natural lighting, realistic textures",
        "anime": "high quality anime illustration, clean line art, dynamic pose",
        "logo": "professional logo design, premium brand identity, vector-like sharpness",
        "wallpaper": "4K wallpaper composition, epic background",
        "fantasy": "epic fantasy art, magical atmosphere",
        "concept": "professional concept art, game cinematic quality"
    }

    ratio_map = {
        "1:1": "square 1:1 composition",
        "16:9": "wide 16:9 cinematic wallpaper composition",
        "9:16": "vertical 9:16 mobile wallpaper composition",
        "4:5": "portrait 4:5 social media composition"
    }

    return f"""
{prompt}

Image style:
{style_map.get(style, style_map["cinematic"])}

Aspect ratio:
{ratio_map.get(ratio, ratio_map["1:1"])}

Quality:
ultra high quality, sharp details, rich colors, professional composition,
clean textures, strong depth, no blur, no distortion, no watermark,
no text artifacts, no bad anatomy, no low quality,no poorly drawn, higly detailed,16k resolution, dslr quality,natural lighting

If the subject is Kalinga or Kharavela:
ancient Kalinga empire, royal golden atmosphere, heroic king mood,
majestic Indian architecture, lions, elephants, banners, cinematic empire energy.
"""

def get_size_from_ratio(ratio):
    if ratio == "16:9":
        return 1280, 720
    if ratio == "9:16":
        return 720, 1280
    if ratio == "4:5":
        return 1024, 1280
    return 1024, 1024

def generate_image(prompt, style="cinematic", ratio="1:1"):
    width, height = get_size_from_ratio(ratio)
    final_prompt = improve_prompt(prompt, style, ratio)
    encoded_prompt = urllib.parse.quote(final_prompt)
    seed = random.randint(10000, 999999)
    return (
        "https://image.pollinations.ai/prompt/"
        + encoded_prompt
        + f"?model=flux&width={width}&height={height}&seed={seed}&enhance=true&nologo=true"
    )
