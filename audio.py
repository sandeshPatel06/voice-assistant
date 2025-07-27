import datetime
import speech_recognition as sr
from gtts import gTTS
import pygame
import uuid
import logging
import os
import pyaudio
from config import voice_enabled

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
pygame.mixer.init()

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
    if not voice_enabled:
        return "None"  # Skip voice input if disabled
    r = sr.Recognizer()
    try:
        # List available microphones
        mic_list = sr.Microphone.list_microphone_names()
        if not mic_list:
            logging.error("No microphones detected.")
            speak("No microphone detected. Please use text input.")
            return "None"

        # Use Intel® Smart Sound Technology microphone (adjust index based on list)
        mic_index = mic_list.index('Microphone (Intel® Smart Sound Technology (Intel® SST))') if 'Microphone (Intel® Smart Sound Technology (Intel® SST))' in mic_list else 0
        logging.info(f"Available microphones: {mic_list}")
        logging.info(f"Using microphone: {mic_list[mic_index] if mic_index < len(mic_list) else 'None'}")

        with sr.Microphone(device_index=mic_index) as source:
            logging.info("Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source, duration=1.5)  # Shorter duration
            r.energy_threshold = 500  # Higher threshold for clarity
            r.dynamic_energy_threshold = True
            logging.info("Listening...")
            r.pause_threshold = 0.8
            try:
                audio = r.listen(source, timeout=4, phrase_time_limit=4)
                logging.info("Recognizing...")
                query = r.recognize_google(audio, language='en-in')
                logging.info(f"User said: {query}")
                return query.lower()
            except sr.WaitTimeoutError:
                logging.warning("No speech detected within 4 seconds.")
                return "None"
            except sr.UnknownValueError:
                logging.warning("Could not understand the audio.")
                return "None"
            except sr.RequestError as e:
                logging.error(f"Speech recognition error: {e}")
                speak("Speech recognition service is unavailable. Please use text input.")
                return "None"
    except Exception as e:
        logging.error(f"Microphone error: {e}")
        speak("Error accessing microphone. Please check your audio setup and try text input.")
        return "None"