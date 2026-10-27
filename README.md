
# J.A.R.V.I.S. — Python Voice Assistant

A modular, extensible voice assistant built with Python. Supports voice commands for system control, web browsing, media playback, note-taking, reminders, and answering questions — all **without requiring API keys** (using free, key-less services).

## Features

### Core
- **Text-to-Speech** via `pyttsx3` (offline, cross-platform)
- **Speech Recognition** via `SpeechRecognition` (Google Web Speech API)
- **Voice command dispatch** with fuzzy keyword matching
- **Configuration via environment variables** — no hard-coded secrets

### Free AI Answering (No API Keys)
Asks questions using a chain of **free, key-less** backends:
1. **DuckDuckGo Instant Answer API** — curated topic answers, definitions
2. **Wikipedia** — article extracts
3. **Ollama** — local LLM (e.g. llama3, mistral) — requires Ollama installed & running, **no key needed**
4. **DuckDuckGo Web Search** — scraped search result snippets

### System Tasks
- CPU, RAM, and disk usage monitoring
- Battery status and network connectivity check
- System shutdown, restart, and display sleep
- Volume control (up/down/mute) and screen brightness
- IP address lookup
- System information report

### Web & Media
- Open popular websites (YouTube, Google, GitHub, Reddit, Netflix, etc.)
- Google and YouTube search
- Play random or specific songs from your music folder
- Play videos from your video folder
- Stop media playback

### Productivity
- **Persistent notes** — save and read notes (stored as JSON)
- **Reminders** — set voice reminders with a background watcher thread
- **Calendar** — daily reminders overview and date info

### Utilities
- Calculator (voice math)
- Unit conversion (Celsius↔Fahrenheit, km↔miles, kg↔pounds, etc.)
- Jokes
- Word definitions
- Translation (opens Google Translate)

### Optional (when configured)
- **Weather** via OpenWeatherMap (free API key)
- **News** via RSS feeds (no key needed; uses BBC & CNN)
- **Email** sending via SMTP (credentials via environment)

## Project Structure

```
personalJarvisAi/
├── main.py              # Entry point, command dispatch, and main loop
├── config.py            # Centralised configuration (env-based)
├── speech_engine.py     # TTS + STT wrapper with fallbacks
├── ai_answer.py         # Free AI answering (DDG, Wikipedia, Ollama, web)
├── tasks/
│   ├── __init__.py
│   ├── system.py        # System info, power control, audio
│   ├── media.py         # Music & video playback
│   ├── web.py           # Websites, search, news, weather
│   ├── productivity.py  # Notes, reminders, calendar
│   ├── utils.py         # Calculator, conversion, jokes, translation
│   └── email.py         # Secure email sending
├── data/                # Persistent JSON data (notes, reminders)
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone https://github.com/sandeshPatel06/personalJarvisAi.git
cd personalJarvisAi
pip install -r requirements.txt
```

### System Dependencies

- **PyAudio** requires PortAudio:
  - Ubuntu/Debian: `sudo apt install portaudio19-dev`
  - macOS: `brew install portaudio`
  - Windows: included with PyAudio wheels

- **Ollama** (optional, for local LLM answering):
  Install from [ollama.ai](https://ollama.ai) and run `ollama serve`.

## Configuration

All sensitive or environment-specific settings are configured via environment variables with sensible defaults:

| Variable | Description | Default |
|---|---|---|
| `JARVIS_VOICE_INDEX` | Voice index (0=male, 1=female on Windows) | `1` |
| `JARVIS_SPEECH_RATE` | Words per minute | `200` |
| `JARVIS_SPEECH_VOLUME` | 0.0–1.0 | `1.0` |
| `JARVIS_MUSIC_DIR` | Music folder path | `~/Music` |
| `JARVIS_VIDEO_DIR` | Video folder path | `~/Videos` |
| `JARVIS_CODE_EDITOR` | Code editor path | *(empty)* |
| `JARVIS_EMAIL_ADDRESS` | Gmail/SMTP address | *(empty)* |
| `JARVIS_EMAIL_PASSWORD` | SMTP password or app password | *(empty)* |
| `JARVIS_SMTP_SERVER` | SMTP server | `smtp.gmail.com` |
| `JARVIS_SMTP_PORT` | SMTP port | `587` |
| `JARVIS_WEATHER_API_KEY` | OpenWeatherMap API key | *(empty)* |
| `JARVIS_OLLAMA_MODEL` | Ollama model name | `llama3` |
| `JARVIS_OLLAMA_URL` | Ollama server URL | `http://127.0.0.1:11434` |
| `JARVIS_LISTEN_TIMEOUT` | Max silence before giving up (seconds) | `8` |
| `JARVIS_PHRASE_TIME_LIMIT` | Max phrase length (seconds) | `5` |

### Example `.env` setup (optional)

```bash
export JARVIS_EMAIL_ADDRESS="your-email@gmail.com"
export JARVIS_EMAIL_PASSWORD="your-app-password"
export JARVIS_WEATHER_API_KEY="your-openweather-key"
export JARVIS_MUSIC_DIR="/home/user/Music"
```

> **Security note**: Email credentials are read from environment variables — never hard-coded. Gmail requires an **App Password** (not your main password) with 2FA enabled.

## Usage

```bash
python main.py
```

The assistant will greet you and begin listening. Try these commands:

| Command | Action |
|---|---|
| "what is the time" | Tell the current time |
| "what is the date" | Tell today's date |
| "search Wikipedia for Python" | 2-sentence Wikipedia summary |
| "open YouTube" | Open YouTube |
| "open github.com" | Open a custom URL |
| "search for latest AI news" | Google search |
| "search YouTube for coding" | YouTube search |
| "play music" | Play a random song |
| "play song [name]" | Play a specific song |
| "calculate 25 times 17" | Math calculation |
| "convert 100 celsius to fahrenheit" | Unit conversion |
| "tell me a joke" | Random joke |
| "define serendipity" | Word definition (via DuckDuckGo) |
| "who is Elon Musk" | AI-powered answer (DuckDuckGo/Wikipedia/Ollama) |
| "what is the capital of France" | Free AI Q&A |
| "save note [text]" | Voice note |
| "read notes" | Read all saved notes |
| "set a reminder [text] in [N] minutes" | Voice reminder |
| "list reminders" | Show upcoming reminders |
| "check the weather" | Weather lookup |
| "get news" | Top headlines |
| "send an email" | Interactive email composer |
| "system info" | CPU, RAM, disk report |
| "battery status" | Battery percentage |
| "shutdown" | Confirm and shut down |
| "volume up" | Increase volume |
| "stop listening" | Exit |

## Free AI Answering Backend Details

### DuckDuckGo Instant Answer API
Hits `https://api.duckduckgo.com/?q=<question>&format=json` — no API key, no authentication. Returns curated topic answers and definitions.

### Wikipedia
Uses the `wikipedia` Python library to fetch article summaries. Handles disambiguation by picking the first option.

### Ollama (Local LLM)
If Ollama is running locally (`ollama serve`), the assistant can query it for answers. This is a fully **offline** option. Example:
```bash
ollama run llama3
```

### DuckDuckGo Web Search
Final fallback — scrapes DuckDuckGo HTML search results for answer snippets.

## Notes & Reminders Persistence

Notes and reminders are saved as JSON in the `data/` directory:
```
data/
├── notes.json      # [{"text": "...", "timestamp": "..."}]
└── reminders.json  # [{"text": "...", "remind_at": "..."}]
```

A background thread checks reminders every 30 seconds and speaks them when due.

## License

This project is licensed under the MIT License.
