import sqlite3
from pathlib import Path
import datetime
from config import command_history

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
    cursor.execute("DELETE FROM conversations WHERE timestamp < ?", 
                  ((datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),))
    conn.commit()
    cursor.execute("SELECT query, response FROM conversations ORDER BY timestamp DESC LIMIT 50")
    command_history[:] = [{'query': row[0], 'response': row[1]} for row in cursor.fetchall()]

def save_conversation(query, response, intent):
    """Save conversation to SQLite"""
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO conversations (timestamp, query, response, intent) VALUES (?, ?, ?, ?)",
                  (timestamp, query, response, intent))
    conn.commit()

def clear_conversation_history():
    """Clear conversation history"""
    cursor.execute("DELETE FROM conversations")
    conn.commit()
    global command_history
    command_history[:] = []

def get_context():
    """Get recent conversation context (last 3 interactions)"""
    cursor.execute("SELECT query, response FROM conversations ORDER BY timestamp DESC LIMIT 3")
    return cursor.fetchall()