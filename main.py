from flask import Flask
import threading
from audio import wish_me, speak ,take_command
from commands import process_command
from database import load_conversation_history
from ml import train_intent_classifier
from config import assistant_running
from routes import start_server

app = Flask(__name__, template_folder='templates')

def run_assistant():
    """Run the assistant on the main device"""
    global assistant_running
    assistant_running = True
    speak(wish_me())
    load_conversation_history()
    train_intent_classifier()
    while assistant_running:
        query = take_command()
        if query == "None":
            continue
        response = process_command(query)
        speak(response)
        if 'stop listening' in query:
            assistant_running = False

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    run_assistant()