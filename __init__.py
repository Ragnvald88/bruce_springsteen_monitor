# stealthmaster/__init__.py
"""
StealthMaster - Ultra-Stealthy Ticketing Bot System

A sophisticated ticketing automation system with advanced anti-detection measures,
intelligent profile management, and adaptive strategies for various ticketing platforms.
"""

__version__ = "2.0.0"
__author__ = "StealthMaster Team"
__license__ = "Proprietary"

# Core module imports
from .config import Settings, load_settings
from .src.constants import BrowserState, DetectionType, PurchaseStatus

# Make key components available at package level
from .stealth.core import StealthCore
from .detection.monitor import DetectionMonitor
from .profiles.manager import ProfileManager

__all__ = [
    # Version
    "__version__",
    # Configuration
    "Settings",
    "load_settings",
    # Constants
    "BrowserState",
    "DetectionType", 
    "PurchaseStatus",
    # Core Components
    "StealthCore",
    "DetectionMonitor",
    "ProfileManager",
]

# Package initialization
import logging

# Set default logging to WARNING to avoid noise
logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.getLogger(__name__).setLevel(logging.WARNING)