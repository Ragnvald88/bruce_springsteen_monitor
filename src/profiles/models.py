# src/core/profiles/models.py
"""Core profile models."""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import uuid

from cryptography.fernet import Fernet
from playwright.async_api import BrowserContext

from .enums import ProfileQuality, DataOptimizationLevel, Platform
from .types import SessionData, ProfileMetrics
from .enums import Platform, ProfileQuality # Assuming these are correctly defined

@dataclass
class ProxyConfig:
    """Enhanced proxy configuration with rotation support."""
    proxy_type: str = "http"
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    rotation_endpoint: Optional[str] = None
    sticky_session: bool = True
    country_code: Optional[str] = None
    proxy_provider: Optional[str] = None  # brightdata, oxylabs, etc.
    
    def get_proxy_url(self, session_id: Optional[str] = None) -> Optional[str]:
        """Get formatted proxy URL with session support."""
        if not self.host or not self.port:
            return None
            
        auth = ""
        if self.username and self.password:
            username_parts = [self.username]
            if session_id and self.sticky_session:
                username_parts.append(f"session-{session_id}")
            if self.country_code:
                username_parts.append(f"country-{self.country_code}")
            
            final_username = "-".join(username_parts)
            auth = f"{final_username}:{self.password}@"
            
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"
    
    def rotate_session(self) -> str:
        """Generate new session ID for proxy rotation."""
        return str(uuid.uuid4())[:8]


@dataclass
class BrowserProfile:
    """Enhanced browser profile with anti-detection features."""
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
    
    # Enhanced fingerprinting
    webgl_vendor: Optional[str] = None
    webgl_renderer: Optional[str] = None
    canvas_fingerprint: Optional[str] = None
    audio_fingerprint: Optional[str] = None
    webrtc_ips: List[str] = field(default_factory=list)
    fonts_list: List[str] = field(default_factory=list)
    
    # Client Hints
    sec_ch_ua: Optional[str] = None
    sec_ch_ua_mobile: Optional[str] = "?0"
    sec_ch_ua_platform: Optional[str] = None
    sec_ch_ua_platform_version: Optional[str] = None
    sec_ch_ua_full_version_list: Optional[str] = None
    
    # CDP Stealth properties
    cdp_stealth_enabled: bool = True
    override_navigator_webdriver: bool = True
    mask_automation_indicators: bool = True
    
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
    fingerprint_hash: Optional[str] = None
    
    # Platform-specific data
    platform_sessions: Dict[str, SessionData] = field(default_factory=dict)
    platform_stats: Dict[str, ProfileMetrics] = field(default_factory=lambda: {})
    
    # Optimization settings
    data_optimization_level: DataOptimizationLevel = DataOptimizationLevel.BALANCED
    block_resources: Set[str] = field(default_factory=lambda: set())
    
    # Persistent context
    persistent_context_dir: Optional[Path] = None
    _context_encryption_key: Optional[bytes] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Initialize computed fields and generate fingerprint hash."""
        if self.avail_width is None:
            self.avail_width = self.screen_width
        if self.avail_height is None:
            self.avail_height = self.screen_height - 40
        
        if self._context_encryption_key is None:
            self._context_encryption_key = Fernet.generate_key()
        
        if not self.accept_language:
            self.accept_language = "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
        
        if self.persistent_context_dir is None:
            self.persistent_context_dir = Path(f"browser_contexts/{self.profile_id}")
        
        # Generate fingerprint hash
        self._generate_fingerprint_hash()
        
        # Initialize platform stats with proper structure
        for platform in Platform:
            if platform.value not in self.platform_stats:
                self.platform_stats[platform.value] = {
                    'attempts': 0,
                    'successes': 0,
                    'failures': 0,
                    'last_success': None,
                    'last_failure': None,
                    'avg_response_time_ms': 0.0,
                    'detection_events': [],
                    'captcha_solve_rate': 0.0,
                    'consecutive_successes': 0
                }
    
    def _generate_fingerprint_hash(self):
        """Generate unique fingerprint hash."""
        fingerprint_data = {
            'user_agent': self.user_agent,
            'screen': f"{self.screen_width}x{self.screen_height}",
            'viewport': f"{self.viewport_width}x{self.viewport_height}",
            'webgl': f"{self.webgl_vendor}:{self.webgl_renderer}",
            'canvas': self.canvas_fingerprint,
            'timezone': self.timezone,
            'languages': self.languages_override
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        self.fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
    
    def get_context_params(self) -> Dict[str, Any]:
        """Get enhanced parameters for Playwright browser context."""
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
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
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
        
        # Enhanced security headers
        if self.sec_ch_ua:
            headers['sec-ch-ua'] = self.sec_ch_ua
        if self.sec_ch_ua_mobile:
            headers['sec-ch-ua-mobile'] = self.sec_ch_ua_mobile
        if self.sec_ch_ua_platform:
            headers['sec-ch-ua-platform'] = self.sec_ch_ua_platform
            
        # Platform-specific headers
        platform_headers = self._get_platform_specific_headers()
        headers.update(platform_headers)
        
        params['extra_http_headers'] = headers
        
        # Permissions
        params['permissions'] = ['geolocation']
        params['geolocation'] = {'latitude': 41.9028, 'longitude': 12.4964}  # Rome
        
        # Storage state for session persistence
        if self.persistent_context_dir:
            params['storage_state'] = str(self.persistent_context_dir / 'state.json')
        
        return params
    
    def get_launch_options(self) -> Dict[str, Any]:
        """Get browser launch options with maximum stealth."""
        args = [
            # Core stealth arguments
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process,TranslateUI',
            '--enable-features=NetworkService,NetworkServiceInProcess',
            
            # Disable automation indicators
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-ipc-flooding-protection',
            
            # Additional stealth
            '--disable-features=UserAgentClientHint',
            '--disable-features=CalculateNativeWinOcclusion',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-features=ScriptStreaming',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',
            '--disable-sync',
            '--disable-domain-reliability',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-features=IsolateOrigins',
            '--disable-features=site-per-process',
            
            # Memory and performance
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-logging',
            '--disable-permissions-api',
            '--disable-notifications',
            
            # Window properties
            f'--window-size={self.viewport_width},{self.viewport_height}',
            '--window-position=0,0',
            '--force-color-profile=srgb',
            
            # WebRTC
            '--disable-webrtc-hw-encoding',
            '--disable-webrtc-hw-decoding',
            '--disable-webrtc-encryption',
        ]
        
        # Add optimization flags
        if self.data_optimization_level in [DataOptimizationLevel.BALANCED, DataOptimizationLevel.AGGRESSIVE]:
            args.extend([
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-features=CalculateNativeWinOcclusion',
                '--disable-backgrounding-occluded-windows',
            ])
        
        args.extend(self.browser_args)
        
        return {
            'args': args,
            'chromium_sandbox': False,
            'handle_sigint': False,
            'handle_sigterm': False,
            'handle_sighup': False,
        }
    
    def _get_platform_specific_headers(self) -> Dict[str, str]:
        """Get platform-specific headers for better stealth."""
        headers = {}
        
        # Add referer for platforms that check it
        if any(session.get('platform') == 'ticketmaster' for session in self.platform_sessions.values()):
            headers['Referer'] = 'https://shop.ticketmaster.it/'
        
        return headers
    
    def get_resource_block_patterns(self) -> List[str]:
        """Get resource blocking patterns based on optimization level."""
        patterns = list(self.block_resources)
        
        if self.data_optimization_level == DataOptimizationLevel.AGGRESSIVE:
            patterns.extend([
                '*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.svg',
                '*.mp4', '*.avi', '*.mov', '*.webm',
                '*.woff', '*.woff2', '*.ttf', '*.otf',
                '*analytics*', '*tracking*', '*doubleclick*', '*facebook*',
                '*google-analytics*', '*hotjar*', '*clarity*', '*segment*',
                '*adsystem*', '*amazon-adsystem*', '*googlesyndication*',
                '*googletagmanager*', '*google-analytics*', '*googleadservices*',
                '*doubleclick*', '*facebook*', '*twitter*', '*linkedin*',
            ])
        elif self.data_optimization_level == DataOptimizationLevel.BALANCED:
            patterns.extend([
                '*.mp4', '*.avi', '*.mov',
                '*analytics*', '*tracking*', '*doubleclick*',
                '*googletagmanager*', '*google-analytics*',
            ])
        elif self.data_optimization_level == DataOptimizationLevel.MINIMAL:
            patterns.extend(['*analytics*', '*tracking*'])
            
        return patterns
    
    def should_rotate_proxy(self) -> bool:
        """Check if proxy should be rotated."""
        if not self.proxy_config or not self.last_used:
            return False
        
        # Time-based rotation
        time_based = (datetime.utcnow() - self.last_used).total_seconds() > 1800
        
        # Performance-based rotation
        total_attempts = sum(stats.get('attempts', 0) for stats in self.platform_stats.values())
        total_failures = sum(stats.get('failures', 0) for stats in self.platform_stats.values())
        failure_based = total_attempts > 10 and (total_failures / total_attempts) > 0.3
        
        # Detection-based rotation
        recent_detections = sum(
            len([e for e in stats.get('detection_events', []) 
                 if (datetime.utcnow() - datetime.fromisoformat(e['timestamp'])).total_seconds() < 3600])
            for stats in self.platform_stats.values()
        )
        detection_based = recent_detections > 2
        
        return time_based or failure_based or detection_based
    
    def rotate_proxy(self):
        """Rotate proxy session."""
        if self.proxy_config:
            self.proxy_session_id = self.proxy_config.rotate_session()
    
    def record_usage(self, success: bool, response_time_ms: float = 0,
                    platform: str = "", error: Optional[str] = None,
                    detected: bool = False, captcha_encountered: bool = False):
        """Record usage statistics with enhanced tracking."""
        self.last_used = datetime.utcnow()
        
        if platform and platform in self.platform_stats:
            stats = self.platform_stats[platform]
            stats['attempts'] += 1
            
            if success:
                stats['successes'] += 1
                stats['consecutive_successes'] += 1
                stats['last_success'] = datetime.utcnow().isoformat()
            else:
                stats['failures'] += 1
                stats['consecutive_successes'] = 0
                stats['last_failure'] = datetime.utcnow().isoformat()
                if error:
                    stats['last_error'] = error
            
            # Update average response time
            if response_time_ms > 0:
                current_avg = stats['avg_response_time_ms']
                total_attempts = stats['attempts']
                stats['avg_response_time_ms'] = (
                    (current_avg * (total_attempts - 1)) + response_time_ms
                ) / total_attempts
            
            # Track detection events
            if detected:
                stats['detection_events'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': error,
                    'type': 'hard_block' if error else 'suspicious'
                })
            
            # Update CAPTCHA solve rate
            if captcha_encountered:
                total_captchas = stats.get('total_captchas', 0) + 1
                solved_captchas = stats.get('solved_captchas', 0) + (1 if success else 0)
                stats['total_captchas'] = total_captchas
                stats['solved_captchas'] = solved_captchas
                stats['captcha_solve_rate'] = solved_captchas / total_captchas
    
    def get_success_rate(self, platform: Optional[str] = None) -> float:
        """Calculate success rate for platform or overall."""
        if platform:
            stats = self.platform_stats.get(platform, {})
            attempts = stats.get('attempts', 0)
            successes = stats.get('successes', 0)
        else:
            attempts = sum(s.get('attempts', 0) for s in self.platform_stats.values())
            successes = sum(s.get('successes', 0) for s in self.platform_stats.values())
        
        return successes / attempts if attempts > 0 else 0.0