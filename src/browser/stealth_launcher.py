"""
Modified browser launcher that integrates all stealth components.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import Browser, Playwright, BrowserContext

try:
    from ..stealth.cdp_bypass_v3 import CDPInterceptor
    from ..stealth.browser_patcher import BrowserPatcher
    from ..stealth.injection_engine import InjectionEngine
    from .launcher import BrowserLauncher
except ImportError:
    import sys
    sys.path.append('..')
    from stealth.cdp_bypass_v3 import CDPInterceptor
    from stealth.browser_patcher import BrowserPatcher
    from stealth.injection_engine import InjectionEngine
    from browser.launcher import BrowserLauncher

logger = logging.getLogger(__name__)


class StealthBrowserLauncher(BrowserLauncher):
    """
    Enhanced browser launcher with integrated stealth capabilities.
    """
    
    def __init__(self, options: Any):
        """Initialize stealth browser launcher"""
        super().__init__(options)
        self.cdp_interceptor = CDPInterceptor()
        self.browser_patcher = BrowserPatcher()
        self.injection_engine = InjectionEngine()
        self._proxy_servers: Dict[str, Any] = {}
        
    async def launch(
        self,
        playwright: Playwright,
        proxy: Optional[Any] = None,
        headless: bool = False,
        **kwargs
    ) -> Browser:
        """
        Launch browser with full stealth capabilities
        
        Args:
            playwright: Playwright instance
            proxy: Optional proxy configuration
            headless: Whether to run headless
            **kwargs: Additional browser options
            
        Returns:
            Stealth browser instance
        """
        # Get browser path
        browser_type = getattr(playwright, self.options.browser_type)
        original_path = browser_type.executable_path
        
        # Patch browser binary
        patched_path = self.browser_patcher.patch_browser(original_path)
        
        # Prepare launch options
        launch_options = self._prepare_launch_options(proxy, headless)
        launch_options['executable_path'] = patched_path
        
        # Add stealth arguments
        launch_options['args'].extend([
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            '--disable-features=OutOfBlinkCors',
            '--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure',
            '--flag-switches-begin',
            '--disable-features=AutomationControlled',
            '--flag-switches-end',
        ])
        
        # Remove automation indicators
        if '--enable-automation' in launch_options['args']:
            launch_options['args'].remove('--enable-automation')
        if '--enable-blink-features=AutomationControlled' in launch_options['args']:
            launch_options['args'].remove('--enable-blink-features=AutomationControlled')
        
        # Launch browser
        browser = await browser_type.launch(**launch_options)
        
        # Get WebSocket endpoint
        ws_endpoint = browser._impl_obj._browser._transport._ws_endpoint
        
        # Start CDP proxy
        proxy_url, proxy_server = await self.cdp_interceptor.start_proxy(ws_endpoint)
        self._proxy_servers[id(browser)] = proxy_server
        
        # Apply injection engine to browser
        browser._stealth_injection_engine = self.injection_engine
        
        # Override context creation
        original_new_context = browser.new_context
        
        async def stealth_new_context(**kwargs) -> BrowserContext:
            context = await original_new_context(**kwargs)
            
            # Apply injections
            await self.injection_engine.inject_context(context)
            
            # Override page creation
            original_new_page = context.new_page
            
            async def stealth_new_page() -> Any:
                page = await original_new_page()
                await self.injection_engine.inject_page(page)
                return page
            
            context.new_page = stealth_new_page
            
            return context
        
        browser.new_context = stealth_new_context
        
        logger.info("Stealth browser launched successfully")
        return browser
    
    def _prepare_launch_options(
        self,
        proxy: Optional[Any],
        headless: bool
    ) -> Dict[str, Any]:
        """Prepare browser launch options"""
        options = super()._prepare_launch_options(proxy, headless)
        
        # Force non-headless for better stealth
        if headless:
            logger.warning("Headless mode detected - forcing headful for better stealth")
            options['headless'] = False
            
        return options
    
    async def close_browser(self, browser: Browser):
        """Close browser and cleanup"""
        browser_id = id(browser)
        
        # Cleanup proxy server
        if browser_id in self._proxy_servers:
            server = self._proxy_servers[browser_id]
            server.close()
            await server.wait_closed()
            del self._proxy_servers[browser_id]
        
        # Cleanup patcher
        self.browser_patcher.cleanup()
        
        # Close browser
        await browser.close()