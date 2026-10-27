"""
Tasks package — modular command handlers for Jarvis.
"""

from .system import SystemTasks
from .media import MediaTasks
from .web import WebTasks, SITES
from .productivity import ProductivityTasks
from .utils import UtilityTasks
from .email import EmailTasks

__all__ = [
    "SystemTasks",
    "MediaTasks",
    "WebTasks",
    "SITES",
    "ProductivityTasks",
    "UtilityTasks",
    "EmailTasks",
]
