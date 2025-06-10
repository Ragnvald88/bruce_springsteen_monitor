# stealthmaster/stealth/fingerprint.py
"""Advanced fingerprint generation for browser spoofing."""

import random
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from config import BrowserOptions


class FingerprintGenerator:
    """Generates realistic browser fingerprints for stealth."""
    
    # Realistic user agents (2024-2025 versions)
    USER_AGENTS = {
        "windows": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        ],
        "mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        ],
        "linux": [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
        ],
    }
    
    # Common viewport sizes
    VIEWPORTS = [
        (1920, 1080),  # Full HD
        (1366, 768),   # Common laptop
        (1536, 864),   # Common laptop
        (1440, 900),   # MacBook
        (1280, 720),   # HD
        (1600, 900),   # Common desktop
        (1680, 1050),  # Older MacBook
        (2560, 1440),  # QHD
    ]
    
    # WebGL vendors and renderers
    WEBGL_DATA = [
        ("Intel Inc.", "Intel Iris OpenGL Engine"),
        ("Intel Inc.", "Intel(R) HD Graphics 630"),
        ("Intel Inc.", "Intel(R) UHD Graphics 630"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1060/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce GTX 1070/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 3060/PCIe/SSE2"),
        ("NVIDIA Corporation", "NVIDIA GeForce RTX 4070/PCIe/SSE2"),
        ("AMD", "AMD Radeon Pro 5300M OpenGL Engine"),
        ("Google Inc. (NVIDIA Corporation)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0)"),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"),
    ]
    
    # Common fonts by platform
    FONTS = {
        "windows": [
            "Arial", "Arial Black", "Arial Narrow", "Book Antiqua", "Bookman Old Style",
            "Calibri", "Cambria", "Cambria Math", "Century", "Century Gothic",
            "Comic Sans MS", "Consolas", "Courier", "Courier New", "Georgia",
            "Helvetica", "Impact", "Lucida Console", "Lucida Sans Unicode", "Microsoft Sans Serif",
            "Palatino Linotype", "Segoe UI", "Tahoma", "Times", "Times New Roman",
            "Trebuchet MS", "Verdana",
        ],
        "mac": [
            "American Typewriter", "Arial", "Arial Black", "Arial Narrow", "Arial Rounded MT Bold",
            "Arial Unicode MS", "Avenir", "Avenir Next", "Avenir Next Condensed", "Baskerville",
            "Big Caslon", "Bodoni 72", "Bradley Hand", "Chalkboard", "Cochin",
            "Comic Sans MS", "Courier", "Courier New", "Futura", "Geneva",
            "Georgia", "Gill Sans", "Helvetica", "Helvetica Neue", "Hoefler Text",
            "Impact", "Lucida Grande", "Marker Felt", "Monaco", "Optima",
            "Palatino", "SF Pro Display", "SF Pro Text", "Tahoma", "Times",
            "Times New Roman", "Trebuchet MS", "Verdana",
        ],
        "linux": [
            "Arial", "Bitstream Vera Sans", "Bitstream Vera Serif", "Courier New", "DejaVu Sans",
            "DejaVu Sans Mono", "DejaVu Serif", "FreeMono", "FreeSans", "FreeSerif",
            "Liberation Mono", "Liberation Sans", "Liberation Serif", "Noto Sans", "Noto Serif",
            "Ubuntu", "Ubuntu Condensed", "Ubuntu Mono",
        ],
    }
    
    # Geolocation data for Italian cities
    GEO_LOCATIONS = [
        {"latitude": 41.9028, "longitude": 12.4964, "city": "Rome"},
        {"latitude": 45.4642, "longitude": 9.1900, "city": "Milan"},
        {"latitude": 40.8518, "longitude": 14.2681, "city": "Naples"},
        {"latitude": 45.0703, "longitude": 7.6869, "city": "Turin"},
        {"latitude": 43.7696, "longitude": 11.2558, "city": "Florence"},
        {"latitude": 44.4949, "longitude": 11.3426, "city": "Bologna"},
        {"latitude": 45.4384, "longitude": 12.3155, "city": "Venice"},
        {"latitude": 45.4064, "longitude": 11.8768, "city": "Padua"},
    ]
    
    def __init__(self):
        """Initialize fingerprint generator."""
        self._fingerprint_cache = {}
    
    def generate(self, platform: str = "windows") -> Dict[str, Any]:
        """
        Generate a complete browser fingerprint.
        
        Args:
            platform: Target platform (windows, mac, linux)
            
        Returns:
            Complete fingerprint configuration
        """
        # Generate unique ID
        fingerprint_id = str(uuid.uuid4())
        
        # Select user agent
        user_agent = random.choice(self.USER_AGENTS.get(platform, self.USER_AGENTS["windows"]))
        
        # Select viewport
        viewport = random.choice(self.VIEWPORTS)
        
        # Calculate screen size (slightly larger than viewport)
        screen_width = viewport[0] + random.randint(0, 200)
        screen_height = viewport[1] + random.randint(100, 300)
        
        # Select WebGL data
        webgl_vendor, webgl_renderer = random.choice(self.WEBGL_DATA)
        
        # Select geolocation
        geo = random.choice(self.GEO_LOCATIONS)
        
        # Build fingerprint
        fingerprint = {
            "id": fingerprint_id,
            "platform": platform,
            "user_agent": user_agent,
            "viewport": {
                "width": viewport[0],
                "height": viewport[1],
            },
            "screen": {
                "width": screen_width,
                "height": screen_height,
                "availWidth": viewport[0],
                "availHeight": viewport[1],
                "colorDepth": 24,
                "pixelDepth": 24,
            },
            "webgl": {
                "vendor": webgl_vendor,
                "renderer": webgl_renderer,
                "version": "WebGL 2.0",
                "shadingLanguageVersion": "WebGL GLSL ES 3.00",
            },
            "canvas": {
                "noise": True,
                "noise_factor": random.uniform(0.00001, 0.00005),
            },
            "audio": {
                "noise": True,
                "noise_factor": random.uniform(0.00001, 0.00009),
                "sample_rate": random.choice([44100, 48000]),
            },
            "fonts": self._select_fonts(platform),
            "navigator": {
                "language": random.choice(["it-IT", "en-US", "en-GB"]),
                "languages": ["it-IT", "it", "en-US", "en"],
                "platform": self._get_navigator_platform(platform),
                "hardwareConcurrency": random.choice([4, 8, 12, 16]),
                "deviceMemory": random.choice([4, 8, 16, 32]),
                "maxTouchPoints": 0,  # Desktop
                "cookieEnabled": True,
                "doNotTrack": random.choice([None, "1"]),
                "appCodeName": "Mozilla",
                "appName": "Netscape",
                "vendor": self._get_vendor(user_agent),
                "vendorSub": "",
                "productSub": "20030107",
            },
            "timezone": {
                "id": "Europe/Rome",
                "offset": -60,  # UTC+1
            },
            "geo": geo,
            "plugins": self._generate_plugins(),
            "battery": {
                "charging": True,
                "chargingTime": 0,
                "dischargingTime": float("inf"),
                "level": 0.99,
            },
            "network": {
                "effectiveType": "4g",
                "rtt": random.randint(50, 150),
                "downlink": random.uniform(5.0, 20.0),
                "saveData": False,
            },
            "device_scale_factor": random.choice([1, 1.25, 1.5, 2]),
            "color_gamut": random.choice(["srgb", "p3", "rec2020"]),
            "reduced_motion": False,
            "prefers_color_scheme": "light",
            "generated_at": datetime.now().isoformat(),
        }
        
        # Cache fingerprint
        self._fingerprint_cache[fingerprint_id] = fingerprint
        
        return fingerprint
    
    def _select_fonts(self, platform: str) -> List[str]:
        """Select realistic fonts for platform."""
        available_fonts = self.FONTS.get(platform, self.FONTS["windows"])
        
        # Select 60-80% of available fonts (realistic)
        num_fonts = int(len(available_fonts) * random.uniform(0.6, 0.8))
        selected = random.sample(available_fonts, num_fonts)
        
        # Always include common fonts
        common = ["Arial", "Courier New", "Times New Roman", "Verdana"]
        for font in common:
            if font in available_fonts and font not in selected:
                selected.append(font)
        
        return sorted(selected)
    
    def _get_navigator_platform(self, platform: str) -> str:
        """Get navigator.platform value for OS."""
        platform_map = {
            "windows": "Win32",
            "mac": "MacIntel",
            "linux": "Linux x86_64",
        }
        return platform_map.get(platform, "Win32")
    
    def _get_vendor(self, user_agent: str) -> str:
        """Get navigator.vendor based on browser."""
        if "Chrome" in user_agent:
            return "Google Inc."
        elif "Firefox" in user_agent:
            return ""
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            return "Apple Computer, Inc."
        return "Google Inc."
    
    def _generate_plugins(self) -> List[Dict[str, str]]:
        """Generate realistic plugin list."""
        base_plugins = [
            {
                "name": "Chrome PDF Plugin",
                "description": "Portable Document Format",
                "filename": "internal-pdf-viewer",
                "mimeTypes": ["application/x-google-chrome-pdf"],
            },
            {
                "name": "Chrome PDF Viewer",
                "description": "Portable Document Format",
                "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                "mimeTypes": ["application/pdf"],
            },
            {
                "name": "Native Client",
                "description": "Native Client Executable",
                "filename": "internal-nacl-plugin",
                "mimeTypes": ["application/x-nacl", "application/x-pnacl"],
            },
        ]
        
        # Randomly include/exclude plugins
        return [p for p in base_plugins if random.random() > 0.3]
    
    def get_cached(self, fingerprint_id: str) -> Optional[Dict[str, Any]]:
        """Get cached fingerprint by ID."""
        return self._fingerprint_cache.get(fingerprint_id)
    
    def rotate_fingerprint(self, current_id: str) -> Dict[str, Any]:
        """
        Rotate to a new fingerprint while maintaining platform consistency.
        
        Args:
            current_id: Current fingerprint ID
            
        Returns:
            New fingerprint
        """
        current = self.get_cached(current_id)
        if current:
            platform = current.get("platform", "windows")
        else:
            platform = "windows"
        
        return self.generate(platform)

# stealthmaster/stealth/injections.py
"""Stealth JavaScript injections for anti-detection."""

import json
from typing import Dict, Any, List


class StealthInjections:
    """Manages all JavaScript injections for stealth."""
    
    def get_context_init_script(self) -> str:
        """Get initialization script for browser context."""
        return """
        // Context initialization
        (() => {
            'use strict';
            
            // Mark as stealth context
            window.__stealthmaster__ = true;
            
            // Override Object.prototype.toString to hide modifications
            const originalToString = Object.prototype.toString;
            Object.prototype.toString = function() {
                if (this === navigator) return '[object Navigator]';
                if (this === window.chrome) return '[object Object]';
                return originalToString.call(this);
            };
        })();
        """
    
    def get_webdriver_evasion(self) -> str:
        """Complete webdriver property removal."""
        return """
        // Webdriver evasion
        (() => {
            'use strict';
            
            // Delete webdriver from all possible locations
            delete Object.getPrototypeOf(navigator).webdriver;
            delete navigator.webdriver;
            delete navigator.__proto__.webdriver;
            
            // Create new navigator prototype without webdriver
            const newProto = Object.create(Object.getPrototypeOf(navigator));
            delete newProto.webdriver;
            Object.setPrototypeOf(navigator, newProto);
            
            // Define as undefined (can't be detected)
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                set: () => {},
                enumerable: false,
                configurable: false
            });
            
            // Also remove from window
            delete window.navigator.webdriver;
            
            // Remove CDP runtime artifacts
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        })();
        """
    
    def get_chrome_runtime_evasion(self) -> str:
        """Create convincing Chrome runtime object."""
        return """
        // Chrome runtime evasion
        (() => {
            'use strict';
            
            if (!window.chrome) {
                window.chrome = {};
            }
            
            // App
            window.chrome.app = {
                isInstalled: false,
                InstallState: {
                    DISABLED: 'disabled',
                    INSTALLED: 'installed', 
                    NOT_INSTALLED: 'not_installed'
                },
                RunningState: {
                    CANNOT_RUN: 'cannot_run',
                    READY_TO_RUN: 'ready_to_run',
                    RUNNING: 'running'
                },
                getDetails: () => null,
                getIsInstalled: () => false,
                runningState: () => 'cannot_run'
            };
            
            // Runtime with all properties
            window.chrome.runtime = {
                OnInstalledReason: {
                    CHROME_UPDATE: 'chrome_update',
                    INSTALL: 'install',
                    SHARED_MODULE_UPDATE: 'shared_module_update',
                    UPDATE: 'update'
                },
                OnRestartRequiredReason: {
                    APP_UPDATE: 'app_update',
                    OS_UPDATE: 'os_update',
                    PERIODIC: 'periodic'
                },
                PlatformArch: {
                    ARM: 'arm',
                    ARM64: 'arm64',
                    MIPS: 'mips',
                    MIPS64: 'mips64',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64'
                },
                PlatformNaclArch: {
                    ARM: 'arm',
                    MIPS: 'mips',
                    MIPS64: 'mips64',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64'
                },
                PlatformOs: {
                    ANDROID: 'android',
                    CROS: 'cros',
                    LINUX: 'linux',
                    MAC: 'mac',
                    OPENBSD: 'openbsd',
                    WIN: 'win'
                },
                RequestUpdateCheckStatus: {
                    NO_UPDATE: 'no_update',
                    THROTTLED: 'throttled',
                    UPDATE_AVAILABLE: 'update_available'
                },
                id: undefined,
                getManifest: undefined,
                connect: () => {},
                sendMessage: () => {}
            };
            
            // LoadTimes
            const timing = performance.timing;
            const loadTimes = {
                get requestTime() { return timing.navigationStart / 1000; },
                get startLoadTime() { return timing.fetchStart / 1000; },
                get commitLoadTime() { return timing.responseStart / 1000; },
                get finishDocumentLoadTime() { return timing.domContentLoadedEventEnd / 1000; },
                get finishLoadTime() { return timing.loadEventEnd / 1000; },
                get firstPaintTime() { return (timing.responseStart + 100) / 1000; },
                get firstPaintAfterLoadTime() { return 0; },
                get navigationType() { return 'Other'; },
                get wasFetchedViaSpdy() { return true; },
                get wasNpnNegotiated() { return true; },
                get npnNegotiatedProtocol() { return 'h2'; },
                get wasAlternateProtocolAvailable() { return false; },
                get connectionInfo() { return 'h2'; }
            };
            
            window.chrome.loadTimes = function() { return loadTimes; };
            
            // CSI
            window.chrome.csi = function() {
                return {
                    onloadT: timing.loadEventEnd,
                    pageT: Date.now() - timing.navigationStart,
                    startE: timing.navigationStart,
                    tran: 15
                };
            };
        })();
        """
    
    def get_permission_evasion(self) -> str:
        """Override permission API to appear legitimate."""
        return """
        // Permission API evasion
        (() => {
            'use strict';
            
            if (!navigator.permissions) return;
            
            const originalQuery = navigator.permissions.query.bind(navigator.permissions);
            
            navigator.permissions.query = async function(descriptor) {
                // Common permissions that should be in specific states
                const permissionStates = {
                    'geolocation': 'granted',
                    'notifications': 'default',
                    'push': 'default',
                    'midi': 'default',
                    'camera': 'default',
                    'microphone': 'default',
                    'background-sync': 'granted',
                    'ambient-light-sensor': 'default',
                    'accelerometer': 'default',
                    'gyroscope': 'default',
                    'magnetometer': 'default',
                    'clipboard-read': 'default',
                    'clipboard-write': 'default'
                };
                
                const name = descriptor.name || descriptor;
                
                if (name in permissionStates) {
                    return {
                        name: name,
                        state: permissionStates[name],
                        onchange: null,
                        addEventListener: () => {},
                        removeEventListener: () => {},
                        dispatchEvent: () => true
                    };
                }
                
                try {
                    return await originalQuery(descriptor);
                } catch (e) {
                    return {
                        name: name,
                        state: 'default',
                        onchange: null
                    };
                }
            };
        })();
        """
    
    def get_plugin_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Create realistic plugin array."""
        plugins = fingerprint.get("plugins", [])
        plugins_json = json.dumps(plugins)
        
        return f"""
        // Plugin evasion
        (() => {{
            'use strict';
            
            const pluginsData = {plugins_json};
            
            // Create proper Plugin objects
            const plugins = pluginsData.map(data => {{
                const plugin = Object.create(Plugin.prototype);
                
                Object.defineProperties(plugin, {{
                    name: {{ value: data.name, enumerable: true }},
                    description: {{ value: data.description, enumerable: true }},
                    filename: {{ value: data.filename, enumerable: true }},
                    length: {{ value: data.mimeTypes.length, enumerable: true }}
                }});
                
                // Add mime types
                data.mimeTypes.forEach((mimeType, index) => {{
                    const mime = Object.create(MimeType.prototype);
                    Object.defineProperties(mime, {{
                        type: {{ value: mimeType, enumerable: true }},
                        suffixes: {{ value: 'pdf', enumerable: true }},
                        description: {{ value: data.description, enumerable: true }},
                        enabledPlugin: {{ value: plugin, enumerable: true }}
                    }});
                    
                    plugin[index] = mime;
                    plugin[mimeType] = mime;
                }});
                
                // Methods
                plugin.item = function(index) {{ return this[index] || null; }};
                plugin.namedItem = function(name) {{ return this[name] || null; }};
                
                return plugin;
            }});
            
            // Create PluginArray
            const pluginArray = Object.create(PluginArray.prototype);
            
            plugins.forEach((plugin, index) => {{
                pluginArray[index] = plugin;
                pluginArray[plugin.name] = plugin;
            }});
            
            Object.defineProperties(pluginArray, {{
                length: {{ value: plugins.length, enumerable: true }}
            }});
            
            pluginArray.item = function(index) {{ return this[index] || null; }};
            pluginArray.namedItem = function(name) {{ return this[name] || null; }};
            pluginArray.refresh = function() {{}};
            
            // Override navigator.plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => pluginArray,
                enumerable: true,
                configurable: false
            }});
            
            // Also set mimeTypes
            const mimeTypes = [];
            plugins.forEach(plugin => {{
                for (let i = 0; i < plugin.length; i++) {{
                    mimeTypes.push(plugin[i]);
                }}
            }});
            
            const mimeTypeArray = Object.create(MimeTypeArray.prototype);
            mimeTypes.forEach((mime, index) => {{
                mimeTypeArray[index] = mime;
                mimeTypeArray[mime.type] = mime;
            }});
            
            Object.defineProperty(mimeTypeArray, 'length', {{
                value: mimeTypes.length
            }});
            
            mimeTypeArray.item = function(index) {{ return this[index] || null; }};
            mimeTypeArray.namedItem = function(name) {{ return this[name] || null; }};
            
            Object.defineProperty(navigator, 'mimeTypes', {{
                get: () => mimeTypeArray,
                enumerable: true,
                configurable: false
            }});
        }})();
        """
    
    def get_webgl_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override WebGL parameters."""
        webgl = fingerprint.get("webgl", {})
        vendor = webgl.get("vendor", "Intel Inc.")
        renderer = webgl.get("renderer", "Intel Iris OpenGL Engine")
        
        return f"""
        // WebGL evasion
        (() => {{
            'use strict';
            
            const vendor = '{vendor}';
            const renderer = '{renderer}';
            
            // WebGL 1.0
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return vendor;   // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) return renderer; // UNMASKED_RENDERER_WEBGL
                if (parameter === 7937) return 'WebKit WebGL'; // VERSION
                if (parameter === 35724) return 'WebGL GLSL ES 1.0'; // SHADING_LANGUAGE_VERSION
                return getParameter.apply(this, arguments);
            }};
            
            // WebGL 2.0
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) return vendor;
                    if (parameter === 37446) return renderer;
                    if (parameter === 7937) return 'WebGL 2.0';
                    if (parameter === 35724) return 'WebGL GLSL ES 3.00';
                    return getParameter2.apply(this, arguments);
                }};
            }}
            
            // Also override getSupportedExtensions
            const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
            WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
                const extensions = getSupportedExtensions.apply(this, arguments);
                // Add/remove some extensions for realism
                if (!extensions.includes('WEBGL_debug_renderer_info')) {{
                    extensions.push('WEBGL_debug_renderer_info');
                }}
                return extensions;
            }};
        }})();
        """
    
    def get_canvas_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Add noise to canvas fingerprinting."""
        canvas = fingerprint.get("canvas", {})
        noise_factor = canvas.get("noise_factor", 0.00001)
        
        return f"""
        // Canvas fingerprinting protection
        (() => {{
            'use strict';
            
            const noiseFactor = {noise_factor};
            
            // Helper to add noise
            const addNoise = (value) => {{
                const noise = (Math.random() - 0.5) * noiseFactor * 255;
                return Math.max(0, Math.min(255, value + noise));
            }};
            
            // Override toDataURL
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                const context = this.getContext('2d');
                if (context && this.width > 0 && this.height > 0) {{
                    try {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = addNoise(imageData.data[i]);     // R
                            imageData.data[i+1] = addNoise(imageData.data[i+1]); // G
                            imageData.data[i+2] = addNoise(imageData.data[i+2]); // B
                            // Alpha channel unchanged
                        }}
                        context.putImageData(imageData, 0, 0);
                    }} catch (e) {{
                        // Ignore errors (cross-origin, etc)
                    }}
                }}
                return originalToDataURL.apply(this, args);
            }};
            
            // Override toBlob
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {{
                const context = this.getContext('2d');
                if (context && this.width > 0 && this.height > 0) {{
                    try {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = addNoise(imageData.data[i]);
                            imageData.data[i+1] = addNoise(imageData.data[i+1]);
                            imageData.data[i+2] = addNoise(imageData.data[i+2]);
                        }}
                        context.putImageData(imageData, 0, 0);
                    }} catch (e) {{
                        // Ignore errors
                    }}
                }}
                return originalToBlob.call(this, callback, ...args);
            }};
            
            // Override getImageData
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                const imageData = originalGetImageData.apply(this, args);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = addNoise(imageData.data[i]);
                    imageData.data[i+1] = addNoise(imageData.data[i+1]);
                    imageData.data[i+2] = addNoise(imageData.data[i+2]);
                }}
                return imageData;
            }};
        }})();
        """
    
    def get_audio_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Add noise to audio fingerprinting."""
        audio = fingerprint.get("audio", {})
        noise_factor = audio.get("noise_factor", 0.00001)
        
        return f"""
        // Audio fingerprinting protection
        (() => {{
            'use strict';
            
            const noiseFactor = {noise_factor};
            
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            
            // Override createOscillator
            const originalCreateOscillator = AudioContext.prototype.createOscillator;
            AudioContext.prototype.createOscillator = function() {{
                const oscillator = originalCreateOscillator.apply(this, arguments);
                const originalConnect = oscillator.connect;
                
                oscillator.connect = function(...args) {{
                    // Add slight frequency variation
                    if (oscillator.frequency && oscillator.frequency.value) {{
                        oscillator.frequency.value *= (1 + (Math.random() - 0.5) * noiseFactor);
                    }}
                    return originalConnect.apply(this, args);
                }};
                
                return oscillator;
            }};
            
            // Override createAnalyser
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            AudioContext.prototype.createAnalyser = function() {{
                const analyser = originalCreateAnalyser.apply(this, arguments);
                
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {{
                    originalGetFloatFrequencyData.apply(this, arguments);
                    for (let i = 0; i < array.length; i++) {{
                        array[i] += (Math.random() - 0.5) * noiseFactor;
                    }}
                }};
                
                const originalGetByteFrequencyData = analyser.getByteFrequencyData;
                analyser.getByteFrequencyData = function(array) {{
                    originalGetByteFrequencyData.apply(this, arguments);
                    for (let i = 0; i < array.length; i++) {{
                        array[i] = Math.max(0, Math.min(255, 
                            array[i] + (Math.random() - 0.5) * noiseFactor * 255));
                    }}
                }};
                
                return analyser;
            }};
        }})();
        """
    
    def get_navigator_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override navigator properties."""
        nav = fingerprint.get("navigator", {})
        
        return f"""
        // Navigator properties evasion
        (() => {{
            'use strict';
            
            const navProps = {json.dumps(nav)};
            
            // Apply each property
            for (const [prop, value] of Object.entries(navProps)) {{
                try {{
                    if (value !== null && value !== undefined) {{
                        Object.defineProperty(navigator, prop, {{
                            get: () => value,
                            enumerable: true,
                            configurable: false
                        }});
                    }}
                }} catch (e) {{
                    // Some properties might be read-only
                }}
            }}
            
            // Special handling for languages
            if (navProps.languages) {{
                Object.defineProperty(navigator, 'languages', {{
                    get: () => Object.freeze([...navProps.languages]),
                    enumerable: true,
                    configurable: false
                }});
            }}
        }})();
        """
    
    def get_screen_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override screen properties."""
        screen = fingerprint.get("screen", {})
        
        return f"""
        // Screen properties evasion
        (() => {{
            'use strict';
            
            const screenProps = {json.dumps(screen)};
            
            // Apply screen properties
            for (const [prop, value] of Object.entries(screenProps)) {{
                try {{
                    Object.defineProperty(screen, prop, {{
                        get: () => value,
                        enumerable: true,
                        configurable: false
                    }});
                }} catch (e) {{
                    // Some properties might be read-only
                }}
            }}
            
            // Also set window.screen
            for (const [prop, value] of Object.entries(screenProps)) {{
                try {{
                    Object.defineProperty(window.screen, prop, {{
                        get: () => value,
                        enumerable: true,
                        configurable: false
                    }});
                }} catch (e) {{
                    // Ignore
                }}
            }}
        }})();
        """
    
    def get_timezone_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override timezone-related functions."""
        timezone = fingerprint.get("timezone", {})
        offset = timezone.get("offset", -60)  # Default to Rome (UTC+1)
        
        return f"""
        // Timezone evasion
        (() => {{
            'use strict';
            
            const timezoneOffset = {offset};
            
            // Override getTimezoneOffset
            Date.prototype.getTimezoneOffset = function() {{
                return timezoneOffset;
            }};
            
            // Override Intl.DateTimeFormat
            const OriginalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = new Proxy(OriginalDateTimeFormat, {{
                construct(target, args) {{
                    if (args.length > 1 && args[1] && !args[1].timeZone) {{
                        args[1].timeZone = 'Europe/Rome';
                    }}
                    return new target(...args);
                }}
            }});
            
            // Override resolvedOptions
            const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
            Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
                const options = originalResolvedOptions.apply(this, arguments);
                options.timeZone = 'Europe/Rome';
                return options;
            }};
        }})();
        """
    
    def get_console_evasion(self) -> str:
        """Protect against console-based detection."""
        return """
        // Console protection
        (() => {
            'use strict';
            
            // Store original console methods
            const originalConsole = {};
            ['log', 'debug', 'info', 'warn', 'error', 'trace'].forEach(method => {
                originalConsole[method] = console[method].bind(console);
            });
            
            // Track console calls for detection
            const consoleCallLog = [];
            const maxLogSize = 100;
            
            // Override console methods
            ['log', 'debug', 'info', 'warn', 'error'].forEach(method => {
                console[method] = new Proxy(originalConsole[method], {
                    apply(target, thisArg, args) {
                        // Log the call
                        consoleCallLog.push({
                            method: method,
                            timestamp: Date.now(),
                            stack: new Error().stack
                        });
                        
                        // Keep log size manageable
                        if (consoleCallLog.length > maxLogSize) {
                            consoleCallLog.shift();
                        }
                        
                        // Check for rapid successive calls (CDP detection)
                        if (consoleCallLog.length >= 3) {
                            const recent = consoleCallLog.slice(-3);
                            const timeDiffs = [
                                recent[1].timestamp - recent[0].timestamp,
                                recent[2].timestamp - recent[1].timestamp
                            ];
                            
                            // If calls are too rapid, it's likely detection
                            if (timeDiffs[0] < 5 && timeDiffs[1] < 5) {
                                return undefined;
                            }
                        }
                        
                        // Check stack for automation tools
                        const stack = new Error().stack || '';
                        const suspiciousPatterns = [
                            'puppeteer',
                            'playwright',
                            'selenium',
                            'webdriver',
                            'cdp',
                            'devtools'
                        ];
                        
                        if (suspiciousPatterns.some(pattern => 
                            stack.toLowerCase().includes(pattern))) {
                            return undefined;
                        }
                        
                        // Normal console usage
                        return target.apply(console, args);
                    }
                });
            });
            
            // Override toString to hide modifications
            console.log.toString = () => 'function log() { [native code] }';
            console.debug.toString = () => 'function debug() { [native code] }';
            console.info.toString = () => 'function info() { [native code] }';
            console.warn.toString = () => 'function warn() { [native code] }';
            console.error.toString = () => 'function error() { [native code] }';
        })();
        """
    
    def get_error_evasion(self) -> str:
        """Clean error stack traces of automation signatures."""
        return """
        // Error stack trace cleaning
        (() => {
            'use strict';
            
            const OriginalError = Error;
            
            // Patterns to remove from stack traces
            const cleanPatterns = [
                /\\bplaywright\\b/gi,
                /\\bpuppeteer\\b/gi,
                /\\bselenium\\b/gi,
                /\\bwebdriver\\b/gi,
                /\\b__playwright\\b/gi,
                /\\b__puppeteer\\b/gi,
                /\\bcdp_session\\b/gi,
                /\\bHeadlessChrome\\b/gi,
                /\\bautomation\\b/gi
            ];
            
            // Override Error constructor
            Error = new Proxy(OriginalError, {
                construct(target, args) {
                    const error = new target(...args);
                    
                    // Clean the stack trace
                    if (error.stack) {
                        let cleanStack = error.stack;
                        cleanPatterns.forEach(pattern => {
                            cleanStack = cleanStack.replace(pattern, '');
                        });
                        
                        // Fix any broken lines
                        cleanStack = cleanStack
                            .split('\\n')
                            .filter(line => line.trim())
                            .join('\\n');
                        
                        error.stack = cleanStack;
                    }
                    
                    return error;
                }
            });
            
            // Copy static properties
            Object.setPrototypeOf(Error, OriginalError);
            Error.captureStackTrace = OriginalError.captureStackTrace;
            Error.stackTraceLimit = OriginalError.stackTraceLimit;
        })();
        """