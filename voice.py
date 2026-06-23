import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import speech_recognition as sr


def listen():

    fs = 16000

    seconds = 5

    print("\n🎤 Listening...")

    recording = sd.rec(

        int(seconds * fs),

        samplerate=fs,

        channels=1,

        dtype='int16'

    )

    sd.wait()

    write(

        "voice.wav",

        fs,

        recording

    )

    recognizer = sr.Recognizer()

    try:

        with sr.AudioFile("voice.wav") as source:

            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)

        print("You said:", text)

        return text

    except Exception as e:

        print("Error:", e)

        return ""