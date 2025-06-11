"""
Updated StealthCore to use new architecture.
"""

import logging
from typing import Dict, Any, Optional
from playwright.async_api import Browser, BrowserContext, Page

try:
    from .injection_engine import InjectionEngine
    from .fingerprint import FingerprintGenerator
    from .behaviors import HumanBehavior
    from ..network.tls_fingerprint import TLSFingerprintRotator
except ImportError:
    from injection_engine import InjectionEngine
    from fingerprint import FingerprintGenerator
    from behaviors import HumanBehavior
    import sys
    sys.path.append('..')
    from network.tls_fingerprint import TLSFingerprintRotator

logger = logging.getLogger(__name__)


class StealthCoreV3:
    """
    Enhanced StealthCore using modern anti-detection architecture.
    """
    
    def __init__(self):
        """Initialize enhanced stealth core"""
        self.injection_engine = InjectionEngine()
        self.fingerprint_generator = FingerprintGenerator()
        self.behavior_engine = HumanBehavior()
        self.tls_rotator = TLSFingerprintRotator()
        
        logger.info("StealthCore V3 initialized with CDP bypass architecture")
    
    async def create_stealth_browser(
        self,
        browser: Browser,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> Browser:
        """
        Apply browser-level stealth configurations
        
        Args:
            browser: Browser instance
            fingerprint: Optional fingerprint to use
            
        Returns:
            Configured browser instance
        """
        if not fingerprint:
            fingerprint = self.fingerprint_generator.generate()
        
        # Browser should already have injection engine from launcher
        if hasattr(browser, '_stealth_injection_engine'):
            logger.info("Browser already has stealth capabilities")
        else:
            logger.warning("Browser launched without StealthBrowserLauncher")
        
        # Store fingerprint
        browser._stealth_fingerprint = fingerprint
        
        # Apply TLS fingerprint
        tls_profile = self.tls_rotator.get_profile(fingerprint["user_agent"])
        browser._tls_profile = tls_profile
        
        return browser
    
    async def create_stealth_context(
        self,
        browser: Browser,
        fingerprint: Optional[Dict[str, Any]] = None,
        proxy: Optional[Dict[str, Any]] = None
    ) -> BrowserContext:
        """
        Create a fully protected browser context
        
        Args:
            browser: Browser instance
            fingerprint: Fingerprint configuration
            proxy: Optional proxy settings
            
        Returns:
            Stealth browser context
        """
        if not fingerprint:
            fingerprint = getattr(browser, "_stealth_fingerprint", self.fingerprint_generator.generate())
        
        # Build context options
        context_options = self._build_context_options(fingerprint, proxy)
        
        # Create context (will be automatically injected by launcher)
        context = await browser.new_context(**context_options)
        
        # Store fingerprint
        context._stealth_fingerprint = fingerprint
        
        logger.info(f"Created stealth context with fingerprint {fingerprint['id']}")
        return context
    
    def _build_context_options(
        self,
        fingerprint: Dict[str, Any],
        proxy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context options from fingerprint"""
        options = {
            "viewport": {
                "width": fingerprint["viewport"]["width"],
                "height": fingerprint["viewport"]["height"],
            },
            "user_agent": fingerprint["user_agent"],
            "locale": fingerprint["navigator"]["language"][:2],
            "timezone_id": fingerprint["timezone"]["id"],
            "geolocation": fingerprint.get("geo"),
            "permissions": ["geolocation"],
            "color_scheme": "light",
            "device_scale_factor": fingerprint.get("device_scale_factor", 1),
            "is_mobile": False,
            "has_touch": False,
            "bypass_csp": True,
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "proxy": proxy
        }
        
        return options
    
    async def protect_page(
        self,
        page: Page,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Apply protection to a page
        
        Args:
            page: Page to protect
            fingerprint: Optional fingerprint override
        """
        # Page should already be injected by launcher
        logger.debug(f"Page {id(page)} already protected by injection engine")
        
        # Initialize human behavior
        await self.behavior_engine.initialize(page)
        
        # Store fingerprint
        if fingerprint:
            page._stealth_fingerprint = fingerprint
        elif hasattr(page.context, '_stealth_fingerprint'):
            page._stealth_fingerprint = page.context._stealth_fingerprint
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stealth system statistics"""
        return {
            "architecture": "CDP Bypass V3",
            "injection_method": "Early-stage CDP",
            "fingerprints_generated": len(self.fingerprint_generator._fingerprint_cache),
            "cdp_bypass_active": True
        }