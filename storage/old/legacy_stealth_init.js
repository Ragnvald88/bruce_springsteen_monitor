// src/core/stealth_init.js (Ultimate Version 9.0 - 2025 Enhanced)
// Advanced anti-detection script incorporating the latest evasion techniques
// Based on Version 7+ with significant improvements for modern bot detection

(() => {
  'use strict';
  
  const STEALTH_VERSION = "9.0.2025";
  const DEBUG_MODE = false; // Set to true for development
  
  // ====== CONFIGURATION ======
  const config = {
    patches: {
      webdriver: true,
      chrome: true,
      permissions: true,
      webgl: true,
      canvas: true,
      audio: true,
      webrtc: true,
      battery: true,
      plugins: true,
      languages: true,
      fonts: true,
      scheduling: true,
      css: true,
      math: true,
      errors: true,
      console: true
    },
    performance: {
      useWeakMaps: true,
      asyncPatches: true,
      lazyLoading: true
    }
  };
  
  // ====== LOGGING SYSTEM ======
  const Logger = {
    _startTime: Date.now(),
    _logs: [],
    
    _format: (level, ...args) => {
      const timestamp = new Date().toISOString();
      const uptime = Date.now() - Logger._startTime;
      return [`🛡️ [${timestamp}] [${uptime}ms] ${level}:`, ...args];
    },
    
    debug: (...args) => {
      if (DEBUG_MODE) {
        console.info(...Logger._format('DEBUG', ...args));
        Logger._logs.push({ level: 'debug', args, time: Date.now() });
      }
    },
    
    info: (...args) => {
      if (DEBUG_MODE) {
        console.info(...Logger._format('INFO', ...args));
        Logger._logs.push({ level: 'info', args, time: Date.now() });
      }
    },
    
    warn: (...args) => {
      if (DEBUG_MODE) {
        console.warn(...Logger._format('WARN', ...args));
      }
      Logger._logs.push({ level: 'warn', args, time: Date.now() });
    },
    
    error: (...args) => {
      console.error(...Logger._format('ERROR', ...args));
      Logger._logs.push({ level: 'error', args, time: Date.now() });
    },
    
    success: (...args) => {
      if (DEBUG_MODE) {
        console.info(...Logger._format('✅', ...args));
      }
      Logger._logs.push({ level: 'success', args, time: Date.now() });
    }
  };
  
  // ====== PROFILE VALIDATION ======
  if (!window.__fingerprint_profile__ || !window.__fingerprint_profile__.name) {
    Logger.error('FATAL: No fingerprint profile found. Emergency patches only.');
    try {
      Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
    } catch (e) {}
    return;
  }
  
  const profile = window.__fingerprint_profile__;
  Logger.info(`Initializing stealth v${STEALTH_VERSION} for profile: ${profile.name}`);
  
  // ====== UTILITIES ======
  const utils = {
    // Cryptographically secure random
    random: () => crypto.getRandomValues(new Uint32Array(1))[0] / (0xffffffff + 1),
    
    randomBetween: (min, max) => Math.floor(utils.random() * (max - min + 1)) + min,
    
    // Gaussian distribution for more realistic randomness
    gaussianRandom: (mean = 0, stdev = 1) => {
      const u = 1 - utils.random();
      const v = utils.random();
      const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
      return z * stdev + mean;
    },
    
    // Enhanced property definition with multiple strategies
    defineProp: (obj, prop, descriptor) => {
      const strategies = [
        // Strategy 1: Direct definition
        () => Object.defineProperty(obj, prop, { ...descriptor, configurable: true }),
        
        // Strategy 2: Delete and redefine
        () => {
          delete obj[prop];
          Object.defineProperty(obj, prop, { ...descriptor, configurable: true });
        },
        
        // Strategy 3: Prototype manipulation
        () => {
          const proto = Object.getPrototypeOf(obj);
          if (proto && proto !== Object.prototype) {
            Object.defineProperty(proto, prop, { ...descriptor, configurable: true });
          } else {
            throw new Error('Proto strategy failed');
          }
        },
        
        // Strategy 4: Direct assignment (for value descriptors)
        () => {
          if ('value' in descriptor) {
            obj[prop] = descriptor.value;
          } else {
            throw new Error('Not a value descriptor');
          }
        }
      ];
      
      for (const strategy of strategies) {
        try {
          strategy();
          return true;
        } catch (e) {
          continue;
        }
      }
      
      Logger.warn(`Failed to define property '${String(prop)}' on`, obj);
      return false;
    },
    
    // Deep property getter with validation
    getDeepProp: (obj, path, defaultValue = undefined) => {
      if (!obj || typeof path !== 'string') return defaultValue;
      
      try {
        const result = path.split('.').reduce((current, key) => {
          if (current && typeof current === 'object' && key in current) {
            return current[key];
          }
          throw new Error('Path not found');
        }, obj);
        
        return result === undefined ? defaultValue : result;
      } catch (e) {
        return defaultValue;
      }
    },
    
    // Create native-looking proxy
    createNativeProxy: (target, handler, nativeName = null) => {
      const proxy = new Proxy(target, {
        apply: handler,
        get(obj, prop) {
          if (prop === 'toString') {
            const name = nativeName || target.name || 'function';
            return () => `function ${name}() { [native code] }`;
          }
          if (prop === Symbol.toStringTag) return undefined;
          if (prop === Symbol.hasInstance) return undefined;
          if (prop === 'name') return nativeName || target.name;
          if (prop === 'length') return target.length;
          return Reflect.get(target, prop);
        },
        getPrototypeOf: () => target.constructor.prototype,
        setPrototypeOf: () => false,
        isExtensible: () => false,
        preventExtensions: () => true,
        getOwnPropertyDescriptor: (obj, prop) => {
          const desc = Object.getOwnPropertyDescriptor(target, prop);
          if (desc && !['arguments', 'caller', 'callee'].includes(prop)) {
            return desc;
          }
          return undefined;
        },
        defineProperty: () => false,
        has: (obj, prop) => prop in target,
        deleteProperty: () => false,
        ownKeys: () => Reflect.ownKeys(target).filter(key => 
          !['arguments', 'caller', 'callee'].includes(key)
        )
      });
      
      return proxy;
    },
    
    // Time operations
    timeOperations: {
      startTime: performance.now(),
      
      getUptime: () => performance.now() - utils.timeOperations.startTime,
      
      addJitter: (value, maxJitter = 0.1) => {
        const jitter = utils.gaussianRandom(0, value * maxJitter);
        return Math.max(0, value + jitter);
      },
      
      humanDelay: () => utils.randomBetween(50, 150),
      
      microDelay: () => utils.randomBetween(0.1, 0.5)
    }
  };
  
  // ====== PATCH TRACKING ======
  const patchTracker = {
    patched: new WeakSet(),
    originals: new WeakMap(),
    
    markPatched: (obj, original = null) => {
      patchTracker.patched.add(obj);
      if (original) {
        patchTracker.originals.set(obj, original);
      }
    },
    
    isPatched: (obj) => patchTracker.patched.has(obj),
    
    getOriginal: (obj) => patchTracker.originals.get(obj)
  };
  
  // ====== MODULES ======
  
  // Module: Core WebDriver and Automation
  const CoreModule = {
    apply: () => {
      // 1. navigator.webdriver
      utils.defineProp(Navigator.prototype, 'webdriver', {
        get: () => false,
        set: () => false,
        enumerable: false
      });
      Logger.debug('Patched navigator.webdriver');
      
      // 2. Remove automation properties
      const automationProps = [
        // WebDriver
        '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate',
        '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped',
        '__selenium_unwrapped', '__fxdriver_unwrapped', '__webdriver_script_fn',
        '__webdriver_script_func', '__webdriver_script_function',
        // Selenium
        '_Selenium_IDE_Recorder', '_selenium', 'callSelenium', '_WEBDRIVER_ELEM_CACHE',
        'selenium', 'webdriver', 'driver', '$cdc_asdjflasutopfhvcZLmcfl_',
        '$chrome_asyncScriptInfo', '$wdc_', '_$webdriverAsyncExecutor',
        // Puppeteer/Playwright
        '__puppeteer_evaluation_script__', '__playwright_evaluation_script__',
        '__puppeteer__', '__playwright__',
        // PhantomJS
        '_phantom', 'phantom', '__phantomas', 'callPhantom',
        // Nightmare
        '__nightmare', 'nightmare',
        // Other
        'domAutomation', 'domAutomationController', 'awesomium',
        '_Firebug', '_FirebugCommandLine', 'Debug', 'debuggerEnabled'
      ];
      
      const cleanObject = (obj) => {
        automationProps.forEach(prop => {
          try {
            if (prop in obj) {
              delete obj[prop];
            }
          } catch (e) {}
        });
      };
      
      cleanObject(window);
      cleanObject(navigator);
      cleanObject(document);
      
      // Clean document attributes
      if (document.documentElement) {
        const attrs = [...document.documentElement.attributes];
        attrs.forEach(attr => {
          if (automationProps.includes(attr.name) || 
              attr.name.includes('driver') ||
              attr.name.includes('selenium') ||
              attr.name.startsWith('$cdc_') ||
              attr.name.startsWith('__')) {
            document.documentElement.removeAttribute(attr.name);
          }
        });
      }
      
      Logger.debug('Removed automation properties');
      
      // 3. Function.prototype.toString protection
      const origToString = Function.prototype.toString;
      const nativeToStringStr = origToString.call(origToString);
      
      utils.defineProp(Function.prototype, 'toString', {
        value: function(...args) {
          // Self check
          if (this === Function.prototype.toString) {
            return nativeToStringStr;
          }
          
          // Check if patched
          if (patchTracker.isPatched(this)) {
            const original = patchTracker.getOriginal(this);
            if (original) {
              return origToString.call(original);
            }
            const name = this.name || '';
            return `function ${name}() { [native code] }`;
          }
          
          // Check for native proxy
          if (this.__isNativeProxy__) {
            const name = this.__nativeName__ || this.name || '';
            return `function ${name}() { [native code] }`;
          }
          
          return origToString.apply(this, args);
        }
      });
      
      patchTracker.markPatched(Function.prototype.toString, origToString);
      Logger.debug('Protected Function.prototype.toString');
    }
  };
  
  // Module: Chrome/Edge Specific
  const ChromeModule = {
    isApplicable: () => {
      const ua = (profile.user_agent || '').toLowerCase();
      return ua.includes('chrome/') || ua.includes('edg/');
    },
    
    apply: () => {
      if (!ChromeModule.isApplicable()) return;
      
      if (!window.chrome) {
        window.chrome = {};
      }
      
      const chromeData = utils.getDeepProp(profile, 'extra_js_props.chrome_object', {});
      const runtimeId = chromeData.runtime_id || 
                       Array.from(crypto.getRandomValues(new Uint8Array(16)))
                         .map(b => b.toString(16).padStart(2, '0'))
                         .join('');
      
      // LoadTimes
      utils.defineProp(window.chrome, 'loadTimes', {
        value: () => {
          const base = performance.timing.navigationStart / 1000;
          const now = Date.now() / 1000;
          return {
            requestTime: base,
            startLoadTime: base + 0.001,
            commitLoadTime: base + 0.005,
            finishDocumentLoadTime: base + utils.randomBetween(100, 300) / 1000,
            finishLoadTime: base + utils.randomBetween(300, 800) / 1000,
            firstPaintTime: base + utils.randomBetween(50, 150) / 1000,
            firstPaintAfterLoadTime: 0,
            navigationType: 'Other',
            wasFetchedViaSpdy: true,
            wasNpnNegotiated: true,
            npnNegotiatedProtocol: 'h2',
            wasAlternateProtocolAvailable: false,
            connectionInfo: 'h2'
          };
        }
      });
      
      // CSI
      utils.defineProp(window.chrome, 'csi', {
        value: () => ({
          onloadT: utils.timeOperations.getUptime() + utils.randomBetween(100, 300),
          pageT: Date.now() - performance.timing.navigationStart,
          startE: performance.timing.navigationStart,
          tran: 15
        })
      });
      
      // Runtime
      window.chrome.runtime = window.chrome.runtime || {
        id: runtimeId,
        getManifest: () => {
          throw new Error('getManifest is not available in this context');
        },
        getURL: (path) => {
          throw new Error('getURL is not available in this context');
        },
        sendMessage: () => {
          throw new Error('Extension context invalidated.');
        },
        connect: () => {
          throw new Error('Extension context invalidated.');
        },
        onMessage: {
          addListener: () => {},
          removeListener: () => {},
          hasListener: () => false
        },
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
          ARM64: 'arm64',
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
        RequestUpdateCheckStatus: {
          THROTTLED: 'throttled',
          NO_UPDATE: 'no_update',
          UPDATE_AVAILABLE: 'update_available'
        },
        OnInstalledReason: {
          INSTALL: 'install',
          UPDATE: 'update',
          CHROME_UPDATE: 'chrome_update',
          SHARED_MODULE_UPDATE: 'shared_module_update'
        },
        OnRestartRequiredReason: {
          APP_UPDATE: 'app_update',
          OS_UPDATE: 'os_update',
          PERIODIC: 'periodic'
        }
      };
      
      // App
      window.chrome.app = window.chrome.app || {
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
        }
      };
      
      Logger.debug('Chrome/Edge specific patches applied');
    }
  };
  
  // Module: Navigator Properties
  const NavigatorModule = {
    apply: () => {
      const navProps = {
        // Basic properties
        appCodeName: 'Mozilla',
        appName: utils.getDeepProp(profile, 'extra_js_props.navigator_appName', 'Netscape'),
        appVersion: profile.user_agent?.substring(8) || '5.0 (Windows NT 10.0; Win64; x64)',
        platform: profile.js_platform || 'Win32',
        userAgent: profile.user_agent || navigator.userAgent,
        vendor: utils.getDeepProp(profile, 'extra_js_props.navigator_vendor', 'Google Inc.'),
        vendorSub: '',
        product: 'Gecko',
        productSub: '20030107',
        
        // Languages
        language: (profile.locale || 'en-US').split(',')[0].trim(),
        languages: utils.getDeepProp(profile, 'extra_js_props.navigator_languages_override', 
                                   ['en-US', 'en']),
        
        // Hardware
        hardwareConcurrency: profile.hardware_concurrency || 4,
        deviceMemory: profile.device_memory ? Math.min(profile.device_memory, 8) : undefined,
        maxTouchPoints: utils.getDeepProp(profile, 'extra_js_props.maxTouchPoints', 0),
        
        // Features
        cookieEnabled: true,
        onLine: true,
        doNotTrack: utils.getDeepProp(profile, 'extra_js_props.doNotTrack', null),
        
        // Media Capabilities
        mediaCapabilities: navigator.mediaCapabilities || {},
        
        // Permissions
        permissions: navigator.permissions || {},
        
        // PDF
        pdfViewerEnabled: utils.getDeepProp(profile, 'extra_js_props.pdfViewerEnabled', true),
        
        // Others
        buildID: utils.getDeepProp(profile, 'extra_js_props.navigator_buildID', undefined),
        oscpu: utils.getDeepProp(profile, 'extra_js_props.navigator_oscpu', undefined),
        
        // Connection
        connection: {
          effectiveType: utils.getDeepProp(profile, 'extra_js_props.connection.effectiveType', '4g'),
          rtt: utils.randomBetween(25, 100),
          downlink: utils.timeOperations.addJitter(
            utils.getDeepProp(profile, 'extra_js_props.connection.downlink', 10), 0.3
          ),
          saveData: false,
          type: 'unknown',
          downlinkMax: undefined,
          ontypechange: null,
          onchange: null
        },
        
        // User Activation
        userActivation: {
          hasBeenActive: true,
          isActive: true
        },
        
        // Storage
        storage: navigator.storage || {},
        
        // Service Worker
        serviceWorker: navigator.serviceWorker || undefined,
        
        // Geolocation
        geolocation: navigator.geolocation || {},
        
        // Media Devices
        mediaDevices: navigator.mediaDevices || {},
        
        // Presentation
        presentation: navigator.presentation || undefined,
        
        // USB
        usb: navigator.usb || undefined,
        
        // Bluetooth
        bluetooth: navigator.bluetooth || undefined,
        
        // Clipboard
        clipboard: navigator.clipboard || {}
      };
      
      // Apply properties
      Object.entries(navProps).forEach(([key, value]) => {
        if (value !== undefined) {
          utils.defineProp(Navigator.prototype, key, { 
            get: () => value,
            enumerable: true,
            configurable: true
          });
        }
      });
      
      Logger.debug('Navigator properties patched');
    }
  };
  
  // Module: Screen and Window
  const ScreenModule = {
    apply: () => {
      const screenProps = {
        width: profile.screen_width || 1920,
        height: profile.screen_height || 1080,
        availWidth: profile.avail_width || profile.screen_width || 1920,
        availHeight: profile.avail_height || 
                     (profile.screen_height || 1080) - 
                     utils.getDeepProp(profile, 'extra_js_props.screen_taskbar_height', 40),
        colorDepth: profile.color_depth || 24,
        pixelDepth: profile.pixel_depth || 24,
        availLeft: 0,
        availTop: 0,
        orientation: {
          angle: utils.getDeepProp(profile, 'extra_js_props.screen_orientation.angle', 0),
          type: utils.getDeepProp(profile, 'extra_js_props.screen_orientation.type', 'landscape-primary'),
          onchange: null
        },
        mozOrientation: utils.getDeepProp(profile, 'extra_js_props.screen_orientation.type', 'landscape-primary'),
        onmozorientationchange: null
      };
      
      // Apply screen properties
      Object.entries(screenProps).forEach(([key, value]) => {
        if (key === 'orientation' && screen.orientation) {
          Object.entries(value).forEach(([orientKey, orientValue]) => {
            utils.defineProp(screen.orientation, orientKey, { 
              get: () => orientValue,
              enumerable: true
            });
          });
        } else {
          utils.defineProp(Screen.prototype, key, { 
            get: () => value,
            enumerable: true
          });
        }
      });
      
      // Window properties
      const windowProps = {
        devicePixelRatio: profile.device_pixel_ratio || 1,
        innerWidth: profile.viewport_width || screenProps.width,
        innerHeight: profile.viewport_height || screenProps.availHeight,
        outerWidth: (profile.viewport_width || screenProps.width) + 
                    utils.getDeepProp(profile, 'extra_js_props.window_chrome_width', 0),
        outerHeight: (profile.viewport_height || screenProps.availHeight) + 
                     utils.getDeepProp(profile, 'extra_js_props.window_chrome_height', 0),
        screenX: utils.getDeepProp(profile, 'extra_js_props.window_screenX', 0),
        screenY: utils.getDeepProp(profile, 'extra_js_props.window_screenY', 0),
        screenLeft: utils.getDeepProp(profile, 'extra_js_props.window_screenX', 0),
        screenTop: utils.getDeepProp(profile, 'extra_js_props.window_screenY', 0),
        scrollX: 0,
        scrollY: 0,
        pageXOffset: 0,
        pageYOffset: 0
      };
      
      Object.entries(windowProps).forEach(([key, value]) => {
        utils.defineProp(window, key, { 
          get: () => value,
          enumerable: true
        });
      });
      
      Logger.debug('Screen and window properties patched');
    }
  };
  
  // Module: WebGL Protection
  const WebGLModule = {
    apply: () => {
      const webglVendor = profile.webgl_vendor;
      const webglRenderer = profile.webgl_renderer;
      
      if (!webglVendor || !webglRenderer) {
        Logger.warn('WebGL vendor/renderer not specified in profile');
        return;
      }
      
      const getContextOriginal = HTMLCanvasElement.prototype.getContext;
      
      HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
        const context = getContextOriginal.apply(this, [contextType, ...args]);
        
        if (context && ['webgl', 'webgl2', 'experimental-webgl'].includes(contextType)) {
          // Patch getParameter
          const getParameterOriginal = context.getParameter.bind(context);
          
          context.getParameter = function(param) {
            const debugInfo = this.getExtension('WEBGL_debug_renderer_info');
            
            if (debugInfo) {
              if (param === debugInfo.UNMASKED_VENDOR_WEBGL) return webglVendor;
              if (param === debugInfo.UNMASKED_RENDERER_WEBGL) return webglRenderer;
            }
            
            // Custom parameters
            const customParams = utils.getDeepProp(profile, 'extra_js_props.webgl_parameters', {});
            if (customParams[param]) return customParams[param];
            
            const result = getParameterOriginal(param);
            
            // Add subtle variations
            switch(param) {
              case 0x0D33: // MAX_TEXTURE_SIZE
              case 0x851C: // MAX_VERTEX_UNIFORM_COMPONENTS
              case 0x8B4A: // MAX_FRAGMENT_UNIFORM_COMPONENTS
                return Math.max(1, result + utils.randomBetween(-2, 2));
              
              case 0x8869: // MAX_VERTEX_ATTRIBS
              case 0x8DFB: // MAX_DRAW_BUFFERS
                return Math.max(1, result);
                
              default:
                return result;
            }
          };
          
          // Patch getSupportedExtensions
          const supportedExtensions = utils.getDeepProp(profile, 'extra_js_props.webgl_extensions', []);
          if (supportedExtensions.length > 0) {
            context.getSupportedExtensions = () => [...supportedExtensions];
          }
          
          // Patch getExtension
          const getExtensionOriginal = context.getExtension.bind(context);
          context.getExtension = function(name) {
            if (name === 'WEBGL_debug_renderer_info') {
              return {
                UNMASKED_VENDOR_WEBGL: 0x9245,
                UNMASKED_RENDERER_WEBGL: 0x9246
              };
            }
            
            if (supportedExtensions.length > 0 && !supportedExtensions.includes(name)) {
              return null;
            }
            
            return getExtensionOriginal(name);
          };
          
          // Patch getShaderPrecisionFormat
          const precisionOriginal = context.getShaderPrecisionFormat?.bind(context);
          if (precisionOriginal) {
            context.getShaderPrecisionFormat = function(shaderType, precisionType) {
              const result = precisionOriginal(shaderType, precisionType);
              if (result) {
                return {
                  rangeMin: result.rangeMin,
                  rangeMax: result.rangeMax,
                  precision: result.precision + utils.randomBetween(-1, 1)
                };
              }
              return result;
            };
          }
          
          patchTracker.markPatched(context.getParameter);
          patchTracker.markPatched(context.getSupportedExtensions);
          patchTracker.markPatched(context.getExtension);
        }
        
        return context;
      };
      
      patchTracker.markPatched(HTMLCanvasElement.prototype.getContext);
      Logger.debug('WebGL protection applied');
    }
  };
  
  // Module: Canvas Fingerprinting Protection
  const CanvasModule = {
    apply: () => {
      const canvasNoise = utils.getDeepProp(profile, 'extra_js_props.canvas_fp_noise', {
        enabled: true,
        intensity: 0.00005,
        rgbShift: 1
      });
      
      if (!canvasNoise.enabled) return;
      
      // Sophisticated noise function
      const applyNoise = (imageData) => {
        const data = imageData.data;
        const intensity = canvasNoise.intensity;
        const shift = canvasNoise.rgbShift;
        
        // Apply different noise patterns
        const noiseType = utils.randomBetween(0, 2);
        
        for (let i = 0; i < data.length; i += 4) {
          if (utils.random() < intensity) {
            switch(noiseType) {
              case 0: // Gaussian noise
                data[i] = Math.max(0, Math.min(255, 
                  data[i] + Math.round(utils.gaussianRandom(0, shift))));
                data[i + 1] = Math.max(0, Math.min(255, 
                  data[i + 1] + Math.round(utils.gaussianRandom(0, shift))));
                data[i + 2] = Math.max(0, Math.min(255, 
                  data[i + 2] + Math.round(utils.gaussianRandom(0, shift))));
                break;
                
              case 1: // Salt and pepper noise
                const val = utils.random() > 0.5 ? 255 : 0;
                const channel = utils.randomBetween(0, 2);
                data[i + channel] = val;
                break;
                
              case 2: // Uniform noise
                data[i] = Math.max(0, Math.min(255, 
                  data[i] + utils.randomBetween(-shift, shift)));
                data[i + 1] = Math.max(0, Math.min(255, 
                  data[i + 1] + utils.randomBetween(-shift, shift)));
                data[i + 2] = Math.max(0, Math.min(255, 
                  data[i + 2] + utils.randomBetween(-shift, shift)));
                break;
            }
          }
        }
        
        return imageData;
      };
      
      // Patch toDataURL
      const toDataURLOriginal = HTMLCanvasElement.prototype.toDataURL;
      HTMLCanvasElement.prototype.toDataURL = function(...args) {
        const ctx = this.getContext('2d');
        if (ctx) {
          try {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const noisyData = applyNoise(imageData);
            ctx.putImageData(noisyData, 0, 0);
          } catch (e) {}
        }
        return toDataURLOriginal.apply(this, args);
      };
      
      // Patch toBlob
      const toBlobOriginal = HTMLCanvasElement.prototype.toBlob;
      HTMLCanvasElement.prototype.toBlob = function(callback, ...args) {
        const ctx = this.getContext('2d');
        if (ctx) {
          try {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const noisyData = applyNoise(imageData);
            ctx.putImageData(noisyData, 0, 0);
          } catch (e) {}
        }
        return toBlobOriginal.call(this, callback, ...args);
      };
      
      // Patch getImageData
      const getImageDataOriginal = CanvasRenderingContext2D.prototype.getImageData;
      CanvasRenderingContext2D.prototype.getImageData = function(...args) {
        const imageData = getImageDataOriginal.apply(this, args);
        return applyNoise(imageData);
      };
      
      // Patch readPixels for WebGL contexts
      ['WebGLRenderingContext', 'WebGL2RenderingContext'].forEach(contextName => {
        if (window[contextName]) {
          const readPixelsOriginal = window[contextName].prototype.readPixels;
          window[contextName].prototype.readPixels = function(x, y, width, height, format, type, pixels) {
            readPixelsOriginal.call(this, x, y, width, height, format, type, pixels);
            
            // Apply noise to pixels array
            if (pixels && pixels.length) {
              for (let i = 0; i < pixels.length; i++) {
                if (utils.random() < canvasNoise.intensity) {
                  pixels[i] = Math.max(0, Math.min(255, 
                    pixels[i] + utils.randomBetween(-canvasNoise.rgbShift, canvasNoise.rgbShift)));
                }
              }
            }
          };
        }
      });
      
      patchTracker.markPatched(HTMLCanvasElement.prototype.toDataURL);
      patchTracker.markPatched(HTMLCanvasElement.prototype.toBlob);
      patchTracker.markPatched(CanvasRenderingContext2D.prototype.getImageData);
      
      Logger.debug('Canvas fingerprinting protection applied');
    }
  };
  
  // Module: WebRTC Protection
  const WebRTCModule = {
    apply: () => {
      if (!window.RTCPeerConnection) return;
      
      const webrtcConfig = utils.getDeepProp(profile, 'extra_js_props.webrtc', {
        preventLeak: true,
        fakeIPs: ['10.0.0.1', '192.168.1.1'],
        stunServers: []
      });
      
      // Override RTCPeerConnection
      const OriginalRTCPeerConnection = window.RTCPeerConnection;
      
      window.RTCPeerConnection = function(config, constraints) {
        if (config && config.iceServers && webrtcConfig.preventLeak) {
          // Remove or modify STUN/TURN servers
          config.iceServers = config.iceServers.filter(server => {
            const urls = Array.isArray(server.urls) ? server.urls : [server.urls];
            return !urls.some(url => url.includes('stun:'));
          });
        }
        
        const pc = new OriginalRTCPeerConnection(config, constraints);
        
        // Override createDataChannel to prevent leaks
        const createDataChannelOriginal = pc.createDataChannel.bind(pc);
        pc.createDataChannel = function(label, options) {
          if (webrtcConfig.preventLeak) {
            Logger.debug('WebRTC: createDataChannel intercepted');
          }
          return createDataChannelOriginal(label, options);
        };
        
        // Override getStats
        const getStatsOriginal = pc.getStats.bind(pc);
        pc.getStats = async function(selector) {
          const stats = await getStatsOriginal(selector);
          
          if (webrtcConfig.preventLeak) {
            // Modify stats to hide real IPs
            stats.forEach((report) => {
              if (report.type === 'candidate-pair' || report.type === 'local-candidate') {
                if (report.ip) {
                  report.ip = webrtcConfig.fakeIPs[0];
                }
                if (report.address) {
                  report.address = webrtcConfig.fakeIPs[0];
                }
              }
            });
          }
          
          return stats;
        };
        
        return pc;
      };
      
      // Copy static properties
      Object.setPrototypeOf(window.RTCPeerConnection, OriginalRTCPeerConnection);
      window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;
      
      // Override RTCIceCandidate
      const OriginalRTCIceCandidate = window.RTCIceCandidate;
      
      window.RTCIceCandidate = function(candidateInit) {
        if (candidateInit && candidateInit.candidate && webrtcConfig.preventLeak) {
          // Replace real IP with fake IP in candidate string
          const ipRegex = /(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/g;
          candidateInit.candidate = candidateInit.candidate.replace(ipRegex, (match) => {
            // Don't replace local IPs
            if (match.startsWith('192.168.') || match.startsWith('10.') || match.startsWith('172.')) {
              return match;
            }
            return webrtcConfig.fakeIPs[0];
          });
        }
        
        return new OriginalRTCIceCandidate(candidateInit);
      };
      
      Object.setPrototypeOf(window.RTCIceCandidate, OriginalRTCIceCandidate);
      window.RTCIceCandidate.prototype = OriginalRTCIceCandidate.prototype;
      
      // MediaDevices.getUserMedia override
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const getUserMediaOriginal = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
        
        navigator.mediaDevices.getUserMedia = async function(constraints) {
          Logger.debug('getUserMedia called with constraints:', constraints);
          
          // Add delay to simulate user permission dialog
          await new Promise(resolve => setTimeout(resolve, utils.randomBetween(500, 1500)));
          
          return getUserMediaOriginal(constraints);
        };
      }
      
      Logger.debug('WebRTC protection applied');
    }
  };
  
  // Module: AudioContext Protection
  const AudioModule = {
    apply: () => {
      const audioConfig = utils.getDeepProp(profile, 'extra_js_props.audio_context', {
        sampleRate: 44100,
        baseLatency: 0.01,
        outputLatency: 0.02,
        noiseIntensity: 0.00001
      });
      
      ['AudioContext', 'webkitAudioContext'].forEach(contextName => {
        if (!window[contextName]) return;
        
        const OriginalAudioContext = window[contextName];
        
        window[contextName] = function(...args) {
          const ctx = new OriginalAudioContext(...args);
          
          // Override properties
          if ('sampleRate' in ctx) {
            utils.defineProp(ctx, 'sampleRate', {
              get: () => audioConfig.sampleRate + utils.randomBetween(-50, 50)
            });
          }
          
          if ('baseLatency' in ctx) {
            utils.defineProp(ctx, 'baseLatency', {
              get: () => utils.timeOperations.addJitter(audioConfig.baseLatency, 0.1)
            });
          }
          
          if ('outputLatency' in ctx) {
            utils.defineProp(ctx, 'outputLatency', {
              get: () => utils.timeOperations.addJitter(audioConfig.outputLatency, 0.1)
            });
          }
          
          // Patch createAnalyser
          const createAnalyserOriginal = ctx.createAnalyser.bind(ctx);
          ctx.createAnalyser = function() {
            const analyser = createAnalyserOriginal();
            
            // Patch getFloatFrequencyData
            const getFloatFrequencyDataOriginal = analyser.getFloatFrequencyData.bind(analyser);
            analyser.getFloatFrequencyData = function(array) {
              getFloatFrequencyDataOriginal(array);
              
              // Add subtle noise
              for (let i = 0; i < array.length; i++) {
                if (utils.random() < 0.1) {
                  array[i] += utils.gaussianRandom(0, audioConfig.noiseIntensity);
                }
              }
            };
            
            // Patch getByteFrequencyData
            const getByteFrequencyDataOriginal = analyser.getByteFrequencyData.bind(analyser);
            analyser.getByteFrequencyData = function(array) {
              getByteFrequencyDataOriginal(array);
              
              for (let i = 0; i < array.length; i++) {
                if (utils.random() < 0.1) {
                  array[i] = Math.max(0, Math.min(255, 
                    array[i] + utils.randomBetween(-1, 1)));
                }
              }
            };
            
            return analyser;
          };
          
          // Patch createOscillator
          const createOscillatorOriginal = ctx.createOscillator.bind(ctx);
          ctx.createOscillator = function() {
            const oscillator = createOscillatorOriginal();
            
            // Add slight frequency variations
            const setFrequencyOriginal = Object.getOwnPropertyDescriptor(
              OscillatorNode.prototype, 'frequency'
            ).set;
            
            if (setFrequencyOriginal) {
              Object.defineProperty(oscillator, 'frequency', {
                set: function(value) {
                  setFrequencyOriginal.call(this, value * (1 + utils.gaussianRandom(0, 0.0001)));
                },
                get: function() {
                  return this.frequency;
                }
              });
            }
            
            return oscillator;
          };
          
          return ctx;
        };
        
        // Copy properties
        Object.setPrototypeOf(window[contextName], OriginalAudioContext);
        window[contextName].prototype = OriginalAudioContext.prototype;
      });
      
      Logger.debug('AudioContext protection applied');
    }
  };
  
  // Module: Font Fingerprinting Protection
  const FontModule = {
    apply: () => {
      const fontConfig = utils.getDeepProp(profile, 'extra_js_props.fonts', {
        enabled: true,
        noise: 0.1
      });
      
      if (!fontConfig.enabled) return;
      
      // Override measureText
      const measureTextOriginal = CanvasRenderingContext2D.prototype.measureText;
      CanvasRenderingContext2D.prototype.measureText = function(text) {
        const metrics = measureTextOriginal.call(this, text);
        
        // Add slight variations to measurements
        const noise = fontConfig.noise;
        
        return new Proxy(metrics, {
          get: (target, prop) => {
            if (prop === 'width') {
              return target.width * (1 + utils.gaussianRandom(0, noise / 100));
            }
            if (prop === 'actualBoundingBoxLeft') {
              return target.actualBoundingBoxLeft * (1 + utils.gaussianRandom(0, noise / 100));
            }
            if (prop === 'actualBoundingBoxRight') {
              return target.actualBoundingBoxRight * (1 + utils.gaussianRandom(0, noise / 100));
            }
            if (prop === 'fontBoundingBoxAscent') {
              return target.fontBoundingBoxAscent * (1 + utils.gaussianRandom(0, noise / 100));
            }
            if (prop === 'fontBoundingBoxDescent') {
              return target.fontBoundingBoxDescent * (1 + utils.gaussianRandom(0, noise / 100));
            }
            return target[prop];
          }
        });
      };
      
      // Override getBoundingClientRect for font measurements
      const getBoundingClientRectOriginal = Element.prototype.getBoundingClientRect;
      Element.prototype.getBoundingClientRect = function() {
        const rect = getBoundingClientRectOriginal.call(this);
        
        // Check if this is likely a font measurement
        if (this.tagName === 'SPAN' && this.style.fontFamily) {
          const noise = fontConfig.noise / 100;
          
          return new DOMRect(
            rect.x + utils.gaussianRandom(0, noise),
            rect.y + utils.gaussianRandom(0, noise),
            rect.width * (1 + utils.gaussianRandom(0, noise)),
            rect.height * (1 + utils.gaussianRandom(0, noise))
          );
        }
        
        return rect;
      };
      
      patchTracker.markPatched(CanvasRenderingContext2D.prototype.measureText);
      patchTracker.markPatched(Element.prototype.getBoundingClientRect);
      
      Logger.debug('Font fingerprinting protection applied');
    }
  };
  
  // Module: Scheduling API Protection
  const SchedulingModule = {
    apply: () => {
      // Create scheduling object if it doesn't exist
      if (!navigator.scheduling) {
        navigator.scheduling = {};
      }
      
      // Implement isInputPending
      navigator.scheduling.isInputPending = function(options = {}) {
        // Simulate realistic input pending behavior
        const now = performance.now();
        const lastInput = window.__lastInputTime__ || 0;
        const timeSinceLastInput = now - lastInput;
        
        // Higher probability of input pending if recent input
        const probability = Math.max(0, 1 - (timeSinceLastInput / 1000));
        
        if (utils.random() < probability * 0.1) {
          Logger.debug('isInputPending returning true');
          return true;
        }
        
        return false;
      };
      
      // Track input events for realistic behavior
      ['mousedown', 'mouseup', 'keydown', 'keyup', 'touchstart', 'touchend'].forEach(eventType => {
        window.addEventListener(eventType, () => {
          window.__lastInputTime__ = performance.now();
        }, { capture: true, passive: true });
      });
      
      // Implement isFramePending (if exists in the future)
      navigator.scheduling.isFramePending = function() {
        // Check if animation frame is pending
        const fps = 60;
        const frameTime = 1000 / fps;
        const now = performance.now();
        const lastFrame = window.__lastFrameTime__ || 0;
        
        return (now - lastFrame) >= frameTime;
      };
      
      // Track animation frames
      const rafOriginal = window.requestAnimationFrame;
      window.requestAnimationFrame = function(callback) {
        return rafOriginal.call(window, (time) => {
          window.__lastFrameTime__ = time;
          callback(time);
        });
      };
      
      Logger.debug('Scheduling API protection applied');
    }
  };
  
  // Module: Permissions API
  const PermissionsModule = {
    apply: () => {
      const permissions = utils.getDeepProp(profile, 'extra_js_props.permissions', {});
      
      if (!navigator.permissions || Object.keys(permissions).length === 0) return;
      
      const queryOriginal = navigator.permissions.query.bind(navigator.permissions);
      
      navigator.permissions.query = async function(descriptor) {
        const name = descriptor.name;
        
        if (permissions[name]) {
          // Simulate async delay
          await new Promise(resolve => 
            setTimeout(resolve, utils.randomBetween(10, 50))
          );
          
          return {
            name: name,
            state: permissions[name],
            onchange: null,
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => false
          };
        }
        
        return queryOriginal(descriptor);
      };
      
      patchTracker.markPatched(navigator.permissions.query);
      Logger.debug('Permissions API patched');
    }
  };
  
  // Module: Battery API
  const BatteryModule = {
    apply: () => {
      const batteryData = utils.getDeepProp(profile, 'extra_js_props.battery', {
        charging: true,
        chargingTime: 0,
        dischargingTime: Infinity,
        level: 1.0
      });
      
      navigator.getBattery = async function() {
        // Simulate async delay
        await new Promise(resolve => 
          setTimeout(resolve, utils.randomBetween(10, 30))
        );
        
        const battery = {
          charging: batteryData.charging,
          chargingTime: batteryData.chargingTime,
          dischargingTime: batteryData.dischargingTime,
          level: Math.min(1, Math.max(0, batteryData.level + utils.gaussianRandom(0, 0.01))),
          onchargingchange: null,
          onchargingtimechange: null,
          ondischargingtimechange: null,
          onlevelchange: null,
          addEventListener: () => {},
          removeEventListener: () => {},
          dispatchEvent: () => false
        };
        
        return battery;
      };
      
      Logger.debug('Battery API patched');
    }
  };
  
  // Module: Plugins and MimeTypes
  const PluginsModule = {
    apply: () => {
      const profilePlugins = utils.getDeepProp(profile, 'extra_js_props.plugins', []);
      
      const createPluginArray = () => {
        const plugins = profilePlugins.map(pluginData => {
          const plugin = {
            name: pluginData.name,
            description: pluginData.description,
            filename: pluginData.filename,
            length: (pluginData.mimeTypes || []).length
          };
          
          // Add methods
          plugin.item = function(index) { 
            return this[index]; 
          };
          
          plugin.namedItem = function(name) {
            for (let i = 0; i < this.length; i++) {
              if (this[i] && this[i].type === name) return this[i];
            }
            return null;
          };
          
          // Add mime types
          (pluginData.mimeTypes || []).forEach((mimeData, index) => {
            const mimeType = {
              type: mimeData.type,
              suffixes: mimeData.suffixes,
              description: mimeData.description,
              enabledPlugin: plugin
            };
            plugin[index] = mimeType;
          });
          
          // Make array-like
          Object.setPrototypeOf(plugin, Plugin.prototype);
          
          return plugin;
        });
        
        const pluginArray = {
          length: plugins.length
        };
        
        // Add methods
        pluginArray.item = function(index) { 
          return this[index]; 
        };
        
        pluginArray.namedItem = function(name) {
          for (let i = 0; i < this.length; i++) {
            if (this[i] && this[i].name === name) return this[i];
          }
          return null;
        };
        
        pluginArray.refresh = function() {};
        
        // Add plugins
        plugins.forEach((plugin, index) => {
          pluginArray[index] = plugin;
        });
        
        // Make array-like
        Object.setPrototypeOf(pluginArray, PluginArray.prototype);
        
        return pluginArray;
      };
      
      const createMimeTypeArray = () => {
        const mimeTypes = [];
        
        profilePlugins.forEach(pluginData => {
          (pluginData.mimeTypes || []).forEach(mimeData => {
            const plugin = navigator.plugins.namedItem(pluginData.name);
            mimeTypes.push({
              type: mimeData.type,
              suffixes: mimeData.suffixes,
              description: mimeData.description,
              enabledPlugin: plugin
            });
          });
        });
        
        const mimeTypeArray = {
          length: mimeTypes.length
        };
        
        // Add methods
        mimeTypeArray.item = function(index) { 
          return this[index]; 
        };
        
        mimeTypeArray.namedItem = function(name) {
          for (let i = 0; i < this.length; i++) {
            if (this[i] && this[i].type === name) return this[i];
          }
          return null;
        };
        
        // Add mime types
        mimeTypes.forEach((mimeType, index) => {
          mimeTypeArray[index] = mimeType;
        });
        
        // Make array-like
        Object.setPrototypeOf(mimeTypeArray, MimeTypeArray.prototype);
        
        return mimeTypeArray;
      };
      
      // Create arrays
      const pluginsArray = createPluginArray();
      const mimeTypesArray = createMimeTypeArray();
      
      // Apply
      utils.defineProp(Navigator.prototype, 'plugins', { 
        get: () => pluginsArray,
        enumerable: true
      });
      
      utils.defineProp(Navigator.prototype, 'mimeTypes', { 
        get: () => mimeTypesArray,
        enumerable: true
      });
      
      Logger.debug('Plugins and MimeTypes patched');
    }
  };
  
  // Module: MediaDevices
  const MediaDevicesModule = {
    apply: () => {
      const mediaDevices = utils.getDeepProp(profile, 'extra_js_props.media_devices', []);
      
      if (!navigator.mediaDevices || mediaDevices.length === 0) return;
      
      navigator.mediaDevices.enumerateDevices = async function() {
        // Simulate async delay
        await new Promise(resolve => 
          setTimeout(resolve, utils.randomBetween(20, 60))
        );
        
        return mediaDevices.map(device => ({
          deviceId: device.deviceId || utils.random().toString(36).substring(2),
          kind: device.kind,
          label: device.label,
          groupId: device.groupId || utils.random().toString(36).substring(2),
          toJSON: function() {
            return {
              deviceId: this.deviceId,
              kind: this.kind,
              label: this.label,
              groupId: this.groupId
            };
          }
        }));
      };
      
      patchTracker.markPatched(navigator.mediaDevices.enumerateDevices);
      Logger.debug('MediaDevices patched');
    }
  };
  
  // Module: Timezone and Intl
  const TimezoneModule = {
    apply: () => {
      const timezone = profile.timezone;
      const locale = (profile.locale || 'en-US').split(',')[0];
      
      if (!timezone) return;
      
      // Patch Intl.DateTimeFormat
      if (typeof Intl !== 'undefined' && Intl.DateTimeFormat) {
        const OriginalDateTimeFormat = Intl.DateTimeFormat;
        
        window.Intl.DateTimeFormat = function(...args) {
          const instance = new OriginalDateTimeFormat(...args);
          
          const resolvedOptionsOriginal = instance.resolvedOptions.bind(instance);
          instance.resolvedOptions = function() {
            const options = resolvedOptionsOriginal();
            options.timeZone = timezone;
            if (!args[0]) options.locale = locale;
            
            const calendar = utils.getDeepProp(profile, 'extra_js_props.intl_calendar');
            const numberingSystem = utils.getDeepProp(profile, 'extra_js_props.intl_numberingSystem');
            
            if (calendar) options.calendar = calendar;
            if (numberingSystem) options.numberingSystem = numberingSystem;
            
            return options;
          };
          
          return instance;
        };
        
        // Copy static methods and properties
        Object.setPrototypeOf(window.Intl.DateTimeFormat, OriginalDateTimeFormat);
        window.Intl.DateTimeFormat.prototype = OriginalDateTimeFormat.prototype;
        
        // Copy static methods
        ['supportedLocalesOf'].forEach(method => {
          if (OriginalDateTimeFormat[method]) {
            window.Intl.DateTimeFormat[method] = OriginalDateTimeFormat[method];
          }
        });
      }
      
      // Patch Date methods
      const toLocaleStringOriginal = Date.prototype.toLocaleString;
      Date.prototype.toLocaleString = function(locales, options) {
        return toLocaleStringOriginal.call(this, locales || locale, {
          ...options,
          timeZone: timezone
        });
      };
      
      const toLocaleDateStringOriginal = Date.prototype.toLocaleDateString;
      Date.prototype.toLocaleDateString = function(locales, options) {
        return toLocaleDateStringOriginal.call(this, locales || locale, {
          ...options,
          timeZone: timezone
        });
      };
      
      const toLocaleTimeStringOriginal = Date.prototype.toLocaleTimeString;
      Date.prototype.toLocaleTimeString = function(locales, options) {
        return toLocaleTimeStringOriginal.call(this, locales || locale, {
          ...options,
          timeZone: timezone
        });
      };
      
      Logger.debug('Timezone and Intl patched');
    }
  };
  
  // Module: Speech Synthesis
  const SpeechModule = {
    apply: () => {
      const speechVoices = utils.getDeepProp(profile, 'extra_js_props.speech_voices', []);
      
      if (!window.speechSynthesis || speechVoices.length === 0) return;
      
      const voices = speechVoices.map(v => ({
        voiceURI: v.voiceURI || v.name,
        name: v.name,
        lang: v.lang,
        localService: v.localService !== false,
        default: v.default || false
      }));
      
      window.speechSynthesis.getVoices = () => voices;
      
      // Trigger voiceschanged event
      setTimeout(() => {
        const event = new Event('voiceschanged');
        window.speechSynthesis.dispatchEvent(event);
      }, utils.randomBetween(100, 300));
      
      Logger.debug('Speech synthesis patched');
    }
  };
  
  // Module: Math Fingerprinting Protection
  const MathModule = {
    apply: () => {
      const mathConfig = utils.getDeepProp(profile, 'extra_js_props.math', {
        enabled: true,
        precision: 1e-10
      });
      
      if (!mathConfig.enabled) return;
      
      // List of Math functions that can vary slightly between implementations
      const functionsToPath = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh'];
      
      functionsToPath.forEach(func => {
        const original = Math[func];
        Math[func] = function(x) {
          const result = original(x);
          
          // Add tiny variations for extreme values
          if (Math.abs(x) > 1e10 || Math.abs(x) < 1e-10) {
            return result + utils.gaussianRandom(0, mathConfig.precision);
          }
          
          return result;
        };
      });
      
      Logger.debug('Math fingerprinting protection applied');
    }
  };
  
  // Module: CSS Fingerprinting Protection
  const CSSModule = {
    apply: () => {
      // Override CSS.supports to add variations
      if (window.CSS && window.CSS.supports) {
        const supportsOriginal = window.CSS.supports;
        
        window.CSS.supports = function(...args) {
          const result = supportsOriginal.apply(this, args);
          
          // Add some randomness to rarely used CSS features
          if (typeof args[0] === 'string' && args[0].includes('lab(')) {
            return utils.random() > 0.5;
          }
          
          return result;
        };
      }
      
      // Override getComputedStyle
      const getComputedStyleOriginal = window.getComputedStyle;
      window.getComputedStyle = function(element, pseudoElt) {
        const style = getComputedStyleOriginal.call(this, element, pseudoElt);
        
        // Add slight variations to certain properties
        return new Proxy(style, {
          get: (target, prop) => {
            const value = target[prop];
            
            // Add noise to font-related measurements
            if (typeof prop === 'string' && 
                (prop.includes('font') || prop.includes('line')) && 
                value && value.includes('px')) {
              const numValue = parseFloat(value);
              if (!isNaN(numValue)) {
                return `${numValue + utils.gaussianRandom(0, 0.01)}px`;
              }
            }
            
            return value;
          }
        });
      };
      
      Logger.debug('CSS fingerprinting protection applied');
    }
  };
  
  // Module: History
  const HistoryModule = {
    apply: () => {
      const historyLength = utils.getDeepProp(profile, 'extra_js_props.history_length');
      
      if (historyLength !== undefined) {
        utils.defineProp(History.prototype, 'length', { 
          get: () => historyLength,
          enumerable: true
        });
        Logger.debug('History length patched');
      }
    }
  };
  
  // Module: Performance API
  const PerformanceModule = {
    apply: () => {
      if (!window.performance) return;
      
      // Add realistic memory values
      if (performance.memory) {
        const baseMemory = utils.randomBetween(10000000, 50000000);
        
        utils.defineProp(performance.memory, 'jsHeapSizeLimit', {
          get: () => 2172649472
        });
        
        utils.defineProp(performance.memory, 'totalJSHeapSize', {
          get: () => baseMemory + utils.randomBetween(0, 1000000)
        });
        
        utils.defineProp(performance.memory, 'usedJSHeapSize', {
          get: () => Math.max(1000000, baseMemory - utils.randomBetween(0, 5000000))
        });
      }
      
      // Add micro-jitter to performance.now()
      const nowOriginal = performance.now.bind(performance);
      performance.now = function() {
        return nowOriginal() + utils.gaussianRandom(0, 0.00001);
      };
      
      Logger.debug('Performance API patched');
    }
  };
  
  // Module: Console Protection
  const ConsoleModule = {
    apply: () => {
      if (DEBUG_MODE) return;
      
      const methods = ['log', 'warn', 'error', 'info', 'debug', 'trace', 'table', 'group', 'groupEnd'];
      const originalConsole = {};
      
      methods.forEach(method => {
        originalConsole[method] = console[method];
        
        console[method] = function(...args) {
          // Filter out stealth-related logs
          const stack = new Error().stack || '';
          const isStealthRelated = args.some(arg => 
            typeof arg === 'string' && 
            (arg.includes('webdriver') || 
             arg.includes('fingerprint') ||
             arg.includes('stealth') ||
             arg.includes('automation'))
          );
          
          if (!isStealthRelated && !stack.includes('stealth_init.js')) {
            return originalConsole[method].apply(console, args);
          }
        };
      });
      
      Logger.debug('Console protection applied');
    }
  };
  
  // Module: Error Stack Sanitization
  const ErrorModule = {
    apply: () => {
      const OriginalError = window.Error;
      const errorTypes = ['Error', 'EvalError', 'RangeError', 'ReferenceError', 
                         'SyntaxError', 'TypeError', 'URIError'];
      
      errorTypes.forEach(errorType => {
        if (window[errorType]) {
          const OriginalErrorType = window[errorType];
          
          window[errorType] = function(...args) {
            const error = new OriginalErrorType(...args);
            
            // Clean stack traces
            if (error.stack) {
              error.stack = error.stack
                .split('\n')
                .filter(line => 
                  !line.includes('stealth_init.js') &&
                  !line.includes('__puppeteer_evaluation_script__') &&
                  !line.includes('__playwright_evaluation_script__') &&
                  !line.includes('evaluateHandle') &&
                  !line.includes('ExecutionContext')
                )
                .join('\n');
            }
            
            return error;
          };
          
          // Copy prototype
          window[errorType].prototype = OriginalErrorType.prototype;
          Object.setPrototypeOf(window[errorType], OriginalErrorType);
        }
      });
      
      Logger.debug('Error stack sanitization applied');
    }
  };
  
  // Module: Behavioral Protection
  const BehavioralModule = {
    apply: () => {
      if (!utils.getDeepProp(profile, 'extra_js_props.behavioral_protection', true)) return;
      
      // Add natural variations to events
      const eventHandler = (event) => {
        if (event.isTrusted) {
          // Add micro-variations to timestamps
          Object.defineProperty(event, 'timeStamp', {
            get: () => event.timeStamp + utils.gaussianRandom(0, 0.1),
            configurable: true
          });
        }
      };
      
      // Monitor events
      const eventsToMonitor = [
        'mousedown', 'mouseup', 'mousemove', 'mouseenter', 'mouseleave',
        'click', 'dblclick', 'contextmenu',
        'keydown', 'keyup', 'keypress',
        'touchstart', 'touchend', 'touchmove',
        'wheel', 'scroll'
      ];
      
      eventsToMonitor.forEach(eventType => {
        window.addEventListener(eventType, eventHandler, { 
          capture: true, 
          passive: true 
        });
      });
      
      // Simulate human-like focus/blur patterns
      let lastFocusTime = Date.now();
      let focusCount = 0;
      
      const focusHandler = () => {
        const now = Date.now();
        const timeSinceLast = now - lastFocusTime;
        
        // Humans don't rapidly focus/blur
        if (timeSinceLast < 100) {
          focusCount++;
          if (focusCount > 10) {
            Logger.warn('Rapid focus/blur detected - possible automation');
          }
        } else {
          focusCount = 0;
        }
        
        lastFocusTime = now;
      };
      
      window.addEventListener('focus', focusHandler);
      window.addEventListener('blur', focusHandler);
      
      Logger.debug('Behavioral protection applied');
    }
  };
  
  // Module: Worker Protection
  const WorkerModule = {
    apply: () => {
      const workerScript = `
        // Basic worker patches
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        
        // Override user agent
        Object.defineProperty(navigator, 'userAgent', { 
          get: () => '${profile.user_agent || navigator.userAgent}' 
        });
        
        // Remove automation properties
        const props = ['webdriver', '__webdriver_evaluate', '__driver_evaluate'];
        props.forEach(prop => {
          try { delete navigator[prop]; } catch(e) {}
          try { delete WorkerGlobalScope[prop]; } catch(e) {}
        });
      `;
      
      try {
        const blob = new Blob([workerScript], { type: 'application/javascript' });
        const workerUrl = URL.createObjectURL(blob);
        
        // Test worker
        const worker = new Worker(workerUrl);
        worker.terminate();
        
        URL.revokeObjectURL(workerUrl);
        
        Logger.debug('Worker protection tested successfully');
      } catch (e) {
        Logger.warn('Could not patch Worker context:', e);
      }
    }
  };
  
  // Module: Iframe Protection
  const IframeModule = {
    apply: () => {
      // Ensure iframes have consistent fingerprints
      if (window.self !== window.top) {
        try {
          const parentScreen = window.top.screen;
          if (parentScreen) {
            ['width', 'height', 'availWidth', 'availHeight', 'colorDepth', 'pixelDepth'].forEach(prop => {
              if (screen[prop] !== parentScreen[prop]) {
                utils.defineProp(screen, prop, { 
                  get: () => parentScreen[prop],
                  enumerable: true
                });
              }
            });
          }
        } catch (e) {
          // Cross-origin iframe
        }
      }
    }
  };
  
  // Module: Network Information API
  const NetworkModule = {
    apply: () => {
      if (!navigator.connection) return;
      
      const connection = navigator.connection;
      
      // Dynamic updates
      const updateConnection = () => {
        const downlink = utils.getDeepProp(profile, 'extra_js_props.connection.downlink', 10);
        
        utils.defineProp(connection, 'downlink', {
          get: () => utils.timeOperations.addJitter(downlink, 0.3)
        });
        
        utils.defineProp(connection, 'rtt', {
          get: () => utils.randomBetween(20, 150)
        });
        
        utils.defineProp(connection, 'effectiveType', {
          get: () => {
            const types = ['slow-2g', '2g', '3g', '4g'];
            const weights = [0.02, 0.05, 0.13, 0.8];
            const rand = utils.random();
            let sum = 0;
            
            for (let i = 0; i < types.length; i++) {
              sum += weights[i];
              if (rand < sum) return types[i];
            }
            
            return '4g';
          }
        });
      };
      
      updateConnection();
      
      // Update periodically
      setInterval(updateConnection, utils.randomBetween(30000, 60000));
      
      Logger.debug('Network Information API patched');
    }
  };
  
  // Module: Mutation Observer
  const MutationModule = {
    apply: () => {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.target === document.documentElement) {
            // Check for automation attributes
            const attr = mutation.attributeName;
            if (attr && (attr.includes('driver') || 
                         attr.includes('selenium') || 
                         attr.startsWith('$cdc_') ||
                         attr.startsWith('__'))) {
              document.documentElement.removeAttribute(attr);
              Logger.debug(`Removed automation attribute: ${attr}`);
            }
          }
        });
      });
      
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: null // Monitor all attributes
      });
      
      Logger.debug('Mutation observer active');
    }
  };
  
  // ====== MODULE REGISTRY ======
  const modules = [
    { name: 'Core', module: CoreModule, priority: 100 },
    { name: 'Chrome', module: ChromeModule, priority: 90 },
    { name: 'Navigator', module: NavigatorModule, priority: 80 },
    { name: 'Screen', module: ScreenModule, priority: 70 },
    { name: 'WebGL', module: WebGLModule, priority: 60 },
    { name: 'Canvas', module: CanvasModule, priority: 55 },
    { name: 'WebRTC', module: WebRTCModule, priority: 50 },
    { name: 'Audio', module: AudioModule, priority: 45 },
    { name: 'Fonts', module: FontModule, priority: 40 },
    { name: 'Scheduling', module: SchedulingModule, priority: 35 },
    { name: 'Permissions', module: PermissionsModule, priority: 30 },
    { name: 'Battery', module: BatteryModule, priority: 25 },
    { name: 'Plugins', module: PluginsModule, priority: 20 },
    { name: 'MediaDevices', module: MediaDevicesModule, priority: 15 },
    { name: 'Timezone', module: TimezoneModule, priority: 10 },
    { name: 'Speech', module: SpeechModule, priority: 9 },
    { name: 'Math', module: MathModule, priority: 8 },
    { name: 'CSS', module: CSSModule, priority: 7 },
    { name: 'History', module: HistoryModule, priority: 6 },
    { name: 'Performance', module: PerformanceModule, priority: 5 },
    { name: 'Console', module: ConsoleModule, priority: 4 },
    { name: 'Error', module: ErrorModule, priority: 3 },
    { name: 'Behavioral', module: BehavioralModule, priority: 2 },
    { name: 'Worker', module: WorkerModule, priority: 1 },
    { name: 'Iframe', module: IframeModule, priority: 1 },
    { name: 'Network', module: NetworkModule, priority: 1 },
    { name: 'Mutation', module: MutationModule, priority: 0 }
  ];
  
  // Sort by priority
  modules.sort((a, b) => b.priority - a.priority);
  
  // ====== APPLY MODULES ======
  const startTime = performance.now();
  const appliedModules = [];
  const failedModules = [];
  
  modules.forEach(({ name, module }) => {
    try {
      if (config.patches[name.toLowerCase()] !== false) {
        module.apply();
        appliedModules.push(name);
      }
    } catch (error) {
      Logger.error(`Failed to apply ${name} module:`, error);
      failedModules.push({ name, error: error.message });
    }
  });
  
  const endTime = performance.now();
  
  // ====== FINALIZATION ======
  
  // Mark initialization complete
  window.__stealth_initialized__ = {
    version: STEALTH_VERSION,
    profile: profile.name,
    timestamp: Date.now(),
    duration: endTime - startTime,
    modules: {
      applied: appliedModules,
      failed: failedModules
    },
    config: config
  };
  
  // Freeze critical objects
  try {
    Object.freeze(window.__stealth_initialized__);
    Object.freeze(Navigator.prototype.webdriver);
    if (window.chrome) Object.freeze(window.chrome.runtime);
  } catch (e) {}
  
  // Final log
  Logger.success(
    `Stealth v${STEALTH_VERSION} initialized in ${(endTime - startTime).toFixed(2)}ms\n` +
    `Profile: ${profile.name}\n` +
    `Applied modules: ${appliedModules.length}/${modules.length}\n` +
    `Failed modules: ${failedModules.length}`
  );
  
  // Clean up in production
  if (!DEBUG_MODE) {
    delete window.__fingerprint_profile__;
  }
  
})();