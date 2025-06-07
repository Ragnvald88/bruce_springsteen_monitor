# src/models/ticket.py
"""
Ticket-related models
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

from .enums import Platform, PriorityLevel, OperationMode

logger = logging.getLogger(__name__)


@dataclass
class EnhancedTicketOpportunity:
    """Next-gen ticket opportunity with advanced metadata"""
    id: str
    platform: Platform
    event_name: str
    url: str  # Main event page URL
    offer_url: str  # Specific URL for this offer
    section: str
    price: float
    quantity: int
    detected_at: datetime
    priority: PriorityLevel

    # Enhanced metadata
    confidence_score: float = 0.95
    detection_method: str = "unknown"
    verification_status: bool = False
    attempt_count: int = 0
    last_attempt: Optional[datetime] = None

    # Profile affinity scoring
    profile_scores: Dict[str, float] = field(default_factory=dict)
    selected_profile_id: Optional[str] = None

    # Platform-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance tracking
    response_times: List[float] = field(default_factory=list)
    data_used_mb: float = 0.0

    # Fingerprint for deduplication
    fingerprint: Optional[str] = None

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint for opportunity."""
        components = [
            str(self.platform.value),
            str(self.event_name).lower().strip(),
            str(self.section).lower().strip(),
            f"{self.price:.2f}",
            str(self.quantity)
        ]
        return hashlib.sha256("|".join(components).encode()).hexdigest()[:32]

    @property
    def age_seconds(self) -> float:
        """How old is this opportunity in seconds."""
        return (datetime.now() - self.detected_at).total_seconds()

    @property
    def is_fresh(self, fresh_threshold_seconds: int = 30) -> bool:
        """Is the opportunity considered fresh."""
        return self.age_seconds < fresh_threshold_seconds

    @property
    def average_response_time(self) -> float:
        """Average response time for strike attempts."""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0

    def calculate_score(self, mode: OperationMode) -> float:
        """Calculate dynamic priority score based on mode."""
        base_score = 100.0

        # Priority weight
        priority_value = self.priority.numeric_value
        base_score += (5 - priority_value) * 20

        # Freshness penalty
        freshness_penalty = min(self.age_seconds / 60, 50)
        base_score -= freshness_penalty

        # Confidence bonus
        base_score += (self.confidence_score - 0.5) * 60

        # Attempt penalty
        base_score -= self.attempt_count * 5

        # Mode-specific adjustments
        if mode in [OperationMode.STEALTH, OperationMode.ULTRA_STEALTH]:
            if self.priority == PriorityLevel.LOW and self.verification_status:
                base_score += 15
            if self.is_fresh:
                base_score -= 10
        elif mode == OperationMode.BEAST:
            if self.priority == PriorityLevel.CRITICAL:
                base_score += 50
            if self.is_fresh:
                base_score += 20
        elif mode == OperationMode.ADAPTIVE:
            if self.selected_profile_id and self.profile_scores.get(self.selected_profile_id, 0) > 70:
                base_score += 10

        return max(0, base_score)

    def __lt__(self, other: 'EnhancedTicketOpportunity') -> bool:
        """For priority queue sorting."""
        return self.calculate_score(OperationMode.ADAPTIVE) > other.calculate_score(OperationMode.ADAPTIVE)


@dataclass
class DataUsageTracker:
    """Track and optimize data usage across the system"""
    total_used_mb: float = 0.0
    session_used_mb: float = 0.0
    platform_usage: Dict[str, float] = field(default_factory=dict)
    profile_usage: Dict[str, float] = field(default_factory=dict)

    # Limits
    global_limit_mb: Optional[float] = None
    session_limit_mb: Optional[float] = None
    daily_limit_mb: Optional[float] = None

    # Optimization metrics
    compression_ratio: float = 1.0
    cached_responses: int = 0
    blocked_resources_saved_mb: float = 0.0

    def add_usage(self, bytes_used: int, platform: Optional[str] = None, profile_id: Optional[str] = None):
        """Record data usage with categorization"""
        mb_used = bytes_used / (1024 * 1024)
        self.total_used_mb += mb_used
        self.session_used_mb += mb_used

        if platform:
            self.platform_usage[platform] = self.platform_usage.get(platform, 0) + mb_used
        if profile_id:
            self.profile_usage[profile_id] = self.profile_usage.get(profile_id, 0) + mb_used

    def is_approaching_limit(self, threshold: float = 0.9) -> bool:
        """Check if approaching any data limit"""
        if self.global_limit_mb and self.total_used_mb >= self.global_limit_mb * threshold:
            logger.warning(f"Global data limit approaching: {self.total_used_mb:.2f}/{self.global_limit_mb:.2f} MB")
            return True
        if self.session_limit_mb and self.session_used_mb >= self.session_limit_mb * threshold:
            logger.warning(f"Session data limit approaching: {self.session_used_mb:.2f}/{self.session_limit_mb:.2f} MB")
            return True
        return False

    def get_remaining_mb(self) -> float:
        """Get remaining data allowance."""
        remaining = float('inf')
        if self.global_limit_mb:
            remaining = min(remaining, self.global_limit_mb - self.total_used_mb)
        if self.session_limit_mb:
            remaining = min(remaining, self.session_limit_mb - self.session_used_mb)
        return max(0, remaining)

    def reset_session_usage(self):
        """Reset session-specific data usage."""
        logger.info(f"Resetting session data usage. Was: {self.session_used_mb:.2f} MB")
        self.session_used_mb = 0.0