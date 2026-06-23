from voice import listen
from ai import ask_ai
from speak import speak
from memory import remember, recall, get_all_memory

print("\n🤖 Saivex Smart Memory Started\n")

speak("Hello Sai Venkat.")
speak("I am Saivex.")


while True:

    question = listen()

    if question == "":

        continue

    q = question.lower()


    if q == "exit":

        speak("Goodbye Sai Venkat.")

        break


    # REMEMBER ANYTHING

    if q.startswith("remember that"):

        text = question[13:].strip()

        key = text.lower()

        remember(key, text)

        answer = "Okay Sai Venkat. I will remember that."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        continue


    # SHOW ALL MEMORIES

    if "what do you remember" in q:

        memory = get_all_memory()

        if len(memory) == 0:

            answer = "I do not remember anything yet."

        else:

            answer = "I remember these things:\n"

            for value in memory.values():

                answer += "\n- " + str(value)

        print("\nSaivex:", answer, "\n")

        speak("I have shown my memories on screen.")

        continue


    # NORMAL AI

    answer = ask_ai(question)

    print("\nSaivex:", answer, "\n")

    speak(answer)