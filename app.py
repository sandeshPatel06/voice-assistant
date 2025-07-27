import os
import datetime
import sqlite3
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
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import requests
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Global state
assistant_running = False
command_history = []
vectorizer = None
classifier = None
intent_classes = ['wikipedia', 'open_youtube', 'open_google', 'open_whatsapp', 'open_gmail', 'play_music', 'time', 'email', 'stop', 'hello', 'how_are_you', 'fine', 'open_code', 'reminder', 'weather', 'news', 'joke', 'search', 'location', 'unknown']

# SQLite setup
db_path = Path('jarvis_conversations.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  query TEXT,
                  response TEXT,
                  intent TEXT)''')
conn.commit()

def load_conversation_history():
    """Load conversation history from SQLite"""
    global command_history
    cursor.execute("SELECT query, response FROM conversations ORDER BY timestamp DESC LIMIT 50")
    command_history = [{'query': row[0], 'response': row[1]} for row in cursor.fetchall()]

def save_conversation(query, response, intent):
    """Save conversation to SQLite"""
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO conversations (timestamp, query, response, intent) VALUES (?, ?, ?, ?)",
                  (timestamp, query, response, intent))
    conn.commit()

def train_intent_classifier():
    """Train or load a simple intent classifier"""
    global vectorizer, classifier
    model_path = Path('intent_classifier.pkl')
    vectorizer_path = Path('vectorizer.pkl')
    
    # Check if pre-trained model exists
    if model_path.exists() and vectorizer_path.exists():
        with open(model_path, 'rb') as f:
            classifier = pickle.load(f)
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)
        return

    # Fetch training data from database
    cursor.execute("SELECT query, intent FROM conversations WHERE intent != 'unknown'")
    data = cursor.fetchall()
    if len(data) < 10:  # Minimum data for training
        logging.warning("Not enough data to train classifier")
        return

    queries, intents = zip(*data)
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(queries)
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(X, intents)

    # Save model and vectorizer
    with open(model_path, 'wb') as f:
        pickle.dump(classifier, f)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)

def predict_intent(query):
    """Predict intent for a query using the trained classifier"""
    if vectorizer is None or classifier is None:
        return 'unknown'
    X = vectorizer.transform([query])
    return classifier.predict(X)[0]

def get_context():
    """Get recent conversation context (last 3 interactions)"""
    cursor.execute("SELECT query, response FROM conversations ORDER BY timestamp DESC LIMIT 3")
    return cursor.fetchall()

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
        logging.info("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=3)
        r.energy_threshold = 300
        logging.info(f"Microphone device: {source.device_index}")
        logging.info("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
            logging.info("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            logging.info(f"User said: {query}")
            return query.lower()
        except sr.WaitTimeoutError:
            logging.warning("No speech detected within 10 seconds.")
            speak("No speech detected. Please try again.")
            return "None"
        except sr.UnknownValueError:
            logging.warning("Could not understand the audio.")
            speak("I couldn't understand that. Please try again.")
            return "None"
        except sr.RequestError as e:
            logging.error(f"Speech recognition error: {e}")
            speak("There was an error with speech recognition.")
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

def call_grok_api(query, context):
    """Call xAI's Grok API for complex queries (optional)"""
    try:
        # Replace with your xAI API key and endpoint
        api_key = 'xai-'
        url = 'https://api.x.ai/grok'
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {'query': query, 'context': context}
        response = requests.post(url, json=data, headers=headers)
        return response.json().get('response', 'Error calling Grok API')
    except Exception as e:
        logging.error(f"Grok API error: {e}")
        return "Sorry, I couldn't process that request with AI."

def process_command(query):
    """Process voice or text commands with ML and context"""
    global command_history
    intent = predict_intent(query)
    context = get_context()
    context_str = " ".join([f"Q: {q} A: {r}" for q, r in context])

    command_history.append({'query': query, 'response': ''})
    save_conversation(query, '', intent)  # Save query with predicted intent
    train_intent_classifier()  # Update classifier with new data

    # Check for contextual follow-up
    if 'previous' in query or 'last' in query:
        if context:
            response = f"Based on our last conversation: {context[0][1]}"
            command_history[-1]['response'] = response
            save_conversation(query, response, intent)
            return response

    # Handle known intents
    if intent == 'wikipedia' or 'wikipedia' in query:
        query = query.replace("wikipedia", "").strip()
        try:
            results = wikipedia.summary(query, sentences=2)
            response = f"According to Wikipedia: {results}"
        except Exception as e:
            logging.error(f"Wikipedia error: {e}")
            response = "Sorry, I couldn't find that on Wikipedia."
    elif intent == 'open_youtube' or 'open youtube' in query:
        webbrowser.open("https://www.youtube.com")
        response = "Opening YouTube"
    elif intent == 'open_google' or 'open google' in query:
        webbrowser.open("https://www.google.com")
        response = "Opening Google"
    elif intent == 'open_whatsapp' or 'open whatsapp' in query:
        webbrowser.open("https://web.whatsapp.com")
        response = "Opening WhatsApp"
    elif intent == 'open_gmail' or 'open gmail' in query:
        webbrowser.open("https://mail.google.com")
        response = "Opening Gmail"
    elif intent == 'play_music' or 'play music' in query:
        music_dir = Path.home() / 'Music'
        try:
            songs = [f for f in music_dir.glob('*') if f.is_file()]
            if songs:
                if os.name == 'nt':
                    subprocess.run(['start', '', str(songs[0])], shell=True, check=True)
                else:
                    subprocess.run(['xdg-open', str(songs[0])], check=True)
                response = "Playing music"
            else:
                response = "No music files found"
        except Exception as e:
            logging.error(f"Music error: {e}")
            response = "Failed to play music"
    elif intent == 'time' or 'the time' in query:
        str_time = datetime.datetime.now().strftime("%H:%M:%S")
        response = f"The time is {str_time}"
    elif intent == 'email' or 'send email' in query:
        content = query.replace("send email", "").strip()
        to = "recipient-email@gmail.com"  # Update recipient
        response = send_email(to, content)
    elif intent == 'stop' or 'stop listening' in query:
        response = "Stopping. Have a nice day!"
    elif intent == 'hello' or 'hello' in query:
        response = "Hello sir..."
    elif intent == 'how_are_you' or 'how are you' in query or 'how r u' in query:
        response = "I am fine, and you sir?"
    elif intent == 'fine' or 'fine' in query or 'good' in query:
        response = "That is good to hear."
    elif intent == 'open_code' or 'open code' in query:
        code_path = "code"  # Update with editor path
        response = open_application(code_path)
    elif intent == 'reminder' or 'set reminder' in query:
        reminder = query.replace("set reminder", "").strip()
        response = f"Reminder set for: {reminder}"
    elif intent == 'weather' or 'weather' in query:
        webbrowser.open("https://www.weather.com")
        response = "Checking the weather..."
    elif intent == 'news' or 'news' in query:
        webbrowser.open("https://news.google.com")
        response = "Fetching the latest news..."
    elif intent == 'joke' or 'joke' in query:
        response = "Why don't scientists trust atoms? Because they make up everything!"
    elif intent == 'search' or 'search' in query:
        query = query.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        response = f"Searching for {query}"
    elif intent == 'location' or 'location' in query:
        query = query.replace("location", "").strip()
        webbrowser.open(f"https://www.google.com/maps/place/{query}")
        response = f"Looking up location {query}"
    else:
        # Fallback to Grok API for complex queries (optional)
        response = call_grok_api(query, context_str) if 'xai-' != 'xai-' else "I didn't understand that command."

    command_history[-1]['response'] = response
    save_conversation(query, response, intent)
    return response

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

def start_server():
    """Start Flask server"""
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Start Flask server
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    # Run the assistant
    run_assistant()