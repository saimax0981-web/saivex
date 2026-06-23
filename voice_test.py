from voice import listen

print("🎤 Voice Test Started")
print("Say 'exit' to stop.\n")

while True:

    text = listen()

    print()

    print("Result:", text)

    print()

    if text.lower() == "exit":

        print("Voice Test Ended.")

        break