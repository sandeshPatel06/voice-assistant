import os
import datetime
import speech_recognition as sr
from gtts import gTTS
import pygame
import wikipedia
import webbrowser
import subprocess
import smtplib
from flask import Flask, request, jsonify, render_template
import threading
import uuid
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Global state
assistant_running = False
command_history = []

def speak(audio, lang='en'):
    """Convert text to speech using gTTS and play with pygame"""
    try:
        tts = gTTS(text=audio, lang=lang)
        temp_file = f"temp_{uuid.uuid4()}.mp3"
        tts.save(temp_file)
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        os.remove(temp_file)
    except Exception as e:
        logging.error(f"Speech error: {e}")

def wish_me():
    """Wish the user based on the time of day"""
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if 0 <= hour < 12 else "Good afternoon" if 12 <= hour < 15 else "Good evening"
    return f"{greeting}. Hello sir, how may I help you?"

def take_command():
    """Take voice commands from the user"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source, timeout=20)
        try:
            logging.info("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            logging.info(f"User said: {query}")
            return query.lower()
        except Exception as e:
            logging.error(f"Recognition error: {e}")
            speak("Say that again please...")
            return "None"

def send_email(to, content):
    """Send an email using SMTP"""
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login('your-email@gmail.com', 'your-password')  # Update credentials
        server.sendmail('your-email@gmail.com', to, content)
        server.close()
        return "Email has been sent!"
    except Exception as e:
        logging.error(f"Email error: {e}")
        return "I am not able to send this email"

def open_application(app_name):
    """Open applications cross-platform"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['start', '', app_name], shell=True, check=True)
        else:  # Linux
            subprocess.run(['xdg-open', app_name], check=True)
        return f"Opening {app_name}"
    except Exception as e:
        logging.error(f"App open error: {e}")
        return f"Failed to open {app_name}"

def process_command(query):
    """Process voice or text commands"""
    global command_history
    command_history.append({'query': query, 'response': ''})
    if 'wikipedia' in query:
        query = query.replace("wikipedia", "").strip()
        try:
            results = wikipedia.summary(query, sentences=2)
            command_history[-1]['response'] = f"According to Wikipedia: {results}"
            return command_history[-1]['response']
        except Exception as e:
            logging.error(f"Wikipedia error: {e}")
            command_history[-1]['response'] = "Sorry, I couldn't find that on Wikipedia."
            return command_history[-1]['response']

    elif 'open youtube' in query:
        webbrowser.open("https://www.youtube.com")
        command_history[-1]['response'] = "Opening YouTube"
        return command_history[-1]['response']

    elif 'open google' in query:
        webbrowser.open("https://www.google.com")
        command_history[-1]['response'] = "Opening Google"
        return command_history[-1]['response']

    elif 'open whatsapp' in query:
        webbrowser.open("https://web.whatsapp.com")
        command_history[-1]['response'] = "Opening WhatsApp"
        return command_history[-1]['response']

    elif 'open gmail' in query:
        webbrowser.open("https://mail.google.com")
        command_history[-1]['response'] = "Opening Gmail"
        return command_history[-1]['response']

    elif 'play music' in query:
        music_dir = Path.home() / 'Music'
        try:
            songs = [f for f in music_dir.glob('*') if f.is_file()]
            if songs:
                if os.name == 'nt':
                    subprocess.run(['start', '', str(songs[0])], shell=True, check=True)
                else:
                    subprocess.run(['xdg-open', str(songs[0])], check=True)
                command_history[-1]['response'] = "Playing music"
                return command_history[-1]['response']
            command_history[-1]['response'] = "No music files found"
            return command_history[-1]['response']
        except Exception as e:
            logging.error(f"Music error: {e}")
            command_history[-1]['response'] = "Failed to play music"
            return command_history[-1]['response']

    elif 'the time' in query:
        str_time = datetime.datetime.now().strftime("%H:%M:%S")
        command_history[-1]['response'] = f"The time is {str_time}"
        return command_history[-1]['response']

    elif 'send email' in query:
        content = query.replace("send email", "").strip()
        to = "recipient-email@gmail.com"  # Update recipient
        command_history[-1]['response'] = send_email(to, content)
        return command_history[-1]['response']

    elif 'stop listening' in query:
        command_history[-1]['response'] = "Stopping. Have a nice day!"
        return command_history[-1]['response']

    elif 'hello' in query:
        command_history[-1]['response'] = "Hello sir..."
        return command_history[-1]['response']

    elif 'how are you' in query or 'how r u' in query:
        command_history[-1]['response'] = "I am fine, and you sir?"
        return command_history[-1]['response']

    elif 'fine' in query or 'good' in query:
        command_history[-1]['response'] = "That is good to hear."
        return command_history[-1]['response']

    elif 'open code' in query:
        code_path = "code"  # Update with editor path
        command_history[-1]['response'] = open_application(code_path)
        return command_history[-1]['response']

    elif 'set reminder' in query:
        reminder = query.replace("set reminder", "").strip()
        command_history[-1]['response'] = f"Reminder set for: {reminder}"
        return command_history[-1]['response']

    elif 'weather' in query:
        webbrowser.open("https://www.weather.com")
        command_history[-1]['response'] = "Checking the weather..."
        return command_history[-1]['response']

    elif 'news' in query:
        webbrowser.open("https://news.google.com")
        command_history[-1]['response'] = "Fetching the latest news..."
        return command_history[-1]['response']

    elif 'joke' in query:
        command_history[-1]['response'] = "Why don't scientists trust atoms? Because they make up everything!"
        return command_history[-1]['response']

    elif 'search' in query:
        query = query.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        command_history[-1]['response'] = f"Searching for {query}"
        return command_history[-1]['response']

    elif 'location' in query:
        query = query.replace("location", "").strip()
        webbrowser.open(f"https://www.google.com/maps/place/{query}")
        command_history[-1]['response'] = f"Looking up location {query}"
        return command_history[-1]['response']

    command_history[-1]['response'] = "I didn't understand that command."
    return command_history[-1]['response']

def run_assistant():
    """Run the assistant on the main device"""
    global assistant_running
    assistant_running = True
    speak(wish_me())
    while assistant_running:
        query = take_command()
        if query == "None":
            continue
        response = process_command(query)
        speak(response)
        if 'stop listening' in query:
            assistant_running = False

@app.route('/')
def index():
    """Render the main web interface"""
    return render_template('index.html', history=command_history)

@app.route('/command', methods=['POST'])
def handle_command():
    """Handle commands from the web interface or smartwatch"""
    data = request.json
    query = data.get('query', '').lower()
    response = process_command(query)
    return jsonify({'response': response})

@app.route('/start', methods=['POST'])
def start_assistant():
    """Start the assistant"""
    global assistant_running
    if not assistant_running:
        threading.Thread(target=run_assistant, daemon=True).start()
        return jsonify({'status': 'Assistant started'})
    return jsonify({'status': 'Assistant already running'})

@app.route('/stop', methods=['POST'])
def stop_assistant():
    """Stop the assistant"""
    global assistant_running
    assistant_running = False
    process_command('stop listening')
    return jsonify({'status': 'Assistant stopped'})

def start_server():
    """Start Flask server"""
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Start Flask server
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    # Run the assistant
    run_assistant()