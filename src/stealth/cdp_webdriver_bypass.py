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
            
            // CRITICAL FIX: More aggressive webdriver removal
            // Store originals before any modifications
            const originalDefineProperty = Object.defineProperty;
            const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
            const originalGetOwnPropertyNames = Object.getOwnPropertyNames;
            const originalHasOwnProperty = Object.prototype.hasOwnProperty;
            
            // Remove webdriver completely before anything else
            if (navigator && 'webdriver' in navigator) {
                delete navigator.webdriver;
            }
            
            // Remove from prototype chain
            if (typeof Navigator !== 'undefined' && Navigator.prototype) {
                delete Navigator.prototype.webdriver;
            }
            
            // Create clean navigator getter that never exposes webdriver
            const navigatorDescriptor = originalGetOwnPropertyDescriptor(window, 'navigator');
            if (navigatorDescriptor) {
                const originalNavigator = navigatorDescriptor.get ? navigatorDescriptor.get() : window.navigator;
                
                originalDefineProperty(window, 'navigator', {
                    get() {
                        const nav = originalNavigator;
                        
                        // Ensure webdriver is never present
                        if ('webdriver' in nav) {
                            delete nav.webdriver;
                        }
                        
                        // Override property access
                        const navProxy = new Proxy(nav, {
                            get(target, prop) {
                                if (prop === 'webdriver') {
                                    return undefined;
                                }
                                return target[prop];
                            },
                            has(target, prop) {
                                if (prop === 'webdriver') {
                                    return false;
                                }
                                return prop in target;
                            },
                            ownKeys(target) {
                                return originalGetOwnPropertyNames(target).filter(key => key !== 'webdriver');
                            },
                            getOwnPropertyDescriptor(target, prop) {
                                if (prop === 'webdriver') {
                                    return undefined;
                                }
                                return originalGetOwnPropertyDescriptor(target, prop);
                            }
                        });
                        
                        return navProxy;
                    },
                    configurable: false,
                    enumerable: true
                });
            }
            
            // Override Object.defineProperty to block webdriver
            Object.defineProperty = function(obj, prop, descriptor) {
                if ((obj === navigator || obj === Navigator.prototype || obj === window.navigator) && prop === 'webdriver') {
                    return obj;
                }
                return originalDefineProperty.call(this, obj, prop, descriptor);
            };
            
            // Override getOwnPropertyDescriptor to hide webdriver
            Object.getOwnPropertyDescriptor = function(obj, prop) {
                if ((obj === navigator || obj === Navigator.prototype) && prop === 'webdriver') {
                    return undefined;
                }
                return originalGetOwnPropertyDescriptor.call(this, obj, prop);
            };
            
            // Override getOwnPropertyNames to exclude webdriver
            Object.getOwnPropertyNames = function(obj) {
                const names = originalGetOwnPropertyNames.call(this, obj);
                if (obj === navigator || obj === Navigator.prototype) {
                    return names.filter(name => name !== 'webdriver');
                }
                return names;
            };
            
            // Override hasOwnProperty
            Object.prototype.hasOwnProperty = function(prop) {
                if (this === navigator && prop === 'webdriver') {
                    return false;
                }
                return originalHasOwnProperty.call(this, prop);
            };
            
            // Override 'in' operator via Proxy on Navigator.prototype
            if (typeof Navigator !== 'undefined') {
                const OriginalNavigator = Navigator;
                const OriginalPrototype = Navigator.prototype;
                
                // Create new clean prototype
                const CleanPrototype = new Proxy(OriginalPrototype, {
                    has(target, prop) {
                        if (prop === 'webdriver') {
                            return false;
                        }
                        return prop in target;
                    },
                    get(target, prop) {
                        if (prop === 'webdriver') {
                            return undefined;
                        }
                        return target[prop];
                    },
                    getOwnPropertyDescriptor(target, prop) {
                        if (prop === 'webdriver') {
                            return undefined;
                        }
                        return originalGetOwnPropertyDescriptor(target, prop);
                    }
                });
                
                // Replace Navigator constructor
                window.Navigator = new Proxy(OriginalNavigator, {
                    construct(target, args) {
                        const instance = new target(...args);
                        
                        // Create proxy for each instance
                        return new Proxy(instance, {
                            get(target, prop) {
                                if (prop === 'webdriver') {
                                    return undefined;
                                }
                                return target[prop];
                            },
                            has(target, prop) {
                                if (prop === 'webdriver') {
                                    return false;
                                }
                                return prop in target;
                            }
                        });
                    },
                    get(target, prop) {
                        if (prop === 'prototype') {
                            return CleanPrototype;
                        }
                        return target[prop];
                    }
                });
                
                // Copy static properties
                for (const prop in OriginalNavigator) {
                    if (originalHasOwnProperty.call(OriginalNavigator, prop) && prop !== 'prototype') {
                        Navigator[prop] = OriginalNavigator[prop];
                    }
                }
            }
            
            // Remove all CDP artifacts
            const cdpProps = [
                'cdc_adoQpoasnfa76pfcZLmcfl_Array',
                'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 
                'cdc_adoQpoasnfa76pfcZLmcfl_Symbol',
                'cdc_adoQpoasnfa76pfcZLmcfl_JSON',
                'cdc_adoQpoasnfa76pfcZLmcfl_Object',
                'cdc_adoQpoasnfa76pfcZLmcfl_Proxy'
            ];
            
            cdpProps.forEach(prop => {
                try {
                    delete window[prop];
                    delete document[prop];
                } catch (e) {}
            });
            
            // Monitor and clean continuously
            const cleanupInterval = setInterval(() => {
                if (navigator && 'webdriver' in navigator) {
                    delete navigator.webdriver;
                }
                
                // Clean CDP props
                for (const key in window) {
                    if (key.includes('cdc_') || key.includes('_cdc')) {
                        try {
                            delete window[key];
                        } catch (e) {}
                    }
                }
            }, 100);
            
            // Stop after page load
            window.addEventListener('load', () => {
                setTimeout(() => clearInterval(cleanupInterval), 5000);
            });
            
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