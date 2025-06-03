// src/core/stealth_init.js
(() => {
  const dbg = false; 
  const log = (...a) => dbg && console.log("🕵️ stealth:", ...a);

  const profile = window.__fingerprint_profile__ || {}; // Bevat nu alle BrowserProfile attributen
  log('Stealth script gebruikt fingerprint profiel:', profile);

  // --- Utility voor consistente random waarde per profiel ---
  const seededRandom = (seedStr) => {
    let seed = 0;
    for (let i = 0; i < seedStr.length; i++) {
      seed = (seed * 31 + seedStr.charCodeAt(i)) & 0xFFFFFFFF;
    }
    return function() {
      seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF;
      return seed / 0xFFFFFFFF;
    };
  };
  const profileRand = profile.name ? seededRandom(profile.name) : Math.random; // Gebruik profielnaam als seed

  // --- 1. navigator.webdriver --- (Bestaand)
  if (navigator.webdriver === true || navigator.webdriver === undefined) { // Ook undefined patchen
    Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
    log('navigator.webdriver gespooft.');
  }

  // --- 2. window.chrome stub --- (Bestaand, licht aangepast)
  if (profile.user_agent && profile.user_agent.toLowerCase().includes('chrome')) {
    window.chrome = window.chrome || {};
    window.chrome.runtime = window.chrome.runtime || {};
    if(!window.chrome.loadTimes) window.chrome.loadTimes = () => ({}); // Return leeg object
    if(!window.chrome.csi) window.chrome.csi = () => ({startE: Date.now(), onloadT: Date.now(), pageT: 0, tran: 15}); // Common values
    log('window.chrome basis properties aangepast.');
  }


  // --- 3. Talen --- (Bestaand, gebruikt nu profiel.locale)
  const languages = profile.locale ? profile.locale.split(',').map(lang => lang.split(';')[0].trim()) : ['it-IT', 'it', 'en-US', 'en'];
  Object.defineProperty(navigator, 'languages', { get: () => languages, configurable: true });
  Object.defineProperty(navigator, 'language', { get: () => languages[0], configurable: true });
  log('navigator.languages en language gespooft naar:', languages);
  
  // --- 4. Platform --- (Bestaand, gebruikt nu profiel.js_platform)
  const platform = profile.js_platform || 'Win32';
  Object.defineProperty(navigator, 'platform', { get: () => platform, configurable: true });
  log('navigator.platform gespooft naar:', platform);

  // --- 5. Plugins --- (Bestaand, maar minimaler en realistischer)
  const createPlugin = (name, filename, description, mimeType, suffixes) => ({
    name, filename, description, length: 1,
    item: () => createMimeType(mimeType, suffixes, description),
    namedItem: () => createMimeType(mimeType, suffixes, description),
    0: createMimeType(mimeType, suffixes, description)
  });
  const createMimeType = (type, suffixes, description) => ({ type, suffixes, description, enabledPlugin: null /* set later */ });

  const pdfPlugin = createPlugin('PDF Viewer', 'internal-pdf-viewer', 'Portable Document Format', 'application/pdf', 'pdf');
  const crpdfPlugin = createPlugin('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', 'Portable Document Format', 'application/pdf', 'pdf');
  // NaCl is deprecated, overweeg weglaten of alleen voor oudere profielen
  // const naclPlugin = createPlugin('Native Client', 'internal-nacl-plugin', '', 'application/x-nacl', '');
  
  const fakePluginsList = [];
  if (profile.user_agent && profile.user_agent.toLowerCase().includes('chrome')) {
      fakePluginsList.push(pdfPlugin, crpdfPlugin);
  } else if (profile.user_agent && profile.user_agent.toLowerCase().includes('firefox')) {
      fakePluginsList.push(pdfPlugin); // Firefox heeft doorgaans alleen een PDF plugin
  }
  // Safari heeft vaak geen plugins meer standaard

  const fakePlugins = Object.freeze(fakePluginsList);
  fakePlugins.item = idx => fakePlugins[idx];
  fakePlugins.namedItem = name => fakePlugins.find(p => p.name === name) || null;
  fakePlugins.refresh = () => {}; // Dummy
  
  const mimeTypesList = fakePlugins.flatMap(p => Array.from({length: p.length}, (_, i) => {
      const mime = p[i];
      mime.enabledPlugin = p; // Link back to plugin
      return mime;
  }));
  const fakeMimeTypes = Object.freeze(mimeTypesList);
  fakeMimeTypes.item = idx => fakeMimeTypes[idx];
  fakeMimeTypes.namedItem = name => fakeMimeTypes.find(m => m.type === name) || null;
  fakeMimeTypes.length = fakeMimeTypes.length;

  Object.defineProperty(navigator, 'plugins', { get: () => fakePlugins, configurable: true });
  Object.defineProperty(navigator, 'mimeTypes', { get: () => fakeMimeTypes, configurable: true });
  log('navigator.plugins en mimeTypes gespooft (realistischer).');

  // --- 6. Permissions API --- (Bestaand)
  if (navigator.permissions) {
    const originalPermissionsQuery = navigator.permissions.query;
    navigator.permissions.query = parameters =>
      parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission || 'prompt' }) // Default naar prompt
        : originalPermissionsQuery.call(navigator.permissions, parameters);
    log('navigator.permissions.query voor notifications gepatcht.');
  }

  // --- 7. WebGL Fingerprint --- (Bestaand, met kleine aanpassing)
  const getParameterProxyHandler = {
    apply(target, ctx, args) {
      const param = args && args.length > 0 ? args[0] : null;
      const RENDERER_INFO = 0x1F00; // WEBGL_debug_renderer_info
      const VENDOR = 0x1F01; // UNMASKED_VENDOR_WEBGL
      const RENDERER = 0x1F02; // UNMASKED_RENDERER_WEBGL

      // Gebruik profiel-specifieke waarden als ze bestaan, anders generieke defaults
      if (param === (profile.extra_js_props?.WEBGL_VENDOR_ID || VENDOR)) { // Haal ID's uit profiel indien gespecificeerd
          return profile.webgl_vendor || 'Google Inc. (Intel)';
      }
      if (param === (profile.extra_js_props?.WEBGL_RENDERER_ID || RENDERER)) {
          return profile.webgl_renderer || `ANGLE (Intel, Intel(R) UHD Graphics ${600 + Math.floor(profileRand()*100)} Direct3D11 vs_5_0 ps_5_0, D3D11)`;
      }
      return Reflect.apply(target, ctx, args);
    },
  };
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      // Definieer WEBGL_VENDOR_ID en WEBGL_RENDERER_ID in profiel.extra_js_props indien nodig
      // bijv. profile.extra_js_props = { WEBGL_VENDOR_ID: ext.UNMASKED_VENDOR_WEBGL, ... }
      // Dit maakt het robuuster als de constanten verschillen.
      // Voor nu, als ext bestaat, gebruik die waardes.
      const VENDOR_ID = ext ? ext.UNMASKED_VENDOR_WEBGL : 0x1F01;
      const RENDERER_ID = ext ? ext.UNMASKED_RENDERER_WEBGL : 0x1F02;
      if (profile.extra_js_props) { // Zorg dat deze bestaan voor de proxy handler
          profile.extra_js_props.WEBGL_VENDOR_ID = VENDOR_ID;
          profile.extra_js_props.WEBGL_RENDERER_ID = RENDERER_ID;
      }


      const proto = Object.getPrototypeOf(gl);
      if (proto && !proto._paramPatched) {
          proto.getParameter = new Proxy(proto.getParameter, getParameterProxyHandler);
          proto._paramPatched = true;
          log('WebGL getParameter gepatcht.');
      }
    }
  } catch (e) { log('WebGL patching error:', e); }


  // --- 8. Consistent Canvas Fingerprint Spoofing (Nieuw/Verbeterd) ---
  if (typeof CanvasRenderingContext2D !== 'undefined') {
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetContext = HTMLCanvasElement.prototype.getContext;

    HTMLCanvasElement.prototype.getContext = function(type, attrs) {
        const context = originalGetContext.call(this, type, attrs);
        if (type === '2d' && context && !context._noisePatched) {
            context.getImageData = function(...args) {
                const imageData = originalGetImageData.apply(this, args);
                // Voeg subtiele, consistente ruis toe gebaseerd op profiel seed
                // Dit is een simpel voorbeeld; geavanceerdere methoden bestaan
                const d = imageData.data;
                for (let i = 0; i < d.length; i += 4) { // Per pixel
                    if (profileRand() < 0.001) { // Pas 0.1% van pixels licht aan
                         d[i] = (d[i] + Math.floor(profileRand() * 3 -1) ) % 256;     // Rood
                         d[i+1] = (d[i+1] + Math.floor(profileRand() * 3-1) ) % 256; // Groen
                         d[i+2] = (d[i+2] + Math.floor(profileRand() * 3-1) ) % 256; // Blauw
                    }
                }
                return imageData;
            };
            context._noisePatched = true;
            log('Canvas 2D getImageData gepatcht met consistente ruis.');
        }
        return context;
    };

    // Optioneel: toDataURL patchen om een vaste afbeelding terug te geven
    // HTMLCanvasElement.prototype.toDataURL = function(type, encoderOptions) {
    //   if (this.width === 300 && this.height === 150) { // Voorbeeld: specifieke canvas afmeting
    //     log('Vaste data URL geretourneerd voor specifieke canvas.');
    //     return profile.extra_js_props?.fixedCanvasDataURL || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACWCAYAAABkW7XSAAABGUlEQVR4Xu3BMQEAAADCoPVPbQhfoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOA1v9QAATX6G/gAAAAASUVORK5CYII='; // Dummy data URL
    //   }
    //   return originalToDataURL.call(this, type, encoderOptions);
    // };
  }

  // --- 9. Uitgebreide Navigator & Screen Properties (Nieuw/Verbeterd) ---
  // Gebruik waarden uit profile, met defaults als ze niet gedefinieerd zijn
  const nav = window.navigator;
  const scr = window.screen;

  Object.defineProperties(nav, {
    hardwareConcurrency: { get: () => profile.hardware_concurrency || 4, configurable: true },
    deviceMemory: { get: () => profile.device_memory || 8, configurable: true },
    // appCodeName: { get: () => 'Mozilla', configurable: true }, // Vaak "Mozilla"
    // appName: { get: () => 'Netscape', configurable: true }, // Vaak "Netscape"
    // product: { get: () => 'Gecko', configurable: true }, // Voor Gecko-gebaseerde, of "WebKit"
    // productSub: { get: () => '20100101', configurable: true }, // Typische Gecko-waarde
    vendor: { get: () => profile.extra_js_props?.navigator_vendor || 'Google Inc.', configurable: true }, // "Google Inc.", "Apple Computer, Inc.", "" (voor Firefox)
    vendorSub: { get: () => '', configurable: true }, // Meestal een lege string
  });
  log('Extra navigator properties gespooft:', {
    hardwareConcurrency: nav.hardwareConcurrency, deviceMemory: nav.deviceMemory, vendor: nav.vendor
  });
  
  Object.defineProperties(scr, {
    width: { get: () => profile.screen_width || 1920, configurable: true },
    height: { get: () => profile.screen_height || 1080, configurable: true },
    availWidth: { get: () => profile.avail_width || profile.screen_width || 1920, configurable: true },
    availHeight: { get: () => profile.avail_height || (profile.screen_height ? profile.screen_height - 40 : 1040) , configurable: true },
    colorDepth: { get: () => profile.color_depth || 24, configurable: true },
    pixelDepth: { get: () => profile.pixel_depth || 24, configurable: true },
    availLeft: { get: () => 0, configurable: true }, // Meestal 0
    availTop: { get: () => 0, configurable: true },  // Meestal 0
    orientation: { get: () => ({ type: 'landscape-primary', angle: 0, onchange: null }), configurable: true } // Desktop
  });
  log('Screen properties gespooft naar profielwaarden.');

  // --- 10. Battery API Spoofing ---
  if (profile.extra_js_props?.spoof_battery !== false) { // Opt-out via profiel
    try {
        const batteryInfo = {
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1.0,
            onchargingchange: null,
            onchargingtimechange: null,
            ondischargingtimechange: null,
            onlevelchange: null
        };
        if (nav.getBattery) { // Controleer of de functie bestaat
             navigator.getBattery = () => Promise.resolve(batteryInfo);
             log('navigator.getBattery gespooft.');
        } else { // Als het niet bestaat, maar we willen het wel simuleren
             Object.defineProperty(navigator, "getBattery", {
                value: () => Promise.resolve(batteryInfo),
                writable: true,
                configurable: true,
                enumerable: true
             });
             log('navigator.getBattery aangemaakt en gespooft.');
        }
    } catch(e) { log('Battery API patching error:', e); }
  }


  // --- Overige bestaande patches ---
  // Worker context: navigator.webdriver patch (Bestaand)
  try {
    if (typeof Worker !== 'undefined') {
        const workerFunc = `Object.defineProperty(navigator,'webdriver',{get:()=>false}); self.postMessage('done');`;
        const blob = new Blob([workerFunc], {type:'application/javascript'});
        const worker = new Worker(URL.createObjectURL(blob));
        setTimeout(() => worker.terminate(), 1000); 
        log('Worker navigator.webdriver gepatcht.');
    }
  } catch (e) { log('Worker patching error:', e); }

  // Error.prepareStackTrace & Function.prototype.toString leakage (Bestaand)
  // ... (Behoud de bestaande code voor Function.prototype.toString patch)
  const originalToString = Function.prototype.toString;
  const nativeToStringStr = Function.prototype.toString.call(originalToString); // Krijg de string representatie van de native toString
  Function.prototype.toString = function() {
    const DisguisedFunctions = [
      { func: navigator.getBattery, name: "getBattery"},
      { func: navigator.permissions?.query, name: "query"},
      // { func: navigator.plugins?.item, name: "item"}, // Kan problemen geven
      // { func: navigator.mimeTypes?.item, name: "item"}
    ];
    for(const df of DisguisedFunctions){
        if(this === df.func) return `function ${df.name}() { [native code] }`;
    }
    if (this === navigator.webdriver) return 'function webdriver() { [native code] }'; // Specifieke check

    return originalToString.apply(this, arguments);
  };
  // Patch de toString van onze toString patch zelf om er native uit te zien
  Function.prototype.toString.toString = () => nativeToStringStr;
  log('Function.prototype.toString gepatcht.');
  

  // Automation flags on window (Bestaand)
  const automationProps = ['__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', '__fxdriver_evaluate',
                           '__driver_unwrapped', '__webdriver_unwrapped', '__selenium_unwrapped', '__fxdriver_unwrapped',
                           '_Selenium_IDE_Recorder', '_selenium', 'callSelenium', '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw',
                           'driver', 'webdriver', 'selenium', 'calledSelenium', '$cdc_ページソース取得UA変更_selenium', '$cdc_asdjflasutopfhvcZLmcfl_'];
  automationProps.forEach(prop => {
    if (window[prop]) delete window[prop];
    if (window.navigator[prop]) delete window.navigator[prop];
  });
  // Check documentElement attributen
  if (window.document && window.document.documentElement) {
    const attrsToRemove = ['selenium', 'webdriver', 'driver'];
    attrsToRemove.forEach(attr => {
        if(window.document.documentElement.hasAttribute(attr)) window.document.documentElement.removeAttribute(attr);
    });
  }
  log('Common automation flags verwijderd/gepatcht.');

  // Device Pixel Ratio (Bestaand, gebruikt nu profiel.device_pixel_ratio)
  const dpr = profile.device_pixel_ratio || window.devicePixelRatio || 1.0;
  try { // In try-catch omdat het soms niet overschrijfbaar is
    Object.defineProperty(window, 'devicePixelRatio', { get: () => dpr, configurable: true});
    log('window.devicePixelRatio gespooft naar:', dpr);
  } catch (e) { log('Kon devicePixelRatio niet spoofen:', e); }


  // Voeg een indicatie toe dat de stealth patches zijn toegepast
  window.stealthPatchesApplied = true;
  log('Stealth script volledig toegepast.');
})();