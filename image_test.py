from image_gen import generate_image


ok = generate_image(

    "A powerful king Kharavela sitting on a golden throne, cinematic lighting, Kalinga empire, ultra detailed, 4k wallpaper"

)


if ok:

    print("Image saved as generated.png")

else:

    print("Failed")