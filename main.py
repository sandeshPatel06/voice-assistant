"""
Main entry point for the Jarvis AI assistant.

Enhancements over the original:
- Modular task architecture (tasks/ package)
- Free AI answering (DuckDuckGo Instant Answer, Wikipedia, Ollama, web search)
- No API keys required for most features
- Configuration via environment variables
- Persistent notes and reminders
- System monitoring (CPU, RAM, disk, battery, network)
- More websites, media control, jokes, unit conversion, calculator
- Robust error handling and cross-platform support
"""

import datetime
import logging
import re
import sys
import webbrowser
import wikipedia

from config import DATA_DIR
from speech_engine import SpeechEngine
from ai_answer import ai_answer
from tasks.system import SystemTasks
from tasks.media import MediaTasks
from tasks.web import WebTasks, SITES
from tasks.productivity import ProductivityTasks
from tasks.utils import UtilityTasks
from tasks.email import EmailTasks

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("jarvis.main")

# ── Data directory ──────────────────────────────────────────────────
DATA_DIR.mkdir(exist_ok=True)


class Jarvis:
    """Main assistant orchestrator."""

    def __init__(self) -> None:
        self.speech = SpeechEngine()
        self.speak = self.speech.speak
        self.listen = self.speech.listen

        # Initialise task modules
        self.system = SystemTasks(self.speech)
        self.media = MediaTasks(self.speech)
        self.web = WebTasks(self.speech)
        self.productivity = ProductivityTasks(self.speech)
        self.utils = UtilityTasks(self.speech)
        self.email = EmailTasks(self.speech)

        # Start the background reminder watcher
        self.productivity.start_reminder_watcher()

    def wish(self) -> None:
        """Greet the user based on the time of day."""
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            self.speak("Good morning")
        elif 12 <= hour < 15:
            self.speak("Good afternoon")
        else:
            self.speak("Good evening")
        self.speak("I am J.A.R.V.I.S., your personal assistant. How may I help you?")

    def _extract_number(self, text: str) -> int | None:
        """Extract a number from spoken text."""
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else None

    def handle_command(self, query: str) -> bool:
        """
        Process a single voice command.
        Returns True if the assistant should continue listening, False to exit.
        """
        if query in ("None", ""):
            return True

        log.info("Received command: %s", query)

        # ── Exit commands ───────────────────────────────────────────
        if any(word in query for word in ["stop listening", "exit", "quit", "bye"]):
            self.speak("Stopping. Have a nice day!")
            return False

        # ── Greetings ───────────────────────────────────────────────
        if any(word in query for word in ["hello", "hi ", "hey "]):
            self.speak("Hello sir!")
        elif any(word in query for word in ["how are you", "how r u"]):
            self.speak("I am fine, thank you for asking. How can I help you?")

        # ── Time & Date ─────────────────────────────────────────────
        elif "the time" in query or "what time" in query:
            self.system.tell_time()
        elif "the date" in query or "what date" in query or "today's date" in query:
            self.system.tell_date()

        # ── Wikipedia ───────────────────────────────────────────────
        elif "wikipedia" in query:
            self.speak("Searching Wikipedia...")
            search_term = query.replace("wikipedia", "").strip()
            if not search_term:
                self.speak("What would you like to search on Wikipedia?")
                search_term = self.listen()
            try:
                results = wikipedia.summary(search_term, sentences=2)
                self.speak("According to Wikipedia")
                self.speak(results)
            except Exception:
                self.speak(f"I could not find information on {search_term}.")

        # ── Open websites ───────────────────────────────────────────
        elif "open" in query and "site" not in query:
            # Try to match known sites
            handled = False
            for site_name in sorted(SITES, key=len, reverse=True):
                if site_name in query:
                    self.web.open_site(site_name)
                    handled = True
                    break
            if not handled:
                # Try to extract a URL
                match = re.search(
                    r"open\s+(?:website\s+)?([\w\.-]+\.\w+)", query
                )
                if match:
                    self.web.open_url(match.group(1))
                else:
                    self.speak(
                        "Which website would you like to open? "
                        "Please say the name or URL."
                    )

        # ── Google search ───────────────────────────────────────────
        elif "search" in query and "youtube" not in query:
            if "search" in query:
                search_term = query.replace("search", "").strip()
                if not search_term:
                    self.speak("What would you like to search for?")
                    search_term = self.listen()
                self.web.search_web(search_term)
            else:
                self.speak("What would you like to search for?")

        elif "search youtube" in query or "youtube search" in query:
            self.speak("What would you like to search on YouTube?")
            search_term = self.listen()
            if search_term != "None":
                self.web.search_youtube(search_term)

        # ── Music & Media ──────────────────────────────────────────
        elif "play music" in query or "play song" in query:
            self.media.play_music()
        elif "play video" in query:
            self.media.play_video()
        elif "stop" in query and ("media" in query or "music" in query or "video" in query):
            self.media.stop_media()

        # ── Calculator & Conversion ─────────────────────────────────
        elif "calculate" in query:
            self.utils.calculate(query)
        elif "convert" in query:
            self.utils.convert_units(query)

        # ── Jokes ──────────────────────────────────────────────────
        elif "joke" in query or "funny" in query:
            self.utils.tell_joke()

        # ── Notes ───────────────────────────────────────────────────
        elif "note" in query:
            if "save" in query or "add" in query:
                self.productivity.add_note()
            elif "read" in query or "show" in query:
                self.productivity.read_notes()

        # ── Reminders ───────────────────────────────────────────────
        elif "reminder" in query or "remind" in query:
            if "set" in query or "remind me" in query:
                self.productivity.set_reminder()
            elif "list" in query or "show" in query:
                self.productivity.list_reminders()

        # ── Calendar / Date info ────────────────────────────────────
        elif "calendar" in query or "today" in query:
            self.productivity.tell_calendar()

        # ── Weather ─────────────────────────────────────────────────
        elif "weather" in query or "temperature" in query:
            self.web.get_weather()

        # ── News ────────────────────────────────────────────────────
        elif "news" in query:
            self.web.get_news()

        # ── Email ───────────────────────────────────────────────────
        elif "send email" in query or "send a mail" in query:
            self.email.send_email()

        # ── System Info ─────────────────────────────────────────────
        elif "system info" in query or "system information" in query:
            self.system.get_system_info()
        elif "cpu" in query or "processor" in query:
            self.system.cpu_usage()
        elif "ram" in query or "memory" in query:
            self.system.ram_usage()
        elif "disk" in query:
            self.system.check_disk_space()
        elif "battery" in query:
            self.system.battery_status()
        elif "ip address" in query or "my ip" in query:
            self.system.get_ip_address()
        elif "network" in query or "online" in query:
            self.system.who_is_online()

        # ── Power Control ───────────────────────────────────────────
        elif "shutdown" in query:
            self.speak("Are you sure you want to shut down? Please confirm.")
            confirm = self.listen()
            if "yes" in confirm:
                self.system.shutdown()
            else:
                self.speak("Shutdown cancelled.")
        elif "restart" in query or "reboot" in query:
            self.speak("Are you sure you want to restart? Please confirm.")
            confirm = self.listen()
            if "yes" in confirm:
                self.system.restart()
            else:
                self.speak("Restart cancelled.")
        elif "sleep" in query and "display" not in query:
            self.system.sleep_display()

        # ── Volume & Brightness ─────────────────────────────────────
        elif "volume up" in query:
            self.system.volume_up()
        elif "volume down" in query:
            self.system.volume_down()
        elif "mute" in query or "unmute" in query:
            self.system.mute()
        elif "brightness" in query:
            level = "high" if "high" in query else "low" if "low" in query else "medium"
            self.system.set_brightness(level)

        # ── Translation ─────────────────────────────────────────────
        elif "translate" in query:
            self.utils.translate(query)

        # ── Define a word ───────────────────────────────────────────
        elif "define" in query or "meaning of" in query:
            word = query.replace("define", "").replace("what is the meaning of", "").strip()
            self.utils.define_word(word)

        # ── Free AI Q&A ─────────────────────────────────────────────
        elif any(word in query for word in ["what is", "who is", "who are", "where is", "when is"]):
            # For "what is" queries, try the calculator first; if it's not
            # math, fall through to AI answering.
            if "what is" in query:
                if not self.utils.calculate(query):
                    self.utils.answer_question(query)
            else:
                self.utils.answer_question(query)

        # ── Fallback — free AI answering ────────────────────────────
        elif len(query.split()) >= 4:
            # Longer phrases that don't match a specific command — try AI answer
            self.utils.answer_question(query)

        else:
            self.speak("I didn't understand that. Could you rephrase?")

        # Check for pending reminders after each command
        self.productivity.check_reminders()
        return True

    def run(self) -> None:
        """Main listening loop."""
        self.wish()
        while True:
            query = self.listen()
            should_continue = self.handle_command(query)
            if not should_continue:
                break


def main() -> None:
    jarvis = Jarvis()
    try:
        jarvis.run()
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        jarvis.speak("Goodbye!")


if __name__ == "__main__":
    main()
