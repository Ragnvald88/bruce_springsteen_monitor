# src/core/ultra_stealth_launcher.py
"""
StealthMaster AI v3.0 - Ultra-Stealth Browser Launcher
Next-generation browser launching with complete anti-detection measures
"""

import asyncio
import logging
import random
import os
import json
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime
from pathlib import Path
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

# Import v3 components
from ..stealth.cdp_bypass_engine import get_cdp_bypass_engine
from ..stealth.advanced_fingerprint import AdvancedFingerprint
from .data_optimization_engine import get_data_optimization_engine

logger = logging.getLogger(__name__)


class UltraStealthLauncher:
    """
    Revolutionary browser launcher with complete stealth measures
    Implements all 2025 anti-detection techniques
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Components
        self.cdp_bypass = get_cdp_bypass_engine()
        self.data_optimizer = get_data_optimization_engine(config.get('data_optimization', {}))
        
        # Browser management
        self.playwright: Optional[Playwright] = None
        self.browsers: List[Browser] = []
        self.temp_dirs: List[Path] = []
        
        # Stealth settings
        self.headless = self.config.get('headless', False)  # Never use headless for max stealth
        self.channel = self.config.get('channel', 'chrome')  # Use real Chrome
        
        # Stats
        self.launch_count = 0
        self.detection_blocks = 0
        
    async def initialize(self) -> None:
        """Initialize the launcher"""
        logger.info("🚀 Initializing Ultra-Stealth Browser Launcher v3.0")
        
        # Start Playwright
        self.playwright = await async_playwright().start()
        
        # Verify Chrome installation
        self._verify_chrome_installation()
        
        logger.info("✅ Ultra-Stealth Launcher ready")
    
    def _verify_chrome_installation(self) -> None:
        """Verify real Chrome is installed"""
        chrome_paths = {
            'win32': [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
            ],
            'darwin': [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            ],
            'linux': [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium-browser'
            ]
        }
        
        import sys
        platform = sys.platform
        
        found = False
        for path in chrome_paths.get(platform, []):
            if os.path.exists(path):
                found = True
                logger.info(f"✅ Found Chrome at: {path}")
                break
        
        if not found:
            logger.warning("⚠️ Real Chrome not found - detection risk increased!")
    
    async def launch_ultra_stealth_browser(
        self,
        proxy: Optional[Dict[str, str]] = None,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> Tuple[Browser, BrowserContext, Page]:
        """
        Launch browser with maximum stealth measures
        Returns: (browser, context, page) tuple
        """
        logger.info("🛡️ Launching Ultra-Stealth Browser...")
        
        # Generate fingerprint if not provided
        if not fingerprint:
            fingerprint = AdvancedFingerprint.generate_fingerprint()
        
        # Create temporary user data directory
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="stealth_profile_"))
        self.temp_dirs.append(temp_dir)
        
        # Build launch arguments
        args = self._build_ultra_stealth_args(fingerprint)
        
        # Remove automation indicators
        ignore_args = [
            '--enable-automation',
            '--enable-blink-features=IdleDetection',
            '--test-type',
            '--enable-logging',
            '--log-level',
            '--dump-dom',
            '--aggressive-cache-discard',
            '--disable-extensions-except',
            '--disable-component-extensions-with-background-pages'
        ]
        
        # Configure browser options
        browser_options = {
            'headless': False,  # NEVER use headless for stealth
            'args': args,
            'ignore_default_args': ignore_args,
            'channel': self.channel,
            'downloads_path': str(temp_dir / 'downloads'),
            'viewport': None,  # Set per context
            'bypass_csp': False,  # Don't bypass CSP (detection vector)
            'java_script_enabled': True,
            'accept_downloads': True,
            'handle_sigint': False,
            'handle_sigterm': False,
            'handle_sighup': False
        }
        
        # Launch browser
        browser = await self.playwright.chromium.launch(**browser_options)
        self.browsers.append(browser)
        
        # Create stealth context
        context = await self._create_ultra_stealth_context(browser, fingerprint, proxy)
        
        # Create first page
        page = await context.new_page()
        
        # Apply all stealth measures
        await self._apply_ultra_stealth_measures(page, context, fingerprint)
        
        # Apply data optimization
        await self.data_optimizer.optimize_page(page)
        
        self.launch_count += 1
        logger.info(f"✅ Ultra-Stealth Browser launched (#{self.launch_count})")
        
        return browser, context, page
    
    def _build_ultra_stealth_args(self, fingerprint: Dict[str, Any]) -> List[str]:
        """Build browser arguments for maximum stealth"""
        
        # Get screen resolution from fingerprint
        screen = fingerprint.get('screen', {})
        width = screen.get('width', 1920)
        height = screen.get('height', 1080)
        
        args = [
            # Window and display
            f'--window-size={width},{height}',
            f'--window-position=0,0',
            '--start-maximized',
            
            # Disable automation flags
            '--disable-blink-features=AutomationControlled',
            '--disable-features=AutomationControlled',
            '--disable-dev-shm-usage',
            
            # Performance and stability
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-features=BlinkGenPropertyTrees',
            '--disable-ipc-flooding-protection',
            
            # Privacy and security
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            
            # Media and permissions
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            '--autoplay-policy=no-user-gesture-required',
            
            # Network
            '--disable-features=NetworkService,NetworkServiceInProcess',
            '--disable-features=VizDisplayCompositor',
            '--disable-features=CalculateNativeWinOcclusion',
            
            # Additional stealth
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--disable-features=UserAgentClientHint',
            '--disable-web-security',  # Required for some fingerprinting
            '--allow-running-insecure-content',
            
            # Font rendering (match fingerprint)
            '--font-render-hinting=none',
            '--disable-font-subpixel-positioning',
            
            # WebGL and Canvas
            '--enable-webgl',
            '--enable-webgl2',
            '--disable-reading-from-canvas',  # Prevent canvas fingerprinting
            
            # Audio
            '--disable-features=AudioServiceOutOfProcess',
            
            # Misc
            '--disable-default-apps',
            '--disable-sync',
            '--disable-features=ChromeWhatsNewUI',
            '--no-first-run',
            '--disable-features=DialMediaRouteProvider',
            '--no-default-browser-check',
            '--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching',
            
            # Language and locale
            f'--lang={fingerprint.get("language", "en-US")}',
        ]
        
        # Add random variations
        if random.random() > 0.5:
            args.append('--disable-features=RendererCodeIntegrity')
        
        return args
    
    async def _create_ultra_stealth_context(
        self,
        browser: Browser,
        fingerprint: Dict[str, Any],
        proxy: Optional[Dict[str, str]] = None
    ) -> BrowserContext:
        """Create browser context with stealth settings"""
        
        # Context options from fingerprint
        context_options = {
            'viewport': fingerprint['viewport'],
            'screen': fingerprint['screen'],
            'user_agent': fingerprint['user_agent'],
            'locale': fingerprint['language'],
            'timezone_id': fingerprint['timezone'],
            'device_scale_factor': fingerprint['device_scale_factor'],
            'is_mobile': False,
            'has_touch': fingerprint.get('has_touch', False),
            'bypass_csp': False,
            'ignore_https_errors': False,  # Don't ignore HTTPS errors (suspicious)
            'accept_downloads': True,
            'extra_http_headers': self._generate_stealth_headers(fingerprint),
            'permissions': ['geolocation', 'notifications', 'camera', 'microphone'],
            'geolocation': {
                'latitude': fingerprint['geo']['latitude'],
                'longitude': fingerprint['geo']['longitude']
            },
            'color_scheme': 'dark' if random.random() > 0.3 else 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none'
        }
        
        # Add proxy if provided
        if proxy:
            context_options['proxy'] = proxy
        
        # Create context
        context = await browser.new_context(**context_options)
        
        # Set additional cookies for realism
        await self._set_realistic_cookies(context)
        
        return context
    
    def _generate_stealth_headers(self, fingerprint: Dict[str, Any]) -> Dict[str, str]:
        """Generate realistic HTTP headers"""
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': f'{fingerprint["language"]},en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': fingerprint['client_hints']['sec_ch_ua'],
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{fingerprint["platform"]}"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Dnt': '1' if random.random() > 0.7 else None
        }
        
        # Remove None values
        headers = {k: v for k, v in headers.items() if v is not None}
        
        return headers
    
    async def _set_realistic_cookies(self, context: BrowserContext) -> None:
        """Set realistic cookies for common sites"""
        
        # Common tracking cookies (makes us look more real)
        common_cookies = [
            {
                'name': '_ga',
                'value': f'GA1.1.{random.randint(100000000, 999999999)}.{int(datetime.now().timestamp())}',
                'domain': '.google.com',
                'path': '/',
                'expires': int((datetime.now().timestamp() + 63072000))  # 2 years
            },
            {
                'name': 'NID',
                'value': ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', k=128)),
                'domain': '.google.com',
                'path': '/',
                'httpOnly': True,
                'expires': int((datetime.now().timestamp() + 15552000))  # 6 months
            }
        ]
        
        for cookie in common_cookies:
            try:
                await context.add_cookies([cookie])
            except:
                pass  # Ignore cookie errors
    
    async def _apply_ultra_stealth_measures(
        self,
        page: Page,
        context: BrowserContext,
        fingerprint: Dict[str, Any]
    ) -> None:
        """Apply all stealth measures to page"""
        
        logger.info("🔧 Applying ultra-stealth measures...")
        
        # 1. Apply CDP bypass (CRITICAL)
        await self.cdp_bypass.apply_cdp_bypass(page)
        
        # 2. Override navigator properties
        await self._override_navigator_properties(page, fingerprint)
        
        # 3. Inject WebGL and Canvas noise
        await self._inject_webgl_canvas_noise(page, fingerprint)
        
        # 4. Audio context fingerprinting protection
        await self._inject_audio_fingerprint_protection(page)
        
        # 5. Font fingerprinting protection
        await self._inject_font_fingerprint_protection(page)
        
        # 6. Battery API spoofing
        await self._inject_battery_api_spoofing(page)
        
        # 7. Hardware concurrency spoofing
        await self._inject_hardware_spoofing(page, fingerprint)
        
        # 8. Plugin and MIME type spoofing
        await self._inject_plugin_spoofing(page, fingerprint)
        
        # 9. Timezone and locale consistency
        await self._inject_timezone_spoofing(page, fingerprint)
        
        # 10. Screen and window property spoofing
        await self._inject_screen_spoofing(page, fingerprint)
        
        # 11. Network information API spoofing
        await self._inject_network_info_spoofing(page)
        
        # 12. Permission API overrides
        await self._inject_permission_overrides(page)
        
        # 13. WebRTC leak prevention
        await self._inject_webrtc_protection(page)
        
        # 14. Client rects noise
        await self._inject_client_rects_noise(page)
        
        # 15. Keyboard and mouse event protection
        await self._inject_event_protection(page)
        
        logger.info("✅ All ultra-stealth measures applied")
    
    async def _override_navigator_properties(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Override navigator properties comprehensively"""
        
        await page.add_init_script(f"""
        // Ultra-stealth navigator overrides
        (() => {{
            'use strict';
            
            // Helper to define perfect property
            const defineProp = (obj, prop, value) => {{
                Object.defineProperty(obj, prop, {{
                    value: value,
                    writable: false,
                    enumerable: true,
                    configurable: false
                }});
            }};
            
            // Remove webdriver
            delete Object.getPrototypeOf(navigator).webdriver;
            defineProp(navigator, 'webdriver', undefined);
            
            // Platform
            defineProp(navigator, 'platform', '{fingerprint["platform"]}');
            
            // Hardware concurrency
            defineProp(navigator, 'hardwareConcurrency', {fingerprint['hardware_concurrency']});
            
            // Memory
            if (navigator.deviceMemory) {{
                defineProp(navigator, 'deviceMemory', {fingerprint.get('device_memory', 8)});
            }}
            
            // Languages
            defineProp(navigator, 'language', '{fingerprint["language"]}');
            defineProp(navigator, 'languages', {json.dumps(fingerprint["languages"])});
            
            // Vendor
            defineProp(navigator, 'vendor', '{fingerprint["vendor"]}');
            defineProp(navigator, 'vendorSub', '');
            
            // Product
            defineProp(navigator, 'product', 'Gecko');
            defineProp(navigator, 'productSub', '20030107');
            
            // App
            defineProp(navigator, 'appCodeName', 'Mozilla');
            defineProp(navigator, 'appName', 'Netscape');
            defineProp(navigator, 'appVersion', '{fingerprint["app_version"]}');
            
            // Max touch points
            defineProp(navigator, 'maxTouchPoints', {fingerprint.get('max_touch_points', 0)});
            
            // Connection
            if (navigator.connection) {{
                ['effectiveType', 'type', 'rtt', 'downlink', 'saveData'].forEach(prop => {{
                    Object.defineProperty(navigator.connection, prop, {{
                        get: () => {{
                            if (prop === 'effectiveType') return '4g';
                            if (prop === 'type') return 'wifi';
                            if (prop === 'rtt') return 50;
                            if (prop === 'downlink') return 10.0;
                            if (prop === 'saveData') return false;
                        }}
                    }});
                }});
            }}
            
            // Brave detection
            if (navigator.brave) {{
                delete navigator.brave;
            }}
        }})();
        """)
    
    async def _inject_webgl_canvas_noise(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Inject WebGL and Canvas fingerprinting protection"""
        
        await page.add_init_script("""
        // WebGL and Canvas noise injection
        (() => {
            'use strict';
            
            // Canvas noise
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {
                const context = originalGetContext.call(this, type, ...args);
                
                if (type === '2d' && context) {
                    // Add noise to canvas operations
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function(...args) {
                        const imageData = originalGetImageData.apply(this, args);
                        
                        // Add subtle noise
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] = Math.min(255, imageData.data[i] + Math.random() * 2 - 1);
                            imageData.data[i + 1] = Math.min(255, imageData.data[i + 1] + Math.random() * 2 - 1);
                            imageData.data[i + 2] = Math.min(255, imageData.data[i + 2] + Math.random() * 2 - 1);
                        }
                        
                        return imageData;
                    };
                    
                    // Modify toDataURL
                    const originalToDataURL = this.toDataURL;
                    this.toDataURL = function(...args) {
                        // Add random pixel
                        context.fillStyle = `rgba(${Math.random()*255},${Math.random()*255},${Math.random()*255},0.01)`;
                        context.fillRect(Math.random() * this.width, Math.random() * this.height, 1, 1);
                        return originalToDataURL.apply(this, args);
                    };
                }
                
                // WebGL noise
                if ((type === 'webgl' || type === 'webgl2') && context) {
                    const originalGetParameter = context.getParameter;
                    context.getParameter = function(parameter) {
                        const result = originalGetParameter.call(this, parameter);
                        
                        // Modify certain parameters
                        if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                            return 'Intel Iris OpenGL Engine';
                        }
                        
                        return result;
                    };
                }
                
                return context;
            };
            
            // WebGL vendor and renderer
            const getParameterProto = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameterProto.call(this, parameter);
            };
            
            if (WebGL2RenderingContext) {
                const getParameter2Proto = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                    return getParameter2Proto.call(this, parameter);
                };
            }
        })();
        """)
    
    async def _inject_audio_fingerprint_protection(self, page: Page) -> None:
        """Protect against audio fingerprinting"""
        
        await page.add_init_script("""
        // Audio fingerprinting protection
        (() => {
            const context = typeof window.AudioContext !== 'undefined' ? window.AudioContext : window.webkitAudioContext;
            if (!context) return;
            
            const origGetFloatFrequencyData = AnalyserNode.prototype.getFloatFrequencyData;
            AnalyserNode.prototype.getFloatFrequencyData = function(array) {
                const result = origGetFloatFrequencyData.call(this, array);
                
                // Add noise to frequency data
                for (let i = 0; i < array.length; i++) {
                    array[i] = array[i] + (Math.random() * 0.1 - 0.05);
                }
                
                return result;
            };
            
            // Modify audio processing
            const origCreateOscillator = context.prototype.createOscillator;
            context.prototype.createOscillator = function() {
                const osc = origCreateOscillator.call(this);
                
                // Add slight frequency variation
                const originalStart = osc.start;
                osc.start = function(when) {
                    osc.frequency.value = osc.frequency.value * (1 + (Math.random() * 0.0001 - 0.00005));
                    return originalStart.call(this, when);
                };
                
                return osc;
            };
        })();
        """)
    
    async def _inject_font_fingerprint_protection(self, page: Page) -> None:
        """Protect against font fingerprinting"""
        
        await page.add_init_script("""
        // Font fingerprinting protection
        (() => {
            const offsetWidthGetter = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth').get;
            const offsetHeightGetter = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight').get;
            
            Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
                get: function() {
                    const result = offsetWidthGetter.call(this);
                    
                    // Add noise to font measurements
                    if (this.style && this.style.fontFamily) {
                        return result + (Math.random() < 0.1 ? 1 : 0);
                    }
                    
                    return result;
                }
            });
            
            Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
                get: function() {
                    const result = offsetHeightGetter.call(this);
                    
                    // Add noise to font measurements
                    if (this.style && this.style.fontFamily) {
                        return result + (Math.random() < 0.1 ? 1 : 0);
                    }
                    
                    return result;
                }
            });
        })();
        """)
    
    async def _inject_battery_api_spoofing(self, page: Page) -> None:
        """Spoof battery API"""
        
        await page.add_init_script("""
        // Battery API spoofing
        (() => {
            if ('getBattery' in navigator) {
                navigator.getBattery = async () => {
                    return {
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 0.99,
                        addEventListener: () => {},
                        removeEventListener: () => {},
                        dispatchEvent: () => true
                    };
                };
            }
        })();
        """)
    
    async def _inject_hardware_spoofing(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Spoof hardware information"""
        
        await page.add_init_script(f"""
        // Hardware spoofing
        (() => {{
            // GPU info
            const debugInfo = {{
                UNMASKED_VENDOR_WEBGL: '{fingerprint.get("gpu_vendor", "Intel Inc.")}',
                UNMASKED_RENDERER_WEBGL: '{fingerprint.get("gpu_renderer", "Intel Iris OpenGL Engine")}'
            }};
            
            // Override WebGL debug info
            const origGetExtension = WebGLRenderingContext.prototype.getExtension;
            WebGLRenderingContext.prototype.getExtension = function(name) {{
                const result = origGetExtension.call(this, name);
                
                if (name === 'WEBGL_debug_renderer_info') {{
                    return {{
                        UNMASKED_VENDOR_WEBGL: 37445,
                        UNMASKED_RENDERER_WEBGL: 37446
                    }};
                }}
                
                return result;
            }};
        }})();
        """)
    
    async def _inject_plugin_spoofing(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Spoof plugins and MIME types"""
        
        await page.add_init_script("""
        // Plugin spoofing
        (() => {
            const pluginArray = [
                {
                    name: 'Chrome PDF Plugin',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                    mimeTypes: [{
                        type: 'application/pdf',
                        suffixes: 'pdf',
                        description: 'Portable Document Format'
                    }]
                },
                {
                    name: 'Chrome PDF Viewer',
                    filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                    description: '',
                    mimeTypes: [{
                        type: 'application/pdf',
                        suffixes: 'pdf',
                        description: ''
                    }]
                },
                {
                    name: 'Native Client',
                    filename: 'internal-nacl-plugin',
                    description: '',
                    mimeTypes: [
                        {
                            type: 'application/x-nacl',
                            suffixes: '',
                            description: 'Native Client Executable'
                        },
                        {
                            type: 'application/x-pnacl',
                            suffixes: '',
                            description: 'Portable Native Client Executable'
                        }
                    ]
                }
            ];
            
            // Create fake PluginArray
            const fakePluginArray = [];
            const fakePluginArrayProto = Object.create(PluginArray.prototype);
            
            pluginArray.forEach((p, i) => {
                const plugin = Object.create(Plugin.prototype);
                plugin.name = p.name;
                plugin.filename = p.filename;
                plugin.description = p.description;
                plugin.length = p.mimeTypes.length;
                
                p.mimeTypes.forEach((mt, j) => {
                    plugin[j] = mt;
                    Object.defineProperty(plugin, mt.type, {
                        value: mt,
                        enumerable: false
                    });
                });
                
                fakePluginArray[i] = plugin;
                Object.defineProperty(fakePluginArray, p.name, {
                    value: plugin,
                    enumerable: false
                });
            });
            
            fakePluginArray.length = pluginArray.length;
            Object.setPrototypeOf(fakePluginArray, fakePluginArrayProto);
            
            // Override navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => fakePluginArray,
                enumerable: true,
                configurable: true
            });
        })();
        """)
    
    async def _inject_timezone_spoofing(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Ensure timezone consistency"""
        
        timezone_offset = fingerprint.get('timezone_offset', -480)  # PST
        
        await page.add_init_script(f"""
        // Timezone spoofing
        (() => {{
            const originalDate = Date;
            
            // Override Date constructor
            Date = new Proxy(originalDate, {{
                construct(target, args) {{
                    const instance = new target(...args);
                    return instance;
                }},
                get(target, prop) {{
                    if (prop === 'prototype') {{
                        return target.prototype;
                    }}
                    return target[prop];
                }}
            }});
            
            // Override timezone methods
            Date.prototype.getTimezoneOffset = function() {{
                return {timezone_offset};
            }};
            
            // Intl.DateTimeFormat
            const origDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = new Proxy(origDateTimeFormat, {{
                construct(target, args) {{
                    if (args.length >= 2 && args[1]) {{
                        args[1].timeZone = args[1].timeZone || '{fingerprint["timezone"]}';
                    }}
                    return new target(...args);
                }}
            }});
        }})();
        """)
    
    async def _inject_screen_spoofing(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Spoof screen properties"""
        
        screen_data = fingerprint['screen']
        
        await page.add_init_script(f"""
        // Screen spoofing
        (() => {{
            const screenProps = {{
                width: {screen_data['width']},
                height: {screen_data['height']},
                availWidth: {screen_data['avail_width']},
                availHeight: {screen_data['avail_height']},
                colorDepth: {screen_data['color_depth']},
                pixelDepth: {screen_data['pixel_depth']}
            }};
            
            for (const prop in screenProps) {{
                Object.defineProperty(screen, prop, {{
                    get: () => screenProps[prop],
                    enumerable: true,
                    configurable: true
                }});
            }}
            
            // Also spoof window properties
            Object.defineProperty(window, 'outerWidth', {{
                get: () => {screen_data['width']},
                enumerable: true,
                configurable: true
            }});
            
            Object.defineProperty(window, 'outerHeight', {{
                get: () => {screen_data['height']},
                enumerable: true,
                configurable: true
            }});
        }})();
        """)
    
    async def _inject_network_info_spoofing(self, page: Page) -> None:
        """Spoof network information API"""
        
        await page.add_init_script("""
        // Network information spoofing
        (() => {
            if ('connection' in navigator || 'mozConnection' in navigator || 'webkitConnection' in navigator) {
                const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                
                if (connection) {
                    Object.defineProperty(connection, 'effectiveType', {
                        get: () => '4g',
                        enumerable: true,
                        configurable: true
                    });
                    
                    Object.defineProperty(connection, 'rtt', {
                        get: () => 50,
                        enumerable: true,
                        configurable: true
                    });
                    
                    Object.defineProperty(connection, 'downlink', {
                        get: () => 10.0,
                        enumerable: true,
                        configurable: true
                    });
                    
                    Object.defineProperty(connection, 'saveData', {
                        get: () => false,
                        enumerable: true,
                        configurable: true
                    });
                }
            }
        })();
        """)
    
    async def _inject_permission_overrides(self, page: Page) -> None:
        """Override permission API"""
        
        await page.add_init_script("""
        // Permission API overrides
        (() => {
            const originalQuery = navigator.permissions.query;
            
            navigator.permissions.query = async function(descriptor) {
                // Common permissions that should be granted
                const autoGrant = ['geolocation', 'notifications', 'camera', 'microphone'];
                
                if (autoGrant.includes(descriptor.name)) {
                    return {
                        state: 'granted',
                        onchange: null,
                        addEventListener: () => {},
                        removeEventListener: () => {},
                        dispatchEvent: () => true
                    };
                }
                
                // Default behavior for others
                return originalQuery.call(this, descriptor);
            };
        })();
        """)
    
    async def _inject_webrtc_protection(self, page: Page) -> None:
        """Prevent WebRTC IP leaks"""
        
        await page.add_init_script("""
        // WebRTC protection
        (() => {
            // Block WebRTC
            const OriginalRTCPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection;
            
            if (OriginalRTCPeerConnection) {
                window.RTCPeerConnection = function(...args) {
                    const pc = new OriginalRTCPeerConnection(...args);
                    
                    // Override createDataChannel to prevent leaks
                    pc.createDataChannel = function() {
                        return {
                            send: () => {},
                            close: () => {},
                            addEventListener: () => {},
                            removeEventListener: () => {}
                        };
                    };
                    
                    // Override createOffer/createAnswer
                    const originalCreateOffer = pc.createOffer;
                    pc.createOffer = function(...args) {
                        return originalCreateOffer.apply(this, args).then(offer => {
                            // Remove local IP addresses
                            offer.sdp = offer.sdp.replace(/([0-9]{1,3}\.){3}[0-9]{1,3}/g, '10.0.0.1');
                            return offer;
                        });
                    };
                    
                    return pc;
                };
                
                window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
            }
        })();
        """)
    
    async def _inject_client_rects_noise(self, page: Page) -> None:
        """Add noise to client rects"""
        
        await page.add_init_script("""
        // Client rects noise
        (() => {
            const originalGetBoundingClientRect = Element.prototype.getBoundingClientRect;
            
            Element.prototype.getBoundingClientRect = function() {
                const rect = originalGetBoundingClientRect.call(this);
                
                // Add micro noise
                const noise = () => Math.random() * 0.1 - 0.05;
                
                return {
                    x: rect.x + noise(),
                    y: rect.y + noise(),
                    width: rect.width + noise(),
                    height: rect.height + noise(),
                    top: rect.top + noise(),
                    right: rect.right + noise(),
                    bottom: rect.bottom + noise(),
                    left: rect.left + noise()
                };
            };
        })();
        """)
    
    async def _inject_event_protection(self, page: Page) -> None:
        """Protect keyboard and mouse events from detection"""
        
        await page.add_init_script("""
        // Event protection
        (() => {
            // Make events look more human
            const originalAddEventListener = EventTarget.prototype.addEventListener;
            
            EventTarget.prototype.addEventListener = function(type, listener, options) {
                // Wrap listener to add human-like properties
                const wrappedListener = function(event) {
                    if (event instanceof MouseEvent) {
                        // Add micro movements
                        Object.defineProperty(event, 'movementX', {
                            get: () => Math.random() * 2 - 1,
                            enumerable: true
                        });
                        
                        Object.defineProperty(event, 'movementY', {
                            get: () => Math.random() * 2 - 1,
                            enumerable: true
                        });
                    }
                    
                    return listener.call(this, event);
                };
                
                return originalAddEventListener.call(this, type, wrappedListener, options);
            };
        })();
        """)
    
    async def close_browser(self, browser: Browser) -> None:
        """Safely close browser and cleanup"""
        
        try:
            await browser.close()
            self.browsers.remove(browser)
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        
        # Cleanup temp directories
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
    
    async def cleanup(self) -> None:
        """Cleanup all resources"""
        
        logger.info("🧹 Cleaning up Ultra-Stealth Launcher...")
        
        # Close all browsers
        for browser in self.browsers[:]:
            await self.close_browser(browser)
        
        # Stop Playwright
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("✅ Cleanup complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get launcher statistics"""
        
        return {
            'launch_count': self.launch_count,
            'active_browsers': len(self.browsers),
            'detection_blocks': self.detection_blocks,
            'cdp_status': self.cdp_bypass.get_detection_stats()
        }


# Global instance
_launcher: Optional[UltraStealthLauncher] = None

async def get_stealth_launcher(config: Optional[Dict[str, Any]] = None) -> UltraStealthLauncher:
    """Get or create global launcher instance"""
    global _launcher
    
    if _launcher is None:
        _launcher = UltraStealthLauncher(config)
        await _launcher.initialize()
    
    return _launcher