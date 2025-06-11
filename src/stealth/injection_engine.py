"""
Early-stage injection engine that runs before page initialization.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import Page, BrowserContext, CDPSession

logger = logging.getLogger(__name__)


class InjectionEngine:
    """
    Manages early-stage script injection to prevent detection.
    Injects scripts at the earliest possible moment.
    """
    
    def __init__(self):
        """Initialize injection engine"""
        self._injected_contexts: set = set()
        self._injection_scripts = self._load_injection_scripts()
        
    def _load_injection_scripts(self) -> Dict[str, str]:
        """Load all injection scripts"""
        return {
            'webdriver': self._get_webdriver_script(),
            'chrome': self._get_chrome_script(),
            'permissions': self._get_permissions_script(),
            'webgl': self._get_webgl_script(),
            'plugins': self._get_plugins_script(),
            'languages': self._get_languages_script(),
            'cdp': self._get_cdp_script(),
        }
    
    async def inject_context(self, context: BrowserContext):
        """
        Inject scripts into browser context
        
        Args:
            context: Browser context to inject into
        """
        context_id = id(context)
        if context_id in self._injected_contexts:
            return
        
        # Inject via CDP for earliest execution
        cdp = await context.new_cdp_session(await context.new_page())
        
        try:
            # Inject all scripts
            for name, script in self._injection_scripts.items():
                await self._inject_cdp_script(cdp, script, name)
            
            # Mark as injected
            self._injected_contexts.add(context_id)
            logger.info("Context injection completed")
            
        finally:
            await cdp.detach()
    
    async def inject_page(self, page: Page):
        """
        Inject scripts into specific page
        
        Args:
            page: Page to inject into
        """
        # Use evaluateOnNewDocument for earliest injection
        for name, script in self._injection_scripts.items():
            await page.evaluate_on_new_document(script)
    
    async def _inject_cdp_script(self, cdp: CDPSession, script: str, name: str):
        """Inject script via CDP"""
        try:
            # Use Page domain for injection
            await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
                "source": script,
                "worldName": "__playwright_utility_world__",
                "includeCommandLineAPI": False
            })
            
            # Also inject into main world
            await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
                "source": script,
                "includeCommandLineAPI": False
            })
            
            logger.debug(f"Injected {name} script via CDP")
            
        except Exception as e:
            logger.error(f"Failed to inject {name} script: {e}")
    
    def _get_webdriver_script(self) -> str:
        """Get webdriver hiding script"""
        return """
        (() => {
            'use strict';
            
            // Stage 1: Prevent webdriver from being defined
            const originalDefineProperty = Object.defineProperty;
            const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
            
            // Create a clean navigator if needed
            if (!window.navigator) {
                window.navigator = {};
            }
            
            // Intercept all property definitions
            Object.defineProperty = function(obj, prop, descriptor) {
                if ((obj === navigator || obj === Navigator.prototype) && prop === 'webdriver') {
                    // Silently ignore webdriver definition
                    return obj;
                }
                return originalDefineProperty.call(this, obj, prop, descriptor);
            };
            
            // Clean existing webdriver
            try {
                delete navigator.webdriver;
                delete Navigator.prototype.webdriver;
            } catch (e) {}
            
            // Stage 2: Proxy navigator to hide webdriver
            const navigatorProxy = new Proxy(navigator, {
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
                    const keys = Object.getOwnPropertyNames(target);
                    return keys.filter(key => key !== 'webdriver');
                },
                getOwnPropertyDescriptor(target, prop) {
                    if (prop === 'webdriver') {
                        return undefined;
                    }
                    return originalGetOwnPropertyDescriptor(target, prop);
                }
            });
            
            // Replace navigator with proxy
            try {
                originalDefineProperty(window, 'navigator', {
                    get: () => navigatorProxy,
                    set: () => {},
                    configurable: false,
                    enumerable: true
                });
            } catch (e) {}
            
            // Stage 3: Clean up CDP artifacts continuously
            const cleanupCDP = () => {
                const windowProps = Object.getOwnPropertyNames(window);
                const cdpProps = windowProps.filter(prop => 
                    prop.includes('$cdc') || 
                    prop.includes('cdc_') ||
                    prop.includes('$chrome_asyncScriptInfo')
                );
                
                cdpProps.forEach(prop => {
                    try {
                        delete window[prop];
                        originalDefineProperty(window, prop, {
                            get: () => undefined,
                            set: () => {},
                            configurable: false
                        });
                    } catch (e) {}
                });
            };
            
            // Initial cleanup
            cleanupCDP();
            
            // Periodic cleanup
            setInterval(cleanupCDP, 500);
            
            // Clean on various events
            ['load', 'DOMContentLoaded'].forEach(event => {
                window.addEventListener(event, cleanupCDP);
            });
        })();
        """
    
    def _get_chrome_script(self) -> str:
        """Get chrome object script"""
        return """
        (() => {
            'use strict';
            
            // Create proper chrome object
            const makeChrome = () => {
                const chrome = {
                    app: {
                        isInstalled: false,
                        InstallState: {
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        },
                        RunningState: {
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        },
                        getDetails: () => null,
                        getIsInstalled: () => false,
                        runningState: () => 'cannot_run'
                    },
                    runtime: new Proxy({}, {
                        get(target, prop) {
                            const props = {
                                OnInstalledReason: {
                                    CHROME_UPDATE: 'chrome_update',
                                    INSTALL: 'install',
                                    SHARED_MODULE_UPDATE: 'shared_module_update',
                                    UPDATE: 'update'
                                },
                                OnRestartRequiredReason: {
                                    APP_UPDATE: 'app_update',
                                    OS_UPDATE: 'os_update',
                                    PERIODIC: 'periodic'
                                },
                                PlatformArch: {
                                    ARM: 'arm',
                                    ARM64: 'arm64',
                                    MIPS: 'mips',
                                    MIPS64: 'mips64',
                                    X86_32: 'x86-32',
                                    X86_64: 'x86-64'
                                },
                                PlatformNaclArch: {
                                    ARM: 'arm',
                                    MIPS: 'mips',
                                    MIPS64: 'mips64',
                                    X86_32: 'x86-32',
                                    X86_64: 'x86-64'
                                },
                                PlatformOs: {
                                    ANDROID: 'android',
                                    CROS: 'cros',
                                    LINUX: 'linux',
                                    MAC: 'mac',
                                    OPENBSD: 'openbsd',
                                    WIN: 'win'
                                },
                                RequestUpdateCheckStatus: {
                                    NO_UPDATE: 'no_update',
                                    THROTTLED: 'throttled',
                                    UPDATE_AVAILABLE: 'update_available'
                                },
                                id: undefined,
                                getManifest: undefined,
                                getURL: undefined,
                                lastError: undefined,
                                onConnect: {
                                    addListener: () => {},
                                    removeListener: () => {},
                                    hasListener: () => false
                                },
                                onMessage: {
                                    addListener: () => {},
                                    removeListener: () => {},
                                    hasListener: () => false
                                }
                            };
                            
                            if (prop in props) {
                                return props[prop];
                            }
                            
                            // Functions that should throw errors
                            if (prop === 'connect' || prop === 'sendMessage') {
                                return () => {
                                    throw new Error('Extension context invalidated.');
                                };
                            }
                            
                            return undefined;
                        },
                        has(target, prop) {
                            const validProps = [
                                'OnInstalledReason', 'OnRestartRequiredReason',
                                'PlatformArch', 'PlatformNaclArch', 'PlatformOs',
                                'RequestUpdateCheckStatus', 'id', 'getManifest',
                                'getURL', 'connect', 'sendMessage', 'lastError',
                                'onConnect', 'onMessage'
                            ];
                            return validProps.includes(prop);
                        }
                    }),
                    loadTimes: function() {
                        const timing = performance.timing;
                        return {
                            requestTime: timing.navigationStart / 1000,
                            startLoadTime: timing.fetchStart / 1000,
                            commitLoadTime: timing.responseStart / 1000,
                            finishDocumentLoadTime: timing.domContentLoadedEventEnd / 1000,
                            finishLoadTime: timing.loadEventEnd / 1000,
                            firstPaintTime: (timing.responseStart + 100) / 1000,
                            firstPaintAfterLoadTime: 0,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: true,
                            wasNpnNegotiated: true,
                            npnNegotiatedProtocol: 'h2',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'h2'
                        };
                    },
                    csi: function() {
                        return {
                            onloadT: performance.timing.loadEventEnd,
                            pageT: Date.now() - performance.timing.navigationStart,
                            startE: performance.timing.navigationStart,
                            tran: 15
                        };
                    }
                };
                
                // Add storage API
                chrome.storage = {
                    local: {
                        get: (keys, callback) => callback({}),
                        set: (items, callback) => callback && callback(),
                        remove: (keys, callback) => callback && callback(),
                        clear: (callback) => callback && callback()
                    },
                    sync: {
                        get: (keys, callback) => callback({}),
                        set: (items, callback) => callback && callback(),
                        remove: (keys, callback) => callback && callback(),
                        clear: (callback) => callback && callback()
                    }
                };
                
                return chrome;
            };
            
            // Install chrome object
            if (!window.chrome || !window.chrome.runtime) {
                Object.defineProperty(window, 'chrome', {
                    get: () => makeChrome(),
                    set: () => {},
                    configurable: false,
                    enumerable: true
                });
            }
        })();
        """
    
    def _get_permissions_script(self) -> str:
        """Get permissions API script"""
        return """
        (() => {
            'use strict';
            
            if (!navigator.permissions) return;
            
            const originalQuery = navigator.permissions.query.bind(navigator.permissions);
            
            navigator.permissions.query = async function(descriptor) {
                const name = descriptor.name || descriptor;
                
                // Simulate realistic permission states
                const states = {
                    'geolocation': 'prompt',
                    'notifications': 'default',
                    'push': 'prompt',
                    'midi': 'prompt',
                    'camera': 'prompt',
                    'microphone': 'prompt',
                    'speaker': 'prompt',
                    'device-info': 'prompt',
                    'background-sync': 'prompt',
                    'bluetooth': 'prompt',
                    'persistent-storage': 'prompt',
                    'ambient-light-sensor': 'denied',
                    'accelerometer': 'denied',
                    'gyroscope': 'denied',
                    'magnetometer': 'denied',
                    'clipboard': 'prompt',
                    'clipboard-read': 'prompt',
                    'clipboard-write': 'prompt',
                    'payment-handler': 'prompt'
                };
                
                if (name in states) {
                    return {
                        name: name,
                        state: states[name],
                        onchange: null,
                        addEventListener: () => {},
                        removeEventListener: () => {},
                        dispatchEvent: () => true
                    };
                }
                
                try {
                    return await originalQuery(descriptor);
                } catch (e) {
                    return {
                        name: name,
                        state: 'prompt',
                        onchange: null
                    };
                }
            };
        })();
        """
    
    def _get_webgl_script(self) -> str:
        """Get WebGL spoofing script"""
        return """
        (() => {
            'use strict';
            
            const getParameterProxyHandler = {
                apply(target, thisArg, args) {
                    const param = args[0];
                    const result = target.apply(thisArg, args);
                    
                    // Spoof vendor and renderer
                    if (param === 37445) { // UNMASKED_VENDOR_WEBGL
                        return 'Intel Inc.';
                    }
                    if (param === 37446) { // UNMASKED_RENDERER_WEBGL
                        return 'Intel Iris OpenGL Engine';
                    }
                    
                    return result;
                }
            };
            
            // WebGL 1
            if (typeof WebGLRenderingContext !== 'undefined') {
                WebGLRenderingContext.prototype.getParameter = new Proxy(
                    WebGLRenderingContext.prototype.getParameter,
                    getParameterProxyHandler
                );
            }
            
            // WebGL 2
            if (typeof WebGL2RenderingContext !== 'undefined') {
                WebGL2RenderingContext.prototype.getParameter = new Proxy(
                    WebGL2RenderingContext.prototype.getParameter,
                    getParameterProxyHandler
                );
            }
        })();
        """
    
    def _get_plugins_script(self) -> str:
        """Get plugins spoofing script"""
        return """
        (() => {
            'use strict';
            
            // Create realistic plugins
            const pluginData = [
                {
                    name: 'Chrome PDF Plugin',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                    mimeTypes: ['application/x-google-chrome-pdf']
                },
                {
                    name: 'Chrome PDF Viewer',
                    filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                    description: 'Portable Document Format',
                    mimeTypes: ['application/pdf']
                },
                {
                    name: 'Native Client',
                    filename: 'internal-nacl-plugin',
                    description: 'Native Client Executable',
                    mimeTypes: ['application/x-nacl', 'application/x-pnacl']
                }
            ];
            
            const mimeTypes = [];
            const plugins = [];
            
            pluginData.forEach((data, index) => {
                const plugin = Object.create(Plugin.prototype, {
                    name: { value: data.name, enumerable: true },
                    filename: { value: data.filename, enumerable: true },
                    description: { value: data.description, enumerable: true },
                    length: { value: data.mimeTypes.length, enumerable: true }
                });
                
                data.mimeTypes.forEach((mimeType, i) => {
                    const mime = Object.create(MimeType.prototype, {
                        type: { value: mimeType, enumerable: true },
                        suffixes: { value: 'pdf', enumerable: true },
                        description: { value: data.description, enumerable: true },
                        enabledPlugin: { value: plugin, enumerable: true }
                    });
                    
                    Object.defineProperty(plugin, i, {
                        value: mime,
                        enumerable: true,
                        configurable: true
                    });
                    
                    Object.defineProperty(plugin, mimeType, {
                        value: mime,
                        enumerable: false,
                        configurable: true
                    });
                    
                    mimeTypes.push(mime);
                });
                
                // Methods
                plugin.item = function(index) {
                    return this[index] || null;
                };
                
                plugin.namedItem = function(name) {
                    return this[name] || null;
                };
                
                plugins.push(plugin);
            });
            
            // Create PluginArray
            const pluginArray = Object.create(PluginArray.prototype, {
                length: { value: plugins.length, enumerable: true }
            });
            
            plugins.forEach((plugin, i) => {
                Object.defineProperty(pluginArray, i, {
                    value: plugin,
                    enumerable: true,
                    configurable: true
                });
                
                Object.defineProperty(pluginArray, plugin.name, {
                    value: plugin,
                    enumerable: false,
                    configurable: true
                });
            });
            
            pluginArray.item = function(index) {
                return this[index] || null;
            };
            
            pluginArray.namedItem = function(name) {
                return this[name] || null;
            };
            
            pluginArray.refresh = function() {};
            
            // Create MimeTypeArray
            const mimeTypeArray = Object.create(MimeTypeArray.prototype, {
                length: { value: mimeTypes.length, enumerable: true }
            });
            
            mimeTypes.forEach((mime, i) => {
                Object.defineProperty(mimeTypeArray, i, {
                    value: mime,
                    enumerable: true,
                    configurable: true
                });
                
                Object.defineProperty(mimeTypeArray, mime.type, {
                    value: mime,
                    enumerable: false,
                    configurable: true
                });
            });
            
            mimeTypeArray.item = function(index) {
                return this[index] || null;
            };
            
            mimeTypeArray.namedItem = function(name) {
                return this[name] || null;
            };
            
            // Override navigator properties
            Object.defineProperty(navigator, 'plugins', {
                get: () => pluginArray,
                enumerable: true,
                configurable: true
            });
            
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => mimeTypeArray,
                enumerable: true,
                configurable: true
            });
        })();
        """
    
    def _get_languages_script(self) -> str:
        """Get languages spoofing script"""
        return """
        (() => {
            'use strict';
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                enumerable: true,
                configurable: true
            });
            
            Object.defineProperty(navigator, 'language', {
                get: () => 'en-US',
                enumerable: true,
                configurable: true
            });
        })();
        """
    
    def _get_cdp_script(self) -> str:
        """Get CDP detection bypass script"""
        return """
        (() => {
            'use strict';
            
            // Override Error stack getter to prevent CDP detection
            const originalError = Error;
            const originalCaptureStackTrace = Error.captureStackTrace;
            
            // Create custom Error that doesn't expose CDP
            window.Error = new Proxy(originalError, {
                construct(target, args) {
                    const error = new target(...args);
                    
                    // Override stack getter
                    Object.defineProperty(error, 'stack', {
                        get() {
                            const stack = error._stack || '';
                            // Remove CDP references from stack
                            return stack.replace(/.*__playwright.*\\n/g, '')
                                       .replace(/.*protocol.*\\n/g, '');
                        },
                        set(value) {
                            error._stack = value;
                        }
                    });
                    
                    return error;
                }
            });
            
            // Maintain static methods
            Object.setPrototypeOf(window.Error, originalError);
            window.Error.captureStackTrace = originalCaptureStackTrace;
            
            // Override console methods to prevent CDP leak
            const originalConsole = window.console;
            const consoleHandler = {
                get(target, prop) {
                    const original = target[prop];
                    if (typeof original === 'function') {
                        return function(...args) {
                            // Filter out CDP objects
                            const filtered = args.filter(arg => {
                                if (arg && typeof arg === 'object') {
                                    const str = JSON.stringify(arg);
                                    return !str.includes('__playwright') && 
                                           !str.includes('protocol');
                                }
                                return true;
                            });
                            return original.apply(target, filtered);
                        };
                    }
                    return original;
                }
            };
            
            window.console = new Proxy(originalConsole, consoleHandler);
        })();
        """