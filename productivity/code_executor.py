import subprocess
import tempfile
import os

BLOCKED_WORDS = ["import os", "import subprocess", "import socket", "import shutil", "open(", "__import__", "eval(", "exec("]

def execute_python_code(code):
    lower_code = code.lower()
    for word in BLOCKED_WORDS:
        if word in lower_code:
            return "Blocked for safety. This code uses a restricted command."
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as file:
            file.write(code)
            temp_path = file.name
        result = subprocess.run(["python", temp_path], capture_output=True, text=True, timeout=5)
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += "\nERROR:\n" + result.stderr
        return output.strip() or "Code executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Code execution stopped because it took too long."
    except Exception as error:
        return f"Code execution error: {error}"
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
