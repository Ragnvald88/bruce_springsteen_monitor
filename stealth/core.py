# stealthmaster/stealth/core.py
"""Core stealth orchestration module."""

import logging
from typing import Dict, Any, Optional

from playwright.async_api import Page, BrowserContext

from stealth.cdp import CDPStealth
from stealth.fingerprint import FingerprintGenerator
from stealth.injections import StealthInjections
from stealth.behaviors import HumanBehavior

logger = logging.getLogger(__name__)


class StealthCore:
    """
    Central orchestrator for all stealth operations.
    Ensures consistent application of anti-detection measures.
    """
    
    def __init__(self):
        """Initialize stealth components."""
        self.fingerprint_gen = FingerprintGenerator()
        self.cdp_stealth = CDPStealth()
        self.injections = StealthInjections()
        self.human_behavior = HumanBehavior()
    
    def generate_fingerprint(self) -> Dict[str, Any]:
        """
        Generate a complete browser fingerprint.
        
        Returns:
            Fingerprint configuration dictionary
        """
        return self.fingerprint_gen.generate()
    
    async def apply_context_stealth(self, context: BrowserContext) -> None:
        """
        Apply context-level stealth measures.
        
        Args:
            context: Browser context to protect
        """
        logger.debug("Applying context-level stealth measures")
        
        # Apply CDP stealth at context level
        await self.cdp_stealth.apply_context_stealth(context)
        
        # Set stealth-enhanced permissions
        await context.grant_permissions(["geolocation", "notifications"])
        
        # Add context initialization script
        await context.add_init_script(self.injections.get_context_init_script())
        
        logger.debug("Context stealth measures applied")
    
    async def apply_page_stealth(
        self,
        page: Page,
        fingerprint: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Apply comprehensive stealth measures to a page.
        
        Args:
            page: Page to protect
            fingerprint: Optional fingerprint (generates if not provided)
        """
        logger.debug("Applying page-level stealth measures")
        
        # Generate fingerprint if not provided
        if not fingerprint:
            fingerprint = self.generate_fingerprint()
        
        # Apply CDP-level stealth
        await self.cdp_stealth.apply_page_stealth(page)
        
        # Inject stealth scripts
        await self._inject_stealth_scripts(page, fingerprint)
        
        # Initialize human behavior simulation
        await self.human_behavior.initialize(page)
        
        # Mark page as stealth-protected
        page._stealth_applied = True
        page._stealth_fingerprint = fingerprint
        
        logger.debug("Page stealth measures applied successfully")
    
    async def _inject_stealth_scripts(
        self,
        page: Page,
        fingerprint: Dict[str, Any],
    ) -> None:
        """Inject all stealth scripts into the page."""
        # Get all injection scripts
        scripts = [
            self.injections.get_webdriver_evasion(),
            self.injections.get_chrome_runtime_evasion(),
            self.injections.get_permission_evasion(),
            self.injections.get_plugin_evasion(fingerprint),
            self.injections.get_webgl_evasion(fingerprint),
            self.injections.get_canvas_evasion(fingerprint),
            self.injections.get_audio_evasion(fingerprint),
            self.injections.get_navigator_evasion(fingerprint),
            self.injections.get_screen_evasion(fingerprint),
            self.injections.get_timezone_evasion(fingerprint),
            self.injections.get_console_evasion(),
            self.injections.get_error_evasion(),
        ]
        
        # Combine and inject
        combined_script = "\n".join(scripts)
        await page.add_init_script(combined_script)
    
    async def check_detection(self, page: Page) -> Dict[str, Any]:
        """
        Check if the page shows signs of bot detection.
        
        Args:
            page: Page to check
            
        Returns:
            Detection status and details
        """
        detection_result = {
            "detected": False,
            "type": None,
            "confidence": 0.0,
            "indicators": [],
        }
        
        try:
            # Check page content
            content = await page.content()
            content_lower = content.lower()
            
            # Detection patterns with confidence scores
            patterns = {
                "captcha": 0.9,
                "recaptcha": 0.9,
                "hcaptcha": 0.9,
                "challenge-form": 0.8,
                "cf-challenge": 0.9,  # Cloudflare
                "verify you are human": 0.9,
                "suspicious activity": 0.8,
                "access denied": 0.7,
                "rate limit": 0.8,
                "too many requests": 0.8,
                "automated": 0.6,
                "bot protection": 0.9,
            }
            
            # Check for patterns
            for pattern, confidence in patterns.items():
                if pattern in content_lower:
                    detection_result["indicators"].append(pattern)
                    detection_result["confidence"] = max(
                        detection_result["confidence"],
                        confidence,
                    )
            
            # Check JavaScript detection
            js_detected = await page.evaluate("""
                () => {
                    // Check for common bot detection libraries
                    const detectionSignals = [];
                    
                    if (window.datadome) detectionSignals.push('datadome');
                    if (window._cf_chl_opt) detectionSignals.push('cloudflare');
                    if (window.recaptcha) detectionSignals.push('recaptcha');
                    if (window.hcaptcha) detectionSignals.push('hcaptcha');
                    if (window.Impermia) detectionSignals.push('imperva');
                    
                    return detectionSignals;
                }
            """)
            
            if js_detected:
                detection_result["indicators"].extend(js_detected)
                detection_result["confidence"] = max(
                    detection_result["confidence"],
                    0.9,
                )
            
            # Determine detection status
            if detection_result["confidence"] >= 0.7:
                detection_result["detected"] = True
                
                # Determine type
                if any("captcha" in ind for ind in detection_result["indicators"]):
                    detection_result["type"] = "captcha"
                elif "cloudflare" in detection_result["indicators"]:
                    detection_result["type"] = "cloudflare"
                elif "rate limit" in detection_result["indicators"]:
                    detection_result["type"] = "rate_limit"
                else:
                    detection_result["type"] = "generic"
            
        except Exception as e:
            logger.error(f"Error checking detection: {e}")
        
        return detection_result
    
    async def handle_detection_recovery(
        self,
        page: Page,
        detection_type: str,
    ) -> bool:
        """
        Attempt to recover from detection.
        
        Args:
            page: Page with detection
            detection_type: Type of detection encountered
            
        Returns:
            Success status
        """
        logger.warning(f"Attempting recovery from {detection_type} detection")
        
        try:
            if detection_type == "cloudflare":
                # Wait for potential challenge resolution
                await page.wait_for_timeout(5000)
                
                # Check if resolved
                detection = await self.check_detection(page)
                if not detection["detected"]:
                    logger.info("Cloudflare challenge resolved")
                    return True
            
            elif detection_type == "rate_limit":
                # Wait longer for rate limit
                logger.info("Waiting for rate limit to clear...")
                await page.wait_for_timeout(30000)
                
                # Refresh page
                await page.reload()
                
                # Check again
                detection = await self.check_detection(page)
                return not detection["detected"]
            
            elif detection_type == "captcha":
                # Can't auto-solve, return false
                logger.error("CAPTCHA detected - manual intervention required")
                return False
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
        
        return False
    
    def get_stealth_status(self, page: Page) -> Dict[str, Any]:
        """
        Get comprehensive stealth status of a page.
        
        Args:
            page: Page to check
            
        Returns:
            Stealth status information
        """
        return {
            "stealth_applied": getattr(page, "_stealth_applied", False),
            "has_fingerprint": hasattr(page, "_stealth_fingerprint"),
            "cdp_protected": self.cdp_stealth.is_protected(page),
            "human_behavior_active": self.human_behavior.is_active(page),
            "fingerprint_id": getattr(page, "_stealth_fingerprint", {}).get("id"),
        }
    
    async def apply_context_stealth(self, context: BrowserContext) -> None:
        """
        Apply stealth measures at the context level.
        
        Args:
            context: BrowserContext to protect
        """
        # Add comprehensive pre-page script
        await context.add_init_script("""
            // Context-level stealth initialization
            (() => {
                'use strict';
                
                // Remove webdriver before anything else loads
                delete Object.getPrototypeOf(navigator).webdriver;
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: false
                });
                
                // Remove automation indicators
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Fix chrome object
                if (!window.chrome) {
                    window.chrome = {};
                }
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {
                        connect: () => {},
                        sendMessage: () => {},
                        onMessage: { addListener: () => {} }
                    };
                }
                
                // Mock plugins early
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const arr = [
                            {
                                name: 'Chrome PDF Plugin',
                                description: 'Portable Document Format',
                                filename: 'internal-pdf-viewer',
                                length: 1
                            },
                            {
                                name: 'Chrome PDF Viewer', 
                                description: 'Portable Document Format',
                                filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                                length: 1
                            },
                            {
                                name: 'Native Client',
                                description: 'Native Client Executable',
                                filename: 'internal-nacl-plugin',
                                length: 2
                            }
                        ];
                        arr.item = (i) => arr[i];
                        arr.namedItem = (name) => arr.find(p => p.name === name);
                        arr.refresh = () => {};
                        Object.defineProperty(arr, 'length', { value: 3 });
                        return arr;
                    },
                    configurable: false
                });
                
                // Fix permissions
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = async (parameters) => {
                    if (parameters.name === 'notifications') {
                        return { state: 'prompt', onchange: null };
                    }
                    return originalQuery(parameters);
                };
            })();
        """)