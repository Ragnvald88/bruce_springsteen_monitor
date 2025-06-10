# stealthmaster/stealth/core.py
"""
Enhanced Stealth Core - Multi-layered bot detection evasion system.
Implements advanced techniques to bypass modern AI-driven detection.
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Page, Route, Request

from .fingerprint import FingerprintGenerator
from .injections import StealthInjections
from .cdp_bypass_engine import CDPStealth
from .behaviors import HumanBehavior
from network.tls_fingerprint import TLSFingerprintRotator

logger = logging.getLogger(__name__)


class StealthCore:
    """
    Advanced stealth orchestration with multi-layered evasion.
    Coordinates all anti-detection measures for maximum effectiveness.
    """
    
    def __init__(self):
        """Initialize stealth core components."""
        self.fingerprint_generator = FingerprintGenerator()
        self.injections = StealthInjections()
        self.cdp_stealth = CDPStealth()
        self.behavior_engine = HumanBehavior()
        self.tls_rotator = TLSFingerprintRotator()
        
        # Detection tracking
        self._detection_scores: Dict[str, float] = {}
        self._protected_contexts: Set[str] = set()
        self._protected_pages: Set[str] = set()
        
        # Evasion strategies
        self._evasion_level = "maximum"  # minimal, balanced, maximum
        self._active_countermeasures: Set[str] = set()
        
        logger.info("StealthCore initialized with maximum evasion capabilities")
    
    async def create_stealth_browser(
        self,
        browser: Browser,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> Browser:
        """
        Apply browser-level stealth configurations.
        
        Args:
            browser: Browser instance
            fingerprint: Optional fingerprint to use
            
        Returns:
            Configured browser instance
        """
        if not fingerprint:
            fingerprint = self.fingerprint_generator.generate()
        
        # Apply TLS fingerprint rotation
        tls_profile = self.tls_rotator.get_profile(fingerprint["user_agent"])
        await self._apply_tls_fingerprint(browser, tls_profile)
        
        # Store fingerprint for this browser
        browser._stealth_fingerprint = fingerprint
        browser._tls_profile = tls_profile
        
        logger.info(f"Applied stealth to browser with fingerprint {fingerprint['id']}")
        return browser
    
    async def create_stealth_context(
        self,
        browser: Browser,
        fingerprint: Optional[Dict[str, Any]] = None,
        proxy: Optional[Dict[str, Any]] = None
    ) -> BrowserContext:
        """
        Create a fully protected browser context.
        
        Args:
            browser: Browser instance
            fingerprint: Fingerprint configuration
            proxy: Optional proxy settings
            
        Returns:
            Stealth browser context
        """
        if not fingerprint:
            fingerprint = getattr(browser, "_stealth_fingerprint", self.fingerprint_generator.generate())
        
        # Build context options with fingerprint
        context_options = self._build_context_options(fingerprint, proxy)
        
        # Create context
        context = await browser.new_context(**context_options)
        
        # Apply stealth before any page creation
        await self._apply_context_stealth(context, fingerprint)
        
        # Mark as protected
        context_id = str(id(context))
        self._protected_contexts.add(context_id)
        context._stealth_fingerprint = fingerprint
        
        logger.info(f"Created stealth context with fingerprint {fingerprint['id']}")
        return context
    
    def _build_context_options(
        self,
        fingerprint: Dict[str, Any],
        proxy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build context options from fingerprint."""
        options = {
            "viewport": {
                "width": fingerprint["viewport"]["width"],
                "height": fingerprint["viewport"]["height"],
            },
            "user_agent": fingerprint["user_agent"],
            "locale": fingerprint["navigator"]["language"][:2],
            "timezone_id": fingerprint["timezone"]["id"],
            "geolocation": fingerprint.get("geo"),
            "permissions": ["geolocation", "notifications"],
            "color_scheme": "light",
            "device_scale_factor": fingerprint.get("device_scale_factor", 1),
            "is_mobile": False,
            "has_touch": False,
            "bypass_csp": True,
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "offline": False,
            "http_credentials": None,
            "storage_state": None,
            "record_har": None,
            "record_video": None,
            "proxy": proxy,
            "extra_http_headers": {
                "Accept-Language": fingerprint["navigator"]["language"] + ",en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": self._generate_client_hints(fingerprint["user_agent"]),
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }
        }
        
        return options
    
    async def _apply_context_stealth(
        self,
        context: BrowserContext,
        fingerprint: Dict[str, Any]
    ) -> None:
        """Apply all stealth measures to context."""
        # Add initialization script with all evasions
        init_script = self._build_init_script(fingerprint)
        await context.add_init_script(init_script)
        
        # Apply route interception for additional protection
        await context.route("**/*", self._handle_route)
        
        # Set up CDP stealth
        await self.cdp_stealth.apply_context_stealth(context)
        
        # Configure page creation handler
        context.on("page", lambda page: asyncio.create_task(
            self._on_page_created(page, fingerprint)
        ))
        
        logger.debug("Applied comprehensive stealth to context")
    
    def _build_init_script(self, fingerprint: Dict[str, Any]) -> str:
        """Build complete initialization script."""
        scripts = [
            self.injections.get_base_evasion(),
            self.injections.get_webdriver_evasion(),
            self.injections.get_chrome_runtime_evasion(),
            self.injections.get_plugin_evasion(fingerprint),
            self.injections.get_webgl_evasion(fingerprint),
            self.injections.get_canvas_evasion(fingerprint),
            self.injections.get_audio_evasion(fingerprint),
            self.injections.get_navigator_evasion(fingerprint),
            self.injections.get_screen_evasion(fingerprint),
            self.injections.get_timezone_evasion(fingerprint),
            self.injections.get_permission_evasion(),
            self.injections.get_console_evasion(),
            self.injections.get_error_evasion(),
            self.injections.get_advanced_evasion(),
        ]
        
        return "\n\n".join(scripts)
    
    async def _on_page_created(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Handle new page creation."""
        try:
            page_id = str(id(page))
            
            # Skip if already protected
            if page_id in self._protected_pages:
                return
            
            # Apply page-level stealth
            await self.protect_page(page, fingerprint)
            
        except Exception as e:
            logger.error(f"Error protecting new page: {e}")
    
    async def protect_page(
        self,
        page: Page,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Apply comprehensive protection to a page.
        
        Args:
            page: Page to protect
            fingerprint: Optional fingerprint override
        """
        page_id = str(id(page))
        
        # Get fingerprint from context or generate new
        if not fingerprint:
            context = page.context
            fingerprint = getattr(context, "_stealth_fingerprint", None)
            if not fingerprint:
                fingerprint = self.fingerprint_generator.generate()
        
        # Apply CDP-level stealth
        await self.cdp_stealth.apply_page_stealth(page)
        
        # Initialize human behavior simulation
        await self.behavior_engine.initialize(page)
        
        # Additional page-specific evasions
        await self._apply_page_evasions(page, fingerprint)
        
        # Mark as protected
        self._protected_pages.add(page_id)
        page._stealth_fingerprint = fingerprint
        
        logger.debug(f"Protected page {page_id} with comprehensive stealth")
    
    async def _apply_page_evasions(self, page: Page, fingerprint: Dict[str, Any]) -> None:
        """Apply page-specific evasion techniques."""
        # Override navigator.webdriver before any script execution
        await page.evaluate_on_new_document("""
            // Ensure webdriver is never exposed
            delete Object.getPrototypeOf(navigator).webdriver;
            
            // Monitor for detection attempts
            const detectAttempts = [];
            const originalGetter = Object.getOwnPropertyDescriptor;
            Object.getOwnPropertyDescriptor = function(obj, prop) {
                if (obj === navigator && prop === 'webdriver') {
                    detectAttempts.push(new Date().toISOString());
                    return undefined;
                }
                return originalGetter.apply(this, arguments);
            };
            
            window.__detectAttempts = detectAttempts;
        """)
        
        # Set up detection monitoring
        page.on("console", lambda msg: self._check_console_detection(msg))
        
        # Monitor for suspicious redirects
        page.on("framenavigated", lambda frame: self._check_detection_redirect(frame))
    
    async def _handle_route(self, route: Route) -> None:
        """Handle route interception for stealth."""
        request = route.request
        
        # Modify headers for stealth
        headers = dict(request.headers)
        
        # Remove suspicious headers
        suspicious = ["sec-ch-ua-full-version", "sec-ch-ua-arch", "sec-ch-ua-bitness"]
        for header in suspicious:
            headers.pop(header.lower(), None)
        
        # Ensure proper header order (Chrome-like)
        ordered_headers = self._order_headers(headers)
        
        await route.continue_(headers=ordered_headers)
    
    def _order_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Order headers to match Chrome behavior."""
        # Chrome header order
        order = [
            "host", "connection", "cache-control", "sec-ch-ua",
            "sec-ch-ua-mobile", "sec-ch-ua-platform", "upgrade-insecure-requests",
            "user-agent", "accept", "sec-fetch-site", "sec-fetch-mode",
            "sec-fetch-user", "sec-fetch-dest", "referer",
            "accept-encoding", "accept-language", "cookie"
        ]
        
        ordered = {}
        
        # Add headers in Chrome order
        for key in order:
            if key in headers:
                ordered[key] = headers[key]
        
        # Add remaining headers
        for key, value in headers.items():
            if key.lower() not in ordered:
                ordered[key] = value
        
        return ordered
    
    def _generate_client_hints(self, user_agent: str) -> str:
        """Generate Sec-CH-UA client hints."""
        # Extract Chrome version
        import re
        match = re.search(r'Chrome/(\d+)', user_agent)
        if match:
            version = match.group(1)
            return f'"Not/A)Brand";v="99", "Google Chrome";v="{version}", "Chromium";v="{version}"'
        
        return '"Chromium";v="121", "Not(A:Brand";v="24", "Google Chrome";v="121"'
    
    async def _apply_tls_fingerprint(self, browser: Browser, tls_profile: Dict[str, Any]) -> None:
        """Apply TLS fingerprint to browser."""
        # This would integrate with the browser's network layer
        # For now, we store it for later use
        browser._tls_profile = tls_profile
        logger.debug(f"Applied TLS profile: {tls_profile.get('name', 'default')}")
    
    def _check_console_detection(self, msg: Any) -> None:
        """Monitor console for detection attempts."""
        text = str(msg.text).lower()
        
        detection_keywords = [
            "bot detected", "automation detected", "webdriver detected",
            "suspicious activity", "security check", "verification required"
        ]
        
        for keyword in detection_keywords:
            if keyword in text:
                logger.warning(f"Possible detection: {msg.text}")
                self._active_countermeasures.add("console_detection")
                break
    
    def _check_detection_redirect(self, frame: Any) -> None:
        """Check for detection-related redirects."""
        url = frame.url.lower()
        
        detection_urls = [
            "challenge", "captcha", "verify", "security",
            "blocked", "denied", "forbidden"
        ]
        
        for pattern in detection_urls:
            if pattern in url:
                logger.warning(f"Detection redirect detected: {frame.url}")
                self._active_countermeasures.add("redirect_detection")
                break
    
    def get_detection_score(self, page: Page) -> float:
        """
        Calculate detection risk score for a page.
        
        Returns:
            Score from 0.0 (undetected) to 1.0 (detected)
        """
        page_id = str(id(page))
        
        # Calculate based on various factors
        score = 0.0
        
        # Check if page is protected
        if page_id not in self._protected_pages:
            score += 0.3
        
        # Check active countermeasures
        score += len(self._active_countermeasures) * 0.1
        
        # Cap at 1.0
        return min(score, 1.0)
    
    async def enhance_evasion(self, page: Page) -> None:
        """
        Enhance evasion for a page showing detection signs.
        
        Args:
            page: Page to enhance
        """
        logger.info("Enhancing evasion measures due to detection risk")
        
        # Add additional noise
        await page.evaluate("""
            // Add more realistic behavior
            (() => {
                // Simulate random mouse movements
                let mouseX = Math.random() * window.innerWidth;
                let mouseY = Math.random() * window.innerHeight;
                
                setInterval(() => {
                    mouseX += (Math.random() - 0.5) * 10;
                    mouseY += (Math.random() - 0.5) * 10;
                    
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX,
                        clientY: mouseY,
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                }, 100 + Math.random() * 200);
                
                // Simulate random scrolling
                setInterval(() => {
                    if (Math.random() < 0.1) {
                        window.scrollBy({
                            top: (Math.random() - 0.5) * 100,
                            behavior: 'smooth'
                        });
                    }
                }, 5000 + Math.random() * 5000);
            })();
        """)
        
        # Rotate TLS fingerprint
        if hasattr(page.context.browser, "_tls_profile"):
            new_profile = self.tls_rotator.rotate()
            page.context.browser._tls_profile = new_profile
        
        # Clear countermeasures
        self._active_countermeasures.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stealth system statistics."""
        return {
            "protected_contexts": len(self._protected_contexts),
            "protected_pages": len(self._protected_pages),
            "active_countermeasures": list(self._active_countermeasures),
            "evasion_level": self._evasion_level,
            "fingerprints_generated": len(self.fingerprint_generator._fingerprint_cache),
        }