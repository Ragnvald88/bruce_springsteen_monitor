# stealthmaster/browser/optimized_launcher.py
"""Optimized browser launcher with all improvements integrated."""

import logging
import re
from typing import Dict, Optional, List, Any
from playwright.async_api import Browser, Playwright, BrowserContext, Route, Request

from config import BrowserOptions, ProxyConfig

logger = logging.getLogger(__name__)


class OptimizedBrowserLauncher:
    """Launches browsers with maximum stealth and minimum data usage."""
    
    def __init__(self, config: BrowserOptions):
        """Initialize the optimized launcher."""
        self.config = config
        self.optimization_stats = {
            "requests_blocked": 0,
            "requests_allowed": 0,
            "data_saved_bytes": 0,
            "cache_hits": 0
        }
        
    async def launch(
        self,
        playwright: Playwright,
        proxy: Optional[ProxyConfig] = None,
        headless: bool = False,
        optimization_level: str = "balanced"
    ) -> Browser:
        """
        Launch an optimized browser.
        
        Args:
            playwright: Playwright instance
            proxy: Optional proxy configuration
            headless: Whether to run headless
            optimization_level: Data optimization level (minimal, balanced, aggressive)
            
        Returns:
            Configured browser instance
        """
        # Build optimized launch arguments
        args = self._get_optimized_launch_args()
        
        # Proxy configuration
        proxy_config = None
        if proxy:
            proxy_config = {
                "server": f"{proxy.type}://{proxy.host}:{proxy.port}",
                "username": proxy.username,
                "password": proxy.password,
            }
        
        # Launch with optimal settings
        launch_options = {
            "headless": headless,
            "args": args,
            "proxy": proxy_config,
            "chromium_sandbox": False,
            "handle_sigint": False,
            "handle_sigterm": False,
            "handle_sighup": False,
        }
        
        browser = await playwright.chromium.launch(**launch_options)
        
        logger.info(
            f"Launched optimized {'headless' if headless else 'headed'} browser "
            f"with {optimization_level} data optimization"
        )
        
        return browser
    
    def _get_optimized_launch_args(self) -> List[str]:
        """Get optimal browser launch arguments for stealth and performance."""
        return [
            # Core stealth arguments
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            
            # Performance optimizations
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            '--disable-accelerated-video-decode',
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            
            # Stealth enhancements
            '--disable-infobars',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-component-extensions-with-background-pages',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            
            # Privacy and tracking prevention
            '--disable-client-side-phishing-detection',
            '--disable-sync',
            '--disable-plugins-discovery',
            '--disable-preconnect',
            '--dns-prefetch-disable',
            
            # Window configuration
            '--window-size=1920,1080',
            '--window-position=0,0',
            '--force-device-scale-factor=1',
            
            # Additional stealth
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-logging',
            '--disable-permissions-api',
            '--disable-notifications',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-hang-monitor',
            '--metrics-recording-only',
            '--no-first-run',
            '--no-default-browser-check',
            '--password-store=basic',
            '--use-mock-keychain',
            '--export-tagged-pdf',
            
            # User agent (will be overridden in context)
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
    
    async def create_optimized_context(
        self,
        browser: Browser,
        fingerprint: Optional[Dict] = None,
        optimization_level: str = "balanced"
    ) -> BrowserContext:
        """
        Create an optimized browser context with stealth and data savings.
        
        Args:
            browser: Browser instance
            fingerprint: Optional fingerprint configuration
            optimization_level: Data optimization level
            
        Returns:
            Optimized browser context
        """
        # Use provided fingerprint or generate optimal one
        if not fingerprint:
            fingerprint = self._generate_optimal_fingerprint()
        
        # Context options for stealth
        context_options = {
            "viewport": {
                "width": fingerprint["viewport"]["width"],
                "height": fingerprint["viewport"]["height"],
            },
            "user_agent": fingerprint["user_agent"],
            "locale": fingerprint["locale"],
            "timezone_id": fingerprint["timezone"],
            "geolocation": fingerprint.get("geo"),
            "permissions": [],  # Don't grant permissions by default
            "color_scheme": "light",
            "device_scale_factor": fingerprint.get("device_scale_factor", 1),
            "is_mobile": False,
            "has_touch": False,
            "bypass_csp": True,
            "ignore_https_errors": True,
            "offline": False,
            "http_credentials": None,
            "extra_http_headers": {
                "Accept-Language": f"{fingerprint['language']},en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Upgrade-Insecure-Requests": "1",
            },
        }
        
        # Create context
        context = await browser.new_context(**context_options)
        
        # Apply comprehensive stealth
        await self._apply_stealth_scripts(context, fingerprint)
        
        # Apply data optimization
        await self._apply_data_optimization(context, optimization_level)
        
        # Store fingerprint for reference
        context._stealth_fingerprint = fingerprint
        context._optimization_stats = self.optimization_stats
        
        logger.debug(f"Created optimized context with {optimization_level} data optimization")
        
        return context
    
    def _generate_optimal_fingerprint(self) -> Dict[str, Any]:
        """Generate an optimal fingerprint for stealth."""
        import random
        
        profiles = [
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "platform": "Win32",
                "vendor": "Google Inc.",
                "viewport": {"width": 1920, "height": 1080},
                "locale": "en-US",
                "language": "en-US,en",
                "timezone": "America/New_York"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "platform": "MacIntel",
                "vendor": "Google Inc.",
                "viewport": {"width": 1920, "height": 1080},
                "locale": "en-US",
                "language": "en-US,en",
                "timezone": "America/New_York"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "platform": "Win32",
                "vendor": "Google Inc.",
                "viewport": {"width": 1920, "height": 1080},
                "locale": "it-IT",
                "language": "it-IT,it,en",
                "timezone": "Europe/Rome"
            }
        ]
        
        return random.choice(profiles)
    
    async def _apply_stealth_scripts(self, context: BrowserContext, fingerprint: Dict) -> None:
        """Apply comprehensive stealth scripts to the context."""
        stealth_script = f"""
        (() => {{
            // 1. Complete webdriver removal
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;
            
            // Also remove from window
            delete window.navigator.webdriver;
            
            // 2. Realistic plugin array
            const makePluginArray = () => {{
                const plugins = [
                    {{name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}},
                    {{name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format'}}
                ];
                
                const arr = [];
                plugins.forEach(p => {{
                    const plugin = Object.create(Plugin.prototype);
                    plugin.name = p.name;
                    plugin.filename = p.filename;
                    plugin.description = p.description;
                    plugin.length = 1;
                    plugin[0] = plugin;
                    plugin.item = function(i) {{ return i === 0 ? this : null; }};
                    plugin.namedItem = function() {{ return null; }};
                    arr.push(plugin);
                }});
                
                arr.length = plugins.length;
                arr.item = function(i) {{ return this[i] || null; }};
                arr.namedItem = function(name) {{ return null; }};
                arr.refresh = function() {{ }};
                
                Object.setPrototypeOf(arr, PluginArray.prototype);
                return arr;
            }};
            
            Object.defineProperty(navigator, 'plugins', {{
                get: makePluginArray,
                configurable: true,
                enumerable: true
            }});
            
            // 3. Chrome object
            if (!window.chrome) {{
                window.chrome = {{
                    app: {{}},
                    runtime: {{
                        connect: () => {{}},
                        sendMessage: () => {{}}
                    }},
                    loadTimes: function() {{
                        return {{
                            requestTime: performance.timing.navigationStart / 1000,
                            startLoadTime: performance.timing.navigationStart / 1000,
                            commitLoadTime: performance.timing.responseStart / 1000,
                            finishDocumentLoadTime: performance.timing.domContentLoadedEventEnd / 1000,
                            finishLoadTime: performance.timing.loadEventEnd / 1000,
                            firstPaintTime: 0,
                            firstPaintAfterLoadTime: 0,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: true,
                            wasNpnNegotiated: true,
                            npnNegotiatedProtocol: 'h2',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'h2'
                        }};
                    }},
                    csi: function() {{
                        return {{
                            onloadT: performance.timing.loadEventEnd,
                            pageT: Date.now() - performance.timing.navigationStart,
                            startE: performance.timing.navigationStart,
                            tran: 15
                        }};
                    }}
                }};
            }}
            
            // 4. Fix other properties
            Object.defineProperty(navigator, 'vendor', {{
                get: () => '{fingerprint["vendor"]}',
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint["platform"]}',
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => '{fingerprint["language"]}'.split(','),
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => 8,
                configurable: true
            }});
            
            // 5. WebGL vendor spoofing
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fingerprint["vendor"]}';
                if (parameter === 37446) return 'ANGLE (Intel, Intel(R) Iris(TM) Graphics OpenGL Engine, OpenGL 4.1)';
                return getParameter.apply(this, arguments);
            }};
            
            // 6. Permissions API
            if (navigator.permissions) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    if (parameters.name === 'notifications') {{
                        return Promise.reject(new DOMException('Permission denied'));
                    }}
                    return originalQuery.apply(this, arguments);
                }};
            }}
            
            // 7. Remove automation artifacts
            ['__webdriver_evaluate', '__selenium_evaluate', '__webdriver_script_function',
             '__webdriver_script_func', '__webdriver_script_fn', '__fxdriver_evaluate',
             '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate',
             '__selenium_unwrapped', '__fxdriver_unwrapped'].forEach(prop => {{
                delete window[prop];
                delete document[prop];
            }});
            
            // 8. Battery API
            if ('getBattery' in navigator) {{
                navigator.getBattery = async () => ({{
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.98,
                    addEventListener: () => {{}},
                    removeEventListener: () => {{}}
                }});
            }}
        }})();
        """
        
        await context.add_init_script(stealth_script)
    
    async def _apply_data_optimization(self, context: BrowserContext, level: str) -> None:
        """Apply data optimization to the context."""
        
        # Define blocking rules based on optimization level
        blocking_rules = {
            "minimal": {
                "block_types": {"font", "media"},
                "block_domains": set()
            },
            "balanced": {
                "block_types": {"font", "media"},
                "block_domains": {
                    'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
                    'facebook.com', 'twitter.com', 'pinterest.com', 'linkedin.com',
                    'hotjar.com', 'mixpanel.com', 'segment.com', 'amplitude.com',
                    'cookielaw.org', 'cookiebot.com', 'onetrust.com'
                },
                "smart_image_blocking": True,
                "smart_script_blocking": True
            },
            "aggressive": {
                "block_types": {"font", "media", "image", "stylesheet"},
                "block_domains": {
                    'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
                    'facebook.com', 'twitter.com', 'pinterest.com', 'linkedin.com',
                    'hotjar.com', 'mixpanel.com', 'segment.com', 'amplitude.com',
                    'cookielaw.org', 'cookiebot.com', 'onetrust.com',
                    'cloudflare.com', 'jsdelivr.net', 'unpkg.com'
                },
                "block_third_party": True
            }
        }
        
        rules = blocking_rules.get(level, blocking_rules["balanced"])
        
        async def handle_route(route: Route):
            request = route.request
            url = request.url.lower()
            resource_type = request.resource_type
            
            # Always allow main document
            if resource_type == "document":
                self.optimization_stats["requests_allowed"] += 1
                await route.continue_()
                return
            
            should_block = False
            
            # Check resource type blocking
            if resource_type in rules["block_types"]:
                should_block = True
            
            # Check domain blocking
            domain = self._extract_domain(url)
            if any(blocked in domain for blocked in rules["block_domains"]):
                should_block = True
            
            # Smart image blocking (balanced mode)
            if rules.get("smart_image_blocking") and resource_type == "image":
                # Allow essential images
                if not any(pattern in url for pattern in ['logo', 'icon', 'button', 'arrow', 'thumb']):
                    should_block = True
                else:
                    should_block = False
            
            # Smart script blocking (balanced mode)
            if rules.get("smart_script_blocking") and resource_type == "script":
                # Block tracking scripts
                tracking_patterns = [
                    'analytics', 'tracking', 'metrics', 'telemetry', 'beacon',
                    'pixel', 'tag', 'gtm', '_ga', 'matomo', 'piwik', 'hotjar'
                ]
                if any(pattern in url for pattern in tracking_patterns):
                    should_block = True
            
            if should_block:
                self.optimization_stats["requests_blocked"] += 1
                # Estimate saved data
                sizes = {
                    "image": 50 * 1024,
                    "stylesheet": 30 * 1024,
                    "font": 40 * 1024,
                    "media": 500 * 1024,
                    "script": 50 * 1024,
                    "other": 10 * 1024
                }
                self.optimization_stats["data_saved_bytes"] += sizes.get(resource_type, 10 * 1024)
                await route.abort()
            else:
                self.optimization_stats["requests_allowed"] += 1
                await route.continue_()
        
        await context.route("**/*", handle_route)
        
        # Disable service workers for better performance
        await context.add_init_script("""
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations = async () => [];
                navigator.serviceWorker.register = async () => {
                    throw new Error('Service worker registration blocked');
                };
            }
        """)
        
        # Set optimal timeouts
        context.set_default_timeout(15000)  # 15s default
        context.set_default_navigation_timeout(30000)  # 30s for navigation
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get current optimization statistics."""
        total = self.optimization_stats["requests_blocked"] + self.optimization_stats["requests_allowed"]
        block_rate = (self.optimization_stats["requests_blocked"] / total * 100) if total > 0 else 0
        
        return {
            "requests_blocked": self.optimization_stats["requests_blocked"],
            "requests_allowed": self.optimization_stats["requests_allowed"],
            "block_rate_percent": round(block_rate, 1),
            "data_saved_mb": round(self.optimization_stats["data_saved_bytes"] / (1024 * 1024), 2),
            "cache_hits": self.optimization_stats["cache_hits"]
        }