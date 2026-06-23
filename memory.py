import json
import os

FILE = "memory.json"


def load_memory():

    if os.path.exists(FILE):

        with open(FILE, "r") as f:

            return json.load(f)

    return {}


def save_memory(memory):

    with open(FILE, "w") as f:

        json.dump(memory, f, indent=4)


def remember(key, value):

    memory = load_memory()

    memory[key] = value

    save_memory(memory)


def recall(key):

    memory = load_memory()

    return memory.get(key)


def get_all():

    return load_memory()