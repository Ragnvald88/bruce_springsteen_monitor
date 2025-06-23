"""
Advanced stealth improvements for StealthMaster
Implements cutting-edge anti-detection measures
"""

import random
import time
import numpy as np
from typing import Tuple, List
import json


class StealthEnhancements:
    """Advanced stealth techniques to avoid detection"""
    
    @staticmethod
    def get_enhanced_chrome_options():
        """Get comprehensive Chrome options for maximum stealth"""
        return [
            # Core stealth arguments
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--disable-browser-side-navigation',
            '--disable-gpu-sandbox',
            '--disable-features=IsolateOrigins,site-per-process',
            
            # Advanced stealth
            '--disable-web-security',
            '--allow-running-insecure-content',
            '--disable-features=TranslateUI',
            '--disable-features=BlinkGenPropertyTrees',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-features=IsolateOrigins',
            '--disable-features=site-per-process',
            
            # Performance and behavior
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--password-store=basic',
            '--use-mock-keychain',
            
            # Fingerprinting protection
            '--force-color-profile=srgb',
            '--disable-features=UserAgentClientHint',
            '--disable-features=WebRtcHideLocalIpsWithMdns',
            
            # Additional flags
            '--flag-switches-begin',
            '--flag-switches-end',
            '--disable-site-isolation-trials',
            '--metrics-recording-only',
            '--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints',
            
            # Memory and resource management
            '--max_old_space_size=4096',
            '--memory-pressure-off',
            '--disable-features=RendererCodeIntegrity',
            '--disable-features=FlashDeprecationWarning',
        ]
    
    @staticmethod
    def get_stealth_javascript():
        """JavaScript to inject for comprehensive stealth"""
        return """
        // Comprehensive navigator spoofing
        const fakeNavigator = {
            webdriver: undefined,
            plugins: [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', length: 1},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', length: 1},
                {name: 'Native Client', filename: 'internal-nacl-plugin', length: 2},
                {name: 'Chromium PDF Plugin', filename: 'internal-pdf-viewer', length: 1},
                {name: 'Microsoft Edge PDF Plugin', filename: 'internal-pdf-viewer', length: 1}
            ],
            languages: ['it-IT', 'it', 'en-US', 'en'],
            language: 'it-IT',
            platform: 'Win32',
            hardwareConcurrency: 8,
            deviceMemory: 8,
            userAgent: navigator.userAgent.replace('HeadlessChrome', 'Chrome'),
            appVersion: navigator.appVersion.replace('HeadlessChrome', 'Chrome'),
            vendor: 'Google Inc.',
            vendorSub: '',
            productSub: '20030107',
            maxTouchPoints: 0,
            scheduling: {},
            userActivation: {},
            doNotTrack: null,
            geolocation: {},
            connection: {
                downlink: 10,
                effectiveType: '4g',
                rtt: 50,
                saveData: false
            },
            keyboard: {},
            locks: {},
            mediaCapabilities: {},
            mediaSession: {},
            permissions: {},
            presentation: {},
            usb: {},
            xr: {},
            serial: {},
            bluetooth: {},
            clipboard: {},
            credentials: {},
            managed: {},
            mediaDevices: {},
            storage: {},
            serviceWorker: {},
            virtualKeyboard: {},
            wakeLock: {},
            ink: {},
            hid: {},
            gpu: {}
        };
        
        // Apply navigator overrides
        for (let key in fakeNavigator) {
            try {
                if (fakeNavigator[key] !== undefined) {
                    Object.defineProperty(navigator, key, {
                        get: () => fakeNavigator[key],
                        configurable: true
                    });
                }
            } catch (e) {}
        }
        
        // Canvas fingerprinting protection with noise
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function() {
            const context = originalGetContext.apply(this, arguments);
            if (context && context.fillText) {
                const originalFillText = context.fillText;
                context.fillText = function() {
                    // Add imperceptible noise to canvas
                    if (arguments[0] && Math.random() < 0.01) {
                        context.fillStyle = 'rgba(0,0,0,0.01)';
                        context.fillRect(
                            Math.random() * this.canvas.width,
                            Math.random() * this.canvas.height,
                            1, 1
                        );
                    }
                    return originalFillText.apply(this, arguments);
                };
            }
            return context;
        };
        
        // WebGL spoofing
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // Spoof common WebGL parameters
            const spoofParams = {
                37445: 'Intel Inc.',  // VENDOR
                37446: 'Intel Iris OpenGL Engine',  // RENDERER
                7936: 'WebGL 1.0 (OpenGL ES 2.0 Chromium)',  // VERSION
                7937: 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)',  // SHADING_LANGUAGE_VERSION
                3379: 16384,  // MAX_TEXTURE_SIZE
                34076: 16384,  // MAX_CUBE_MAP_TEXTURE_SIZE
                34024: 16384,  // MAX_RENDERBUFFER_SIZE
                34930: 16,  // MAX_TEXTURE_IMAGE_UNITS
                35660: 16,  // MAX_VERTEX_TEXTURE_IMAGE_UNITS
                36349: 1024,  // MAX_VERTEX_UNIFORM_VECTORS
                36348: 1024,  // MAX_FRAGMENT_UNIFORM_VECTORS
                36347: 8,  // MAX_VERTEX_ATTRIBS
                35661: 8,  // MAX_COMBINED_TEXTURE_IMAGE_UNITS
                35658: 8,  // MAX_VARYING_VECTORS
                7938: ['ANGLE (Intel Inc., Intel Iris OpenGL Engine, OpenGL 4.1)'],  // EXTENSIONS
            };
            
            if (spoofParams[parameter]) {
                return spoofParams[parameter];
            }
            return getParameter.apply(this, [parameter]);
        };
        
        // WebGL2 support
        if (typeof WebGL2RenderingContext !== 'undefined') {
            WebGL2RenderingContext.prototype.getParameter = WebGLRenderingContext.prototype.getParameter;
        }
        
        // Chrome object enhancement
        if (!window.chrome) {
            window.chrome = {};
        }
        
        window.chrome = {
            ...window.chrome,
            runtime: {
                PlatformOs: {
                    MAC: 'mac',
                    WIN: 'win',
                    ANDROID: 'android',
                    CROS: 'cros',
                    LINUX: 'linux',
                    OPENBSD: 'openbsd'
                },
                PlatformArch: {
                    ARM: 'arm',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64',
                    MIPS: 'mips',
                    MIPS64: 'mips64'
                },
                PlatformNaclArch: {
                    ARM: 'arm',
                    X86_32: 'x86-32',
                    X86_64: 'x86-64',
                    MIPS: 'mips',
                    MIPS64: 'mips64'
                },
                connect: function() {},
                sendMessage: function() {},
                onMessage: {
                    addListener: function() {}
                },
                id: 'nkbihfbeogaeaoehlefnkodbefgpgknn'
            },
            loadTimes: function() {
                return {
                    requestTime: Date.now() / 1000 - Math.random() * 100,
                    startLoadTime: Date.now() / 1000 - Math.random() * 50,
                    commitLoadTime: Date.now() / 1000 - Math.random() * 30,
                    finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 10,
                    finishLoadTime: Date.now() / 1000 - Math.random() * 5,
                    firstPaintTime: Date.now() / 1000 - Math.random() * 3,
                    firstPaintAfterLoadTime: Date.now() / 1000 - Math.random() * 2,
                    navigationType: 'Other',
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: true,
                    npnNegotiatedProtocol: 'h2',
                    wasAlternateProtocolAvailable: false,
                    connectionInfo: 'h2'
                };
            },
            csi: function() {
                return {
                    onloadT: Date.now() - Math.random() * 1000,
                    pageT: Date.now() - Math.random() * 5000,
                    startE: Date.now() - Math.random() * 5000,
                    tran: 15
                };
            },
            app: {
                isInstalled: false,
                getDetails: function() { return null; },
                getIsInstalled: function() { return false; },
                runningState: function() { return 'running'; }
            }
        };
        
        // Permissions API override
        const originalQuery = window.navigator.permissions.query;
        navigator.permissions.query = (parameters) => {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: 'granted' });
            }
            if (parameters.name === 'clipboard-read' || parameters.name === 'clipboard-write') {
                return Promise.resolve({ state: 'granted' });
            }
            if (parameters.name === 'camera' || parameters.name === 'microphone') {
                return Promise.resolve({ state: 'prompt' });
            }
            return originalQuery(parameters);
        };
        
        // Battery API spoofing
        if ('getBattery' in navigator) {
            navigator.getBattery = async () => ({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 0.92 + Math.random() * 0.08,
                onchargingchange: null,
                onchargingtimechange: null,
                ondischargingtimechange: null,
                onlevelchange: null
            });
        }
        
        // Screen properties
        Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
        Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
        Object.defineProperty(screen, 'width', { get: () => 1920 });
        Object.defineProperty(screen, 'height', { get: () => 1080 });
        Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
        Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
        Object.defineProperty(screen, 'availLeft', { get: () => 0 });
        Object.defineProperty(screen, 'availTop', { get: () => 0 });
        Object.defineProperty(screen, 'orientation', {
            get: () => ({
                angle: 0,
                type: 'landscape-primary',
                onchange: null
            })
        });
        
        // Timezone spoofing for Italy
        const originalDateTimeFormat = Intl.DateTimeFormat;
        Intl.DateTimeFormat = function(...args) {
            if (args.length === 0 || !args[0]) {
                args[0] = 'it-IT';
            }
            return originalDateTimeFormat.apply(this, args);
        };
        Intl.DateTimeFormat.prototype = originalDateTimeFormat.prototype;
        
        // Console protection
        const originalConsole = window.console;
        const consoleProxy = new Proxy(originalConsole, {
            get(target, prop) {
                if (prop === 'debug') {
                    return () => {};
                }
                return target[prop];
            }
        });
        window.console = consoleProxy;
        
        // Remove automation indicators from DOM
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {  // Element node
                        // Remove webdriver attributes
                        if (node.hasAttribute && node.hasAttribute('webdriver')) {
                            node.removeAttribute('webdriver');
                        }
                        // Remove automation attributes
                        const attrs = node.attributes;
                        if (attrs) {
                            for (let i = attrs.length - 1; i >= 0; i--) {
                                if (attrs[i].name.includes('automation') || 
                                    attrs[i].name.includes('webdriver') ||
                                    attrs[i].name.includes('selenium')) {
                                    node.removeAttribute(attrs[i].name);
                                }
                            }
                        }
                    }
                });
            });
        });
        
        observer.observe(document, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['webdriver']
        });
        
        // Function existence checks that bots look for
        delete window.callPhantom;
        delete window._phantom;
        delete window.__nightmare;
        delete window._selenium;
        delete window.__webdriver_script_fn;
        delete window.__driver_evaluate;
        delete window.__webdriver_evaluate;
        delete window.__selenium_evaluate;
        delete window.__fxdriver_evaluate;
        delete window.__driver_unwrapped;
        delete window.__webdriver_unwrapped;
        delete window.__selenium_unwrapped;
        delete window.__fxdriver_unwrapped;
        delete window.__webdriver_script_func;
        delete window.__webdriver_script_function;
        delete window.$cdc_asdjflasutopfhvcZLmcfl_;
        delete window.$chrome_asyncScriptInfo;
        delete window.__$webdriverAsyncExecutor;
        
        // Prevent detection of CDP
        const originalError = Error;
        Error = new Proxy(originalError, {
            construct(target, args) {
                const err = new target(...args);
                if (err.stack) {
                    err.stack = err.stack
                        .split('\n')
                        .filter(line => !line.includes('devtools'))
                        .join('\n');
                }
                return err;
            }
        });
        Error.prototype = originalError.prototype;
        
        // Done
        console.log('%c✅ Stealth mode activated', 'color: green; font-weight: bold');
        """
    
    @staticmethod
    def human_like_delay(min_ms: int = 50, max_ms: int = 150) -> float:
        """Generate human-like delay in seconds"""
        # Use beta distribution for more realistic delays
        alpha, beta = 2, 5  # Skewed towards faster typing
        normalized = np.random.beta(alpha, beta)
        delay_ms = min_ms + (max_ms - min_ms) * normalized
        return delay_ms / 1000
    
    @staticmethod
    def generate_mouse_path(start: Tuple[int, int], end: Tuple[int, int], 
                          num_points: int = 50) -> List[Tuple[int, int]]:
        """Generate human-like mouse movement path"""
        points = []
        
        # Add start point
        points.append(start)
        
        # Generate control points for bezier curve
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # Add randomness to control points
        ctrl1_x = mid_x + random.randint(-100, 100)
        ctrl1_y = mid_y + random.randint(-100, 100)
        ctrl2_x = mid_x + random.randint(-100, 100)
        ctrl2_y = mid_y + random.randint(-100, 100)
        
        # Generate bezier curve points
        for i in range(1, num_points - 1):
            t = i / (num_points - 1)
            
            # Cubic bezier formula
            x = ((1-t)**3 * start[0] + 
                 3*(1-t)**2*t * ctrl1_x + 
                 3*(1-t)*t**2 * ctrl2_x + 
                 t**3 * end[0])
            
            y = ((1-t)**3 * start[1] + 
                 3*(1-t)**2*t * ctrl1_y + 
                 3*(1-t)*t**2 * ctrl2_y + 
                 t**3 * end[1])
            
            # Add small random jitter
            x += random.gauss(0, 2)
            y += random.gauss(0, 2)
            
            points.append((int(x), int(y)))
        
        # Add end point
        points.append(end)
        
        return points
    
    @staticmethod
    def human_like_typing(element, text: str, driver):
        """Type text with human-like speed and patterns"""
        for i, char in enumerate(text):
            element.send_keys(char)
            
            # Variable typing speed
            if char == ' ':
                delay = random.gauss(0.15, 0.05)  # Spaces are faster
            elif char in '.,!?;:':
                delay = random.gauss(0.3, 0.1)  # Punctuation causes pause
            else:
                delay = random.gauss(0.1, 0.04)  # Normal characters
            
            # Ensure reasonable bounds
            delay = max(0.05, min(delay, 0.5))
            
            # Occasional longer pauses (thinking)
            if random.random() < 0.05:  # 5% chance
                delay += random.uniform(0.5, 1.5)
            
            # Typos and corrections (rare)
            if random.random() < 0.02 and i < len(text) - 1:  # 2% chance
                # Make a typo
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                
                # Delete the typo
                element.send_keys('\b')
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(delay)
    
    @staticmethod
    def random_mouse_movement(driver, duration: float = 1.0):
        """Perform random mouse movements to simulate human behavior"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Get current viewport dimensions
            viewport_width = driver.execute_script("return window.innerWidth")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # Random position within viewport
            x = random.randint(100, viewport_width - 100)
            y = random.randint(100, viewport_height - 100)
            
            # Move mouse
            driver.execute_script(f"""
                const event = new MouseEvent('mousemove', {{
                    clientX: {x},
                    clientY: {y},
                    bubbles: true,
                    cancelable: true,
                    view: window
                }});
                document.dispatchEvent(event);
            """)
            
            time.sleep(random.uniform(0.1, 0.3))
    
    @staticmethod
    def random_scrolling(driver, duration: float = 0.5):
        """Perform random scrolling to simulate human behavior"""
        current_scroll = driver.execute_script("return window.pageYOffset")
        max_scroll = driver.execute_script("return document.body.scrollHeight - window.innerHeight")
        
        # Small random scroll
        if max_scroll > 0:
            target_scroll = current_scroll + random.randint(-200, 200)
            target_scroll = max(0, min(target_scroll, max_scroll))
            
            # Smooth scroll
            driver.execute_script(f"""
                window.scrollTo({{
                    top: {target_scroll},
                    behavior: 'smooth'
                }});
            """)
            time.sleep(duration)
    
    @staticmethod
    def get_random_user_agent():
        """Get a random realistic user agent"""
        user_agents = [
            # Windows Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Mac Chrome
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Windows Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            
            # Linux Chrome
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        
        return random.choice(user_agents)
    
    @staticmethod
    def test_detection(driver) -> dict:
        """Test various detection methods"""
        tests = {
            'webdriver': "return navigator.webdriver",
            'chrome': "return window.chrome && window.chrome.runtime",
            'permissions': "return navigator.permissions && navigator.permissions.query",
            'plugins_length': "return navigator.plugins.length",
            'languages': "return navigator.languages.join(',')",
            'platform': "return navigator.platform",
            'vendor': "return navigator.vendor",
            'user_agent': "return navigator.userAgent",
            'webgl_vendor': """
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl');
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    return gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                } catch(e) { return 'error'; }
            """,
            'webgl_renderer': """
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl');
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                } catch(e) { return 'error'; }
            """,
            'canvas_fingerprint': """
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = 200;
                    canvas.height = 50;
                    const ctx = canvas.getContext('2d');
                    ctx.textBaseline = 'top';
                    ctx.font = '14px Arial';
                    ctx.fillStyle = '#f60';
                    ctx.fillRect(0, 0, 100, 50);
                    ctx.fillStyle = '#069';
                    ctx.fillText('Browser Fingerprint', 2, 2);
                    return canvas.toDataURL().substring(0, 50);
                } catch(e) { return 'error'; }
            """,
            'screen_resolution': "return screen.width + 'x' + screen.height",
            'timezone': "return Intl.DateTimeFormat().resolvedOptions().timeZone",
            'memory': "return navigator.deviceMemory || 'undefined'",
            'cpus': "return navigator.hardwareConcurrency || 'undefined'",
            'connection': "return navigator.connection ? navigator.connection.effectiveType : 'undefined'",
        }
        
        results = {}
        for test_name, script in tests.items():
            try:
                result = driver.execute_script(script)
                results[test_name] = result
            except Exception as e:
                results[test_name] = f"Error: {str(e)}"
        
        return results
    
    @staticmethod
    def analyze_detection_results(results: dict) -> dict:
        """Analyze detection test results"""
        issues = []
        score = 100
        
        # Check each result
        if results.get('webdriver') is True:
            issues.append("❌ navigator.webdriver is exposed")
            score -= 30
        
        if not results.get('chrome'):
            issues.append("⚠️ Chrome object missing or incomplete")
            score -= 10
        
        if results.get('plugins_length', 0) == 0:
            issues.append("⚠️ No plugins detected (suspicious)")
            score -= 15
        
        if 'HeadlessChrome' in results.get('user_agent', ''):
            issues.append("❌ HeadlessChrome in user agent")
            score -= 25
        
        if results.get('platform') not in ['Win32', 'MacIntel', 'Linux x86_64']:
            issues.append("⚠️ Unusual platform detected")
            score -= 10
        
        if results.get('vendor') != 'Google Inc.':
            issues.append("⚠️ Non-Google vendor")
            score -= 5
        
        if 'error' in str(results.get('webgl_vendor', '')):
            issues.append("⚠️ WebGL not properly configured")
            score -= 10
        
        return {
            'score': max(0, score),
            'issues': issues,
            'status': 'GOOD' if score >= 80 else 'WARNING' if score >= 60 else 'POOR'
        }