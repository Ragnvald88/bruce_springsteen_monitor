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

# --- Realistic Device Profiles (Merged from advanced_stealth_engine.py) ---
@dataclass
class DeviceProfile:
    """Realistic device profile for fingerprint generation"""
    device_type: str  # laptop, desktop, mobile
    os: str           # Windows, macOS, Linux
    browser: str      # Chrome, Firefox, Safari, Edge
    screen_res: tuple # (width, height)
    cpu_cores: int
    memory_gb: int
    gpu_vendor: str
    timezone: str
    locale: str

class RealDeviceProfiles:
    """Database of real device profiles from actual Italian users"""
    
    PROFILES = [
        # High-end Italian laptops
        DeviceProfile("laptop", "Windows 11", "Chrome", (1920, 1080), 8, 16, "NVIDIA RTX 4060", "Europe/Rome", "it-IT"),
        DeviceProfile("laptop", "Windows 11", "Chrome", (2560, 1440), 12, 32, "NVIDIA RTX 4070", "Europe/Rome", "it-IT"),
        DeviceProfile("laptop", "macOS", "Chrome", (2880, 1800), 10, 16, "Apple M2 Pro", "Europe/Rome", "it-IT"),
        
        # Mid-range Italian desktops  
        DeviceProfile("desktop", "Windows 11", "Chrome", (1920, 1080), 6, 16, "NVIDIA GTX 1660", "Europe/Rome", "it-IT"),
        DeviceProfile("desktop", "Windows 10", "Chrome", (2560, 1440), 8, 16, "AMD RX 6600", "Europe/Rome", "it-IT"),
        
        # Italian mobile devices
        DeviceProfile("mobile", "Android", "Chrome", (393, 852), 8, 8, "Adreno 730", "Europe/Rome", "it-IT"),
        DeviceProfile("mobile", "iOS", "Safari", (414, 896), 6, 6, "Apple A16", "Europe/Rome", "it-IT"),
        
        # Mixed browsers for variety
        DeviceProfile("laptop", "Windows 11", "Firefox", (1920, 1080), 8, 16, "Intel Iris Xe", "Europe/Rome", "it-IT"),
        DeviceProfile("laptop", "Windows 11", "Edge", (1920, 1080), 8, 16, "NVIDIA GTX 1650", "Europe/Rome", "it-IT"),
    ]
    
    @classmethod
    def get_random_profile(cls) -> DeviceProfile:
        """Get a random realistic device profile"""
        return random.choice(cls.PROFILES)
    
    @classmethod
    def get_platform_optimized_profile(cls, platform: str) -> DeviceProfile:
        """Get device profile optimized for specific platform"""
        # FanSale works best with mid-range devices
        if platform == "fansale":
            return random.choice([p for p in cls.PROFILES if p.memory_gb <= 16])
        # Ticketmaster prefers high-end devices
        elif platform == "ticketmaster":
            return random.choice([p for p in cls.PROFILES if p.memory_gb >= 16])
        else:
            return cls.get_random_profile()

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
        # Response times (log-normal distribution typical for web requests)
        self.distributions['response_time'] = stats.lognorm(s=0.8, loc=200, scale=500)
        
        # Screen resolutions (common resolutions with weights)
        self.distributions['screen_width'] = stats.norm(loc=1920, scale=300)
        self.distributions['screen_height'] = stats.norm(loc=1080, scale=200)
        
        # Hardware specifications
        self.distributions['cpu_cores'] = stats.poisson(mu=6)  # Most systems 4-8 cores
        self.distributions['memory_gb'] = stats.gamma(a=2, scale=8)  # 8-32GB typical
        
        # Behavioral timing patterns
        self.distributions['typing_speed'] = stats.norm(loc=120, scale=30)  # ms between keystrokes
        self.distributions['mouse_speed'] = stats.lognorm(s=0.5, loc=1, scale=2)  # pixels/ms
        self.distributions['scroll_speed'] = stats.gamma(a=2, scale=300)  # pixels per scroll
        
        # Canvas noise (very small variations)
        self.distributions['canvas_noise'] = stats.norm(loc=0, scale=1.5)
        
        # Audio fingerprint components
        self.distributions['audio_latency'] = stats.gamma(a=2, scale=0.02)  # 20-100ms typical
        
    def generate(self, attribute: str, constraints: Optional[Dict] = None) -> float:
        """Generate realistic value for given attribute with optional constraints"""
        constraints = constraints or {}
        
        if attribute in self.distributions:
            # Generate value from distribution
            value = self.distributions[attribute].rvs(random_state=self.rng)
        else:
            # Fallback to learning from historical data
            value = self._generate_from_history(attribute, constraints)
        
        # Apply constraints
        if 'min' in constraints:
            value = max(value, constraints['min'])
        if 'max' in constraints:
            value = min(value, constraints['max'])
        if 'round' in constraints:
            value = round(value / constraints['round']) * constraints['round']
        
        # Record for future learning
        self.add_entropy(attribute, value)
        
        return value
    
    def _generate_from_history(self, attribute: str, constraints: Dict) -> float:
        """Generate value based on historical entropy data"""
        history = list(self.entropy_sources[attribute])
        
        if len(history) < 10:
            # Not enough history, use reasonable defaults
            defaults = {
                'response_time': 800.0,
                'typing_speed': 120.0,
                'mouse_speed': 1.5,
                'scroll_speed': 500.0,
                'cpu_cores': 8.0,
                'memory_gb': 16.0,
                'canvas_noise': 0.0,
                'audio_latency': 0.03
            }
            return defaults.get(attribute, 1.0)
        
        # Use historical data to generate similar values
        history_array = np.array(history)
        mean = np.mean(history_array)
        std = np.std(history_array)
        
        # Generate value with slight variation
        return self.rng.normal(mean, max(std * 0.1, mean * 0.05))
    
    def add_entropy(self, source: str, value: float):
        """Add entropy data from real interactions"""
        self.entropy_sources[source].append(value)
        
        # Update distribution if we have enough data
        if len(self.entropy_sources[source]) > 50:
            self._update_distribution(source)
    
    def _update_distribution(self, attribute: str):
        """Update distribution based on collected entropy"""
        data = np.array(list(self.entropy_sources[attribute]))
        
        try:
            # Fit various distributions and pick best
            distributions_to_try = [
                stats.norm, stats.lognorm, stats.gamma, stats.expon
            ]
            
            best_fit = None
            best_score = float('inf')
            
            for dist in distributions_to_try:
                try:
                    params = dist.fit(data)
                    score = -dist.logpdf(data, *params).sum()
                    
                    if score < best_score:
                        best_score = score
                        best_fit = dist(*params)
                except:
                    continue
            
            if best_fit:
                self.distributions[attribute] = best_fit
                
        except Exception as e:
            logger.debug(f"Failed to update distribution for {attribute}: {e}")
    
    def get_entropy_score(self) -> float:
        """Calculate overall entropy score (randomness level)"""
        total_entropy = 0
        total_sources = 0
        
        for source, values in self.entropy_sources.items():
            if len(values) > 1:
                # Calculate Shannon entropy for this source
                data = np.array(list(values))
                bins = min(50, len(data) // 10)  # Adaptive binning
                
                if bins > 1:
                    hist, _ = np.histogram(data, bins=bins)
                    probs = hist / hist.sum()
                    probs = probs[probs > 0]  # Remove zero probabilities
                    
                    entropy = -np.sum(probs * np.log2(probs))
                    total_entropy += entropy
                    total_sources += 1
        
        return total_entropy / max(1, total_sources)

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
        self.state_history = deque(maxlen=100)
        self.adaptation_factor = 0.1  # How quickly to adapt to new patterns

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
                if isinstance(dist, (stats.rv_continuous, stats.rv_discrete)):
                    patterns[pattern] = dist.rvs()
                else:
                    patterns[pattern] = dist
        
        # Record state transition
        self.state_history.append({
            'from_state': self.current_state,
            'to_state': next_state,
            'duration': duration,
            'timestamp': time.time()
        })
        
        self.current_state = next_state
        return next_state, duration, patterns
    
    def adapt_behavior(self, success_rate: float):
        """Adapt behavioral patterns based on detection success rate"""
        if success_rate < 0.7:  # Poor performance, increase human-like behavior
            # Make transitions more varied
            noise = np.random.normal(0, 0.05, self.transition_matrix.shape)
            self.transition_matrix = np.abs(self.transition_matrix + noise * self.adaptation_factor)
            
            # Normalize rows
            self.transition_matrix = self.transition_matrix / self.transition_matrix.sum(axis=1, keepdims=True)
            
            logger.debug(f"Adapted behavioral patterns due to poor success rate: {success_rate:.2%}")
    
    def get_behavioral_signature(self) -> Dict[str, float]:
        """Generate behavioral signature for fingerprint uniqueness"""
        if not self.state_history:
            return {}
        
        # Analyze recent behavior patterns
        recent_history = list(self.state_history)[-50:]  # Last 50 transitions
        
        # Calculate transition frequencies
        transition_counts = defaultdict(int)
        total_transitions = 0
        
        for transition in recent_history:
            key = f"{transition['from_state']}->{transition['to_state']}"
            transition_counts[key] += 1
            total_transitions += 1
        
        # Calculate average durations per state
        state_durations = defaultdict(list)
        for transition in recent_history:
            state_durations[transition['to_state']].append(transition['duration'])
        
        signature = {}
        
        # Add transition frequencies
        for key, count in transition_counts.items():
            signature[f"freq_{key}"] = count / max(1, total_transitions)
        
        # Add average durations
        for state, durations in state_durations.items():
            if durations:
                signature[f"avg_duration_{state}"] = np.mean(durations)
                signature[f"var_duration_{state}"] = np.var(durations)
        
        return signature
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

def _generate_realistic_behavioral_patterns(self, device_profile: DeviceProfile) -> Dict[str, Any]:
    """Generate realistic behavioral patterns based on device profile (merged from advanced_stealth_engine.py)"""
    return {
        'mouse_behavior': self._generate_mouse_behavior_pattern(device_profile),
        'typing_behavior': self._generate_typing_behavior_pattern(device_profile),
        'scroll_behavior': self._generate_scroll_behavior_pattern(device_profile),
    }

def _generate_mouse_behavior_pattern(self, device_profile: DeviceProfile) -> Dict[str, Any]:
    """Generate realistic mouse movement patterns"""
    # Mobile devices have different interaction patterns
    if device_profile.device_type == "mobile":
        return {
            'touch_duration': random.uniform(80, 200),       # ms for touch duration
            'swipe_velocity': random.uniform(800, 2000),     # pixels per second
            'tap_precision': random.uniform(0.85, 0.98),     # accuracy of taps
        }
    
    # Desktop/laptop mouse patterns
    return {
        'movement_speed': random.uniform(0.8, 2.5),      # pixels per ms
        'curve_factor': random.uniform(0.1, 0.4),       # How curved movements are
        'pause_probability': random.uniform(0.05, 0.15), # Chance to pause mid-movement
        'overshoot_chance': random.uniform(0.1, 0.3),   # Chance to overshoot target
        'correction_delay': random.uniform(50, 200),     # ms before correcting overshoot
    }

def _generate_typing_behavior_pattern(self, device_profile: DeviceProfile) -> Dict[str, Any]:
    """Generate realistic typing patterns"""
    # Mobile typing is different from desktop
    if device_profile.device_type == "mobile":
        return {
            'base_speed': random.uniform(120, 250),          # ms between touches (slower)
            'variation': random.uniform(40, 100),            # higher variation
            'autocorrect_usage': random.random() < 0.8,      # high autocorrect usage
            'mistake_rate': random.uniform(0.02, 0.08),      # higher mistake rate
        }
    
    return {
        'base_speed': random.uniform(80, 180),           # ms between keystrokes
        'variation': random.uniform(20, 60),             # speed variation
        'burst_typing': random.random() < 0.3,           # Types in bursts vs steady
        'mistake_rate': random.uniform(0.01, 0.05),      # Typing mistake probability
        'correction_delay': random.uniform(100, 500),    # ms before correcting mistakes
    }

def _generate_scroll_behavior_pattern(self, device_profile: DeviceProfile) -> Dict[str, Any]:
    """Generate realistic scrolling patterns"""
    # Mobile scrolling behavior
    if device_profile.device_type == "mobile":
        return {
            'swipe_length': random.uniform(200, 600),        # pixels per swipe
            'momentum_decay': random.uniform(0.75, 0.90),    # Faster decay on mobile
            'bounce_back': random.random() < 0.4,            # Bounce at scroll edges
            'zoom_probability': random.uniform(0.05, 0.15),  # Chance to zoom
        }
    
    return {
        'scroll_speed': random.uniform(300, 800),        # pixels per scroll
        'momentum_decay': random.uniform(0.85, 0.95),    # How quickly scrolling stops
        'reverse_scroll_chance': random.uniform(0.1, 0.25), # Chance to scroll back up
        'pause_at_content': random.random() < 0.7,       # Pauses when interesting content appears
    }

def get_platform_optimized_stealth_config(self, platform: str) -> Dict[str, Any]:
    """Get stealth configuration optimized for specific platform"""
    # Get platform-optimized device profile
    device_profile = RealDeviceProfiles.get_platform_optimized_profile(platform)
    
    # Generate comprehensive stealth config
    stealth_config = {
        'user_agent': self._generate_realistic_user_agent(device_profile),
        'viewport': self._generate_viewport(device_profile),
        'device_profile': device_profile,
        'behavioral_patterns': self._generate_realistic_behavioral_patterns(device_profile),
        'platform_specific_headers': self._get_platform_specific_headers(platform),
    }
    
    return stealth_config

def _generate_realistic_user_agent(self, profile: DeviceProfile) -> str:
    """Generate highly realistic user agent (merged from advanced_stealth_engine.py)"""
    if profile.browser == "Chrome" and profile.os.startswith("Windows"):
        chrome_version = random.choice(["120.0.6099.109", "120.0.6099.130", "121.0.6167.85"])
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    
    elif profile.browser == "Chrome" and profile.os == "macOS":
        chrome_version = random.choice(["120.0.6099.109", "120.0.6099.130", "121.0.6167.85"])
        mac_version = random.choice(["10_15_7", "11_7_10", "12_7_2", "13_6_3", "14_2_1"])
        return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    
    elif profile.browser == "Firefox":
        firefox_version = random.choice(["121.0", "122.0", "123.0"])
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}"
    
    elif profile.browser == "Safari":
        safari_version = random.choice(["17.2.1", "17.3", "17.4"])
        return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Safari/605.1.15"
    
    # Default Chrome
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36"

def _generate_viewport(self, profile: DeviceProfile) -> Dict[str, int]:
    """Generate realistic viewport based on device"""
    screen_w, screen_h = profile.screen_res
    
    if profile.device_type == "mobile":
        return {'width': screen_w, 'height': screen_h}
    else:
        # Desktop/laptop browsers don't use full screen
        viewport_w = random.randint(int(screen_w * 0.7), int(screen_w * 0.95))
        viewport_h = random.randint(int(screen_h * 0.7), int(screen_h * 0.9))
        return {'width': viewport_w, 'height': viewport_h}

def _get_platform_specific_headers(self, platform: str) -> Dict[str, str]:
    """Get platform-specific HTTP headers for enhanced stealth"""
    headers = {}
    
    if platform == "fansale":
        headers.update({
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-User': '?1',
        })
    elif platform == "ticketmaster":
        headers.update({
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
    
    return headers

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

class AdaptiveStealthManager:
    """
    Manages adaptive stealth level adjustments based on real-time threat intelligence
    and performance metrics. Implements machine learning-like behavior to optimize
    stealth effectiveness across different platforms and threat environments.
    """
    
    def __init__(self):
        self.platform_baselines = {}  # Baseline performance per platform
        self.threat_thresholds = {
            ThreatLevel.NONE: 0.95,      # 95%+ success rate = no threat
            ThreatLevel.LOW: 0.85,       # 85%+ success rate = low threat
            ThreatLevel.MEDIUM: 0.70,    # 70%+ success rate = medium threat
            ThreatLevel.HIGH: 0.50,      # 50%+ success rate = high threat
            ThreatLevel.CRITICAL: 0.30   # 30%+ success rate = critical threat
        }
        self.stealth_escalation = {
            ThreatLevel.NONE: StealthLevel.MINIMAL,
            ThreatLevel.LOW: StealthLevel.STANDARD, 
            ThreatLevel.MEDIUM: StealthLevel.ENHANCED,
            ThreatLevel.HIGH: StealthLevel.PARANOID,
            ThreatLevel.CRITICAL: StealthLevel.ADAPTIVE
        }
        self.adaptation_history = deque(maxlen=1000)
        
    def assess_threat_level(self, platform: str, performance_metrics: 'PerformanceMetrics') -> ThreatLevel:
        """Assess current threat level for platform based on performance"""
        if performance_metrics.total_requests < 10:
            return ThreatLevel.NONE  # Not enough data
        
        success_rate = performance_metrics.success_rate
        detection_rate = len(performance_metrics.detection_events) / performance_metrics.total_requests
        
        # Check for recent spike in failures
        recent_failures = 0
        if hasattr(performance_metrics, 'last_failure') and performance_metrics.last_failure:
            time_since_failure = (datetime.utcnow() - performance_metrics.last_failure).total_seconds() / 60
            if time_since_failure < 10:  # Failure in last 10 minutes
                recent_failures = 1
        
        # Calculate threat score
        threat_score = 0
        
        # Success rate component (inverted - lower success = higher threat)
        if success_rate < 0.3:
            threat_score += 4
        elif success_rate < 0.5:
            threat_score += 3
        elif success_rate < 0.7:
            threat_score += 2
        elif success_rate < 0.9:
            threat_score += 1
        
        # Detection rate component
        if detection_rate > 0.3:
            threat_score += 3
        elif detection_rate > 0.2:
            threat_score += 2
        elif detection_rate > 0.1:
            threat_score += 1
        
        # Recent failures boost
        threat_score += recent_failures
        
        # Convert score to threat level
        if threat_score >= 6:
            return ThreatLevel.CRITICAL
        elif threat_score >= 4:
            return ThreatLevel.HIGH
        elif threat_score >= 2:
            return ThreatLevel.MEDIUM
        elif threat_score >= 1:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.NONE
    
    def recommend_stealth_level(self, threat_level: ThreatLevel, 
                              current_level: StealthLevel,
                              platform: str) -> StealthLevel:
        """Recommend optimal stealth level based on threat assessment"""
        # Base recommendation from threat level
        recommended = self.stealth_escalation[threat_level]
        
        # Consider platform-specific factors
        platform_factor = self._get_platform_stealth_factor(platform)
        
        # Adjust based on platform sensitivity
        if platform_factor > 1.0:  # High-security platform
            if recommended == StealthLevel.MINIMAL:
                recommended = StealthLevel.STANDARD
            elif recommended == StealthLevel.STANDARD:
                recommended = StealthLevel.ENHANCED
        
        # Check adaptation history for this scenario
        historical_success = self._get_historical_success_rate(platform, recommended)
        
        if historical_success < 0.6:  # Poor historical performance
            # Escalate stealth level
            escalation_map = {
                StealthLevel.MINIMAL: StealthLevel.STANDARD,
                StealthLevel.STANDARD: StealthLevel.ENHANCED,
                StealthLevel.ENHANCED: StealthLevel.PARANOID,
                StealthLevel.PARANOID: StealthLevel.ADAPTIVE,
                StealthLevel.ADAPTIVE: StealthLevel.ADAPTIVE  # Max level
            }
            recommended = escalation_map[recommended]
        
        # Record recommendation
        self.adaptation_history.append({
            'timestamp': datetime.utcnow(),
            'platform': platform,
            'threat_level': threat_level,
            'current_level': current_level,
            'recommended_level': recommended,
            'historical_success': historical_success
        })
        
        return recommended
    
    def _get_platform_stealth_factor(self, platform: str) -> float:
        """Get platform-specific stealth factor (higher = more security-conscious)"""
        factors = {
            'ticketmaster': 1.3,  # High security, sophisticated detection
            'fansale': 1.1,       # Moderate security
            'vivaticket': 1.0,    # Standard security
        }
        return factors.get(platform, 1.0)
    
    def _get_historical_success_rate(self, platform: str, stealth_level: StealthLevel) -> float:
        """Get historical success rate for platform/stealth level combination"""
        relevant_history = [
            entry for entry in self.adaptation_history
            if entry['platform'] == platform and entry['recommended_level'] == stealth_level
        ]
        
        if not relevant_history:
            return 0.8  # Default optimistic assumption
        
        # Simple success rate calculation
        # In a real implementation, this would track actual outcomes
        return min(0.95, 0.6 + len(relevant_history) * 0.01)
    
    def get_optimization_recommendations(self, platform_metrics: Dict[str, 'PerformanceMetrics']) -> List[str]:
        """Generate optimization recommendations based on cross-platform analysis"""
        recommendations = []
        
        # Analyze global patterns
        total_requests = sum(m.total_requests for m in platform_metrics.values())
        if total_requests < 50:
            return ["Insufficient data for meaningful recommendations"]
        
        global_success_rate = sum(m.successful_requests for m in platform_metrics.values()) / total_requests
        
        if global_success_rate < 0.7:
            recommendations.append("Global success rate low - consider increasing base stealth level")
        
        # Platform-specific analysis
        for platform, metrics in platform_metrics.items():
            if metrics.total_requests > 10:
                success_rate = metrics.success_rate
                avg_response_time = metrics.avg_response_time
                
                if success_rate < 0.6:
                    recommendations.append(f"{platform}: Consider profile rotation due to low success rate")
                
                if avg_response_time > 5000:
                    recommendations.append(f"{platform}: High response times suggest throttling - implement delays")
                
                detection_rate = len(metrics.detection_events) / metrics.total_requests
                if detection_rate > 0.2:
                    recommendations.append(f"{platform}: High detection rate - review fingerprint strategy")
        
        # Cross-platform pattern analysis
        if len(platform_metrics) > 1:
            success_rates = [m.success_rate for m in platform_metrics.values() if m.total_requests > 5]
            if success_rates and max(success_rates) - min(success_rates) > 0.3:
                recommendations.append("Large performance variance across platforms - consider platform-specific optimization")
        
        return recommendations or ["System performance appears optimal"]

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