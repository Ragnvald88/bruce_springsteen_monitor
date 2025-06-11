"""
StealthMaster Core - CDP-Optional Architecture
Uses nodriver-inspired techniques to avoid detection at protocol level
"""

import asyncio
import json
import random
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.async_api import Page, Browser, BrowserContext
    
try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None
    
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
except ImportError:
    webdriver = None
    Service = None

from ..utils.logging import get_logger
from .fingerprint import FingerprintGenerator

logger = get_logger(__name__)


class NodriverCore:
    """
    Stealth Core - Implements CDP-optional automation
    Inspired by nodriver's approach of avoiding CDP detection entirely
    """
    
    def __init__(self):
        self.fingerprint_gen = FingerprintGenerator()
        self.use_undetected_chrome = True  # Primary mode
        self.proxy_rotation_enabled = True
        self.residential_proxies: List[str] = []
        self._stats = {
            "sessions_created": 0,
            "detections_avoided": 0,
            "successful_operations": 0
        }
    
    async def create_stealth_browser(self, **kwargs) -> Dict[str, Any]:
        """
        Create truly undetectable browser instance
        Uses undetected-chromedriver as primary, Playwright as fallback
        """
        try:
            if self.use_undetected_chrome:
                return await self._create_undetected_browser(**kwargs)
            else:
                return await self._create_playwright_browser(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create stealth browser: {e}")
            # Fallback to alternative method
            self.use_undetected_chrome = not self.use_undetected_chrome
            return await self.create_stealth_browser(**kwargs)
    
    async def _create_undetected_browser(self, **kwargs) -> Dict[str, Any]:
        """Create browser using undetected-chromedriver (no CDP detection)"""
        options = uc.ChromeOptions()
        
        # V4 Optimizations - learned from V3's successes
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Performance optimizations from V3
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Fingerprint randomization
        fingerprint = self.fingerprint_gen.generate()
        viewport = fingerprint.get('viewport', {})
        options.add_argument(f'--window-size={viewport.get("width", 1920)},{viewport.get("height", 1080)}')
        
        # User agent rotation
        user_agent = fingerprint.get('userAgent', self._get_random_user_agent())
        options.add_argument(f'--user-agent={user_agent}')
        
        # Proxy support
        if self.proxy_rotation_enabled and self.residential_proxies:
            proxy = random.choice(self.residential_proxies)
            options.add_argument(f'--proxy-server={proxy}')
        
        # Language and timezone
        options.add_argument(f'--lang={fingerprint.get("language", "en-US")}')
        
        # Create driver
        driver = uc.Chrome(options=options, version_main=None)
        
        # Apply runtime stealth patches
        await self._apply_runtime_patches(driver)
        
        self._stats["sessions_created"] += 1
        
        return {
            "driver": driver,
            "fingerprint": fingerprint,
            "type": "undetected_chrome"
        }
    
    async def _apply_runtime_patches(self, driver):
        """Apply additional stealth patches at runtime"""
        scripts = [
            # Remove webdriver property
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            
            # Fix chrome.runtime
            """
            if (!window.chrome) window.chrome = {};
            if (!window.chrome.runtime) window.chrome.runtime = {};
            """,
            
            # Permissions API
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """,
            
            # Plugin array
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [];
                    arr.item = () => null;
                    arr.namedItem = () => null;
                    arr.refresh = () => {};
                    
                    // Add fake PDF plugin
                    const plugin = {
                        name: 'Chrome PDF Plugin',
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 1,
                        item: (i) => i === 0 ? {
                            type: 'application/x-google-chrome-pdf',
                            suffixes: 'pdf',
                            description: 'Portable Document Format',
                            enabledPlugin: plugin
                        } : null,
                        namedItem: (n) => n === 'Chrome PDF Plugin' ? plugin : null
                    };
                    
                    arr.push(plugin);
                    return arr;
                }
            });
            """,
            
            # Canvas fingerprinting protection
            """
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {
                const ctx = this.getContext('2d');
                if (ctx) {
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = imageData.data[i] ^ (Math.random() * 2);
                        imageData.data[i + 1] = imageData.data[i + 1] ^ (Math.random() * 2);
                        imageData.data[i + 2] = imageData.data[i + 2] ^ (Math.random() * 2);
                    }
                    ctx.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, args);
            };
            """,
            
            # WebGL vendor spoofing
            """
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            """,
            
            # Battery API spoofing
            """
            if (navigator.getBattery) {
                navigator.getBattery = () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1,
                    addEventListener: () => {},
                    removeEventListener: () => {}
                });
            }
            """
        ]
        
        for script in scripts:
            try:
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': script
                })
            except:
                # Fallback to execute_script if CDP not available
                driver.execute_script(script)
        
        self._stats["detections_avoided"] += 1
    
    async def _create_playwright_browser(self, **kwargs) -> Dict[str, Any]:
        """Fallback Playwright browser with maximum stealth"""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        
        # Use Firefox for better stealth (no CDP)
        browser = await playwright.firefox.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        fingerprint = self.fingerprint_gen.generate()
        
        context = await browser.new_context(
            viewport={
                'width': fingerprint['viewport']['width'],
                'height': fingerprint['viewport']['height']
            },
            user_agent=fingerprint['userAgent'],
            locale=fingerprint['language'],
            timezone_id=fingerprint['timezone']
        )
        
        # Apply stealth scripts to context
        await context.add_init_script("""
            // Same stealth patches as above
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Additional Firefox-specific patches
            delete Object.getPrototypeOf(navigator).webdriver;
        """)
        
        page = await context.new_page()
        
        return {
            "browser": browser,
            "context": context,
            "page": page,
            "fingerprint": fingerprint,
            "type": "playwright_firefox"
        }
    
    def _get_random_user_agent(self) -> str:
        """Get random realistic user agent"""
        user_agents = [
            # Chrome 122+ on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            
            # Chrome on Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
        ]
        return random.choice(user_agents)
    
    async def enhance_stealth_for_page(self, page: Any) -> None:
        """Apply additional stealth enhancements to existing page"""
        if hasattr(page, 'execute_script'):
            # Selenium page
            await self._apply_runtime_patches(page)
        else:
            # Playwright page
            await page.evaluate("""
                // Apply all stealth patches
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Fix chrome object
                if (!window.chrome) window.chrome = {};
                if (!window.chrome.runtime) window.chrome.runtime = {};
            """)
    
    def get_stats(self) -> Dict[str, int]:
        """Get stealth operation statistics"""
        return self._stats.copy()
    
    def add_residential_proxy(self, proxy: str) -> None:
        """Add residential proxy to rotation pool"""
        self.residential_proxies.append(proxy)
        logger.info(f"Added residential proxy to pool: {proxy[:20]}...")
    
    def clear_proxy_pool(self) -> None:
        """Clear all proxies from pool"""
        self.residential_proxies.clear()
        logger.info("Cleared proxy pool")


# Global instance
nodriver_core = NodriverCore()