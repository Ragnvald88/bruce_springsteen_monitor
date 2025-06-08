"""
StealthMaster AI Integration Module
Integrates CDP stealth into the main application
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import Browser, BrowserContext, Page

from .cdp_stealth import CDPStealthEngine
from .ultra_stealth import UltraStealthEngine

logger = logging.getLogger(__name__)


class StealthIntegration:
    """Integrates all stealth measures for the ticket monitoring system"""
    
    @staticmethod
    async def create_stealth_browser(playwright, headless: bool = True) -> Browser:
        """Create a browser with maximum stealth capabilities"""
        
        # For critical operations like Ticketmaster, use headful
        if not headless:
            logger.info("🖥️ Running in headful mode for maximum stealth")
            
        # Use CDP stealth for undetectable browser
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-http2',
                '--force-http1',
                '--aggressive-cache-discard',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--password-store=basic',
                '--use-mock-keychain',
                '--force-color-profile=srgb',
                '--disable-features=UserAgentClientHint',
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu-sandbox',
                '--window-size=1920,1080',
                '--start-maximized',
            ],
            ignore_default_args=['--enable-automation'],
            channel='chrome',  # Use real Chrome
        )
        
        return browser
        
    @staticmethod
    async def create_stealth_context(
        browser: Browser, 
        profile_config: Dict[str, Any],
        proxy_config: Optional[Dict] = None
    ) -> BrowserContext:
        """Create a context with all stealth measures applied"""
        
        # Base context options from profile
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'screen': {'width': 1920, 'height': 1080},
            'user_agent': profile_config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ),
            'locale': profile_config.get('locale', 'en-US'),
            'timezone_id': profile_config.get('timezone', 'America/New_York'),
            'permissions': ['geolocation', 'notifications'],
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
            'bypass_csp': True,
            'ignore_https_errors': True,
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
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
        
        # Add proxy if configured
        if proxy_config:
            context_options['proxy'] = proxy_config
            logger.info(f"🔐 Using proxy: {proxy_config.get('server', 'Unknown')}")
            
        # Create context
        context = await browser.new_context(**context_options)
        
        # Apply CDP stealth init script
        await context.add_init_script("""
        // StealthMaster AI Init Script
        (() => {
            // Remove webdriver property
            delete Object.getPrototypeOf(navigator).webdriver;
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: false,
                enumerable: false
            });
            
            // Remove automation artifacts
            delete window.__playwright;
            delete window.__selenium;
            delete window.__webdriver;
            
            // Fix Chrome object
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {},
                    onMessage: { addListener: () => {} }
                },
                loadTimes: function() {
                    return {
                        commitLoadTime: Date.now() / 1000,
                        connectionInfo: "http/1.1",
                        finishDocumentLoadTime: Date.now() / 1000,
                        finishLoadTime: Date.now() / 1000,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: Date.now() / 1000,
                        navigationType: "Other",
                        npnNegotiatedProtocol: "unknown",
                        requestTime: Date.now() / 1000,
                        startLoadTime: Date.now() / 1000,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false
                    };
                },
                csi: function() { return {}; },
                app: {}
            };
            
            // Fix plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [
                        {
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        }
                    ];
                    arr.item = (i) => arr[i];
                    arr.namedItem = (name) => arr.find(p => p.name === name);
                    arr.refresh = () => {};
                    return arr;
                }
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: 'default' });
                }
                return originalQuery(parameters);
            };
        })();
        """)
        
        return context
        
    @staticmethod
    async def apply_page_stealth(page: Page) -> None:
        """Apply all stealth measures to a page"""
        
        # Apply CDP stealth
        await CDPStealthEngine.apply_page_stealth(page)
        
        # Apply additional ultra stealth measures
        await UltraStealthEngine.apply_ultra_stealth(page)
        
        logger.info("✅ All stealth measures applied to page")
        
    @staticmethod
    async def create_stealth_page(
        browser: Browser,
        profile_config: Dict[str, Any],
        proxy_config: Optional[Dict] = None,
        platform: Optional[str] = None
    ) -> tuple[BrowserContext, Page]:
        """Create a fully stealthed context and page"""
        
        # Platform-specific adjustments
        if platform == 'fansale':
            profile_config['locale'] = 'it-IT'
            profile_config['timezone'] = 'Europe/Rome'
            logger.info("🇮🇹 Using Italian locale for Fansale")
            
        elif platform == 'ticketmaster':
            # Ticketmaster is most suspicious of automation
            logger.info("🎫 Using enhanced stealth for Ticketmaster")
            
        # Create context
        context = await StealthIntegration.create_stealth_context(
            browser, 
            profile_config, 
            proxy_config
        )
        
        # Create page
        page = await context.new_page()
        
        # Apply page-level stealth
        await StealthIntegration.apply_page_stealth(page)
        
        # Add human behavior simulation
        await StealthIntegration._add_human_behavior(page)
        
        return context, page
        
    @staticmethod
    async def _add_human_behavior(page: Page) -> None:
        """Add human-like behavior patterns to page"""
        
        await page.add_init_script("""
        // Human behavior simulation
        (() => {
            // Random mouse movements
            let mouseX = 100, mouseY = 100;
            
            setInterval(() => {
                if (Math.random() < 0.1) {  // 10% chance every interval
                    mouseX += (Math.random() - 0.5) * 50;
                    mouseY += (Math.random() - 0.5) * 50;
                    
                    // Keep within viewport
                    mouseX = Math.max(0, Math.min(window.innerWidth, mouseX));
                    mouseY = Math.max(0, Math.min(window.innerHeight, mouseY));
                    
                    // Dispatch mouse event
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX,
                        clientY: mouseY,
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                }
            }, 1000);
            
            // Random scrolls
            let lastScroll = Date.now();
            
            setInterval(() => {
                if (Date.now() - lastScroll > 5000 && Math.random() < 0.3) {
                    window.scrollBy({
                        top: (Math.random() - 0.5) * 200,
                        behavior: 'smooth'
                    });
                    lastScroll = Date.now();
                }
            }, 2000);
        })();
        """)
        
    @staticmethod
    async def handle_detection(page: Page, platform: str) -> bool:
        """Handle detection and recovery"""
        
        content = await page.content()
        
        # Check for common detection indicators
        detected = False
        
        if 'captcha' in content.lower() or 'challenge' in content.lower():
            logger.warning(f"⚠️ Captcha detected on {platform}")
            detected = True
            
        if any(word in content.lower() for word in ['blocked', 'forbidden', 'denied']):
            logger.warning(f"⚠️ Access blocked on {platform}")
            detected = True
            
        if detected:
            # Platform-specific recovery
            if platform == 'ticketmaster':
                logger.info("Attempting Ticketmaster recovery...")
                # Wait longer before retry
                await asyncio.sleep(30)
                
            elif platform == 'fansale':
                logger.info("Attempting Fansale recovery...")
                # Clear cookies and retry
                await page.context.clear_cookies()
                await asyncio.sleep(10)
                
        return detected
        
    @staticmethod
    def get_platform_config(platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        
        configs = {
            'fansale': {
                'headless': True,  # Fansale works with headless
                'locale': 'it-IT',
                'timezone': 'Europe/Rome',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1920, 'height': 1080}
            },
            'ticketmaster': {
                'headless': False,  # Ticketmaster needs headful
                'locale': 'it-IT',
                'timezone': 'Europe/Rome',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1920, 'height': 1080}
            },
            'vivaticket': {
                'headless': True,
                'locale': 'it-IT',
                'timezone': 'Europe/Rome',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1920, 'height': 1080}
            }
        }
        
        return configs.get(platform, configs['fansale'])