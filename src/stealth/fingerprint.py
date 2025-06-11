"""
Enhanced Fingerprint Generator
Provides realistic, per-session randomized fingerprints
"""

import random
import hashlib
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import pytz

from ..utils.logging import get_logger

logger = get_logger(__name__)


class EnhancedFingerprintGenerator:
    """
    Fingerprint Generator with advanced randomization
    Creates consistent but unique fingerprints per session
    """
    
    def __init__(self):
        self.seed = None
        self._fingerprint_cache = {}
        self._session_id = None
        
        # Realistic device profiles
        self.device_profiles = [
            {
                "name": "Windows Gaming Desktop",
                "os": "Windows",
                "viewport": {"width": 1920, "height": 1080},
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "cores": 8,
                "memory": 16,
                "gpu": "NVIDIA GeForce RTX 3070"
            },
            {
                "name": "MacBook Pro",
                "os": "macOS",
                "viewport": {"width": 1440, "height": 900},
                "screen": {"width": 2880, "height": 1800, "colorDepth": 30},
                "cores": 8,
                "memory": 16,
                "gpu": "Apple M1 Pro"
            },
            {
                "name": "Windows Laptop",
                "os": "Windows",
                "viewport": {"width": 1366, "height": 768},
                "screen": {"width": 1366, "height": 768, "colorDepth": 24},
                "cores": 4,
                "memory": 8,
                "gpu": "Intel Iris Xe Graphics"
            },
            {
                "name": "Linux Desktop",
                "os": "Linux",
                "viewport": {"width": 1920, "height": 1080},
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "cores": 6,
                "memory": 32,
                "gpu": "AMD Radeon RX 6700 XT"
            }
        ]
        
        # Realistic browser versions
        self.browser_versions = {
            "Chrome": ["121.0.6167.85", "122.0.6261.94", "123.0.6312.58"],
            "Firefox": ["122.0", "123.0", "124.0"],
            "Edge": ["121.0.2277.83", "122.0.2365.92", "123.0.2420.81"]
        }
        
        # Common languages by region
        self.language_sets = [
            ["en-US", "en"],
            ["en-GB", "en"],
            ["it-IT", "it", "en"],
            ["de-DE", "de", "en"],
            ["fr-FR", "fr", "en"],
            ["es-ES", "es", "en"]
        ]
        
        # Timezone groups
        self.timezone_groups = {
            "US": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
            "Europe": ["Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome", "Europe/Madrid"],
            "Asia": ["Asia/Tokyo", "Asia/Shanghai", "Asia/Seoul", "Asia/Singapore"]
        }
    
    def set_session_id(self, session_id: str) -> None:
        """Set session ID for consistent fingerprinting within session"""
        self._session_id = session_id
        self.seed = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
        random.seed(self.seed)
        logger.debug(f"Set fingerprint session: {session_id}")
    
    def generate(self, consistent: bool = True) -> Dict[str, Any]:
        """
        Generate realistic browser fingerprint
        
        Args:
            consistent: If True, returns same fingerprint for same session
        """
        if consistent and self._session_id and self._session_id in self._fingerprint_cache:
            return self._fingerprint_cache[self._session_id]
        
        # Select random device profile
        profile = random.choice(self.device_profiles)
        
        # Select browser
        browser = random.choice(["Chrome", "Firefox", "Edge"])
        version = random.choice(self.browser_versions[browser])
        
        # Build user agent
        user_agent = self._build_user_agent(profile["os"], browser, version)
        
        # Select languages
        languages = random.choice(self.language_sets)
        
        # Select timezone from appropriate region
        region = "Europe" if any("it" in lang or "de" in lang or "fr" in lang or "es" in lang for lang in languages) else "US"
        timezone = random.choice(self.timezone_groups[region])
        
        # Generate canvas noise
        canvas_noise = random.uniform(0.0001, 0.001)
        
        # Build fingerprint
        fingerprint = {
            "userAgent": user_agent,
            "language": languages[0],
            "languages": languages,
            "platform": self._get_platform(profile["os"]),
            "viewport": profile["viewport"],
            "screen": profile["screen"],
            "hardwareConcurrency": profile["cores"],
            "deviceMemory": profile["memory"],
            "timezone": timezone,
            "timezoneOffset": self._get_timezone_offset(timezone),
            "webgl": {
                "vendor": self._get_webgl_vendor(profile["gpu"]),
                "renderer": profile["gpu"]
            },
            "canvas": {
                "noise": canvas_noise,
                "hash": hashlib.md5(f"{self._session_id}{canvas_noise}".encode()).hexdigest()
            },
            "fonts": self._get_font_list(profile["os"]),
            "audio": {
                "sampleRate": 48000,
                "channelCount": 2,
                "maxChannelCount": 2
            },
            "plugins": self._get_plugins(browser),
            "battery": {
                "charging": random.choice([True, True, False]),  # Most devices are plugged in
                "level": random.uniform(0.5, 1.0) if random.random() > 0.3 else 1.0
            },
            "connection": {
                "effectiveType": random.choice(["4g", "4g", "wifi"]),
                "rtt": random.randint(20, 150),
                "downlink": random.uniform(1.5, 10.0)
            },
            "mediaDevices": self._get_media_devices(),
            "touchSupport": self._get_touch_support(profile),
            "webdriver": False,  # Always false in V4
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache if consistent mode
        if consistent and self._session_id:
            self._fingerprint_cache[self._session_id] = fingerprint
        
        return fingerprint
    
    def _build_user_agent(self, os: str, browser: str, version: str) -> str:
        """Build realistic user agent string"""
        os_strings = {
            "Windows": "Windows NT 10.0; Win64; x64",
            "macOS": "Macintosh; Intel Mac OS X 10_15_7",
            "Linux": "X11; Linux x86_64"
        }
        
        if browser == "Chrome":
            return f"Mozilla/5.0 ({os_strings[os]}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        elif browser == "Firefox":
            return f"Mozilla/5.0 ({os_strings[os]}; rv:{version.split('.')[0]}.0) Gecko/20100101 Firefox/{version}"
        else:  # Edge
            return f"Mozilla/5.0 ({os_strings[os]}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}"
    
    def _get_platform(self, os: str) -> str:
        """Get platform string"""
        platforms = {
            "Windows": "Win32",
            "macOS": "MacIntel",
            "Linux": "Linux x86_64"
        }
        return platforms[os]
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """Get timezone offset in minutes"""
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        offset = now.utcoffset().total_seconds() / 60
        return int(offset)
    
    def _get_webgl_vendor(self, gpu: str) -> str:
        """Get WebGL vendor string"""
        if "NVIDIA" in gpu:
            return "NVIDIA Corporation"
        elif "AMD" in gpu or "Radeon" in gpu:
            return "Advanced Micro Devices, Inc."
        elif "Intel" in gpu:
            return "Intel Inc."
        elif "Apple" in gpu:
            return "Apple Inc."
        return "Unknown"
    
    def _get_font_list(self, os: str) -> List[str]:
        """Get realistic font list for OS"""
        base_fonts = [
            "Arial", "Arial Black", "Comic Sans MS", "Courier New",
            "Georgia", "Impact", "Times New Roman", "Trebuchet MS", "Verdana"
        ]
        
        os_fonts = {
            "Windows": ["Calibri", "Cambria", "Consolas", "Segoe UI", "Tahoma"],
            "macOS": ["Helvetica", "Helvetica Neue", "Lucida Grande", "Monaco", "SF Pro Display"],
            "Linux": ["DejaVu Sans", "Liberation Sans", "Noto Sans", "Ubuntu", "Droid Sans"]
        }
        
        return base_fonts + os_fonts.get(os, [])
    
    def _get_plugins(self, browser: str) -> List[Dict[str, str]]:
        """Get browser plugins"""
        if browser == "Chrome" or browser == "Edge":
            return [
                {
                    "name": "Chrome PDF Plugin",
                    "filename": "internal-pdf-viewer",
                    "description": "Portable Document Format"
                },
                {
                    "name": "Chrome PDF Viewer",
                    "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    "description": "Portable Document Format"
                }
            ]
        return []
    
    def _get_media_devices(self) -> List[Dict[str, str]]:
        """Get media devices"""
        devices = []
        
        # Audio inputs
        for i in range(random.randint(1, 3)):
            devices.append({
                "kind": "audioinput",
                "label": f"Microphone {i+1}",
                "groupId": hashlib.md5(f"audio-in-{i}".encode()).hexdigest()[:16]
            })
        
        # Audio outputs
        for i in range(random.randint(1, 2)):
            devices.append({
                "kind": "audiooutput",
                "label": f"Speaker {i+1}",
                "groupId": hashlib.md5(f"audio-out-{i}".encode()).hexdigest()[:16]
            })
        
        # Video inputs
        if random.random() > 0.3:  # 70% have cameras
            devices.append({
                "kind": "videoinput",
                "label": "Integrated Camera",
                "groupId": hashlib.md5("video-0".encode()).hexdigest()[:16]
            })
        
        return devices
    
    def _get_touch_support(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get touch support info"""
        # Laptops and desktops typically don't have touch
        has_touch = profile["name"] == "Windows Laptop" and random.random() > 0.7
        
        return {
            "maxTouchPoints": 10 if has_touch else 0,
            "touchEvent": has_touch,
            "touchStart": has_touch
        }
    
    def mutate_slightly(self, fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create slight mutation of existing fingerprint
        Useful for appearing as same device with minor changes
        """
        mutated = fingerprint.copy()
        
        # Slightly change viewport (window resize)
        if random.random() > 0.5:
            mutated["viewport"]["width"] += random.randint(-50, 50)
            mutated["viewport"]["height"] += random.randint(-50, 50)
        
        # Update timestamp
        mutated["timestamp"] = datetime.now().isoformat()
        
        # Slight battery change
        if "battery" in mutated and mutated["battery"]["level"] < 1.0:
            mutated["battery"]["level"] = max(0.1, min(1.0, 
                mutated["battery"]["level"] + random.uniform(-0.02, 0.02)
            ))
        
        # Network fluctuation
        if "connection" in mutated:
            mutated["connection"]["rtt"] = max(10, mutated["connection"]["rtt"] + random.randint(-10, 10))
        
        return mutated


# Global instance
fingerprint_generator = EnhancedFingerprintGenerator()

# Alias for backward compatibility
FingerprintGenerator = EnhancedFingerprintGenerator