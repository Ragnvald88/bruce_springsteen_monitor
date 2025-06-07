# src/utils/stealth_tester.py
"""
Comprehensive Stealth Testing Utility
Tests anti-detection measures and logs results
"""

import asyncio
import time
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from playwright.async_api import Browser, BrowserContext, Page, Response
from ..core.detection_monitor import (
    get_detection_monitor, 
    DetectionEventType
)

logger = logging.getLogger(__name__)


class StealthTester:
    """Comprehensive stealth testing suite"""
    
    def __init__(self):
        self.monitor = get_detection_monitor()
        self.test_urls = {
            "bot_detection": [
                "https://bot.sannysoft.com/",
                "https://arh.antoinevastel.com/bots/areyouheadless",
                "https://fingerprintjs.github.io/fingerprintjs/",
                "https://pixelscan.net/",
                "https://browserleaks.com/automation"
            ],
            "fingerprint": [
                "https://amiunique.org/",
                "https://browserleaks.com/canvas",
                "https://browserleaks.com/webrtc",
                "https://browserleaks.com/javascript"
            ],
            "platforms": {
                "fansale": "https://www.fansale.de/fansale/",
                "ticketmaster": "https://www.ticketmaster.com/",
                "vivaticket": "https://www.vivaticket.com/"
            }
        }
    
    async def run_comprehensive_test(
        self,
        context: BrowserContext,
        profile_id: str,
        platform: str = "test"
    ) -> Dict[str, Any]:
        """Run comprehensive stealth tests"""
        results = {
            "profile_id": profile_id,
            "platform": platform,
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Test 1: Basic bot detection
        logger.info(f"🔍 Running bot detection tests for {profile_id}")
        bot_results = await self._test_bot_detection(context, profile_id, platform)
        results["tests"]["bot_detection"] = bot_results
        
        # Test 2: Fingerprint consistency
        logger.info(f"🔍 Running fingerprint tests for {profile_id}")
        fingerprint_results = await self._test_fingerprint(context, profile_id, platform)
        results["tests"]["fingerprint"] = fingerprint_results
        
        # Test 3: Platform-specific tests
        if platform in self.test_urls["platforms"]:
            logger.info(f"🔍 Running platform-specific tests for {platform}")
            platform_results = await self._test_platform_access(
                context, profile_id, platform
            )
            results["tests"]["platform_access"] = platform_results
        
        # Test 4: JavaScript execution context
        logger.info(f"🔍 Testing JavaScript execution context")
        js_results = await self._test_javascript_context(context, profile_id, platform)
        results["tests"]["javascript"] = js_results
        
        # Test 5: Network behavior
        logger.info(f"🔍 Testing network behavior")
        network_results = await self._test_network_behavior(context, profile_id, platform)
        results["tests"]["network"] = network_results
        
        # Calculate overall score
        results["overall_score"] = self._calculate_overall_score(results)
        
        # Log summary
        self._log_test_summary(results)
        
        return results
    
    async def _test_bot_detection(
        self,
        context: BrowserContext,
        profile_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """Test against common bot detection services"""
        results = {
            "services_tested": [],
            "detections": 0,
            "passes": 0,
            "details": {}
        }
        
        for url in self.test_urls["bot_detection"]:
            service_name = url.split("//")[1].split("/")[0]
            try:
                page = await context.new_page()
                start_time = time.time()
                
                # Navigate and wait for load
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                load_time = (time.time() - start_time) * 1000
                
                # Check for bot detection indicators
                detected = await self._check_bot_indicators(page)
                
                results["services_tested"].append(service_name)
                results["details"][service_name] = {
                    "detected": detected,
                    "load_time_ms": load_time,
                    "status_code": response.status if response else None
                }
                
                if detected:
                    results["detections"] += 1
                    event_type = DetectionEventType.BOT_DETECTED
                else:
                    results["passes"] += 1
                    event_type = DetectionEventType.STEALTH_CHECK_PASSED
                
                # Log event
                self.monitor.log_event(
                    event_type=event_type,
                    platform=platform,
                    profile_id=profile_id,
                    success=not detected,
                    details={
                        "service": service_name,
                        "url": url,
                        "load_time_ms": load_time
                    }
                )
                
                await page.close()
                
                # Random delay between tests
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error testing {service_name}: {e}")
                results["details"][service_name] = {"error": str(e)}
        
        return results
    
    async def _check_bot_indicators(self, page: Page) -> bool:
        """Check for common bot detection indicators"""
        indicators = []
        
        # Check for headless indicators
        headless_check = await page.evaluate("""
            () => {
                const indicators = [];
                
                // Chrome headless detection
                if (navigator.webdriver) indicators.push('webdriver');
                if (window.chrome && !window.chrome.runtime) indicators.push('chrome_runtime');
                if (navigator.plugins.length === 0) indicators.push('no_plugins');
                
                // Check for automation properties
                if (window.document.documentElement.getAttribute('webdriver')) {
                    indicators.push('webdriver_attribute');
                }
                
                // Check for CDP
                if (window.__nightmare || window._phantom || window.callPhantom) {
                    indicators.push('automation_globals');
                }
                
                return indicators;
            }
        """)
        
        # Check page content for detection messages
        content = await page.content()
        detection_keywords = [
            "bot detected",
            "automated",
            "not human",
            "headless",
            "please verify",
            "access denied",
            "suspicious activity"
        ]
        
        for keyword in detection_keywords:
            if keyword.lower() in content.lower():
                indicators.append(f"keyword:{keyword}")
        
        # Check for Cloudflare challenge
        if "cf-browser-verification" in content or "cf-challenge" in content:
            indicators.append("cloudflare_challenge")
        
        detected = len(headless_check) > 0 or len(indicators) > 0
        
        if detected:
            logger.warning(f"Bot indicators found: {headless_check + indicators}")
        
        return detected
    
    async def _test_fingerprint(
        self,
        context: BrowserContext,
        profile_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """Test fingerprint consistency and uniqueness"""
        results = {
            "fingerprints": [],
            "consistency": True,
            "uniqueness_score": 0
        }
        
        # Collect fingerprints from multiple sources
        for url in self.test_urls["fingerprint"][:2]:  # Test first 2 for speed
            try:
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Collect fingerprint data
                fingerprint_data = await page.evaluate("""
                    () => {
                        return {
                            userAgent: navigator.userAgent,
                            language: navigator.language,
                            platform: navigator.platform,
                            screenResolution: `${screen.width}x${screen.height}`,
                            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                            canvas: document.createElement('canvas').toDataURL().slice(-50),
                            webgl: (() => {
                                const canvas = document.createElement('canvas');
                                const gl = canvas.getContext('webgl');
                                return gl ? gl.getParameter(gl.RENDERER) : null;
                            })()
                        };
                    }
                """)
                
                results["fingerprints"].append({
                    "source": url.split("//")[1].split("/")[0],
                    "data": fingerprint_data
                })
                
                await page.close()
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Fingerprint test error: {e}")
        
        # Check consistency
        if len(results["fingerprints"]) > 1:
            first_fp = results["fingerprints"][0]["data"]
            for fp in results["fingerprints"][1:]:
                if fp["data"] != first_fp:
                    results["consistency"] = False
                    break
        
        # Log fingerprint event
        self.monitor.log_event(
            event_type=DetectionEventType.FINGERPRINT_CHALLENGED,
            platform=platform,
            profile_id=profile_id,
            success=results["consistency"],
            details={
                "fingerprint_sources": len(results["fingerprints"]),
                "consistent": results["consistency"]
            }
        )
        
        return results
    
    async def _test_platform_access(
        self,
        context: BrowserContext,
        profile_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """Test actual platform access"""
        url = self.test_urls["platforms"][platform]
        results = {
            "url": url,
            "accessible": False,
            "load_time_ms": 0,
            "requires_captcha": False,
            "requires_queue": False,
            "error": None
        }
        
        try:
            page = await context.new_page()
            
            # Set up response monitoring
            responses = []
            page.on("response", lambda r: responses.append(r))
            
            start_time = time.time()
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            load_time = (time.time() - start_time) * 1000
            
            results["load_time_ms"] = load_time
            results["status_code"] = response.status if response else None
            
            # Check for access
            if response and response.status == 200:
                results["accessible"] = True
                
                # Check for captcha
                captcha_selectors = [
                    'iframe[src*="recaptcha"]',
                    'div[class*="captcha"]',
                    'div[id*="captcha"]',
                    '.g-recaptcha',
                    '#px-captcha'
                ]
                
                for selector in captcha_selectors:
                    if await page.query_selector(selector):
                        results["requires_captcha"] = True
                        break
                
                # Check for queue
                content = await page.content()
                queue_indicators = ["queue", "waiting room", "please wait"]
                for indicator in queue_indicators:
                    if indicator.lower() in content.lower():
                        results["requires_queue"] = True
                        break
            
            # Log access attempt
            if results["accessible"] and not results["requires_captcha"]:
                event_type = DetectionEventType.ACCESS_GRANTED
            elif results["requires_captcha"]:
                event_type = DetectionEventType.CAPTCHA_TRIGGERED
            elif results["requires_queue"]:
                event_type = DetectionEventType.QUEUE_ENTERED
            else:
                event_type = DetectionEventType.ACCESS_DENIED
            
            self.monitor.log_event(
                event_type=event_type,
                platform=platform,
                profile_id=profile_id,
                success=results["accessible"],
                details={
                    "url": url,
                    "load_time_ms": load_time,
                    "requires_captcha": results["requires_captcha"],
                    "requires_queue": results["requires_queue"]
                }
            )
            
            await page.close()
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Platform access test error: {e}")
            
            self.monitor.log_event(
                event_type=DetectionEventType.ACCESS_DENIED,
                platform=platform,
                profile_id=profile_id,
                success=False,
                details={"error": str(e)}
            )
        
        return results
    
    async def _test_javascript_context(
        self,
        context: BrowserContext,
        profile_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """Test JavaScript execution context for automation leaks"""
        results = {
            "automation_detected": False,
            "leaked_properties": []
        }
        
        try:
            page = await context.new_page()
            
            # Check for automation properties
            leaks = await page.evaluate("""
                () => {
                    const leaks = [];
                    
                    // Check navigator properties
                    if (navigator.webdriver === true) leaks.push('navigator.webdriver');
                    if (navigator.automation) leaks.push('navigator.automation');
                    
                    // Check window properties
                    const suspiciousProps = [
                        '__webdriver_evaluate',
                        '__selenium_evaluate',
                        '__webdriver_script_function',
                        '__webdriver_script_func',
                        '__webdriver_script_fn',
                        '__fxdriver_evaluate',
                        '__driver_unwrapped',
                        '__webdriver_unwrapped',
                        '__driver_evaluate',
                        '__selenium_unwrapped',
                        '__fxdriver_unwrapped',
                        '_phantom',
                        '__nightmare',
                        '_selenium',
                        'callPhantom',
                        'callSelenium',
                        '_Selenium_IDE_Recorder',
                        '__stopAllTimers'
                    ];
                    
                    for (const prop of suspiciousProps) {
                        if (window[prop]) leaks.push(`window.${prop}`);
                    }
                    
                    // Check document properties
                    if (document.__selenium_injected) leaks.push('document.__selenium_injected');
                    if (document.$cdc_asdjflasutopfhvcZLmcfl_) leaks.push('document.$cdc');
                    if (document.$wdc_) leaks.push('document.$wdc');
                    
                    // Check for modified functions
                    const nativeCode = '[native code]';
                    if (!Function.prototype.toString.toString().includes(nativeCode)) {
                        leaks.push('Function.prototype.toString modified');
                    }
                    
                    return leaks;
                }
            """)
            
            results["leaked_properties"] = leaks
            results["automation_detected"] = len(leaks) > 0
            
            await page.close()
            
        except Exception as e:
            logger.error(f"JavaScript context test error: {e}")
            results["error"] = str(e)
        
        return results
    
    async def _test_network_behavior(
        self,
        context: BrowserContext,
        profile_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """Test network behavior patterns"""
        results = {
            "headers_normal": True,
            "timing_normal": True,
            "issues": []
        }
        
        try:
            page = await context.new_page()
            
            # Capture network data
            requests = []
            
            def on_request(request):
                requests.append({
                    "url": request.url,
                    "headers": request.headers,
                    "method": request.method
                })
            
            page.on("request", on_request)
            
            # Navigate to test page
            await page.goto("https://httpbin.org/headers", wait_until="networkidle")
            
            # Check headers
            response_data = await page.evaluate("() => document.body.innerText")
            
            # Analyze request headers
            if requests:
                headers = requests[0]["headers"]
                
                # Check for suspicious header patterns
                if "headless" in str(headers).lower():
                    results["headers_normal"] = False
                    results["issues"].append("Headless indicator in headers")
                
                # Check for missing headers
                expected_headers = ["accept-language", "accept-encoding"]
                for header in expected_headers:
                    if header not in headers:
                        results["issues"].append(f"Missing header: {header}")
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Network behavior test error: {e}")
            results["error"] = str(e)
        
        return results
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall stealth score (0-100)"""
        score = 100.0
        
        # Bot detection (40% weight)
        if "bot_detection" in results["tests"]:
            bot_test = results["tests"]["bot_detection"]
            if bot_test.get("detections", 0) > 0:
                detection_rate = bot_test["detections"] / len(bot_test["services_tested"])
                score -= detection_rate * 40
        
        # Fingerprint consistency (20% weight)
        if "fingerprint" in results["tests"]:
            fp_test = results["tests"]["fingerprint"]
            if not fp_test.get("consistency", True):
                score -= 20
        
        # Platform access (20% weight)
        if "platform_access" in results["tests"]:
            platform_test = results["tests"]["platform_access"]
            if not platform_test.get("accessible", False):
                score -= 20
            elif platform_test.get("requires_captcha", False):
                score -= 10
        
        # JavaScript leaks (10% weight)
        if "javascript" in results["tests"]:
            js_test = results["tests"]["javascript"]
            if js_test.get("automation_detected", False):
                score -= 10
        
        # Network behavior (10% weight)
        if "network" in results["tests"]:
            network_test = results["tests"]["network"]
            if not network_test.get("headers_normal", True):
                score -= 10
        
        return max(0, score)
    
    def _log_test_summary(self, results: Dict[str, Any]):
        """Log test results summary"""
        score = results["overall_score"]
        profile_id = results["profile_id"]
        
        if score >= 90:
            logger.info(f"✅ Profile {profile_id}: EXCELLENT stealth (Score: {score:.1f})")
        elif score >= 70:
            logger.info(f"⚠️ Profile {profile_id}: GOOD stealth (Score: {score:.1f})")
        elif score >= 50:
            logger.warning(f"⚠️ Profile {profile_id}: MODERATE stealth (Score: {score:.1f})")
        else:
            logger.error(f"❌ Profile {profile_id}: POOR stealth (Score: {score:.1f})")
        
        # Log specific issues
        for test_name, test_results in results["tests"].items():
            if isinstance(test_results, dict):
                if test_results.get("automation_detected"):
                    logger.warning(f"  - {test_name}: Automation detected!")
                if test_results.get("detections", 0) > 0:
                    logger.warning(
                        f"  - {test_name}: {test_results['detections']} detections"
                    )


async def test_profile_stealth(
    context: BrowserContext,
    profile_id: str,
    platform: str = "test"
) -> float:
    """Quick function to test a profile's stealth and return score"""
    tester = StealthTester()
    results = await tester.run_comprehensive_test(context, profile_id, platform)
    return results["overall_score"]