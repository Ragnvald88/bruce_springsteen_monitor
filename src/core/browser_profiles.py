# src/core/browser_profiles.py v1.0 - Enhanced for Ticket Bot Excellence
from __future__ import annotations
import asyncio
import dataclasses
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple, Callable, Set, TypedDict
import random
import uuid
import logging
import json
import re
from datetime import datetime, timedelta
import hashlib
import copy
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict
import yaml
import aiofiles
import base64
from cryptography.fernet import Fernet
import pickle
import zstandard as zstd
from playwright.async_api import BrowserContext, Cookie

# --- Imports from advanced_profile_system ---
try:
    from .advanced_profile_system import (
        DynamicProfile,
        MutationStrategy,
        ProfileState,
        DetectionEvent,
        FingerprintComponent,
        BehavioralModel
    )
except ImportError:
    from advanced_profile_system import (
        DynamicProfile,
        MutationStrategy,
        ProfileState,
        DetectionEvent,
        FingerprintComponent,
        BehavioralModel
    )

logger = logging.getLogger(__name__)

# --- Enums ---
class ProfileQuality(Enum):
    """Profile quality tiers with enhanced metadata"""
    LOW = (1, 0.1, 300)      # (tier, success_multiplier, cooldown_seconds)
    MEDIUM = (2, 0.5, 180)   
    HIGH = (3, 0.8, 120)     
    PREMIUM = (4, 1.0, 60)   
    
    @property
    def tier(self):
        return self.value[0]
    
    @property
    def success_multiplier(self):
        return self.value[1]
    
    @property
    def cooldown_seconds(self):
        return self.value[2]

class DataOptimizationLevel(Enum):
    """Data usage optimization levels"""
    OFF = "off"
    MINIMAL = "minimal"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

class Platform(Enum):
    """Supported ticketing platforms"""
    FANSALE = "fansale"
    TICKETMASTER = "ticketmaster"
    VIVATICKET = "vivaticket"
    
    @property
    def login_url(self):
        urls = {
            "fansale": "https://www.fansale.it/login",
            "ticketmaster": "https://shop.ticketmaster.it/login",
            "vivaticket": "https://shop.vivaticket.com/login"
        }
        return urls.get(self.value, "")

# --- Type Definitions ---
class SessionData(TypedDict):
    """Structure for platform session data"""
    platform: str
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    auth_tokens: Dict[str, str]
    last_updated: str
    is_valid: bool
    user_id: Optional[str]

# --- Proxy Configuration ---
@dataclass
class ProxyConfig:
    """Enhanced proxy configuration with rotation support"""
    proxy_type: str = "http"
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_endpoint: Optional[str] = None
    sticky_session: bool = True
    country_code: Optional[str] = None
    
    def get_proxy_url(self, session_id: Optional[str] = None) -> Optional[str]:
        """Get formatted proxy URL with session support"""
        if not self.host or not self.port:
            return None
            
        auth = ""
        if self.username and self.password:
            # Support for proxy providers with session/country parameters
            username_parts = [self.username]
            if session_id and self.sticky_session:
                username_parts.append(f"session-{session_id}")
            if self.country_code:
                username_parts.append(f"country-{self.country_code}")
            
            final_username = "-".join(username_parts)
            auth = f"{final_username}:{self.password}@"
            
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"
    
    def rotate_session(self) -> str:
        """Generate new session ID for proxy rotation"""
        return str(uuid.uuid4())[:8]

# --- Enhanced Browser Profile ---
@dataclass
class BrowserProfile:
    """Enhanced browser profile with session management"""
    # Basic identification
    name: str
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Browser fingerprint
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    screen_width: int = 1920
    screen_height: int = 1080
    avail_width: Optional[int] = None
    avail_height: Optional[int] = None
    device_pixel_ratio: float = 1.0
    color_depth: int = 24
    pixel_depth: int = 24
    js_platform: str = "Win32"
    hardware_concurrency: int = 8
    device_memory: Optional[int] = 8
    
    # Localization
    timezone: str = "Europe/Rome"
    locale: str = "it-IT"
    languages_override: List[str] = field(default_factory=lambda: ["it-IT", "it", "en-US", "en"])
    
    # WebGL fingerprint
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None
    
    # Client Hints
    sec_ch_ua: Optional[str] = None
    sec_ch_ua_mobile: Optional[str] = "?0"
    sec_ch_ua_platform: Optional[str] = None
    sec_ch_ua_platform_version: Optional[str] = None
    sec_ch_ua_full_version_list: Optional[str] = None
    
    # Advanced fingerprinting
    canvas_fingerprint: Optional[str] = None
    audio_fingerprint: Optional[str] = None
    webrtc_ips: List[str] = field(default_factory=list)
    
    # Additional properties
    extra_js_props: Dict[str, Any] = field(default_factory=dict)
    extra_http_headers: Dict[str, str] = field(default_factory=dict)
    browser_args: List[str] = field(default_factory=list)
    
    # Network configuration
    proxy_config: Optional[ProxyConfig] = None
    proxy_session_id: Optional[str] = None
    accept_language: Optional[str] = None
    accept_encoding: str = "gzip, deflate, br"
    
    # Profile metadata
    quality: ProfileQuality = ProfileQuality.MEDIUM
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Platform-specific data
    platform_sessions: Dict[str, SessionData] = field(default_factory=dict)
    platform_stats: Dict[str, Dict[str, Any]] = field(default_factory=lambda: defaultdict(lambda: {
        'attempts': 0, 'successes': 0, 'failures': 0,
        'last_success': None, 'last_failure': None,
        'avg_response_time_ms': 0.0, 'detection_events': []
    }))
    
    # Optimization settings
    data_optimization_level: DataOptimizationLevel = DataOptimizationLevel.BALANCED
    block_resources: Set[str] = field(default_factory=lambda: set())
    
    # Persistent context
    persistent_context_dir: Optional[Path] = None
    _context_encryption_key: Optional[bytes] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Initialize computed fields"""
        if self.avail_width is None:
            self.avail_width = self.screen_width
        if self.avail_height is None:
            self.avail_height = self.screen_height - 40  # Typical taskbar
        
        # Generate encryption key for sensitive data
        if self._context_encryption_key is None:
            self._context_encryption_key = Fernet.generate_key()
        
        # Set Italian-focused HTTP headers
        if not self.accept_language:
            self.accept_language = "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
        
        # Initialize persistent context directory
        if self.persistent_context_dir is None:
            self.persistent_context_dir = Path(f"browser_contexts/{self.profile_id}")
    
    def get_context_params(self) -> Dict[str, Any]:
        """Get parameters for Playwright browser context"""
        params = {
            'viewport': {'width': self.viewport_width, 'height': self.viewport_height},
            'screen': {'width': self.screen_width, 'height': self.screen_height},
            'user_agent': self.user_agent,
            'locale': self.locale,
            'timezone_id': self.timezone,
            'color_scheme': 'light',
            'device_scale_factor': self.device_pixel_ratio,
            'has_touch': False,
            'is_mobile': False,
        }
        
        # Proxy configuration
        if self.proxy_config:
            proxy_url = self.proxy_config.get_proxy_url(self.proxy_session_id)
            if proxy_url:
                params['proxy'] = {'server': proxy_url}
        
        # Headers including Client Hints
        headers = dict(self.extra_http_headers)
        headers['Accept-Language'] = self.accept_language
        headers['Accept-Encoding'] = self.accept_encoding
        
        if self.sec_ch_ua:
            headers['sec-ch-ua'] = self.sec_ch_ua
        if self.sec_ch_ua_mobile:
            headers['sec-ch-ua-mobile'] = self.sec_ch_ua_mobile
        if self.sec_ch_ua_platform:
            headers['sec-ch-ua-platform'] = self.sec_ch_ua_platform
        
        params['extra_http_headers'] = headers
        
        # Permissions
        params['permissions'] = ['geolocation', 'notifications', 'camera', 'microphone']
        params['geolocation'] = {'latitude': 41.9028, 'longitude': 12.4964}  # Rome
        
        return params
    
    def get_launch_options(self) -> Dict[str, Any]:
        """Get browser launch options optimized for stealth"""
        args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--enable-features=NetworkService,NetworkServiceInProcess',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--password-store=basic',
            '--use-mock-keychain',
            '--force-color-profile=srgb',
            f'--window-size={self.viewport_width},{self.viewport_height}',
        ]
        
        # Add optimization flags
        if self.data_optimization_level in [DataOptimizationLevel.BALANCED, DataOptimizationLevel.AGGRESSIVE]:
            args.extend([
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-features=CalculateNativeWinOcclusion',
            ])
        
        args.extend(self.browser_args)
        
        return {
            'args': args,
            'chromium_sandbox': False,
            'handle_sigint': False,
            'handle_sigterm': False,
            'handle_sighup': False,
        }
    
    def get_resource_block_patterns(self) -> List[str]:
        """Get resource blocking patterns based on optimization level"""
        patterns = list(self.block_resources)
        
        if self.data_optimization_level == DataOptimizationLevel.AGGRESSIVE:
            patterns.extend([
                '*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.svg',
                '*.mp4', '*.avi', '*.mov', '*.webm',
                '*.woff', '*.woff2', '*.ttf', '*.otf',
                '*analytics*', '*tracking*', '*doubleclick*', '*facebook*',
                '*google-analytics*', '*hotjar*', '*clarity*', '*segment*'
            ])
        elif self.data_optimization_level == DataOptimizationLevel.BALANCED:
            patterns.extend([
                '*.mp4', '*.avi', '*.mov',
                '*analytics*', '*tracking*', '*doubleclick*'
            ])
        elif self.data_optimization_level == DataOptimizationLevel.MINIMAL:
            patterns.extend(['*analytics*', '*tracking*'])
            
        return patterns
    
    def should_rotate_proxy(self) -> bool:
        """Check if proxy should be rotated"""
        if not self.proxy_config or not self.last_used:
            return False
        
        # Rotate based on time or failure rate
        time_based = (datetime.utcnow() - self.last_used).total_seconds() > 1800  # 30 minutes
        
        total_attempts = sum(stats['attempts'] for stats in self.platform_stats.values())
        total_failures = sum(stats['failures'] for stats in self.platform_stats.values())
        failure_based = total_attempts > 10 and (total_failures / total_attempts) > 0.3
        
        return time_based or failure_based
    
    def rotate_proxy(self):
        """Rotate proxy session"""
        if self.proxy_config:
            self.proxy_session_id = self.proxy_config.rotate_session()
            logger.info(f"Profile {self.profile_id}: Rotated proxy session to {self.proxy_session_id}")
    
    async def save_session(self, platform: Platform, context: BrowserContext):
        """Save platform session data from browser context"""
        try:
            # Get all cookies
            cookies = await context.cookies()
            
            # Get storage state (includes localStorage and sessionStorage)
            storage_state = await context.storage_state()
            
            session_data: SessionData = {
                'platform': platform.value,
                'cookies': cookies,
                'local_storage': storage_state.get('origins', [{}])[0].get('localStorage', {}),
                'session_storage': {},  # Playwright doesn't expose sessionStorage in storage_state
                'auth_tokens': self._extract_auth_tokens(cookies, storage_state),
                'last_updated': datetime.utcnow().isoformat(),
                'is_valid': True,
                'user_id': self._extract_user_id(cookies, storage_state)
            }
            
            self.platform_sessions[platform.value] = session_data
            
            # Persist to disk if persistent context enabled
            if self.persistent_context_dir:
                await self._save_encrypted_session(platform, session_data)
                
            logger.info(f"Profile {self.profile_id}: Saved session for {platform.value}")
            
        except Exception as e:
            logger.error(f"Profile {self.profile_id}: Failed to save session for {platform.value}: {e}")
    
    async def restore_session(self, platform: Platform, context: BrowserContext) -> bool:
        """Restore platform session to browser context"""
        try:
            session_data = self.platform_sessions.get(platform.value)
            
            if not session_data:
                # Try loading from disk
                session_data = await self._load_encrypted_session(platform)
                
            if not session_data or not session_data.get('is_valid'):
                return False
            
            # Check session age
            last_updated = datetime.fromisoformat(session_data['last_updated'])
            if (datetime.utcnow() - last_updated).total_seconds() > 86400:  # 24 hours
                logger.warning(f"Profile {self.profile_id}: Session for {platform.value} is too old")
                return False
            
            # Restore cookies
            if session_data.get('cookies'):
                await context.add_cookies(session_data['cookies'])
            
            logger.info(f"Profile {self.profile_id}: Restored session for {platform.value}")
            return True
            
        except Exception as e:
            logger.error(f"Profile {self.profile_id}: Failed to restore session for {platform.value}: {e}")
            return False
    
    def record_usage(self, success: bool, response_time_ms: float = 0,
                    platform: str = "", error: Optional[str] = None,
                    detected: bool = False):
        """Record usage statistics with enhanced tracking"""
        self.last_used = datetime.utcnow()
        
        if platform:
            stats = self.platform_stats[platform]
            stats['attempts'] += 1
            
            if success:
                stats['successes'] += 1
                stats['last_success'] = datetime.utcnow().isoformat()
            else:
                stats['failures'] += 1
                stats['last_failure'] = datetime.utcnow().isoformat()
                if error:
                    stats['last_error'] = error
            
            # Update average response time
            if response_time_ms > 0:
                current_avg = stats['avg_response_time_ms']
                total_attempts = stats['attempts']
                stats['avg_response_time_ms'] = ((current_avg * (total_attempts - 1)) + response_time_ms) / total_attempts
            
            # Track detection events
            if detected:
                stats['detection_events'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': error
                })
    
    def get_success_rate(self, platform: Optional[str] = None) -> float:
        """Calculate success rate for platform or overall"""
        if platform:
            stats = self.platform_stats.get(platform, {})
            attempts = stats.get('attempts', 0)
            successes = stats.get('successes', 0)
        else:
            attempts = sum(s.get('attempts', 0) for s in self.platform_stats.values())
            successes = sum(s.get('successes', 0) for s in self.platform_stats.values())
        
        return successes / attempts if attempts > 0 else 0.0
    
    def _extract_auth_tokens(self, cookies: List[Dict], storage_state: Dict) -> Dict[str, str]:
        """Extract authentication tokens from cookies and storage"""
        tokens = {}
        
        # Common auth cookie names
        auth_cookie_names = ['auth_token', 'session_id', 'access_token', 'jwt', 'sid']
        for cookie in cookies:
            if any(name in cookie.get('name', '').lower() for name in auth_cookie_names):
                tokens[cookie['name']] = cookie['value']
        
        # Check localStorage for tokens
        for origin in storage_state.get('origins', []):
            for key, value in origin.get('localStorage', {}).items():
                if any(name in key.lower() for name in auth_cookie_names):
                    tokens[key] = value
        
        return tokens
    
    def _extract_user_id(self, cookies: List[Dict], storage_state: Dict) -> Optional[str]:
        """Extract user ID from cookies or storage"""
        # Platform-specific extraction logic
        for cookie in cookies:
            if 'user_id' in cookie.get('name', '').lower():
                return cookie.get('value')
        
        return None
    
    async def _save_encrypted_session(self, platform: Platform, session_data: SessionData):
        """Save encrypted session data to disk"""
        try:
            self.persistent_context_dir.mkdir(parents=True, exist_ok=True)
            session_file = self.persistent_context_dir / f"{platform.value}_session.enc"
            
            # Compress and encrypt
            fernet = Fernet(self._context_encryption_key)
            compressed = zstd.compress(json.dumps(session_data).encode())
            encrypted = fernet.encrypt(compressed)
            
            async with aiofiles.open(session_file, 'wb') as f:
                await f.write(encrypted)
                
        except Exception as e:
            logger.error(f"Failed to save encrypted session: {e}")
    
    async def _load_encrypted_session(self, platform: Platform) -> Optional[SessionData]:
        """Load encrypted session data from disk"""
        try:
            session_file = self.persistent_context_dir / f"{platform.value}_session.enc"
            if not session_file.exists():
                return None
            
            async with aiofiles.open(session_file, 'rb') as f:
                encrypted = await f.read()
            
            # Decrypt and decompress
            fernet = Fernet(self._context_encryption_key)
            compressed = fernet.decrypt(encrypted)
            decompressed = zstd.decompress(compressed)
            
            return json.loads(decompressed.decode())
            
        except Exception as e:
            logger.error(f"Failed to load encrypted session: {e}")
            return None

# --- Profile Scoring Configuration ---
@dataclass
class ProfileScoringConfig:
    """Enhanced scoring configuration for profile selection"""
    base_score: float = 100.0
    
    # State-based modifiers
    state_modifiers: Dict[ProfileState, float] = field(default_factory=lambda: {
        ProfileState.PRISTINE: 20.0,
        ProfileState.HEALTHY: 30.0,
        ProfileState.SUSPICIOUS: -40.0,
        ProfileState.DORMANT: -20.0,
        ProfileState.COMPROMISED: -1000.0,
        ProfileState.EVOLVING: -500.0
    })
    
    # Platform-specific bonuses
    platform_bonuses: Dict[str, float] = field(default_factory=lambda: {
        'fansale': 10.0,      # Bonus for profiles successful on each platform
        'ticketmaster': 15.0,  # Ticketmaster is harder, so bigger bonus
        'vivaticket': 12.0
    })
    
    # Session-based scoring
    has_valid_session_bonus: float = 50.0  # Major bonus for having logged-in session
    session_age_penalty_per_hour: float = 0.5  # Penalty for old sessions
    
    # Performance metrics
    success_rate_weight: float = 40.0
    avg_response_time_weight: float = 20.0  # Faster is better
    consecutive_failure_penalty: float = 10.0
    
    # Risk assessment
    avg_risk_score_penalty_weight: float = 25.0
    drift_penalty: float = 50.0
    proxy_rotation_bonus: float = 15.0  # Bonus for fresh proxy
    
    # Time-based factors
    recency_bonus_max: float = 25.0
    recency_threshold_hours: float = 12.0
    peak_time_bonus: float = 20.0  # Bonus during ticket release times

# --- Enhanced Profile Manager Configuration ---
@dataclass
class ProfileManagerConfig:
    """Configuration for ProfileManager with session management"""
    # Pool management
    num_target_profiles: int = 20
    profiles_per_platform: int = 5  # Dedicated profiles per platform
    evolution_interval_seconds: int = 900
    
    # Persistence
    persistence_filepath: str = "profiles_backup.json"
    session_backup_dir: str = "session_backups"
    
    # Scoring
    scoring_config: ProfileScoringConfig = field(default_factory=ProfileScoringConfig)
    
    # Cooldowns with variance (base_seconds, variance_factor)
    cooldowns_seconds: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        DetectionEvent.HARD_BLOCK.value: (3600 * 4, 0.3),     # 4 hours
        DetectionEvent.CAPTCHA_CHALLENGE.value: (1800, 0.3),  # 30 minutes
        DetectionEvent.RATE_LIMIT.value: (600, 0.3),          # 10 minutes
        DetectionEvent.SUCCESS.value: (30, 0.2),              # 30 seconds
        "post_mutation": (900, 0.3),                          # 15 minutes
        "task_selection": (10, 0.2),                          # 10 seconds
        "login_required": (300, 0.2),                         # 5 minutes
    })
    
    # Evolution and health
    compromise_threshold_pct: float = 0.20
    min_pool_size_for_replacement: int = 10
    max_pool_size_multiplier: float = 1.5
    evolution_max_retries: int = 3
    evolution_retry_backoff_base_seconds: int = 60
    evolution_interval_jitter_factor: float = 0.2
    
    # Session management
    session_validation_interval_seconds: int = 1800  # 30 minutes
    max_session_age_hours: int = 24
    auto_login_retry_limit: int = 3
    
    # Platform-specific settings
    platform_priorities: Dict[str, float] = field(default_factory=lambda: {
        'ticketmaster': 1.0,  # Highest priority
        'fansale': 0.8,
        'vivaticket': 0.7
    })
    
    # Advanced features
    enable_tls_rotation: bool = True
    enable_behavioral_warmup: bool = True
    enable_session_preloading: bool = True
    warmup_sites: List[str] = field(default_factory=lambda: [
        "https://www.google.it",
        "https://www.repubblica.it",
        "https://www.corriere.it",
        "https://www.amazon.it"
    ])

# --- Enhanced Profile Manager ---
class ProfileManager:
    """Advanced profile manager with session and platform management"""
    
    def __init__(self, config: Optional[ProfileManagerConfig] = None, base_profile_template: Optional[Dict] = None):
        self.config = config or ProfileManagerConfig()
        self.dynamic_profiles: List[DynamicProfile] = []
        self.static_profiles: Dict[str, BrowserProfile] = {}  # profile_id -> BrowserProfile
        self.mutation_strategy = MutationStrategy()
        
        # Cooldown management
        self.profile_cooldowns: Dict[str, datetime] = {}
        
        # Platform session pools
        self.platform_pools: Dict[str, List[str]] = defaultdict(list)  # platform -> [profile_ids]
        self.session_ready_profiles: Dict[str, Set[str]] = defaultdict(set)  # platform -> {profile_ids}
        
        # Base template
        self.base_profile_template = base_profile_template or self._get_default_base_template()
        
        # Task management
        self._evolution_task: Optional[asyncio.Task] = None
        self._session_validation_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Locks
        self._profiles_lock = asyncio.Lock()
        self._cooldown_lock = asyncio.Lock()
        self._session_lock = asyncio.Lock()
        
        # TLS fingerprint rotation
        self._tls_fingerprints = self._load_tls_fingerprints()
        self._current_tls_index = 0
        
        # Initialize
        asyncio.create_task(self._initialize_profile_pool())
        
        logger.info(f"ProfileManager V2 initialized. Target: {self.config.num_target_profiles} profiles, "
                   f"{self.config.profiles_per_platform} per platform")
    
    def _get_default_base_template(self) -> Dict[str, Any]:
        """Get Italian-focused default template"""
        return {
            "os_name": "Windows",
            "browser_name": "Chrome",
            "device_class": "mid_range_desktop",
            "country": "IT",
            "language": "it-IT"
        }
    
    def _load_tls_fingerprints(self) -> List[Dict[str, Any]]:
        """Load realistic TLS fingerprints"""
        # These would be loaded from a database of real browser fingerprints
        return [
            {
                "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
                "h2_settings": "1:65536,2:0,3:1000,4:6291456,6:262144",
                "h2_window_update": 15663105,
                "h2_priority": {"stream_id": 3, "exclusive": 1, "parent_stream_id": 0, "weight": 201}
            },
            # Add more fingerprints from real browsers
        ]
    
    async def _initialize_profile_pool(self):
        """Initialize profile pool with platform distribution"""
        async with self._profiles_lock:
            # Try loading from disk first
            loaded = await self._load_profiles_from_disk()
            
            if loaded:
                logger.info(f"Loaded {len(self.dynamic_profiles)} profiles from disk")
                # Rebuild static profiles
                for dp in self.dynamic_profiles:
                    sp = self._adapt_dynamic_to_static(dp)
                    self.static_profiles[dp.id] = sp
                    # Categorize by platform sessions
                    for platform in Platform:
                        if platform.value in sp.platform_sessions:
                            self.platform_pools[platform.value].append(dp.id)
                            if sp.platform_sessions[platform.value].get('is_valid'):
                                self.session_ready_profiles[platform.value].add(dp.id)
            
            # Create new profiles if needed
            profiles_needed = self.config.num_target_profiles - len(self.dynamic_profiles)
            
            if profiles_needed > 0:
                logger.info(f"Creating {profiles_needed} new profiles")
                
                # Distribute across platforms
                for i in range(profiles_needed):
                    platform_index = i % len(Platform)
                    platform = list(Platform)[platform_index]
                    
                    profile = await self._create_platform_optimized_profile(platform)
                    if profile:
                        self.dynamic_profiles.append(profile['dynamic'])
                        self.static_profiles[profile['dynamic'].id] = profile['static']
                        self.platform_pools[platform.value].append(profile['dynamic'].id)
            
            logger.info(f"Profile pool initialized. Distribution: {dict(self.platform_pools)}")
    
    async def _create_platform_optimized_profile(self, platform: Platform) -> Optional[Dict[str, Any]]:
        """Create profile optimized for specific platform"""
        try:
            # Platform-specific optimizations
            base_template = copy.deepcopy(self.base_profile_template)
            
            if platform == Platform.TICKETMASTER:
                # Ticketmaster specific settings
                base_template['browser_name'] = random.choice(['Chrome', 'Edge'])
                base_template['device_class'] = random.choice(['high_end_desktop', 'high_end_laptop'])
            elif platform == Platform.FANSALE:
                # Fansale preferences
                base_template['browser_name'] = 'Chrome'
                base_template['device_class'] = random.choice(['mid_range_desktop', 'mid_range_laptop'])
            else:  # Vivaticket
                base_template['browser_name'] = random.choice(['Chrome', 'Firefox'])
                base_template['device_class'] = 'mid_range_desktop'
            
            # Create dynamic profile
            profile_id = f"{platform.value}_{str(uuid.uuid4())[:8]}"
            dynamic_profile = DynamicProfile(
                mutation_strategy=self.mutation_strategy,
                base_profile_dict=base_template,
                profile_id=profile_id
            )
            
            # Create static profile
            static_profile = self._adapt_dynamic_to_static(dynamic_profile)
            
            # Platform-specific enhancements
            static_profile.timezone = "Europe/Rome"
            static_profile.locale = "it-IT"
            static_profile.languages_override = ["it-IT", "it", "en-US", "en"]
            
            # Assign quality based on randomization
            static_profile.quality = random.choices(
                list(ProfileQuality),
                weights=[0.1, 0.3, 0.4, 0.2],  # Prefer HIGH quality
                k=1
            )[0]
            
            # Setup proxy if available
            if hasattr(self.config, 'proxy_configs') and self.config.proxy_configs:
                static_profile.proxy_config = random.choice(self.config.proxy_configs)
                static_profile.proxy_session_id = static_profile.proxy_config.rotate_session()
            
            return {
                'dynamic': dynamic_profile,
                'static': static_profile
            }
            
        except Exception as e:
            logger.error(f"Failed to create platform profile: {e}", exc_info=True)
            return None
    
    def _adapt_dynamic_to_static(self, dynamic_profile: DynamicProfile) -> BrowserProfile:
        """Convert DynamicProfile to BrowserProfile with enhancements"""
        js_data = dynamic_profile.get_stealth_init_js_profile_data()
        
        # Extract screen dimensions
        screen_res = js_data.get('screen_resolution', (1920, 1080))
        screen_width = screen_res[0] if isinstance(screen_res, tuple) else 1920
        screen_height = screen_res[1] if isinstance(screen_res, tuple) else 1080
        
        static_profile = BrowserProfile(
            name=f"{js_data.get('browser_name', 'Unknown')}_{dynamic_profile.device_class}",
            profile_id=dynamic_profile.id,
            user_agent=js_data.get('user_agent', ''),
            viewport_width=int(screen_width * 0.95),
            viewport_height=int(screen_height * 0.85),
            screen_width=screen_width,
            screen_height=screen_height,
            avail_width=js_data.get('avail_width', screen_width),
            avail_height=js_data.get('avail_height', screen_height - 40),
            device_pixel_ratio=float(js_data.get('device_pixel_ratio', 1.0)),
            color_depth=int(js_data.get('color_depth', 24)),
            pixel_depth=int(js_data.get('pixel_depth', 24)),
            js_platform=js_data.get('js_platform', 'Win32'),
            hardware_concurrency=int(js_data.get('hardware_concurrency', 8)),
            device_memory=js_data.get('device_memory', 8),
            timezone=js_data.get('timezone', 'Europe/Rome'),
            locale=js_data.get('locale', 'it-IT'),
            languages_override=js_data.get('languages_override', ['it-IT', 'it', 'en-US', 'en']),
            webgl_vendor=js_data.get('webgl_vendor'),
            webgl_renderer=js_data.get('webgl_renderer'),
            canvas_fingerprint=js_data.get('canvas_fingerprint'),
            audio_fingerprint=js_data.get('audio_fingerprint'),
            webrtc_ips=js_data.get('webrtc_ips', []),
            sec_ch_ua=js_data.get('sec_ch_ua'),
            sec_ch_ua_mobile=js_data.get('sec_ch_ua_mobile', '?0'),
            sec_ch_ua_platform=js_data.get('sec_ch_ua_platform'),
            sec_ch_ua_platform_version=js_data.get('sec_ch_ua_platform_version'),
            sec_ch_ua_full_version_list=js_data.get('sec_ch_ua_full_version_list'),
            extra_js_props=js_data.get('extra_js_props', {})
        )
        
        # Generate realistic Accept-Language header
        if static_profile.languages_override:
            parts = []
            q_values = [1.0, 0.9, 0.8, 0.7]
            for i, lang in enumerate(static_profile.languages_override[:4]):
                if i == 0:
                    parts.append(lang)
                else:
                    parts.append(f"{lang};q={q_values[min(i, len(q_values)-1)]:.1f}")
            static_profile.accept_language = ','.join(parts)
        
        return static_profile
    
    async def get_profile_for_platform(self, platform: Platform, require_session: bool = True) -> Optional[BrowserProfile]:
        """Get best profile for specific platform"""
        async with self._profiles_lock:
            async with self._cooldown_lock:
                now = datetime.utcnow()
                candidates = []
                
                # Get profiles assigned to this platform
                platform_profile_ids = self.platform_pools.get(platform.value, [])
                
                for profile_id in platform_profile_ids:
                    # Check if on cooldown
                    if profile_id in self.profile_cooldowns:
                        if now < self.profile_cooldowns[profile_id]:
                            continue
                    
                    dynamic_profile = next((p for p in self.dynamic_profiles if p.id == profile_id), None)
                    static_profile = self.static_profiles.get(profile_id)
                    
                    if not dynamic_profile or not static_profile:
                        continue
                    
                    # Skip compromised/evolving profiles
                    if dynamic_profile.state in [ProfileState.COMPROMISED, ProfileState.EVOLVING]:
                        continue
                    
                    # Calculate score
                    score = self._calculate_profile_score(
                        dynamic_profile, static_profile, platform, require_session
                    )
                    
                    if score > 0:
                        candidates.append((score, static_profile))
                
                if not candidates:
                    logger.warning(f"No suitable profiles for {platform.value}")
                    # Try creating a new profile
                    new_profile = await self._create_platform_optimized_profile(platform)
                    if new_profile:
                        self.dynamic_profiles.append(new_profile['dynamic'])
                        self.static_profiles[new_profile['dynamic'].id] = new_profile['static']
                        self.platform_pools[platform.value].append(new_profile['dynamic'].id)
                        return new_profile['static']
                    return None
                
                # Select best profile
                candidates.sort(key=lambda x: x[0], reverse=True)
                selected_profile = candidates[0][1]
                
                # Apply cooldown
                cooldown_base, variance = self.config.cooldowns_seconds.get("task_selection", (10, 0.2))
                cooldown_seconds = self._calculate_cooldown_with_jitter(cooldown_base, variance)
                self.profile_cooldowns[selected_profile.profile_id] = now + timedelta(seconds=cooldown_seconds)
                
                # Update last used
                selected_profile.last_used = now
                
                logger.info(f"Selected profile {selected_profile.profile_id} for {platform.value} "
                          f"(score: {candidates[0][0]:.2f}, has_session: {platform.value in selected_profile.platform_sessions})")
                
                return selected_profile
    
    def _calculate_profile_score(self, dynamic_profile: DynamicProfile, static_profile: BrowserProfile,
                                platform: Platform, require_session: bool) -> float:
        """Calculate profile score for platform selection"""
        config = self.config.scoring_config
        score = config.base_score
        
        # State modifier
        score += config.state_modifiers.get(dynamic_profile.state, 0)
        
        # Session bonus
        session = static_profile.platform_sessions.get(platform.value)
        if session and session.get('is_valid'):
            score += config.has_valid_session_bonus
            # Penalize old sessions
            session_age_hours = (datetime.utcnow() - datetime.fromisoformat(session['last_updated'])).total_seconds() / 3600
            score -= session_age_hours * config.session_age_penalty_per_hour
        elif require_session:
            score -= 100  # Heavy penalty if session required but not available
        
        # Platform success bonus
        platform_stats = static_profile.platform_stats.get(platform.value, {})
        if platform_stats.get('successes', 0) > 0:
            score += config.platform_bonuses.get(platform.value, 0)
            # Success rate
            success_rate = static_profile.get_success_rate(platform.value)
            score += (success_rate - 0.5) * config.success_rate_weight
        
        # Response time factor
        avg_response_time = platform_stats.get('avg_response_time_ms', 0)
        if avg_response_time > 0:
            # Faster is better (normalize to 0-1 where 1 is fastest)
            normalized_speed = max(0, 1 - (avg_response_time / 5000))  # 5s as baseline
            score += normalized_speed * config.avg_response_time_weight
        
        # Consecutive failures penalty
        consecutive_failures = dynamic_profile.consecutive_failures
        score -= consecutive_failures * config.consecutive_failure_penalty
        
        # Risk assessment
        if dynamic_profile.component_risk_scores:
            avg_risk = sum(dynamic_profile.component_risk_scores.values()) / len(dynamic_profile.component_risk_scores)
            score -= avg_risk * config.avg_risk_score_penalty_weight
        
        # Recency bonus
        time_since_used = (datetime.utcnow() - (static_profile.last_used or static_profile.created_at)).total_seconds() / 3600
        if time_since_used < config.recency_threshold_hours:
            recency_factor = 1 - (time_since_used / config.recency_threshold_hours)
            score += recency_factor * config.recency_bonus_max
        
        # Proxy freshness bonus
        if static_profile.proxy_config and static_profile.should_rotate_proxy():
            score += config.proxy_rotation_bonus
        
        # Peak time bonus (ticket release hours)
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 11 or 18 <= current_hour <= 20:  # Common ticket release times
            score += config.peak_time_bonus
        
        # Quality multiplier
        score *= static_profile.quality.success_multiplier
        
        return max(0, score)  # Ensure non-negative
    
    async def record_feedback(self, profile_id: str, event: DetectionEvent, platform: str,
                            metadata: Optional[Dict] = None, invalidate_session: bool = False):
        """Record profile feedback with session management"""
        async with self._profiles_lock:
            async with self._cooldown_lock:
                # Update dynamic profile
                dynamic_profile = next((p for p in self.dynamic_profiles if p.id == profile_id), None)
                if dynamic_profile:
                    dynamic_profile.record_detection_event(event, metadata or {})
                
                # Update static profile
                static_profile = self.static_profiles.get(profile_id)
                if static_profile:
                    # Record usage
                    response_time = metadata.get('response_time_ms', 0) if metadata else 0
                    static_profile.record_usage(
                        success=(event == DetectionEvent.SUCCESS),
                        response_time_ms=response_time,
                        platform=platform,
                        error=metadata.get('error') if metadata else None,
                        detected=(event in [DetectionEvent.HARD_BLOCK, DetectionEvent.CAPTCHA_CHALLENGE])
                    )
                    
                    # Invalidate session if needed
                    if invalidate_session and platform in static_profile.platform_sessions:
                        static_profile.platform_sessions[platform]['is_valid'] = False
                        self.session_ready_profiles[platform].discard(profile_id)
                        logger.warning(f"Invalidated session for profile {profile_id} on {platform}")
                
                # Apply cooldown based on event
                now = datetime.utcnow()
                cooldown_params = self.config.cooldowns_seconds.get(event.value)
                
                if cooldown_params:
                    base_duration, variance = cooldown_params
                    cooldown_seconds = self._calculate_cooldown_with_jitter(base_duration, variance)
                    self.profile_cooldowns[profile_id] = now + timedelta(seconds=cooldown_seconds)
                    logger.debug(f"Profile {profile_id} on cooldown for {cooldown_seconds/60:.1f} minutes after {event.value}")
    
    async def warm_up_profile(self, profile: BrowserProfile, browser_manager: Any) -> bool:
        """Warm up profile with realistic browsing"""
        if not self.config.enable_behavioral_warmup:
            return True
        
        logger.info(f"Warming up profile {profile.profile_id}")
        
        try:
            # Get context from browser manager
            context = await browser_manager.get_persistent_context_for_profile(profile)
            
            # Visit Italian sites
            sites_to_visit = random.sample(self.config.warmup_sites, k=min(3, len(self.config.warmup_sites)))
            
            for site in sites_to_visit:
                try:
                    page = await context.new_page()
                    await page.goto(site, wait_until='domcontentloaded', timeout=30000)
                    
                    # Simulate human behavior
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    # Scroll a bit
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    # Maybe click something
                    if random.random() > 0.5:
                        links = await page.query_selector_all('a')
                        if links and len(links) > 5:
                            link = random.choice(links[:10])
                            try:
                                await link.click(timeout=5000)
                            except:
                                pass
                    
                    await page.close()
                    
                except Exception as e:
                    logger.warning(f"Warmup site {site} failed: {e}")
            
            # Mark profile as warmed up
            dynamic_profile = next((p for p in self.dynamic_profiles if p.id == profile.profile_id), None)
            if dynamic_profile and dynamic_profile.state == ProfileState.PRISTINE:
                dynamic_profile.state = ProfileState.HEALTHY
            
            logger.info(f"Profile {profile.profile_id} warmed up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Profile warmup failed: {e}", exc_info=True)
            return False
        finally:
            if 'context' in locals():
                await context.close()
    
    async def ensure_platform_session(self, profile: BrowserProfile, platform: Platform,
                                    login_callback: Optional[Callable] = None) -> bool:
        """Ensure profile has valid session for platform"""
        # Check existing session
        session = profile.platform_sessions.get(platform.value)
        if session and session.get('is_valid'):
            # Validate age
            session_age = (datetime.utcnow() - datetime.fromisoformat(session['last_updated'])).total_seconds() / 3600
            if session_age < self.config.max_session_age_hours:
                return True
        
        # Need to login
        if not login_callback:
            logger.warning(f"No login callback provided for {platform.value}")
            return False
        
        logger.info(f"Profile {profile.profile_id} needs login for {platform.value}")
        
        try:
            # Execute login
            success = await login_callback(profile, platform)
            
            if success:
                self.session_ready_profiles[platform.value].add(profile.profile_id)
                logger.info(f"Profile {profile.profile_id} successfully logged into {platform.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Login failed for profile {profile.profile_id} on {platform.value}: {e}")
            return False
    
    async def _periodic_session_validation(self):
        """Validate sessions periodically"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.session_validation_interval_seconds)
                
                async with self._profiles_lock:
                    for profile_id, static_profile in self.static_profiles.items():
                        for platform, session in static_profile.platform_sessions.items():
                            if not session.get('is_valid'):
                                continue
                            
                            # Check age
                            session_age = (datetime.utcnow() - datetime.fromisoformat(session['last_updated'])).total_seconds() / 3600
                            
                            if session_age > self.config.max_session_age_hours:
                                session['is_valid'] = False
                                self.session_ready_profiles[platform].discard(profile_id)
                                logger.info(f"Invalidated old session for profile {profile_id} on {platform}")
                
            except Exception as e:
                logger.error(f"Session validation error: {e}")
    
    async def _periodic_profile_evolution_task(self):
        """Enhanced evolution with session awareness"""
        while not self._shutdown_event.is_set():
            try:
                # Jittered sleep
                sleep_duration = self._calculate_cooldown_with_jitter(
                    self.config.evolution_interval_seconds,
                    self.config.evolution_interval_jitter_factor
                )
                await asyncio.sleep(sleep_duration)
                
                if self._shutdown_event.is_set():
                    break
                
                async with self._profiles_lock:
                    # Evolve profiles
                    for dynamic_profile in list(self.dynamic_profiles):
                        if dynamic_profile.should_mutate():
                            changes = dynamic_profile.mutate()
                            if changes:
                                # Update static profile
                                static_profile = self._adapt_dynamic_to_static(dynamic_profile)
                                self.static_profiles[dynamic_profile.id] = static_profile
                                logger.info(f"Profile {dynamic_profile.id} evolved with {len(changes)} changes")
                    
                    # Replace compromised profiles
                    await self._replace_compromised_profiles()
                    
                    # Save state
                    await self._save_profiles_to_disk()
                
            except Exception as e:
                logger.error(f"Evolution task error: {e}", exc_info=True)
    
    async def _replace_compromised_profiles(self):
        """Replace compromised profiles with platform awareness"""
        compromised_profiles = [p for p in self.dynamic_profiles if p.state == ProfileState.COMPROMISED]
        
        if not compromised_profiles:
            return
        
        compromise_rate = len(compromised_profiles) / len(self.dynamic_profiles)
        
        if compromise_rate >= self.config.compromise_threshold_pct:
            logger.warning(f"Replacing {len(compromised_profiles)} compromised profiles")
            
            for profile in compromised_profiles:
                # Remove from all pools
                profile_id = profile.id
                self.dynamic_profiles.remove(profile)
                self.static_profiles.pop(profile_id, None)
                
                for platform_profiles in self.platform_pools.values():
                    if profile_id in platform_profiles:
                        platform_profiles.remove(profile_id)
                
                for session_profiles in self.session_ready_profiles.values():
                    session_profiles.discard(profile_id)
                
                # Create replacement for same platform
                for platform, profile_ids in self.platform_pools.items():
                    if profile_id in profile_ids:
                        new_profile = await self._create_platform_optimized_profile(Platform(platform))
                        if new_profile:
                            self.dynamic_profiles.append(new_profile['dynamic'])
                            self.static_profiles[new_profile['dynamic'].id] = new_profile['static']
                            self.platform_pools[platform].append(new_profile['dynamic'].id)
                        break
    
    def _calculate_cooldown_with_jitter(self, base_seconds: float, variance_factor: float = 0.3) -> float:
        """Calculate cooldown with jitter"""
        if base_seconds <= 0:
            return 0.0
        jittered = np.random.normal(loc=base_seconds, scale=base_seconds * variance_factor)
        return max(base_seconds * 0.5, min(base_seconds * 2.0, jittered))
    
    async def start_background_tasks(self):
        """Start all background tasks"""
        self._shutdown_event.clear()
        
        # Start evolution
        self._evolution_task = asyncio.create_task(self._periodic_profile_evolution_task())
        
        # Start session validation
        if self.config.enable_session_preloading:
            self._session_validation_task = asyncio.create_task(self._periodic_session_validation())
        
        logger.info("Background tasks started")
    
    async def stop_background_tasks(self):
        """Stop all background tasks"""
        self._shutdown_event.set()
        
        tasks = [t for t in [self._evolution_task, self._session_validation_task] if t]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final save
        await self._save_profiles_to_disk()
        
        logger.info("Background tasks stopped")
    
    async def _save_profiles_to_disk(self):
        """Save profiles with session data"""
        try:
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'version': '2.0',
                'profiles': []
            }
            
            for dynamic_profile in self.dynamic_profiles:
                static_profile = self.static_profiles.get(dynamic_profile.id)
                
                profile_data = {
                    'id': dynamic_profile.id,
                    'state': dynamic_profile.state.value,
                    'created_at': dynamic_profile.created_at.isoformat(),
                    'last_active': dynamic_profile.last_active.isoformat(),
                    'fingerprint': dynamic_profile.get_fingerprint_snapshot(),
                    'stats': {
                        'success_count': dynamic_profile.success_count,
                        'failure_count': dynamic_profile.failure_count,
                        'consecutive_failures': dynamic_profile.consecutive_failures
                    }
                }
                
                if static_profile:
                    profile_data['static'] = {
                        'quality': static_profile.quality.name,
                        'platform_sessions': static_profile.platform_sessions,
                        'platform_stats': dict(static_profile.platform_stats),
                        'proxy_session_id': static_profile.proxy_session_id
                    }
                
                backup_data['profiles'].append(profile_data)
            
            # Save to disk
            Path(self.config.persistence_filepath).parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(self.config.persistence_filepath, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2))
            
            logger.info(f"Saved {len(self.dynamic_profiles)} profiles to disk")
            
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}", exc_info=True)
    
    async def _load_profiles_from_disk(self) -> bool:
        """Load profiles from disk"""
        try:
            if not Path(self.config.persistence_filepath).exists():
                return False
            
            async with aiofiles.open(self.config.persistence_filepath, 'r') as f:
                content = await f.read()
                backup_data = json.loads(content)
            
            logger.info(f"Loading profiles from {backup_data.get('timestamp', 'unknown time')}")
            
            for profile_data in backup_data.get('profiles', []):
                try:
                    # Recreate dynamic profile
                    base_profile = profile_data.get('fingerprint', {})
                    base_profile['device_class'] = base_profile.get('device_class', 'mid_range_desktop')
                    
                    dynamic_profile = DynamicProfile(
                        mutation_strategy=self.mutation_strategy,
                        base_profile_dict=base_profile,
                        profile_id=profile_data['id']
                    )
                    
                    # Restore state
                    dynamic_profile.state = ProfileState(profile_data['state'])
                    dynamic_profile.created_at = datetime.fromisoformat(profile_data['created_at'])
                    dynamic_profile.last_active = datetime.fromisoformat(profile_data['last_active'])
                    
                    stats = profile_data.get('stats', {})
                    dynamic_profile.success_count = stats.get('success_count', 0)
                    dynamic_profile.failure_count = stats.get('failure_count', 0)
                    dynamic_profile.consecutive_failures = stats.get('consecutive_failures', 0)
                    
                    self.dynamic_profiles.append(dynamic_profile)
                    
                    # Create static profile
                    static_profile = self._adapt_dynamic_to_static(dynamic_profile)
                    
                    # Restore static data
                    static_data = profile_data.get('static', {})
                    if static_data.get('quality'):
                        static_profile.quality = ProfileQuality[static_data['quality']]
                    
                    static_profile.platform_sessions = static_data.get('platform_sessions', {})
                    static_profile.platform_stats = defaultdict(
                        lambda: {'attempts': 0, 'successes': 0, 'failures': 0},
                        static_data.get('platform_stats', {})
                    )
                    static_profile.proxy_session_id = static_data.get('proxy_session_id')
                    
                    self.static_profiles[dynamic_profile.id] = static_profile
                    
                except Exception as e:
                    logger.error(f"Failed to load profile {profile_data.get('id', 'unknown')}: {e}")
            
            return len(self.dynamic_profiles) > 0
            
        except Exception as e:
            logger.error(f"Failed to load profiles from disk: {e}", exc_info=True)
            return False
    
    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pool metrics"""
        metrics = {
            'total_profiles': len(self.dynamic_profiles),
            'platform_distribution': {p: len(ids) for p, ids in self.platform_pools.items()},
            'session_ready': {p: len(ids) for p, ids in self.session_ready_profiles.items()},
            'state_distribution': defaultdict(int),
            'quality_distribution': defaultdict(int),
            'avg_success_rates': {}
        }
        
        for dynamic_profile in self.dynamic_profiles:
            metrics['state_distribution'][dynamic_profile.state.value] += 1
            
            static_profile = self.static_profiles.get(dynamic_profile.id)
            if static_profile:
                metrics['quality_distribution'][static_profile.quality.name] += 1
        
        # Platform success rates
        for platform in Platform:
            total_attempts = 0
            total_successes = 0
            
            for static_profile in self.static_profiles.values():
                stats = static_profile.platform_stats.get(platform.value, {})
                total_attempts += stats.get('attempts', 0)
                total_successes += stats.get('successes', 0)
            
            if total_attempts > 0:
                metrics['avg_success_rates'][platform.value] = total_successes / total_attempts
        
        return metrics

# --- Utility Functions ---
def create_profile_manager_from_config(config_path: str) -> ProfileManager:
    """Create ProfileManager from YAML config file"""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    pm_settings = config.get('profile_manager', {})
    
    # Create scoring config
    scoring_config = ProfileScoringConfig()
    if 'scoring' in pm_settings:
        for key, value in pm_settings['scoring'].items():
            if hasattr(scoring_config, key):
                setattr(scoring_config, key, value)
    
    # Create main config
    pm_config = ProfileManagerConfig(
        num_target_profiles=pm_settings.get('num_profiles', 20),
        profiles_per_platform=pm_settings.get('profiles_per_platform', 5),
        evolution_interval_seconds=pm_settings.get('evolution_interval', 900),
        persistence_filepath=pm_settings.get('persistence_file', 'profiles_backup.json'),
        session_backup_dir=pm_settings.get('session_backup_dir', 'session_backups'),
        scoring_config=scoring_config,
        enable_tls_rotation=pm_settings.get('enable_tls_rotation', True),
        enable_behavioral_warmup=pm_settings.get('enable_behavioral_warmup', True),
        enable_session_preloading=pm_settings.get('enable_session_preloading', True)
    )
    
    # Platform priorities
    if 'platform_priorities' in pm_settings:
        pm_config.platform_priorities = pm_settings['platform_priorities']
    
    # Proxy configs
    if 'proxies' in config:
        proxy_configs = []
        for proxy_data in config['proxies']:
            proxy_configs.append(ProxyConfig(**proxy_data))
        pm_config.proxy_configs = proxy_configs
    
    return ProfileManager(config=pm_config)

# --- Main execution for testing ---
if __name__ == '__main__':
    import asyncio
    
    async def test_profile_manager():
        """Test enhanced profile manager"""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        
        # Create manager
        config = ProfileManagerConfig(
            num_target_profiles=12,
            profiles_per_platform=4,
            evolution_interval_seconds=60
        )
        
        manager = ProfileManager(config=config)
        
        # Start background tasks
        await manager.start_background_tasks()
        
        try:
            # Test getting profiles for each platform
            for platform in Platform:
                profile = await manager.get_profile_for_platform(platform, require_session=False)
                if profile:
                    logger.info(f"Got profile {profile.profile_id} for {platform.value}")
                    
                    # Simulate usage
                    await asyncio.sleep(1)
                    
                    #
        except Exception as e:
            logger.error(f"Error during profile testing: {e}")