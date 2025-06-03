# src/core/profiles/types.py
"""Type definitions for profile system."""
from typing import TypedDict, Dict, List, Any, Optional


class SessionData(TypedDict):
    """Structure for platform session data."""
    platform: str
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    auth_tokens: Dict[str, str]
    last_updated: str
    is_valid: bool
    user_id: Optional[str]
    fingerprint_hash: Optional[str]  # Track which fingerprint was used


class ProfileMetrics(TypedDict):
    """Profile performance metrics."""
    attempts: int
    successes: int
    failures: int
    last_success: Optional[str]
    last_failure: Optional[str]
    avg_response_time_ms: float
    detection_events: List[Dict[str, Any]]
    captcha_solve_rate: float
    consecutive_successes: int