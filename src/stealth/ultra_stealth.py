"""
Ultra Stealth Mode - Advanced Anti-Detection System
Implements cutting-edge techniques to bypass all known detection methods
"""

import asyncio
import random
import json
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page, BrowserContext, Browser

import logging
logger = logging.getLogger(__name__)


class UltraStealthEngine:
    """Ultimate stealth implementation with maximum evasion capabilities"""
    
    @staticmethod
    async def apply_ultra_stealth(page: Page) -> None:
        """Apply comprehensive stealth measures to page"""
        
        # 1. Remove webdriver property completely
        await page.add_init_script("""
        // Ultra Stealth Mode v3.0
        (() => {
            // Delete webdriver property
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // Override the getter
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: false,
                enumerable: false
            });
            
            // Also handle the new CDP webdriver detection
            Object.defineProperty(navigator, 'webdriver', {
                get: new Proxy(Object.getOwnPropertyDescriptor(navigator, 'webdriver').get, {
                    apply: (target, thisArg, args) => {
                        return undefined;
                    }
                })
            });
        })();
        """)
        
        # 2. Fix Chrome object
        await page.add_init_script("""
        (() => {
            // Create convincing chrome object
            window.chrome = {
                app: {
                    isInstalled: false,
                    InstallState: {"DISABLED":0,"INSTALLED":1,"NOT_INSTALLED":2},
                    RunningState: {"CANNOT_RUN":0,"READY_TO_RUN":1,"RUNNING":2}
                },
                runtime: {
                    OnInstalledReason: {
                        CHROME_UPDATE: "chrome_update",
                        INSTALL: "install",
                        SHARED_MODULE_UPDATE: "shared_module_update",
                        UPDATE: "update"
                    },
                    OnRestartRequiredReason: {
                        APP_UPDATE: "app_update",
                        OS_UPDATE: "os_update",
                        PERIODIC: "periodic"
                    },
                    PlatformArch: {
                        ARM: "arm",
                        ARM64: "arm64",
                        MIPS: "mips",
                        MIPS64: "mips64",
                        X86_32: "x86-32",
                        X86_64: "x86-64"
                    },
                    PlatformNaclArch: {
                        ARM: "arm",
                        MIPS: "mips",
                        MIPS64: "mips64",
                        X86_32: "x86-32",
                        X86_64: "x86-64"
                    },
                    PlatformOs: {
                        ANDROID: "android",
                        CROS: "cros",
                        LINUX: "linux",
                        MAC: "mac",
                        OPENBSD: "openbsd",
                        WIN: "win"
                    },
                    RequestUpdateCheckStatus: {
                        NO_UPDATE: "no_update",
                        THROTTLED: "throttled",
                        UPDATE_AVAILABLE: "update_available"
                    },
                    lastError: null,
                    id: undefined
                },
                csi: function() { return {} },
                loadTimes: function() {
                    return {
                        commitLoadTime: 1680000000 + Math.random() * 1000000,
                        connectionInfo: "http/1.1",
                        finishDocumentLoadTime: 1680000000 + Math.random() * 1000000,
                        finishLoadTime: 1680000000 + Math.random() * 1000000,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: 1680000000 + Math.random() * 1000000,
                        navigationType: "Reload",
                        npnNegotiatedProtocol: "unknown",
                        requestTime: 1680000000 + Math.random() * 1000000,
                        startLoadTime: 1680000000 + Math.random() * 1000000,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false
                    }
                }
            };
        })();
        """)
        
        # 3. Override permissions
        await page.add_init_script("""
        (() => {
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(parameters);
            };
            
            // Fix Notification.permission
            Object.defineProperty(Notification, 'permission', {
                get: () => 'default'
            });
        })();
        """)
        
        # 4. Fix navigator.plugins
        await page.add_init_script("""
        (() => {
            function mockPlugin(name, description, filename) {
                return {
                    name: name,
                    description: description,
                    filename: filename,
                    length: 1,
                    item: (index) => ({
                        type: "application/x-google-chrome-pdf",
                        suffixes: "pdf",
                        description: "Portable Document Format",
                        enabledPlugin: mockPlugin(name, description, filename)
                    }),
                    namedItem: (name) => ({
                        type: "application/x-google-chrome-pdf",
                        suffixes: "pdf",
                        description: "Portable Document Format",
                        enabledPlugin: mockPlugin(name, description, filename)
                    }),
                    [0]: {
                        type: "application/x-google-chrome-pdf",
                        suffixes: "pdf",
                        description: "Portable Document Format",
                        enabledPlugin: mockPlugin(name, description, filename)
                    }
                };
            }
            
            const plugins = [
                mockPlugin("Chrome PDF Plugin", "Portable Document Format", "internal-pdf-viewer"),
                mockPlugin("Chrome PDF Viewer", "Portable Document Format", "mhjfbmdgcfjbbpaeojofohoefgiehjai"),
                mockPlugin("Chromium PDF Plugin", "Portable Document Format", "internal-pdf-viewer"),
                mockPlugin("Microsoft Edge PDF Plugin", "Portable Document Format", "internal-pdf-viewer"),
                mockPlugin("PDF Viewer", "Portable Document Format", "internal-pdf-viewer")
            ];
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const pluginArray = Object.create(PluginArray.prototype);
                    plugins.forEach((plugin, i) => {
                        pluginArray[i] = plugin;
                        pluginArray[plugin.name] = plugin;
                    });
                    pluginArray.length = plugins.length;
                    pluginArray.item = (index) => plugins[index] || null;
                    pluginArray.namedItem = (name) => plugins.find(p => p.name === name) || null;
                    pluginArray.refresh = () => {};
                    return pluginArray;
                },
                configurable: false,
                enumerable: true
            });
        })();
        """)
        
        # 5. Override WebGL
        await page.add_init_script("""
        (() => {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };

            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter2.apply(this, arguments);
            };
        })();
        """)
        
        # 6. Fix canvas fingerprinting
        await page.add_init_script("""
        (() => {
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            // Add noise to canvas
            const injectNoise = (canvas) => {
                const ctx = canvas.getContext('2d');
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = imageData.data[i] + (Math.random() * 2 - 1); // R
                    imageData.data[i + 1] = imageData.data[i + 1] + (Math.random() * 2 - 1); // G
                    imageData.data[i + 2] = imageData.data[i + 2] + (Math.random() * 2 - 1); // B
                }
                ctx.putImageData(imageData, 0, 0);
            };
            
            HTMLCanvasElement.prototype.toDataURL = function() {
                injectNoise(this);
                return originalToDataURL.apply(this, arguments);
            };
            
            HTMLCanvasElement.prototype.toBlob = function() {
                injectNoise(this);
                return originalToBlob.apply(this, arguments);
            };
        })();
        """)
        
        # 7. Fix audio context fingerprinting
        await page.add_init_script("""
        (() => {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const originalCreateOscillator = AudioContext.prototype.createOscillator;
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            
            AudioContext.prototype.createOscillator = function() {
                const oscillator = originalCreateOscillator.apply(this, arguments);
                const originalConnect = oscillator.connect;
                oscillator.connect = function() {
                    // Add slight frequency variation
                    oscillator.frequency.value = oscillator.frequency.value * (1 + (Math.random() * 0.0001 - 0.00005));
                    return originalConnect.apply(this, arguments);
                };
                return oscillator;
            };
            
            AudioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.apply(this, arguments);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.apply(this, arguments);
                    for (let i = 0; i < array.length; i++) {
                        array[i] = array[i] + (Math.random() * 0.1 - 0.05);
                    }
                };
                return analyser;
            };
        })();
        """)
        
        # 8. Override languages
        await page.add_init_script("""
        (() => {
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: false,
                enumerable: true
            });
        })();
        """)
        
        # 9. Fix timezone fingerprinting
        await page.add_init_script("""
        (() => {
            const originalDateTimeFormat = Intl.DateTimeFormat;
            window.Intl.DateTimeFormat = new Proxy(originalDateTimeFormat, {
                construct(target, args) {
                    if (args.length > 1 && args[1] && args[1].timeZone) {
                        args[1].timeZone = 'America/New_York';
                    }
                    return new target(...args);
                }
            });
            
            const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
            Intl.DateTimeFormat.prototype.resolvedOptions = function() {
                const options = originalResolvedOptions.apply(this, arguments);
                options.timeZone = 'America/New_York';
                return options;
            };
        })();
        """)
        
        # 10. Remove automation indicators
        await page.add_init_script("""
        (() => {
            // Remove Playwright specific
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__PW_inspect;
            
            // Remove Puppeteer specific
            delete window.__puppeteer_evaluation_script__;
            delete window.puppeteer;
            
            // Remove Selenium specific
            delete window.__selenium_evaluate;
            delete window.__selenium_unwrap;
            delete window.__webdriver_evaluate;
            delete window.__driver_evaluate;
            delete window.__webdriver_unwrap;
            delete window.__driver_unwrap;
            delete window.__selenium_unwrap;
            delete window.__fxdriver_evaluate;
            delete window.__fxdriver_unwrap;
            delete window._Selenium_IDE_Recorder;
            delete window._selenium;
            delete window.calledSelenium;
            delete window.$cdc_asdjflasutopfhvcZLmcfl_;
            delete window.$chrome_asyncScriptInfo;
            delete window.__$webdriverAsyncExecutor;
            
            // Remove common automation properties
            delete document.$cdc_asdjflasutopfhvcZLmcfl_;
            delete document.__selenium_unwrapped;
            delete document.__webdriver_evaluate;
            delete document.__driver_evaluate;
            delete document.__webdriver_unwrapped;
            delete document.__driver_unwrapped;
            delete document.__selenium_evaluate;
            delete document.__fxdriver_evaluate;
            delete document.__fxdriver_unwrapped;
        })();
        """)
        
        logger.info("✅ Ultra Stealth measures applied successfully")
        
    @staticmethod
    async def create_stealth_context(browser: Browser, proxy_config: Optional[Dict] = None) -> BrowserContext:
        """Create a browser context with maximum stealth"""
        
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'screen': {'width': 1920, 'height': 1080},
            'user_agent': UltraStealthEngine._get_random_user_agent(),
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation'],
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},  # New York
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
            'bypass_csp': True,
            'ignore_https_errors': True,
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Chromium";v="120", "Google Chrome";v="120", "Not-A.Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
        }
        
        if proxy_config:
            context_options['proxy'] = proxy_config
            
        context = await browser.new_context(**context_options)
        
        # Apply stealth to all new pages
        async def on_page(page):
            await UltraStealthEngine.apply_ultra_stealth(page)
            
        context.on('page', on_page)
        
        return context
        
    @staticmethod
    def _get_random_user_agent() -> str:
        """Get a random realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        ]
        return random.choice(user_agents)
        
    @staticmethod
    async def simulate_human_behavior(page: Page) -> None:
        """Simulate realistic human behavior on page"""
        
        # Random mouse movements
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1800)
            y = random.randint(100, 900)
            await page.mouse.move(x, y, steps=random.randint(10, 30))
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
        # Random scrolls
        for _ in range(random.randint(1, 3)):
            await page.evaluate(f"window.scrollTo(0, {random.randint(100, 500)})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
        # Random viewport interactions
        if random.random() < 0.3:
            await page.mouse.wheel(0, random.randint(50, 200))
            await asyncio.sleep(random.uniform(0.2, 0.5))