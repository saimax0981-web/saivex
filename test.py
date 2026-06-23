import os

from speak import speak

from voice import listen


speak("Hello Sai Venkat.")

speak("I am Saivex.")

command = listen()


if "chrome" in command:

    speak("Opening Chrome Sai Venkat")

    os.system("start chrome")


elif "notepad" in command:

    speak("Opening Notepad")

    os.system("start notepad")


elif "calculator" in command:

    speak("Opening Calculator")

    os.system("start calc")


else:

    speak("Sorry Sai Venkat. Command not found.")