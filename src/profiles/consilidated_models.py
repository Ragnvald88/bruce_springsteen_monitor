# src/profiles/consolidated_models.py
"""
Consolidated Profile Models - StealthMaster AI v2.0
Combines all profile-related data structures in one place
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime


class ProfileQuality(Enum):
    """Profile quality levels with success rates"""
    LOW = (1, 0.3, 300)      # (tier, success_rate, cooldown_seconds)
    MEDIUM = (2, 0.6, 180)
    HIGH = (3, 0.8, 120)
    PREMIUM = (4, 0.95, 60)
    ULTRA = (5, 0.99, 30)

    @property
    def tier(self):
        return self.value[0]
    
    @property
    def success_rate(self):
        return self.value[1]
    
    @property
    def cooldown_seconds(self):
        return self.value[2]


class DataOptimizationLevel(Enum):
    """Data usage optimization levels"""
    MINIMAL = "minimal"      # Block everything except critical
    BALANCED = "balanced"    # Block ads, trackers, large images
    AGGRESSIVE = "aggressive" # Only load text and small images
    FULL = "full"           # Load everything (for auth pages)


class Platform(Enum):
    """Supported platforms"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"
    GENERIC = "generic"
    
    @property
    def domain(self):
        """Get primary domain for platform"""
        domains = {
            Platform.FANSALE: "fansale.it",
            Platform.TICKETMASTER: "ticketmaster.it",
            Platform.VIVATICKET: "vivaticket.com"
        }
        return domains.get(self, "example.com")


@dataclass
class SessionData:
    """Browser session data"""
    session_id: str
    profile_id: str
    platform: str
    created_at: datetime
    last_activity: datetime
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    
    # Performance metrics
    requests_made: int = 0
    data_used_mb: float = 0.0
    detections_encountered: int = 0
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if session is expired"""
        age = datetime.now() - self.created_at
        return age.total_seconds() > max_age_hours * 3600


@dataclass
class ProfileMetrics:
    """Performance metrics for a profile"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    
    # Platform-specific metrics
    platform_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Detection events
    captchas_encountered: int = 0
    captchas_solved: int = 0
    blocks_encountered: int = 0
    
    # Timing metrics
    avg_response_time_ms: float = 0.0
    fastest_success_ms: float = float('inf')
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts
    
    @property
    def detection_rate(self) -> float:
        """Calculate detection rate"""
        if self.total_attempts == 0:
            return 0.0
        detections = self.captchas_encountered + self.blocks_encountered
        return detections / self.total_attempts
    
    def update_platform_stats(self, platform: str, success: bool, response_time_ms: float):
        """Update platform-specific statistics"""
        if platform not in self.platform_stats:
            self.platform_stats[platform] = {
                'attempts': 0,
                'successes': 0,
                'avg_response_time': 0.0,
                'last_success': None,
                'last_attempt': None
            }
        
        stats = self.platform_stats[platform]
        stats['attempts'] += 1
        stats['last_attempt'] = datetime.now()
        
        if success:
            stats['successes'] += 1
            stats['last_success'] = datetime.now()
            
            if response_time_ms < self.fastest_success_ms:
                self.fastest_success_ms = response_time_ms
        
        # Update average response time
        old_avg = stats['avg_response_time']
        n = stats['attempts']
        stats['avg_response_time'] = (old_avg * (n - 1) + response_time_ms) / n