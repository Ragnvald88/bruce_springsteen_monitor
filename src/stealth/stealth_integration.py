# src/stealth/stealth_integration.py
"""
StealthMaster AI v3.0 - Stealth Integration Module
Consolidates all stealth measures for easy application
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any, List
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from .advanced_fingerprint import AdvancedFingerprint
from .cdp_bypass_engine import CDPStealthEngine
from .ultra_stealth import UltraStealthEngine

logger = logging.getLogger(__name__)


class StealthIntegration:
    """
    Master integration class for all stealth measures
    Provides simple interface to apply comprehensive anti-detection
    """
    
    @staticmethod
    async def create_stealth_browser(
        playwright: Playwright,
        headless: bool = False,
        proxy: Optional[Dict[str, str]] = None
    ) -> Browser:
        """
        Create a browser with maximum stealth capabilities
        
        Args:
            playwright: Playwright instance
            headless: Whether to run headless (NOT recommended for stealth)
            proxy: Optional proxy configuration
            
        Returns:
            Configured browser instance
        """
        
        if headless:
            logger.warning("⚠️ Headless mode reduces stealth effectiveness!")
        
        # Use CDP stealth engine for browser creation
        browser = await CDPStealthEngine.create_stealth_browser(playwright, proxy)
        
        logger.info("✅ Stealth browser created with all protections")
        
        return browser
    
    @staticmethod
    async def create_stealth_context(
        browser: Browser,
        proxy_config: Optional[Dict[str, str]] = None,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> BrowserContext:
        """
        Create a browser context with stealth settings
        
        Args:
            browser: Browser instance
            proxy_config: Optional proxy configuration
            fingerprint: Optional fingerprint (generates if not provided)
            
        Returns:
            Configured browser context
        """
        
        # Generate fingerprint if not provided
        if not fingerprint:
            fingerprint = AdvancedFingerprint.generate_fingerprint()
        
        # Create context with CDP stealth
        context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
        
        # Store fingerprint for reference
        context._fingerprint = fingerprint
        
        # Apply context-level stealth
        await StealthIntegration._apply_context_stealth(context, fingerprint)
        
        logger.debug("✅ Stealth context created with fingerprint")
        
        return context
    
    @staticmethod
    async def apply_page_stealth(page: Page) -> None:
        """
        Apply all stealth measures to a page
        
        Args:
            page: Page instance to protect
        """
        
        logger.debug("Applying comprehensive stealth measures to page...")
        
        # Apply CDP stealth
        await CDPStealthEngine.apply_page_stealth(page)
        
        # Apply ultra stealth
        await UltraStealthEngine.apply_ultra_stealth(page)
        
        # Apply additional protections
        await StealthIntegration._apply_advanced_protections(page)
        
        # Add human behavior patterns
        await StealthIntegration._add_human_behavior(page)
        
        logger.debug("✅ All stealth measures applied to page")
    
    @staticmethod
    async def _apply_context_stealth(context: BrowserContext, fingerprint: Dict[str, Any]) -> None:
        """Apply context-level stealth settings"""
        
        # Set extra HTTP headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': f"{fingerprint['language']},en;q=0.9",
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1' if random.random() > 0.7 else '0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        await context.set_extra_http_headers(headers)
        
        # Set geolocation
        await context.set_geolocation({
            'latitude': fingerprint['geo']['latitude'],
            'longitude': fingerprint['geo']['longitude']
        })
        
        # Grant permissions
        await context.grant_permissions(['geolocation', 'notifications'])
    
    @staticmethod
    async def _apply_advanced_protections(page: Page) -> None:
        """Apply additional advanced protections"""
        
        await page.add_init_script("""
        // Advanced protections
        (() => {
            'use strict';
            
            // 1. Protect against toString detection
            const nativeToString = Function.prototype.toString;
            Function.prototype.toString = new Proxy(nativeToString, {
                apply(target, thisArg, args) {
                    if (thisArg === Function.prototype.toString) {
                        return 'function toString() { [native code] }';
                    }
                    return target.apply(thisArg, args);
                }
            });
            
            // 2. Protect against permission detection
            if (navigator.permissions && navigator.permissions.query) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = async function(descriptor) {
                    // Always return granted for common permissions
                    if (['geolocation', 'notifications', 'camera', 'microphone'].includes(descriptor.name)) {
                        return {
                            state: 'granted',
                            onchange: null,
                            addEventListener: () => {},
                            removeEventListener: () => {},
                            dispatchEvent: () => true
                        };
                    }
                    return originalQuery.call(this, descriptor);
                };
            }
            
            // 3. Protect against iframe detection
            if (window.top === window) {
                // We're not in an iframe, but protect against detection
                Object.defineProperty(window, 'frameElement', {
                    get: () => null,
                    enumerable: true
                });
            }
            
            // 4. Protect against screen size detection inconsistencies
            const screenProps = ['availWidth', 'availHeight', 'width', 'height'];
            screenProps.forEach(prop => {
                const originalDescriptor = Object.getOwnPropertyDescriptor(screen, prop);
                if (originalDescriptor) {
                    Object.defineProperty(screen, prop, {
                        ...originalDescriptor,
                        get: function() {
                            const value = originalDescriptor.get.call(this);
                            // Ensure consistency
                            if (prop === 'availWidth') return Math.min(value, window.outerWidth);
                            if (prop === 'availHeight') return Math.min(value, window.outerHeight);
                            return value;
                        }
                    });
                }
            });
            
            // 5. Protect against Web Worker detection
            if (typeof Worker !== 'undefined') {
                const OriginalWorker = Worker;
                window.Worker = new Proxy(OriginalWorker, {
                    construct(target, args) {
                        // Add slight delay to mimic human behavior
                        return new Promise(resolve => {
                            setTimeout(() => {
                                resolve(new target(...args));
                            }, Math.random() * 100);
                        });
                    }
                });
            }
            
            // 6. Protect against AudioContext fingerprinting
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const OriginalAudioContext = AudioContext;
                const audioContextNoise = () => (Math.random() - 0.5) * 0.0001;
                
                window.AudioContext = window.webkitAudioContext = new Proxy(OriginalAudioContext, {
                    construct(target, args) {
                        const context = new target(...args);
                        
                        // Add noise to audio processing
                        const originalCreateOscillator = context.createOscillator;
                        context.createOscillator = function() {
                            const oscillator = originalCreateOscillator.call(this);
                            const originalFrequency = oscillator.frequency;
                            
                            Object.defineProperty(oscillator.frequency, 'value', {
                                get() {
                                    return originalFrequency.value;
                                },
                                set(val) {
                                    originalFrequency.value = val + audioContextNoise();
                                }
                            });
                            
                            return oscillator;
                        };
                        
                        return context;
                    }
                });
            }
            
            // 7. Protect against GPU detection
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                    return 'Intel Inc.';
                }
                if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.call(this, parameter);
            };
            
            // 8. Protect against touch event detection
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 0,
                enumerable: true
            });
            
            // 9. Protect against automation tool detection
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        })();
        """)
    
    @staticmethod
    async def _add_human_behavior(page: Page) -> None:
        """Add human-like behavior patterns to page"""
        
        await page.add_init_script("""
        // Human behavior simulation
        (() => {
            'use strict';
            
            // Random mouse movements
            let mouseX = window.innerWidth / 2;
            let mouseY = window.innerHeight / 2;
            let lastMovement = Date.now();
            
            const simulateMouseMovement = () => {
                const now = Date.now();
                if (now - lastMovement > 1000 + Math.random() * 2000) {
                    // Move mouse randomly
                    mouseX += (Math.random() - 0.5) * 100;
                    mouseY += (Math.random() - 0.5) * 100;
                    
                    // Keep within bounds
                    mouseX = Math.max(0, Math.min(window.innerWidth, mouseX));
                    mouseY = Math.max(0, Math.min(window.innerHeight, mouseY));
                    
                    // Dispatch event
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX,
                        clientY: mouseY,
                        bubbles: true,
                        cancelable: true
                    });
                    
                    document.dispatchEvent(event);
                    lastMovement = now;
                }
            };
            
            // Random scrolling
            let lastScroll = Date.now();
            
            const simulateScroll = () => {
                const now = Date.now();
                if (now - lastScroll > 5000 + Math.random() * 5000) {
                    if (document.body.scrollHeight > window.innerHeight) {
                        // Smooth scroll
                        const scrollAmount = (Math.random() - 0.5) * 200;
                        window.scrollBy({
                            top: scrollAmount,
                            behavior: 'smooth'
                        });
                        lastScroll = now;
                    }
                }
            };
            
            // Random focus changes
            let lastFocus = Date.now();
            
            const simulateFocus = () => {
                const now = Date.now();
                if (now - lastFocus > 10000 + Math.random() * 10000) {
                    const focusableElements = document.querySelectorAll(
                        'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
                    );
                    
                    if (focusableElements.length > 0) {
                        const randomElement = focusableElements[
                            Math.floor(Math.random() * focusableElements.length)
                        ];
                        
                        // Simulate hover before focus
                        const hoverEvent = new MouseEvent('mouseenter', {
                            bubbles: true,
                            cancelable: true
                        });
                        randomElement.dispatchEvent(hoverEvent);
                        
                        setTimeout(() => {
                            randomElement.focus();
                        }, Math.random() * 500);
                        
                        lastFocus = now;
                    }
                }
            };
            
            // Idle detection
            let lastActivity = Date.now();
            let isIdle = false;
            
            ['mousemove', 'keydown', 'scroll', 'click'].forEach(eventType => {
                document.addEventListener(eventType, () => {
                    lastActivity = Date.now();
                    isIdle = false;
                });
            });
            
            // Main behavior loop
            setInterval(() => {
                const now = Date.now();
                
                // Check if idle
                if (now - lastActivity > 30000) {
                    isIdle = true;
                }
                
                // Only simulate if not idle
                if (!isIdle) {
                    simulateMouseMovement();
                    simulateScroll();
                    simulateFocus();
                }
            }, 1000);
            
            // Visibility change handling
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    isIdle = true;
                } else {
                    lastActivity = Date.now();
                    isIdle = false;
                }
            });
        })();
        """)
    
    @staticmethod
    async def handle_detection(page: Page, platform: str) -> bool:
        """
        Handle detection and attempt recovery
        
        Args:
            page: Page that may be detected
            platform: Platform name for specific handling
            
        Returns:
            True if recovery successful, False otherwise
        """
        
        logger.warning(f"🚨 Potential detection on {platform}, attempting recovery...")
        
        # Check page content for detection indicators
        content = await page.content()
        detection_indicators = [
            'captcha',
            'challenge',
            'verify',
            'robot',
            'automated',
            'suspicious activity',
            'access denied'
        ]
        
        detected = any(indicator in content.lower() for indicator in detection_indicators)
        
        if detected:
            logger.error(f"❌ Confirmed detection on {platform}")
            
            # Platform-specific recovery
            if platform.lower() == 'cloudflare':
                # Wait for challenge to potentially resolve
                await asyncio.sleep(5)
                
                # Check if resolved
                new_content = await page.content()
                if not any(indicator in new_content.lower() for indicator in detection_indicators):
                    logger.info("✅ Detection resolved")
                    return True
            
            return False
        
        logger.info("✅ No detection confirmed")
        return True
    
    @staticmethod
    async def simulate_human_interaction(
        page: Page,
        element_selector: str,
        action_type: str = 'click'
    ) -> None:
        """
        Simulate human-like interaction with an element
        
        Args:
            page: Page instance
            element_selector: CSS selector for element
            action_type: Type of action ('click', 'type', 'hover')
        """
        
        try:
            # Wait for element with human-like delay
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            element = await page.wait_for_selector(element_selector, timeout=10000)
            
            if not element:
                logger.warning(f"Element not found: {element_selector}")
                return
            
            # Get element position
            box = await element.bounding_box()
            if not box:
                logger.warning("Could not get element bounding box")
                return
            
            # Calculate click position with slight randomness
            x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
            y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
            
            # Move mouse to element with human-like path
            await CDPStealthEngine.simulate_human_mouse(page)
            
            # Hover first
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Perform action
            if action_type == 'click':
                await page.mouse.click(x, y)
            elif action_type == 'hover':
                # Just hover, already done
                pass
            elif action_type == 'type' and element:
                await element.click()
                # Type will be handled separately
                
        except Exception as e:
            logger.error(f"Error in human interaction: {e}")
    
    @staticmethod
    def get_stealth_status(page: Page) -> Dict[str, Any]:
        """
        Get current stealth status of a page
        
        Args:
            page: Page to check
            
        Returns:
            Dictionary with stealth status information
        """
        
        # This would check various indicators
        return {
            'cdp_protected': hasattr(page, '_cdp_protected'),
            'fingerprint_applied': hasattr(page.context, '_fingerprint'),
            'ultra_stealth_applied': hasattr(page, '_ultra_stealth'),
            'human_behavior_active': True  # Always active with our injection
        }


class StealthHelper:
    """Helper functions for common stealth operations"""
    
    @staticmethod
    async def create_stealth_page(
        browser: Browser,
        url: Optional[str] = None,
        proxy: Optional[Dict[str, str]] = None
    ) -> Page:
        """
        Create a fully protected page with one function call
        
        Args:
            browser: Browser instance
            url: Optional URL to navigate to
            proxy: Optional proxy configuration
            
        Returns:
            Protected page instance
        """
        
        # Create context
        context = await StealthIntegration.create_stealth_context(browser, proxy)
        
        # Create page
        page = await context.new_page()
        
        # Apply page stealth
        await StealthIntegration.apply_page_stealth(page)
        
        # Navigate if URL provided
        if url:
            await page.goto(url, wait_until='domcontentloaded')
        
        return page
    
    @staticmethod
    async def type_like_human(
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True
    ) -> None:
        """
        Type text with human-like timing and occasional typos
        
        Args:
            page: Page instance
            selector: Element selector
            text: Text to type
            clear_first: Whether to clear existing text
        """
        
        # Click element first
        await StealthIntegration.simulate_human_interaction(page, selector, 'click')
        
        element = await page.query_selector(selector)
        if not element:
            return
        
        # Clear if needed
        if clear_first:
            await element.click({'clickCount': 3})  # Triple click to select all
            await page.keyboard.press('Delete')
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Type with human-like delays
        for i, char in enumerate(text):
            # Occasional typo
            if random.random() < 0.02 and i < len(text) - 1:
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
                
                # Delete it
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Type correct character
            await page.keyboard.type(char)
            
            # Variable delay
            if char == ' ':
                delay = random.uniform(0.05, 0.15)
            elif char in '.,!?':
                delay = random.uniform(0.15, 0.3)
            else:
                delay = random.uniform(0.03, 0.12)
            
            await asyncio.sleep(delay)
    
    @staticmethod
    async def scroll_naturally(
        page: Page,
        direction: str = 'down',
        distance: Optional[int] = None
    ) -> None:
        """
        Scroll page naturally like a human
        
        Args:
            page: Page instance
            direction: 'up' or 'down'
            distance: Optional specific distance
        """
        
        if not distance:
            distance = random.randint(100, 500)
        
        if direction == 'down':
            scroll_y = distance
        else:
            scroll_y = -distance
        
        # Smooth scroll with easing
        await page.evaluate(f"""
            (() => {{
                const startY = window.scrollY;
                const targetY = startY + {scroll_y};
                const duration = {random.uniform(500, 1500)};
                const startTime = Date.now();
                
                const easeInOutQuad = (t) => {{
                    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
                }};
                
                const scroll = () => {{
                    const elapsed = Date.now() - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const easeProgress = easeInOutQuad(progress);
                    
                    window.scrollTo(0, startY + (targetY - startY) * easeProgress);
                    
                    if (progress < 1) {{
                        requestAnimationFrame(scroll);
                    }}
                }};
                
                requestAnimationFrame(scroll);
            }})();
        """)
        
        # Wait for scroll to complete
        await asyncio.sleep(random.uniform(0.5, 1.5))