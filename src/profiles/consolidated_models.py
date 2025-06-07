# src/profiles/consolidated_models.py
"""
Consolidated Profile Models - StealthMaster AI Optimized
Combines: models.py + enums.py + types.py + config.py
Result: Single file with all profile data structures
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, TypedDict

# ============== ENUMS ==============

class ProfileQuality(Enum):
    """Simplified profile quality levels"""
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

class DataOptimizationLevel(Enum):
    """Data usage optimization levels"""
    MINIMAL = "minimal"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

class Platform(Enum):
    """Supported platforms with configurations"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"  
    VIVATICKET = "vivaticket"
    GENERIC = "generic"

    @property
    def requires_stealth(self) -> bool:
        """Check if platform needs enhanced stealth"""
        return self in [Platform.TICKETMASTER, Platform.VIVATICKET]
    
    @property
    def preferred_browsers(self) -> List[str]:
        """Get preferred browsers for platform"""
        preferences = {
            self.FANSALE: ["Chrome", "Firefox", "Edge"],
            self.TICKETMASTER: ["Chrome", "Edge"],
            self.VIVATICKET: ["Chrome", "Firefox"],
            self.GENERIC: ["Chrome"]
        }
        return preferences.get(self, ["Chrome"])
    
    @property
    def stealth_requirements(self) -> Dict[str, Any]:
        """Get stealth requirements for platform"""
        requirements = {
            self.FANSALE: {
                "aggressive_stealth": False,
                "browser_preferences": ["Chrome", "Firefox", "Edge"],
                "requires_referrer": True,
                "supports_mobile": False,
                "min_viewport_width": 1280,
                "preferred_locale": "it-IT"
            },
            self.TICKETMASTER: {
                "aggressive_stealth": True,
                "browser_preferences": ["Chrome", "Edge"],
                "requires_referrer": True,
                "supports_mobile": False,
                "min_viewport_width": 1366,
                "preferred_locale": "en-US",
                "requires_webgl": True,
                "requires_canvas": True
            },
            self.VIVATICKET: {
                "aggressive_stealth": True,
                "browser_preferences": ["Chrome", "Firefox"],
                "requires_referrer": True,
                "supports_mobile": False,
                "min_viewport_width": 1280,
                "preferred_locale": "it-IT"
            },
            self.GENERIC: {
                "aggressive_stealth": False,
                "browser_preferences": ["Chrome"],
                "requires_referrer": False,
                "supports_mobile": True,
                "min_viewport_width": 1024,
                "preferred_locale": "en-US"
            }
        }
        return requirements.get(self, requirements[self.GENERIC])

# ============== TYPE DEFINITIONS ==============

class SessionData(TypedDict):
    """Platform session data structure"""
    platform: str
    cookies: List[Dict[str, Any]]
    auth_tokens: Dict[str, str]
    last_updated: str
    is_valid: bool
    fingerprint_hash: Optional[str]

class ProfileMetrics(TypedDict):
    """Profile performance metrics"""
    attempts: int
    successes: int
    failures: int
    last_success: Optional[str]
    avg_response_time_ms: float
    detection_events: int

# ============== CONFIGURATION CLASSES ==============

@dataclass
class ProxyConfig:
    """Simplified proxy configuration"""
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"
    country_code: Optional[str] = None
    rotation_endpoint: Optional[str] = None
    sticky_session: bool = True
    proxy_provider: Optional[str] = None
    
    def get_proxy_url(self, session_id: Optional[str] = None) -> Optional[str]:
        """Get formatted proxy URL"""
        if not self.host or not self.port:
            return None
        
        auth = ""
        if self.username and self.password:
            username = self.username
            if session_id:
                username = f"{self.username}-session-{session_id}"
            if self.country_code:
                username = f"{username}-country-{self.country_code}"
            auth = f"{username}:{self.password}@"
        
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"

@dataclass
class BrowserConfig:
    """Essential browser configuration"""
    browser_type: str = "chromium"
    headless: bool = True
    stealth_mode: bool = True
    user_data_dir: Optional[str] = None
    extra_args: List[str] = field(default_factory=list)

# ============== MAIN PROFILE MODEL ==============

@dataclass  
class BrowserProfile:
    """Streamlined browser profile with essential fields only"""
    
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
    
    # Proxy Configuration
    proxy: Optional[ProxyConfig] = None
    
    # Profile Management
    quality: ProfileQuality = ProfileQuality.MEDIUM
    platforms: Set[Platform] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    use_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Session Data
    sessions: Dict[str, SessionData] = field(default_factory=dict)
    
    # Optimization
    data_optimization: DataOptimizationLevel = DataOptimizationLevel.BALANCED
    
    def __post_init__(self):
        """Initialize computed fields"""
        if not self.user_agent:
            self.user_agent = self._generate_user_agent()
        
        # Set default platforms
        if not self.platforms:
            self.platforms = {Platform.FANSALE}
    
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
            (not self.last_used or (datetime.now() - self.last_used).days < 7)
        )
    
    def add_platform(self, platform: Platform):
        """Add platform to profile"""
        self.platforms.add(platform)
        
        # Initialize session data for platform
        if platform.value not in self.sessions:
            self.sessions[platform.value] = SessionData(
                platform=platform.value,
                cookies=[],
                auth_tokens={},
                last_updated=datetime.now().isoformat(),
                is_valid=False,
                fingerprint_hash=None
            )
    
    def record_attempt(self, success: bool, platform: Optional[Platform] = None):
        """Record usage attempt"""
        self.use_count += 1
        self.last_used = datetime.now()
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update platform session validity
        if platform and platform.value in self.sessions:
            self.sessions[platform.value]['is_valid'] = success
            self.sessions[platform.value]['last_updated'] = datetime.now().isoformat()
    
    def get_session(self, platform: Platform) -> Optional[SessionData]:
        """Get session data for platform"""
        return self.sessions.get(platform.value)
    
    def clear_session(self, platform: Platform):
        """Clear session data for platform"""
        if platform.value in self.sessions:
            self.sessions[platform.value]['cookies'] = []
            self.sessions[platform.value]['auth_tokens'] = {}
            self.sessions[platform.value]['is_valid'] = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = {
            'profile_id': self.profile_id,
            'browser': self.browser,
            'browser_version': self.browser_version,
            'os': self.os,
            'device_type': self.device_type,
            'viewport_width': self.viewport_width,
            'viewport_height': self.viewport_height,
            'user_agent': self.user_agent,
            'locale': self.locale,
            'timezone': self.timezone,
            'quality': self.quality.value,
            'platforms': [p.value for p in self.platforms],
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'use_count': self.use_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'sessions': self.sessions
        }
        
        if self.proxy:
            data['proxy'] = {
                'host': self.proxy.host,
                'port': self.proxy.port,
                'username': self.proxy.username,
                'proxy_type': self.proxy.proxy_type
            }
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrowserProfile':
        """Create profile from dictionary"""
        # Parse platforms
        platforms = {Platform(p) for p in data.get('platforms', ['fansale'])}
        
        # Parse dates
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        last_used = datetime.fromisoformat(data['last_used']) if data.get('last_used') else None
        
        # Parse proxy
        proxy = None
        if data.get('proxy'):
            proxy_data = data['proxy']
            proxy = ProxyConfig(
                host=proxy_data.get('host', ''),
                port=proxy_data.get('port', 0),
                username=proxy_data.get('username'),
                proxy_type=proxy_data.get('proxy_type', 'http')
            )
        
        # Parse quality
        quality = ProfileQuality.MEDIUM
        if data.get('quality'):
            for q in ProfileQuality:
                if q.value == data['quality']:
                    quality = q
                    break
        
        return cls(
            profile_id=data['profile_id'],
            browser=data.get('browser', 'Chrome'),
            browser_version=data.get('browser_version', '121.0.6167.85'),
            os=data.get('os', 'Windows 11'),
            device_type=data.get('device_type', 'desktop'),
            viewport_width=data.get('viewport_width', 1920),
            viewport_height=data.get('viewport_height', 980),
            user_agent=data.get('user_agent', ''),
            locale=data.get('locale', 'it-IT'),
            timezone=data.get('timezone', 'Europe/Rome'),
            quality=quality,
            platforms=platforms,
            created_at=created_at,
            last_used=last_used,
            use_count=data.get('use_count', 0),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            sessions=data.get('sessions', {}),
            proxy=proxy
        )

# ============== FACTORY FUNCTIONS ==============

def create_optimized_profile(platform: Platform, quality: ProfileQuality = ProfileQuality.MEDIUM) -> BrowserProfile:
    """Create profile optimized for specific platform"""
    
    profile = BrowserProfile(quality=quality)
    profile.add_platform(platform)
    
    # Platform-specific optimizations
    if platform == Platform.FANSALE:
        profile.locale = "it-IT"
        profile.timezone = "Europe/Rome"
        profile.browser = "Chrome"
    elif platform == Platform.TICKETMASTER:
        profile.browser = "Chrome"
        profile.quality = ProfileQuality.HIGH  # Ticketmaster needs higher quality
        profile.data_optimization = DataOptimizationLevel.AGGRESSIVE
    elif platform == Platform.VIVATICKET:
        profile.browser = "Chrome"
        profile.locale = "it-IT"
    
    return profile

def create_profiles_batch(platform: Platform, count: int = 5) -> List[BrowserProfile]:
    """Create batch of profiles for platform"""
    profiles = []
    
    for i in range(count):
        quality = ProfileQuality.MEDIUM if i < 3 else ProfileQuality.HIGH
        profile = create_optimized_profile(platform, quality)
        profiles.append(profile)
    
    return profiles

# Export everything
__all__ = [
    'ProfileQuality', 'DataOptimizationLevel', 'Platform',
    'SessionData', 'ProfileMetrics', 
    'ProxyConfig', 'BrowserConfig', 'BrowserProfile',
    'create_optimized_profile', 'create_profiles_batch'
]