"""Advanced Akamai bot detection bypass techniques."""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, BrowserContext

# Import ultimate bypass for advanced mode
try:
    from .ultimate_bypass import UltimateAkamaiBypass, StealthMasterBot
    ULTIMATE_MODE_AVAILABLE = True
except ImportError:
    ULTIMATE_MODE_AVAILABLE = False

logger = logging.getLogger(__name__)


class AkamaiBypass:
    """Specialized techniques for bypassing Akamai bot detection."""
    
    def __init__(self):
        """Initialize Akamai bypass with optional ultimate mode."""
        self.ultimate_mode = False
        self.ultimate_bypass = None
        
    def enable_ultimate_mode(self):
        """Enable ultimate bypass mode if available."""
        if ULTIMATE_MODE_AVAILABLE:
            self.ultimate_mode = True
            self.ultimate_bypass = UltimateAkamaiBypass()
            logger.info("Ultimate Akamai bypass mode enabled")
        else:
            logger.warning("Ultimate mode not available - missing dependencies")
    
    @staticmethod
    def get_bypass_script():
        """Get the Akamai bypass JavaScript code."""
        return """
                // Critical: Override webdriver detection
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                    configurable: false,
                    enumerable: true
                });
                
                // Fix Chrome runtime
                if (!window.chrome) {
                    window.chrome = {
                        runtime: {
                            connect: () => {},
                            sendMessage: () => {},
                            onMessage: { addListener: () => {} }
                        },
                        loadTimes: () => ({
                            requestTime: Date.now() / 1000,
                            startLoadTime: Date.now() / 1000,
                            commitLoadTime: Date.now() / 1000,
                            finishDocumentLoadTime: Date.now() / 1000,
                            finishLoadTime: Date.now() / 1000,
                            firstPaintTime: Date.now() / 1000,
                            firstPaintAfterLoadTime: 0,
                            navigationType: "Other",
                            wasFetchedViaSpdy: false,
                            wasNpnNegotiated: false,
                            npnNegotiatedProtocol: "",
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: "http/1.1"
                        }),
                        csi: () => ({
                            onloadT: Date.now(),
                            pageT: Date.now() - 1000,
                            startE: Date.now() - 2000,
                            tran: 15
                        })
                    };
                }
                
                // Override CDP detection
                delete Object.getPrototypeOf(navigator).webdriver;
                
                // Akamai sensor data expectations
                window._abck = window._abck || {};
                
                // Fix language/languages inconsistency
                Object.defineProperty(navigator, 'language', {
                    get: () => 'en-US',
                    configurable: false
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    configurable: false
                });
        """
    
    @staticmethod
    async def apply_bypass(page: Page) -> None:
        """Apply Akamai-specific bypass techniques."""
        try:
            # Check if this is Selenium or Playwright
            if hasattr(page, 'execute_script'):
                # Selenium - execute the bypass script directly
                page.execute_script(AkamaiBypass.get_bypass_script())
                logger.debug("Applied Akamai bypass for Selenium")
            else:
                # Playwright - use original implementation
                # 1. Pre-inject critical overrides before page loads
                await page.add_init_script(AkamaiBypass.get_bypass_script())
                
                # 2. Set proper user agent
                await page.set_extra_http_headers({
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                })
                
                # 3. Handle Akamai challenges and sensor data
                await page.route('**/_bm/**', lambda route: route.continue_())
                await page.route('**/akam/**', lambda route: route.continue_())
                
                # 4. Additional browser context fixes for Fansale
                await page.evaluate("""
                    // Fix for Fansale specifically
                    window.bmak = window.bmak || {};
                    window.bmak.js_post = false;
                    window.bmak.fpcf = { f: () => 0, s: () => {} };
                    window.bmak.sensor_data = '-1';
                    
                    // Mock touch support for consistency
                    Object.defineProperty(navigator, 'maxTouchPoints', {
                        get: () => 0,
                        configurable: false
                    });
                    
                    // Fix hardwareConcurrency
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8,
                        configurable: false
                    });
                    
                    // Fix deviceMemory
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => 8,
                        configurable: false
                    });
                """)
                
                logger.info("Applied Akamai bypass techniques")
            
        except Exception as e:
            logger.error(f"Failed to apply Akamai bypass: {e}")
    
    @staticmethod
    async def handle_challenge(page: Page) -> bool:
        """Handle Akamai challenge if detected."""
        try:
            # Check for Akamai challenge
            if hasattr(page, 'content'):
                # Playwright
                content = await page.content()
            else:
                # Selenium
                content = page.page_source
            
            if '_abck' in content or 'akamai' in content.lower():
                logger.info("Akamai challenge detected, waiting for sensor data...")
                
                # Wait for sensor data to be collected
                if hasattr(page, 'wait_for_timeout'):
                    # Playwright
                    await page.wait_for_timeout(3000)
                    
                    # Trigger some human-like events
                    await page.mouse.move(100, 100)
                    await page.mouse.move(200, 200)
                    await page.mouse.move(150, 150)
                    
                    # Wait for challenge to complete
                    await page.wait_for_timeout(2000)
                else:
                    # Selenium - simple wait
                    await asyncio.sleep(3)
                    
                    # Trigger mouse movement via JavaScript
                    page.execute_script("""
                        var event = new MouseEvent('mousemove', {
                            clientX: 100, clientY: 100
                        });
                        document.dispatchEvent(event);
                    """)
                    
                    await asyncio.sleep(2)
                
                return True
                
        except Exception as e:
            logger.error(f"Error handling Akamai challenge: {e}")
            
        return False
    
    @staticmethod
    async def prepare_for_fansale_login(page: Page) -> None:
        """Special preparation for Fansale login to avoid detection."""
        try:
            # Wait for page to be ready
            await page.wait_for_load_state('networkidle')
            
            # Add human-like behavior
            await page.wait_for_timeout(2000)
            
            # Move mouse randomly to simulate human
            for _ in range(3):
                x = 100 + (200 * asyncio.get_event_loop().time() % 1)
                y = 100 + (200 * asyncio.get_event_loop().time() % 1)
                await page.mouse.move(x, y)
                await page.wait_for_timeout(500)
            
            # Pre-inject additional stealth for login
            await page.evaluate("""
                // Override more detection methods
                Object.defineProperty(navigator.connection, 'rtt', {
                    get: () => 50 + Math.random() * 100
                });
                
                // Fix keyboard/mouse event properties
                const originalAddEventListener = EventTarget.prototype.addEventListener;
                EventTarget.prototype.addEventListener = function(type, listener, options) {
                    if (type === 'click' || type === 'mousedown' || type === 'mouseup') {
                        const newListener = function(event) {
                            if (event.isTrusted === false) {
                                Object.defineProperty(event, 'isTrusted', {
                                    get: () => true
                                });
                            }
                            return listener.call(this, event);
                        };
                        return originalAddEventListener.call(this, type, newListener, options);
                    }
                    return originalAddEventListener.call(this, type, listener, options);
                };
                
                // Set realistic window properties
                Object.defineProperty(window.screen, 'availWidth', {
                    get: () => window.screen.width
                });
                Object.defineProperty(window.screen, 'availHeight', {
                    get: () => window.screen.height - 25
                });
            """)
            
            logger.info("Prepared page for Fansale login")
            
        except Exception as e:
            logger.error(f"Error preparing for Fansale login: {e}")