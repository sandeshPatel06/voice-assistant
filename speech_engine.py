"""
Speech engine: handles text-to-speech and speech-to-text with robust
error handling and cross-platform fallbacks.

If PyAudio is not installed or the microphone is unavailable, the
listen() method falls back to text input via the terminal.
"""

import logging
import sys
from typing import Optional

import pyttsx3
import speech_recognition as sr

from config import (
    VOICE_INDEX,
    SPEECH_RATE,
    SPEECH_VOLUME,
    LISTEN_TIMEOUT,
    PHRASE_TIME_LIMIT,
)

log = logging.getLogger("jarvis.speech")


class SpeechEngine:
    """Wraps pyttsx3 (TTS) and SpeechRecognition (STT)."""

    def __init__(self) -> None:
        self._engine: Optional[pyttsx3.Engine] = None
        self._recognizer = sr.Recognizer()
        self.tts_enabled = True
        self.stt_enabled = True  # Set to False if microphone unavailable
        self._check_microphone()
        self._init_tts()

    # ── Micropone / STT availability ────────────────────────────────
    def _check_microphone(self) -> None:
        """Test whether the microphone is accessible."""
        try:
            with sr.Microphone() as source:
                pass  # Just open and close to verify
            log.info("Microphone is available for speech recognition")
        except AttributeError:
            # PyAudio not installed
            log.warning(
                "PyAudio is not installed — speech recognition disabled. "
                "Install with: pip install pyaudio  (requires portaudio)"
            )
            self.stt_enabled = False
        except Exception:
            log.warning("Microphone not accessible — using text input fallback")
            self.stt_enabled = False

    # ── Text-to-Speech ──────────────────────────────────────────────
    def _init_tts(self) -> None:
        try:
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty("voices")
            if voices and VOICE_INDEX < len(voices):
                self._engine.setProperty("voice", voices[VOICE_INDEX].id)
            self._engine.setProperty("rate", SPEECH_RATE)
            self._engine.setProperty("volume", SPEECH_VOLUME)
            log.info("TTS initialised with voice index %d", VOICE_INDEX)
        except Exception:
            log.exception("Failed to initialise TTS engine")
            self.tts_enabled = False
            self._engine = None

    def speak(self, text: str) -> None:
        """Speak *text* aloud. Falls back to printing if TTS is unavailable."""
        print(f"[J.A.R.V.I.S.] {text}")
        if self.tts_enabled and self._engine is not None:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                log.exception("TTS speak failed")
                self._init_tts()  # Try re-initialising once

    # ── Speech-to-Text ──────────────────────────────────────────────
    def listen(self, prompt: Optional[str] = None) -> str:
        """
        Listen for a voice command and return the recognised text.
        Falls back to text input if the microphone is unavailable.
        Returns ``"None"`` on failure.
        """
        if prompt:
            print(prompt)

        # Text input fallback (PyAudio not installed or mic unavailable)
        if not self.stt_enabled:
            print("[J.A.R.V.I.S.] (Text mode — microphone unavailable)")
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                return "None"
            return user_input.lower() if user_input else "None"

        # Microphone-based speech recognition
        with sr.Microphone() as source:
            self._recognizer.pause_threshold = 1
            self._recognizer.energy_threshold = 300
            try:
                print("Listening...")
                audio = self._recognizer.listen(
                    source,
                    timeout=LISTEN_TIMEOUT,
                    phrase_time_limit=PHRASE_TIME_LIMIT,
                )
            except sr.WaitTimeoutError:
                return "None"

        try:
            print("Recognising...")
            query = self._recognizer.recognize_google(audio, language="en-in")
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            self.speak("Sorry, I could not understand that.")
            return "None"
        except sr.RequestError:
            # Google Web Speech API unavailable — fall back to text
            log.warning("Speech service unavailable; switching to text mode")
            self.stt_enabled = False
            return self.listen(prompt="Type your command: ")
        except Exception:
            log.exception("Speech recognition failed")
            return "None"


# Module-level singleton
speech = SpeechEngine()
