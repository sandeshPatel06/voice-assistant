from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Email credentials for send_email function
EMAIL_USER = os.getenv('EMAIL_USER', 'your-email@gmail.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'your-password')

# API key for securing /command endpoint
API_KEY = os.getenv('API_KEY', 'jarvis-api-12345')

# Secret key for Flask app
SECRET_KEY = os.getenv('SECRET_KEY', 'jarvis-secret-67890')

# Global state for assistant control
assistant_running = False
voice_enabled = True  # Voice input enabled by default

# Command history for web interface and context
command_history = []

# Intent classes for ML classifier
intent_classes = [
    'wikipedia', 'open_youtube', 'open_google', 'open_whatsapp', 'open_gmail',
    'play_music', 'time', 'email', 'stop', 'hello', 'how_are_you', 'fine',
    'open_code', 'reminder', 'weather', 'news', 'joke', 'search', 'location', 'unknown'
]