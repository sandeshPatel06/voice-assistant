"""
Centralized configuration for the Jarvis AI assistant.
All user-configurable settings live here.
"""

import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Speech / TTS ────────────────────────────────────────────────────
# Voice index: 0 = male (default), 1 = female (on Windows sapi5)
VOICE_INDEX = int(os.getenv("JARVIS_VOICE_INDEX", "1"))
SPEECH_RATE = int(os.getenv("JARVIS_SPEECH_RATE", "200"))   # words-per-minute
SPEECH_VOLUME = float(os.getenv("JARVIS_SPEECH_VOLUME", "1.0"))

# Speech-recognition settings
LISTEN_TIMEOUT = int(os.getenv("JARVIS_LISTEN_TIMEOUT", "8"))     # seconds to wait for speech
PHRASE_TIME_LIMIT = int(os.getenv("JARVIS_PHRASE_TIME_LIMIT", "5"))  # max phrase length

# ── Email ────────────────────────────────────────────────────────────
# Configure via environment variables — no hard-coded credentials.
EMAIL_ADDRESS = os.getenv("JARVIS_EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("JARVIS_EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("JARVIS_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("JARVIS_SMTP_PORT", "587"))

# ── Weather ──────────────────────────────────────────────────────────
WEATHER_API_KEY = os.getenv("JARVIS_WEATHER_API_KEY", "")

# ── Media ────────────────────────────────────────────────────────────
MUSIC_DIR = os.getenv("JARVIS_MUSIC_DIR", str(Path.home() / "Music"))
VIDEO_DIR = os.getenv("JARVIS_VIDEO_DIR", str(Path.home() / "Videos"))

# ── Code Editor ──────────────────────────────────────────────────────
CODE_EDITOR_PATH = os.getenv("JARVIS_CODE_EDITOR", "")

# ── Free AI answering backend priority ──────────────────────────────
# The assistant tries these in order to answer a free-form question.
#   - "duckduckgo":  Instant Answer API (no key needed)
#   - "wikipedia":   Wikipedia article extract (no key needed)
#   - "ollama":      local LLM via Ollama (no key needed, must be running)
#   - "web_search":  DuckDuckGo HTML search scrape (no key needed)
AI_BACKENDS = ["duckduckgo", "wikipedia", "ollama", "web_search"]
OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434")

# ── Reminders & notes ────────────────────────────────────────────────
REMINDERS_FILE = DATA_DIR / "reminders.json"
NOTES_FILE = DATA_DIR / "notes.json"
