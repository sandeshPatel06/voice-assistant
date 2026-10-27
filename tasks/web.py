"""
Web and internet tasks: open websites, search, read news, weather.
"""

import logging
import webbrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_engine import SpeechEngine

log = logging.getLogger("jarvis.tasks.web")

# ── Common website shortcuts ─────────────────────────────────────────
SITES: dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "twitter": "https://twitter.com",
    "facebook": "https://facebook.com",
    "instagram": "https://instagram.com",
    "linkedin": "https://linkedin.com",
    "reddit": "https://reddit.com",
    "netflix": "https://netflix.com",
    "stackoverflow": "https://stackoverflow.com",
    "amazon": "https://amazon.com",
    "weather": "https://www.weather.com",
    "news": "https://news.google.com",
}


class WebTasks:
    """Handle web browsing, search, news, and weather."""

    def __init__(self, speech: "SpeechEngine") -> None:
        self.speak = speech.speak
        self.listen = speech.listen

    # ── Open websites ────────────────────────────────────────────────
    def open_site(self, site_name: str) -> None:
        """Open a known website by name."""
        url = SITES.get(site_name.lower())
        if url:
            self.speak(f"Opening {site_name}")
            webbrowser.open(url)
        else:
            self.speak(f"I don't have a shortcut for {site_name}.")
            self.speak("Would you like to provide a URL?")

    def open_url(self, url: str) -> None:
        """Open an arbitrary URL, ensuring it has a scheme."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.speak(f"Opening {url}")
        webbrowser.open(url)

    # ── Search ───────────────────────────────────────────────────────
    def search_web(self, query: str) -> None:
        """Search Google for *query*."""
        url = f"https://www.google.com/search?q={query}"
        self.speak(f"Searching for {query}")
        webbrowser.open(url)

    def search_youtube(self, query: str) -> None:
        url = f"https://www.youtube.com/results?search_query={query}"
        self.speak(f"Searching YouTube for {query}")
        webbrowser.open(url)

    # ── News ─────────────────────────────────────────────────────────
    def get_news(self) -> None:
        """Fetch top headlines using an RSS feed (no API key)."""
        try:
            import feedparser
        except ImportError:
            self.speak("Feed parser is not installed. Opening news website instead.")
            webbrowser.open("https://news.google.com")
            return

        feeds = [
            "http://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.cnn.com/rss/edition.rss",
        ]

        titles: list[str] = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    titles.append(entry.title)
                if len(titles) >= 5:
                    break
            except Exception:
                log.exception("Failed to parse feed: %s", feed_url)

        if titles:
            self.speak("Here are the latest headlines:")
            for title in titles[:5]:
                self.speak(title)
        else:
            self.speak("I could not fetch news. Opening news website instead.")
            webbrowser.open("https://news.google.com")

    # ── Weather ──────────────────────────────────────────────────────
    def get_weather(self) -> None:
        """Get weather for a city using a free API."""
        try:
            from pyowm import OWM
            from config import WEATHER_API_KEY
        except ImportError:
            self.speak("Weather module is not installed. Opening weather website instead.")
            webbrowser.open("https://www.weather.com")
            return

        if not WEATHER_API_KEY:
            self.speak(
                "No weather API key configured. "
                "Set JARVIS_WEATHER_API_KEY in your environment "
                "or I can open the weather website."
            )
            webbrowser.open("https://www.weather.com")
            return

        self.speak("Which city would you like the weather for?")
        city = self.listen()
        if city == "None":
            self.speak("No city provided.")
            return

        try:
            owm = OWM(WEATHER_API_KEY)
            mgr = owm.weather_manager()
            weather = mgr.weather_at_place(city).weather
            temp = weather.temperature("celsius")["temp"]
            status = weather.detailed_status
            self.speak(
                f"In {city}, it's {status} with a temperature of {temp}°C."
            )
        except Exception:
            self.speak(f"Could not get weather for {city}.")
            log.exception("Weather fetch failed")
