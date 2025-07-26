import os
import datetime
import speech_recognition as sr
from gtts import gTTS
import pygame
import wikipedia
import webbrowser
import subprocess
import smtplib
from flask import Flask, request, jsonify
import threading
import uuid
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app for future smartwatch integration
app = Flask(__name__)

# Initialize pygame mixer for audio playback
pygame.mixer.init()

def speak(audio, lang='en'):
    """Convert text to speech using gTTS and play with pygame"""
    try:
        tts = gTTS(text=audio, lang=lang)
        temp_file = f"temp_{uuid.uuid4()}.mp3"
        tts.save(temp_file)
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # Wait for playback to finish
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
        audio = r.listen(source, timeout=5)
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

# Flask endpoint for future smartwatch commands
@app.route('/command', methods=['POST'])
def handle_command():
    data = request.json
    query = data.get('query', '').lower()
    response = process_command(query)
    return jsonify({'response': response})

def process_command(query):
    """Process voice or text commands"""
    if 'wikipedia' in query:
        query = query.replace("wikipedia", "").strip()
        try:
            results = wikipedia.summary(query, sentences=2)
            return f"According to Wikipedia: {results}"
        except Exception as e:
            logging.error(f"Wikipedia error: {e}")
            return "Sorry, I couldn't find that on Wikipedia."

    elif 'open youtube' in query:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"

    elif 'open google' in query:
        webbrowser.open("https://www.google.com")
        return "Opening Google"

    elif 'open whatsapp' in query:
        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp"

    elif 'open gmail' in query:
        webbrowser.open("https://mail.google.com")
        return "Opening Gmail"

    elif 'play music' in query:
        music_dir = Path.home() / 'Music'  # Cross-platform music directory
        try:
            songs = [f for f in music_dir.glob('*') if f.is_file()]
            if songs:
                if os.name == 'nt':
                    subprocess.run(['start', '', str(songs[0])], shell=True, check=True)
                else:
                    subprocess.run(['xdg-open', str(songs[0])], check=True)
                return "Playing music"
            return "No music files found"
        except Exception as e:
            logging.error(f"Music error: {e}")
            return "Failed to play music"

    elif 'the time' in query:
        str_time = datetime.datetime.now().strftime("%H:%M:%S")
        return f"The time is {str_time}"

    elif 'send email' in query:
        content = query.replace("send email", "").strip()
        to = "recipient-email@gmail.com"  # Update recipient
        return send_email(to, content)

    elif 'stop listening' in query:
        return "Stopping. Have a nice day!"

    elif 'hello' in query:
        return "Hello sir..."

    elif 'how are you' in query or 'how r u' in query:
        return "I am fine, and you sir?"

    elif 'fine' in query or 'good' in query:
        return "That is good to hear."

    elif 'open code' in query:
        code_path = "code"  # Update with editor path (e.g., 'code' for VS Code)
        return open_application(code_path)

    elif 'set reminder' in query:
        reminder = query.replace("set reminder", "").strip()
        return f"Reminder set for: {reminder}"

    elif 'weather' in query:
        webbrowser.open("https://www.weather.com")
        return "Checking the weather..."

    elif 'news' in query:
        webbrowser.open("https://news.google.com")
        return "Fetching the latest news..."

    elif 'joke' in query:
        return "Why don't scientists trust atoms? Because they make up everything!"

    elif 'search' in query:
        query = query.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Searching for {query}"

    elif 'location' in query:
        query = query.replace("location", "").strip()
        webbrowser.open(f"https://www.google.com/maps/place/{query}")
        return f"Looking up location {query}"

    return "I didn't understand that command."

def run_assistant():
    """Run the assistant on the main device"""
    speak(wish_me())
    while True:
        query = take_command()
        if query == "None":
            continue
        response = process_command(query)
        speak(response)
        if 'stop listening' in query:
            break

def start_server():
    """Start Flask server for future smartwatch integration"""
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    # Run the assistant
    run_assistant()