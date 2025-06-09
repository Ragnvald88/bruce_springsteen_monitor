# Domain Entity: Browser Profile
"""
Browser profile entity representing a stealth browser configuration.
Pure domain object with no external dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Set, Any
import uuid


class ProfileQuality(Enum):
    """Profile quality levels"""
    LOW = (1, 0.3, 300)      # (tier, success_rate, cooldown_seconds)
    MEDIUM = (2, 0.6, 180)
    HIGH = (3, 0.8, 120)
    PREMIUM = (4, 0.95, 60)

    @property
    def tier(self): return self.value[0]
    
    @property
    def success_rate(self): return self.value[1]
    
    @property
    def cooldown_seconds(self): return self.value[2]


class ProfileState(Enum):
    """Profile operational states"""
    PRISTINE = "pristine"
    HEALTHY = "healthy"
    SUSPICIOUS = "suspicious"
    DORMANT = "dormant"
    COMPROMISED = "compromised"
    EVOLVING = "evolving"


@dataclass
class SessionData:
    """Platform session data"""
    platform: str
    cookies: list = field(default_factory=list)
    auth_tokens: dict = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_valid: bool = False
    fingerprint_hash: Optional[str] = None


@dataclass
class BrowserProfile:
    """Browser profile with anti-detection features"""
    # Core Identity
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    browser: str = "Chrome"
    browser_version: str = "121.0.6167.85"
    os: str = "Windows 11"
    device_type: str = "desktop"
    
    # Display Settings
    viewport_width: int = 1920
    viewport_height: int = 980
    screen_width: int = 1920
    screen_height: int = 1080
    
    # Network & Location
    user_agent: str = ""
    locale: str = "it-IT"
    timezone: str = "Europe/Rome"
    accept_language: str = "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    
    # Hardware Simulation
    hardware_concurrency: int = 8
    device_memory: int = 8
    gpu_vendor: str = "NVIDIA"
    gpu_model: str = "GeForce RTX 3060"
    
    # Profile Management
    quality: ProfileQuality = ProfileQuality.MEDIUM
    state: ProfileState = ProfileState.PRISTINE
    platforms: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    use_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Session Data
    sessions: Dict[str, SessionData] = field(default_factory=dict)
    
    # Proxy Configuration (will be ProxyConfig object)
    proxy: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize computed fields"""
        if not self.user_agent:
            self.user_agent = self._generate_user_agent()
    
    def _generate_user_agent(self) -> str:
        """Generate consistent user agent"""
        if self.browser == "Chrome":
            if "Windows" in self.os:
                return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.browser_version} Safari/537.36"
            else:
                return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.browser_version} Safari/537.36"
        elif self.browser == "Firefox":
            major_version = self.browser_version.split('.')[0]
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{major_version}.0) Gecko/20100101 Firefox/{self.browser_version}"
        else:  # Edge
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.browser_version} Edg/{self.browser_version}"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def is_healthy(self) -> bool:
        """Check if profile is healthy"""
        return (
            self.success_rate >= 0.5 and
            self.failure_count < 10 and
            self.state not in [ProfileState.COMPROMISED, ProfileState.EVOLVING] and
            (not self.last_used or (datetime.utcnow() - self.last_used).days < 7)
        )
    
    def add_platform(self, platform: str):
        """Add platform to profile"""
        self.platforms.add(platform)
        
        # Initialize session data for platform
        if platform not in self.sessions:
            self.sessions[platform] = SessionData(
                platform=platform,
                cookies=[],
                auth_tokens={},
                last_updated=datetime.utcnow().isoformat(),
                is_valid=False,
                fingerprint_hash=None
            )
    
    def record_attempt(self, success: bool, platform: Optional[str] = None):
        """Record usage attempt"""
        self.use_count += 1
        self.last_used = datetime.utcnow()
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update platform session validity
        if platform and platform in self.sessions:
            self.sessions[platform].is_valid = success
            self.sessions[platform].last_updated = datetime.utcnow().isoformat()
    
    def get_session(self, platform: str) -> Optional[SessionData]:
        """Get session data for platform"""
        return self.sessions.get(platform)
    
    def clear_session(self, platform: str):
        """Clear session data for platform"""
        if platform in self.sessions:
            self.sessions[platform].cookies = []
            self.sessions[platform].auth_tokens = {}
            self.sessions[platform].is_valid = False