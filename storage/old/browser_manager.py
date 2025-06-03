# src/core/browser_profiles.py
# Advanced Browser Profile Management System with IPRoyal Proxy Integration
# Version 6.0 - Next-Gen Architecture with Data Optimization

import asyncio
import json
import logging
import hashlib
import time
import random
import os
import yaml
import aiofiles
import gzip
import pickle
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Type
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum, auto
import base64
import zlib
from urllib.parse import urlparse

# Third-party imports
import httpx
from fake_useragent import UserAgent
from playwright.async_api import Browser, BrowserContext, Page, Route, Request

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ProfileType(Enum):
    """Profile categorization for optimization"""
    DESKTOP_WINDOWS = "desktop_windows"
    DESKTOP_MAC = "desktop_mac"
    DESKTOP_LINUX = "desktop_linux"
    MOBILE_ANDROID = "mobile_android"
    MOBILE_IOS = "mobile_ios"
    TABLET = "tablet"

class ProfileQuality(Enum):
    """Profile quality ratings"""
    PREMIUM = (5, 0.95)  # tier, success_threshold
    HIGH = (4, 0.85)
    STANDARD = (3, 0.70)
    LOW = (2, 0.50)
    UNTESTED = (1, 0.0)
    
    def __init__(self, tier: int, threshold: float):
        self.tier = tier
        self.success_threshold = threshold

class DataOptimizationLevel(Enum):
    """Data usage optimization strategies"""
    AGGRESSIVE = "aggressive"  # Block all images, fonts, media
    BALANCED = "balanced"      # Block media, allow critical resources
    MINIMAL = "minimal"        # Allow most, block only ads/tracking
    OFF = "off"               # No optimization


# ============================================================================
# PROXY CONFIGURATION
# ============================================================================

@dataclass
class ProxyConfig:
    """IPRoyal proxy configuration with rotation support"""
    endpoint: str
    username: str
    password: str
    country: Optional[str] = None
    city: Optional[str] = None
    sticky_session: bool = False
    session_duration_minutes: int = 10
    rotation_interval_seconds: int = 300
    
    # Data optimization
    bandwidth_limit_mb: Optional[float] = None
    compression_enabled: bool = True
    
    # Advanced settings
    retry_attempts: int = 3
    timeout_seconds: int = 30
    health_check_interval: int = 60
    
    # Metrics
    data_used_mb: float = field(default=0.0, init=False)
    last_rotation: datetime = field(default_factory=datetime.now, init=False)
    failed_attempts: int = field(default=0, init=False)
    
    def get_proxy_url(self, session_id: Optional[str] = None) -> str:
        """Generate proxy URL with optional session ID for sticky sessions"""
        auth = f"{self.username}:{self.password}"
        if session_id and self.sticky_session:
            auth = f"{self.username}-session-{session_id}:{self.password}"
        
        # Add location parameters if specified
        if self.country:
            auth = f"{auth}-country-{self.country}"
        if self.city:
            auth = f"{auth}-city-{self.city}"
            
        return f"http://{auth}@{self.endpoint}"
    
    def should_rotate(self) -> bool:
        """Check if proxy should be rotated"""
        if not self.sticky_session:
            return False
        
        elapsed = (datetime.now() - self.last_rotation).total_seconds()
        return elapsed >= self.rotation_interval_seconds
    
    def record_usage(self, bytes_used: int):
        """Track data usage"""
        self.data_used_mb += bytes_used / (1024 * 1024)


# ============================================================================
# BROWSER PROFILE
# ============================================================================

@dataclass
class BrowserProfile:
    """Enhanced browser profile with proxy and optimization support"""
    # Core identifiers
    name: str
    profile_id: str = field(default_factory=lambda: hashlib.md5(
        f"{time.time()}_{random.random()}".encode()
    ).hexdigest())
    
    # Browser fingerprint
    user_agent: str = ""
    viewport_width: int = 1920
    viewport_height: int = 1080
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    
    # Localization
    timezone: str = "America/New_York"
    locale: str = "en-US"
    languages: List[str] = field(default_factory=lambda: ["en-US", "en"])
    
    # Hardware fingerprint
    hardware_concurrency: int = 4
    memory_gb: int = 8
    platform: str = "Win32"
    
    # WebGL & Canvas
    webgl_vendor: str = "Intel Inc."
    webgl_renderer: str = "Intel Iris OpenGL Engine"
    canvas_fingerprint: Optional[str] = None
    
    # Browser features
    webrtc_enabled: bool = True
    plugins: List[Dict[str, str]] = field(default_factory=list)
    
    # Network settings
    accept_language: str = "en-US,en;q=0.9"
    accept_encoding: str = "gzip, deflate, br"
    do_not_track: Optional[str] = None
    
    # Proxy configuration
    proxy_config: Optional[ProxyConfig] = None
    proxy_session_id: Optional[str] = None
    
    # Optimization settings
    data_optimization_level: DataOptimizationLevel = DataOptimizationLevel.BALANCED
    block_resources: List[str] = field(default_factory=lambda: ["font", "image", "media"])
    cache_enabled: bool = True
    
    # Browser launch arguments
    browser_args: List[str] = field(default_factory=list)
    
    # Performance metrics
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    detection_count: int = 0
    total_data_mb: float = 0.0
    
    # Platform-specific metrics
    platform_stats: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: {
            'attempts': 0, 'successes': 0, 'failures': 0, 'detections': 0
        })
    )
    
    # Advanced tracking
    response_times: deque = field(default_factory=lambda: deque(maxlen=50))
    error_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_error: Optional[str] = None
    last_detection_reason: Optional[str] = None
    
    # Profile metadata
    profile_type: ProfileType = ProfileType.DESKTOP_WINDOWS
    quality: ProfileQuality = ProfileQuality.UNTESTED
    tags: Set[str] = field(default_factory=set)
    notes: str = ""
    
    def __post_init__(self):
        """Initialize computed fields"""
        if not self.user_agent:
            self._generate_user_agent()
        
        if not self.canvas_fingerprint:
            self.canvas_fingerprint = self._generate_canvas_fingerprint()
        
        # Set fingerprint hash
        self.fingerprint_hash = self._calculate_fingerprint_hash()
        
        # Initialize browser args if needed
        if not self.browser_args:
            self.browser_args = self._get_optimized_browser_args()
    
    def _generate_user_agent(self):
        """Generate appropriate user agent based on profile type"""
        ua = UserAgent()
        
        if self.profile_type == ProfileType.DESKTOP_WINDOWS:
            self.user_agent = ua.chrome
            self.platform = "Win32"
        elif self.profile_type == ProfileType.DESKTOP_MAC:
            self.user_agent = ua.safari
            self.platform = "MacIntel"
        elif self.profile_type == ProfileType.MOBILE_ANDROID:
            self.user_agent = ua.android
            self.platform = "Linux armv71"
            self.is_mobile = True
            self.has_touch = True
        elif self.profile_type == ProfileType.MOBILE_IOS:
            self.user_agent = ua.ios
            self.platform = "iPhone"
            self.is_mobile = True
            self.has_touch = True
    
    def _generate_canvas_fingerprint(self) -> str:
        """Generate unique canvas fingerprint"""
        components = [
            self.user_agent,
            str(self.viewport_width),
            str(self.viewport_height),
            self.webgl_vendor,
            self.webgl_renderer,
            str(time.time())
        ]
        return hashlib.sha256("".join(components).encode()).hexdigest()[:16]
    
    def _calculate_fingerprint_hash(self) -> str:
        """Calculate unique fingerprint hash for the profile"""
        fingerprint_data = {
            'user_agent': self.user_agent,
            'viewport': f"{self.viewport_width}x{self.viewport_height}",
            'timezone': self.timezone,
            'locale': self.locale,
            'platform': self.platform,
            'webgl': f"{self.webgl_vendor}|{self.webgl_renderer}",
            'canvas': self.canvas_fingerprint,
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def _get_optimized_browser_args(self) -> List[str]:
        """Get browser arguments optimized for stealth and performance"""
        args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=IsolateOrigins,site-per-process',
            '--flag-switches-begin',
            '--flag-switches-end',
        ]
        
        # Data optimization args
        if self.data_optimization_level == DataOptimizationLevel.AGGRESSIVE:
            args.extend([
                '--disable-images',
                '--disable-javascript',  # Use carefully
                '--disable-plugins',
                '--disable-java',
                '--disable-local-storage',
                '--disk-cache-size=1',
                '--media-cache-size=1',
                '--disable-application-cache',
            ])
        elif self.data_optimization_level == DataOptimizationLevel.BALANCED:
            args.extend([
                '--disable-plugins',
                '--disable-java',
                '--disk-cache-size=52428800',  # 50MB
                '--media-cache-size=10485760',  # 10MB
            ])
        
        # Memory optimization
        args.extend([
            '--memory-pressure-off',
            '--in-process-gpu',
            '--max_old_space_size=512',
            '--js-flags=--expose-gc',
        ])
        
        return args
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        total_attempts = self.success_count + self.failure_count
        return self.success_count / max(1, total_attempts)
    
    @property
    def detection_rate(self) -> float:
        """Calculate detection rate"""
        return self.detection_count / max(1, self.usage_count)
    
    @property
    def avg_response_time(self) -> float:
        """Average response time in milliseconds"""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0
    
    @property
    def health_score(self) -> float:
        """Calculate profile health score (0-100)"""
        if self.usage_count == 0:
            return 50.0  # Neutral for unused profiles
        
        score = 100.0
        
        # Success rate impact (40 points)
        score -= (1 - self.success_rate) * 40
        
        # Detection rate impact (40 points)
        score -= self.detection_rate * 40
        
        # Response time impact (10 points)
        if self.avg_response_time > 5000:
            score -= min((self.avg_response_time - 5000) / 1000, 10)
        
        # Recency bonus (10 points)
        if self.last_used:
            hours_since_use = (datetime.now() - self.last_used).total_seconds() / 3600
            if hours_since_use < 1:
                score += 10
            elif hours_since_use < 6:
                score += 5
        
        return max(0.0, min(100.0, score))
    
    def update_quality(self):
        """Update profile quality based on performance"""
        if self.usage_count < 5:
            self.quality = ProfileQuality.UNTESTED
        elif self.success_rate >= ProfileQuality.PREMIUM.success_threshold:
            self.quality = ProfileQuality.PREMIUM
        elif self.success_rate >= ProfileQuality.HIGH.success_threshold:
            self.quality = ProfileQuality.HIGH
        elif self.success_rate >= ProfileQuality.STANDARD.success_threshold:
            self.quality = ProfileQuality.STANDARD
        else:
            self.quality = ProfileQuality.LOW
    
    def record_usage(self, success: bool, response_time_ms: float = 0,
                    data_used_bytes: int = 0, platform: Optional[str] = None,
                    error: Optional[str] = None, detected: bool = False):
        """Record profile usage with detailed metrics"""
        self.usage_count += 1
        self.last_used = datetime.now()
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.last_error = error
                self.error_types[error] += 1
        
        if detected:
            self.detection_count += 1
            self.last_detection_reason = error
        
        if response_time_ms > 0:
            self.response_times.append(response_time_ms)
        
        if data_used_bytes > 0:
            self.total_data_mb += data_used_bytes / (1024 * 1024)
            if self.proxy_config:
                self.proxy_config.record_usage(data_used_bytes)
        
        # Platform-specific tracking
        if platform:
            self.platform_stats[platform]['attempts'] += 1
            if success:
                self.platform_stats[platform]['successes'] += 1
            else:
                self.platform_stats[platform]['failures'] += 1
            if detected:
                self.platform_stats[platform]['detections'] += 1
        
        # Update quality rating
        self.update_quality()
    
    def should_rotate_proxy(self) -> bool:
        """Check if proxy should be rotated"""
        return self.proxy_config and self.proxy_config.should_rotate()
    
    def rotate_proxy(self):
        """Rotate proxy session"""
        if self.proxy_config:
            self.proxy_session_id = hashlib.md5(
                f"{self.profile_id}_{time.time()}".encode()
            ).hexdigest()[:16]
            self.proxy_config.last_rotation = datetime.now()
            logger.info(f"Rotated proxy session for profile {self.name}: {self.proxy_session_id}")
    
    def get_context_params(self) -> Dict[str, Any]:
        """Get parameters for browser context creation"""
        params = {
            'viewport': {
                'width': self.viewport_width,
                'height': self.viewport_height
            },
            'device_scale_factor': self.device_scale_factor,
            'is_mobile': self.is_mobile,
            'has_touch': self.has_touch,
            'user_agent': self.user_agent,
            'timezone_id': self.timezone,
            'locale': self.locale,
            'permissions': [],
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
        }
        
        # Add proxy if configured
        if self.proxy_config:
            proxy_url = self.proxy_config.get_proxy_url(self.proxy_session_id)
            params['proxy'] = {
                'server': proxy_url,
                'bypass': 'localhost,127.0.0.1,local.test'
            }
        
        # Add extra headers
        params['extra_http_headers'] = {
            'Accept-Language': self.accept_language,
            'Accept-Encoding': self.accept_encoding,
        }
        
        if self.do_not_track:
            params['extra_http_headers']['DNT'] = self.do_not_track
        
        # Add storage state if caching is enabled
        if self.cache_enabled:
            cache_dir = Path("cache") / self.profile_id
            cache_dir.mkdir(parents=True, exist_ok=True)
            params['storage_state'] = str(cache_dir / "state.json")
        
        return params
    
    def get_resource_block_patterns(self) -> List[str]:
        """Get resource blocking patterns based on optimization level"""
        patterns = []
        
        if self.data_optimization_level == DataOptimizationLevel.OFF:
            return patterns
        
        # Common tracking and ads
        patterns.extend([
            '*doubleclick.net*',
            '*googletagmanager.com*',
            '*google-analytics.com*',
            '*googleadservices.com*',
            '*googlesyndication.com*',
            '*facebook.com/tr*',
            '*amazon-adsystem.com*',
            '*adsystem.google.com*',
        ])
        
        if self.data_optimization_level in [DataOptimizationLevel.BALANCED, DataOptimizationLevel.AGGRESSIVE]:
            # Block specified resource types
            if 'font' in self.block_resources:
                patterns.extend(['*.woff*', '*.ttf', '*.otf'])
            if 'image' in self.block_resources:
                patterns.extend(['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.ico', '*.svg'])
            if 'media' in self.block_resources:
                patterns.extend(['*.mp4', '*.webm', '*.mp3', '*.wav', '*.flv', '*.avi'])
        
        if self.data_optimization_level == DataOptimizationLevel.AGGRESSIVE:
            # Block even more aggressively
            patterns.extend([
                '*.css',  # Block stylesheets
                '*cdn*',  # Block CDN resources
                '*static*',  # Block static resources
            ])
        
        return patterns
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization"""
        data = asdict(self)
        
        # Convert non-serializable fields
        data['created_at'] = self.created_at.isoformat()
        data['last_used'] = self.last_used.isoformat() if self.last_used else None
        data['response_times'] = list(self.response_times)
        data['tags'] = list(self.tags)
        data['data_optimization_level'] = self.data_optimization_level.value
        data['profile_type'] = self.profile_type.value
        data['quality'] = self.quality.name
        
        # Handle proxy config
        if self.proxy_config:
            data['proxy_config'] = asdict(self.proxy_config)
            data['proxy_config']['last_rotation'] = self.proxy_config.last_rotation.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrowserProfile':
        """Create profile from dictionary"""
        # Convert string fields back to objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if 'last_used' in data and data['last_used']:
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        
        if 'response_times' in data:
            data['response_times'] = deque(data['response_times'], maxlen=50)
        
        if 'tags' in data:
            data['tags'] = set(data['tags'])
        
        if 'data_optimization_level' in data:
            data['data_optimization_level'] = DataOptimizationLevel(data['data_optimization_level'])
        
        if 'profile_type' in data:
            data['profile_type'] = ProfileType(data['profile_type'])
        
        if 'quality' in data:
            data['quality'] = ProfileQuality[data['quality']]
        
        # Handle proxy config
        if 'proxy_config' in data and data['proxy_config']:
            proxy_data = data['proxy_config']
            if 'last_rotation' in proxy_data:
                proxy_data['last_rotation'] = datetime.fromisoformat(proxy_data['last_rotation'])
            data['proxy_config'] = ProxyConfig(**proxy_data)
        
        # Handle defaultdict fields
        if 'error_types' not in data:
            data['error_types'] = defaultdict(int)
        else:
            data['error_types'] = defaultdict(int, data['error_types'])
        
        if 'platform_stats' not in data:
            data['platform_stats'] = defaultdict(lambda: {
                'attempts': 0, 'successes': 0, 'failures': 0, 'detections': 0
            })
        else:
            data['platform_stats'] = defaultdict(
                lambda: {'attempts': 0, 'successes': 0, 'failures': 0, 'detections': 0},
                data['platform_stats']
            )
        
        return cls(**data)


# ============================================================================
# PROFILE MANAGER CONFIGURATION
# ============================================================================

@dataclass
class ProfileManagerConfig:
    """Configuration for ProfileManager"""
    # Storage settings
    profiles_file: str = "profiles.json"
    backup_dir: str = "profiles_backup"
    max_backups: int = 10
    auto_save_interval: int = 300  # seconds
    
    # Profile pool settings
    min_profiles: int = 10
    max_profiles: int = 100
    target_quality_distribution: Dict[ProfileQuality, float] = field(
        default_factory=lambda: {
            ProfileQuality.PREMIUM: 0.2,
            ProfileQuality.HIGH: 0.3,
            ProfileQuality.STANDARD: 0.3,
            ProfileQuality.LOW: 0.1,
            ProfileQuality.UNTESTED: 0.1,
        }
    )
    
    # Profile rotation settings
    rotation_strategy: str = "weighted_quality"  # random, round_robin, weighted_quality
    min_rest_period_minutes: int = 30
    max_consecutive_uses: int = 10
    
    # Proxy settings
    proxy_configs: List[ProxyConfig] = field(default_factory=list)
    proxy_assignment_strategy: str = "round_robin"  # round_robin, random, sticky
    proxy_health_check_enabled: bool = True
    
    # Data optimization
    global_data_limit_mb: Optional[float] = None
    per_profile_data_limit_mb: Optional[float] = None
    data_reset_period_days: int = 30
    
    # Profile generation
    profile_types_distribution: Dict[ProfileType, float] = field(
        default_factory=lambda: {
            ProfileType.DESKTOP_WINDOWS: 0.5,
            ProfileType.DESKTOP_MAC: 0.2,
            ProfileType.DESKTOP_LINUX: 0.1,
            ProfileType.MOBILE_ANDROID: 0.15,
            ProfileType.MOBILE_IOS: 0.05,
        }
    )
    
    # Advanced features
    enable_ml_optimization: bool = False
    enable_fingerprint_randomization: bool = True
    enable_behavioral_analysis: bool = True
    anomaly_detection_threshold: float = 0.8


# ============================================================================
# PROFILE MANAGER
# ============================================================================

class ProfileManager:
    """Advanced profile manager with rotation, optimization, and monitoring"""
    
    def __init__(self, config: Optional[ProfileManagerConfig] = None):
        """Initialize ProfileManager with configuration"""
        self.config = config or ProfileManagerConfig()
        self.profiles: Dict[str, BrowserProfile] = {}
        self._profile_index: Dict[str, BrowserProfile] = {}  # name -> profile
        self._quality_index: Dict[ProfileQuality, List[BrowserProfile]] = defaultdict(list)
        self._platform_index: Dict[str, List[BrowserProfile]] = defaultdict(list)
        
        # Rotation state
        self._rotation_index = 0
        self._last_used: Dict[str, datetime] = {}
        self._consecutive_uses: Dict[str, int] = defaultdict(int)
        
        # Proxy management
        self._proxy_index = 0
        self._proxy_assignments: Dict[str, ProxyConfig] = {}
        
        # Data tracking
        self.total_data_used_mb = 0.0
        self.data_reset_date = datetime.now() + timedelta(days=self.config.data_reset_period_days)
        
        # Monitoring
        self._save_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._metrics_history: deque = deque(maxlen=1000)
        
        logger.info(f"ProfileManager initialized with {len(self.config.proxy_configs)} proxy configs")
    
    async def initialize(self):
        """Initialize ProfileManager and load profiles"""
        # Load existing profiles
        await self.load_profiles()
        
        # Generate profiles if needed
        if len(self.profiles) < self.config.min_profiles:
            await self.generate_profiles(self.config.min_profiles - len(self.profiles))
        
        # Start background tasks
        self._save_task = asyncio.create_task(self._auto_save_loop(), name="ProfileAutoSave")
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="ProfileMonitor")
        
        logger.info(f"ProfileManager initialized with {len(self.profiles)} profiles")
    
    async def load_profiles(self):
        """Load profiles from disk with compression support"""
        profiles_path = Path(self.config.profiles_file)
        
        if not profiles_path.exists():
            logger.info("No existing profiles found")
            return
        
        try:
            # Try loading compressed file first
            compressed_path = profiles_path.with_suffix('.json.gz')
            if compressed_path.exists():
                async with aiofiles.open(compressed_path, 'rb') as f:
                    compressed_data = await f.read()
                    data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))
            else:
                async with aiofiles.open(profiles_path, 'r') as f:
                    data = json.loads(await f.read())
            
            # Load profiles
            for profile_data in data.get('profiles', []):
                profile = BrowserProfile.from_dict(profile_data)
                self.profiles[profile.profile_id] = profile
                self._index_profile(profile)
            
            # Load metadata
            self.total_data_used_mb = data.get('total_data_used_mb', 0.0)
            if 'data_reset_date' in data:
                self.data_reset_date = datetime.fromisoformat(data['data_reset_date'])
            
            logger.info(f"Loaded {len(self.profiles)} profiles from {profiles_path}")
            
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}", exc_info=True)
    
    async def save_profiles(self, compress: bool = True):
        """Save profiles to disk with optional compression"""
        try:
            # Prepare data
            data = {
                'version': '6.0',
                'saved_at': datetime.now().isoformat(),
                'profiles': [p.to_dict() for p in self.profiles.values()],
                'total_data_used_mb': self.total_data_used_mb,
                'data_reset_date': self.data_reset_date.isoformat(),
                'statistics': self._calculate_statistics(),
            }
            
            json_data = json.dumps(data, indent=2)
            
            # Save with compression
            if compress:
                compressed_data = gzip.compress(json_data.encode('utf-8'))
                save_path = Path(self.config.profiles_file).with_suffix('.json.gz')
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(compressed_data)
                
                # Calculate compression ratio
                compression_ratio = len(compressed_data) / len(json_data)
                logger.info(
                    f"Saved {len(self.profiles)} profiles to {save_path} "
                    f"(compressed {compression_ratio:.1%})"
                )
            else:
                save_path = Path(self.config.profiles_file)
                async with aiofiles.open(save_path, 'w') as f:
                    await f.write(json_data)
                logger.info(f"Saved {len(self.profiles)} profiles to {save_path}")
            
            # Create backup
            await self._create_backup()
            
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}", exc_info=True)
    
    async def _create_backup(self):
        """Create backup of current profiles"""
        backup_dir = Path(self.config.backup_dir)
        backup_dir.mkdir(exist_ok=True)
        
        # Clean old backups
        existing_backups = sorted(backup_dir.glob("profiles_*.json.gz"))
        if len(existing_backups) >= self.config.max_backups:
            for old_backup in existing_backups[:-self.config.max_backups+1]:
                old_backup.unlink()
        
        # Create new backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"profiles_{timestamp}.json.gz"
        
        source_path = Path(self.config.profiles_file).with_suffix('.json.gz')
        if source_path.exists():
            import shutil
            shutil.copy2(source_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
    
    def _index_profile(self, profile: BrowserProfile):
        """Index profile for fast lookup"""
        self._profile_index[profile.name] = profile
        self._quality_index[profile.quality].append(profile)
        self._platform_index[profile.platform].append(profile)
        
        # Platform-specific indexing
        for platform in profile.platform_stats.keys():
            self._platform_index[f"stats_{platform}"].append(profile)
    
    def _reindex_profiles(self):
        """Rebuild all profile indices"""
        self._profile_index.clear()
        self._quality_index.clear()
        self._platform_index.clear()
        
        for profile in self.profiles.values():
            self._index_profile(profile)
    
    async def generate_profiles(self, count: int):
        """Generate new profiles with specified distribution"""
        logger.info(f"Generating {count} new profiles")
        
        generated = []
        
        for i in range(count):
            # Select profile type based on distribution
            profile_type = self._select_profile_type()
            
            # Generate profile
            profile = await self._generate_single_profile(profile_type)
            
            # Assign proxy if available
            if self.config.proxy_configs:
                proxy_config = self._select_proxy_for_profile(profile)
                profile.proxy_config = proxy_config
                profile.rotate_proxy()  # Initialize session
            
            # Add to manager
            self.profiles[profile.profile_id] = profile
            self._index_profile(profile)
            generated.append(profile)
        
        logger.info(f"Generated {len(generated)} profiles")
        
        # Save immediately
        await self.save_profiles()
        
        return generated
    
    def _select_profile_type(self) -> ProfileType:
        """Select profile type based on distribution"""
        types = list(self.config.profile_types_distribution.keys())
        weights = list(self.config.profile_types_distribution.values())
        return random.choices(types, weights=weights, k=1)[0]
    
    async def _generate_single_profile(self, profile_type: ProfileType) -> BrowserProfile:
        """Generate a single profile with randomized attributes"""
        # Base attributes by type
        if profile_type == ProfileType.DESKTOP_WINDOWS:
            viewport_width = random.choice([1920, 1680, 1600, 1440, 1366, 1280])
            viewport_height = random.choice([1080, 1050, 900, 768])
            hardware_concurrency = random.choice([4, 6, 8, 12, 16])
            memory_gb = random.choice([8, 16, 32])
            platform = "Win32"
            
        elif profile_type == ProfileType.DESKTOP_MAC:
            viewport_width = random.choice([1920, 1680, 1440, 1280])
            viewport_height = random.choice([1080, 1050, 900, 800])
            hardware_concurrency = random.choice([4, 6, 8])
            memory_gb = random.choice([8, 16])
            platform = "MacIntel"
            
        elif profile_type in [ProfileType.MOBILE_ANDROID, ProfileType.MOBILE_IOS]:
            viewport_width = random.choice([375, 390, 393, 412, 414])
            viewport_height = random.choice([667, 812, 844, 896, 915])
            hardware_concurrency = random.choice([2, 4, 6, 8])
            memory_gb = random.choice([2, 3, 4, 6])
            platform = "Linux armv71" if profile_type == ProfileType.MOBILE_ANDROID else "iPhone"
        
        else:  # Desktop Linux or Tablet
            viewport_width = random.choice([1920, 1680, 1366, 1024])
            viewport_height = random.choice([1080, 900, 768])
            hardware_concurrency = random.choice([4, 6, 8])
            memory_gb = random.choice([4, 8, 16])
            platform = "Linux x86_64"
        
        # Localization
        locales = [
            ("en-US", "America/New_York", ["en-US", "en"]),
            ("en-GB", "Europe/London", ["en-GB", "en"]),
            ("de-DE", "Europe/Berlin", ["de-DE", "de", "en"]),
            ("fr-FR", "Europe/Paris", ["fr-FR", "fr", "en"]),
            ("es-ES", "Europe/Madrid", ["es-ES", "es", "en"]),
            ("it-IT", "Europe/Rome", ["it-IT", "it", "en"]),
        ]
        
        locale, timezone, languages = random.choice(locales)
        
        # WebGL vendors/renderers
        webgl_configs = [
            ("Intel Inc.", "Intel Iris OpenGL Engine"),
            ("Intel Inc.", "Intel HD Graphics 620"),
            ("NVIDIA Corporation", "GeForce GTX 1660/PCIe/SSE2"),
            ("AMD", "AMD Radeon Pro 5500M"),
            ("Google Inc.", "ANGLE (Intel HD Graphics 620 Direct3D11)"),
        ]
        
        webgl_vendor, webgl_renderer = random.choice(webgl_configs)
        
        # Generate profile
        profile = BrowserProfile(
            name=f"{profile_type.value}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            device_scale_factor=random.choice([1.0, 1.25, 1.5, 2.0]),
            is_mobile=profile_type in [ProfileType.MOBILE_ANDROID, ProfileType.MOBILE_IOS],
            has_touch=profile_type in [ProfileType.MOBILE_ANDROID, ProfileType.MOBILE_IOS, ProfileType.TABLET],
            timezone=timezone,
            locale=locale,
            languages=languages,
            hardware_concurrency=hardware_concurrency,
            memory_gb=memory_gb,
            platform=platform,
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            webrtc_enabled=random.choice([True, True, False]),  # 66% enabled
            accept_language=f"{locale},{locale.split('-')[0]};q=0.9,en;q=0.8",
            do_not_track=random.choice([None, "1"]),  # 50% DNT
            profile_type=profile_type,
            data_optimization_level=random.choice([
                DataOptimizationLevel.BALANCED,
                DataOptimizationLevel.BALANCED,
                DataOptimizationLevel.MINIMAL,
                DataOptimizationLevel.AGGRESSIVE,
            ]),
            tags={profile_type.value, "generated", f"batch_{int(time.time())}"},
        )
        
        return profile
    
    def _select_proxy_for_profile(self, profile: BrowserProfile) -> ProxyConfig:
        """Select proxy configuration for profile"""
        if not self.config.proxy_configs:
            return None
        
        if self.config.proxy_assignment_strategy == "round_robin":
            proxy = self.config.proxy_configs[self._proxy_index % len(self.config.proxy_configs)]
            self._proxy_index += 1
        elif self.config.proxy_assignment_strategy == "random":
            proxy = random.choice(self.config.proxy_configs)
        else:  # sticky
            # Try to reuse same proxy for profile
            if profile.profile_id in self._proxy_assignments:
                proxy = self._proxy_assignments[profile.profile_id]
            else:
                proxy = self.config.proxy_configs[self._proxy_index % len(self.config.proxy_configs)]
                self._proxy_index += 1
                self._proxy_assignments[profile.profile_id] = proxy
        
        # Create a copy to avoid shared state
        return ProxyConfig(
            endpoint=proxy.endpoint,
            username=proxy.username,
            password=proxy.password,
            country=proxy.country,
            city=proxy.city,
            sticky_session=proxy.sticky_session,
            session_duration_minutes=proxy.session_duration_minutes,
            rotation_interval_seconds=proxy.rotation_interval_seconds,
            bandwidth_limit_mb=proxy.bandwidth_limit_mb,
            compression_enabled=proxy.compression_enabled,
        )
    
    async def select_profile(self, 
                           strategy: Optional[str] = None,
                           platform: Optional[str] = None,
                           exclude_ids: Optional[Set[str]] = None,
                           quality_filter: Optional[ProfileQuality] = None,
                           **kwargs) -> BrowserProfile:
        """Select profile using specified strategy"""
        strategy = strategy or self.config.rotation_strategy
        exclude_ids = exclude_ids or set()
        
        # Filter candidates
        candidates = [
            p for p in self.profiles.values()
            if p.profile_id not in exclude_ids
        ]
        
        # Apply quality filter
        if quality_filter:
            candidates = [p for p in candidates if p.quality.tier >= quality_filter.tier]
        
        # Apply platform filter
        if platform:
            # Prefer profiles with experience on this platform
            platform_experienced = [
                p for p in candidates 
                if platform in p.platform_stats and p.platform_stats[platform]['attempts'] > 0
            ]
            if platform_experienced:
                candidates = platform_experienced
        
        # Apply rest period filter
        now = datetime.now()
        rested_candidates = []
        for profile in candidates:
            last_used = self._last_used.get(profile.profile_id)
            if not last_used or (now - last_used).total_seconds() / 60 >= self.config.min_rest_period_minutes:
                rested_candidates.append(profile)
        
        # Use rested candidates if available
        if rested_candidates:
            candidates = rested_candidates
        
        if not candidates:
            # Generate new profile if needed
            logger.warning("No suitable profiles found, generating new one")
            new_profiles = await self.generate_profiles(1)
            return new_profiles[0]
        
        # Select based on strategy
        if strategy == "random":
            selected = random.choice(candidates)
            
        elif strategy == "round_robin":
            # Sort by last used time
            candidates.sort(key=lambda p: self._last_used.get(p.profile_id, datetime.min))
            selected = candidates[0]
            
        elif strategy == "weighted_quality":
            # Weight by quality and success rate
            weights = []
            for profile in candidates:
                weight = profile.quality.tier * 0.5 + profile.success_rate * 0.5
                
                # Platform-specific weighting
                if platform and platform in profile.platform_stats:
                    platform_success = (
                        profile.platform_stats[platform]['successes'] / 
                        max(1, profile.platform_stats[platform]['attempts'])
                    )
                    weight = weight * 0.7 + platform_success * 0.3
                
                # Freshness bonus
                consecutive_uses = self._consecutive_uses.get(profile.profile_id, 0)
                if consecutive_uses < self.config.max_consecutive_uses:
                    weight *= (1 + 0.1 * (self.config.max_consecutive_uses - consecutive_uses))
                
                weights.append(max(0.1, weight))
            
            selected = random.choices(candidates, weights=weights, k=1)[0]
        
        else:
            selected = random.choice(candidates)
        
        # Update tracking
        self._last_used[selected.profile_id] = now
        self._consecutive_uses[selected.profile_id] += 1
        
        # Reset consecutive uses for other profiles
        for profile_id in self._consecutive_uses:
            if profile_id != selected.profile_id:
                self._consecutive_uses[profile_id] = 0
        
        # Check proxy rotation
        if selected.should_rotate_proxy():
            selected.rotate_proxy()
        
        logger.info(
            f"Selected profile {selected.name} "
            f"(quality: {selected.quality.name}, success: {selected.success_rate:.1%})"
        )
        
        return selected
    
    def get_profile(self, name_or_id: str) -> Optional[BrowserProfile]:
        """Get profile by name or ID"""
        # Try ID first
        if name_or_id in self.profiles:
            return self.profiles[name_or_id]
        
        # Try name
        return self._profile_index.get(name_or_id)
    
    def retire_profile(self, profile: Union[str, BrowserProfile], reason: str = ""):
        """Retire a profile from active use"""
        if isinstance(profile, str):
            profile = self.get_profile(profile)
        
        if not profile:
            return
        
        logger.info(f"Retiring profile {profile.name}: {reason}")
        
        # Remove from indices
        if profile.name in self._profile_index:
            del self._profile_index[profile.name]
        
        for quality_list in self._quality_index.values():
            if profile in quality_list:
                quality_list.remove(profile)
        
        for platform_list in self._platform_index.values():
            if profile in platform_list:
                platform_list.remove(profile)
        
        # Remove from main dict
        if profile.profile_id in self.profiles:
            del self.profiles[profile.profile_id]
        
        # Clean up tracking
        self._last_used.pop(profile.profile_id, None)
        self._consecutive_uses.pop(profile.profile_id, None)
        self._proxy_assignments.pop(profile.profile_id, None)
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        if not self.profiles:
            return {}
        
        # Quality distribution
        quality_dist = {}
        for quality in ProfileQuality:
            count = len(self._quality_index[quality])
            quality_dist[quality.name] = {
                'count': count,
                'percentage': count / len(self.profiles) * 100
            }
        
        # Platform distribution
        platform_dist = defaultdict(int)
        for profile in self.profiles.values():
            platform_dist[profile.profile_type.value] += 1
        
        # Success metrics
        success_rates = [p.success_rate for p in self.profiles.values()]
        detection_rates = [p.detection_rate for p in self.profiles.values()]
        health_scores = [p.health_score for p in self.profiles.values()]
        
        # Data usage
        data_per_profile = [p.total_data_mb for p in self.profiles.values()]
        
        return {
            'total_profiles': len(self.profiles),
            'quality_distribution': quality_dist,
            'platform_distribution': dict(platform_dist),
            'average_success_rate': sum(success_rates) / len(success_rates),
            'average_detection_rate': sum(detection_rates) / len(detection_rates),
            'average_health_score': sum(health_scores) / len(health_scores),
            'total_data_used_mb': self.total_data_used_mb,
            'average_data_per_profile_mb': sum(data_per_profile) / len(data_per_profile),
            'profiles_with_proxy': sum(1 for p in self.profiles.values() if p.proxy_config),
        }
    
    async def _auto_save_loop(self):
        """Periodically save profiles"""
        while True:
            try:
                await asyncio.sleep(self.config.auto_save_interval)
                await self.save_profiles()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-save error: {e}", exc_info=True)
    
    async def _monitor_loop(self):
        """Monitor profiles and perform maintenance"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check data reset
                if datetime.now() >= self.data_reset_date:
                    await self._reset_data_usage()
                
                # Check global data limit
                if (self.config.global_data_limit_mb and 
                    self.total_data_used_mb >= self.config.global_data_limit_mb):
                    logger.warning(
                        f"Global data limit reached: "
                        f"{self.total_data_used_mb:.1f}/{self.config.global_data_limit_mb:.1f} MB"
                    )
                
                # Maintain quality distribution
                await self._maintain_quality_distribution()
                
                # Collect metrics
                metrics = {
                    'timestamp': datetime.now(),
                    'statistics': self._calculate_statistics(),
                    'active_profiles': len([
                        p for p in self.profiles.values() 
                        if p.last_used and (datetime.now() - p.last_used).days < 1
                    ]),
                }
                self._metrics_history.append(metrics)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}", exc_info=True)
    
    async def _reset_data_usage(self):
        """Reset data usage counters"""
        logger.info("Resetting data usage counters")
        
        self.total_data_used_mb = 0.0
        for profile in self.profiles.values():
            profile.total_data_mb = 0.0
            if profile.proxy_config:
                profile.proxy_config.data_used_mb = 0.0
        
        self.data_reset_date = datetime.now() + timedelta(days=self.config.data_reset_period_days)
        await self.save_profiles()
    
    async def _maintain_quality_distribution(self):
        """Maintain target quality distribution by retiring/generating profiles"""
        current_dist = {}
        for quality in ProfileQuality:
            current_dist[quality] = len(self._quality_index[quality]) / max(1, len(self.profiles))
        
        # Check if we need to adjust
        for quality, target_ratio in self.config.target_quality_distribution.items():
            current_ratio = current_dist[quality]
            
            if current_ratio < target_ratio * 0.8:  # 20% tolerance
                # Need more of this quality
                if quality == ProfileQuality.UNTESTED:
                    # Generate new profiles
                    needed = int((target_ratio - current_ratio) * len(self.profiles))
                    if needed > 0:
                        await self.generate_profiles(needed)
                
            elif current_ratio > target_ratio * 1.2:  # 20% tolerance
                # Too many of this quality
                if quality == ProfileQuality.LOW:
                    # Retire some low-quality profiles
                    candidates = sorted(
                        self._quality_index[quality],
                        key=lambda p: p.health_score
                    )
                    
                    excess = int((current_ratio - target_ratio) * len(self.profiles))
                    for profile in candidates[:excess]:
                        self.retire_profile(profile, "Quality distribution maintenance")
    
    async def optimize_profiles(self):
        """Run optimization pass on all profiles"""
        logger.info("Running profile optimization")
        
        optimized = 0
        
        for profile in list(self.profiles.values()):
            # Update quality ratings
            old_quality = profile.quality
            profile.update_quality()
            
            if old_quality != profile.quality:
                # Re-index if quality changed
                self._quality_index[old_quality].remove(profile)
                self._quality_index[profile.quality].append(profile)
                optimized += 1
            
            # Optimize data usage settings
            if profile.detection_rate > 0.3 and profile.data_optimization_level == DataOptimizationLevel.OFF:
                profile.data_optimization_level = DataOptimizationLevel.BALANCED
                optimized += 1
            elif profile.success_rate > 0.9 and profile.data_optimization_level == DataOptimizationLevel.AGGRESSIVE:
                profile.data_optimization_level = DataOptimizationLevel.MINIMAL
                optimized += 1
        
        logger.info(f"Optimized {optimized} profiles")
        
        if optimized > 0:
            await self.save_profiles()
    
    def get_report(self) -> str:
        """Generate detailed report"""
        stats = self._calculate_statistics()
        
        report_lines = [
            "\n" + "="*60,
            "PROFILE MANAGER REPORT",
            "="*60,
            f"Total Profiles: {stats.get('total_profiles', 0)}",
            f"Average Success Rate: {stats.get('average_success_rate', 0):.1%}",
            f"Average Detection Rate: {stats.get('average_detection_rate', 0):.1%}",
            f"Average Health Score: {stats.get('average_health_score', 0):.1f}",
            f"Total Data Used: {stats.get('total_data_used_mb', 0):.1f} MB",
            f"Profiles with Proxy: {stats.get('profiles_with_proxy', 0)}",
            "",
            "QUALITY DISTRIBUTION:",
        ]
        
        for quality, data in stats.get('quality_distribution', {}).items():
            report_lines.append(f"  {quality}: {data['count']} ({data['percentage']:.1f}%)")
        
        report_lines.extend([
            "",
            "PLATFORM DISTRIBUTION:",
        ])
        
        for platform, count in stats.get('platform_distribution', {}).items():
            percentage = count / max(1, stats.get('total_profiles', 1)) * 100
            report_lines.append(f"  {platform}: {count} ({percentage:.1f}%)")
        
        report_lines.append("="*60)
        
        return "\n".join(report_lines)
    
    async def shutdown(self):
        """Shutdown ProfileManager gracefully"""
        logger.info("Shutting down ProfileManager")
        
        # Cancel tasks
        for task in [self._save_task, self._monitor_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Final save
        await self.save_profiles()
        
        logger.info("ProfileManager shutdown complete")


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_profile_from_config(config: Dict[str, Any]) -> BrowserProfile:
    """Create profile from configuration dictionary"""
    return BrowserProfile.from_dict(config)

def create_profile_manager_from_config(config_path: str) -> ProfileManager:
    """Create ProfileManager from YAML configuration file"""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Extract proxy configurations
    proxy_configs = []
    for proxy_data in config_data.get('proxies', []):
        if all(key in proxy_data for key in ['endpoint', 'username', 'password']):
            proxy_configs.append(ProxyConfig(**proxy_data))
        else:
            logger.warning(f"Skipping invalid proxy configuration: {proxy_data}")
    
    # Create ProfileManagerConfig
    pm_config_data = config_data.get('profile_manager', {})
    pm_config_data['proxy_configs'] = proxy_configs
    
    pm_config = ProfileManagerConfig(**pm_config_data)
    
    @property
    def profiles(self) -> Dict[str, BrowserProfile]:
        """Get static browser profiles adapted from dynamic profiles"""
        static_profiles = {}
        for dynamic_profile in self.dynamic_profiles:
            static_profile = self.adapt_dynamic_profile_to_static(dynamic_profile)
            static_profiles[dynamic_profile.id] = static_profile
        return static_profiles
    
    return ProfileManager(pm_config)


# ============================================================================
# EXAMPLE CONFIGURATION LOADER
# ============================================================================

def load_iprroyal_proxy_from_env() -> Optional[ProxyConfig]:
    """Load IPRoyal proxy configuration from environment variables"""
    endpoint = os.getenv('IPROYAL_ENDPOINT')
    username = os.getenv('IPROYAL_USERNAME')
    password = os.getenv('IPROYAL_PASSWORD')
    
    if not all([endpoint, username, password]):
        return None
    
    return ProxyConfig(
        endpoint=endpoint,
        username=username,
        password=password,
        country=os.getenv('IPROYAL_COUNTRY'),
        city=os.getenv('IPROYAL_CITY'),
        sticky_session=os.getenv('IPROYAL_STICKY_SESSION', 'true').lower() == 'true',
        session_duration_minutes=int(os.getenv('IPROYAL_SESSION_DURATION', '10')),
        rotation_interval_seconds=int(os.getenv('IPROYAL_ROTATION_INTERVAL', '300')),
        compression_enabled=True,
        bandwidth_limit_mb=float(os.getenv('IPROYAL_BANDWIDTH_LIMIT_MB', '0')) or None,
    )


# Example usage for testing
if __name__ == "__main__":
    async def test():
        # Create proxy config
        proxy = ProxyConfig(
            endpoint="proxy.iproyal.com:12321",
            username="user123",
            password="pass456",
            country="US",
            sticky_session=True,
            compression_enabled=True
        )
        
        # Create profile with proxy
        profile = BrowserProfile(
            name="test_profile",
            proxy_config=proxy,
            data_optimization_level=DataOptimizationLevel.BALANCED
        )
        
        print(f"Profile: {profile.name}")
        print(f"Proxy URL: {profile.proxy_config.get_proxy_url()}")
        print(f"Resource blocks: {profile.get_resource_block_patterns()}")
        
        # Test ProfileManager
        pm_config = ProfileManagerConfig(proxy_configs=[proxy])
        pm = ProfileManager(pm_config)
        await pm.initialize()
        
        # Select profile
        selected = await pm.select_profile(platform="ticketmaster")
        print(f"Selected: {selected.name} (quality: {selected.quality.name})")
        
        await pm.shutdown()
    
    asyncio.run(test())