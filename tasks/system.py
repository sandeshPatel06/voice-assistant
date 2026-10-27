"""
System-level tasks: information, power control, volume, etc.
"""

import datetime
import logging
import platform
import shutil
import socket
import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_engine import SpeechEngine

log = logging.getLogger("jarvis.tasks.system")


class SystemTasks:
    """Handle system queries and control commands."""

    def __init__(self, speech: "SpeechEngine") -> None:
        self.speak = speech.speak
        self.listen = speech.listen

    # ── Information ──────────────────────────────────────────────────
    def get_system_info(self) -> None:
        """Report CPU, RAM, disk, and OS info."""
        try:
            import psutil
        except ImportError:
            psutil = None  # type: ignore[assignment]

        os_name = platform.system()
        os_ver = platform.version()
        hostname = socket.gethostname()

        self.speak(f"I'm running on {os_name} version {os_ver.split()[0]}")
        self.speak(f"Device name: {hostname}")

        if psutil:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            self.speak(f"CPU usage is {cpu}%")
            self.speak(
                f"Memory usage is {mem.percent}% "
                f"with {round(mem.available / (1024 ** 3), 1)} GB available"
            )
            self.speak(
                f"Disk usage is {disk.percent}% "
                f"with {round(disk.free / (1024 ** 3), 1)} GB free"
            )

    def tell_time(self) -> None:
        """Speak the current time."""
        str_time = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"Sir, the time is {str_time}")

    def tell_date(self) -> None:
        """Speak today's date."""
        str_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.speak(f"Today is {str_date}")

    def battery_status(self) -> None:
        """Report battery percentage if available."""
        try:
            import psutil
        except ImportError:
            self.speak("Battery monitoring is not available.")
            return

        battery = psutil.sensors_battery()
        if battery is None:
            self.speak("No battery detected.")
            return

        self.speak(
            f"Battery is at {battery.percent}% "
            f"and {'plugged in' if battery.power_plugged else 'running on battery'}"
        )

    # ── Power Control ────────────────────────────────────────────────
    def shutdown(self) -> None:
        self.speak("Shutting down the system. Goodbye!")
        self._run_power_command(["shutdown", "-h", "now"])

    def restart(self) -> None:
        self.speak("Restarting the system. Goodbye!")
        self._run_power_command(["shutdown", "-r", "now"])

    def sleep_display(self) -> None:
        """Attempt to put the display to sleep."""
        if sys.platform == "linux":
            subprocess.run(["xset", "dpms", "force", "off"], timeout=5)
        elif sys.platform == "darwin":
            subprocess.run(["pmset", " displaysleepnow"], timeout=5)
        elif sys.platform == "win32":
            subprocess.run(["rundll32.exe", "powrprof.dll, SetSuspendState"], timeout=5)
        self.speak("Display should be sleeping now.")

    def _run_power_command(self, cmd: list[str]) -> None:
        try:
            subprocess.run(cmd, check=False, timeout=10)
        except FileNotFoundError:
            log.warning("Power command not found: %s", cmd[0])
            self.speak(f"Could not execute: {' '.join(cmd)}")
        except PermissionError:
            self.speak("Permission denied. Try running with sudo.")
        except Exception:
            log.exception("Power command failed")

    # ── Audio ────────────────────────────────────────────────────────
    def volume_up(self) -> None:
        if sys.platform == "linux":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"], timeout=5)
        elif sys.platform == "win32":
            subprocess.run(["nircmd.exe", "changesysvolume", "10000"], timeout=5)
        self.speak("Volume increased.")

    def volume_down(self) -> None:
        if sys.platform == "linux":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"], timeout=5)
        elif sys.platform == "win32":
            subprocess.run(["nircmd.exe", "changesysvolume", "-10000"], timeout=5)
        self.speak("Volume decreased.")

    def mute(self) -> None:
        if sys.platform == "linux":
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], timeout=5)
        elif sys.platform == "win32":
            subprocess.run(["nircmd.exe", "mutesysvolume", "2"], timeout=5)
        self.speak("Audio toggled.")

    # ── Utilities ────────────────────────────────────────────────────
    def get_ip_address(self) -> None:
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            self.speak(f"Your IP address is {ip}")
        except Exception:
            self.speak("I could not determine your IP address.")

    def check_disk_space(self) -> None:
        try:
            usage = shutil.disk_usage("/")
            free_gb = round(usage.free / (1024 ** 3), 2)
            total_gb = round(usage.total / (1024 ** 3), 2)
            self.speak(f"Total disk: {total_gb} GB, Free: {free_gb} GB")
        except Exception:
            self.speak("Could not check disk space.")

    def cpu_usage(self) -> None:
        try:
            import psutil
            usage = psutil.cpu_percent(interval=1)
            self.speak(f"CPU usage is at {usage}%")
        except ImportError:
            self.speak("psutil is not installed.")

    def ram_usage(self) -> None:
        try:
            import psutil
            mem = psutil.virtual_memory()
            self.speak(f"RAM usage is at {mem.percent}%")
        except ImportError:
            self.speak("psutil is not installed.")

    def who_is_online(self) -> None:
        """Check if the network is reachable."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            self.speak("You are online.")
        except OSError:
            self.speak("You appear to be offline.")

    # ── Screen brightness ────────────────────────────────────────────
    def set_brightness(self, level: str) -> None:
        """Try to set screen brightness on Linux."""
        brightness_map = {
            "low": "20",
            "medium": "50",
            "high": "80",
            "full": "100",
        }
        percentage = brightness_map.get(level.lower())
        if percentage:
            if sys.platform == "linux":
                # Requires xbacklight or brightnessctl installed
                try:
                    subprocess.run(
                        ["brightnessctl", "s", f"{percentage}%"],
                        timeout=5,
                    )
                except FileNotFoundError:
                    subprocess.run(
                        ["xbacklight", "-set", percentage], timeout=5
                    )
                self.speak(f"Brightness set to {level}.")
            elif sys.platform == "win32":
                self.speak("Brightness control requires Windows 10+ with Monitorian.")
            else:
                self.speak("Brightness control is not supported on this platform.")
        else:
            self.speak("Please specify low, medium, or high brightness.")
