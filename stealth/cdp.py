# stealthmaster/stealth/cdp.py
"""CDP (Chrome DevTools Protocol) level stealth implementation."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set

from playwright.async_api import Page, BrowserContext, CDPSession

logger = logging.getLogger(__name__)


class CDPStealth:
    """Implements CDP-level anti-detection measures."""
    
    def __init__(self):
        """Initialize CDP stealth engine."""
        self._protected_pages: Set[str] = set()
        self._cdp_sessions: Dict[str, CDPSession] = {}
    
    async def apply_context_stealth(self, context: BrowserContext) -> None:
        """
        Apply CDP stealth at context level.
        
        Args:
            context: Browser context to protect
        """
        # Add script to be evaluated on every new document
        await context.add_init_script(self._get_runtime_enable_bypass())
        
        logger.debug("Applied CDP stealth to context")
    
    async def apply_page_stealth(self, page: Page) -> None:
        """
        Apply comprehensive CDP stealth to a page.
        
        Args:
            page: Page to protect
        """
        page_id = str(id(page))
        
        if page_id in self._protected_pages:
            logger.debug(f"Page {page_id} already protected")
            return
        
        try:
            # Create CDP session
            client = await page.context.new_cdp_session(page)
            self._cdp_sessions[page_id] = client
            
            # Apply CDP-level protections
            await self._apply_cdp_overrides(client)
            await self._disable_webdriver_detection(client)
            await self._setup_console_api_bypass(client)
            await self._configure_page_domain(client)
            
            # Mark as protected
            self._protected_pages.add(page_id)
            
            logger.debug(f"Applied CDP stealth to page {page_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply CDP stealth: {e}")
    
    def _get_runtime_enable_bypass(self) -> str:
        """Get script to bypass Runtime.Enable detection."""
        return """
        // Runtime.Enable bypass
        (() => {
            'use strict';
            
            // Store original console methods before any modification
            const originalConsole = {
                log: console.log,
                debug: console.debug,
                info: console.info,
                warn: console.warn,
                error: console.error,
                dir: console.dir,
                dirxml: console.dirxml,
                table: console.table,
                trace: console.trace,
                group: console.group,
                groupCollapsed: console.groupCollapsed,
                groupEnd: console.groupEnd,
                clear: console.clear,
                count: console.count,
                countReset: console.countReset,
                assert: console.assert,
                profile: console.profile,
                profileEnd: console.profileEnd,
                time: console.time,
                timeLog: console.timeLog,
                timeEnd: console.timeEnd,
                timeStamp: console.timeStamp,
                context: console.context,
                memory: console.memory
            };
            
            // Detection prevention
            let rapidCallCount = 0;
            let lastCallTime = 0;
            
            // Create proxy for each console method
            Object.keys(originalConsole).forEach(method => {
                if (typeof originalConsole[method] === 'function') {
                    console[method] = new Proxy(originalConsole[method], {
                        apply(target, thisArg, args) {
                            const now = Date.now();
                            
                            // Detect rapid successive calls
                            if (now - lastCallTime < 10) {
                                rapidCallCount++;
                                if (rapidCallCount > 5) {
                                    // Likely automation detection, ignore
                                    return;
                                }
                            } else {
                                rapidCallCount = 0;
                            }
                            
                            lastCallTime = now;
                            
                            // Check call stack for CDP
                            const stack = new Error().stack || '';
                            if (stack.includes('Runtime.consoleAPICalled') || 
                                stack.includes('CDP') ||
                                stack.includes('DevTools')) {
                                return;
                            }
                            
                            // Normal console call
                            return target.apply(originalConsole, args);
                        },
                        get(target, prop) {
                            if (prop === 'toString') {
                                return () => `function ${method}() { [native code] }`;
                            }
                            return target[prop];
                        }
                    });
                }
            });
            
            // Prevent inspection of console object
            const consoleProxy = new Proxy(console, {
                get(target, prop) {
                    if (prop === Symbol.toStringTag) {
                        return 'Console';
                    }
                    return target[prop];
                },
                getOwnPropertyDescriptor(target, prop) {
                    const descriptor = Object.getOwnPropertyDescriptor(target, prop);
                    if (descriptor && typeof target[prop] === 'function') {
                        descriptor.value = target[prop];
                        descriptor.writable = false;
                        descriptor.configurable = false;
                    }
                    return descriptor;
                }
            });
            
            // Replace global console
            try {
                Object.defineProperty(window, 'console', {
                    get: () => consoleProxy,
                    set: () => true,
                    enumerable: true,
                    configurable: false
                });
            } catch (e) {
                // Fallback
                window.console = consoleProxy;
            }
        })();
        """
    
    async def _apply_cdp_overrides(self, client: CDPSession) -> None:
        """Apply CDP-level overrides to prevent detection."""
        # Override user agent at CDP level
        await client.send('Network.setUserAgentOverride', {
            'userAgent': await self._get_current_user_agent(client),
            'acceptLanguage': 'en-US,en;q=0.9',
            'platform': 'Win32'
        })
        
        # Emulate timezone
        await client.send('Emulation.setTimezoneOverride', {
            'timezoneId': 'Europe/Rome'
        })
        
        # Emulate locale
        await client.send('Emulation.setLocaleOverride', {
            'locale': 'en-US'
        })
        
        # Disable WebDriver flag at CDP level
        await client.send('Page.addScriptToEvaluateOnNewDocument', {
            'source': """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
    
    async def _disable_webdriver_detection(self, client: CDPSession) -> None:
        """Disable webdriver detection at CDP level."""
        # Remove automation indicators
        await client.send('Page.addScriptToEvaluateOnNewDocument', {
            'source': """
                // Remove Chrome automation extension
                const newProto = Object.create(Object.getPrototypeOf(navigator));
                delete newProto.webdriver;
                Object.setPrototypeOf(navigator, newProto);
                
                // Remove CDP-specific properties
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
                
                // Clean document attributes
                if (document.documentElement) {
                    const attrs = [...document.documentElement.attributes];
                    attrs.forEach(attr => {
                        if (attr.name.includes('webdriver') || 
                            attr.name.includes('selenium') ||
                            attr.name.includes('driver')) {
                            document.documentElement.removeAttribute(attr.name);
                        }
                    });
                }
            """
        })
    
    async def _setup_console_api_bypass(self, client: CDPSession) -> None:
        """Setup console API bypass to prevent CDP detection."""
        # This prevents detection through Runtime.consoleAPICalled events
        await client.send('Runtime.discardConsoleEntries')
        
        # Disable console domain to prevent console API events
        try:
            await client.send('Console.disable')
        except Exception:
            pass  # Console domain might not be enabled
        
        # Add console override script
        await client.send('Page.addScriptToEvaluateOnNewDocument', {
            'source': """
                // Override console to prevent CDP detection
                (() => {
                    const originalConsole = window.console;
                    const methods = ['log', 'debug', 'info', 'warn', 'error'];
                    
                    methods.forEach(method => {
                        const original = originalConsole[method];
                        
                        originalConsole[method] = function(...args) {
                            // Check if being called by CDP
                            const stack = new Error().stack;
                            if (stack && (
                                stack.includes('Runtime.callFunctionOn') ||
                                stack.includes('Runtime.evaluate') ||
                                stack.includes('__puppeteer_evaluation_script__') ||
                                stack.includes('__playwright_evaluation_script__')
                            )) {
                                // Ignore CDP calls
                                return;
                            }
                            
                            // Normal call
                            return original.apply(this, args);
                        };
                        
                        // Maintain native appearance
                        originalConsole[method].toString = () => 
                            `function ${method}() { [native code] }`;
                    });
                })();
            """
        })
    
    async def _configure_page_domain(self, client: CDPSession) -> None:
        """Configure Page domain for stealth."""
        # Enable Page domain with stealth settings
        await client.send('Page.enable')
        
        # Set bypass CSP
        await client.send('Page.setBypassCSP', {'enabled': True})
        
        # Handle JavaScript dialogs automatically
        client.on('Page.javascriptDialogOpening', 
                 lambda params: self._handle_dialog(client, params))
        
        # Add frame navigation monitoring
        client.on('Page.frameNavigated', 
                 lambda params: self._on_frame_navigated(params))
    
    async def _get_current_user_agent(self, client: CDPSession) -> str:
        """Get current user agent from page."""
        try:
            result = await client.send('Runtime.evaluate', {
                'expression': 'navigator.userAgent',
                'returnByValue': True
            })
            return result.get('result', {}).get('value', '')
        except Exception:
            # Default user agent
            return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/131.0.0.0 Safari/537.36")
    
    async def _handle_dialog(self, client: CDPSession, params: Dict[str, Any]) -> None:
        """Handle JavaScript dialogs automatically."""
        try:
            await client.send('Page.handleJavaScriptDialog', {
                'accept': True,
                'promptText': ''
            })
        except Exception as e:
            logger.error(f"Failed to handle dialog: {e}")
    
    def _on_frame_navigated(self, params: Dict[str, Any]) -> None:
        """Handle frame navigation events."""
        frame = params.get('frame', {})
        url = frame.get('url', '')
        
        # Log navigations for debugging
        if url and not url.startswith('about:'):
            logger.debug(f"Frame navigated to: {url}")
    
    def is_protected(self, page: Page) -> bool:
        """
        Check if a page has CDP protection applied.
        
        Args:
            page: Page to check
            
        Returns:
            Protection status
        """
        page_id = str(id(page))
        return page_id in self._protected_pages
    
    async def cleanup(self, page: Page) -> None:
        """
        Clean up CDP resources for a page.
        
        Args:
            page: Page to clean up
        """
        page_id = str(id(page))
        
        # Close CDP session
        if page_id in self._cdp_sessions:
            try:
                # CDP sessions are automatically closed with the page
                del self._cdp_sessions[page_id]
            except Exception:
                pass
        
        # Remove from protected set
        self._protected_pages.discard(page_id)

# stealthmaster/stealth/behaviors.py
"""Human behavior simulation for anti-detection."""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class HumanBehavior:
    """Simulates human-like behavior patterns."""
    
    def __init__(self):
        """Initialize behavior engine."""
        self._active_pages: Dict[str, Dict[str, Any]] = {}
        self._behavior_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self, page: Page) -> None:
        """
        Initialize human behavior simulation for a page.
        
        Args:
            page: Page to apply behaviors to
        """
        page_id = str(id(page))
        
        if page_id in self._active_pages:
            logger.debug(f"Behaviors already initialized for page {page_id}")
            return
        
        # Initialize page data
        self._active_pages[page_id] = {
            "page": page,
            "created_at": datetime.now(),
            "last_interaction": datetime.now(),
            "interaction_count": 0,
            "idle_time": 0,
            "mouse_position": (0, 0),
        }
        
        # Start behavior simulation
        task = asyncio.create_task(self._behavior_loop(page_id))
        self._behavior_tasks[page_id] = task
        
        # Inject behavior tracking script
        await self._inject_behavior_script(page)
        
        logger.debug(f"Initialized human behaviors for page {page_id}")
    
    async def _inject_behavior_script(self, page: Page) -> None:
        """Inject client-side behavior simulation."""
        await page.add_init_script("""
        // Human behavior tracking
        (() => {
            'use strict';
            
            // Track user activity
            let lastActivity = Date.now();
            let isIdle = false;
            let mousePosition = { x: 0, y: 0 };
            
            // Mouse tracking
            document.addEventListener('mousemove', (e) => {
                mousePosition.x = e.clientX;
                mousePosition.y = e.clientY;
                lastActivity = Date.now();
                isIdle = false;
            });
            
            // Activity tracking
            ['click', 'keydown', 'scroll', 'touchstart'].forEach(eventType => {
                document.addEventListener(eventType, () => {
                    lastActivity = Date.now();
                    isIdle = false;
                });
            });
            
            // Idle detection
            setInterval(() => {
                if (Date.now() - lastActivity > 30000) {
                    isIdle = true;
                }
            }, 5000);
            
            // Natural micro-movements when idle
            setInterval(() => {
                if (!isIdle) return;
                
                // Small random mouse movements
                const event = new MouseEvent('mousemove', {
                    clientX: mousePosition.x + (Math.random() - 0.5) * 2,
                    clientY: mousePosition.y + (Math.random() - 0.5) * 2,
                    bubbles: true
                });
                document.dispatchEvent(event);
            }, 3000 + Math.random() * 2000);
            
            // Realistic scrolling patterns
            let scrollDirection = 1;
            let lastScrollTime = Date.now();
            
            const naturalScroll = () => {
                if (isIdle || Date.now() - lastScrollTime < 5000) return;
                
                const scrollHeight = document.documentElement.scrollHeight;
                const viewHeight = window.innerHeight;
                const currentScroll = window.scrollY;
                
                if (scrollHeight > viewHeight) {
                    // Determine scroll amount with variation
                    const baseScroll = 100 + Math.random() * 200;
                    const scrollAmount = baseScroll * scrollDirection;
                    
                    // Change direction at boundaries
                    if (currentScroll + viewHeight >= scrollHeight - 10) {
                        scrollDirection = -1;
                    } else if (currentScroll <= 10) {
                        scrollDirection = 1;
                    }
                    
                    // Smooth scroll
                    window.scrollBy({
                        top: scrollAmount,
                        behavior: 'smooth'
                    });
                    
                    lastScrollTime = Date.now();
                }
            };
            
            // Random scrolling intervals
            setInterval(() => {
                if (Math.random() < 0.3) {
                    naturalScroll();
                }
            }, 8000 + Math.random() * 7000);
            
            // Focus simulation
            const simulateFocus = () => {
                const focusable = document.querySelectorAll(
                    'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                
                if (focusable.length > 0 && Math.random() < 0.2) {
                    const element = focusable[Math.floor(Math.random() * focusable.length)];
                    
                    // Simulate hover before focus
                    const hoverEvent = new MouseEvent('mouseenter', { bubbles: true });
                    element.dispatchEvent(hoverEvent);
                    
                    setTimeout(() => {
                        element.focus();
                        
                        // Sometimes click
                        if (Math.random() < 0.1 && element.tagName !== 'INPUT') {
                            element.click();
                        }
                    }, 300 + Math.random() * 500);
                }
            };
            
            // Random focus changes
            setInterval(() => {
                if (!isIdle) {
                    simulateFocus();
                }
            }, 15000 + Math.random() * 10000);
            
            // Page visibility handling
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    isIdle = true;
                } else {
                    lastActivity = Date.now();
                    isIdle = false;
                }
            });
            
            // Export state for external access
            window.__humanBehavior__ = {
                get isIdle() { return isIdle; },
                get lastActivity() { return lastActivity; },
                get mousePosition() { return mousePosition; }
            };
        })();
        """)
    
    async def _behavior_loop(self, page_id: str) -> None:
        """Main behavior simulation loop."""
        page_data = self._active_pages[page_id]
        page = page_data["page"]
        
        while page_id in self._active_pages:
            try:
                # Random interval between behaviors
                await asyncio.sleep(random.uniform(2, 5))
                
                # Check if page is still valid
                if page.is_closed():
                    break
                
                # Get current state from page
                state = await self._get_page_state(page)
                
                if not state.get("isIdle", False):
                    # Perform random behaviors
                    behavior = random.choice([
                        self._simulate_mouse_movement,
                        self._simulate_viewport_change,
                        self._simulate_reading_pattern,
                        self._simulate_hover_behavior,
                    ])
                    
                    await behavior(page, page_data)
                    
                    # Update interaction data
                    page_data["last_interaction"] = datetime.now()
                    page_data["interaction_count"] += 1
                else:
                    page_data["idle_time"] += 3
                
            except Exception as e:
                logger.error(f"Behavior loop error: {e}")
                await asyncio.sleep(5)
        
        logger.debug(f"Behavior loop ended for page {page_id}")
    
    async def _get_page_state(self, page: Page) -> Dict[str, Any]:
        """Get current page state."""
        try:
            return await page.evaluate("""
                () => {
                    const behavior = window.__humanBehavior__ || {};
                    return {
                        isIdle: behavior.isIdle || false,
                        lastActivity: behavior.lastActivity || Date.now(),
                        mousePosition: behavior.mousePosition || { x: 0, y: 0 },
                        scrollY: window.scrollY,
                        scrollHeight: document.documentElement.scrollHeight,
                        viewHeight: window.innerHeight
                    };
                }
            """)
        except Exception:
            return {}
    
    async def _simulate_mouse_movement(
        self,
        page: Page,
        page_data: Dict[str, Any]
    ) -> None:
        """Simulate natural mouse movements."""
        try:
            viewport = page.viewport_size
            if not viewport:
                return
            
            # Get current position
            current_x, current_y = page_data.get("mouse_position", (0, 0))
            
            # Generate natural target
            target_x = random.randint(100, viewport["width"] - 100)
            target_y = random.randint(100, viewport["height"] - 100)
            
            # Move with bezier curve
            await self._move_mouse_naturally(
                page,
                (current_x, current_y),
                (target_x, target_y)
            )
            
            # Update position
            page_data["mouse_position"] = (target_x, target_y)
            
        except Exception as e:
            logger.debug(f"Mouse movement error: {e}")
    
    async def _move_mouse_naturally(
        self,
        page: Page,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> None:
        """Move mouse with natural bezier curve."""
        # Generate control points for bezier curve
        ctrl1_x = start[0] + (end[0] - start[0]) * 0.25 + random.uniform(-50, 50)
        ctrl1_y = start[1] + (end[1] - start[1]) * 0.25 + random.uniform(-50, 50)
        
        ctrl2_x = start[0] + (end[0] - start[0]) * 0.75 + random.uniform(-50, 50)
        ctrl2_y = start[1] + (end[1] - start[1]) * 0.75 + random.uniform(-50, 50)
        
        # Number of steps based on distance
        distance = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
        steps = max(10, int(distance / 5))
        
        # Move along bezier curve
        for i in range(steps + 1):
            t = i / steps
            
            # Bezier curve formula
            x = (1-t)**3 * start[0] + \
                3*(1-t)**2*t * ctrl1_x + \
                3*(1-t)*t**2 * ctrl2_x + \
                t**3 * end[0]
            
            y = (1-t)**3 * start[1] + \
                3*(1-t)**2*t * ctrl1_y + \
                3*(1-t)*t**2 * ctrl2_y + \
                t**3 * end[1]
            
            await page.mouse.move(x, y)
            
            # Variable delay for natural movement
            delay = random.uniform(0.005, 0.02)
            if i % 5 == 0:  # Occasional pauses
                delay *= random.uniform(1, 3)
            
            await asyncio.sleep(delay)
    
    async def _simulate_viewport_change(
        self,
        page: Page,
        page_data: Dict[str, Any]
    ) -> None:
        """Simulate viewport interactions like scrolling."""
        try:
            state = await self._get_page_state(page)
            
            scroll_height = state.get("scrollHeight", 0)
            view_height = state.get("viewHeight", 0)
            current_scroll = state.get("scrollY", 0)
            
            if scroll_height > view_height:
                # Determine scroll direction and amount
                if current_scroll < scroll_height - view_height - 100:
                    # Scroll down
                    scroll_amount = random.randint(100, 300)
                else:
                    # Scroll up
                    scroll_amount = -random.randint(100, 300)
                
                # Smooth scroll
                await page.evaluate(f"""
                    window.scrollBy({{
                        top: {scroll_amount},
                        behavior: 'smooth'
                    }});
                """)
                
                # Wait for scroll to complete
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
        except Exception as e:
            logger.debug(f"Viewport change error: {e}")
    
    async def _simulate_reading_pattern(
        self,
        page: Page,
        page_data: Dict[str, Any]
    ) -> None:
        """Simulate reading patterns with pauses."""
        try:
            # Find text elements
            elements = await page.query_selector_all("p, h1, h2, h3, span")
            
            if elements:
                # Pick random element to "read"
                element = random.choice(elements)
                
                # Get element position
                box = await element.bounding_box()
                if box:
                    # Move mouse to text area
                    x = box["x"] + box["width"] * 0.3
                    y = box["y"] + box["height"] * 0.5
                    
                    await self._move_mouse_naturally(
                        page,
                        page_data.get("mouse_position", (0, 0)),
                        (x, y)
                    )
                    
                    page_data["mouse_position"] = (x, y)
                    
                    # Simulate reading time
                    text_length = await element.evaluate("el => el.textContent.length")
                    read_time = min(5, text_length * 0.05)  # ~50ms per character
                    await asyncio.sleep(read_time)
                    
        except Exception as e:
            logger.debug(f"Reading pattern error: {e}")
    
    async def _simulate_hover_behavior(
        self,
        page: Page,
        page_data: Dict[str, Any]
    ) -> None:
        """Simulate hovering over interactive elements."""
        try:
            # Find interactive elements
            elements = await page.query_selector_all("a, button, input, select")
            
            if elements:
                element = random.choice(elements)
                
                # Check if visible
                is_visible = await element.is_visible()
                if is_visible:
                    # Get position
                    box = await element.bounding_box()
                    if box:
                        # Move to element
                        x = box["x"] + box["width"] / 2
                        y = box["y"] + box["height"] / 2
                        
                        await self._move_mouse_naturally(
                            page,
                            page_data.get("mouse_position", (0, 0)),
                            (x, y)
                        )
                        
                        page_data["mouse_position"] = (x, y)
                        
                        # Hover duration
                        await asyncio.sleep(random.uniform(0.5, 2))
                        
                        # Sometimes click (rarely)
                        if random.random() < 0.05:
                            await element.click()
                            
        except Exception as e:
            logger.debug(f"Hover behavior error: {e}")
    
    async def type_like_human(
        self,
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True
    ) -> None:
        """
        Type text with human-like patterns.
        
        Args:
            page: Page instance
            selector: Element selector
            text: Text to type
            clear_first: Whether to clear existing text
        """
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if not element:
                return
            
            # Click to focus
            await element.click()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Clear if needed
            if clear_first:
                await element.click(click_count=3)  # Triple click
                await page.keyboard.press("Delete")
                await asyncio.sleep(random.uniform(0.2, 0.4))
            
            # Type with variations
            for i, char in enumerate(text):
                # Occasional typos
                if random.random() < 0.02 and i < len(text) - 1:
                    # Type wrong character
                    wrong_char = random.choice("asdfghjkl")
                    await page.keyboard.type(wrong_char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                    
                    # Delete it
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                
                # Type correct character
                await page.keyboard.type(char)
                
                # Variable delays
                if char == " ":
                    delay = random.uniform(0.05, 0.15)
                elif char in ".,!?":
                    delay = random.uniform(0.15, 0.3)
                else:
                    # Typing rhythm variations
                    base_delay = random.uniform(0.03, 0.08)
                    if random.random() < 0.1:  # Occasional pause
                        delay = base_delay * random.uniform(2, 4)
                    else:
                        delay = base_delay
                
                await asyncio.sleep(delay)
                
        except Exception as e:
            logger.error(f"Human typing error: {e}")
    
    async def click_with_behavior(
        self,
        page: Page,
        selector: str
    ) -> bool:
        """
        Click element with human-like behavior.
        
        Args:
            page: Page instance
            selector: Element selector
            
        Returns:
            Success status
        """
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if not element:
                return False
            
            # Get element position
            box = await element.bounding_box()
            if not box:
                return False
            
            # Calculate click position with offset
            x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
            y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
            
            # Move to element first
            page_data = self._active_pages.get(str(id(page)), {})
            current_pos = page_data.get("mouse_position", (0, 0))
            
            await self._move_mouse_naturally(page, current_pos, (x, y))
            
            # Hover briefly
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Click
            await page.mouse.click(x, y)
            
            # Update position
            if str(id(page)) in self._active_pages:
                self._active_pages[str(id(page))]["mouse_position"] = (x, y)
            
            return True
            
        except Exception as e:
            logger.error(f"Human click error: {e}")
            return False
    
    def is_active(self, page: Page) -> bool:
        """Check if behaviors are active for page."""
        page_id = str(id(page))
        return page_id in self._active_pages
    
    async def cleanup(self, page: Page) -> None:
        """Clean up behaviors for a page."""
        page_id = str(id(page))
        
        # Cancel behavior task
        if page_id in self._behavior_tasks:
            task = self._behavior_tasks[page_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._behavior_tasks[page_id]
        
        # Remove page data
        if page_id in self._active_pages:
            del self._active_pages[page_id]
        
        logger.debug(f"Cleaned up behaviors for page {page_id}")
    
    def is_protected(self, page: Page) -> bool:
        """Check if page has CDP protection applied."""
        return str(id(page)) in self._active_pages