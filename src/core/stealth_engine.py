# src/core/stealth_engine.py
"""
StealthMaster AI - Ultimate Stealth Engine v10.0
Advanced anti-detection system with ML optimization and real-time adaptation
Copyright (c) 2025 - Production Ready
"""

import asyncio
import hashlib
import json
import logging
import math
import random
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
from enum import Enum
import base64
import struct

import numpy as np
from playwright.async_api import Page, BrowserContext, Route, Request, Response
import httpx

# Advanced imports for ML and fingerprinting
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

try:
    import tls_client
    HAS_TLS_CLIENT = True
except ImportError:
    HAS_TLS_CLIENT = False

logger = logging.getLogger(__name__)


# ============== Data Classes ==============

@dataclass
class DeviceProfile:
    """Complete device profile for fingerprint generation"""
    device_type: str  # laptop, desktop, mobile, tablet
    os: str          # Windows 11, macOS, Linux, Android, iOS
    os_version: str  # Specific version
    browser: str     # Chrome, Firefox, Safari, Edge
    browser_version: str
    screen_res: Tuple[int, int]
    viewport_size: Tuple[int, int]
    cpu_cores: int
    memory_gb: int
    gpu_vendor: str
    gpu_model: str
    timezone: str
    locale: str
    languages: List[str]
    
    # Advanced fingerprinting
    battery_level: Optional[float] = None
    charging: Optional[bool] = None
    
    # Network characteristics
    connection_type: str = "wifi"  # wifi, ethernet, cellular
    effective_type: str = "4g"     # slow-2g, 2g, 3g, 4g
    downlink: float = 10.0         # Mbps
    rtt: int = 50                  # Round trip time in ms
    
    # Behavioral characteristics
    typing_speed_wpm: float = field(default_factory=lambda: random.uniform(40, 80))
    mouse_precision: float = field(default_factory=lambda: random.uniform(0.7, 0.95))
    scroll_behavior: str = field(default_factory=lambda: random.choice(['smooth', 'stepped', 'momentum']))
    
    # Platform-specific
    platform_hints: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Auto-calculate viewport from screen if not set
        if not self.viewport_size:
            # Account for browser chrome and OS elements
            width_reduction = random.randint(0, 100) if self.device_type == "desktop" else 0
            height_reduction = random.randint(100, 200) if self.device_type in ["desktop", "laptop"] else 50
            self.viewport_size = (
                self.screen_res[0] - width_reduction,
                self.screen_res[1] - height_reduction
            )


@dataclass
class SensorData:
    """Comprehensive sensor data for anti-bot evasion"""
    # Motion sensors
    accelerometer: List[float] = field(default_factory=lambda: [0.1, -0.2, 9.81])
    gyroscope: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    magnetometer: List[float] = field(default_factory=lambda: [45.0, 0.0, 60.0])
    
    # Orientation
    alpha: float = 0.0  # Z-axis rotation
    beta: float = 0.0   # X-axis rotation
    gamma: float = 0.0  # Y-axis rotation
    
    # Light/Proximity
    ambient_light: float = field(default_factory=lambda: random.uniform(50, 500))
    proximity: float = field(default_factory=lambda: random.choice([0, 5, 100]))
    
    # Touch/Pointer events
    touch_points: List[Dict[str, Any]] = field(default_factory=list)
    pointer_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    frame_rate: float = 60.0
    memory_pressure: float = field(default_factory=lambda: random.uniform(0.1, 0.3))
    
    # Advanced timing
    performance_entries: Dict[str, int] = field(default_factory=dict)
    
    def generate_realistic_motion(self, device_type: str) -> None:
        """Generate realistic motion data based on device type"""
        if device_type == "mobile":
            # Simulate hand-held device micro-movements
            self.accelerometer = [
                random.gauss(0.1, 0.05),
                random.gauss(-0.15, 0.05),
                random.gauss(9.81, 0.1)
            ]
            self.gyroscope = [
                random.gauss(0, 0.01),
                random.gauss(0, 0.01),
                random.gauss(0, 0.01)
            ]
        elif device_type == "tablet":
            # Less movement than phone
            self.accelerometer = [
                random.gauss(0.05, 0.02),
                random.gauss(-0.1, 0.02),
                random.gauss(9.81, 0.05)
            ]
        else:
            # Desktop/laptop - minimal movement
            self.accelerometer = [0.0, 0.0, 9.81]
            self.gyroscope = [0.0, 0.0, 0.0]


@dataclass
class TLSFingerprint:
    """Advanced TLS fingerprint configuration"""
    ja3_string: str
    ja3_hash: str
    ja3s_string: Optional[str] = None
    ja3s_hash: Optional[str] = None
    
    # TLS Extensions in order
    extensions: List[int] = field(default_factory=list)
    
    # Cipher suites
    cipher_suites: List[int] = field(default_factory=list)
    
    # ALPN protocols
    alpn_protocols: List[str] = field(default_factory=lambda: ['h2', 'http/1.1'])
    
    # HTTP/2 Settings
    h2_settings: Dict[str, int] = field(default_factory=lambda: {
        'SETTINGS_HEADER_TABLE_SIZE': 65536,
        'SETTINGS_ENABLE_PUSH': 0,
        'SETTINGS_MAX_CONCURRENT_STREAMS': 1000,
        'SETTINGS_INITIAL_WINDOW_SIZE': 6291456,
        'SETTINGS_MAX_HEADER_LIST_SIZE': 262144
    })
    
    # HTTP/2 Window Update
    h2_window_update: int = 15663105
    
    # HTTP/2 Priority
    h2_priority: Dict[str, Any] = field(default_factory=lambda: {
        'stream_id': 3,
        'exclusive': 1, 
        'parent_stream_id': 0,
        'weight': 201
    })
    
    # Header order
    pseudo_header_order: List[str] = field(default_factory=lambda: [
        ':method', ':authority', ':scheme', ':path'
    ])
    
    header_order: List[str] = field(default_factory=lambda: [
        'cache-control', 'sec-ch-ua', 'sec-ch-ua-mobile', 
        'sec-ch-ua-platform', 'upgrade-insecure-requests', 
        'user-agent', 'accept', 'sec-fetch-site', 
        'sec-fetch-mode', 'sec-fetch-user', 'sec-fetch-dest',
        'accept-encoding', 'accept-language', 'cookie'
    ])


# ============== Main Stealth Engine ==============

class StealthEngine:
    """
    Ultimate stealth engine with ML optimization and real-time adaptation
    Consolidates all anti-detection mechanisms
    """
    
    # Class-level fingerprint database
    FINGERPRINT_DATABASE = {
        'chrome_windows': {
            'ja3': '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,65037-0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0',
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ],
            'screen_resolutions': [(1920, 1080), (2560, 1440), (1366, 768), (3840, 2160)],
            'gpu_vendors': ['NVIDIA', 'AMD', 'Intel'],
        },
        'firefox_windows': {
            'ja3': '771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-13-51-45-43-27-21,29-23-24-25,0',
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            ],
        },
        'safari_macos': {
            'ja3': '771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49159-52394-49155-49154-10,0-23-65281-10-11-16-5-13-18-51-45-43-27-21,29-23-24-25,0',
            'user_agents': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            ],
            'screen_resolutions': [(2560, 1600), (3024, 1964), (3456, 2234)],
        }
    }
    
    def __init__(self, profile_manager=None, ml_optimizer=None):
        self.profile_manager = profile_manager
        self.ml_optimizer = ml_optimizer or self._create_default_ml_optimizer()
        
        # Performance tracking
        self.success_history = deque(maxlen=1000)
        self.detection_history = deque(maxlen=1000)
        self.performance_metrics = defaultdict(lambda: {
            'attempts': 0, 'successes': 0, 'detections': 0, 
            'avg_response_time': 0.0, 'last_success': None
        })
        
        # Fingerprint evolution tracking
        self.fingerprint_mutations = defaultdict(list)
        self.successful_fingerprints = set()
        
        # Session management
        self.active_sessions: Dict[str, Any] = {}
        self._session_lock = asyncio.Lock()
        
        # Initialize submodules
        self.sensor_generator = SensorDataGenerator()
        self.behavior_engine = BehaviorEngine()
        self.cdp_protector = CDPProtector()
        self.canvas_stabilizer = CanvasStabilizer()
        
        logger.info("🛡️ StealthEngine v10.0 initialized - Ultimate anti-detection active")
    
    def _create_default_ml_optimizer(self):
        """Create default ML optimizer if TensorFlow available"""
        if HAS_TENSORFLOW:
            return MLOptimizer()
        else:
            logger.warning("TensorFlow not available - ML optimization disabled")
            return None
    
    async def create_stealth_context(self, 
                                   browser_context: BrowserContext,
                                   device_profile: Optional[DeviceProfile] = None,
                                   platform: str = "generic") -> BrowserContext:
        """
        Transform a browser context into a fully protected stealth context
        """
        if not device_profile:
            device_profile = self.generate_device_profile(platform)
        
        # 1. Apply core stealth patches
        await self._apply_core_stealth(browser_context, device_profile)
        
        # 2. Configure network interception
        await self._setup_network_interception(browser_context, device_profile)
        
        # 3. Inject advanced stealth scripts
        await self._inject_stealth_scripts(browser_context, device_profile)
        
        # 4. Setup behavioral patterns
        await self.behavior_engine.initialize_context(browser_context, device_profile)
        
        # 5. Configure CDP protection
        if hasattr(browser_context, '_connection'):
            await self.cdp_protector.protect_context(browser_context)
        
        logger.info(f"✅ Stealth context created: {device_profile.browser} on {device_profile.os}")
        
        return browser_context
    
    def generate_device_profile(self, platform: str = "generic") -> DeviceProfile:
        """
        Generate a realistic device profile optimized for the target platform
        """
        # Platform-specific optimization
        platform_preferences = {
            'ticketmaster': {
                'browsers': ['Chrome', 'Edge'],
                'os': ['Windows 11', 'macOS'],
                'high_end_devices': True
            },
            'fansale': {
                'browsers': ['Chrome', 'Firefox', 'Safari'],
                'os': ['Windows 10', 'Windows 11', 'macOS'],
                'include_mobile': True
            },
            'generic': {
                'browsers': ['Chrome', 'Firefox', 'Edge', 'Safari'],
                'os': ['Windows 10', 'Windows 11', 'macOS', 'Ubuntu'],
                'balanced': True
            }
        }
        
        prefs = platform_preferences.get(platform, platform_preferences['generic'])
        
        # Select OS and browser
        os_choice = random.choice(prefs['os'])
        browser_choice = random.choice(prefs['browsers'])
        
        # Generate consistent hardware profile
        if prefs.get('high_end_devices'):
            cpu_cores = random.choice([8, 12, 16, 24])
            memory_gb = random.choice([16, 32, 64])
            gpu_vendor = random.choice(['NVIDIA', 'AMD'])
            gpu_model = self._get_high_end_gpu(gpu_vendor)
        else:
            cpu_cores = random.choice([4, 6, 8, 12])
            memory_gb = random.choice([8, 16, 32])
            gpu_vendor = random.choice(['NVIDIA', 'AMD', 'Intel'])
            gpu_model = self._get_standard_gpu(gpu_vendor)
        
        # Generate screen resolution
        if os_choice.startswith('Windows'):
            screen_res = random.choice([(1920, 1080), (2560, 1440), (1366, 768), (3840, 2160)])
        elif os_choice == 'macOS':
            screen_res = random.choice([(2560, 1600), (3024, 1964), (3456, 2234)])
        else:
            screen_res = random.choice([(1920, 1080), (2560, 1440)])
        
        # Generate version
        browser_version = self._get_latest_browser_version(browser_choice)
        
        # Device type
        if prefs.get('include_mobile') and random.random() < 0.15:
            device_type = random.choice(['mobile', 'tablet'])
        else:
            device_type = random.choice(['desktop', 'laptop'])
        
        # Generate consistent locale/timezone for Italy focus
        locale = random.choice(['it-IT', 'en-US', 'en-GB'])
        timezone = 'Europe/Rome' if locale == 'it-IT' else random.choice([
            'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'America/New_York'
        ])
        
        profile = DeviceProfile(
            device_type=device_type,
            os=os_choice,
            os_version=self._get_os_version(os_choice),
            browser=browser_choice,
            browser_version=browser_version,
            screen_res=screen_res,
            viewport_size=(0, 0),  # Auto-calculated
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            gpu_vendor=gpu_vendor,
            gpu_model=gpu_model,
            timezone=timezone,
            locale=locale,
            languages=self._generate_language_list(locale),
            battery_level=random.uniform(0.3, 1.0) if device_type in ['mobile', 'tablet', 'laptop'] else None,
            charging=random.choice([True, False]) if device_type in ['mobile', 'tablet', 'laptop'] else None,
            platform_hints={'target': platform}
        )
        
        # Apply ML optimization if available
        if self.ml_optimizer:
            profile = self.ml_optimizer.optimize_profile(profile, platform)
        
        return profile
    
    async def _apply_core_stealth(self, context: BrowserContext, profile: DeviceProfile):
        """Apply core stealth modifications to context"""
        
        # Set viewport
        await context.set_viewport_size({
            'width': profile.viewport_size[0],
            'height': profile.viewport_size[1]
        })
        
        # Set user agent
        await context.set_extra_http_headers({
            'User-Agent': self._generate_user_agent(profile)
        })
        
        # Set geolocation if mobile
        if profile.device_type in ['mobile', 'tablet']:
            await context.set_geolocation({
                'latitude': 41.9028 + random.uniform(-0.1, 0.1),  # Rome
                'longitude': 12.4964 + random.uniform(-0.1, 0.1)
            })
        
        # Set locale
        await context.set_locale(profile.locale)
        
        # Set timezone
        await context.set_timezone(profile.timezone)
        
        # Add cookies for trust
        await self._add_trust_cookies(context, profile)
    
    async def _setup_network_interception(self, context: BrowserContext, profile: DeviceProfile):
        """Setup network request interception for stealth"""
        
        async def handle_route(route: Route, request: Request):
            headers = {**request.headers}
            
            # Apply proper header ordering
            ordered_headers = self._order_headers(headers, profile.browser)
            
            # Add platform-specific headers
            if profile.browser == 'Chrome':
                ordered_headers.update({
                    'sec-ch-ua': self._generate_sec_ch_ua(profile),
                    'sec-ch-ua-mobile': '?1' if profile.device_type in ['mobile', 'tablet'] else '?0',
                    'sec-ch-ua-platform': f'"{profile.os.split()[0]}"',
                })
            
            # Continue with modified headers
            await route.continue_(headers=ordered_headers)
        
        await context.route('**/*', handle_route)
    
    async def _inject_stealth_scripts(self, context: BrowserContext, profile: DeviceProfile):
        """Inject comprehensive stealth scripts"""
        
        # Generate script content
        stealth_script = self._generate_stealth_script(profile)
        
        # Add initialization script
        await context.add_init_script(stealth_script)
        
    def _generate_stealth_script(self, profile: DeviceProfile) -> str:
        """Generate comprehensive stealth script"""
        
        # Get sensor data
        sensor_data = self.sensor_generator.generate_for_profile(profile)
        
        script = f"""
        // StealthEngine v10.0 - Advanced Anti-Detection
        (() => {{
            'use strict';
            
            const STEALTH_CONFIG = {json.dumps({
                'profile': asdict(profile),
                'sensors': asdict(sensor_data),
                'fingerprint': self._generate_fingerprint_config(profile)
            })};
            
            // ========== Core Patches ==========
            
            // Remove webdriver indicators
            delete navigator.__proto__.webdriver;
            delete navigator.__proto__.__proto__.webdriver;
            
            // CDP Detection Prevention
            const originalCall = Function.prototype.call;
            Function.prototype.call = function() {{
                if (this.toString().includes('Runtime.')) {{
                    return undefined;
                }}
                return originalCall.apply(this, arguments);
            }};
            
            // ========== Navigator Overrides ==========
            
            const navigatorProps = {{
                platform: STEALTH_CONFIG.profile.os.includes('Windows') ? 'Win32' : 
                         STEALTH_CONFIG.profile.os.includes('Mac') ? 'MacIntel' : 'Linux',
                vendor: STEALTH_CONFIG.profile.browser === 'Chrome' ? 'Google Inc.' : 
                       STEALTH_CONFIG.profile.browser === 'Safari' ? 'Apple Computer, Inc.' : '',
                vendorSub: '',
                hardwareConcurrency: STEALTH_CONFIG.profile.cpu_cores,
                deviceMemory: Math.min(8, STEALTH_CONFIG.profile.memory_gb),
                languages: STEALTH_CONFIG.profile.languages,
                language: STEALTH_CONFIG.profile.languages[0],
                maxTouchPoints: STEALTH_CONFIG.profile.device_type === 'mobile' ? 5 : 
                               STEALTH_CONFIG.profile.device_type === 'tablet' ? 10 : 0,
                connection: {{
                    effectiveType: STEALTH_CONFIG.profile.effective_type,
                    type: STEALTH_CONFIG.profile.connection_type,
                    downlink: STEALTH_CONFIG.profile.downlink,
                    rtt: STEALTH_CONFIG.profile.rtt,
                    saveData: false
                }}
            }};
            
            for (const [key, value] of Object.entries(navigatorProps)) {{
                Object.defineProperty(navigator, key, {{
                    get: () => value,
                    enumerable: true,
                    configurable: true
                }});
            }}
            
            // ========== Screen & Window ==========
            
            const screenProps = {{
                width: {profile.screen_res[0]},
                height: {profile.screen_res[1]},
                availWidth: {profile.screen_res[0]},
                availHeight: {profile.screen_res[1] - random.randint(40, 100)},
                colorDepth: 24,
                pixelDepth: 24,
                orientation: {{
                    angle: 0,
                    type: 'landscape-primary'
                }}
            }};
            
            for (const [key, value] of Object.entries(screenProps)) {{
                Object.defineProperty(screen, key, {{
                    get: () => value,
                    enumerable: true,
                    configurable: true
                }});
            }}
            
            Object.defineProperty(window, 'devicePixelRatio', {{
                get: () => {self._calculate_dpr(profile)},
                enumerable: true
            }});
            
            // ========== WebGL Protection ==========
            
            const getContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {{
                const context = getContext.apply(this, [type, ...args]);
                
                if (type === 'webgl' || type === 'webgl2' || type === 'experimental-webgl') {{
                    const getParameter = context.getParameter.bind(context);
                    context.getParameter = function(param) {{
                        // UNMASKED_VENDOR_WEBGL
                        if (param === 0x9245) {{
                            return STEALTH_CONFIG.fingerprint.webgl_vendor;
                        }}
                        // UNMASKED_RENDERER_WEBGL  
                        if (param === 0x9246) {{
                            return STEALTH_CONFIG.fingerprint.webgl_renderer;
                        }}
                        return getParameter(param);
                    }};
                }}
                
                return context;
            }};
            
            // ========== Canvas Fingerprinting ==========
            
            {self.canvas_stabilizer.generate_script()}
            
            // ========== AudioContext Protection ==========
            
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {{
                const audioContext = AudioContext.prototype;
                const originalCreateOscillator = audioContext.createOscillator;
                
                audioContext.createOscillator = function() {{
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    const originalFrequency = Object.getOwnPropertyDescriptor(
                        OscillatorNode.prototype, 'frequency'
                    );
                    
                    Object.defineProperty(oscillator, 'frequency', {{
                        get: function() {{
                            return originalFrequency.get.call(this);
                        }},
                        set: function(value) {{
                            // Add fingerprint-specific noise
                            value = value * (1 + STEALTH_CONFIG.fingerprint.audio_drift);
                            originalFrequency.set.call(this, value);
                        }}
                    }});
                    
                    return oscillator;
                }};
            }}
            
            // ========== Battery API ==========
            
            if (STEALTH_CONFIG.profile.battery_level !== null) {{
                navigator.getBattery = async () => ({{
                    charging: STEALTH_CONFIG.profile.charging,
                    chargingTime: STEALTH_CONFIG.profile.charging ? 
                                  Math.floor(Math.random() * 3600) : Infinity,
                    dischargingTime: !STEALTH_CONFIG.profile.charging ? 
                                     Math.floor(Math.random() * 10800) : Infinity,
                    level: STEALTH_CONFIG.profile.battery_level,
                    addEventListener: () => {{}},
                    removeEventListener: () => {{}},
                    dispatchEvent: () => false
                }});
            }}
            
            // ========== Sensor APIs ==========
            
            {self.sensor_generator.generate_script(sensor_data)}
            
            // ========== Permissions API ==========
            
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = async function(desc) {{
                if (desc.name === 'notifications') {{
                    return {{ state: 'prompt', onchange: null }};
                }}
                return originalQuery.apply(this, arguments);
            }};
            
            // ========== Timing Protection ==========
            
            const originalNow = performance.now;
            let timeOffset = 0;
            
            performance.now = function() {{
                return originalNow.call(this) + timeOffset;
            }};
            
            // Add realistic drift over time
            setInterval(() => {{
                timeOffset += (Math.random() - 0.5) * 0.000001;
            }}, 1000);
            
            // ========== Error Stack Sanitization ==========
            
            const ErrorTypes = ['Error', 'EvalError', 'RangeError', 'ReferenceError', 
                               'SyntaxError', 'TypeError', 'URIError'];
            
            for (const errorType of ErrorTypes) {{
                const OriginalError = window[errorType];
                window[errorType] = new Proxy(OriginalError, {{
                    construct(target, args) {{
                        const err = new target(...args);
                        
                        if (err.stack) {{
                            err.stack = err.stack
                                .split('\\n')
                                .filter(line => !line.includes('__puppeteer_evaluation_script__') &&
                                              !line.includes('__playwright_evaluation_script__'))
                                .join('\\n');
                        }}
                        
                        return err;
                    }}
                }});
            }}
            
            // ========== Chrome Runtime ==========
            
            if (STEALTH_CONFIG.profile.browser === 'Chrome' && !window.chrome) {{
                window.chrome = {{
                    runtime: {{
                        connect: () => {{ throw new Error('Extension context invalidated'); }},
                        sendMessage: () => {{ throw new Error('Extension context invalidated'); }}
                    }},
                    loadTimes: () => ({{
                        requestTime: Date.now() / 1000 - 100,
                        startLoadTime: Date.now() / 1000 - 99,
                        commitLoadTime: Date.now() / 1000 - 98,
                        finishDocumentLoadTime: Date.now() / 1000 - 97,
                        finishLoadTime: Date.now() / 1000 - 96,
                        firstPaintTime: Date.now() / 1000 - 95,
                        firstPaintAfterLoadTime: 0,
                        navigationType: 'Reload',
                        wasFetchedViaSpdy: true,
                        wasNpnNegotiated: true,
                        npnNegotiatedProtocol: 'h2',
                        wasAlternateProtocolAvailable: false,
                        connectionInfo: 'h2'
                    }}),
                    csi: () => ({{
                        onloadT: Date.now(),
                        pageT: Date.now() - performance.timing.navigationStart,
                        startE: performance.timing.navigationStart,
                        tran: 15
                    }})
                }};
            }}
            
            console.log('🛡️ StealthEngine v10.0 protection active');
        }})();
        """
        
        return script
    
    def _generate_user_agent(self, profile: DeviceProfile) -> str:
        """Generate authentic user agent string"""
        
        templates = {
            ('Chrome', 'Windows'): 'Mozilla/5.0 (Windows NT {os_version}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36',
            ('Chrome', 'macOS'): 'Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser_version} Safari/537.36',
            ('Firefox', 'Windows'): 'Mozilla/5.0 (Windows NT {os_version}; Win64; x64; rv:{firefox_version}) Gecko/20100101 Firefox/{firefox_version}',
            ('Safari', 'macOS'): 'Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_version}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_version} Safari/605.1.15',
        }
        
        template_key = (profile.browser, profile.os.split()[0])
        template = templates.get(template_key, templates[('Chrome', 'Windows')])
        
        # Format version numbers
        os_version = '10.0' if 'Windows' in profile.os else None
        mac_version = profile.os_version.replace('.', '_') if 'macOS' in profile.os else None
        firefox_version = profile.browser_version.split('.')[0]
        safari_version = profile.browser_version
        
        return template.format(
            os_version=os_version,
            mac_version=mac_version,
            browser_version=profile.browser_version,
            firefox_version=firefox_version,
            safari_version=safari_version
        )
    
    def _generate_sec_ch_ua(self, profile: DeviceProfile) -> str:
        """Generate Sec-CH-UA header value"""
        major_version = profile.browser_version.split('.')[0]
        
        if profile.browser == 'Chrome':
            return f'"Not_A Brand";v="8", "Chromium";v="{major_version}", "Google Chrome";v="{major_version}"'
        elif profile.browser == 'Edge':
            return f'"Not_A Brand";v="8", "Chromium";v="{major_version}", "Microsoft Edge";v="{major_version}"'
        else:
            return ''
    
    def _order_headers(self, headers: Dict[str, str], browser: str) -> Dict[str, str]:
        """Order headers according to browser behavior"""
        
        browser_orders = {
            'Chrome': [
                'host', 'connection', 'cache-control', 'sec-ch-ua', 
                'sec-ch-ua-mobile', 'sec-ch-ua-platform', 'upgrade-insecure-requests',
                'user-agent', 'accept', 'sec-fetch-site', 'sec-fetch-mode',
                'sec-fetch-user', 'sec-fetch-dest', 'referer', 'accept-encoding',
                'accept-language', 'cookie'
            ],
            'Firefox': [
                'host', 'user-agent', 'accept', 'accept-language', 
                'accept-encoding', 'referer', 'connection', 'cookie',
                'upgrade-insecure-requests', 'sec-fetch-dest', 
                'sec-fetch-mode', 'sec-fetch-site'
            ],
            'Safari': [
                'host', 'cookie', 'connection', 'upgrade-insecure-requests',
                'accept', 'user-agent', 'referer', 'accept-language',
                'accept-encoding'
            ]
        }
        
        order = browser_orders.get(browser, browser_orders['Chrome'])
        ordered = {}
        
        # Add headers in order
        for key in order:
            if key in headers:
                ordered[key] = headers[key]
        
        # Add remaining headers
        for key, value in headers.items():
            if key not in ordered:
                ordered[key] = value
                
        return ordered
    
    def _generate_fingerprint_config(self, profile: DeviceProfile) -> Dict[str, Any]:
        """Generate consistent fingerprint configuration"""
        
        # WebGL fingerprint
        if profile.gpu_vendor == 'NVIDIA':
            webgl_vendor = 'NVIDIA Corporation'
            webgl_renderer = f'NVIDIA {profile.gpu_model}'
        elif profile.gpu_vendor == 'AMD':
            webgl_vendor = 'AMD'
            webgl_renderer = f'AMD {profile.gpu_model}'
        else:
            webgl_vendor = 'Intel Inc.'
            webgl_renderer = f'Intel {profile.gpu_model}'
        
        # Platform-specific adjustments
        if profile.os.startswith('Windows'):
            webgl_renderer = f'ANGLE ({webgl_vendor}, {webgl_renderer} Direct3D11 vs_5_0 ps_5_0)'
        
        # Generate consistent audio fingerprint
        audio_drift = self._generate_consistent_float(
            f"{profile.browser}_{profile.os}_{profile.gpu_model}",
            -0.00001, 0.00001
        )
        
        return {
            'webgl_vendor': webgl_vendor,
            'webgl_renderer': webgl_renderer,
            'audio_drift': audio_drift,
            'canvas_noise': self._generate_consistent_float(
                f"{profile.device_type}_{profile.browser}", 
                0.00001, 0.00005
            )
        }
    
    def _generate_consistent_float(self, seed: str, min_val: float, max_val: float) -> float:
        """Generate consistent float from seed"""
        hash_val = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
        normalized = (hash_val % 10000) / 10000
        return min_val + (normalized * (max_val - min_val))
    
    async def _add_trust_cookies(self, context: BrowserContext, profile: DeviceProfile):
        """Add cookies that indicate trusted user"""
        
        trust_cookies = [
            {
                'name': 'returning_visitor',
                'value': '1',
                'domain': '.ticketmaster.com',
                'path': '/',
                'expires': int(time.time()) + 86400 * 30
            },
            {
                'name': 'gdpr_consent',
                'value': 'accepted',
                'domain': '.fansale.it',
                'path': '/',
                'expires': int(time.time()) + 86400 * 365
            }
        ]
        
        for cookie in trust_cookies:
            try:
                await context.add_cookies([cookie])
            except:
                pass  # Ignore domain mismatch errors
    
    def _get_latest_browser_version(self, browser: str) -> str:
        """Get realistic latest browser version"""
        versions = {
            'Chrome': ['121.0.6167.85', '120.0.6099.130', '120.0.6099.109'],
            'Firefox': ['122.0', '121.0', '120.0.1'],
            'Safari': ['17.2.1', '17.2', '17.1.2'],
            'Edge': ['121.0.2277.83', '120.0.2210.144', '120.0.2210.133']
        }
        return random.choice(versions.get(browser, ['100.0.0.0']))
    
    def _get_os_version(self, os: str) -> str:
        """Get specific OS version"""
        versions = {
            'Windows 11': '10.0.22631',
            'Windows 10': '10.0.19045',
            'macOS': '14.2.1',
            'Ubuntu': '22.04'
        }
        return versions.get(os, '10.0')
    
    def _get_high_end_gpu(self, vendor: str) -> str:
        """Get high-end GPU model"""
        gpus = {
            'NVIDIA': ['GeForce RTX 4090', 'GeForce RTX 4080', 'GeForce RTX 4070 Ti'],
            'AMD': ['Radeon RX 7900 XTX', 'Radeon RX 7900 XT', 'Radeon RX 6950 XT']
        }
        return random.choice(gpus.get(vendor, ['Unknown GPU']))
    
    def _get_standard_gpu(self, vendor: str) -> str:
        """Get standard GPU model"""
        gpus = {
            'NVIDIA': ['GeForce RTX 3060', 'GeForce GTX 1660 Ti', 'GeForce RTX 3050'],
            'AMD': ['Radeon RX 6600', 'Radeon RX 6500 XT', 'Radeon RX 5500 XT'],
            'Intel': ['Iris Xe Graphics', 'UHD Graphics 770', 'UHD Graphics 730']
        }
        return random.choice(gpus.get(vendor, ['Unknown GPU']))
    
    def _generate_language_list(self, locale: str) -> List[str]:
        """Generate realistic language preference list"""
        if locale == 'it-IT':
            return ['it-IT', 'it', 'en-US', 'en']
        elif locale == 'en-GB':
            return ['en-GB', 'en', 'en-US']
        else:
            return ['en-US', 'en']
    
    def _calculate_dpr(self, profile: DeviceProfile) -> float:
        """Calculate device pixel ratio"""
        if profile.screen_res[0] >= 2560:
            return random.choice([1.5, 2.0])
        elif profile.device_type in ['mobile', 'tablet']:
            return random.choice([2.0, 3.0])
        else:
            return 1.0
    
    async def create_tls_session(self, profile: DeviceProfile) -> httpx.AsyncClient:
        """Create HTTP client with proper TLS fingerprint"""
        
        # Get TLS fingerprint for browser/OS combo
        tls_fp = self._get_tls_fingerprint(profile)
        
        if HAS_TLS_CLIENT:
            # Use tls-client for exact fingerprint control
            session = tls_client.Session(
                client_identifier=f"{profile.browser.lower()}_{profile.browser_version.split('.')[0]}",
                ja3_string=tls_fp.ja3_string,
                h2_settings=tls_fp.h2_settings,
                h2_window_update=tls_fp.h2_window_update,
                pseudo_header_order=tls_fp.pseudo_header_order,
                header_order=tls_fp.header_order
            )
            
            # Wrap in httpx-compatible interface
            return TLSClientWrapper(session, profile)
        else:
            # Fallback to standard httpx with best-effort configuration
            return httpx.AsyncClient(
                http2=True,
                headers=self._order_headers({
                    'User-Agent': self._generate_user_agent(profile),
                    'Accept-Language': ','.join(profile.languages),
                }, profile.browser)
            )
    
    def _get_tls_fingerprint(self, profile: DeviceProfile) -> TLSFingerprint:
        """Get appropriate TLS fingerprint for profile"""
        
        # Try exact match first
        key = f"{profile.browser.lower()}_{profile.os.split()[0].lower()}"
        fingerprint_data = self.FINGERPRINT_DATABASE.get(key)
        
        # Fallback to Chrome Windows
        if not fingerprint_data:
            fingerprint_data = self.FINGERPRINT_DATABASE['chrome_windows']
        
        return TLSFingerprint(
            ja3_string=fingerprint_data['ja3'],
            ja3_hash=hashlib.md5(fingerprint_data['ja3'].encode()).hexdigest()
        )
    
    def track_success(self, profile_id: str, platform: str, success: bool, 
                     detection_confidence: float = 0.0):
        """Track success/failure for ML optimization"""
        
        event = {
            'timestamp': time.time(),
            'profile_id': profile_id,
            'platform': platform,
            'success': success,
            'detection_confidence': detection_confidence
        }
        
        self.success_history.append(event)
        
        # Update metrics
        metrics = self.performance_metrics[f"{profile_id}_{platform}"]
        metrics['attempts'] += 1
        if success:
            metrics['successes'] += 1
            metrics['last_success'] = datetime.now()
        else:
            metrics['detections'] += 1
        
        # Trigger ML learning if available
        if self.ml_optimizer and len(self.success_history) % 100 == 0:
            asyncio.create_task(self.ml_optimizer.learn_from_history(list(self.success_history)))
    
    def get_success_rate(self, profile_id: str, platform: str) -> float:
        """Get success rate for profile/platform combination"""
        metrics = self.performance_metrics.get(f"{profile_id}_{platform}")
        if not metrics or metrics['attempts'] == 0:
            return 0.0
        return metrics['successes'] / metrics['attempts']


# ============== Sub-Modules ==============

class SensorDataGenerator:
    """Generate realistic sensor data for anti-bot evasion"""
    
    def generate_for_profile(self, profile: DeviceProfile) -> SensorData:
        """Generate sensor data matching device profile"""
        sensor_data = SensorData()
        
        # Generate realistic motion data
        sensor_data.generate_realistic_motion(profile.device_type)
        
        # Add performance entries
        sensor_data.performance_entries = {
            'navigationStart': 0,
            'domContentLoadedEventEnd': random.randint(800, 2000),
            'loadEventEnd': random.randint(1500, 3000),
            'firstPaint': random.randint(100, 500),
            'firstContentfulPaint': random.randint(200, 800)
        }
        
        return sensor_data
    
    def generate_script(self, sensor_data: SensorData) -> str:
        """Generate JavaScript for sensor APIs"""
        
        return f"""
        // Sensor API overrides
        if (window.DeviceMotionEvent) {{
            Object.defineProperty(window, 'DeviceMotionEvent', {{
                value: function() {{
                    return {{
                        acceleration: {{
                            x: {sensor_data.accelerometer[0]},
                            y: {sensor_data.accelerometer[1]},
                            z: {sensor_data.accelerometer[2]}
                        }},
                        accelerationIncludingGravity: {{
                            x: {sensor_data.accelerometer[0]},
                            y: {sensor_data.accelerometer[1]},
                            z: {sensor_data.accelerometer[2]}
                        }},
                        rotationRate: {{
                            alpha: {sensor_data.gyroscope[0]},
                            beta: {sensor_data.gyroscope[1]},
                            gamma: {sensor_data.gyroscope[2]}
                        }},
                        interval: 16
                    }};
                }}
            }});
        }}
        
        if (window.DeviceOrientationEvent) {{
            Object.defineProperty(window, 'DeviceOrientationEvent', {{
                value: function() {{
                    return {{
                        alpha: {sensor_data.alpha},
                        beta: {sensor_data.beta},
                        gamma: {sensor_data.gamma},
                        absolute: false
                    }};
                }}
            }});
        }}
        """
    
    def generate_akamai_bd(self, profile: DeviceProfile, sensor_data: SensorData) -> str:
        """Generate Akamai 'bd' parameter"""
        
        components = []
        
        # Basic environment data
        components.extend([
            '-1',  # Start marker
            '2',   # Version
            profile.timezone.split('/')[-1],  # Timezone
            '-1',  # Plugins count
            str(int(profile.screen_res[0])),  # Screen width
            str(int(profile.screen_res[1])),  # Screen height
            str(int(profile.viewport_size[0])),  # Viewport width
            str(int(profile.viewport_size[1])),  # Viewport height
            str(int(profile.screen_res[0])),  # Available width
            str(int(profile.screen_res[1] - 40)),  # Available height
            '24',  # Color depth
            '24',  # Pixel depth
            '0',   # Touch support
            'false',  # Maxtouchpoints check
        ])
        
        # Motion data
        if profile.device_type in ['mobile', 'tablet']:
            motion_string = f"{sensor_data.accelerometer[0]:.3f},{sensor_data.accelerometer[1]:.3f},{sensor_data.accelerometer[2]:.3f}"
            components.append(motion_string)
        else:
            components.append('0,0,0')
        
        # Timing data
        components.append(str(int(time.time() * 1000)))
        
        return ','.join(components)


class BehaviorEngine:
    """Advanced behavioral simulation engine"""
    
    async def initialize_context(self, context: BrowserContext, profile: DeviceProfile):
        """Initialize behavioral patterns for context"""
        # Generate behavior profile
        behavior_config = self._generate_behavior_config(profile)
        
        # Inject behavior script
        await context.add_init_script(self._generate_behavior_script(behavior_config))
        
        # Set up page-level behavior hooks
        context.on('page', lambda page: asyncio.create_task(self._setup_page_behavior(page, behavior_config)))
        
        logger.debug(f"Behavior engine initialized for {profile.device_type}")
    
    def _generate_behavior_config(self, profile: DeviceProfile) -> Dict[str, Any]:
        """Generate realistic behavior configuration"""
        return {
            'mouse': {
                'movement_speed': random.uniform(0.8, 2.5),  # pixels/ms
                'curve_factor': random.uniform(0.1, 0.4),
                'hesitation_points': random.randint(0, 3),
                'overshoot_probability': random.uniform(0.05, 0.2),
                'jitter_amplitude': random.uniform(0.5, 2.0),
                'acceleration_curve': random.choice(['ease-in-out', 'linear', 'ease-out']),
            },
            'keyboard': {
                'typing_speed_wpm': profile.typing_speed_wpm,
                'key_hold_time': random.uniform(50, 150),  # ms
                'inter_key_delay': random.uniform(80, 200),  # ms
                'typo_probability': random.uniform(0.01, 0.05),
                'correction_delay': random.uniform(300, 800),  # ms
                'burst_typing': random.random() < 0.3,
                'pause_patterns': self._generate_pause_patterns(),
            },
            'scroll': {
                'behavior': profile.scroll_behavior,
                'speed': random.uniform(300, 800),  # pixels/scroll
                'momentum_decay': random.uniform(0.85, 0.95),
                'wheel_delta_multiplier': random.uniform(0.8, 1.2),
                'touch_sensitivity': random.uniform(0.7, 1.3),
            },
            'attention': {
                'focus_duration': random.uniform(2000, 8000),  # ms
                'distraction_probability': random.uniform(0.05, 0.15),
                'reading_speed': random.uniform(200, 400),  # words/min
                'hover_duration': random.uniform(50, 300),  # ms
                'double_check_probability': random.uniform(0.1, 0.3),
            },
            'timing': {
                'think_time': random.uniform(500, 2000),  # ms before actions
                'micro_pauses': random.uniform(10, 50),  # ms between micro-actions
                'fatigue_factor': random.uniform(0.001, 0.005),  # slowdown over time
                'rush_factor': random.uniform(0.8, 1.2),  # speed during urgency
            }
        }
    def _generate_behavior_script(self, config: Dict[str, Any]) -> str:
        """Generate behavior injection script"""
        return f"""
        // Behavioral Simulation Engine
        (() => {{
            const BEHAVIOR_CONFIG = {json.dumps(config)};
            
            // Mouse movement simulation
            let lastMouseX = 0, lastMouseY = 0;
            let mouseVelocity = 0;
            
            document.addEventListener('mousemove', (e) => {{
                const deltaX = e.clientX - lastMouseX;
                const deltaY = e.clientY - lastMouseY;
                const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                
                mouseVelocity = distance / BEHAVIOR_CONFIG.mouse.movement_speed;
                
                // Add micro-jitter to mouse position
                if (Math.random() < 0.1) {{
                    e.clientX += (Math.random() - 0.5) * BEHAVIOR_CONFIG.mouse.jitter_amplitude;
                    e.clientY += (Math.random() - 0.5) * BEHAVIOR_CONFIG.mouse.jitter_amplitude;
                }}
                
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
            }}, true);
            
            // Keyboard behavior tracking
            let keyPressCount = 0;
            let lastKeyTime = Date.now();
            let typingVelocity = 0;
            
            document.addEventListener('keydown', (e) => {{
                const now = Date.now();
                const timeDelta = now - lastKeyTime;
                
                // Calculate typing velocity
                typingVelocity = 1000 / timeDelta; // keys per second
                
                // Add realistic key hold variation
                setTimeout(() => {{
                    if (e.target && e.target.dispatchEvent) {{
                        e.target.dispatchEvent(new KeyboardEvent('keyup', e));
                    }}
                }}, BEHAVIOR_CONFIG.keyboard.key_hold_time + (Math.random() - 0.5) * 20);
                
                keyPressCount++;
                lastKeyTime = now;
                
                // Check for pause patterns
                BEHAVIOR_CONFIG.keyboard.pause_patterns.forEach(pattern => {{
                    if (keyPressCount % pattern.after_chars === 0 && Math.random() < pattern.probability) {{
                        e.preventDefault();
                        setTimeout(() => {{
                            e.target.dispatchEvent(new KeyboardEvent('keydown', e));
                        }}, pattern.duration);
                    }}
                }});
            }}, true);
            
            // Scroll behavior enhancement
            let scrollMomentum = 0;
            let lastScrollTime = Date.now();
            
            document.addEventListener('wheel', (e) => {{
                const now = Date.now();
                const timeDelta = now - lastScrollTime;
                
                // Apply momentum
                if (BEHAVIOR_CONFIG.scroll.behavior === 'momentum' && timeDelta < 100) {{
                    scrollMomentum = scrollMomentum * BEHAVIOR_CONFIG.scroll.momentum_decay + e.deltaY;
                    e.deltaY = scrollMomentum;
                }} else {{
                    scrollMomentum = e.deltaY;
                }}
                
                // Add variation to scroll delta
                e.deltaY *= BEHAVIOR_CONFIG.scroll.wheel_delta_multiplier;
                
                lastScrollTime = now;
            }}, {{ passive: false }});
            
            // Attention simulation
            let focusStartTime = Date.now();
            let isDistracted = false;
            
            setInterval(() => {{
                const focusDuration = Date.now() - focusStartTime;
                
                if (!isDistracted && focusDuration > BEHAVIOR_CONFIG.attention.focus_duration) {{
                    if (Math.random() < BEHAVIOR_CONFIG.attention.distraction_probability) {{
                        isDistracted = true;
                        
                        // Simulate distraction (mouse drift, etc.)
                        const distractionEvent = new MouseEvent('mousemove', {{
                            clientX: lastMouseX + (Math.random() - 0.5) * 100,
                            clientY: lastMouseY + (Math.random() - 0.5) * 100
                        }});
                        document.dispatchEvent(distractionEvent);
                        
                        setTimeout(() => {{
                            isDistracted = false;
                            focusStartTime = Date.now();
                        }}, random.uniform(1000, 3000));
                    }}
                }}
            }}, 1000);
            
            // Timing fatigue simulation
            let sessionStartTime = Date.now();
            let fatigueFactor = 1.0;
            
            setInterval(() => {{
                const sessionDuration = Date.now() - sessionStartTime;
                fatigueFactor = 1.0 + (sessionDuration / 1000) * BEHAVIOR_CONFIG.timing.fatigue_factor;
                
                // Apply fatigue to various behaviors
                BEHAVIOR_CONFIG.mouse.movement_speed *= fatigueFactor;
                BEHAVIOR_CONFIG.keyboard.inter_key_delay *= fatigueFactor;
            }}, 5000);
            
            // Export behavior metrics
            window.__behaviorMetrics = {{
                getMouseVelocity: () => mouseVelocity,
                getTypingVelocity: () => typingVelocity,
                getFatigueFactor: () => fatigueFactor,
                isDistracted: () => isDistracted,
                getSessionDuration: () => Date.now() - sessionStartTime
            }};
        }})();
        """
    async def _setup_page_behavior(self, page: Page, config: Dict[str, Any]):
        """Set up page-level behavior patterns"""
        # Add realistic delays before interactions
        original_click = page.click

        async def custom_click(selector, **kwargs):
            # Pre-click hesitation
            await asyncio.sleep(config['timing']['think_time'] / 1000)

            # Move mouse to element with human-like path
            element = await page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                if box:
                    await self._human_mouse_move(page, box['x'] + box['width']/2, box['y'] + box['height']/2, config)

            # Actual click with micro-delay
            await asyncio.sleep(config['timing']['micro_pauses'] / 1000)
            return await original_click(selector, **kwargs)

        page.click = custom_click

        # Override type method for human-like typing
        original_type = page.type

        async def custom_type(selector, text, **kwargs):
            await page.focus(selector)
            await asyncio.sleep(config['timing']['think_time'] / 1000)
            
            # Type with realistic speed and patterns
            for i, char in enumerate(text):
                # Check for typos
                if random.random() < config['keyboard']['typo_probability']:
                    # Type wrong character
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    await original_type(selector, wrong_char, delay=config['keyboard']['inter_key_delay'])
                    await asyncio.sleep(config['keyboard']['correction_delay'] / 1000)
                    # Delete and correct
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(config['keyboard']['inter_key_delay'] / 1000)
                
                # Type correct character
                await original_type(selector, char, delay=config['keyboard']['inter_key_delay'])
                
                # Check for pause patterns
                for pattern in config['keyboard']['pause_patterns']:
                    if i % pattern['after_chars'] == 0 and random.random() < pattern['probability']:
                        await asyncio.sleep(pattern['duration'] / 1000)
            
            return True
    async def _human_mouse_move(self, page: Page, target_x: float, target_y: float, config: Dict[str, Any]):
        """Simulate human-like mouse movement"""
        # Get current mouse position (simplified, you'd track this)
        current_x, current_y = 0, 0
        
        # Calculate path with bezier curve
        control_points = self._generate_bezier_control_points(
            current_x, current_y, target_x, target_y, config['mouse']['curve_factor']
        )
        
        # Move along path
        steps = random.randint(10, 30)
        for i in range(steps):
            t = i / steps
            # Bezier curve calculation
            x, y = self._bezier_point(t, current_x, current_y, 
                                     control_points[0], control_points[1],
                                     control_points[2], control_points[3],
                                     target_x, target_y)
            
            # Add jitter
            x += (random.random() - 0.5) * config['mouse']['jitter_amplitude']
            y += (random.random() - 0.5) * config['mouse']['jitter_amplitude']
            
            await page.mouse.move(x, y)
            await asyncio.sleep(config['mouse']['movement_speed'] / 1000)
        
        # Overshoot and correct
        if random.random() < config['mouse']['overshoot_probability']:
            overshoot_x = target_x + (random.random() - 0.5) * 20
            overshoot_y = target_y + (random.random() - 0.5) * 20
            await page.mouse.move(overshoot_x, overshoot_y)
            await asyncio.sleep(random.uniform(50, 150) / 1000)
            await page.mouse.move(target_x, target_y)
    
    def _generate_bezier_control_points(self, x1, y1, x2, y2, curve_factor):
        """Generate control points for bezier curve"""
        # Add randomness to control points for natural curves
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Perpendicular to the line
        dx = x2 - x1
        dy = y2 - y1
        
        # Control points offset
        offset = curve_factor * math.sqrt(dx*dx + dy*dy)
        
        return [
            mid_x - dy * offset + random.uniform(-20, 20),
            mid_y + dx * offset + random.uniform(-20, 20),
            mid_x + dy * offset + random.uniform(-20, 20),
            mid_y - dx * offset + random.uniform(-20, 20)
        ]
    
    def _bezier_point(self, t, x0, y0, x1, y1, x2, y2, x3, y3):
        """Calculate point on cubic bezier curve"""
        u = 1 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t
        
        x = uuu * x0 + 3 * uu * t * x1 + 3 * u * tt * x2 + ttt * x3
        y = uuu * y0 + 3 * uu * t * y1 + 3 * u * tt * y2 + ttt * y3
        
        return x, y


class CDPProtector:
    """Chrome DevTools Protocol detection prevention"""
    
    async def protect_context(self, context: BrowserContext):
        """Apply CDP protection to context"""
        if not hasattr(context, '_connection'):
            logger.warning("Context doesn't support CDP protection")
            return
        
        # Intercept CDP commands
        client = await context.new_cdp_session(await context.pages()[0])
        
        # Override runtime.enable to prevent console detection
        await client.send('Runtime.enable')
        
        # Inject CDP protection script
        await client.send('Page.addScriptToEvaluateOnNewDocument', {
            'source': self._generate_cdp_protection_script()
        })
        
        logger.debug("CDP protection applied")
    
    def _generate_cdp_protection_script(self) -> str:
        """Generate CDP detection prevention script"""
        return """
        // CDP Detection Prevention
        (() => {
            // Override console methods to hide CDP
            const originalConsoleDir = console.dir;
            console.dir = function(obj) {
                if (obj && obj.constructor && obj.constructor.name === 'ChromeDevTools') {
                    return undefined;
                }
                return originalConsoleDir.apply(this, arguments);
            };
            
            // Hide CDP-related properties
            const cdpProperties = [
                '__puppeteer_initial',
                '__playwright_initial',
                'calledRun',
                'emitClose',
                '_hasBeenBound'
            ];
            
            cdpProperties.forEach(prop => {
                if (window[prop]) {
                    delete window[prop];
                }
            });
            
            // Override Error.prepareStackTrace
            const originalPrepareStackTrace = Error.prepareStackTrace;
            Error.prepareStackTrace = function(err, structuredStackTrace) {
                if (structuredStackTrace) {
                    // Filter out CDP-related frames
                    structuredStackTrace = structuredStackTrace.filter(frame => {
                        const fileName = frame.getFileName();
                        return !fileName || (!fileName.includes('__puppeteer_evaluation_script__') &&
                                           !fileName.includes('__playwright_evaluation_script__'));
                    });
                }
                
                if (originalPrepareStackTrace) {
                    return originalPrepareStackTrace.call(this, err, structuredStackTrace);
                }
                return err.stack;
            };
            
            // Protect against CDP runtime detection
            const nativeToString = Function.prototype.toString;
            Function.prototype.toString = new Proxy(nativeToString, {
                apply(target, thisArg, argsList) {
                    if (thisArg === Function.prototype.toString) {
                        return nativeToString.call(nativeToString);
                    }
                    const result = Reflect.apply(target, thisArg, argsList);
                    
                    // Hide CDP modifications
                    if (result.includes('native code]')) {
                        return result;
                    }
                    
                    // Check if this is a native function that was modified
                    if (window.chrome && thisArg && thisArg.name) {
                        const nativeFuncs = ['querySelector', 'querySelectorAll', 'getElementById',
                                           'getElementsByClassName', 'getElementsByTagName'];
                        if (nativeFuncs.includes(thisArg.name)) {
                            return `function ${thisArg.name}() { [native code] }`;
                        }
                    }
                    
                    return result;
                }
            });
        })();
        """


class CanvasStabilizer:
    """Stabilize canvas fingerprint while adding controlled noise"""
    
    def generate_script(self) -> str:
        """Generate canvas stabilization script"""
        return """
        // Canvas Fingerprint Stabilization
        (() => {
            const seed = STEALTH_CONFIG.fingerprint.canvas_noise;
            let noiseIndex = 0;
            
            // Deterministic random based on seed
            function seededRandom() {
                const x = Math.sin(seed + noiseIndex++) * 10000;
                return x - Math.floor(x);
            }
            
            // Override toDataURL
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                if (context) {
                    // Add deterministic noise to canvas
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    
                    // Apply consistent but unique noise
                    for (let i = 0; i < data.length; i += 4) {
                        if (seededRandom() < 0.001) { // Very subtle noise
                            const noise = Math.floor(seededRandom() * 3) - 1;
                            data[i] = Math.max(0, Math.min(255, data[i] + noise));
                            data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                            data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                        }
                    }
                    
                    context.putImageData(imageData, 0, 0);
                }
                
                return originalToDataURL.apply(this, arguments);
            };
            
            // Override toBlob
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(callback) {
                const dataURL = this.toDataURL();
                originalToBlob.call(this, function(blob) {
                    // Blob is already affected by our toDataURL override
                    callback(blob);
                });
            };
            
            // Override getImageData to ensure consistency
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function() {
                const imageData = originalGetImageData.apply(this, arguments);
                
                // Apply same noise algorithm
                const data = imageData.data;
                noiseIndex = 0; // Reset for consistency
                
                for (let i = 0; i < data.length; i += 4) {
                    if (seededRandom() < 0.001) {
                        const noise = Math.floor(seededRandom() * 3) - 1;
                        data[i] = Math.max(0, Math.min(255, data[i] + noise));
                        data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                        data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                    }
                }
                
                return imageData;
            };
            
            // Font fingerprinting protection
            const measureTextOriginal = CanvasRenderingContext2D.prototype.measureText;
            CanvasRenderingContext2D.prototype.measureText = function(text) {
                const metrics = measureTextOriginal.call(this, text);
                
                // Add consistent micro-variations
                const variation = 1 + (seededRandom() - 0.5) * 0.001;
                
                return new Proxy(metrics, {
                    get(target, prop) {
                        if (prop === 'width') {
                            return target.width * variation;
                        }
                        return target[prop];
                    }
                });
            };
        })();
        """


class TLSClientWrapper:
    """Wrapper to make tls-client compatible with httpx interface"""
    
    def __init__(self, tls_session, profile: DeviceProfile):
        self.session = tls_session
        self.profile = profile
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Async GET request"""
        response = await asyncio.to_thread(self.session.get, url, **kwargs)
        return self._convert_response(response)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Async POST request"""
        response = await asyncio.to_thread(self.session.post, url, **kwargs)
        return self._convert_response(response)
    
    def _convert_response(self, tls_response) -> httpx.Response:
        """Convert tls-client response to httpx format"""
        # Create httpx.Response compatible object
        return httpx.Response(
            status_code=tls_response.status_code,
            headers=tls_response.headers,
            content=tls_response.content,
            request=httpx.Request("GET", tls_response.url)
        )
class MLOptimizer:
    """Machine Learning optimizer for profile selection and mutation"""
    
    def __init__(self):
        self.model = self._build_model() if HAS_TENSORFLOW else None
        self.feature_extractors = {
            'profile': self._extract_profile_features,
            'platform': self._extract_platform_features,
            'timing': self._extract_timing_features
        }
    
    def _build_model(self):
        """Build TensorFlow model for success prediction"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(50,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def optimize_profile(self, profile: DeviceProfile, platform: str) -> DeviceProfile:
        """Optimize profile using ML predictions"""
        if not self.model:
            return profile
        
        # Extract features
        features = self._extract_features(profile, platform)
        
        # Predict success probability
        success_prob = self.model.predict(features.reshape(1, -1))[0][0]
        
        # If low success probability, mutate profile
        if success_prob < 0.7:
            return self._mutate_profile(profile, platform)
        
        return profile
    
    def _extract_features(self, profile: DeviceProfile, platform: str) -> np.ndarray:
        """Extract features for ML model"""
        features = []
        
        # Profile features
        features.extend(self._extract_profile_features(profile))
        
        # Platform features
        features.extend(self._extract_platform_features(platform))
        
        # Timing features
        features.extend(self._extract_timing_features())
        
        return np.array(features)
    
    def _extract_profile_features(self, profile: DeviceProfile) -> List[float]:
        """Extract numerical features from profile"""
        return [
            hash(profile.browser) % 1000 / 1000,
            hash(profile.os) % 1000 / 1000,
            profile.screen_res[0] / 4000,
            profile.screen_res[1] / 3000,
            profile.cpu_cores / 32,
            profile.memory_gb / 64,
            hash(profile.gpu_vendor) % 1000 / 1000,
            1.0 if profile.device_type == 'mobile' else 0.0,
            profile.battery_level or 1.0,
            1.0 if profile.charging else 0.0
        ]
    
    def _extract_platform_features(self, platform: str) -> List[float]:
        """Extract platform-specific features"""
        platform_encoding = {
            'ticketmaster': [1, 0, 0],
            'fansale': [0, 1, 0],
            'vivaticket': [0, 0, 1],
            'generic': [0, 0, 0]
        }
        return platform_encoding.get(platform, [0, 0, 0])
    
    def _extract_timing_features(self) -> List[float]:
        """Extract timing-based features"""
        now = datetime.now()
        return [
            now.hour / 24,  # Hour of day
            now.weekday() / 7,  # Day of week
            now.day / 31,  # Day of month
            1.0 if now.hour >= 9 and now.hour <= 17 else 0.0,  # Business hours
        ]
    
    def _mutate_profile(self, profile: DeviceProfile, platform: str) -> DeviceProfile:
        """Mutate profile to increase success probability"""
        # Clone profile
        import copy
        mutated = copy.deepcopy(profile)
        
        # Platform-specific mutations
        if platform == 'ticketmaster':
            # Ticketmaster prefers newer browsers
            mutated.browser_version = self._get_latest_version(mutated.browser)
            
        elif platform == 'fansale':
            # Fansale works better with Italian locale
            if mutated.locale != 'it-IT':
                mutated.locale = 'it-IT'
                mutated.languages = ['it-IT', 'it', 'en-US', 'en']
        
        return mutated
    
    def _get_latest_version(self, browser: str) -> str:
        """Get latest browser version"""
        latest_versions = {
            'Chrome': '121.0.6167.85',
            'Firefox': '122.0',
            'Safari': '17.2.1',
            'Edge': '121.0.2277.83'
        }
        return latest_versions.get(browser, '100.0.0.0')
    async def learn_from_history(self, history: List[Dict[str, Any]]):
        """Train model on historical data"""
        if not self.model or len(history) < 100:
            return
        
        # Prepare training data
        X = []
        y = []
        
        for event in history:
            features = self._extract_features(
                event['profile'],
                event['platform']
            )
            X.append(features)
            y.append(1.0 if event['success'] else 0.0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        self.model.fit(X, y, epochs=10, batch_size=32, verbose=0)
        
        logger.info("ML model updated with historical data")


# ============== Utility Functions ==============

def create_stealth_engine(profile_manager=None) -> StealthEngine:
    """Factory function to create stealth engine"""
    return StealthEngine(profile_manager=profile_manager)


# ============== Integration with existing system ==============

class StealthEngineIntegration:
    """Integration layer for existing codebase"""
    
    @staticmethod
    async def enhance_playwright_context(context: BrowserContext, 
                                       profile_data: Dict[str, Any],
                                       platform: str = "generic") -> BrowserContext:
        """Enhance existing playwright context with stealth"""
        engine = create_stealth_engine()
        
        # Convert profile data to DeviceProfile
        device_profile = DeviceProfile(
            device_type=profile_data.get('device_type', 'desktop'),
            os=profile_data.get('os', 'Windows 11'),
            os_version=profile_data.get('os_version', '10.0.22631'),
            browser=profile_data.get('browser', 'Chrome'),
            browser_version=profile_data.get('browser_version', '121.0.6167.85'),
            screen_res=tuple(profile_data.get('screen_resolution', [1920, 1080])),
            viewport_size=tuple(profile_data.get('viewport_size', [1920, 980])),
            cpu_cores=profile_data.get('hardware_concurrency', 8),
            memory_gb=profile_data.get('device_memory', 16),
            gpu_vendor=profile_data.get('gpu_vendor', 'NVIDIA'),
            gpu_model=profile_data.get('gpu_model', 'GeForce RTX 3060'),
            timezone=profile_data.get('timezone', 'Europe/Rome'),
            locale=profile_data.get('locale', 'it-IT'),
            languages=profile_data.get('languages', ['it-IT', 'it', 'en-US', 'en'])
        )
        
        # Apply stealth enhancements
        return await engine.create_stealth_context(context, device_profile, platform)        