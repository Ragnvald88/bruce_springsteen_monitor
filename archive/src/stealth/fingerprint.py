"""
Enhanced Fingerprint Generator
Provides realistic, per-session randomized fingerprints
"""

import random
import hashlib
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import pytz
import numpy as np

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
                "gpu": "NVIDIA GeForce RTX 3070",
                "gpu_vendor_id": "0x10de",
                "gpu_device_id": "0x2484"
            },
            {
                "name": "MacBook Pro",
                "os": "macOS",
                "viewport": {"width": 1440, "height": 900},
                "screen": {"width": 2880, "height": 1800, "colorDepth": 30},
                "cores": 8,
                "memory": 16,
                "gpu": "Apple M1 Pro",
                "gpu_vendor_id": "0x106b",
                "gpu_device_id": "0x0001"
            },
            {
                "name": "Windows Laptop",
                "os": "Windows",
                "viewport": {"width": 1366, "height": 768},
                "screen": {"width": 1366, "height": 768, "colorDepth": 24},
                "cores": 4,
                "memory": 8,
                "gpu": "Intel Iris Xe Graphics",
                "gpu_vendor_id": "0x8086",
                "gpu_device_id": "0x9a49"
            },
            {
                "name": "Linux Desktop",
                "os": "Linux",
                "viewport": {"width": 1920, "height": 1080},
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "cores": 6,
                "memory": 32,
                "gpu": "AMD Radeon RX 6700 XT",
                "gpu_vendor_id": "0x1002",
                "gpu_device_id": "0x73df"
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
            "webgl": self._generate_webgl_fingerprint(profile),
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
            "battery": self._generate_battery_status(profile) or {
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
            "webrtc": self._generate_webrtc_fingerprint(profile),
            "sensors": self._generate_sensor_data(),
            "permissions": self._generate_permissions_state(),
            "memory": {
                "jsHeapSizeLimit": profile["memory"] * 1024 * 1024 * 1024,  # Convert GB to bytes
                "totalJSHeapSize": random.randint(10000000, 50000000),
                "usedJSHeapSize": random.randint(5000000, 30000000)
            },
            "gpu": {
                "vendor": profile.get("gpu_vendor_id", "0x0000"),
                "device": profile.get("gpu_device_id", "0x0000"),
                "powerPreference": "default"
            },
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
    
    def _generate_webgl_fingerprint(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate WebGL fingerprint data"""
        vendor = self._get_webgl_vendor(profile["gpu"])
        renderer = profile["gpu"]
        
        # Add noise to make it unique per session
        if self.seed:
            noise = random.Random(self.seed + 1).random()
        else:
            noise = random.random()
            
        # WebGL parameters
        return {
            "vendor": vendor,
            "renderer": renderer,
            "vendorId": profile.get("gpu_vendor_id", "0x0000"),
            "deviceId": profile.get("gpu_device_id", "0x0000"),
            "unmaskedVendor": vendor,
            "unmaskedRenderer": renderer,
            "shadings": {
                "maxVertexAttribs": 16,
                "maxVertexUniformVectors": random.choice([256, 512, 1024]),
                "maxVertexTextureImageUnits": random.choice([16, 32]),
                "maxVaryingVectors": random.choice([15, 30, 32]),
                "maxFragmentUniformVectors": random.choice([224, 1024, 2048]),
                "maxTextureImageUnits": random.choice([16, 32])  
            },
            "extensions": self._get_webgl_extensions(profile["os"]),
            "parameters": self._get_webgl_parameters(),
            "contextAttributes": {
                "alpha": True,
                "antialias": True,
                "depth": True,
                "desynchronized": False,
                "failIfMajorPerformanceCaveat": False,
                "powerPreference": "default",
                "premultipliedAlpha": True,
                "preserveDrawingBuffer": False,
                "stencil": False,
                "xrCompatible": False
            },
            "fingerprint": self._calculate_canvas_fingerprint(noise)
        }
    
    def _get_webgl_extensions(self, os: str) -> List[str]:
        """Get WebGL extensions based on OS"""
        # Common extensions
        common = [
            "ANGLE_instanced_arrays",
            "EXT_blend_minmax",
            "EXT_color_buffer_half_float",
            "EXT_disjoint_timer_query",
            "EXT_float_blend",
            "EXT_frag_depth",
            "EXT_shader_texture_lod",
            "EXT_texture_compression_bptc",
            "EXT_texture_compression_rgtc",
            "EXT_texture_filter_anisotropic",
            "EXT_sRGB",
            "KHR_parallel_shader_compile",
            "OES_element_index_uint",
            "OES_fbo_render_mipmap",
            "OES_standard_derivatives",
            "OES_texture_float",
            "OES_texture_float_linear",
            "OES_texture_half_float",
            "OES_texture_half_float_linear",
            "OES_vertex_array_object",
            "WEBGL_color_buffer_float",
            "WEBGL_compressed_texture_s3tc",
            "WEBGL_compressed_texture_s3tc_srgb",
            "WEBGL_debug_renderer_info",
            "WEBGL_debug_shaders",
            "WEBGL_depth_texture",
            "WEBGL_draw_buffers",
            "WEBGL_lose_context",
            "WEBGL_multi_draw"
        ]
        
        # OS-specific extensions
        if os == "Windows":
            common.extend([
                "EXT_texture_compression_s3tc",
                "EXT_texture_compression_s3tc_srgb"
            ])
        elif os == "macOS":
            common.extend([
                "WEBGL_compressed_texture_astc",
                "WEBGL_compressed_texture_etc",
                "WEBGL_compressed_texture_etc1"
            ])
            
        # Randomly exclude some extensions for variation
        if self.seed:
            rng = random.Random(self.seed + 2)
            num_to_exclude = rng.randint(0, 3)
            for _ in range(num_to_exclude):
                if len(common) > 20:
                    common.pop(rng.randint(10, len(common) - 1))
                    
        return sorted(common)
    
    def _get_webgl_parameters(self) -> Dict[str, Any]:
        """Get WebGL parameters"""
        return {
            "MAX_COMBINED_TEXTURE_IMAGE_UNITS": 32,
            "MAX_CUBE_MAP_TEXTURE_SIZE": 16384,
            "MAX_FRAGMENT_UNIFORM_VECTORS": 1024,
            "MAX_RENDERBUFFER_SIZE": 16384,
            "MAX_TEXTURE_IMAGE_UNITS": 16,
            "MAX_TEXTURE_SIZE": 16384,
            "MAX_VARYING_VECTORS": 30,
            "MAX_VERTEX_ATTRIBS": 16,
            "MAX_VERTEX_TEXTURE_IMAGE_UNITS": 16,
            "MAX_VERTEX_UNIFORM_VECTORS": 4096,
            "MAX_VIEWPORT_DIMS": [32767, 32767],
            "ALIASED_LINE_WIDTH_RANGE": [1, 1],
            "ALIASED_POINT_SIZE_RANGE": [1, 1024],
            "MAX_3D_TEXTURE_SIZE": 2048,
            "MAX_ARRAY_TEXTURE_LAYERS": 2048,
            "MAX_COLOR_ATTACHMENTS": 8,
            "MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS": 245760,
            "MAX_COMBINED_UNIFORM_BLOCKS": 70,
            "MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS": 266240,
            "MAX_DRAW_BUFFERS": 8,
            "MAX_ELEMENT_INDEX": 4294967295,
            "MAX_ELEMENTS_INDICES": 1073741824,
            "MAX_ELEMENTS_VERTICES": 1073741824,
            "MAX_FRAGMENT_INPUT_COMPONENTS": 128,
            "MAX_FRAGMENT_UNIFORM_BLOCKS": 14,
            "MAX_FRAGMENT_UNIFORM_COMPONENTS": 16384,
            "MAX_PROGRAM_TEXEL_OFFSET": 7,
            "MAX_SAMPLES": 16,
            "MAX_SERVER_WAIT_TIMEOUT": 0,
            "MAX_TEXTURE_LOD_BIAS": 16,
            "MAX_TRANSFORM_FEEDBACK_INTERLEAVED_COMPONENTS": 128,
            "MAX_TRANSFORM_FEEDBACK_SEPARATE_ATTRIBS": 4,
            "MAX_TRANSFORM_FEEDBACK_SEPARATE_COMPONENTS": 4,
            "MAX_UNIFORM_BLOCK_SIZE": 65536,
            "MAX_UNIFORM_BUFFER_BINDINGS": 72,
            "MAX_VARYING_COMPONENTS": 120,
            "MAX_VERTEX_OUTPUT_COMPONENTS": 128,
            "MAX_VERTEX_UNIFORM_BLOCKS": 14,
            "MAX_VERTEX_UNIFORM_COMPONENTS": 16384,
            "MIN_PROGRAM_TEXEL_OFFSET": -8
        }
    
    def _calculate_canvas_fingerprint(self, noise: float) -> str:
        """Calculate a unique canvas fingerprint"""
        # Simulate canvas rendering with slight variations
        base_values = [
            124.04347527516074 + noise * 0.1,
            124.08011107728962 - noise * 0.05,
            124.0229747820527 + noise * 0.08,
            11.526160387657628 - noise * 0.02
        ]
        
        # Convert to hash
        data_str = ''.join([f"{v:.10f}" for v in base_values])
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _generate_webrtc_fingerprint(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate WebRTC fingerprint data"""
        # Generate consistent but unique IP ranges
        if self.seed:
            rng = random.Random(self.seed + 3)
        else:
            rng = random
            
        # Local IP candidates
        local_ips = []
        
        # Add IPv4 local candidate
        local_ip = f"192.168.{rng.randint(0, 255)}.{rng.randint(2, 254)}"
        local_ips.append({
            "address": local_ip,
            "type": "host",
            "protocol": "udp",
            "port": rng.randint(50000, 60000)
        })
        
        # Sometimes add IPv6
        if rng.random() > 0.3:
            local_ips.append({
                "address": f"fe80::{rng.randint(1000, 9999)}:{rng.randint(1000, 9999)}:{rng.randint(1000, 9999)}:{rng.randint(1000, 9999)}",
                "type": "host",
                "protocol": "udp",
                "port": rng.randint(50000, 60000)
            })
            
        # STUN/TURN candidates (public IPs hidden)
        stun_candidates = []
        if rng.random() > 0.2:
            stun_candidates.append({
                "address": "obfuscated",
                "type": "srflx",
                "protocol": "udp",
                "port": rng.randint(50000, 60000)
            })
            
        return {
            "iceCandidates": {
                "local": local_ips,
                "stun": stun_candidates
            },
            "sdpFingerprint": self._generate_sdp_fingerprint(rng),
            "mediaDevices": self._get_media_devices(),
            "supportedCodecs": self._get_supported_codecs(profile["os"]),
            "dataChannelSupported": True,
            "maxDataChannelLimit": 65535
        }
    
    def _generate_sdp_fingerprint(self, rng) -> str:
        """Generate SDP fingerprint"""
        # Simulate SDP fingerprint format
        parts = []
        for _ in range(32):
            parts.append(f"{rng.randint(0, 255):02X}")
        return ":".join(parts)
    
    def _get_supported_codecs(self, os: str) -> Dict[str, List[str]]:
        """Get supported WebRTC codecs"""
        audio_codecs = [
            "opus/48000/2",
            "PCMU/8000",
            "PCMA/8000",
            "CN/8000",
            "CN/16000",
            "CN/32000",
            "telephone-event/48000",
            "telephone-event/32000",
            "telephone-event/16000",
            "telephone-event/8000"
        ]
        
        video_codecs = [
            "VP8",
            "VP9",
            "H264",
            "red",
            "ulpfec",
            "rtx"
        ]
        
        # Add AV1 for newer systems
        if os in ["Windows", "macOS"]:
            video_codecs.insert(2, "AV1")
            
        return {
            "audio": audio_codecs,
            "video": video_codecs
        }
    
    def _generate_battery_status(self, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate battery status (for laptops)"""
        # Only laptops have battery
        if "Laptop" in profile["name"] or "MacBook" in profile["name"]:
            if self.seed:
                rng = random.Random(self.seed + 4)
            else:
                rng = random
                
            charging = rng.random() > 0.6
            level = rng.uniform(0.2, 1.0) if not charging else rng.uniform(0.5, 1.0)
            
            return {
                "charging": charging,
                "chargingTime": 0 if charging else float('inf'),
                "dischargingTime": float('inf') if charging else rng.randint(3600, 14400),
                "level": round(level, 2)
            }
            
        return None
    
    def _generate_sensor_data(self) -> Dict[str, Any]:
        """Generate sensor API data"""
        return {
            "accelerometer": {
                "supported": True,
                "permission": "prompt"
            },
            "gyroscope": {
                "supported": True,
                "permission": "prompt"
            },
            "magnetometer": {
                "supported": False,
                "permission": "denied"
            },
            "ambientLight": {
                "supported": False,
                "permission": "denied"
            },
            "proximity": {
                "supported": False,
                "permission": "denied"
            }
        }
    
    def _generate_permissions_state(self) -> Dict[str, str]:
        """Generate permissions API state"""
        # Common permissions and their typical states
        permissions = {
            "geolocation": "prompt",
            "notifications": "prompt",
            "midi": "prompt",
            "camera": "prompt",
            "microphone": "prompt",
            "speaker": "granted",
            "device-info": "granted",
            "background-sync": "prompt",
            "bluetooth": "prompt",
            "persistent-storage": "prompt",
            "ambient-light-sensor": "denied",
            "accelerometer": "prompt",
            "gyroscope": "prompt",
            "magnetometer": "denied",
            "clipboard": "prompt",
            "screen-wake-lock": "prompt"
        }
        
        # Randomly grant some permissions to appear more natural
        if self.seed:
            rng = random.Random(self.seed + 5)
        else:
            rng = random
            
        # Sometimes grant notifications and geolocation
        if rng.random() > 0.7:
            permissions["notifications"] = "granted"
        if rng.random() > 0.8:
            permissions["geolocation"] = "granted"
            
        return permissions


# Global instance
fingerprint_generator = EnhancedFingerprintGenerator()

# Alias for backward compatibility
FingerprintGenerator = EnhancedFingerprintGenerator