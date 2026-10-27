"""
Media tasks: play music, videos, control playback.
"""

import logging
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_engine import SpeechEngine

from config import MUSIC_DIR, VIDEO_DIR

log = logging.getLogger("jarvis.tasks.media")


class MediaTasks:
    """Handle music and video playback."""

    def __init__(self, speech: "SpeechEngine") -> None:
        self.speak = speech.speak
        self.listen = speech.listen

    def play_music(self) -> None:
        """Play a random song from the music directory."""
        music_dir = Path(MUSIC_DIR).expanduser()
        if not music_dir.exists():
            self.speak(f"Music directory not found at {music_dir}")
            return

        songs = [
            f for f in os.listdir(music_dir)
            if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a"))
        ]
        if not songs:
            self.speak("No music files found in your music directory.")
            return

        song = random.choice(songs)
        song_path = str(music_dir / song)
        self.speak(f"Now playing {song}")
        self._play_file(song_path)

    def play_specific_song(self, song_name: str) -> None:
        """Play a specific song by name (partial match)."""
        music_dir = Path(MUSIC_DIR).expanduser()
        if not music_dir.exists():
            self.speak("Music directory not found.")
            return

        songs = [
            f for f in os.listdir(music_dir)
            if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a"))
        ]
        matched = [s for s in songs if song_name.lower() in s.lower()]
        if not matched:
            self.speak(f"Could not find a song matching {song_name}.")
            return

        song_path = str(music_dir / matched[0])
        self.speak(f"Now playing {matched[0]}")
        self._play_file(song_path)

    def play_video(self) -> None:
        """Play a random video from the video directory."""
        video_dir = Path(VIDEO_DIR).expanduser()
        if not video_dir.exists():
            self.speak(f"Video directory not found at {video_dir}")
            return

        videos = [
            f for f in os.listdir(video_dir)
            if f.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".wmv"))
        ]
        if not videos:
            self.speak("No video files found.")
            return

        video = random.choice(videos)
        video_path = str(video_dir / video)
        self.speak(f"Now playing {video}")
        self._play_file(video_path)

    def stop_media(self) -> None:
        """Stop any currently playing media."""
        try:
            subprocess.run(["pkill", "-f", "vlc"], timeout=5) if sys.platform != "win32" else None
            self.speak("Media stopped.")
        except Exception:
            self.speak("Could not stop media.")

    def _play_file(self, file_path: str) -> None:
        """Open a media file using the default player."""
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path], timeout=5)
            else:
                subprocess.run(["xdg-open", file_path], timeout=5)
        except Exception:
            log.exception("Failed to play %s", file_path)
            self.speak("Could not open the file.")
