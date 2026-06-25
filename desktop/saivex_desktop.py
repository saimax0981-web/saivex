import webbrowser
import subprocess
import time
import os
import sys

def start_server():
    return subprocess.Popen([sys.executable, "app.py"], cwd=os.getcwd())

if __name__ == "__main__":
    print("Starting SAIVEX Desktop...")
    server = start_server()
    time.sleep(3)
    webbrowser.open("http://127.0.0.1:5000")
    try:
        server.wait()
    except KeyboardInterrupt:
        server.terminate()
