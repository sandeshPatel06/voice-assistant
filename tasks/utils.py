"""
Utility tasks: calculator, unit conversion, translation, jokes, etc.
"""

import logging
import re
import webbrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_engine import SpeechEngine

from ai_answer import ai_answer

log = logging.getLogger("jarvis.tasks.utils")


class UtilityTasks:
    """Handle utility and calculation tasks."""

    def __init__(self, speech: "SpeechEngine") -> None:
        self.speak = speech.speak
        self.listen = speech.listen

    # ── Calculator ───────────────────────────────────────────────────
    # Ordered list: multi-word phrases first, then single words.
    _WORD_OPERATORS = [
        ("divided by", "/"),
        ("multiplied by", "*"),
        ("times by", "*"),
        ("plus", "+"),
        ("add", "+"),
        ("sum of", "+"),
        ("minus", "-"),
        ("subtract", "-"),
        ("subtraction", "-"),
        ("times", "*"),
        ("multiply", "*"),
        ("divided", "/"),
        ("divide", "/"),
    ]

    def calculate(self, query: str) -> bool:
        """
        Evaluate a spoken math expression.
        Returns True if the query was recognised as math, False to let
        other handlers take over.
        """
        # Only treat as math if it contains a digit
        if not re.search(r"\d", query):
            return False

        # Strip trigger words
        expr = re.sub(
            r"(calculate|what is|compute|compute)", "", query, flags=re.I
        ).strip()

        # Convert spoken operators to symbols (multi-word first)
        for word_phrase, op in self._WORD_OPERATORS:
            expr = re.sub(rf"\b{word_phrase}\b", op, expr, flags=re.I)

        # Remove any leftover "by" that was part of "divided by" (already handled)
        # but if a stray "by" remains, leave it — the allowed-char check will catch it.

        # Allow only safe characters
        allowed = set("0123456789+-*/.() ")
        if not expr or any(c not in allowed for c in expr):
            self.speak("I couldn't understand the calculation. Please try again.")
            return True

        try:
            result = eval(expr, {"__builtins__": {}}, {})
            self.speak(f"The result is {result}")
            return True
        except Exception:
            self.speak("I could not perform that calculation.")
            return True

    # ── Unit conversion ──────────────────────────────────────────────
    def convert_units(self, query: str) -> None:
        """Simple unit conversion for common cases."""
        # e.g. "convert 100 celsius to fahrenheit"
        match = re.search(r"convert\s+(\d+(?:\.\d+)?)\s*(\w+)\s+to\s+(\w+)", query, re.I)
        if not match:
            self.speak("I couldn't understand. Try saying 'convert 100 celsius to fahrenheit'.")
            return

        value, from_unit, to_unit = float(match.group(1)), match.group(2).lower(), match.group(3).lower()

        conversions = {
            ("celsius", "fahrenheit"): lambda v: v * 9 / 5 + 32,
            ("fahrenheit", "celsius"): lambda v: (v - 32) * 5 / 9,
            ("celsius", "kelvin"): lambda v: v + 273.15,
            ("kelvin", "celsius"): lambda v: v - 273.15,
            ("fahrenheit", "kelvin"): lambda v: (v - 32) * 5 / 9 + 273.15,
            ("kelvin", "fahrenheit"): lambda v: (v - 273.15) * 9 / 5 + 32,
            ("kilometers", "miles"): lambda v: v * 0.621371,
            ("miles", "kilometers"): lambda v: v / 0.621371,
            ("meters", "feet"): lambda v: v * 3.28084,
            ("feet", "meters"): lambda v: v / 3.28084,
            ("kilograms", "pounds"): lambda v: v * 2.20462,
            ("pounds", "kilograms"): lambda v: v / 2.20462,
            ("liters", "gallons"): lambda v: v * 0.264172,
            ("gallons", "liters"): lambda v: v / 0.264172,
        }

        key = (from_unit, to_unit)
        if key in conversions:
            result = conversions[key](value)
            self.speak(f"{value} {from_unit} is {round(result, 2)} {to_unit}")
        else:
            self.speak(f"I can't convert {from_unit} to {to_unit} yet.")

    # ── Translation ──────────────────────────────────────────────────
    def translate(self, query: str) -> None:
        """Translate text using Google Translate (web, no API key)."""
        self.speak("Opening Google Translate.")
        webbrowser.open("https://translate.google.com")

    # ── Jokes ────────────────────────────────────────────────────────
    def tell_joke(self) -> None:
        """Tell a random joke."""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why don't skeletons fight each other? They don't have the guts.",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "I'm reading a book about anti-gravity. It's impossible to put down!",
            "What do you get when you cross a snowman and a vampire? Frostbite.",
            "Why did the mathematician name his dog Cauchy? Because he left a residue at every pole!",
            "How does a penguin build its house? Igloos it together!",
            "What's orange and sounds like a parrot? A carrot!",
        ]
        import random
        self.speak(random.choice(jokes))

    # ── General question answering ───────────────────────────────────
    def answer_question(self, query: str) -> None:
        """Answer a free-form question using free AI backends."""
        self.speak("Let me look that up for you.")
        answer = ai_answer.answer(query)
        if answer:
            self.speak(answer)
        else:
            self.speak("I'm sorry, I couldn't find an answer.")

    # ── Define a word ────────────────────────────────────────────────
    def define_word(self, word: str) -> None:
        """Define a word using DuckDuckGo Instant Answer."""
        answer = ai_answer.answer(f"definition of {word}")
        if answer:
            self.speak(answer)
        else:
            self.speak(f"I couldn't find a definition for {word}.")
