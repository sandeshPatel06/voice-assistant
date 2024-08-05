
# Voice Assistant

This is a simple voice assistant program built with Python. It can perform various tasks such as searching Wikipedia, opening websites, playing music, telling the time, sending emails, and more.

## Features

- **Text-to-Speech**: Uses `pyttsx3` for converting text to speech.
- **Speech Recognition**: Uses `SpeechRecognition` for recognizing voice commands.
- **Wikipedia Search**: Searches Wikipedia and returns summaries.
- **Open Websites**: Opens various websites like YouTube, Google, Stack Overflow, etc.
- **Play Music**: Plays music from a specified directory.
- **Tell Time**: Tells the current time.
- **Send Email**: Sends an email using SMTP.
- **Weather and News**: Opens websites to check weather and news.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/sandeshPatel06/personalJarvisAi.git
cd voice-assistant
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the `main.py` file:

```bash
python main.py
```

2. The assistant will start listening for your commands. You can try commands like:

- "open YouTube"
- "search Wikipedia for Python"
- "play music"
- "tell me the time"
- "send an email"
- "check the weather"

## Configuration

- To send emails, you need to enable low-security apps in your Gmail account and replace `your-email@gmail.com` and `your-password` in the `send_email` function with your email and password.
- Change the `music_dir` variable to your music directory.
- Change the `code_path` variable to the path of your code editor.

## Requirements

- Python 3.x
- `pyttsx3`
- `SpeechRecognition`
- `wikipedia-api`

## License
 
This project is licensed under the MIT License.
