# stealthmaster/browser/launcher.py
"""Stealth browser launcher with advanced anti-detection."""

import logging
from typing import Dict, Optional, List

from playwright.async_api import Browser, Playwright, BrowserContext

try:
    from ..config import BrowserOptions, ProxyConfig
    from ..stealth.core import StealthCore
except ImportError:
    from config import BrowserOptions, ProxyConfig
    from stealth.core import StealthCore

logger = logging.getLogger(__name__)


class BrowserLauncher:
    """Launches browsers with maximum stealth configuration."""
    
    def __init__(self, config: BrowserOptions):
        """Initialize the launcher with configuration."""
        self.config = config
        self.stealth_core = StealthCore()
    
    async def launch(
        self,
        playwright: Playwright,
        proxy: Optional[ProxyConfig] = None,
        headless: bool = False,
    ) -> Browser:
        """
        Launch a browser with stealth configuration.
        
        Args:
            playwright: Playwright instance
            proxy: Optional proxy configuration
            headless: Whether to run headless (not recommended)
            
        Returns:
            Configured browser instance
        """
        # Build launch arguments
        args = self._build_launch_args()
        
        # Proxy configuration
        proxy_config = None
        if proxy and proxy.host and proxy.port:
            # Format proxy properly
            proxy_type = getattr(proxy, 'type', 'http').lower()
            if proxy_type not in ['http', 'https', 'socks5']:
                proxy_type = 'http'
            
            proxy_config = {
                "server": f"{proxy_type}://{proxy.host}:{proxy.port}",
            }
            
            # Only add credentials if both exist
            if proxy.username and proxy.password:
                proxy_config["username"] = proxy.username
                proxy_config["password"] = proxy.password
            
            logger.info(f"Using proxy: {proxy_type}://{proxy.host}:{proxy.port}")
        
        # Launch browser with proper configuration
        launch_options = {
            "headless": headless,
            "args": args,
            "proxy": proxy_config,
            "chromium_sandbox": False,
            "handle_sigint": False,
            "handle_sigterm": False,
            "handle_sighup": False,
        }
        
        # Force non-headless user agent even in headless mode
        if headless:
            # Remove any existing user agent args
            args = [arg for arg in args if not arg.startswith("--user-agent=")]
            # Add proper user agent
            args.append("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
            launch_options["args"] = args
        
        browser = await playwright.chromium.launch(**launch_options)
        
        # Apply browser-level stealth immediately after launch
        await self.stealth_core.create_stealth_browser(browser)
        
        logger.info(
            f"Launched {'headless' if headless else 'headed'} browser "
            f"{'with proxy' if proxy else 'without proxy'} with stealth"
        )
        
        return browser
    
    def _build_launch_args(self) -> List[str]:
        """Build optimized launch arguments for stealth."""
        args = [
            # Disable automation indicators
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            
            # Performance optimizations
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-accelerated-2d-canvas",
            
            # Stealth enhancements
            "--disable-infobars",
            "--disable-extensions",
            "--disable-default-apps",
            "--disable-component-extensions-with-background-pages",
            
            # Window settings
            "--window-size=1920,1080",
            "--start-maximized",
            
            # Additional stealth flags
            "--disable-plugins-discovery",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-hang-monitor",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--safebrowsing-disable-auto-update",
            "--password-store=basic",
            "--use-mock-keychain",
            
            # Remove automation extension
            "--disable-component-update",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            
            # User agent override (if specified)
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        return args
    
    async def create_context(
        self,
        browser: Browser,
        fingerprint: Optional[Dict] = None,
    ) -> BrowserContext:
        """
        Create a browser context with stealth settings.
        
        Args:
            browser: Browser instance
            fingerprint: Optional fingerprint configuration
            
        Returns:
            Configured browser context
        """
        # Generate fingerprint if not provided
        if not fingerprint:
            fingerprint = self.stealth_core.generate_fingerprint()
        
        # Context options
        context_options = {
            "viewport": {
                "width": fingerprint["viewport"]["width"],
                "height": fingerprint["viewport"]["height"],
            },
            "user_agent": fingerprint["user_agent"],
            "locale": fingerprint["language"][:2],
            "timezone_id": "Europe/Rome",
            "geolocation": fingerprint.get("geo"),
            "permissions": ["geolocation", "notifications"],
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
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        }
        
        # Create context
        context = await browser.new_context(**context_options)
        
        # Store fingerprint for reference
        context._stealth_fingerprint = fingerprint
        
        # Apply context-level stealth BEFORE creating pages
        await self.stealth_core.apply_context_stealth(context)
        
        logger.debug(f"Created stealth context with fingerprint ID: {fingerprint.get('id', 'default')}")
        
        return context