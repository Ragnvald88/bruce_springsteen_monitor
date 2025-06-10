# stealthmaster/stealth/cdp.py
"""
CDP (Chrome DevTools Protocol) Stealth - Advanced protocol-level evasion.
Implements cutting-edge techniques to bypass 2025 AI-driven bot detection.
"""

import asyncio
import json
import logging
import random
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime
import re

from playwright.async_api import BrowserContext, Page, CDPSession

logger = logging.getLogger(__name__)


class CDPStealth:
    """
    Advanced CDP-level stealth implementation for 2025 detection evasion.
    Bypasses modern AI-driven bot detection at the protocol level.
    """
    
    def __init__(self):
        """Initialize CDP stealth components."""
        self._patched_contexts: Set[str] = set()
        self._patched_pages: Set[str] = set()
        self._cdp_sessions: Dict[str, CDPSession] = {}
        
        # Detection countermeasures
        self._blocked_domains = self._get_blocked_domains()
        self._modified_responses = {}
        
        logger.info("CDP Stealth  initialized with 2025 evasion capabilities")
    
    def _get_blocked_domains(self) -> List[str]:
        """Get list of CDP domains to block/modify."""
        return [
            "Runtime.enable",
            "Runtime.evaluate",
            "Runtime.getProperties",
            "Runtime.consoleAPICalled",
            "Debugger.enable",
            "Debugger.getScriptSource",
            "Page.addScriptToEvaluateOnNewDocument",
            "Network.enable",
            "Log.enable",
            "DOM.enable",
            "CSS.enable",
            "Overlay.enable",
            "Inspector.enable",
            "Profiler.enable",
            "HeapProfiler.enable"
        ]
    
    async def apply_context_stealth(self, context: BrowserContext) -> None:
        """
        Apply CDP-level stealth to browser context.
        
        Args:
            context: Browser context to protect
        """
        context_id = str(id(context))
        
        if context_id in self._patched_contexts:
            return
        
        try:
            # Override CDP exposure before any page creation
            await context.add_init_script(self._get_cdp_override_script())
            
            # Set up route interception for CDP detection
            await context.route("**/*", self._handle_cdp_detection_route)
            
            # Apply context-wide CDP modifications
            context.on("page", lambda page: asyncio.create_task(
                self.apply_page_stealth(page)
            ))
            
            self._patched_contexts.add(context_id)
            logger.debug(f"Applied CDP stealth to context {context_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply context CDP stealth: {e}")
    
    async def apply_page_stealth(self, page: Page) -> None:
        """
        Apply comprehensive CDP stealth to a page.
        
        Args:
            page: Page to protect
        """
        page_id = str(id(page))
        
        if page_id in self._patched_pages:
            return
        
        try:
            # Create CDP session
            cdp_session = await page.context.new_cdp_session(page)
            self._cdp_sessions[page_id] = cdp_session
            
            # Apply CDP-level modifications
            await self._apply_cdp_overrides(cdp_session)
            await self._modify_runtime_domain(cdp_session)
            await self._setup_network_interception(cdp_session)
            await self._setup_console_override(cdp_session)
            
            # Inject advanced evasion scripts
            await cdp_session.send("Page.addScriptToEvaluateOnNewDocument", {
                "source": self._get_advanced_evasion_script()
            })
            
            # Monitor for CDP detection attempts
            await self._setup_detection_monitoring(cdp_session, page)
            
            self._patched_pages.add(page_id)
            logger.debug(f"Applied CDP stealth to page {page_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply page CDP stealth: {e}")
    
    def _get_cdp_override_script(self) -> str:
        """Get script to override CDP detection at context level."""
        return """
        (() => {
            'use strict';
            
            // Override CDP domain exposure
            const cdpDomains = ['Runtime', 'Debugger', 'Profiler', 'HeapProfiler', 'Page', 'Network'];
            
            cdpDomains.forEach(domain => {
                if (window[domain]) {
                    delete window[domain];
                }
                
                Object.defineProperty(window, domain, {
                    get: function() {
                        return undefined;
                    },
                    set: function() {
                        return true;
                    },
                    enumerable: false,
                    configurable: false
                });
            });
            
            // Override console methods that might expose CDP
            const originalConsole = window.console;
            const consoleProxy = new Proxy(originalConsole, {
                get: function(target, prop) {
                    // Block certain console methods used for detection
                    if (['memory', 'profile', 'profileEnd'].includes(prop)) {
                        return undefined;
                    }
                    
                    // Clean stack traces
                    if (prop === 'log' || prop === 'error' || prop === 'warn') {
                        return function(...args) {
                            // Clean arguments of CDP references
                            const cleanArgs = args.map(arg => {
                                if (typeof arg === 'string') {
                                    return arg.replace(/\b(CDP|DevTools|Protocol|Runtime\.)\b/gi, '');
                                }
                                return arg;
                            });
                            
                            return target[prop].apply(target, cleanArgs);
                        };
                    }
                    
                    return target[prop];
                }
            });
            
            window.console = consoleProxy;
            
            // Override Error stack traces to remove CDP references
            const OriginalError = window.Error;
            window.Error = class Error extends OriginalError {
                constructor(message) {
                    super(message);
                    if (this.stack) {
                        this.stack = this.stack
                            .split('\\n')
                            .filter(line => !line.includes('__puppeteer_evaluation_script__'))
                            .filter(line => !line.includes('evaluateHandle'))
                            .filter(line => !line.includes('ExecutionContext'))
                            .filter(line => !line.includes('CDPSession'))
                            .join('\\n');
                    }
                }
            };
            
            // Prevent CDP session detection via prototype
            const originalCall = Function.prototype.call;
            Function.prototype.call = function(...args) {
                // Block CDP-related function calls
                if (this.toString().includes('CDP') || 
                    this.toString().includes('DevTools') ||
                    this.toString().includes('Runtime.enable')) {
                    throw new Error('Undefined is not a function');
                }
                return originalCall.apply(this, args);
            };
            
            // Monitor and block WebSocket connections to DevTools
            const OriginalWebSocket = window.WebSocket;
            window.WebSocket = class WebSocket extends OriginalWebSocket {
                constructor(url, protocols) {
                    // Block DevTools WebSocket connections
                    if (url.includes('devtools') || url.includes('/json') || url.includes('inspector')) {
                        throw new Error('WebSocket connection failed');
                    }
                    super(url, protocols);
                }
            };
        })();
        """
    
    def _get_advanced_evasion_script(self) -> str:
        """Get advanced CDP evasion script for page-level injection."""
        return """
        (() => {
            'use strict';
            
            // Advanced CDP detection evasion
            const cdpDetectionEvasion = {
                // Block Runtime.enable detection
                blockRuntimeEnable: function() {
                    const nativeWebSocket = window.WebSocket;
                    const nativeSend = nativeWebSocket.prototype.send;
                    
                    nativeWebSocket.prototype.send = function(data) {
                        if (typeof data === 'string') {
                            try {
                                const parsed = JSON.parse(data);
                                // Block Runtime.enable and other CDP commands
                                if (parsed.method && (
                                    parsed.method === 'Runtime.enable' ||
                                    parsed.method === 'Debugger.enable' ||
                                    parsed.method === 'Profiler.enable'
                                )) {
                                    return;
                                }
                            } catch (e) {}
                        }
                        return nativeSend.call(this, data);
                    };
                },
                
                // Clean execution context
                cleanExecutionContext: function() {
                    // Remove execution context markers
                    delete window.__commandLineAPI;
                    delete window.__commandLineAPIImpl;
                    
                    // Override inspect function
                    window.inspect = undefined;
                    
                    // Clean global functions that might expose automation
                    const suspiciousFunctions = ['debug', 'monitorEvents', 'profile', 'profileEnd'];
                    suspiciousFunctions.forEach(func => {
                        if (window[func]) {
                            delete window[func];
                        }
                    });
                },
                
                // Prevent CDP protocol detection via timing
                preventTimingDetection: function() {
                    // Add random micro-delays to prevent timing analysis
                    const originalSetTimeout = window.setTimeout;
                    window.setTimeout = function(callback, delay, ...args) {
                        // Add 0-5ms random delay
                        const randomDelay = Math.random() * 5;
                        return originalSetTimeout.call(window, callback, delay + randomDelay, ...args);
                    };
                },
                
                // Block CDP domain property access
                blockDomainAccess: function() {
                    const handler = {
                        get: function(target, prop) {
                            // Check if accessing CDP-related properties
                            const cdpProps = ['enable', 'disable', 'evaluate', 'awaitPromise'];
                            if (cdpProps.includes(prop)) {
                                throw new TypeError('Cannot read property \\'' + prop + '\\' of undefined');
                            }
                            return target[prop];
                        }
                    };
                    
                    // Wrap suspicious objects
                    if (window.chrome && window.chrome.send) {
                        window.chrome.send = new Proxy(window.chrome.send, handler);
                    }
                },
                
                // Initialize all evasions
                init: function() {
                    this.blockRuntimeEnable();
                    this.cleanExecutionContext();
                    this.preventTimingDetection();
                    this.blockDomainAccess();
                }
            };
            
            // Initialize evasions
            cdpDetectionEvasion.init();
            
            // Monitor for dynamic detection attempts
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === 1) { // Element node
                                // Check for CDP detection scripts
                                if (node.tagName === 'SCRIPT' && node.src) {
                                    if (node.src.includes('devtools') || 
                                        node.src.includes('inspector') ||
                                        node.src.includes('debugger')) {
                                        node.remove();
                                    }
                                }
                            }
                        });
                    }
                });
            });
            
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        })();
        """
    
    async def _apply_cdp_overrides(self, cdp: CDPSession) -> None:
        """Apply CDP protocol overrides."""
        try:
            # Disable domains that could expose automation
            domains_to_disable = ["Debugger", "Profiler", "HeapProfiler", "Runtime"]
            
            for domain in domains_to_disable:
                try:
                    await cdp.send(f"{domain}.disable")
                except Exception:
                    pass  # Domain might not be enabled
            
            # Override Page domain settings
            await cdp.send("Page.setWebLifecycleState", {"state": "active"})
            
            # Set touch and mobile emulation to false
            await cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": False})
            
            # Ensure navigator.webdriver is never exposed
            await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                    configurable: false,
                    enumerable: false
                });
                """
            })
            
        except Exception as e:
            logger.debug(f"CDP override error: {e}")
    
    async def _modify_runtime_domain(self, cdp: CDPSession) -> None:
        """Modify Runtime domain to prevent detection."""
        try:
            # Override console API
            await cdp.send("Runtime.consoleAPICalled", {
                "type": "log",
                "args": [],
                "executionContextId": 1,
                "timestamp": 0
            })
            
            # Modify global execution context
            await cdp.send("Runtime.evaluate", {
                "expression": """
                    // Remove automation indicators from global scope
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                    
                    // Clean document properties
                    delete document.$cdc_asdjflasutopfhvcZLmcfl_;
                    delete document.$chrome_asyncScriptInfo;
                    
                    // Remove webdriver callout
                    delete navigator.__webdriver_script_fn;
                    delete navigator.__driver_evaluate;
                    delete navigator.__webdriver_evaluate;
                    delete navigator.__selenium_evaluate;
                    delete navigator.__fxdriver_evaluate;
                    delete navigator.__driver_unwrapped;
                    delete navigator.__webdriver_unwrapped;
                    delete navigator.__selenium_unwrapped;
                    delete navigator.__fxdriver_unwrapped;
                """
            })
            
        except Exception as e:
            logger.debug(f"Runtime modification error: {e}")
    
    async def _setup_network_interception(self, cdp: CDPSession) -> None:
        """Set up network-level interception for CDP detection."""
        try:
            # Enable network domain with minimal features
            await cdp.send("Network.enable", {
                "maxPostDataSize": 0,
                "maxResourceBufferSize": 0,
                "maxTotalBufferSize": 0
            })
            
            # Intercept and modify responses that might contain detection scripts
            await cdp.send("Network.setResponseInterceptionEnabled", {"enabled": True})
            
            # Set up response interceptor
            async def on_response(params):
                request_id = params.get("requestId")
                response = params.get("response", {})
                
                # Check for detection-related responses
                url = response.get("url", "")
                if any(pattern in url.lower() for pattern in ["detect", "fingerprint", "bot", "cdp"]):
                    # Log potential detection attempt
                    logger.warning(f"Potential detection script: {url}")
            
            cdp.on("Network.responseReceived", on_response)
            
        except Exception as e:
            logger.debug(f"Network interception setup error: {e}")
    
    async def _setup_console_override(self, cdp: CDPSession) -> None:
        """Override console to prevent CDP detection via console."""
        try:
            await cdp.send("Console.enable")
            
            # Override console methods
            await cdp.send("Runtime.evaluate", {
                "expression": """
                    // Store original console
                    const originalConsole = window.console;
                    
                    // Create filtered console
                    window.console = new Proxy(originalConsole, {
                        get(target, prop) {
                            // Filter out CDP-related console methods
                            if (['memory', 'profile', 'profileEnd', 'timeStamp'].includes(prop)) {
                                return () => {};
                            }
                            
                            // Wrap other methods to clean output
                            if (typeof target[prop] === 'function') {
                                return function(...args) {
                                    // Filter CDP-related messages
                                    const filteredArgs = args.filter(arg => {
                                        if (typeof arg === 'string') {
                                            return !arg.includes('CDP') && 
                                                   !arg.includes('DevTools') &&
                                                   !arg.includes('Protocol');
                                        }
                                        return true;
                                    });
                                    
                                    if (filteredArgs.length > 0) {
                                        return target[prop].apply(target, filteredArgs);
                                    }
                                };
                            }
                            
                            return target[prop];
                        }
                    });
                """
            })
            
        except Exception as e:
            logger.debug(f"Console override error: {e}")
    
    async def _setup_detection_monitoring(self, cdp: CDPSession, page: Page) -> None:
        """Monitor for CDP detection attempts."""
        detection_patterns = [
            "Runtime.enable",
            "Debugger.enable", 
            "CDP detected",
            "DevTools detected",
            "Automation detected"
        ]
        
        # Monitor console messages
        async def on_console_message(params):
            message = params.get("message", {})
            text = message.get("text", "")
            
            for pattern in detection_patterns:
                if pattern.lower() in text.lower():
                    logger.warning(f"CDP detection attempt via console: {text}")
                    # Could trigger additional evasion here
        
        cdp.on("Console.messageAdded", on_console_message)
        
        # Monitor network requests for detection endpoints
        async def on_request(params):
            request = params.get("request", {})
            url = request.get("url", "")
            
            if any(pattern in url for pattern in ["detect", "fingerprint", "verify"]):
                logger.warning(f"Detection endpoint accessed: {url}")
        
        cdp.on("Network.requestWillBeSent", on_request)
    
    async def _handle_cdp_detection_route(self, route) -> None:
        """Handle routes that might be CDP detection related."""
        request = route.request
        url = request.url.lower()
        
        # Block known detection scripts
        detection_patterns = [
            "devtools-detector",
            "cdp-detector",
            "bot-detector",
            "automation-check"
        ]
        
        if any(pattern in url for pattern in detection_patterns):
            # Return empty response
            await route.fulfill(
                status=200,
                content_type="application/javascript",
                body="// Blocked"
            )
            logger.info(f"Blocked detection script: {request.url}")
        else:
            await route.continue_()
    
    async def cleanup_page(self, page: Page) -> None:
        """Clean up CDP session for a page."""
        page_id = str(id(page))
        
        if page_id in self._cdp_sessions:
            try:
                cdp = self._cdp_sessions[page_id]
                await cdp.detach()
            except Exception:
                pass
            
            del self._cdp_sessions[page_id]
        
        if page_id in self._patched_pages:
            self._patched_pages.remove(page_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CDP stealth statistics."""
        return {
            "patched_contexts": len(self._patched_contexts),
            "patched_pages": len(self._patched_pages),
            "active_cdp_sessions": len(self._cdp_sessions)
        }
