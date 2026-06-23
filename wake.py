import sounddevice as sd
import numpy as np

print("🎤 Waiting for wake word...")

while True:

    audio = sd.rec(

        int(2 * 16000),

        samplerate=16000,

        channels=1,

        dtype='int16'

    )

    sd.wait()

    print("Listening...")

    text = input()

    if "hey saivex" in text.lower():

        print("\n✅ Wake word detected!")

        break