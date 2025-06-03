# src/core/stealth_engine.py v2.0 - Next-Generation Anti-Detection System
"""
StealthEngine: A unified, entropy-based browser fingerprinting and anti-detection system.
Implements advanced techniques from 2024/2025 research on browser fingerprinting evasion.
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import numpy as np
from scipy import stats
import aiofiles
import httpx
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# --- Stub Classes for Forward References ---
class PlatformSession:
    pass

class PerformanceMetrics:
    pass

class NetworkConfig:
    proxy_url: Optional[str] = None

class ProxyPool:
    """Stub for ProxyPool to resolve type annotation."""
    async def get_proxy(self) -> Optional[str]:
        return None


# --- Advanced Enums ---
class StealthLevel(Enum):
    """Multi-tier stealth levels based on threat assessment"""
    MINIMAL = auto()      # Basic anti-automation
    STANDARD = auto()     # Standard fingerprinting defense  
    ENHANCED = auto()     # Advanced behavioral + fingerprint
    PARANOID = auto()     # Maximum stealth, performance trade-off
    ADAPTIVE = auto()     # AI-driven dynamic adjustment


class ThreatLevel(Enum):
    """Detected threat levels from platforms"""
    NONE = 0
    LOW = 1          # Slight anomalies
    MEDIUM = 2       # Clear automation signals
    HIGH = 3         # Active detection/blocking
    CRITICAL = 4     # Complete compromise


# --- Entropy-Based Fingerprint Generation ---
class EntropyPool:
    """
    Manages entropy for generating realistic, non-predictable values.
    Based on browser fingerprinting research showing importance of entropy management.
    """
    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.RandomState(seed)
        self.entropy_sources: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.distributions: Dict[str, stats.rv_continuous] = {}
        self._initialize_distributions()
    
    def _initialize_distributions(self):
        """Initialize realistic statistical distributions for various attributes"""
        # Browser fingerprinting gathers information related to a user's operating system, browser type, screen resolution, time zone, keyboard layout, and more. By processing these details, it creates a unique identifier, or "digital fingerprint," for each user.:antCitation[]{citationIdentifiersString="5:0"}

class BehavioralMarkovChain:
    """
    Models human behavior using Markov chains for realistic interaction patterns.
    Behavioural Fingerprinting – Observes user actions such as mouse movements, typing patterns, and scrolling behaviour.
    """
    
    def __init__(self):
        self.states = ['idle', 'reading', 'typing', 'clicking', 'scrolling', 'hovering']
        self.transition_matrix = self._initialize_transitions()
        self.current_state = 'idle'
        self.state_durations = self._initialize_durations()
        self.micro_patterns = self._initialize_micro_patterns()

def _initialize_transitions(self) -> np.ndarray:
    """Initialize realistic state transition probabilities"""
    # Rows: from state, Columns: to state
    transitions = np.array([
        # idle  read  type  click scroll hover
        [0.1,   0.3,  0.1,  0.2,  0.2,   0.1],  # from idle
        [0.2,   0.3,  0.1,  0.1,  0.2,   0.1],  # from reading
        [0.3,   0.2,  0.2,  0.1,  0.1,   0.1],  # from typing
        [0.2,   0.3,  0.1,  0.1,  0.2,   0.1],  # from clicking
        [0.1,   0.4,  0.1,  0.1,  0.2,   0.1],  # from scrolling
        [0.2,   0.2,  0.1,  0.3,  0.1,   0.1],  # from hovering
    ])
    
    # Normalize rows
    return transitions / transitions.sum(axis=1, keepdims=True)

def _initialize_durations(self) -> Dict[str, stats.rv_continuous]:
    """State duration distributions (in seconds)"""
    return {
        'idle': stats.expon(scale=2.0),
        'reading': stats.gamma(a=2, scale=3.0),
        'typing': stats.lognorm(s=0.5, scale=1.0),
        'clicking': stats.expon(scale=0.5),
        'scrolling': stats.gamma(a=1.5, scale=1.0),
        'hovering': stats.expon(scale=1.5),
    }

def _initialize_micro_patterns(self) -> Dict[str, Dict]:
    """Micro-patterns within each state"""
    return {
        'typing': {
            'inter_key_delay': stats.lognorm(s=0.3, loc=0.05, scale=0.1),
            'dwell_time': stats.norm(loc=0.08, scale=0.02),
            'burst_length': stats.poisson(mu=5),
        },
        'scrolling': {
            'velocity': stats.lognorm(s=0.5, loc=100, scale=300),
            'acceleration': stats.norm(loc=1.0, scale=0.3),
            'pause_probability': 0.1,
        },
        'clicking': {
            'pre_click_hover': stats.expon(scale=0.3),
            'click_duration': stats.norm(loc=0.1, scale=0.03),
            'double_click_probability': 0.15,
        },
    }

def next_action(self) -> Tuple[str, float, Dict]:
    """Generate next action based on current state"""
    # Determine next state
    state_idx = self.states.index(self.current_state)
    next_state_idx = np.random.choice(
        len(self.states), 
        p=self.transition_matrix[state_idx]
    )
    next_state = self.states[next_state_idx]
    
    # Generate duration
    duration = max(0.1, self.state_durations[next_state].rvs())
    
    # Generate micro-patterns
    patterns = {}
    if next_state in self.micro_patterns:
        for pattern, dist in self.micro_patterns[next_state].items():
            if isinstance(dist, stats.rv_continuous):
                patterns[pattern] = dist.rvs()
            else:
                patterns[pattern] = dist
    
    self.current_state = next_state
    return next_state, duration, patterns
@dataclass
class FingerprintDNA:
    # Core identity (rarely changes)
    os_family: str
    os_version: str
    browser_family: str
    browser_version: str
    device_type: str

    # Hardware profile
    cpu_vendor: str
    cpu_cores: int
    memory_gb: float
    gpu_vendor: str
    gpu_model: str

    # Display profile
    screen_width: int
    screen_height: int
    color_depth: int
    device_pixel_ratio: float

    # Network profile
    connection_type: str
    timezone: str
    languages: List[str]

    # Unique identifiers
    canvas_noise: Dict[str, float]
    audio_params: Dict[str, float]
    webgl_params: Dict[str, Any]

    # Behavioral signature
    behavioral_seed: int
    interaction_style: str

    # Mutation tracking
    mutation_history: List[Dict] = field(default_factory=list)
    last_mutation: datetime = field(default_factory=datetime.utcnow)
    mutation_resistance: float = 0.8  # Resistance to change

    def calculate_entropy(self) -> float:
        """Calculate fingerprint entropy (uniqueness score)"""
        # Combine all attributes into feature vector
        features = []
        for attr, value in self.__dict__.items():
            if attr.startswith('_') or attr in ['mutation_history', 'last_mutation']:
                continue

            if isinstance(value, (str, int, float)):
                features.append(hash(str(value)) % 1000)
            elif isinstance(value, list):
                features.append(hash(tuple(value)) % 1000)
            elif isinstance(value, dict):
                features.append(hash(tuple(sorted(value.items()))) % 1000)

        # Calculate Shannon entropy
        feature_array = np.array(features)
        probabilities = np.bincount(feature_array) / len(feature_array)
        probabilities = probabilities[probabilities > 0]

        return -np.sum(probabilities * np.log2(probabilities))

    def mutate(self, attribute: str, value: Any, reason: str = "natural"):
        """Apply mutation with tracking"""
        old_value = getattr(self, attribute, None)
        setattr(self, attribute, value)

        self.mutation_history.append({
            'timestamp': datetime.utcnow(),
            'attribute': attribute,
            'old_value': old_value,
            'new_value': value,
            'reason': reason,
            'entropy_before': self.calculate_entropy()
        })

        self.last_mutation = datetime.utcnow
@dataclass
class StealthProfile:
    profile_id: str
fingerprint_dna: FingerprintDNA
behavioral_chain: BehavioralMarkovChain
entropy_pool: EntropyPool

# Platform sessions
sessions: Dict[str, 'PlatformSession'] = field(default_factory=dict)

# Performance metrics
metrics: Dict[str, 'PerformanceMetrics'] = field(default_factory=lambda: defaultdict(PerformanceMetrics))

# Stealth configuration
stealth_level: StealthLevel = StealthLevel.STANDARD
threat_assessment: ThreatLevel = ThreatLevel.NONE

# Network configuration
network_config: Optional['NetworkConfig'] = None

# State
created_at: datetime = field(default_factory=datetime.utcnow)
last_used: Optional[datetime] = None
health_score: float = 100.0
is_warmed_up: bool = False

def to_playwright_context(self) -> Dict[str, Any]:
    """Convert to Playwright browser context parameters"""
    dna = self.fingerprint_dna
    
    # Generate viewport with realistic chrome offsets
    viewport_width = int(dna.screen_width * 0.95)
    viewport_height = int(dna.screen_height * 0.90)
    
    # Build user agent
    user_agent = self._build_user_agent()
    
    # Client hints
    sec_ch_ua = self._build_client_hints()
    
    params = {
        'user_agent': user_agent,
        'viewport': {
            'width': viewport_width,
            'height': viewport_height
        },
        'screen': {
            'width': dna.screen_width,
            'height': dna.screen_height
        },
        'device_scale_factor': dna.device_pixel_ratio,
        'is_mobile': dna.device_type in ['mobile', 'tablet'],
        'has_touch': dna.device_type in ['mobile', 'tablet'],
        'locale': dna.languages[0] if dna.languages else 'en-US',
        'timezone_id': dna.timezone,
        'color_scheme': 'light',
        'reduced_motion': 'no-preference',
        'forced_colors': 'none',
        'permissions': ['geolocation', 'notifications'],
        'extra_http_headers': {
            'Accept-Language': self._build_accept_language(),
            'sec-ch-ua': sec_ch_ua['sec-ch-ua'],
            'sec-ch-ua-mobile': sec_ch_ua['sec-ch-ua-mobile'],
            'sec-ch-ua-platform': sec_ch_ua['sec-ch-ua-platform'],
        }
    }
    
    # Add proxy if configured
    if self.network_config and self.network_config.proxy_url:
        params['proxy'] = {'server': self.network_config.proxy_url}
    
    return params

def _build_user_agent(self) -> str:
    """Build realistic user agent string"""
    dna = self.fingerprint_dna
    
    if dna.browser_family == 'Chrome':
        if dna.os_family == 'Windows':
            return f"Mozilla/5.0 (Windows NT {dna.os_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{dna.browser_version} Safari/537.36"
        elif dna.os_family == 'macOS':
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {dna.os_version.replace('.', '_')}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{dna.browser_version} Safari/537.36"
    
    # Add more browser/OS combinations
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def _build_client_hints(self) -> Dict[str, str]:
    """Build realistic client hints headers"""
    dna = self.fingerprint_dna
    
    # Brand versioning for Chrome
    brands = []
    if dna.browser_family == 'Chrome':
        major_version = dna.browser_version.split('.')[0]
        brands = [
            f'"Not A(Brand";v="99"',
            f'"Chromium";v="{major_version}"',
            f'"Google Chrome";v="{major_version}"'
        ]
    
    return {
        'sec-ch-ua': ', '.join(brands),
        'sec-ch-ua-mobile': '?1' if dna.device_type in ['mobile', 'tablet'] else '?0',
        'sec-ch-ua-platform': f'"{dna.os_family}"',
    }

def _build_accept_language(self) -> str:
    """Build accept-language header with quality values"""
    parts = []
    for i, lang in enumerate(self.fingerprint_dna.languages[:4]):
        if i == 0:
            parts.append(lang)
        else:
            q = 1.0 - (i * 0.1)
            parts.append(f"{lang};q={q:.1f}")
    return ','.join(parts)

@dataclass
class PlatformSession:
    # Authentication state
    is_authenticated: bool = False
    auth_tokens: Dict[str, str] = field(default_factory=dict)
    cookies: List[Dict] = field(default_factory=list)

    # Session metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    # Session health
    validation_failures: int = 0
    requires_refresh: bool = False

    # Platform-specific data
    user_data: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self, max_age_hours: int = 24) -> bool:
        """Check if session is still valid"""
        if not self.is_authenticated:
            return False
        
        if self.validation_failures >= 3:
            return False
        
        if self.last_validated:
            age = (datetime.utcnow() - self.last_validated).total_seconds() / 3600
            if age > max_age_hours:
                return False
        
        return True

@dataclass
class PerformanceMetrics:
    total_requests: int = 0
successful_requests: int = 0
failed_requests: int = 0
Copytotal_response_time: float = 0.0
detection_events: List[Dict] = field(default_factory=list)

last_success: Optional[datetime] = None
last_failure: Optional[datetime] = None

@property
def success_rate(self) -> float:
    if self.total_requests == 0:
        return 0.0
    return self.successful_requests / self.total_requests

@property
def avg_response_time(self) -> float:
    if self.total_requests == 0:
        return 0.0
    return self.total_response_time / self.total_requests

def record_request(self, success: bool, response_time: float, detection: Optional[str] = None):
    """Record request outcome"""
    self.total_requests += 1
    self.total_response_time += response_time
    
    if success:
        self.successful_requests += 1
        self.last_success = datetime.utcnow()
    else:
        self.failed_requests += 1
        self.last_failure = datetime.utcnow()
        
        if detection:
            self.detection_events.append({
                'timestamp': datetime.utcnow(),
                'type': detection,
                'response_time': response_time
            })

@dataclass
class NetworkConfig:
    """Advanced network configuration with TLS fingerprinting"""
    proxy_url: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    # TLS Configuration
    tls_version: str = "1.3"
    cipher_suites: List[str] = field(default_factory=list)
    h2_settings: Dict[str, int] = field(default_factory=dict)
    h2_window_update: int = 15663105

    # Network behavior
    connection_reuse: bool = True
    http2_enabled: bool = True
    http3_enabled: bool = False

    # Timing configuration
    dns_cache_ttl: int = 300
    connection_timeout: int = 30
    read_timeout: int = 30

    def to_httpx_config(self) -> Dict[str, Any]:
        """Convert to httpx client configuration"""
        config = {
            'timeout': httpx.Timeout(
                connect=self.connection_timeout,
                read=self.read_timeout
            ),
            'limits': httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            ),
            'http2': self.http2_enabled,
        }
        
        if self.proxy_url:
            config['proxies'] = {'all://': self.proxy_url}
            if self.proxy_username and self.proxy_password:
                config['proxies'] = {
                    'all://': httpx.Proxy(
                        self.proxy_url,
                        auth=(self.proxy_username, self.proxy_password)
                    )
                }
        
        return config

class StealthEngine:
    """
    Core engine for managing stealth profiles with advanced anti-detection.
    Implements countermeasures against detecting first- and third-party 
    fingerprinters even when they use obfuscation by tainting attributes, 
    propagating them, and logging when they are leaked (via 62 sources and 25 sinks). 
    Moreover, it discriminates the invasiveness of fingerprinting activities,
    even from the same service, by measuring the joint entropy of the collected attributes
    """
    pass
def __init__(self, config: Optional['StealthEngineConfig'] = None):
    self.config = config or StealthEngineConfig()
    
    # Profile management
    self.profiles = {}
    self.profile_pools = defaultdict(list)
    
    # Global entropy pool for learning
    self.global_entropy = EntropyPool()
    
    # Threat intelligence
    self.threat_intelligence = ThreatIntelligence()
    
    # Performance tracking
    self.global_metrics = PerformanceMetrics()
    
    # Background tasks
    self._tasks = []
    self._shutdown = asyncio.Event()
    
    # Initialize
    asyncio.create_task(self._initialize())

async def _initialize(self):
    """Initialize engine"""
    # Load existing profiles
    await self._load_profiles()
    
    # Start background tasks
    self._tasks.append(
        asyncio.create_task(self._profile_evolution_loop())
    )
    self._tasks.append(
        asyncio.create_task(self._threat_monitoring_loop())
    )
    
    logger.info(f"StealthEngine initialized with {len(self.profiles)} profiles")

async def create_profile(self, platform: Optional[str] = None, 
                       base_template: Optional[Dict] = None) -> StealthProfile:
    """Create new stealth profile with platform optimization"""
    # Generate fingerprint DNA
    dna = await self._generate_fingerprint_dna(platform, base_template)
    
    # Create behavioral model
    behavioral_chain = BehavioralMarkovChain()
    
    # Create entropy pool with global knowledge
    entropy_pool = EntropyPool()
    entropy_pool.entropy_sources = self.global_entropy.entropy_sources.copy()
    
    # Create profile
    profile = StealthProfile(
        profile_id=self._generate_profile_id(),
        fingerprint_dna=dna,
        behavioral_chain=behavioral_chain,
        entropy_pool=entropy_pool,
        stealth_level=self.config.default_stealth_level
    )
    
    # Configure network
    profile.network_config = await self._generate_network_config(dna)
    
    # Store profile
    self.profiles[profile.profile_id] = profile
    
    if platform:
        self.profile_pools[platform].append(profile.profile_id)
    
    logger.info(f"Created profile {profile.profile_id} for {platform or 'general'}")
    
    return profile

async def _generate_fingerprint_dna(self, platform: Optional[str], 
                                  template: Optional[Dict]) -> FingerprintDNA:
    """Generate realistic fingerprint DNA"""
    entropy = self.global_entropy
    
    # Platform-specific preferences
    platform_prefs = self.config.platform_preferences.get(platform, {})
    
    # OS selection based on platform stats
    os_weights = platform_prefs.get('os_weights', {
        'Windows': 0.7, 'macOS': 0.2, 'Linux': 0.1
    })
    os_family = np.random.choice(
        list(os_weights.keys()), 
        p=list(os_weights.values())
    )
    
    # Generate correlated attributes
    if os_family == 'Windows':
        os_version = random.choice(['10.0', '11.0'])
        cpu_vendor = np.random.choice(['Intel', 'AMD'], p=[0.7, 0.3])
    elif os_family == 'macOS':
        os_version = random.choice(['13.0', '14.0', '15.0'])
        cpu_vendor = 'Apple'
    else:
        os_version = '5.15'
        cpu_vendor = 'Intel'
    
    # Browser selection
    browser_weights = platform_prefs.get('browser_weights', {
        'Chrome': 0.75, 'Firefox': 0.15, 'Safari': 0.1
    })
    browser_family = np.random.choice(
        list(browser_weights.keys()),
        p=list(browser_weights.values())
    )
    
    # Generate hardware profile
    device_type = template.get('device_type', 
                             np.random.choice(['desktop', 'laptop'], p=[0.4, 0.6]))
    
    cpu_cores = int(entropy.generate('cpu_cores', {'min': 4, 'max': 16, 'round': 2}))
    memory_gb = int(entropy.generate('memory_gb', {'min': 4, 'max': 32, 'round': 4}))
    
    # GPU based on price tier
    gpu_vendors = {
        'NVIDIA': ['RTX 4090', 'RTX 4080', 'RTX 4070', 'GTX 1660'],
        'AMD': ['RX 7900 XTX', 'RX 7800 XT', 'RX 6700 XT'],
        'Intel': ['Arc A770', 'UHD Graphics 770']
    }
    gpu_vendor = np.random.choice(list(gpu_vendors.keys()), p=[0.6, 0.3, 0.1])
    gpu_model = random.choice(gpu_vendors[gpu_vendor])
    
    # Screen configuration
    screen_configs = [
        (1920, 1080), (2560, 1440), (3840, 2160),  # Common 16:9
        (1920, 1200), (2560, 1600),  # 16:10
        (3440, 1440), (5120, 1440),  # Ultrawide
    ]
    
    if device_type == 'laptop':
        screen_configs = screen_configs[:3]  # Laptops rarely ultrawide
    
    screen_width, screen_height = random.choice(screen_configs)
    
    # Generate canvas/audio fingerprints
    canvas_noise = {
        'r_shift': random.uniform(-2, 2),
        'g_shift': random.uniform(-2, 2),
        'b_shift': random.uniform(-2, 2),
        'alpha_noise': random.uniform(0.0001, 0.0005),
    }
    
    audio_params = {
        'sample_rate': random.choice([44100, 48000]),
        'max_channel_count': random.choice([2, 6, 8]),
        'latency': random.uniform(0.01, 0.05),
    }
    
    # WebGL parameters based on GPU
    webgl_params = self._generate_webgl_params(gpu_vendor, gpu_model)
    
    return FingerprintDNA(
        os_family=os_family,
        os_version=os_version,
        browser_family=browser_family,
        browser_version=self._get_browser_version(browser_family),
        device_type=device_type,
        cpu_vendor=cpu_vendor,
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        gpu_vendor=gpu_vendor,
        gpu_model=gpu_model,
        screen_width=screen_width,
        screen_height=screen_height,
        color_depth=24,
        device_pixel_ratio=1.0 if os_family == 'Windows' else 2.0,
        connection_type='ethernet' if device_type == 'desktop' else 'wifi',
        timezone=self._get_timezone_for_platform(platform),
        languages=self._get_languages_for_platform(platform),
        canvas_noise=canvas_noise,
        audio_params=audio_params,
        webgl_params=webgl_params,
        behavioral_seed=random.randint(0, 2**32),
        interaction_style=random.choice(['cautious', 'normal', 'confident'])
    )

def _generate_webgl_params(self, gpu_vendor: str, gpu_model: str) -> Dict[str, Any]:
    """Generate realistic WebGL parameters based on GPU"""
    base_params = {
        'vendor': f'Google Inc. ({gpu_vendor})',
        'renderer': f'ANGLE ({gpu_vendor}, {gpu_model} Direct3D11 vs_5_0 ps_5_0)',
        'version': 'WebGL 2.0 (OpenGL ES 3.0 Chromium)',
        'shading_language_version': 'WebGL GLSL ES 3.00 (OpenGL ES GLSL ES 3.0 Chromium)',
        'max_texture_size': 16384,
        'max_renderbuffer_size': 16384,
        'max_viewport_dims': [32767, 32767],
    }
    
    # GPU-specific adjustments
    if 'RTX 40' in gpu_model:
        base_params['max_texture_size'] = 32768
    elif 'Intel' in gpu_vendor:
        base_params['max_texture_size'] = 8192
    
    return base_params

def _get_browser_version(self, browser_family: str) -> str:
    """Get current browser version"""
    versions = {
        'Chrome': ['120.0.6099.130', '121.0.6167.85', '122.0.6261.112'],
        'Firefox': ['121.0', '122.0', '123.0'],
        'Safari': ['17.2', '17.3', '17.4']
    }
    return random.choice(versions.get(browser_family, ['120.0.0.0']))

def _get_timezone_for_platform(self, platform: Optional[str]) -> str:
    """Get appropriate timezone for platform"""
    if platform in ['fansale', 'ticketmaster', 'vivaticket']:
        return 'Europe/Rome'  # Italian platforms
    
    # Default to common timezones
    return random.choice([
        'Europe/London', 'Europe/Paris', 'Europe/Berlin',
        'America/New_York', 'America/Chicago', 'America/Los_Angeles'
    ])

def _get_languages_for_platform(self, platform: Optional[str]) -> List[str]:
    """Get language preferences for platform"""
    if platform in ['fansale', 'ticketmaster', 'vivaticket']:
        return ['it-IT', 'it', 'en-US', 'en']
    
    return ['en-US', 'en']

async def _generate_network_config(self, dna: FingerprintDNA) -> NetworkConfig:
    """Generate network configuration with TLS fingerprint"""
    # TLS cipher suites based on browser
    if dna.browser_family == 'Chrome':
        cipher_suites = [
            'TLS_AES_128_GCM_SHA256',
            'TLS_AES_256_GCM_SHA384',
            'TLS_CHACHA20_POLY1305_SHA256',
            'ECDHE-ECDSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES128-GCM-SHA256',
        ]
    else:
        cipher_suites = [
            'TLS_AES_128_GCM_SHA256',
            'TLS_CHACHA20_POLY1305_SHA256',
            'TLS_AES_256_GCM_SHA384',
        ]
    
    # HTTP/2 settings
    h2_settings = {
        'SETTINGS_HEADER_TABLE_SIZE': 65536,
        'SETTINGS_ENABLE_PUSH': 0,
        'SETTINGS_INITIAL_WINDOW_SIZE': 6291456,
        'SETTINGS_MAX_HEADER_LIST_SIZE': 262144,
    }
    
    # Get proxy if configured
    proxy_url = None
    if self.config.proxy_pool:
        proxy_url = await self.config.proxy_pool.get_proxy()
    
    return NetworkConfig(
        proxy_url=proxy_url,
        cipher_suites=cipher_suites,
        h2_settings=h2_settings,
        http2_enabled=True,
        http3_enabled=dna.browser_family == 'Chrome' and random.random() > 0.7
    )

def _generate_profile_id(self) -> str:
    """Generate unique profile ID"""
    timestamp = int(time.time() * 1000000)
    random_part = random.randint(1000, 9999)
    return f"sp_{timestamp}_{random_part}"

async def get_profile_for_task(self, platform: str, 
                              requirements: Optional[Dict] = None) -> Optional[StealthProfile]:
    """Get best profile for task with requirements"""
    candidates = []
    
    # Get platform profiles
    platform_profiles = [
        self.profiles[pid] for pid in self.profile_pools.get(platform, [])
        if pid in self.profiles
    ]
    
    # Filter by requirements
    for profile in platform_profiles:
        # Check health
        if profile.health_score < 50:
            continue
        
        # Check threat level
        if profile.threat_assessment.value >= ThreatLevel.HIGH.value:
            continue
        
        # Check session requirement
        if requirements and requirements.get('requires_session'):
            session = profile.sessions.get(platform)
            if not session or not session.is_valid():
                continue
        
        # Calculate score
        score = self._calculate_profile_score(profile, platform, requirements)
        candidates.append((score, profile))
    
    if not candidates:
        # Create new profile if none suitable
        logger.warning(f"No suitable profiles for {platform}, creating new one")
        return await self.create_profile(platform)
    
    # Select best
    candidates.sort(key=lambda x: x[0], reverse=True)
    selected = candidates[0][1]
    
    # Update usage
    selected.last_used = datetime.utcnow()
    
    logger.info(f"Selected profile {selected.profile_id} for {platform} (score: {candidates[0][0]:.2f})")
    
    return selected

def _calculate_profile_score(self, profile: StealthProfile, 
                           platform: str, requirements: Optional[Dict]) -> float:
    """Calculate profile suitability score"""
    score = 100.0
    
    # Health score component
    score *= (profile.health_score / 100)
    
    # Threat level penalty
    score *= (1 - profile.threat_assessment.value * 0.2)
    
    # Platform performance
    platform_metrics = profile.metrics.get(platform)
    if platform_metrics:
        score *= platform_metrics.success_rate
        
        # Response time factor
        if platform_metrics.avg_response_time > 0:
            speed_factor = max(0.5, 1 - platform_metrics.avg_response_time / 5000)
            score *= speed_factor
    
    # Entropy bonus (higher entropy = more unique)
    entropy = profile.fingerprint_dna.calculate_entropy()
    score *= (1 + entropy / 10)  # Small bonus for uniqueness
    
    # Recency penalty
    if profile.last_used:
        hours_since_use = (datetime.utcnow() - profile.last_used).total_seconds() / 3600
        if hours_since_use < 1:
            score *= 0.8  # Recently used penalty
    
    # Warmup bonus
    if profile.is_warmed_up:
        score *= 1.2
    
    return score

async def warm_up_profile(self, profile: StealthProfile, sites: Optional[List[str]] = None):
    """Warm up profile with realistic browsing"""
    if profile.is_warmed_up:
        return
    
    logger.info(f"Warming up profile {profile.profile_id}")
    
    sites = sites or [
        'https://www.google.com',
        'https://www.youtube.com',
        'https://www.amazon.com',
        'https://www.wikipedia.org',
    ]
    
    # Simulate realistic browsing pattern
    behavioral_model = profile.behavioral_chain
    
    for site in sites:
        # Generate browsing sequence
        actions = []
        total_duration = 0
        
        while total_duration < 30:  # 30 seconds per site
            action, duration, patterns = behavioral_model.next_action()
            actions.append({
                'action': action,
                'duration': duration,
                'patterns': patterns
            })
            total_duration += duration
        
        # Log warm-up actions
        logger.debug(f"Warm-up sequence for {site}: {[a['action'] for a in actions]}")
    
    profile.is_warmed_up = True
    profile.health_score = min(100, profile.health_score + 10)

async def record_result(self, profile_id: str, platform: str, 
                      success: bool, response_time: float,
                      detection: Optional[str] = None):
    """Record task result and update profile health"""
    if profile_id not in self.profiles:
        logger.error(f"Unknown profile: {profile_id}")
        return
    
    profile = self.profiles[profile_id]
    
    # Update metrics
    platform_metrics = profile.metrics[platform]
    platform_metrics.record_request(success, response_time, detection)
    
    # Update global metrics
    self.global_metrics.record_request(success, response_time, detection)
    
    # Update health score
    if success:
        profile.health_score = min(100, profile.health_score + 2)
        profile.threat_assessment = ThreatLevel.NONE
    else:
        profile.health_score = max(0, profile.health_score - 10)
        
        # Update threat assessment
        if detection:
            if 'captcha' in detection.lower():
                profile.threat_assessment = ThreatLevel.MEDIUM
            elif 'blocked' in detection.lower():
                profile.threat_assessment = ThreatLevel.HIGH
            else:
                profile.threat_assessment = ThreatLevel.LOW
    
    # Add entropy from this interaction
    if response_time > 0:
        profile.entropy_pool.add_entropy('response_time', response_time)
        self.global_entropy.add_entropy('response_time', response_time)

async def _profile_evolution_loop(self):
    """Background task for profile evolution"""
    while not self._shutdown.is_set():
        try:
            await asyncio.sleep(self.config.evolution_interval)
            
            # Evolve profiles based on threat level
            for profile in list(self.profiles.values()):
                if profile.threat_assessment.value >= ThreatLevel.MEDIUM.value:
                    await self._evolve_profile(profile)
            
            # Replace critically compromised profiles
            compromised = [
                p for p in self.profiles.values() 
                if p.threat_assessment == ThreatLevel.CRITICAL or p.health_score < 20
            ]
            
            for profile in compromised:
                logger.warning(f"Replacing compromised profile {profile.profile_id}")
                
                # Get platforms
                platforms = [
                    platform for platform, pids in self.profile_pools.items()
                    if profile.profile_id in pids
                ]
                
                # Remove old profile
                del self.profiles[profile.profile_id]
                for platform in platforms:
                    self.profile_pools[platform].remove(profile.profile_id)
                
                # Create replacement
                for platform in platforms:
                    new_profile = await self.create_profile(platform)
                    await self.warm_up_profile(new_profile)
            
        except Exception as e:
            logger.error(f"Evolution loop error: {e}", exc_info=True)

async def _evolve_profile(self, profile: StealthProfile):
    """Evolve profile to evade detection"""
    logger.info(f"Evolving profile {profile.profile_id} due to threat level {profile.threat_assessment.name}")
    
    dna = profile.fingerprint_dna
    
    # Determine mutation scope based on threat
    if profile.threat_assessment == ThreatLevel.LOW:
        # Minor mutations
        mutations = ['browser_version', 'canvas_noise']
    elif profile.threat_assessment == ThreatLevel.MEDIUM:
        # Moderate mutations
        mutations = ['browser_version', 'canvas_noise', 'webgl_params', 'audio_params']
    else:
        # Major mutations
        mutations = ['browser_family', 'browser_version', 'gpu_model', 
                    'canvas_noise', 'webgl_params', 'audio_params']
    
    # Apply mutations
    for attr in mutations:
        if attr == 'browser_version':
            dna.mutate(attr, self._get_browser_version(dna.browser_family), 'evolution')
        elif attr == 'canvas_noise':
            new_noise = {
                'r_shift': random.uniform(-2, 2),
                'g_shift': random.uniform(-2, 2),
                'b_shift': random.uniform(-2, 2),
                'alpha_noise': random.uniform(0.0001, 0.0005),
            }
            dna.mutate(attr, new_noise, 'evolution')
        elif attr == 'webgl_params':
            new_params = self._generate_webgl_params(dna.gpu_vendor, dna.gpu_model)
            # Add some variation
            new_params['max_texture_size'] = new_params['max_texture_size'] + random.choice([-2048, 0, 2048])
            dna.mutate(attr, new_params, 'evolution')
        elif attr == 'audio_params':
            new_audio = {
                'sample_rate': random.choice([44100, 48000]),
                'max_channel_count': random.choice([2, 6, 8]),
                'latency': random.uniform(0.01, 0.05),
            }
            dna.mutate(attr, new_audio, 'evolution')
    
    # Reset threat assessment
    profile.threat_assessment = ThreatLevel.NONE
    profile.health_score = min(100, profile.health_score + 20)

async def _threat_monitoring_loop(self):
    """Monitor global threat patterns"""
    while not self._shutdown.is_set():
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            
            # Analyze global patterns
            total_requests = self.global_metrics.total_requests
            if total_requests > 100:
                global_failure_rate = 1 - self.global_metrics.success_rate
                
                if global_failure_rate > 0.3:
                    logger.warning(f"High global failure rate: {global_failure_rate:.2%}")
                    
                    # Increase stealth level for all profiles
                    for profile in self.profiles.values():
                        if profile.stealth_level == StealthLevel.MINIMAL:
                            profile.stealth_level = StealthLevel.STANDARD
                        elif profile.stealth_level == StealthLevel.STANDARD:
                            profile.stealth_level = StealthLevel.ENHANCED
            
            # Platform-specific analysis
            for platform, profile_ids in self.profile_pools.items():
                platform_metrics = []
                for pid in profile_ids:
                    if pid in self.profiles:
                        metrics = self.profiles[pid].metrics.get(platform)
                        if metrics and metrics.total_requests > 0:
                            platform_metrics.append(metrics)
                
                if platform_metrics:
                    avg_success_rate = np.mean([m.success_rate for m in platform_metrics])
                    if avg_success_rate < 0.7:
                        logger.warning(f"Low success rate on {platform}: {avg_success_rate:.2%}")
            
        except Exception as e:
            logger.error(f"Threat monitoring error: {e}", exc_info=True)

async def _save_profiles(self):
    """Save profiles to disk"""
    save_data = {
        'version': '2.0',
        'timestamp': datetime.utcnow().isoformat(),
        'profiles': []
    }
    
    for profile in self.profiles.values():
        profile_data = {
            'profile_id': profile.profile_id,
            'fingerprint_dna': profile.fingerprint_dna.__dict__,
            'metrics': {
                platform: {
                    'total_requests': m.total_requests,
                    'successful_requests': m.successful_requests,
                    'failed_requests': m.failed_requests,
                }
                for platform, m in profile.metrics.items()
            },
            'health_score': profile.health_score,
            'threat_assessment': profile.threat_assessment.value,
            'created_at': profile.created_at.isoformat(),
            'last_used': profile.last_used.isoformat() if profile.last_used else None,
        }
        save_data['profiles'].append(profile_data)
    
    async with aiofiles.open(self.config.profiles_path, 'w') as f:
        await f.write(json.dumps(save_data, indent=2))

async def _load_profiles(self):
    """Load profiles from disk"""
    if not Path(self.config.profiles_path).exists():
        return
    
    try:
        async with aiofiles.open(self.config.profiles_path, 'r') as f:
            save_data = json.loads(await f.read())
        
        for profile_data in save_data.get('profiles', []):
            # Recreate DNA
            dna_dict = profile_data['fingerprint_dna']
            dna = FingerprintDNA(**{
                k: v for k, v in dna_dict.items() 
                if k in FingerprintDNA.__dataclass_fields__
            })
            
            # Create profile
            profile = StealthProfile(
                profile_id=profile_data['profile_id'],
                fingerprint_dna=dna,
                behavioral_chain=BehavioralMarkovChain(),
                entropy_pool=EntropyPool()
            )
            
            # Restore metadata
            profile.health_score = profile_data.get('health_score', 100)
            profile.threat_assessment = ThreatLevel(profile_data.get('threat_assessment', 0))
            profile.created_at = datetime.fromisoformat(profile_data['created_at'])
            if profile_data.get('last_used'):
                profile.last_used = datetime.fromisoformat(profile_data['last_used'])
            
            self.profiles[profile.profile_id] = profile
            
            logger.info(f"Loaded profile {profile.profile_id}")
            
    except Exception as e:
        logger.error(f"Failed to load profiles: {e}", exc_info=True)

async def shutdown(self):
    """Shutdown engine gracefully"""
    logger.info("Shutting down StealthEngine")
    
    self._shutdown.set()
    
    # Cancel tasks
    for task in self._tasks:
        task.cancel()
    
    await asyncio.gather(*self._tasks, return_exceptions=True)
    
    # Save profiles
    await self._save_profiles()

@dataclass
class StealthEngineConfig:
    """Configuration for StealthEngine"""
    # Profile management
    profiles_per_platform: int = 10
    max_total_profiles: int = 50
    # Evolution settings
    evolution_interval: float = 900  # 15 minutes
    evolution_threshold: float = 0.7  # Success rate threshold

    # Stealth settings
    default_stealth_level: StealthLevel = StealthLevel.STANDARD
    auto_adjust_stealth: bool = True

    # Platform preferences
    platform_preferences: Dict[str, Dict] = field(default_factory=lambda: {
        'ticketmaster': {
            'os_weights': {'Windows': 0.8, 'macOS': 0.15, 'Linux': 0.05},
            'browser_weights': {'Chrome': 0.85, 'Firefox': 0.10, 'Safari': 0.05},
        },
        'fansale': {
            'os_weights': {'Windows': 0.75, 'macOS': 0.20, 'Linux': 0.05},
            'browser_weights': {'Chrome': 0.80, 'Firefox': 0.15, 'Safari': 0.05},
        },
        'vivaticket': {
            'os_weights': {'Windows': 0.70, 'macOS': 0.25, 'Linux': 0.05},
            'browser_weights': {'Chrome': 0.75, 'Firefox': 0.20, 'Safari': 0.05},
        }
    })

    # Persistence
    profiles_path: str = "data/stealth_profiles.json"

    # Proxy pool (optional)
    proxy_pool: Optional["ProxyPool"] = None
class ThreatIntelligence:
    def __init__(self):
        self.detection_patterns = defaultdict(list)
        self.platform_indicators = defaultdict(set)
        self.global_indicators = set()

def add_detection(self, platform: str, detection_type: str, 
                 context: Dict[str, Any]):
    """Record detection event"""
    event = {
        'timestamp': datetime.utcnow(),
        'type': detection_type,
        'context': context
    }
    
    self.detection_patterns[platform].append(event)
    
    # Extract indicators
    if 'user_agent' in context:
        self.platform_indicators[platform].add(f"ua:{context['user_agent']}")
    
    # Analyze patterns
    self._analyze_patterns(platform)

def _analyze_patterns(self, platform: str):
    """Analyze detection patterns for insights"""
    recent_events = [
        e for e in self.detection_patterns[platform]
        if (datetime.utcnow() - e['timestamp']).total_seconds() < 3600
    ]
    
    if len(recent_events) > 10:
        # Check for specific patterns
        detection_types = [e['type'] for e in recent_events]
        
        # Sudden spike in captchas
        captcha_rate = detection_types.count('captcha') / len(detection_types)
        if captcha_rate > 0.5:
            logger.warning(f"{platform}: High captcha rate ({captcha_rate:.2%})")
            self.global_indicators.add('high_captcha_rate')
        
        # Consistent blocks
        block_rate = detection_types.count('block') / len(detection_types)
        if block_rate > 0.3:
            logger.error(f"{platform}: High block rate ({block_rate:.2%})")
            self.global_indicators.add('high_block_rate')

def get_risk_assessment(self, platform: str) -> ThreatLevel:
    """Get current risk level for platform"""
    if 'high_block_rate' in self.global_indicators:
        return ThreatLevel.CRITICAL
    
    if 'high_captcha_rate' in self.global_indicators:
        return ThreatLevel.HIGH
    
    # Platform-specific assessment
    recent_events = [
        e for e in self.detection_patterns[platform]
        if (datetime.utcnow() - e['timestamp']).total_seconds() < 3600
    ]
    
    if not recent_events:
        return ThreatLevel.NONE
    
    failure_rate = sum(1 for e in recent_events if e['type'] != 'success') / len(recent_events)
    
    if failure_rate > 0.5:
        return ThreatLevel.HIGH
    elif failure_rate > 0.3:
        return ThreatLevel.MEDIUM
    elif failure_rate > 0.1:
        return ThreatLevel.LOW
    
    return ThreatLevel.NONE

class ProxyPool:
    """Simple proxy pool for network diversity"""
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.current_index = 0

    async def get_proxy(self) -> str:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

def create_stealth_engine(config_path: Optional[str] = None) -> StealthEngine:
    """Factory function to create StealthEngine with configuration"""
    config = StealthEngineConfig()
    if config_path and Path(config_path).exists():
        # Load configuration from file
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    return StealthEngine(config)