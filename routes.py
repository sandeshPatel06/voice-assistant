from flask import Flask, render_template, request, jsonify
from config import assistant_running, command_history, SECRET_KEY, API_KEY, voice_enabled
from commands import process_command
from database import load_conversation_history, clear_conversation_history
from audio import take_command, speak, wish_me
from ml import train_intent_classifier
import threading

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/')
def index():
    """Render the main web interface"""
    return render_template('index.html', history=command_history, api_key=API_KEY, voice_enabled=voice_enabled)

@app.route('/command', methods=['POST'])
def handle_command():
    """Handle commands from the web interface or smartwatch"""
    if request.headers.get('X-API-Key') != API_KEY:
        logging.info(f"Received X-API-Key: {request.headers.get('X-API-Key')}, Expected: {API_KEY}")
        return jsonify({'error': 'Unauthorized'}), 401
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

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    clear_conversation_history()
    return jsonify({'status': 'History cleared'})

@app.route('/toggle_voice', methods=['POST'])
def toggle_voice():
    """Toggle voice input on/off"""
    global voice_enabled
    voice_enabled = not voice_enabled
    status = 'Voice input enabled' if voice_enabled else 'Voice input disabled'
    return jsonify({'status': status, 'voice_enabled': voice_enabled})

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