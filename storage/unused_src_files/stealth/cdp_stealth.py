"""
CDP-based Stealth Implementation
Uses Chrome DevTools Protocol for deeper control
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import Browser, BrowserContext, Page
from .advanced_fingerprint import AdvancedFingerprint

logger = logging.getLogger(__name__)


class CDPStealthEngine:
    """Advanced stealth using Chrome DevTools Protocol"""
    
    @staticmethod
    async def create_undetectable_browser(browser_type) -> Browser:
        """Create a browser instance that's undetectable"""
        
        # browser_type is already a BrowserType (e.g., playwright.chromium)
        browser = await browser_type.launch(
            headless=False,  # Headless is easier to detect
            args=[
                # Critical for stealth
                '--disable-blink-features=AutomationControlled',
                
                # Disable automation flags
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                
                # Disable WebDriver
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                
                # Network
                '--disable-http2',
                '--force-http1',
                '--aggressive-cache-discard',
                '--disable-background-networking',
                
                # Performance
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                
                # Other stealth flags
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--password-store=basic',
                '--use-mock-keychain',
                '--force-color-profile=srgb',
                '--disable-features=UserAgentClientHint',
                
                # GPU
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu-sandbox',
                
                # Automation
                '--disable-blink-features=AutomationControlled',
                '--disable-features=site-per-process',
                '--disable-features=AudioServiceOutOfProcess',
                '--disable-features=IsolateOrigins',
                '--disable-features=site-per-process',
                
                # Additional anti-detection flags
                '--disable-features=ChromeWhatsNewUI',
                '--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints',
                '--disable-features=ChromePasswordManagerOnboardingAndroid',
                '--disable-features=FlashDeprecationWarning',
                '--disable-features=EnablePasswordsAccountStorage',
                
                # Important: Use a real Chrome executable if available
                # '--executable-path=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ],
            
            # Remove default Playwright args that reveal automation
            ignore_default_args=['--enable-automation'],
            
            # Use Chrome channel for better compatibility
            channel='chrome',
        )
        
        return browser
        
    @staticmethod
    async def create_stealth_context(browser: Browser, proxy_config: Optional[Dict] = None) -> BrowserContext:
        """Create a stealth browser context with randomized fingerprint"""
        
        # Generate random fingerprint
        fingerprint = AdvancedFingerprint.generate_fingerprint()
        
        context_options = {
            'viewport': fingerprint['viewport'],
            'screen': fingerprint['screen'],
            'device_scale_factor': fingerprint['device_scale_factor'],
            'is_mobile': False,
            'has_touch': False,
            'user_agent': fingerprint['user_agent'],
            'accept_downloads': True,
            'locale': fingerprint['language'],
            'timezone_id': fingerprint['timezone'],
            'permissions': ['geolocation', 'notifications'],
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
            'ignore_https_errors': True,
            'bypass_csp': True,
            'java_script_enabled': True,
            'offline': False,
            'http_credentials': None,
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }
        }
        
        if proxy_config:
            context_options['proxy'] = proxy_config
            
        context = await browser.new_context(**context_options)
        
        # Store fingerprint for later use
        context._fingerprint = fingerprint
        
        # Add advanced stealth script
        await context.add_init_script(AdvancedFingerprint.get_stealth_script(fingerprint))
        
        # Add additional CDP-specific script
        await context.add_init_script("""
        // Remove webdriver before anything else loads
        delete Object.getPrototypeOf(navigator).webdriver;
        
        // CDP Stealth Script
        (() => {
            // Store the original getter
            const originalGet = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver');
            
            // Remove the property completely
            delete Navigator.prototype.webdriver;
            
            // Redefine it as undefined
            Object.defineProperty(Navigator.prototype, 'webdriver', {
                get: () => undefined,
                set: () => {},
                configurable: false,
                enumerable: false
            });
            
            // Also handle direct access
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                set: () => {},
                configurable: false,
                enumerable: false
            });
            
            // Remove other automation indicators
            delete window.__playwright;
            delete window.__selenium;
            delete window.__webdriver;
            
            // Fix Chrome object
            if (!window.chrome) {
                window.chrome = {};
            }
            
            window.chrome.runtime = {
                connect: () => {},
                sendMessage: () => {},
                onMessage: { addListener: () => {} }
            };
            
            window.chrome.loadTimes = function() {
                return {
                    commitLoadTime: Date.now() / 1000,
                    connectionInfo: "http/1.1",
                    finishDocumentLoadTime: Date.now() / 1000,
                    finishLoadTime: Date.now() / 1000,
                    firstPaintAfterLoadTime: 0,
                    firstPaintTime: Date.now() / 1000,
                    navigationType: "Reload",
                    npnNegotiatedProtocol: "unknown",
                    requestTime: Date.now() / 1000,
                    startLoadTime: Date.now() / 1000,
                    wasAlternateProtocolAvailable: false,
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false
                };
            };
            
            window.chrome.csi = function() { 
                return {
                    onloadT: Date.now(),
                    pageT: Date.now() + Math.random() * 1000,
                    startE: Date.now() - 1000,
                    tran: 15
                };
            };
            
            // Fix permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: 'default' });
                }
                return originalQuery(parameters);
            };
            
            // Fix plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [
                        {
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin",
                            [0]: {
                                description: "Portable Document Format",
                                enabledPlugin: {},
                                suffixes: "pdf",
                                type: "application/x-google-chrome-pdf"
                            }
                        },
                        {
                            description: "Portable Document Format",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer",
                            [0]: {
                                description: "Portable Document Format",
                                enabledPlugin: {},
                                suffixes: "pdf",
                                type: "application/pdf"
                            }
                        }
                    ];
                    
                    arr.item = (i) => arr[i];
                    arr.namedItem = (name) => arr.find(p => p.name === name);
                    arr.refresh = () => {};
                    
                    return arr;
                }
            });
            
            // Fix WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.apply(this, arguments);
            };
            
            // Fix hairline
            Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
                get() {
                    const height = Math.floor(this.getBoundingClientRect().height);
                    if (this.id === 'modernizr' || (height === 1 && this.style && this.style.display === 'block')) {
                        return 2;
                    }
                    return height;
                }
            });
            
            Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
                get() {
                    const width = Math.floor(this.getBoundingClientRect().width);
                    if (this.id === 'modernizr' || (width === 1 && this.style && this.style.display === 'block')) {
                        return 2;
                    }
                    return width;
                }
            });
        })();
        """)
        
        return context
        
    @staticmethod
    async def apply_page_stealth(page: Page) -> None:
        """Apply additional stealth measures to a page"""
        
        try:
            # Use CDP to remove webdriver property
            client = await page.context.new_cdp_session(page)
            
            # Override navigator.webdriver using CDP with multiple methods
            await client.send('Page.addScriptToEvaluateOnNewDocument', {
                'source': """
                // Remove webdriver
                delete Object.getPrototypeOf(navigator).webdriver;
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Remove CDP runtime detection
                (function() {
                    const originalCall = Function.prototype.call;
                    Function.prototype.call = function(...args) {
                        if (args[1] && args[1].includes && args[1].includes('Runtime.')) {
                            return undefined;
                        }
                        return originalCall.apply(this, args);
                    };
                })();
                
                // Hide automation indicators
                window.chrome = window.chrome || {};
                window.chrome.runtime = window.chrome.runtime || {};
                """
            })
            
            # Get current context user agent
            user_agent = page.context._options.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
            
            # Remove automation header
            await client.send('Network.setUserAgentOverride', {
                'userAgent': user_agent,
                'acceptLanguage': 'en-US,en;q=0.9',
                'platform': 'Win32'
            })
            
            # Enable stealth mode for runtime
            await client.send('Runtime.enable')
            
            # Emulate human-like behavior
            await client.send('Emulation.setIdleOverride', {'isUserActive': True, 'isScreenUnlocked': True})
            
            # Set touch enabled to false (desktop)
            await client.send('Emulation.setTouchEmulationEnabled', {'enabled': False})
            
            # Set hardware concurrency based on fingerprint
            if hasattr(page.context, '_fingerprint'):
                hardware_concurrency = page.context._fingerprint.get('hardware_concurrency', 8)
            else:
                hardware_concurrency = 8
            await client.send('Emulation.setHardwareConcurrencyOverride', {'hardwareConcurrency': hardware_concurrency})
            
            logger.info("✅ CDP stealth measures applied")
            
        except Exception as e:
            logger.debug(f"CDP stealth application warning: {e}")
            # Continue even if CDP fails - page might still work
        
    @staticmethod
    async def simulate_human_mouse(page: Page) -> None:
        """Simulate human-like mouse movements"""
        import math
        
        viewport = page.viewport_size
        if not viewport:
            return
            
        # Generate smooth curve
        steps = 20
        start_x, start_y = 100, 100
        end_x = viewport['width'] - 100
        end_y = viewport['height'] - 100
        
        for i in range(steps):
            t = i / steps
            # Use sine wave for smooth movement
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * math.sin(t * math.pi / 2)
            
            await page.mouse.move(x, y)
            await asyncio.sleep(0.01)
            
    @staticmethod
    async def type_like_human(page: Page, selector: str, text: str) -> None:
        """Type text with human-like delays"""
        import random
        
        element = await page.query_selector(selector)
        if not element:
            return
            
        await element.click()
        
        for char in text:
            await page.keyboard.type(char)
            # Variable delay between keystrokes
            delay = random.uniform(0.05, 0.25)
            if random.random() < 0.1:  # 10% chance of longer pause
                delay += random.uniform(0.5, 1.0)
            await asyncio.sleep(delay)