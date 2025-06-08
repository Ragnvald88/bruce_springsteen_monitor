"""
Advanced Fingerprinting and Anti-Detection Module
Implements state-of-the-art evasion techniques
"""

import random
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

class AdvancedFingerprint:
    """Generate realistic browser fingerprints that evade detection"""
    
    # Realistic user agents from real browsers
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    ]
    
    # Realistic viewport sizes
    VIEWPORTS = [
        (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
        (1280, 720), (1600, 900), (1680, 1050), (2560, 1440)
    ]
    
    # Realistic screen resolutions (slightly larger than viewport)
    SCREEN_RESOLUTIONS = {
        (1920, 1080): (1920, 1080),
        (1366, 768): (1366, 768),
        (1536, 864): (1536, 864),
        (1440, 900): (1440, 960),
        (1280, 720): (1280, 800),
        (1600, 900): (1600, 900),
        (1680, 1050): (1680, 1050),
        (2560, 1440): (2560, 1440)
    }
    
    # WebGL vendor/renderer combinations
    WEBGL_VENDORS = [
        ("Intel Inc.", "Intel Iris OpenGL Engine"),
        ("Intel Inc.", "Intel(R) HD Graphics 630"),
        ("Intel Inc.", "Intel(R) UHD Graphics 630"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1070/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 2070/PCIe/SSE2"),
        ("ATI Technologies Inc.", "AMD Radeon Pro 5300M OpenGL Engine"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)"),
    ]
    
    # Canvas noise functions
    CANVAS_NOISE = """
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    
    HTMLCanvasElement.prototype.toDataURL = function(...args) {
        const context = this.getContext('2d');
        if (context) {
            const width = this.width;
            const height = this.height;
            const imageData = context.getImageData(0, 0, width, height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 2) - 1;
                imageData.data[i+1] += Math.floor(Math.random() * 2) - 1;
                imageData.data[i+2] += Math.floor(Math.random() * 2) - 1;
            }
            context.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, args);
    };
    """
    
    @classmethod
    def generate_fingerprint(cls) -> Dict[str, Any]:
        """Generate a complete browser fingerprint"""
        viewport = random.choice(cls.VIEWPORTS)
        screen = cls.SCREEN_RESOLUTIONS.get(viewport, viewport)
        webgl = random.choice(cls.WEBGL_VENDORS)
        
        # Generate consistent hardware concurrency based on system
        hardware_concurrency = random.choice([4, 8, 12, 16])
        
        # Device memory (in GB)
        device_memory = random.choice([4, 8, 16, 32])
        
        return {
            'user_agent': random.choice(cls.USER_AGENTS),
            'viewport': {'width': viewport[0], 'height': viewport[1]},
            'screen': {'width': screen[0], 'height': screen[1]},
            'device_scale_factor': random.choice([1, 1.25, 1.5, 2]),
            'webgl_vendor': webgl[0],
            'webgl_renderer': webgl[1],
            'hardware_concurrency': hardware_concurrency,
            'device_memory': device_memory,
            'max_touch_points': 0,  # Desktop browsers
            'color_depth': 24,
            'pixel_depth': 24,
            'timezone': cls._get_random_timezone(),
            'language': cls._get_random_language(),
            'platform': cls._get_platform_from_ua(random.choice(cls.USER_AGENTS)),
            'plugins': cls._generate_plugins(),
            'audio_context_noise': random.uniform(0.00001, 0.00009),
            'canvas_noise': True
        }
    
    @staticmethod
    def _get_random_timezone() -> str:
        """Get random realistic timezone"""
        timezones = [
            'America/New_York', 'America/Chicago', 'America/Los_Angeles',
            'America/Denver', 'America/Phoenix', 'America/Detroit',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin',
            'Europe/Rome', 'Europe/Madrid', 'Europe/Amsterdam'
        ]
        return random.choice(timezones)
    
    @staticmethod
    def _get_random_language() -> str:
        """Get random language based on timezone"""
        languages = ['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'nl-NL']
        return random.choice(languages)
    
    @staticmethod
    def _get_platform_from_ua(user_agent: str) -> str:
        """Extract platform from user agent"""
        if 'Windows' in user_agent:
            return 'Win32'
        elif 'Mac' in user_agent:
            return 'MacIntel'
        elif 'Linux' in user_agent:
            return 'Linux x86_64'
        return 'Win32'
    
    @staticmethod
    def _generate_plugins() -> List[Dict[str, str]]:
        """Generate realistic plugin list"""
        base_plugins = [
            {
                "name": "Chrome PDF Plugin",
                "description": "Portable Document Format",
                "filename": "internal-pdf-viewer"
            },
            {
                "name": "Chrome PDF Viewer",
                "description": "Portable Document Format",
                "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai"
            },
            {
                "name": "Native Client",
                "description": "Native Client Executable",
                "filename": "internal-nacl-plugin"
            }
        ]
        # Randomly include/exclude plugins
        return [p for p in base_plugins if random.random() > 0.3]
    
    @classmethod
    def get_stealth_script(cls, fingerprint: Dict[str, Any]) -> str:
        """Generate complete stealth script for injection"""
        return f"""
        // Advanced Stealth Script
        (() => {{
            // Remove webdriver
            delete Object.getPrototypeOf(navigator).webdriver;
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
                configurable: false
            }});
            
            // Set hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint['hardware_concurrency']}
            }});
            
            // Set device memory
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint['device_memory']}
            }});
            
            // Override WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fingerprint['webgl_vendor']}';
                if (parameter === 37446) return '{fingerprint['webgl_renderer']}';
                return getParameter.apply(this, arguments);
            }};
            
            // Platform
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint['platform']}'
            }});
            
            // Plugins with proper behavior
            Object.defineProperty(navigator, 'plugins', {{
                get: () => {{
                    const plugins = {json.dumps(fingerprint['plugins'])};
                    const arr = [];
                    plugins.forEach((p, i) => {{
                        const plugin = {{
                            description: p.description,
                            filename: p.filename,
                            length: 1,
                            name: p.name,
                            [0]: {{
                                description: p.description,
                                enabledPlugin: {{}},
                                suffixes: "pdf",
                                type: "application/pdf"
                            }}
                        }};
                        arr[i] = plugin;
                        arr[p.name] = plugin;
                    }});
                    arr.item = (i) => arr[i];
                    arr.namedItem = (name) => arr[name];
                    arr.refresh = () => {{}};
                    return arr;
                }}
            }});
            
            // Battery API spoofing
            if ('getBattery' in navigator) {{
                navigator.getBattery = async () => ({{
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.99,
                    onchargingchange: null,
                    onchargingtimechange: null,
                    ondischargingtimechange: null,
                    onlevelchange: null
                }});
            }}
            
            // Chrome object
            if (!window.chrome) {{
                window.chrome = {{}};
            }}
            window.chrome.runtime = {{
                PlatformOs: {{
                    MAC: 'mac',
                    WIN: 'win',
                    ANDROID: 'android',
                    CROS: 'cros',
                    LINUX: 'linux',
                    OPENBSD: 'openbsd'
                }},
                PlatformArch: {{
                    ARM: 'arm',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64',
                    MIPS: 'mips',
                    MIPS64: 'mips64'
                }},
                PlatformNaclArch: {{
                    ARM: 'arm',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64',
                    MIPS: 'mips',
                    MIPS64: 'mips64'
                }},
                connect: () => {{}},
                sendMessage: () => {{}}
            }};
            
            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {{
                if (parameters.name === 'notifications') {{
                    return Promise.resolve({{ state: 'default' }});
                }}
                return originalQuery(parameters);
            }};
            
            // Audio context fingerprinting protection
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {{
                const originalCreateOscillator = AudioContext.prototype.createOscillator;
                AudioContext.prototype.createOscillator = function() {{
                    const oscillator = originalCreateOscillator.apply(this, arguments);
                    const originalConnect = oscillator.connect;
                    oscillator.connect = function() {{
                        arguments[0].gain.value += {fingerprint['audio_context_noise']};
                        return originalConnect.apply(this, arguments);
                    }};
                    return oscillator;
                }};
            }}
            
            {cls.CANVAS_NOISE if fingerprint['canvas_noise'] else ''}
            
            // Console detection evasion
            let devtools = {{open: false, orientation: null}};
            setInterval(() => {{
                if (window.outerHeight - window.innerHeight > 200 || 
                    window.outerWidth - window.innerWidth > 200) {{
                    // Console might be open, but don't change behavior
                }}
            }}, 500);
        }})();
        """