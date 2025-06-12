"""
Browser Launcher using Nodriver Core
Implements CDP-optional browser automation with enhanced stealth
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import uuid

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page
    from selenium.webdriver.remote.webdriver import WebDriver

from ..stealth.nodriver_core import nodriver_core
from ..stealth.fingerprint import fingerprint_generator
from ..database.statistics import stats_manager
from ..utils.logging import get_logger
# Config will be passed from main

logger = get_logger(__name__)


class NodriverBrowserLauncher:
    """
    Browser Launcher with nodriver integration
    Provides undetectable browser automation
    """
    
    def __init__(self, settings=None):
        self.browsers: Dict[str, Any] = {}
        self.contexts: Dict[str, Any] = {}
        self.fingerprints: Dict[str, Any] = {}
        self._session_id = f"launcher_{uuid.uuid4().hex[:8]}"
        self.settings = settings
        
        # Performance tracking
        self._launch_times: List[float] = []
        self._detection_attempts = 0
        self._successful_operations = 0
        
        # Configure nodriver with residential proxies if available
        self._configure_proxies()
        
        logger.info("Browser Launcher initialized")
    
    def _configure_proxies(self):
        """Configure residential proxies from config"""
        if not self.settings or not hasattr(self.settings, 'proxy_settings'):
            logger.warning("No proxy settings available")
            return
            
        proxy_settings = self.settings.proxy_settings
        
        if proxy_settings.enabled:
            proxy_list = proxy_settings.primary_pool
            for proxy in proxy_list:
                # Format proxy for nodriver
                if hasattr(proxy, 'host'):
                    proxy_str = f"{proxy.type}://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
                    nodriver_core.add_residential_proxy(proxy_str)
            logger.info(f"Configured {len(proxy_list)} residential proxies from settings")
    
    async def launch_browser(self, proxy=None, **kwargs) -> str:
        """
        Launch a new browser instance with stealth
        
        Args:
            proxy: Optional proxy configuration dict with 'server', 'username', 'password'
        
        Returns:
            browser_id: Unique identifier for the browser
        """
        start_time = time.time()
        browser_id = str(uuid.uuid4())
        
        try:
            # Set session-specific fingerprint
            fingerprint_generator.set_session_id(browser_id)
            
            # Get proxy from settings if not provided
            if not proxy and self.settings and hasattr(self.settings, 'proxy_settings'):
                if self.settings.proxy_settings.enabled and self.settings.proxy_settings.primary_pool:
                    # Select first proxy from pool
                    proxy_config = self.settings.proxy_settings.primary_pool[0]
                    proxy = {
                        'server': f"{proxy_config.type}://{proxy_config.host}:{proxy_config.port}",
                        'username': proxy_config.username,
                        'password': proxy_config.password
                    }
                    logger.info(f"🌐 Using proxy from settings: {proxy_config.host}:{proxy_config.port}")
                    logger.debug(f"Proxy type: {proxy_config.type}, Username: {proxy_config.username}")
                else:
                    logger.warning("⚠️ No proxy configured - using direct connection")
            
            # Add proxy to kwargs if provided
            if proxy:
                kwargs['proxy'] = proxy
            
            # Launch browser with nodriver core
            browser_data = await nodriver_core.create_stealth_browser(**kwargs)
            
            # Store browser data
            self.browsers[browser_id] = browser_data
            self.fingerprints[browser_id] = browser_data.get("fingerprint", {})
            
            # Track performance
            launch_time = (time.time() - start_time) * 1000
            self._launch_times.append(launch_time)
            
            # Record metric
            stats_manager.record_performance_metric(
                self._session_id,
                "browser_launch",
                launch_time,
                success=True
            )
            
            logger.info(f"Launched browser {browser_id} in {launch_time:.0f}ms")
            return browser_id
            
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            stats_manager.record_performance_metric(
                self._session_id,
                "browser_launch",
                (time.time() - start_time) * 1000,
                success=False
            )
            raise
    
    async def create_context(self, browser_id: str, **kwargs) -> str:
        """
        Create a new browser context with unique fingerprint
        
        Args:
            browser_id: Browser to create context in
            
        Returns:
            context_id: Unique identifier for the context
        """
        context_id = str(uuid.uuid4())
        
        try:
            browser_data = self.browsers.get(browser_id)
            if not browser_data:
                raise ValueError(f"Browser {browser_id} not found")
            
            # Generate context-specific fingerprint mutation
            base_fingerprint = self.fingerprints[browser_id]
            context_fingerprint = fingerprint_generator.mutate_slightly(base_fingerprint)
            
            if browser_data.get("type") == "undetected_chrome":
                # For Selenium/undetected-chromedriver, use the same session
                self.contexts[context_id] = {
                    "driver": browser_data["driver"],
                    "fingerprint": context_fingerprint,
                    "browser_id": browser_id
                }
            else:
                # For Playwright, create new context
                browser = browser_data.get("browser")
                context = await browser.new_context(
                    viewport={
                        "width": context_fingerprint["viewport"]["width"],
                        "height": context_fingerprint["viewport"]["height"]
                    },
                    user_agent=context_fingerprint["userAgent"],
                    locale=context_fingerprint["language"],
                    timezone_id=context_fingerprint["timezone"],
                    **kwargs
                )
                
                self.contexts[context_id] = {
                    "context": context,
                    "fingerprint": context_fingerprint,
                    "browser_id": browser_id
                }
            
            logger.debug(f"Created context {context_id} for browser {browser_id}")
            return context_id
            
        except Exception as e:
            logger.error(f"Failed to create context: {e}")
            raise
    
    async def new_page(self, context_id: str) -> Any:
        """
        Create a new page in the given context
        
        Args:
            context_id: Context to create page in
            
        Returns:
            Page object (Selenium WebDriver or Playwright Page)
        """
        try:
            context_data = self.contexts.get(context_id)
            if not context_data:
                raise ValueError(f"Context {context_id} not found")
            
            if "driver" in context_data:
                # Selenium - open new tab
                driver = context_data["driver"]
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                
                # Apply additional stealth
                await nodriver_core.enhance_stealth_for_page(driver)
                
                return driver
            else:
                # Playwright
                context = context_data["context"]
                page = await context.new_page()
                
                # Apply stealth enhancements
                await nodriver_core.enhance_stealth_for_page(page)
                
                return page
                
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise
    
    @asynccontextmanager
    async def get_page(self, platform: Optional[str] = None):
        """
        Context manager for getting a stealth page
        
        Args:
            platform: Optional platform identifier for stats
            
        Yields:
            Page object ready for automation
        """
        browser_id = None
        context_id = None
        page = None
        
        try:
            # Launch browser
            browser_id = await self.launch_browser()
            
            # Create context
            context_id = await self.create_context(browser_id)
            
            # Create page
            page = await self.new_page(context_id)
            
            # Track successful operation
            self._successful_operations += 1
            
            yield page
            
        finally:
            # Cleanup
            try:
                if page:
                    if hasattr(page, "close"):
                        await page.close()
                    elif hasattr(page, "quit"):
                        page.quit()
                
                if context_id and context_id in self.contexts:
                    context_data = self.contexts.pop(context_id)
                    if "context" in context_data:
                        await context_data["context"].close()
                
                if browser_id and browser_id in self.browsers:
                    browser_data = self.browsers.pop(browser_id)
                    if "browser" in browser_data:
                        await browser_data["browser"].close()
                    elif "driver" in browser_data:
                        browser_data["driver"].quit()
                        
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def test_stealth(self, page: Any) -> Dict[str, Any]:
        """
        Test stealth capabilities of a page
        
        Args:
            page: Page to test
            
        Returns:
            Test results dictionary
        """
        results = {}
        
        try:
            # Navigate to test page
            test_url = "https://bot.sannysoft.com/"
            
            if hasattr(page, "goto"):
                # Playwright
                await page.goto(test_url, wait_until="domcontentloaded")
                
                # Run tests
                results["webdriver"] = await page.evaluate("navigator.webdriver")
                results["chrome"] = await page.evaluate("!!window.chrome")
                results["chrome.runtime"] = await page.evaluate("!!window.chrome?.runtime")
                results["permissions"] = await page.evaluate("""
                    navigator.permissions.query({name: 'notifications'})
                        .then(p => p.state)
                        .catch(e => 'error')
                """)
                results["plugins.length"] = await page.evaluate("navigator.plugins.length")
                results["languages"] = await page.evaluate("navigator.languages")
                
            else:
                # Selenium
                page.get(test_url)
                time.sleep(2)  # Wait for page load
                
                results["webdriver"] = page.execute_script("return navigator.webdriver")
                results["chrome"] = page.execute_script("return !!window.chrome")
                results["chrome.runtime"] = page.execute_script("return !!window.chrome?.runtime")
                results["plugins.length"] = page.execute_script("return navigator.plugins.length")
                results["languages"] = page.execute_script("return navigator.languages")
            
            # Check detection
            detection_score = 0
            if results.get("webdriver") is True:
                detection_score += 50
            if results.get("chrome.runtime") is False and results.get("chrome"):
                detection_score += 25
            if results.get("plugins.length", 0) == 0:
                detection_score += 25
            
            results["detection_score"] = detection_score
            results["is_detected"] = detection_score > 25
            
            # Track detection attempts
            self._detection_attempts += 1
            if not results["is_detected"]:
                logger.info("✅ Stealth test passed!")
            else:
                logger.warning(f"⚠️ Stealth test failed with score: {detection_score}")
            
            return results
            
        except Exception as e:
            logger.error(f"Stealth test failed: {e}")
            return {"error": str(e), "is_detected": True}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get launcher statistics"""
        avg_launch_time = sum(self._launch_times) / len(self._launch_times) if self._launch_times else 0
        
        return {
            "browsers_launched": len(self._launch_times),
            "avg_launch_time_ms": avg_launch_time,
            "successful_operations": self._successful_operations,
            "detection_attempts": self._detection_attempts,
            "active_browsers": len(self.browsers),
            "active_contexts": len(self.contexts),
            "nodriver_stats": nodriver_core.get_stats()
        }
    
    async def close_all(self):
        """Close all browsers and contexts"""
        logger.info("Closing all browsers...")
        
        # Close contexts
        for context_id, context_data in list(self.contexts.items()):
            try:
                if "context" in context_data:
                    await context_data["context"].close()
            except Exception as e:
                logger.error(f"Error closing context {context_id}: {e}")
        
        # Close browsers
        for browser_id, browser_data in list(self.browsers.items()):
            try:
                if "browser" in browser_data:
                    await browser_data["browser"].close()
                elif "driver" in browser_data:
                    browser_data["driver"].quit()
            except Exception as e:
                logger.error(f"Error closing browser {browser_id}: {e}")
        
        self.browsers.clear()
        self.contexts.clear()
        
        logger.info("All browsers closed")


# Global instance
launcher = NodriverBrowserLauncher()