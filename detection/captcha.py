# stealthmaster/detection/captcha.py
"""CAPTCHA detection and handling system."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import base64
import json

from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class CaptchaType(Enum):
    """Types of CAPTCHAs."""
    
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    GEETEST = "geetest"
    CLOUDFLARE = "cloudflare"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class CaptchaStatus(Enum):
    """CAPTCHA solving status."""
    
    DETECTED = "detected"
    SOLVING = "solving"
    SOLVED = "solved"
    FAILED = "failed"
    BYPASSED = "bypassed"


class CaptchaDetector:
    """Detects various types of CAPTCHAs on web pages."""
    
    def __init__(self):
        """Initialize CAPTCHA detector."""
        self._detection_signatures = self._load_signatures()
    
    def _load_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Load CAPTCHA detection signatures."""
        return {
            CaptchaType.RECAPTCHA_V2: {
                "selectors": [
                    'iframe[src*="recaptcha"]',
                    'div.g-recaptcha',
                    '#g-recaptcha',
                    'iframe[title="reCAPTCHA"]'
                ],
                "scripts": [
                    "google.com/recaptcha",
                    "grecaptcha.render",
                    "grecaptcha.execute"
                ],
                "attributes": {
                    "data-sitekey": True,
                    "data-callback": False
                }
            },
            CaptchaType.RECAPTCHA_V3: {
                "selectors": [
                    'input[name="g-recaptcha-response"]'
                ],
                "scripts": [
                    "google.com/recaptcha/api.js?render=",
                    "grecaptcha.ready"
                ],
                "attributes": {}
            },
            CaptchaType.HCAPTCHA: {
                "selectors": [
                    'div.h-captcha',
                    'iframe[src*="hcaptcha.com"]',
                    '#hcaptcha'
                ],
                "scripts": [
                    "hcaptcha.com",
                    "hcaptcha.render"
                ],
                "attributes": {
                    "data-sitekey": True
                }
            },
            CaptchaType.FUNCAPTCHA: {
                "selectors": [
                    'div#funcaptcha',
                    'div[id*="arkose"]',
                    'iframe[src*="funcaptcha"]'
                ],
                "scripts": [
                    "funcaptcha.com",
                    "arkoselabs.com"
                ],
                "attributes": {
                    "data-public-key": True
                }
            },
            CaptchaType.CLOUDFLARE: {
                "selectors": [
                    'div.cf-challenge',
                    '#cf-challenge-running',
                    '.cf-turnstile'
                ],
                "scripts": [
                    "challenges.cloudflare.com",
                    "cf-challenge"
                ],
                "attributes": {}
            }
        }
    
    async def detect(self, page: Page) -> Optional[Dict[str, Any]]:
        """
        Detect CAPTCHA on the page.
        
        Args:
            page: Page to check
            
        Returns:
            CAPTCHA information if detected
        """
        for captcha_type, signature in self._detection_signatures.items():
            detection = await self._check_signature(page, captcha_type, signature)
            if detection:
                return detection
        
        # Check for generic CAPTCHA indicators
        generic = await self._check_generic_captcha(page)
        if generic:
            return generic
        
        return None
    
    async def _check_signature(
        self,
        page: Page,
        captcha_type: CaptchaType,
        signature: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for specific CAPTCHA signature."""
        # Check selectors
        for selector in signature.get("selectors", []):
            element = await page.query_selector(selector)
            if element:
                logger.info(f"Detected {captcha_type.value} via selector: {selector}")
                
                # Extract additional info
                info = await self._extract_captcha_info(page, element, captcha_type, signature)
                
                return {
                    "type": captcha_type,
                    "selector": selector,
                    "element": element,
                    **info
                }
        
        # Check scripts
        for script_pattern in signature.get("scripts", []):
            has_script = await page.evaluate(f"""
                () => {{
                    const scripts = Array.from(document.scripts);
                    return scripts.some(s => s.src.includes('{script_pattern}') || 
                                           s.textContent.includes('{script_pattern}'));
                }}
            """)
            
            if has_script:
                logger.info(f"Detected {captcha_type.value} via script: {script_pattern}")
                return {
                    "type": captcha_type,
                    "script_pattern": script_pattern
                }
        
        return None
    
    async def _check_generic_captcha(self, page: Page) -> Optional[Dict[str, Any]]:
        """Check for generic CAPTCHA indicators."""
        generic_keywords = [
            "captcha", "challenge", "verify", "human", "robot",
            "security check", "anti-bot"
        ]
        
        for keyword in generic_keywords:
            # Check page content
            found = await page.evaluate(f"""
                () => {{
                    const text = document.body.innerText.toLowerCase();
                    return text.includes('{keyword.lower()}');
                }}
            """)
            
            if found:
                # Try to find the element
                elements = await page.query_selector_all(f'*:has-text("{keyword}")')
                if elements:
                    return {
                        "type": CaptchaType.UNKNOWN,
                        "keyword": keyword,
                        "element": elements[0]
                    }
        
        return None
    
    async def _extract_captcha_info(
        self,
        page: Page,
        element: ElementHandle,
        captcha_type: CaptchaType,
        signature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract CAPTCHA-specific information."""
        info = {}
        
        # Extract attributes
        for attr, required in signature.get("attributes", {}).items():
            value = await element.get_attribute(attr)
            if value:
                info[attr.replace("-", "_")] = value
        
        # Type-specific extraction
        if captcha_type == CaptchaType.RECAPTCHA_V2:
            # Check if invisible
            is_visible = await element.is_visible()
            info["invisible"] = not is_visible
            
            # Get site key from page if not in element
            if "data_sitekey" not in info:
                sitekey = await page.evaluate("""
                    () => {
                        const scripts = Array.from(document.scripts);
                        for (const script of scripts) {
                            const match = script.textContent.match(/sitekey["']\s*:\s*["']([^"']+)/);
                            if (match) return match[1];
                        }
                        return null;
                    }
                """)
                if sitekey:
                    info["data_sitekey"] = sitekey
        
        elif captcha_type == CaptchaType.CLOUDFLARE:
            # Check challenge type
            challenge_type = await page.evaluate("""
                () => {
                    if (document.querySelector('.cf-turnstile')) return 'turnstile';
                    if (document.querySelector('#cf-challenge-running')) return 'challenge';
                    return 'unknown';
                }
            """)
            info["challenge_type"] = challenge_type
        
        return info


class CaptchaSolver:
    """Base CAPTCHA solver interface."""
    
    async def solve(
        self,
        captcha_type: CaptchaType,
        page: Page,
        captcha_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Solve CAPTCHA.
        
        Args:
            captcha_type: Type of CAPTCHA
            page: Page with CAPTCHA
            captcha_info: CAPTCHA information
            
        Returns:
            Solution token if successful
        """
        raise NotImplementedError


class ManualCaptchaSolver(CaptchaSolver):
    """Manual CAPTCHA solving with user interaction."""
    
    async def solve(
        self,
        captcha_type: CaptchaType,
        page: Page,
        captcha_info: Dict[str, Any]
    ) -> Optional[str]:
        """Wait for manual CAPTCHA solving."""
        logger.info(f"Waiting for manual {captcha_type.value} solving...")
        
        # Wait for CAPTCHA to disappear or be solved
        start_time = datetime.now()
        timeout = 300  # 5 minutes
        
        while (datetime.now() - start_time).seconds < timeout:
            # Check if CAPTCHA is still present
            detector = CaptchaDetector()
            current = await detector.detect(page)
            
            if not current or current["type"] != captcha_type:
                logger.info("CAPTCHA solved manually")
                return "manual_solve"
            
            await asyncio.sleep(2)
        
        logger.error("Manual CAPTCHA solving timeout")
        return None


class CloudflareSolver(CaptchaSolver):
    """Specialized Cloudflare challenge solver."""
    
    async def solve(
        self,
        captcha_type: CaptchaType,
        page: Page,
        captcha_info: Dict[str, Any]
    ) -> Optional[str]:
        """Handle Cloudflare challenges."""
        challenge_type = captcha_info.get("challenge_type", "unknown")
        
        if challenge_type == "turnstile":
            # Cloudflare Turnstile (managed challenge)
            logger.info("Waiting for Cloudflare Turnstile...")
            
            # These often auto-solve
            await page.wait_for_timeout(5000)
            
            # Check if still present
            detector = CaptchaDetector()
            current = await detector.detect(page)
            
            if not current or current["type"] != CaptchaType.CLOUDFLARE:
                return "auto_solved"
        
        elif challenge_type == "challenge":
            # Classic Cloudflare challenge
            logger.info("Waiting for Cloudflare challenge to complete...")
            
            # Wait for challenge to complete
            try:
                await page.wait_for_selector(
                    '.cf-challenge',
                    state='hidden',
                    timeout=30000
                )
                return "challenge_passed"
            except Exception:
                pass
        
        return None


class CaptchaHandler:
    """Main CAPTCHA handling system."""
    
    def __init__(self):
        """Initialize CAPTCHA handler."""
        self.detector = CaptchaDetector()
        self.solvers: Dict[CaptchaType, CaptchaSolver] = {
            CaptchaType.CLOUDFLARE: CloudflareSolver(),
            # Default to manual for others
            CaptchaType.RECAPTCHA_V2: ManualCaptchaSolver(),
            CaptchaType.RECAPTCHA_V3: ManualCaptchaSolver(),
            CaptchaType.HCAPTCHA: ManualCaptchaSolver(),
            CaptchaType.FUNCAPTCHA: ManualCaptchaSolver(),
        }
        
        self._solving_history: List[Dict[str, Any]] = []
    
    async def handle(self, page: Page) -> Dict[str, Any]:
        """
        Detect and handle CAPTCHA on page.
        
        Args:
            page: Page to check
            
        Returns:
            Handling result
        """
        # Detect CAPTCHA
        detection = await self.detector.detect(page)
        
        if not detection:
            return {
                "detected": False,
                "type": None,
                "status": CaptchaStatus.BYPASSED
            }
        
        captcha_type = detection["type"]
        logger.warning(f"CAPTCHA detected: {captcha_type.value}")
        
        # Record detection
        record = {
            "timestamp": datetime.now(),
            "type": captcha_type,
            "url": page.url,
            "status": CaptchaStatus.DETECTED
        }
        self._solving_history.append(record)
        
        # Get solver
        solver = self.solvers.get(captcha_type, ManualCaptchaSolver())
        
        # Attempt to solve
        record["status"] = CaptchaStatus.SOLVING
        solution = await solver.solve(captcha_type, page, detection)
        
        if solution:
            record["status"] = CaptchaStatus.SOLVED
            record["solution"] = solution
            
            return {
                "detected": True,
                "type": captcha_type,
                "status": CaptchaStatus.SOLVED,
                "solution": solution
            }
        else:
            record["status"] = CaptchaStatus.FAILED
            
            return {
                "detected": True,
                "type": captcha_type,
                "status": CaptchaStatus.FAILED,
                "error": "Could not solve CAPTCHA"
            }
    
    async def wait_for_captcha_completion(
        self,
        page: Page,
        timeout: int = 60000
    ) -> bool:
        """
        Wait for CAPTCHA to be completed.
        
        Args:
            page: Page with CAPTCHA
            timeout: Maximum wait time in milliseconds
            
        Returns:
            True if CAPTCHA was completed
        """
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds * 1000 < timeout:
            # Check if CAPTCHA is still present
            detection = await self.detector.detect(page)
            
            if not detection:
                logger.info("CAPTCHA completed")
                return True
            
            # Check for navigation (might indicate completion)
            current_url = page.url
            await page.wait_for_timeout(2000)
            
            if page.url != current_url:
                logger.info("Page navigated, assuming CAPTCHA completed")
                return True
        
        logger.error("CAPTCHA completion timeout")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CAPTCHA handling statistics."""
        total = len(self._solving_history)
        
        if total == 0:
            return {
                "total_captchas": 0,
                "success_rate": 0.0,
                "by_type": {},
                "avg_solving_time": 0
            }
        
        # Calculate stats
        solved = sum(1 for r in self._solving_history if r["status"] == CaptchaStatus.SOLVED)
        success_rate = solved / total
        
        # Group by type
        by_type = {}
        for record in self._solving_history:
            captcha_type = record["type"].value
            if captcha_type not in by_type:
                by_type[captcha_type] = {"total": 0, "solved": 0}
            
            by_type[captcha_type]["total"] += 1
            if record["status"] == CaptchaStatus.SOLVED:
                by_type[captcha_type]["solved"] += 1
        
        return {
            "total_captchas": total,
            "success_rate": success_rate,
            "by_type": by_type,
            "recent_captchas": self._solving_history[-10:]
        }
    
    def register_solver(self, captcha_type: CaptchaType, solver: CaptchaSolver) -> None:
        """
        Register a custom CAPTCHA solver.
        
        Args:
            captcha_type: Type of CAPTCHA
            solver: Solver instance
        """
        self.solvers[captcha_type] = solver
        logger.info(f"Registered solver for {captcha_type.value}")


class AntiCaptchaAPISOlver(CaptchaSolver):
    """Example external CAPTCHA solving service integration."""
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
    
    async def solve(
        self,
        captcha_type: CaptchaType,
        page: Page,
        captcha_info: Dict[str, Any]
    ) -> Optional[str]:
        """Solve using external service."""
        # This is a placeholder for external service integration
        # Real implementation would call the actual API
        logger.info(f"Would solve {captcha_type.value} using external service")
        return None