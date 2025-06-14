# stealthmaster/detection/__init__.py
"""Anti-detection monitoring and recovery systems."""

# Only import ticket detector by default to avoid dependencies
from .ticket_detector import TicketDetector

# These require additional dependencies, import them when needed
__all__ = ["TicketDetector", "CaptchaHandler", "DetectionMonitor", "RecoveryStrategy"]

# Lazy imports to avoid dependency issues
def get_captcha_handler():
    from .captcha import CaptchaHandler
    return CaptchaHandler

def get_detection_monitor():
    from .monitor import DetectionMonitor
    return DetectionMonitor

def get_recovery_strategy():
    from .recovery import RecoveryStrategy
    return RecoveryStrategy
