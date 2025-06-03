# src/core/models.py
from __future__ import annotations

import hashlib
import logging # Added logging
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

# Import enums from within the same 'core' package
from .enums import PlatformType, PriorityLevel, OperationMode

logger = logging.getLogger(__name__) # Initialize logger

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

    def add_usage(self, bytes_used: int, platform: Optional[str] = None, profile_id: Optional[str] = None): # Made platform/profile_id optional
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
        if self.global_limit_mb is not None and self.total_used_mb >= self.global_limit_mb * threshold:
            logger.warning(f"Global data limit approaching: {self.total_used_mb:.2f}/{self.global_limit_mb:.2f} MB")
            return True
        if self.session_limit_mb is not None and self.session_used_mb >= self.session_limit_mb * threshold:
            logger.warning(f"Session data limit approaching: {self.session_used_mb:.2f}/{self.session_limit_mb:.2f} MB")
            return True
        # Add daily limit check if implemented
        return False

    def get_remaining_mb(self) -> float:
        """Get remaining data allowance based on the most restrictive limit."""
        remaining = float('inf')
        if self.global_limit_mb is not None:
            remaining = min(remaining, self.global_limit_mb - self.total_used_mb)
        if self.session_limit_mb is not None: # This might reset per session, logic depends on app
            remaining = min(remaining, self.session_limit_mb - self.session_used_mb)
        return max(0, remaining)

    def reset_session_usage(self):
        """Resets the session-specific data usage."""
        logger.info(f"Resetting session data usage. Was: {self.session_used_mb:.2f} MB")
        self.session_used_mb = 0.0


@dataclass
class EnhancedTicketOpportunity:
    """Next-gen ticket opportunity with advanced metadata"""
    id: str
    platform: PlatformType
    event_name: str
    url: str # Main event page URL
    offer_url: str # Specific URL for this offer, might be same as url or include fragment/params
    section: str
    price: float
    quantity: int
    detected_at: datetime
    priority: PriorityLevel

    # Enhanced metadata
    confidence_score: float = 0.95 # How confident the monitor is about this opportunity
    detection_method: str = "unknown" # e.g., "api_poll", "html_scrape", "websocket"
    verification_status: bool = False # Has this opportunity been double-checked?
    attempt_count: int = 0
    last_attempt: Optional[datetime] = None

    # Profile affinity scoring
    profile_scores: Dict[str, float] = field(default_factory=dict) # profile_id -> score for this opp
    selected_profile_id: Optional[str] = None

    # Platform-specific raw data or additional parsed fields
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance tracking for attempts on this opportunity
    response_times: List[float] = field(default_factory=list) # For strike attempts
    data_used_mb: float = 0.0 # For strike attempts

    # Fingerprint for deduplication (e.g., platform_event_section_price_quantity)
    fingerprint: Optional[str] = None

    def __post_init__(self):
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint for opportunity based on key characteristics."""
        # More robust fingerprinting might involve more fields or normalization
        components = [
            str(self.platform.value),
            str(self.event_name).lower().strip(),
            str(self.section).lower().strip(),
            f"{self.price:.2f}", # Standardize price format
            str(self.quantity)
        ]
        return hashlib.sha256("|".join(components).encode()).hexdigest()[:32] # Longer for more uniqueness

    @property
    def age_seconds(self) -> float:
        """How old is this opportunity in seconds."""
        return (datetime.now() - self.detected_at).total_seconds()

    @property
    def is_fresh(self, fresh_threshold_seconds: int = 30) -> bool:
        """Is the opportunity considered fresh (recently detected)."""
        return self.age_seconds < fresh_threshold_seconds

    @property
    def average_response_time(self) -> float:
        """Average response time for strike attempts on this opportunity."""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0

    def calculate_score(self, mode: OperationMode) -> float:
        """
        Calculate a dynamic score for this opportunity based on various factors
        and the current operation mode. Higher score means higher priority.
        """
        base_score = 100.0

        # Priority weight: CRITICAL (1) -> +80, HIGH (2) -> +60, NORMAL (3) -> +40, LOW (4) -> +20
        priority_value = self.priority.numeric_value # Using the property
        base_score += (5 - priority_value) * 20

        # Freshness: Penalize older opportunities. Max penalty of -50.
        freshness_penalty = min(self.age_seconds / 60, 50) # Penalize per minute old
        base_score -= freshness_penalty

        # Confidence: Higher confidence is better.
        base_score += (self.confidence_score - 0.5) * 60 # Scale confidence (0-1) to a -30 to +30 range

        # Attempt count: Penalize opportunities that have failed multiple times
        base_score -= self.attempt_count * 5

        # Mode-specific adjustments
        if mode == OperationMode.STEALTH or mode == OperationMode.ULTRA_STEALTH:
            # In stealth modes, might prefer less contested or slightly older but verified items
            if self.priority == PriorityLevel.LOW and self.verification_status:
                base_score += 15
            if self.is_fresh: # Very fresh items might be honey-pots in stealth
                base_score -= 10
        elif mode == OperationMode.BEAST:
            # Beast mode aggressively targets critical and fresh opportunities
            if self.priority == PriorityLevel.CRITICAL:
                base_score += 50
            if self.is_fresh:
                base_score += 20
        elif mode == OperationMode.ADAPTIVE:
            # Adaptive might consider profile affinity more
            if self.selected_profile_id and self.profile_scores.get(self.selected_profile_id, 0) > 70:
                base_score += 10

        return max(0, base_score) # Ensure score is not negative

    def __lt__(self, other: EnhancedTicketOpportunity) -> bool:
        # Higher score = higher priority, so for min-heap (PriorityQueue), less than means higher score.
        # This assumes OperationMode.ADAPTIVE is a sensible default for general queue sorting.
        # If different modes need different sorting in the queue, the queue itself might need a custom comparator.
        return self.calculate_score(OperationMode.ADAPTIVE) > other.calculate_score(OperationMode.ADAPTIVE)
