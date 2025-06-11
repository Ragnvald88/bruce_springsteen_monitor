# stealthmaster/stealth/injections.py
"""Stealth JavaScript injections for anti-detection."""

import json
from typing import Dict, Any, List


class StealthInjections:
    """Manages all JavaScript injections for stealth."""
    
    def get_context_init_script(self) -> str:
        """Get initialization script for browser context."""
        return """
        // Context initialization
        (() => {
            'use strict';
            
            // Mark as stealth context
            window.__stealthmaster__ = true;
            
            // Override Object.prototype.toString to hide modifications
            const originalToString = Object.prototype.toString;
            Object.prototype.toString = function() {
                if (this === navigator) return '[object Navigator]';
                if (this === window.chrome) return '[object Object]';
                return originalToString.call(this);
            };
        })();
        """
    
    def get_webdriver_evasion(self) -> str:
        """Complete webdriver property removal."""
        return """
        // Webdriver evasion
        (() => {
            'use strict';
            
            // Pre-emptive webdriver removal
            const originalGet = Object.getOwnPropertyDescriptor;
            Object.getOwnPropertyDescriptor = function(obj, prop) {
                if (prop === 'webdriver' && obj === navigator) {
                    return undefined;
                }
                return originalGet.call(this, obj, prop);
            };
            
            // Delete webdriver from all possible locations
            delete Object.getPrototypeOf(navigator).webdriver;
            delete navigator.webdriver;
            delete navigator.__proto__.webdriver;
            
            // Create new navigator prototype without webdriver
            const newProto = Object.create(Object.getPrototypeOf(navigator));
            delete newProto.webdriver;
            Object.setPrototypeOf(navigator, newProto);
            
            // Define as undefined (can't be detected)
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                set: () => {},
                enumerable: false,
                configurable: false
            });
            
            // Also remove from window
            delete window.navigator.webdriver;
            
            // Remove CDP runtime artifacts
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        })();
        """
    
    def get_chrome_runtime_evasion(self) -> str:
        """Create convincing Chrome runtime object."""
        return """
        // Chrome runtime evasion
        (() => {
            'use strict';
            
            if (!window.chrome) {
                window.chrome = {};
            }
            
            // App
            window.chrome.app = {
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
            };
            
            // Runtime with all properties - ENHANCED FOR DETECTION BYPASS
            const mockRuntime = {
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
                // CRITICAL: These must exist but be undefined for normal web pages
                id: undefined,
                getManifest: undefined,
                getURL: undefined,
                // CRITICAL: These functions must throw errors like real Chrome on normal pages
                connect: function() {
                    throw new Error('Uncaught Error: Extension context invalidated.');
                },
                sendMessage: function() {
                    throw new Error('Uncaught Error: Extension context invalidated.');
                },
                // Additional properties for full compatibility
                lastError: undefined,
                onConnect: {
                    addListener: function() {},
                    removeListener: function() {},
                    hasListener: function() { return false; }
                },
                onMessage: {
                    addListener: function() {},
                    removeListener: function() {},
                    hasListener: function() { return false; }
                },
                onInstalled: {
                    addListener: function() {},
                    removeListener: function() {},
                    hasListener: function() { return false; }
                }
            };
            
            // Create proxy to handle property access like real Chrome
            window.chrome.runtime = new Proxy(mockRuntime, {
                get(target, prop) {
                    if (prop in target) {
                        return target[prop];
                    }
                    // Return undefined for unknown properties
                    return undefined;
                },
                has(target, prop) {
                    return prop in target;
                },
                ownKeys(target) {
                    return Object.keys(target);
                },
                getOwnPropertyDescriptor(target, prop) {
                    if (prop in target) {
                        return {
                            configurable: true,
                            enumerable: true,
                            value: target[prop]
                        };
                    }
                    return undefined;
                }
            });
            
            // LoadTimes
            const timing = performance.timing;
            const loadTimes = {
                get requestTime() { return timing.navigationStart / 1000; },
                get startLoadTime() { return timing.fetchStart / 1000; },
                get commitLoadTime() { return timing.responseStart / 1000; },
                get finishDocumentLoadTime() { return timing.domContentLoadedEventEnd / 1000; },
                get finishLoadTime() { return timing.loadEventEnd / 1000; },
                get firstPaintTime() { return (timing.responseStart + 100) / 1000; },
                get firstPaintAfterLoadTime() { return 0; },
                get navigationType() { return 'Other'; },
                get wasFetchedViaSpdy() { return true; },
                get wasNpnNegotiated() { return true; },
                get npnNegotiatedProtocol() { return 'h2'; },
                get wasAlternateProtocolAvailable() { return false; },
                get connectionInfo() { return 'h2'; }
            };
            
            window.chrome.loadTimes = function() { return loadTimes; };
            
            // CSI
            window.chrome.csi = function() {
                return {
                    onloadT: timing.loadEventEnd,
                    pageT: Date.now() - timing.navigationStart,
                    startE: timing.navigationStart,
                    tran: 15
                };
            };
        })();
        """
    
    def get_permission_evasion(self) -> str:
        """Override permission API to appear legitimate."""
        return """
        // Permission API evasion
        (() => {
            'use strict';
            
            if (!navigator.permissions) return;
            
            const originalQuery = navigator.permissions.query.bind(navigator.permissions);
            
            navigator.permissions.query = async function(descriptor) {
                // Common permissions that should be in specific states
                const permissionStates = {
                    'geolocation': 'granted',
                    'notifications': 'default',
                    'push': 'default',
                    'midi': 'default',
                    'camera': 'default',
                    'microphone': 'default',
                    'background-sync': 'granted',
                    'ambient-light-sensor': 'default',
                    'accelerometer': 'default',
                    'gyroscope': 'default',
                    'magnetometer': 'default',
                    'clipboard-read': 'default',
                    'clipboard-write': 'default'
                };
                
                const name = descriptor.name || descriptor;
                
                if (name in permissionStates) {
                    return {
                        name: name,
                        state: permissionStates[name],
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
                        state: 'default',
                        onchange: null
                    };
                }
            };
        })();
        """
    
    def get_plugin_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Create realistic plugin array."""
        plugins = fingerprint.get("plugins", [])
        plugins_json = json.dumps(plugins)
        
        return f"""
        // Plugin evasion
        (() => {{
            'use strict';
            
            const pluginsData = {plugins_json};
            
            // Create proper Plugin objects
            const plugins = pluginsData.map(data => {{
                const plugin = Object.create(Plugin.prototype);
                
                Object.defineProperties(plugin, {{
                    name: {{ value: data.name, enumerable: true }},
                    description: {{ value: data.description, enumerable: true }},
                    filename: {{ value: data.filename, enumerable: true }},
                    length: {{ value: data.mimeTypes.length, enumerable: true }}
                }});
                
                // Add mime types
                data.mimeTypes.forEach((mimeType, index) => {{
                    const mime = Object.create(MimeType.prototype);
                    Object.defineProperties(mime, {{
                        type: {{ value: mimeType, enumerable: true }},
                        suffixes: {{ value: 'pdf', enumerable: true }},
                        description: {{ value: data.description, enumerable: true }},
                        enabledPlugin: {{ value: plugin, enumerable: true }}
                    }});
                    
                    plugin[index] = mime;
                    plugin[mimeType] = mime;
                }});
                
                // Methods
                plugin.item = function(index) {{ return this[index] || null; }};
                plugin.namedItem = function(name) {{ return this[name] || null; }};
                
                return plugin;
            }});
            
            // Create PluginArray
            const pluginArray = Object.create(PluginArray.prototype);
            
            plugins.forEach((plugin, index) => {{
                pluginArray[index] = plugin;
                pluginArray[plugin.name] = plugin;
            }});
            
            Object.defineProperties(pluginArray, {{
                length: {{ value: plugins.length, enumerable: true }}
            }});
            
            pluginArray.item = function(index) {{ return this[index] || null; }};
            pluginArray.namedItem = function(name) {{ return this[name] || null; }};
            pluginArray.refresh = function() {{}};
            
            // Override navigator.plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => pluginArray,
                enumerable: true,
                configurable: false
            }});
            
            // Also set mimeTypes
            const mimeTypes = [];
            plugins.forEach(plugin => {{
                for (let i = 0; i < plugin.length; i++) {{
                    mimeTypes.push(plugin[i]);
                }}
            }});
            
            const mimeTypeArray = Object.create(MimeTypeArray.prototype);
            mimeTypes.forEach((mime, index) => {{
                mimeTypeArray[index] = mime;
                mimeTypeArray[mime.type] = mime;
            }});
            
            Object.defineProperty(mimeTypeArray, 'length', {{
                value: mimeTypes.length
            }});
            
            mimeTypeArray.item = function(index) {{ return this[index] || null; }};
            mimeTypeArray.namedItem = function(name) {{ return this[name] || null; }};
            
            Object.defineProperty(navigator, 'mimeTypes', {{
                get: () => mimeTypeArray,
                enumerable: true,
                configurable: false
            }});
        }})();
        """
    
    def get_webgl_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override WebGL parameters."""
        webgl = fingerprint.get("webgl", {})
        vendor = webgl.get("vendor", "Intel Inc.")
        renderer = webgl.get("renderer", "Intel Iris OpenGL Engine")
        
        return f"""
        // WebGL evasion
        (() => {{
            'use strict';
            
            const vendor = '{vendor}';
            const renderer = '{renderer}';
            
            // WebGL 1.0
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return vendor;   // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) return renderer; // UNMASKED_RENDERER_WEBGL
                if (parameter === 7937) return 'WebKit WebGL'; // VERSION
                if (parameter === 35724) return 'WebGL GLSL ES 1.0'; // SHADING_LANGUAGE_VERSION
                return getParameter.apply(this, arguments);
            }};
            
            // WebGL 2.0
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) return vendor;
                    if (parameter === 37446) return renderer;
                    if (parameter === 7937) return 'WebGL 2.0';
                    if (parameter === 35724) return 'WebGL GLSL ES 3.00';
                    return getParameter2.apply(this, arguments);
                }};
            }}
            
            // Also override getSupportedExtensions
            const getSupportedExtensions = WebGLRenderingContext.prototype.getSupportedExtensions;
            WebGLRenderingContext.prototype.getSupportedExtensions = function() {{
                const extensions = getSupportedExtensions.apply(this, arguments);
                // Add/remove some extensions for realism
                if (!extensions.includes('WEBGL_debug_renderer_info')) {{
                    extensions.push('WEBGL_debug_renderer_info');
                }}
                return extensions;
            }};
        }})();
        """
    
    def get_canvas_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Add noise to canvas fingerprinting."""
        canvas = fingerprint.get("canvas", {})
        noise_factor = canvas.get("noise_factor", 0.00001)
        
        return f"""
        // Canvas fingerprinting protection
        (() => {{
            'use strict';
            
            const noiseFactor = {noise_factor};
            
            // Helper to add noise
            const addNoise = (value) => {{
                const noise = (Math.random() - 0.5) * noiseFactor * 255;
                return Math.max(0, Math.min(255, value + noise));
            }};
            
            // Override toDataURL
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(...args) {{
                const context = this.getContext('2d');
                if (context && this.width > 0 && this.height > 0) {{
                    try {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = addNoise(imageData.data[i]);     // R
                            imageData.data[i+1] = addNoise(imageData.data[i+1]); // G
                            imageData.data[i+2] = addNoise(imageData.data[i+2]); // B
                            // Alpha channel unchanged
                        }}
                        context.putImageData(imageData, 0, 0);
                    }} catch (e) {{
                        // Ignore errors (cross-origin, etc)
                    }}
                }}
                return originalToDataURL.apply(this, args);
            }};
            
            // Override toBlob
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {{
                const context = this.getContext('2d');
                if (context && this.width > 0 && this.height > 0) {{
                    try {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {{
                            imageData.data[i] = addNoise(imageData.data[i]);
                            imageData.data[i+1] = addNoise(imageData.data[i+1]);
                            imageData.data[i+2] = addNoise(imageData.data[i+2]);
                        }}
                        context.putImageData(imageData, 0, 0);
                    }} catch (e) {{
                        // Ignore errors
                    }}
                }}
                return originalToBlob.call(this, callback, ...args);
            }};
            
            // Override getImageData
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
                const imageData = originalGetImageData.apply(this, args);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = addNoise(imageData.data[i]);
                    imageData.data[i+1] = addNoise(imageData.data[i+1]);
                    imageData.data[i+2] = addNoise(imageData.data[i+2]);
                }}
                return imageData;
            }};
        }})();
        """
    
    def get_audio_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Add noise to audio fingerprinting."""
        audio = fingerprint.get("audio", {})
        noise_factor = audio.get("noise_factor", 0.00001)
        
        return f"""
        // Audio fingerprinting protection
        (() => {{
            'use strict';
            
            const noiseFactor = {noise_factor};
            
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            
            // Override createOscillator
            const originalCreateOscillator = AudioContext.prototype.createOscillator;
            AudioContext.prototype.createOscillator = function() {{
                const oscillator = originalCreateOscillator.apply(this, arguments);
                const originalConnect = oscillator.connect;
                
                oscillator.connect = function(...args) {{
                    // Add slight frequency variation
                    if (oscillator.frequency && oscillator.frequency.value) {{
                        oscillator.frequency.value *= (1 + (Math.random() - 0.5) * noiseFactor);
                    }}
                    return originalConnect.apply(this, args);
                }};
                
                return oscillator;
            }};
            
            // Override createAnalyser
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            AudioContext.prototype.createAnalyser = function() {{
                const analyser = originalCreateAnalyser.apply(this, arguments);
                
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {{
                    originalGetFloatFrequencyData.apply(this, arguments);
                    for (let i = 0; i < array.length; i++) {{
                        array[i] += (Math.random() - 0.5) * noiseFactor;
                    }}
                }};
                
                const originalGetByteFrequencyData = analyser.getByteFrequencyData;
                analyser.getByteFrequencyData = function(array) {{
                    originalGetByteFrequencyData.apply(this, arguments);
                    for (let i = 0; i < array.length; i++) {{
                        array[i] = Math.max(0, Math.min(255, 
                            array[i] + (Math.random() - 0.5) * noiseFactor * 255));
                    }}
                }};
                
                return analyser;
            }};
        }})();
        """
    
    def get_navigator_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override navigator properties."""
        nav = fingerprint.get("navigator", {})
        
        return f"""
        // Navigator properties evasion
        (() => {{
            'use strict';
            
            const navProps = {json.dumps(nav)};
            
            // Apply each property
            for (const [prop, value] of Object.entries(navProps)) {{
                try {{
                    if (value !== null && value !== undefined) {{
                        Object.defineProperty(navigator, prop, {{
                            get: () => value,
                            enumerable: true,
                            configurable: false
                        }});
                    }}
                }} catch (e) {{
                    // Some properties might be read-only
                }}
            }}
            
            // Special handling for languages
            if (navProps.languages) {{
                Object.defineProperty(navigator, 'languages', {{
                    get: () => Object.freeze([...navProps.languages]),
                    enumerable: true,
                    configurable: false
                }});
            }}
        }})();
        """
    
    def get_screen_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override screen properties."""
        screen = fingerprint.get("screen", {})
        
        return f"""
        // Screen properties evasion
        (() => {{
            'use strict';
            
            const screenProps = {json.dumps(screen)};
            
            // Apply screen properties
            for (const [prop, value] of Object.entries(screenProps)) {{
                try {{
                    Object.defineProperty(screen, prop, {{
                        get: () => value,
                        enumerable: true,
                        configurable: false
                    }});
                }} catch (e) {{
                    // Some properties might be read-only
                }}
            }}
            
            // Also set window.screen
            for (const [prop, value] of Object.entries(screenProps)) {{
                try {{
                    Object.defineProperty(window.screen, prop, {{
                        get: () => value,
                        enumerable: true,
                        configurable: false
                    }});
                }} catch (e) {{
                    // Ignore
                }}
            }}
        }})();
        """
    
    def get_timezone_evasion(self, fingerprint: Dict[str, Any]) -> str:
        """Override timezone-related functions."""
        timezone = fingerprint.get("timezone", {})
        offset = timezone.get("offset", -60)  # Default to Rome (UTC+1)
        
        return f"""
        // Timezone evasion
        (() => {{
            'use strict';
            
            const timezoneOffset = {offset};
            
            // Override getTimezoneOffset
            Date.prototype.getTimezoneOffset = function() {{
                return timezoneOffset;
            }};
            
            // Override Intl.DateTimeFormat
            const OriginalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = new Proxy(OriginalDateTimeFormat, {{
                construct(target, args) {{
                    if (args.length > 1 && args[1] && !args[1].timeZone) {{
                        args[1].timeZone = 'Europe/Rome';
                    }}
                    return new target(...args);
                }}
            }});
            
            // Override resolvedOptions
            const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
            Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
                const options = originalResolvedOptions.apply(this, arguments);
                options.timeZone = 'Europe/Rome';
                return options;
            }};
        }})();
        """
    
    def get_console_evasion(self) -> str:
        """Protect against console-based detection."""
        return """
        // Console protection
        (() => {
            'use strict';
            
            // Store original console methods
            const originalConsole = {};
            ['log', 'debug', 'info', 'warn', 'error', 'trace'].forEach(method => {
                originalConsole[method] = console[method].bind(console);
            });
            
            // Track console calls for detection
            const consoleCallLog = [];
            const maxLogSize = 100;
            
            // Override console methods
            ['log', 'debug', 'info', 'warn', 'error'].forEach(method => {
                console[method] = new Proxy(originalConsole[method], {
                    apply(target, thisArg, args) {
                        // Log the call
                        consoleCallLog.push({
                            method: method,
                            timestamp: Date.now(),
                            stack: new Error().stack
                        });
                        
                        // Keep log size manageable
                        if (consoleCallLog.length > maxLogSize) {
                            consoleCallLog.shift();
                        }
                        
                        // Check for rapid successive calls (CDP detection)
                        if (consoleCallLog.length >= 3) {
                            const recent = consoleCallLog.slice(-3);
                            const timeDiffs = [
                                recent[1].timestamp - recent[0].timestamp,
                                recent[2].timestamp - recent[1].timestamp
                            ];
                            
                            // If calls are too rapid, it's likely detection
                            if (timeDiffs[0] < 5 && timeDiffs[1] < 5) {
                                return undefined;
                            }
                        }
                        
                        // Check stack for automation tools
                        const stack = new Error().stack || '';
                        const suspiciousPatterns = [
                            'puppeteer',
                            'playwright',
                            'selenium',
                            'webdriver',
                            'cdp',
                            'devtools'
                        ];
                        
                        if (suspiciousPatterns.some(pattern => 
                            stack.toLowerCase().includes(pattern))) {
                            return undefined;
                        }
                        
                        // Normal console usage
                        return target.apply(console, args);
                    }
                });
            });
            
            // Override toString to hide modifications
            console.log.toString = () => 'function log() { [native code] }';
            console.debug.toString = () => 'function debug() { [native code] }';
            console.info.toString = () => 'function info() { [native code] }';
            console.warn.toString = () => 'function warn() { [native code] }';
            console.error.toString = () => 'function error() { [native code] }';
        })();
        """
    
    def get_error_evasion(self) -> str:
        """Clean error stack traces of automation signatures."""
        return """
        // Error stack trace cleaning
        (() => {
            'use strict';
            
            const OriginalError = Error;
            
            // Patterns to remove from stack traces
            const cleanPatterns = [
                /\\bplaywright\\b/gi,
                /\\bpuppeteer\\b/gi,
                /\\bselenium\\b/gi,
                /\\bwebdriver\\b/gi,
                /\\b__playwright\\b/gi,
                /\\b__puppeteer\\b/gi,
                /\\bcdp_session\\b/gi,
                /\\bHeadlessChrome\\b/gi,
                /\\bautomation\\b/gi
            ];
            
            // Override Error constructor
            Error = new Proxy(OriginalError, {
                construct(target, args) {
                    const error = new target(...args);
                    
                    // Clean the stack trace
                    if (error.stack) {
                        let cleanStack = error.stack;
                        cleanPatterns.forEach(pattern => {
                            cleanStack = cleanStack.replace(pattern, '');
                        });
                        
                        // Fix any broken lines
                        cleanStack = cleanStack
                            .split('\\n')
                            .filter(line => line.trim())
                            .join('\\n');
                        
                        error.stack = cleanStack;
                    }
                    
                    return error;
                }
            });
            
            // Copy static properties
            Object.setPrototypeOf(Error, OriginalError);
            Error.captureStackTrace = OriginalError.captureStackTrace;
            Error.stackTraceLimit = OriginalError.stackTraceLimit;
        })();
        """