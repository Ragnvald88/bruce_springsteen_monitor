# src/core/errors.py
"""Custom exceptions for the monitoring system"""

class MonitorError(Exception):
    """Base exception for all monitoring errors"""
    pass

class BlockedError(MonitorError):
    """Raised when detected as blocked by anti-bot systems"""
    pass

class RateLimitError(MonitorError):
    """Raised when rate limited by the platform"""
    pass

class ProfileError(MonitorError):
    """Raised when there's an issue with browser profiles"""
    pass
class BlockedError(RuntimeError):
    """Raised by platform checkers when a hard block (403, empty body …) occurs."""