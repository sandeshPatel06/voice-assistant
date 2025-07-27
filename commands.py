import wikipedia
import webbrowser
import subprocess
import smtplib
from pathlib import Path
import datetime
import logging
from config import command_history, EMAIL_USER, EMAIL_PASS
from database import save_conversation, get_context
from ml import predict_intent
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_email(to, content):
    """Send an email using SMTP"""
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to, content)
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
    """Process voice or text commands with ML and context"""
    intent = predict_intent(query)
    context = get_context()
    context_str = " ".join([f"Q: {q} A: {r}" for q, r in context])

    command_history.append({'query': query, 'response': ''})
    save_conversation(query, '', intent)

    if 'previous' in query or 'last' in query:
        if context:
            response = f"Based on our last conversation: {context[0][1]}"
            command_history[-1]['response'] = response
            save_conversation(query, response, intent)
            return response

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
        response = "I didn't understand that command."

    command_history[-1]['response'] = response
    save_conversation(query, response, intent)
    return response