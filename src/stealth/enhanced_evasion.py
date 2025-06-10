# stealthmaster/stealth/enhanced_evasion.py
"""Enhanced bot detection evasion with realistic browser emulation."""

import json
import random
from typing import Dict, Any
from playwright.async_api import BrowserContext, Page


class EnhancedStealthEvasion:
    """Advanced stealth techniques for maximum evasion."""
    
    def __init__(self):
        """Initialize with realistic browser profiles."""
        self.profiles = [
            {
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "platform": "Win32",
                "vendor": "Google Inc.",
                "plugins": [
                    {"name": "PDF Viewer", "filename": "internal-pdf-viewer"},
                    {"name": "Chrome PDF Viewer", "filename": "internal-pdf-viewer"},
                    {"name": "Chromium PDF Viewer", "filename": "internal-pdf-viewer"},
                    {"name": "Microsoft Edge PDF Viewer", "filename": "internal-pdf-viewer"},
                    {"name": "WebKit built-in PDF", "filename": "internal-pdf-viewer"}
                ]
            },
            {
                "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "platform": "MacIntel",
                "vendor": "Google Inc.",
                "plugins": [
                    {"name": "PDF Viewer", "filename": "internal-pdf-viewer"},
                    {"name": "Chrome PDF Viewer", "filename": "internal-pdf-viewer"},
                    {"name": "Chromium PDF Viewer", "filename": "internal-pdf-viewer"}
                ]
            }
        ]
        
    async def apply_enhanced_stealth(self, context: BrowserContext) -> None:
        """Apply comprehensive stealth measures to browser context."""
        profile = random.choice(self.profiles)
        
        # Comprehensive stealth script
        stealth_script = f"""
        (() => {{
            // 1. Remove webdriver property completely
            const newProto = navigator.__proto__;
            delete newProto.webdriver;
            navigator.__proto__ = newProto;
            
            // 2. Mock realistic plugins with proper behavior
            const makePluginArray = () => {{
                const plugins = {json.dumps(profile['plugins'])};
                const arr = [];
                
                plugins.forEach((p, i) => {{
                    const plugin = {{
                        name: p.name,
                        filename: p.filename,
                        description: p.name,
                        version: null,
                        length: 1,
                        item: (index) => index === 0 ? plugin : null,
                        namedItem: (name) => null,
                        [Symbol.iterator]: function*() {{
                            yield plugin;
                        }}
                    }};
                    
                    arr.push(plugin);
                    arr[p.name] = plugin;
                }});
                
                arr.length = plugins.length;
                arr.item = (index) => arr[index] || null;
                arr.namedItem = (name) => arr[name] || null;
                arr.refresh = () => {{}};
                
                // Set proper prototype
                Object.setPrototypeOf(arr, PluginArray.prototype);
                
                return arr;
            }};
            
            Object.defineProperty(navigator, 'plugins', {{
                get: makePluginArray,
                configurable: true,
                enumerable: true
            }});
            
            // 3. Fix mimeTypes to match plugins
            const makeMimeTypeArray = () => {{
                const mimeTypes = [
                    {{
                        type: 'application/pdf',
                        suffixes: 'pdf',
                        description: 'Portable Document Format',
                        enabledPlugin: navigator.plugins[0]
                    }}
                ];
                
                const arr = [];
                mimeTypes.forEach(mt => {{
                    arr.push(mt);
                    arr[mt.type] = mt;
                }});
                
                arr.length = mimeTypes.length;
                arr.item = (index) => arr[index] || null;
                arr.namedItem = (name) => arr[name] || null;
                
                Object.setPrototypeOf(arr, MimeTypeArray.prototype);
                return arr;
            }};
            
            Object.defineProperty(navigator, 'mimeTypes', {{
                get: makeMimeTypeArray,
                configurable: true,
                enumerable: true
            }});
            
            // 4. Fix permissions API
            if (navigator.permissions) {{
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(parameters) {{
                    // Reject certain permission queries that bots commonly allow
                    if (parameters.name === 'notifications') {{
                        return Promise.reject(new DOMException('Permission denied'));
                    }}
                    return originalQuery.apply(this, arguments);
                }};
            }}
            
            // 5. Add chrome object for Chromium browsers
            if (!window.chrome) {{
                window.chrome = {{
                    runtime: {{
                        PlatformOs: {{
                            MAC: 'mac',
                            WIN: 'win',
                            LINUX: 'linux'
                        }},
                        PlatformArch: {{
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        }},
                        PlatformNaclArch: {{
                            ARM: 'arm',
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        }},
                        RequestUpdateCheckStatus: {{
                            THROTTLED: 'throttled',
                            NO_UPDATE: 'no_update',
                            UPDATE_AVAILABLE: 'update_available'
                        }},
                        OnInstalledReason: {{
                            INSTALL: 'install',
                            UPDATE: 'update',
                            CHROME_UPDATE: 'chrome_update',
                            SHARED_MODULE_UPDATE: 'shared_module_update'
                        }},
                        OnRestartRequiredReason: {{
                            APP_UPDATE: 'app_update',
                            OS_UPDATE: 'os_update',
                            PERIODIC: 'periodic'
                        }}
                    }},
                    loadTimes: function() {{
                        return {{
                            requestTime: Date.now() / 1000,
                            startLoadTime: Date.now() / 1000,
                            commitLoadTime: Date.now() / 1000,
                            finishDocumentLoadTime: Date.now() / 1000,
                            finishLoadTime: Date.now() / 1000,
                            firstPaintTime: Date.now() / 1000,
                            firstPaintAfterLoadTime: Date.now() / 1000,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: true,
                            wasNpnNegotiated: true,
                            npnNegotiatedProtocol: 'h2',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'h2'
                        }};
                    }},
                    csi: function() {{
                        return {{
                            onloadT: Date.now(),
                            pageT: Date.now() - 1000,
                            startE: Date.now() - 2000,
                            tran: 15
                        }};
                    }}
                }};
            }}
            
            // 6. Fix WebGL vendor string
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{profile["vendor"]}';
                }}
                if (parameter === 37446) {{
                    return 'ANGLE (Intel, Intel(R) Iris(TM) Graphics OpenGL Engine, OpenGL 4.1)';
                }}
                return getParameter.apply(this, arguments);
            }};
            
            const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
            WebGL2RenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{
                    return '{profile["vendor"]}';
                }}
                if (parameter === 37446) {{
                    return 'ANGLE (Intel, Intel(R) Iris(TM) Graphics OpenGL Engine, OpenGL 4.1)';
                }}
                return getParameter2.apply(this, arguments);
            }};
            
            // 7. Fix language and platform
            Object.defineProperty(navigator, 'language', {{
                get: () => 'en-US',
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'languages', {{
                get: () => ['en-US', 'en'],
                configurable: true
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{profile["platform"]}',
                configurable: true
            }});
            
            // 8. Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // 9. Fix navigator.vendor
            Object.defineProperty(navigator, 'vendor', {{
                get: () => '{profile["vendor"]}',
                configurable: true
            }});
            
            // 10. Add realistic window properties
            window.screenY = 74;
            window.screenTop = 74;
            window.outerHeight = 1050;
            window.outerWidth = 1920;
            
            // 11. Override headless detection
            Object.defineProperty(navigator, 'userAgent', {{
                get: () => '{profile["ua"]}',
                configurable: true
            }});
            
            // 12. Fix hardwareConcurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => 8,
                configurable: true
            }});
            
            // 13. Add realistic media devices
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {{
                navigator.mediaDevices.enumerateDevices = async () => [
                    {{
                        deviceId: "default",
                        kind: "audioinput",
                        label: "Default - MacBook Pro Microphone (Built-in)",
                        groupId: "default"
                    }},
                    {{
                        deviceId: "default",
                        kind: "audiooutput",
                        label: "Default - MacBook Pro Speakers (Built-in)",
                        groupId: "default"
                    }}
                ];
            }}
            
            // 14. Battery API
            if ('getBattery' in navigator) {{
                navigator.getBattery = async () => ({{
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.98,
                    addEventListener: () => {{}},
                    removeEventListener: () => {{}}
                }});
            }}
            
            // 15. Fix Notification API
            const originalNotification = window.Notification;
            window.Notification = new Proxy(originalNotification, {{
                construct(target, args) {{
                    const permission = Notification.permission;
                    if (permission === 'default') {{
                        throw new DOMException('User denied notification permission');
                    }}
                    return new target(...args);
                }}
            }});
            
            // 16. Console warning removal
            const originalConsole = console.log;
            console.log = function(...args) {{
                if (args[0] && args[0].includes && args[0].includes('HeadlessChrome')) {{
                    return;
                }}
                return originalConsole.apply(console, args);
            }};
        }})();
        """
        
        # Apply the stealth script
        await context.add_init_script(stealth_script)
        
        # Additional context-level settings
        await context.add_init_script("""
            // Override timezone fingerprinting
            Date.prototype.getTimezoneOffset = function() { return -60; };  // Europe/Rome
            Intl.DateTimeFormat.prototype.resolvedOptions = function() {
                return {
                    locale: 'it-IT',
                    calendar: 'gregory',
                    numberingSystem: 'latn',
                    timeZone: 'Europe/Rome',
                    year: 'numeric',
                    month: 'numeric',
                    day: 'numeric'
                };
            };
        """)
        
    async def apply_page_stealth(self, page: Page) -> None:
        """Apply page-level stealth measures."""
        # Override page visibility API
        await page.evaluate("""
            () => {
                Object.defineProperty(document, 'hidden', {
                    get: () => false,
                    configurable: true
                });
                
                Object.defineProperty(document, 'visibilityState', {
                    get: () => 'visible',
                    configurable: true
                });
                
                // Always report window as focused
                document.hasFocus = () => true;
                
                // Mock realistic mouse/keyboard capabilities
                window.onmousedown = () => {};
                window.onmouseup = () => {};
                window.onmousemove = () => {};
                window.onclick = () => {};
                window.onkeydown = () => {};
                window.onkeyup = () => {};
                window.onkeypress = () => {};
            }
        """)
        
    def get_optimal_launch_args(self) -> list:
        """Get optimal browser launch arguments."""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-features=TranslateUI',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-sync',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--no-first-run',
            '--password-store=basic',
            '--use-mock-keychain',
            '--export-tagged-pdf',
            '--no-default-browser-check',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-features=IsolateOrigins',
            '--disable-features=site-per-process',
            '--disable-gpu-sandbox',
            '--disable-logging',
            '--disable-permissions-api',
            '--disable-plugins-discovery',
            '--disable-renderer-accessibility',
            '--disable-renderer-backgrounding',
            '--disable-speech-api',
            '--disable-voice-input',
            '--no-pings',
            '--no-zygote',
            '--use-gl=swiftshader',
            '--window-size=1920,1080',
            '--window-position=0,0',
            '--force-device-scale-factor=1'
        ]