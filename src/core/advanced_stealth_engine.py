#!/usr/bin/env python3
"""
🛡️ DEPRECATION NOTICE: This file has been consolidated into stealth_engine.py

All functionality from advanced_stealth_engine.py has been merged into the main
stealth_engine.py file to eliminate code duplication and improve performance.

Use: from src.core.stealth_engine import StealthEngine
instead of importing from this file.

Legacy imports are provided below for backward compatibility.
"""

# Import unified stealth engine for backward compatibility
try:
    from .stealth_engine import StealthEngine, RealDeviceProfiles, DeviceProfile
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("DEPRECATED: Import from stealth_engine.py instead")
except ImportError:
    # Original implementation below for fallback
    pass

import asyncio
import random
import time
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

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
    """Database of real device profiles from actual users"""
    
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
        
        # Mixed browsers
        DeviceProfile("laptop", "Windows 11", "Firefox", (1920, 1080), 8, 16, "Intel Iris Xe", "Europe/Rome", "it-IT"),
        DeviceProfile("laptop", "Windows 11", "Edge", (1366, 768), 4, 8, "Intel UHD", "Europe/Rome", "it-IT"),
    ]
    
    @classmethod
    def get_random_profile(cls) -> DeviceProfile:
        """Get a random realistic device profile"""
        return random.choice(cls.PROFILES)

class AdvancedStealthEngine:
    """Next-generation anti-detection engine"""
    
    def __init__(self):
        self.current_profile: Optional[DeviceProfile] = None
        self.fingerprint_cache: Dict[str, Any] = {}
        self.behavioral_metrics = {
            'mouse_movements': 0,
            'clicks': 0,
            'scrolls': 0,
            'typing_patterns': [],
            'session_start': time.time()
        }
    
    def generate_ultra_stealth_profile(self) -> Dict[str, Any]:
        """Generate an ultra-realistic browser profile"""
        self.current_profile = RealDeviceProfiles.get_random_profile()
        profile = self.current_profile
        
        # Generate consistent fingerprint based on device
        fingerprint_seed = f"{profile.device_type}_{profile.os}_{profile.browser}"
        random.seed(hash(fingerprint_seed) % 2**32)
        
        stealth_config = {
            # Core browser settings
            'user_agent': self._generate_realistic_user_agent(profile),
            'viewport': self._generate_viewport(profile),
            'screen_resolution': profile.screen_res,
            'device_pixel_ratio': self._calculate_device_pixel_ratio(profile),
            
            # Hardware fingerprint
            'hardware_concurrency': profile.cpu_cores,
            'device_memory': profile.memory_gb,
            'webgl_vendor': profile.gpu_vendor,
            'webgl_renderer': self._generate_webgl_renderer(profile),
            
            # Localization
            'timezone': profile.timezone,
            'locale': profile.locale,
            'languages': self._generate_language_list(profile),
            
            # Advanced fingerprints
            'canvas_fingerprint': self._generate_canvas_fingerprint(profile),
            'audio_fingerprint': self._generate_audio_fingerprint(profile),
            'webrtc_ips': self._generate_webrtc_ips(),
            'fonts': self._generate_font_list(profile),
            'plugins': self._generate_plugin_list(profile),
            
            # Client hints
            'sec_ch_ua': self._generate_sec_ch_ua(profile),
            'sec_ch_ua_platform': self._get_platform_string(profile),
            'sec_ch_ua_mobile': '?1' if profile.device_type == 'mobile' else '?0',
            
            # Behavioral patterns
            'mouse_behavior': self._generate_mouse_behavior_pattern(),
            'typing_behavior': self._generate_typing_behavior_pattern(),
            'scroll_behavior': self._generate_scroll_behavior_pattern(),
        }
        
        # Reset random seed
        random.seed()
        
        return stealth_config
    
    def _generate_realistic_user_agent(self, profile: DeviceProfile) -> str:
        """Generate highly realistic user agent"""
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
        
        # Desktop/laptop - account for browser chrome
        browser_chrome_height = random.randint(120, 180)  # Address bar, bookmarks, etc.
        taskbar_height = random.randint(40, 50) if profile.os.startswith("Windows") else random.randint(25, 35)
        
        viewport_w = screen_w
        viewport_h = screen_h - browser_chrome_height - taskbar_height
        
        # Add some realistic variation
        viewport_w += random.randint(-20, 20)
        viewport_h += random.randint(-15, 15)
        
        return {'width': max(viewport_w, 800), 'height': max(viewport_h, 600)}
    
    def _calculate_device_pixel_ratio(self, profile: DeviceProfile) -> float:
        """Calculate realistic device pixel ratio"""
        screen_w, screen_h = profile.screen_res
        
        # High-DPI displays
        if screen_w >= 2560 or screen_h >= 1440:
            return random.choice([1.25, 1.5, 2.0])
        elif screen_w >= 1920:
            return random.choice([1.0, 1.25])
        else:
            return 1.0
    
    def _generate_webgl_renderer(self, profile: DeviceProfile) -> str:
        """Generate realistic WebGL renderer string"""
        gpu_mappings = {
            "NVIDIA RTX 4060": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002882) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "NVIDIA RTX 4070": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002786) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "Apple M2 Pro": "Apple M2 Pro",
            "NVIDIA GTX 1660": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 (0x00002184) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "AMD RX 6600": "ANGLE (AMD, AMD Radeon RX 6600 (0x000073FF) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "Intel Iris Xe": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x00009A49) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "Intel UHD": "ANGLE (Intel, Intel(R) UHD Graphics (0x00009BC4) Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "Adreno 730": "Adreno (TM) 730",
            "Apple A16": "Apple A16 GPU"
        }
        
        return gpu_mappings.get(profile.gpu_vendor, "ANGLE (Unknown GPU)")
    
    def _generate_language_list(self, profile: DeviceProfile) -> List[str]:
        """Generate realistic language preferences for Italian users"""
        base_langs = ["it-IT", "it"]
        
        # Add English with varying probability
        if random.random() < 0.85:  # Most Italians know some English
            base_langs.extend(["en-US", "en"])
        
        # Occasionally add other European languages
        if random.random() < 0.3:
            other_langs = ["fr-FR", "de-DE", "es-ES"]
            base_langs.append(random.choice(other_langs))
        
        return base_langs
    
    def _generate_canvas_fingerprint(self, profile: DeviceProfile) -> str:
        """Generate realistic canvas fingerprint"""
        # Create a deterministic but varied fingerprint
        seed = f"{profile.gpu_vendor}_{profile.os}_{profile.screen_res}"
        return hashlib.md5(seed.encode()).hexdigest()[:16]
    
    def _generate_audio_fingerprint(self, profile: DeviceProfile) -> str:
        """Generate realistic audio context fingerprint"""
        seed = f"audio_{profile.device_type}_{profile.os}"
        return hashlib.sha1(seed.encode()).hexdigest()[:12]
    
    def _generate_webrtc_ips(self) -> List[str]:
        """Generate realistic WebRTC IP leakage"""
        # Simulate typical Italian residential network
        base_ips = [
            f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",  # Home router
            f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}",     # Corporate network
        ]
        
        # Occasionally add IPv6
        if random.random() < 0.4:
            base_ips.append(f"2001:db8::{random.randint(1000, 9999)}:{random.randint(1000, 9999)}")
        
        return base_ips
    
    def _generate_font_list(self, profile: DeviceProfile) -> List[str]:
        """Generate realistic system font list"""
        base_fonts = [
            "Arial", "Calibri", "Cambria", "Comic Sans MS", "Consolas",
            "Georgia", "Impact", "Lucida Console", "Segoe UI", "Times New Roman",
            "Trebuchet MS", "Verdana"
        ]
        
        if profile.os == "macOS":
            mac_fonts = [
                "Helvetica Neue", "San Francisco", "Menlo", "Monaco",
                "Avenir", "Futura", "Optima"
            ]
            base_fonts.extend(mac_fonts)
        
        if profile.os.startswith("Windows"):
            win_fonts = [
                "Segoe UI Historic", "Segoe UI Emoji", "Microsoft YaHei",
                "Malgun Gothic", "Yu Gothic"
            ]
            base_fonts.extend(win_fonts)
        
        # Italian system might have these
        italian_fonts = ["Times New Roman", "Arial Unicode MS"]
        base_fonts.extend(italian_fonts)
        
        # Randomize order and selection
        selected_fonts = random.sample(base_fonts, k=random.randint(20, len(base_fonts)))
        return sorted(selected_fonts)
    
    def _generate_plugin_list(self, profile: DeviceProfile) -> List[Dict[str, str]]:
        """Generate realistic browser plugin list"""
        plugins = []
        
        # PDF viewers (always present)
        plugins.append({
            "name": "Chrome PDF Plugin",
            "filename": "internal-pdf-viewer",
            "description": "Portable Document Format"
        })
        
        # Platform-specific plugins
        if profile.os.startswith("Windows"):
            plugins.append({
                "name": "Microsoft Edge PDF Plugin",
                "filename": "pdf",
                "description": "pdf"
            })
        
        return plugins
    
    def _generate_sec_ch_ua(self, profile: DeviceProfile) -> str:
        """Generate realistic Sec-CH-UA header"""
        if profile.browser == "Chrome":
            version = "120"
            return f'"Not_A Brand";v="8", "Chromium";v="{version}", "Google Chrome";v="{version}"'
        elif profile.browser == "Edge":
            version = "120"
            return f'"Not_A Brand";v="8", "Chromium";v="{version}", "Microsoft Edge";v="{version}"'
        else:
            return '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
    
    def _get_platform_string(self, profile: DeviceProfile) -> str:
        """Get platform string for Sec-CH-UA-Platform"""
        if profile.os.startswith("Windows"):
            return '"Windows"'
        elif profile.os == "macOS":
            return '"macOS"'
        elif profile.os == "Android":
            return '"Android"'
        elif profile.os == "iOS":
            return '"iOS"'
        else:
            return '"Linux"'
    
    def _generate_mouse_behavior_pattern(self) -> Dict[str, Any]:
        """Generate realistic mouse movement patterns"""
        return {
            'movement_speed': random.uniform(0.8, 2.5),      # pixels per ms
            'curve_factor': random.uniform(0.1, 0.4),       # How curved movements are
            'pause_probability': random.uniform(0.05, 0.15), # Chance to pause mid-movement
            'overshoot_chance': random.uniform(0.1, 0.3),   # Chance to overshoot target
            'correction_delay': random.uniform(50, 200),     # ms before correcting overshoot
        }
    
    def _generate_typing_behavior_pattern(self) -> Dict[str, Any]:
        """Generate realistic typing patterns"""
        return {
            'base_speed': random.uniform(80, 180),           # ms between keystrokes
            'variation': random.uniform(20, 60),             # speed variation
            'burst_typing': random.random() < 0.3,           # Types in bursts vs steady
            'mistake_rate': random.uniform(0.01, 0.05),      # Typing mistake probability
            'correction_delay': random.uniform(100, 500),    # ms before correcting mistakes
        }
    
    def _generate_scroll_behavior_pattern(self) -> Dict[str, Any]:
        """Generate realistic scrolling patterns"""
        return {
            'scroll_speed': random.uniform(300, 800),        # pixels per scroll
            'momentum_decay': random.uniform(0.85, 0.95),    # How quickly scrolling stops
            'reverse_scroll_chance': random.uniform(0.1, 0.25), # Chance to scroll back up
            'pause_at_content': random.random() < 0.7,       # Pauses when interesting content appears
        }
    
    async def inject_ultra_stealth_script(self, page) -> None:
        """Inject the most advanced stealth script available"""
        stealth_config = self.generate_ultra_stealth_profile()
        
        # Generate the injection script
        injection_script = self._build_injection_script(stealth_config)
        
        # Inject before any page loads
        await page.add_init_script(injection_script)
        
        logger.info(f"🛡️ Ultra-stealth injected: {self.current_profile.device_type} {self.current_profile.os} {self.current_profile.browser}")
    
    def _build_injection_script(self, config: Dict[str, Any]) -> str:
        """Build the comprehensive stealth injection script"""
        return f"""
        // StealthMaster AI v2.0 - Ultra Anti-Detection
        (() => {{
            'use strict';
            
            // Core fingerprint overrides
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: true
            }});
            
            // Hardware fingerprint
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {config['hardware_concurrency']},
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {config['device_memory']},
                configurable: true
            }});
            
            // Language preferences
            Object.defineProperty(navigator, 'languages', {{
                get: () => {json.dumps(config['languages'])},
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'language', {{
                get: () => '{config['languages'][0]}',
                configurable: true
            }});
            
            // Screen properties with realistic jitter
            const originalScreen = screen;
            Object.defineProperty(window, 'screen', {{
                get: () => new Proxy(originalScreen, {{
                    get: (target, prop) => {{
                        if (prop === 'width') return {config['screen_resolution'][0]} + Math.floor((Math.random() - 0.5) * 4);
                        if (prop === 'height') return {config['screen_resolution'][1]} + Math.floor((Math.random() - 0.5) * 4);
                        if (prop === 'availWidth') return {config['screen_resolution'][0] - random.randint(0, 40)};
                        if (prop === 'availHeight') return {config['screen_resolution'][1] - random.randint(80, 120)};
                        if (prop === 'colorDepth') return 24;
                        if (prop === 'pixelDepth') return 24;
                        return target[prop];
                    }}
                }})
            }});
            
            // Device pixel ratio
            Object.defineProperty(window, 'devicePixelRatio', {{
                get: () => {config['device_pixel_ratio']},
                configurable: true
            }});
            
            // WebGL fingerprint protection
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {{
                const context = originalGetContext.call(this, type, ...args);
                
                if (type === 'webgl' || type === 'webgl2') {{
                    const originalGetParameter = context.getParameter;
                    context.getParameter = function(parameter) {{
                        if (parameter === context.VENDOR) return 'Google Inc. (ANGLE)';
                        if (parameter === context.RENDERER) return '{config['webgl_renderer']}';
                        if (parameter === context.VERSION) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
                        if (parameter === context.SHADING_LANGUAGE_VERSION) return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
                        return originalGetParameter.call(this, parameter);
                    }};
                }}
                
                return context;
            }};
            
            // Canvas fingerprint with deterministic noise
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                const context = this.getContext('2d');
                if (context) {{
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    
                    // Add deterministic noise based on device
                    const seed = '{config['canvas_fingerprint']}';
                    let hash = 0;
                    for (let i = 0; i < seed.length; i++) {{
                        hash = ((hash << 5) - hash + seed.charCodeAt(i)) & 0xffffffff;
                    }}
                    
                    for (let i = 0; i < data.length; i += 4) {{
                        if ((hash + i) % 1000 === 0) {{
                            const noise = ((hash + i) % 5) - 2;
                            data[i] = Math.max(0, Math.min(255, data[i] + noise));
                            data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                            data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                        }}
                    }}
                    
                    context.putImageData(imageData, 0, 0);
                }}
                
                return originalToDataURL.call(this, ...args);
            }};
            
            // Plugin enumeration
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = {json.dumps(config['plugins'])};
                    plugins.refresh = () => {{}};
                    plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                    return plugins;
                }}
            }});
            
            // Font detection protection
            const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
            const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
            
            Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {{
                get: function() {{
                    const value = originalOffsetWidth.get.call(this);
                    if (this.style && this.style.fontFamily) {{
                        // Add slight variation to font measurements
                        return value + (Math.sin(value * 0.1) * 0.5);
                    }}
                    return value;
                }}
            }});
            
            // Audio context fingerprint
            const originalCreateOscillator = window.AudioContext?.prototype?.createOscillator || 
                                           window.webkitAudioContext?.prototype?.createOscillator;
            
            if (originalCreateOscillator) {{
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                AudioContextClass.prototype.createOscillator = function() {{
                    const oscillator = originalCreateOscillator.call(this);
                    const originalStart = oscillator.start;
                    oscillator.start = function(when) {{
                        // Add slight frequency variation
                        this.frequency.value += (Math.random() - 0.5) * 0.001;
                        return originalStart.call(this, when);
                    }};
                    return oscillator;
                }};
            }}
            
            // Performance timing protection
            const originalPerformanceNow = performance.now;
            performance.now = function() {{
                return originalPerformanceNow.call(this) + (Math.random() - 0.5) * 0.1;
            }};
            
            // Memory info spoofing
            if (performance.memory) {{
                const memInfo = {{
                    usedJSHeapSize: Math.floor(Math.random() * 50000000) + 10000000,
                    totalJSHeapSize: 0,
                    jsHeapSizeLimit: 2197815296
                }};
                memInfo.totalJSHeapSize = memInfo.usedJSHeapSize + Math.floor(Math.random() * 10000000);
                
                Object.defineProperty(performance, 'memory', {{
                    get: () => memInfo,
                    configurable: true
                }});
            }}
            
            // WebRTC protection
            if (window.RTCPeerConnection) {{
                const originalCreateDataChannel = RTCPeerConnection.prototype.createDataChannel;
                RTCPeerConnection.prototype.createDataChannel = function() {{
                    throw new Error('WebRTC disabled for privacy');
                }};
                
                const originalCreateOffer = RTCPeerConnection.prototype.createOffer;
                RTCPeerConnection.prototype.createOffer = function() {{
                    return Promise.reject(new Error('WebRTC disabled for privacy'));
                }};
            }}
            
            // Mouse and keyboard event simulation
            let mouseMovements = 0;
            let lastMouseMove = Date.now();
            
            document.addEventListener('mousemove', () => {{
                mouseMovements++;
                lastMouseMove = Date.now();
            }});
            
            // Behavior tracking
            window.behaviorMetrics = {{
                mouseMovements: () => mouseMovements,
                timeSinceLastMove: () => Date.now() - lastMouseMove,
                sessionDuration: () => Date.now() - {int(time.time() * 1000)},
                isActive: () => Date.now() - lastMouseMove < 30000
            }};
            
            console.log('🛡️ StealthMaster AI v2.0 loaded - Device: {self.current_profile.device_type if self.current_profile else "unknown"}');
        }})();
        """