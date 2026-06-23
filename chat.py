from ai import ask_ai
from speak import speak
from memory import remember, recall, get_all

print("\n🤖 Saivex Smart Memory Started\n")

welcome = "Hello Sai Venkat. I am Saivex."

print("Saivex:", welcome)

speak(welcome)


while True:

    question = input("You: ")

    q = question.lower()


    if q == "exit":

        answer = "Goodbye Sai Venkat."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        break


    # NAME

    if "my name is" in q:

        name = question.split("is")[-1].strip()

        remember("name", name)

        answer = f"Okay Sai Venkat. I will remember your name."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        continue


    # FAVORITE KING

    if "favorite king is" in q:

        king = question.split("is")[-1].strip()

        remember("favorite_king", king)

        answer = "Okay Sai Venkat. I will remember your favorite king."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        continue


    # LOVE

    if "i love" in q:

        love = question.replace("I love", "").replace("i love", "").strip()

        remember("love", love)

        answer = "Okay Sai Venkat. I will remember that."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        continue


    # WHAT IS MY NAME

    if "what is my name" in q:

        name = recall("name")

        if name:

            answer = f"Your name is {name}."

        else:

            answer = "I don't know your name yet."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        continue


    # WHAT IS MY FAVORITE KING

    if "favorite king" in q:

        king = recall("favorite_king")

        if king:

            answer = f"Your favorite king is {king}."

        else:

            answer = "I don't know your favorite king yet."

        print("\nSaivex:", answer, "\n")

        speak(answer)

        continue


    # WHAT DO YOU REMEMBER

    if "what do you remember" in q:

        memory = get_all()

        print("\nSaivex:\n")

        if len(memory) == 0:

            print("I do not remember anything.")

        else:

            for key, value in memory.items():

                print(f"{key} : {value}")

        print()

        speak("I have shown my memories on screen.")

        continue


    # NORMAL AI

    answer = ask_ai(question)

    print("\nSaivex:", answer, "\n")

try:

    speak(str(answer))

except Exception as e:

    print("Voice Error:", e)