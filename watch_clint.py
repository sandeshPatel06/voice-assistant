import requests
import logging
from config import API_KEY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_command_to_server(query):
    """Send command to the server and get response"""
    try:
        headers = {'X-API-Key': API_KEY}
        response = requests.post('http://<server-ip>:5000/command', json={'query': query}, headers=headers)
        return response.json().get('response', 'Error communicating with server')
    except Exception as e:
        logging.error(f"Server communication error: {e}")
        return "Failed to connect to server"

def run_client():
    """Run the smartwatch client"""
    while True:
        query = input("Enter command (or 'quit' to exit): ")  # Placeholder for voice input
        if query == 'quit':
            break
        response = send_command_to_server(query)
        print(response)

if __name__ == "__main__":
    run_client()