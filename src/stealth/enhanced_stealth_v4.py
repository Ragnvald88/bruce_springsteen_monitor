"""
Enhanced Stealth v4.0 - Ultimate Anti-Detection System
Fixes blocking issues on Fansale and Ticketmaster
"""

from playwright.async_api import Page, BrowserContext
import logging
import random
import asyncio

logger = logging.getLogger(__name__)


class EnhancedStealthV4:
    """Advanced stealth implementation to bypass all detection methods"""
    
    @staticmethod
    async def apply_ultra_stealth(page: Page, context: BrowserContext) -> None:
        """Apply comprehensive stealth measures to page and context"""
        
        # 1. CDP Detection Bypass - Critical for avoiding blocks
        await context.add_init_script("""
        // CDP Detection Bypass v4.0
        (() => {
            // Remove CDP runtime detection
            const originalCall = Function.prototype.call;
            Function.prototype.call = function(...args) {
                if (this.toString().includes('Runtime.enable')) {
                    return undefined;
                }
                return originalCall.apply(this, args);
            };
            
            // Hide CDP properties
            Object.defineProperty(window, 'chrome', {
                get: function() {
                    return {
                        runtime: {
                            getManifest: undefined,
                            connect: undefined,
                            sendMessage: undefined
                        },
                        loadTimes: function() {
                            return {
                                commitLoadTime: Date.now() / 1000,
                                connectionInfo: "http/1.1",
                                finishDocumentLoadTime: Date.now() / 1000,
                                finishLoadTime: Date.now() / 1000,
                                firstPaintAfterLoadTime: 0,
                                firstPaintTime: Date.now() / 1000,
                                navigationType: "navigate",
                                npnNegotiatedProtocol: "h2",
                                requestTime: Date.now() / 1000,
                                startLoadTime: Date.now() / 1000,
                                wasAlternateProtocolAvailable: false,
                                wasFetchedViaSpdy: true,
                                wasNpnNegotiated: true
                            };
                        },
                        csi: function() { return {}; }
                    };
                }
            });
        })();
        """)
        
        # 2. WebDriver Detection Bypass
        await page.add_init_script("""
        // WebDriver Bypass v4.0
        (() => {
            // Multiple approaches to ensure webdriver is hidden
            delete Object.getPrototypeOf(navigator).webdriver;
            
            const newProto = Object.create(Object.getPrototypeOf(navigator));
            delete newProto.webdriver;
            Object.setPrototypeOf(navigator, newProto);
            
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: false,
                enumerable: false
            });
            
            // Also hide in window
            delete window.navigator.webdriver;
        })();
        """)
        
        # 3. Advanced Permissions Bypass
        await page.add_init_script("""
        // Permissions Bypass v4.0
        (() => {
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = async (parameters) => {
                if (parameters.name === 'notifications') {
                    return { state: 'prompt', onchange: null };
                }
                if (parameters.name === 'geolocation') {
                    return { state: 'prompt', onchange: null };
                }
                if (parameters.name === 'camera' || parameters.name === 'microphone') {
                    return { state: 'denied', onchange: null };
                }
                try {
                    return await originalQuery.call(window.navigator.permissions, parameters);
                } catch {
                    return { state: 'prompt', onchange: null };
                }
            };
        })();
        """)
        
        # 4. Plugin Spoofing - Critical for Ticketmaster
        await page.add_init_script("""
        // Plugin Spoofing v4.0
        (() => {
            const pluginData = [
                {
                    name: "Chrome PDF Plugin",
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    mimeTypes: [{
                        type: "application/x-google-chrome-pdf",
                        suffixes: "pdf",
                        description: "Portable Document Format"
                    }]
                },
                {
                    name: "Chrome PDF Viewer", 
                    description: "Portable Document Format",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    mimeTypes: [{
                        type: "application/pdf",
                        suffixes: "pdf",
                        description: "Portable Document Format"
                    }]
                },
                {
                    name: "Native Client",
                    description: "Native Client",
                    filename: "internal-nacl-plugin",
                    mimeTypes: [
                        {
                            type: "application/x-nacl",
                            suffixes: "",
                            description: "Native Client Executable"
                        },
                        {
                            type: "application/x-pnacl",
                            suffixes: "",
                            description: "Portable Native Client Executable"
                        }
                    ]
                }
            ];
            
            // Create proper PluginArray
            const pluginArray = Object.create(PluginArray.prototype);
            pluginData.forEach((data, i) => {
                const plugin = Object.create(Plugin.prototype);
                plugin.name = data.name;
                plugin.description = data.description;
                plugin.filename = data.filename;
                plugin.length = data.mimeTypes.length;
                
                data.mimeTypes.forEach((mime, j) => {
                    const mimeType = Object.create(MimeType.prototype);
                    mimeType.type = mime.type;
                    mimeType.suffixes = mime.suffixes;
                    mimeType.description = mime.description;
                    mimeType.enabledPlugin = plugin;
                    plugin[j] = mimeType;
                    plugin[mime.type] = mimeType;
                });
                
                plugin.item = function(index) { return this[index] || null; };
                plugin.namedItem = function(name) { return this[name] || null; };
                
                pluginArray[i] = plugin;
                pluginArray[data.name] = plugin;
            });
            
            pluginArray.length = pluginData.length;
            pluginArray.item = function(index) { return this[index] || null; };
            pluginArray.namedItem = function(name) { return this[name] || null; };
            pluginArray.refresh = function() {};
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => pluginArray,
                configurable: false,
                enumerable: true
            });
        })();
        """)
        
        # 5. Canvas Fingerprinting Protection
        await page.add_init_script("""
        // Canvas Protection v4.0
        (() => {
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            
            const canvasNoise = () => Math.random() * 0.1 - 0.05;
            
            HTMLCanvasElement.prototype.toDataURL = function(...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += canvasNoise();
                        imageData.data[i + 1] += canvasNoise();
                        imageData.data[i + 2] += canvasNoise();
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, args);
            };
            
            HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += canvasNoise();
                        imageData.data[i + 1] += canvasNoise();
                        imageData.data[i + 2] += canvasNoise();
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToBlob.call(this, callback, ...args);
            };
        })();
        """)
        
        # 6. WebGL Fingerprinting Protection
        await page.add_init_script("""
        // WebGL Protection v4.0
        (() => {
            const vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD'];
            const renderers = [
                'Intel Iris OpenGL Engine',
                'NVIDIA GeForce GTX 1080 Ti',
                'AMD Radeon Pro 5500M'
            ];
            
            const randomVendor = vendors[Math.floor(Math.random() * vendors.length)];
            const randomRenderer = renderers[Math.floor(Math.random() * renderers.length)];
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return randomVendor;
                if (parameter === 37446) return randomRenderer;
                return getParameter.apply(this, arguments);
            };
            
            if (WebGL2RenderingContext) {
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return randomVendor;
                    if (parameter === 37446) return randomRenderer;
                    return getParameter2.apply(this, arguments);
                };
            }
        })();
        """)
        
        # 7. Advanced Navigator Properties
        await page.add_init_script("""
        // Navigator Properties v4.0
        (() => {
            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: false
            });
            
            Object.defineProperty(navigator, 'language', {
                get: () => 'en-US',
                configurable: false
            });
            
            // Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 4 + Math.floor(Math.random() * 4),
                configurable: false
            });
            
            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => Math.pow(2, Math.floor(Math.random() * 4) + 2),
                configurable: false
            });
            
            // Connection
            if (navigator.connection) {
                Object.defineProperty(navigator.connection, 'rtt', {
                    get: () => 50 + Math.floor(Math.random() * 100),
                    configurable: false
                });
            }
        })();
        """)
        
        # 8. Timezone Spoofing
        await page.add_init_script("""
        // Timezone Spoofing v4.0
        (() => {
            const timezone = 'Europe/Rome';  // Italian timezone
            
            // Override Date methods
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return -60; // Rome is UTC+1
            };
            
            // Intl.DateTimeFormat
            if (window.Intl && window.Intl.DateTimeFormat) {
                const originalDateTimeFormat = window.Intl.DateTimeFormat;
                window.Intl.DateTimeFormat = new Proxy(originalDateTimeFormat, {
                    construct(target, args) {
                        if (args.length > 1 && args[1].timeZone === undefined) {
                            args[1].timeZone = timezone;
                        }
                        return new target(...args);
                    }
                });
            }
        })();
        """)
        
        # 9. Battery API Spoofing
        await page.add_init_script("""
        // Battery API v4.0
        (() => {
            if ('getBattery' in navigator) {
                navigator.getBattery = async () => ({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.99,
                    onchargingchange: null,
                    onchargingtimechange: null,
                    ondischargingtimechange: null,
                    onlevelchange: null
                });
            }
        })();
        """)
        
        # 10. Mouse Movement Patterns
        async def add_human_mouse_movement():
            try:
                # Get page dimensions
                viewport = page.viewport_size
                if not viewport:
                    return
                    
                width = viewport['width']
                height = viewport['height']
                
                # Generate natural mouse path
                start_x = random.randint(100, width - 100)
                start_y = random.randint(100, height - 100)
                
                # Move mouse with natural curve
                await page.mouse.move(start_x, start_y)
                
                # Small random movements
                for _ in range(3):
                    dx = random.randint(-50, 50)
                    dy = random.randint(-50, 50)
                    new_x = max(0, min(width, start_x + dx))
                    new_y = max(0, min(height, start_y + dy))
                    
                    steps = random.randint(10, 20)
                    await page.mouse.move(new_x, new_y, steps=steps)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
            except Exception as e:
                logger.debug(f"Mouse movement error: {e}")
        
        # Apply mouse movements
        asyncio.create_task(add_human_mouse_movement())
        
        logger.info("Enhanced Stealth v4.0 measures applied successfully")