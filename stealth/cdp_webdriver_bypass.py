# stealthmaster/stealth/cdp_webdriver_bypass.py
"""
Advanced CDP-based WebDriver bypass that prevents property creation.
This module implements cutting-edge techniques to prevent the webdriver 
property from ever being created, making detection impossible.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from playwright.async_api import Browser, BrowserContext, Page, CDPSession

logger = logging.getLogger(__name__)


class CDPWebDriverBypass:
    """
    Implements true WebDriver property prevention at the CDP level.
    This bypasses all known detection methods by preventing the property
    from being created in the first place.
    """
    
    def __init__(self):
        """Initialize the CDP WebDriver bypass system."""
        self._patched_browsers = set()
        self._cdp_sessions = {}
        logger.info("CDP WebDriver Bypass initialized")
    
    async def patch_browser_launch(self, browser: Browser) -> None:
        """
        Patch browser at launch to prevent WebDriver property creation.
        Must be called immediately after browser launch.
        
        Args:
            browser: The browser instance to patch
        """
        browser_id = id(browser)
        if browser_id in self._patched_browsers:
            return
            
        try:
            # Get browser CDP session
            # Note: This requires accessing browser internals
            contexts = browser.contexts
            if not contexts:
                # Create temporary context to get CDP access
                temp_context = await browser.new_context()
                await self._patch_browser_cdp(temp_context)
                await temp_context.close()
            else:
                await self._patch_browser_cdp(contexts[0])
            
            self._patched_browsers.add(browser_id)
            logger.info("Browser patched for WebDriver bypass")
            
        except Exception as e:
            logger.error(f"Failed to patch browser: {e}")
    
    async def _patch_browser_cdp(self, context: BrowserContext) -> None:
        """Patch browser using CDP session from context."""
        # Create a temporary page to get CDP session
        temp_page = await context.new_page()
        cdp = await context.new_cdp_session(temp_page)
        
        try:
            # Inject script that runs before ANY page creation
            await self._inject_early_script(cdp)
            
            # Set up browser-wide overrides
            await self._setup_browser_overrides(cdp)
            
        finally:
            await cdp.detach()
            await temp_page.close()
    
    async def _inject_early_script(self, cdp: CDPSession) -> None:
        """Inject script that prevents WebDriver property creation."""
        # This script runs in every execution context before any other script
        prevention_script = """
        (() => {
            'use strict';
            
            // Store the original Object.defineProperty
            const originalDefineProperty = Object.defineProperty;
            const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
            
            // Track if we've patched navigator
            let navigatorPatched = false;
            
            // Override Object.defineProperty to intercept webdriver definition
            Object.defineProperty = function(obj, prop, descriptor) {
                // Check if trying to define webdriver on navigator or its prototype
                if ((obj === navigator || obj === Navigator.prototype) && prop === 'webdriver') {
                    // Log attempt but don't define it
                    console.debug('Blocked webdriver property definition');
                    return obj;
                }
                
                // Check if defining navigator itself
                if (prop === 'navigator' && !navigatorPatched) {
                    // Patch the navigator object being defined
                    const result = originalDefineProperty.call(this, obj, prop, descriptor);
                    patchNavigator();
                    return result;
                }
                
                // Normal property definition
                return originalDefineProperty.call(this, obj, prop, descriptor);
            };
            
            // Function to patch navigator
            function patchNavigator() {
                if (navigatorPatched) return;
                navigatorPatched = true;
                
                try {
                    // Remove webdriver from Navigator prototype
                    const navProto = Navigator.prototype;
                    const protoDescriptor = originalGetOwnPropertyDescriptor(navProto, 'webdriver');
                    
                    if (protoDescriptor) {
                        delete navProto.webdriver;
                    }
                    
                    // Create a new Navigator prototype without webdriver
                    const cleanProto = Object.create(Object.getPrototypeOf(navProto));
                    
                    // Copy all properties except webdriver
                    for (const prop of Object.getOwnPropertyNames(navProto)) {
                        if (prop !== 'webdriver') {
                            const descriptor = originalGetOwnPropertyDescriptor(navProto, prop);
                            if (descriptor) {
                                originalDefineProperty(cleanProto, prop, descriptor);
                            }
                        }
                    }
                    
                    // Set the clean prototype
                    Object.setPrototypeOf(navigator, cleanProto);
                    
                    // Prevent future webdriver definitions
                    originalDefineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        set: () => {},
                        enumerable: false,
                        configurable: false
                    });
                    
                } catch (e) {
                    console.debug('Navigator patch error:', e);
                }
            }
            
            // Patch immediately if navigator exists
            if (typeof navigator !== 'undefined') {
                patchNavigator();
            }
            
            // Also override the Navigator constructor
            if (typeof Navigator !== 'undefined') {
                const OriginalNavigator = Navigator;
                
                // Create patched Navigator constructor
                window.Navigator = new Proxy(OriginalNavigator, {
                    construct(target, args) {
                        const instance = new target(...args);
                        
                        // Remove webdriver from instance
                        delete instance.webdriver;
                        
                        // Prevent webdriver property
                        originalDefineProperty(instance, 'webdriver', {
                            get: () => undefined,
                            set: () => {},
                            enumerable: false,
                            configurable: false
                        });
                        
                        return instance;
                    }
                });
                
                // Copy static properties
                for (const prop in OriginalNavigator) {
                    if (OriginalNavigator.hasOwnProperty(prop)) {
                        Navigator[prop] = OriginalNavigator[prop];
                    }
                }
            }
            
            // Monitor for late navigator creation
            const observer = new MutationObserver(() => {
                if (window.navigator && !navigatorPatched) {
                    patchNavigator();
                }
            });
            
            observer.observe(document, {
                childList: true,
                subtree: true
            });
            
            // Additional protection against CDP detection
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            
        })();
        """
        
        # Inject at multiple levels for maximum coverage
        await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": prevention_script,
            "worldName": "__playwright_utility_world__"
        })
        
        await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": prevention_script
        })
        
        # Also inject into runtime
        await cdp.send("Runtime.evaluate", {
            "expression": prevention_script,
            "includeCommandLineAPI": False,
            "returnByValue": False,
            "awaitPromise": False
        })
    
    async def _setup_browser_overrides(self, cdp: CDPSession) -> None:
        """Set up browser-wide CDP overrides."""
        try:
            # Disable WebDriver flag at browser level
            await cdp.send("Emulation.setAutomationOverride", {"enabled": False})
        except:
            pass  # Not all browsers support this
        
        try:
            # Override user agent to remove HeadlessChrome
            await cdp.send("Emulation.setUserAgentOverride", {
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "acceptLanguage": "en-US,en;q=0.9",
                "platform": "MacIntel"
            })
        except:
            pass
        
        try:
            # Ensure webdriver is false in page settings
            await cdp.send("Page.enable")
            await cdp.send("Page.setWebDriverValue", {"value": False})
        except:
            pass  # Not all CDP implementations have this
    
    async def apply_to_context(self, context: BrowserContext) -> None:
        """
        Apply WebDriver bypass to a browser context.
        
        Args:
            context: The browser context to protect
        """
        # Inject prevention script into context
        await context.add_init_script(self._get_context_script())
        
        # Monitor new pages
        context.on("page", lambda page: asyncio.create_task(
            self.apply_to_page(page)
        ))
        
        logger.debug("Applied WebDriver bypass to context")
    
    async def apply_to_page(self, page: Page) -> None:
        """
        Apply WebDriver bypass to a specific page.
        
        Args:
            page: The page to protect
        """
        page_id = id(page)
        
        try:
            # Get CDP session for page
            cdp = await page.context.new_cdp_session(page)
            self._cdp_sessions[page_id] = cdp
            
            # Apply page-specific protections
            await self._inject_early_script(cdp)
            
            # Additional page protections
            await cdp.send("Runtime.evaluate", {
                "expression": """
                    // Final safeguard - ensure webdriver is never true
                    Object.defineProperty(navigator, 'webdriver', {
                        get: function() {
                            return false;
                        },
                        set: function() {},
                        enumerable: false,
                        configurable: false
                    });
                    
                    // Clean up any CDP artifacts
                    for (const key in window) {
                        if (key.includes('cdc_') || key.includes('_cdc')) {
                            delete window[key];
                        }
                    }
                """
            })
            
            logger.debug(f"Applied WebDriver bypass to page {page_id}")
            
        except Exception as e:
            logger.error(f"Failed to apply page bypass: {e}")
    
    def _get_context_script(self) -> str:
        """Get the context-level injection script."""
        return """
        (() => {
            'use strict';
            
            // Context-level WebDriver prevention
            const script = document.createElement('script');
            script.textContent = `
                delete Object.getPrototypeOf(navigator).webdriver;
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                    enumerable: false,
                    configurable: false
                });
            `;
            
            // Inject before any other scripts
            if (document.documentElement) {
                document.documentElement.appendChild(script);
                script.remove();
            } else {
                // If no documentElement yet, wait for it
                new MutationObserver((mutations, observer) => {
                    if (document.documentElement) {
                        document.documentElement.appendChild(script);
                        script.remove();
                        observer.disconnect();
                    }
                }).observe(document, { childList: true, subtree: true });
            }
            
            // Additional CDP cleanup
            const cleanupCDP = () => {
                const cdpProps = Object.keys(window).filter(key => 
                    key.includes('cdc_') || 
                    key.includes('_cdc') || 
                    key.includes('ChromeDriver')
                );
                
                cdpProps.forEach(prop => {
                    try {
                        delete window[prop];
                    } catch (e) {}
                });
            };
            
            cleanupCDP();
            
            // Monitor for dynamic CDP injection
            const origAdd = EventTarget.prototype.addEventListener;
            EventTarget.prototype.addEventListener = function(...args) {
                // Block CDP-related event listeners
                if (args[0] && typeof args[0] === 'string') {
                    if (args[0].includes('cdc') || args[0].includes('webdriver')) {
                        return;
                    }
                }
                return origAdd.apply(this, args);
            };
        })();
        """
    
    async def cleanup(self, page_id: Any) -> None:
        """Clean up CDP session for a page."""
        if page_id in self._cdp_sessions:
            try:
                await self._cdp_sessions[page_id].detach()
            except:
                pass
            del self._cdp_sessions[page_id]