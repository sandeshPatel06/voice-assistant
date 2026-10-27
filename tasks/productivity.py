"""
Productivity tasks: notes, reminders, calendar.
Data is persisted as JSON in the data/ directory.
"""

import datetime
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_engine import SpeechEngine

from config import REMINDERS_FILE, NOTES_FILE

log = logging.getLogger("jarvis.tasks.productivity")

_reminder_lock = threading.Lock()
_reminder_threads: list[threading.Thread] = []


class ProductivityTasks:
    """Handle notes, reminders, and calendar tasks."""

    def __init__(self, speech: "SpeechEngine") -> None:
        self.speak = speech.speak
        self.listen = speech.listen
        self._ensure_data_files()

    def _ensure_data_files(self) -> None:
        for f in (REMINDERS_FILE, NOTES_FILE):
            f.parent.mkdir(parents=True, exist_ok=True)
            if not f.exists():
                f.write_text("[]")

    # ── Notes ────────────────────────────────────────────────────────
    def add_note(self) -> None:
        self.speak("What note would you like me to save?")
        note_text = self.listen()
        if note_text == "None":
            self.speak("No note taken.")
            return

        notes = self._load_notes()
        entry = {
            "text": note_text,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        notes.append(entry)
        self._save_notes(notes)
        self.speak("Note saved successfully.")

    def read_notes(self) -> None:
        notes = self._load_notes()
        if not notes:
            self.speak("You have no notes.")
            return

        self.speak(f"You have {len(notes)} notes.")
        for i, note in enumerate(notes, 1):
            self.speak(f"Note {i}: {note['text']}")

    def _load_notes(self) -> list[dict]:
        try:
            with open(NOTES_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_notes(self, notes: list[dict]) -> None:
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f, indent=2)

    # ── Reminders ────────────────────────────────────────────────────
    def set_reminder(self) -> None:
        self.speak("What should I remind you about?")
        reminder_text = self.listen()
        if reminder_text == "None":
            self.speak("No reminder set.")
            return

        self.speak("In how many minutes should I remind you?")
        mins_text = self.listen()
        try:
            minutes = int("".join(c for c in mins_text if c.isdigit()))
        except ValueError:
            minutes = 0

        if minutes <= 0:
            self.speak("I didn't catch the time. Reminder not set.")
            return

        remind_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        reminder = {
            "text": reminder_text,
            "remind_at": remind_at.isoformat(),
            "created_at": datetime.datetime.now().isoformat(),
        }
        reminders = self._load_reminders()
        reminders.append(reminder)
        self._save_reminders(reminders)

        self.speak(
            f"Reminder set for {reminder_text} in {minutes} minutes."
        )
        log.info("Reminder set: %s at %s", reminder_text, remind_at.isoformat())

    def check_reminders(self) -> None:
        """Check and trigger any due reminders. Non-blocking."""
        now = datetime.datetime.now()
        reminders = self._load_reminders()
        due = [r for r in reminders if self._parse_dt(r["remind_at"]) <= now]
        pending = [
            r for r in reminders if self._parse_dt(r["remind_at"]) > now
        ]

        for r in due:
            self.speak(f"Reminder: {r['text']}")
            log.info("Triggered reminder: %s", r["text"])

        self._save_reminders(pending)

    def list_reminders(self) -> None:
        reminders = self._load_reminders()
        if not reminders:
            self.speak("You have no upcoming reminders.")
            return

        self.speak(f"You have {len(reminders)} reminders.")
        for r in reminders:
            remind_at = self._parse_dt(r["remind_at"])
            self.speak(
                f"{r['text']} at {remind_at.strftime('%I:%M %p on %B %d')}"
            )

    def _load_reminders(self) -> list[dict]:
        try:
            with open(REMINDERS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_reminders(self, reminders: list[dict]) -> None:
        with open(REMINDERS_FILE, "w") as f:
            json.dump(reminders, f, indent=2)

    @staticmethod
    def _parse_dt(dt_str: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(dt_str)

    # ── Calendar ─────────────────────────────────────────────────────
    def tell_calendar(self) -> None:
        """Tell today's events (from reminders) and date info."""
        today = datetime.date.today()
        self.speak(f"Today is {today.strftime('%A, %B %d, %Y')}")

        reminders = self._load_reminders()
        today_reminders = [
            r for r in reminders
            if self._parse_dt(r["remind_at"]).date() == today
        ]
        if today_reminders:
            self.speak(f"You have {len(today_reminders)} reminders today:")
            for r in today_reminders:
                self.speak(r["text"])
        else:
            self.speak("You have no reminders scheduled for today.")

    # ── Reminder watcher ─────────────────────────────────────────────
    def start_reminder_watcher(self) -> None:
        """Start a background thread that periodically checks reminders."""

        def _watcher() -> None:
            # Small delay to let the assistant initialise
            time.sleep(5)
            while True:
                time.sleep(30)
                with _reminder_lock:
                    try:
                        self.check_reminders()
                    except Exception:
                        log.exception("Reminder watcher error")

        t = threading.Thread(target=_watcher, daemon=True)
        t.start()
        _reminder_threads.append(t)
