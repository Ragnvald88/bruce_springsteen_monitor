// src/core/stealth_init.js (Verbeterde Versie)
(() => {
  const dbg = false; // Zet op true voor console logs vanuit stealth
  const log = (...a) => dbg && console.log("🕵️ stealth:", ...a);

  // Haal het volledige, gedetailleerde profiel op.
  // Dit profiel wordt nu verondersteld veel meer specifieke data te bevatten.
  const profile = window.__fingerprint_profile__ || {};
  log('Stealth script GEACTIVEERD met uitgebreid profiel:', profile.name || 'Onbekend Profiel');

  // --- Hulpprogramma voor consistent, seeded random getal ---
  const seededRandom = (seedStr) => {
    let seed = 0;
    if (seedStr) {
      for (let i = 0; i < seedStr.length; i++) {
        seed = (seed * 31 + seedStr.charCodeAt(i)) & 0xFFFFFFFF;
      }
    } else { // Fallback als geen seed string (zou niet moeten gebeuren met profielnaam)
        seed = Math.floor(Math.random() * 0xFFFFFFFF);
    }
    return function() {
      seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF;
      return seed / 0xFFFFFFFF;
    };
  };
  // Gebruik profielnaam als seed voor alle randomisaties binnen dit script
  const profileRand = seededRandom(profile.name || "default_seed");

  // --- Hulpprogramma om veilig een eigenschap te definiëren ---
  const defineProperty = (obj, prop, descriptor) => {
    try {
      Object.defineProperty(obj, prop, { ...descriptor, configurable: true });
    } catch (e) {
      log(`Fout bij definiëren eigenschap ${prop}:`, e);
    }
  };

  // --- 1. navigator.webdriver ---
  if (navigator.webdriver || navigator.webdriver === undefined) {
    defineProperty(navigator, 'webdriver', { get: () => false });
    log('navigator.webdriver gespooft naar false.');
  }

  // --- 2. Uitgebreide window.chrome en Chromium-specifieke stubs (indien Chrome profiel) ---
  const isChromeBased = profile.user_agent && profile.user_agent.toLowerCase().includes('chrome');
  if (isChromeBased) {
    window.chrome = window.chrome || {};
    const chrome = window.chrome;
    // Basisfuncties (uitgebreid)
    if (!chrome.loadTimes) defineProperty(chrome, 'loadTimes', { get: () => () => ({}) });
    if (!chrome.csi) defineProperty(chrome, 'csi', { get: () => () => ({startE: Date.now() - Math.floor(profileRand() * 200), onloadT: Date.now() - Math.floor(profileRand()*50), pageT: profileRand() * 5000, tran: 15})});

    // App & Webstore stubs (vaak aanwezig)
    chrome.app = chrome.app || {
      isInstalled: false,
      getDetails: () => null,
      getIsInstalled: () => false,
      installState: () => 'not_installed',
      runningState: () => 'cannot_run',
    };
    chrome.webstore = chrome.webstore || {
      onInstallStageChanged: {},
      onDownloadProgress: {},
      install: (url, successCb, failureCb) => failureCb('INSTALL_ERROR', 'User cancelled'),
    };
    // Runtime (uitgebreider)
    chrome.runtime = chrome.runtime || {
      id: profile.extra_js_props?.chrome_runtime_id || Array(32).fill(0).map(() => 'abcdefghijklmnopqrstuvwxyz'[Math.floor(profileRand() * 26)]).join(''), // Genereer een dummy extension ID
      getManifest: () => ({ manifest_version: 2, name: 'Stealth Extension Stub', version: '1.0' }),
      getURL: (path) => `chrome-extension://${chrome.runtime.id}/${path}`,
      sendMessage: () => {},
      onMessage: { addListener: () => {} },
      lastError: undefined, // Initieel geen error
      connect: () => ({ onMessage: { addListener: () => {} }, postMessage: () => {}, disconnect: () => {} }),
      onConnect: { addListener: () => {} },
    };
    log('window.chrome stubs uitgebreid voor Chrome profiel.');
  }

  // --- 3. Talen & Locale ---
  // `profile.locale` (bijv. "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7")
  const languages = (profile.locale || 'it-IT,it,en-US,en').split(',').map(lang => lang.split(';')[0].trim());
  defineProperty(navigator, 'languages', { get: () => languages });
  defineProperty(navigator, 'language', { get: () => languages[0] });
  log('navigator.languages en language gespooft:', languages);

  // --- 4. Platform ---
  // `profile.js_platform` (bijv. "Win32", "MacIntel", "Linux x86_64")
  defineProperty(navigator, 'platform', { get: () => profile.js_platform || 'Win32' });
  log('navigator.platform gespooft:', navigator.platform);

  // --- 5. Plugins & MimeTypes (Profiel-gestuurd) ---
  // Verwacht `profile.extra_js_props.plugins_array` als een array van plugin objecten.
  // Elk plugin object: { name, filename, description, mimeTypes: [{ type, suffixes, description }, ...] }
  const pluginsArray = profile.extra_js_props?.plugins_array || [];
  const mimeTypesArray = [];

  const createPluginObject = (pluginData) => {
    const mimeTypeObjects = (pluginData.mimeTypes || []).map(mimeData => {
      const mime = {
        type: mimeData.type,
        suffixes: mimeData.suffixes,
        description: mimeData.description,
        enabledPlugin: null // Wordt later ingevuld
      };
      mimeTypesArray.push(mime); // Verzamel alle mimetypes
      return mime;
    });

    const plugin = {
      name: pluginData.name,
      filename: pluginData.filename,
      description: pluginData.description,
      length: mimeTypeObjects.length,
      item: (index) => mimeTypeObjects[index],
      namedItem: (name) => mimeTypeObjects.find(m => m.type === name) || null,
    };
    // Link mimetypes terug naar de plugin
    mimeTypeObjects.forEach(m => m.enabledPlugin = plugin);
    // Maak de mimeTypes ook direct toegankelijk via index op het plugin object
    mimeTypeObjects.forEach((mt, i) => plugin[i] = mt);
    return plugin;
  };

  const finalPluginsList = pluginsArray.map(createPluginObject);
  Object.freeze(finalPluginsList); // Maak de lijst onveranderbaar

  const fakePlugins = {
    length: finalPluginsList.length,
    item: (index) => finalPluginsList[index],
    namedItem: (name) => finalPluginsList.find(p => p.name === name) || null,
    refresh: () => { log("navigator.plugins.refresh() aangeroepen"); },
    // Maak plugins ook toegankelijk via index
    ...finalPluginsList
  };

  defineProperty(navigator, 'plugins', { get: () => fakePlugins });

  Object.freeze(mimeTypesArray);
  const fakeMimeTypes = {
    length: mimeTypesArray.length,
    item: (index) => mimeTypesArray[index],
    namedItem: (name) => mimeTypesArray.find(m => m.type === name) || null,
    // Maak mimetypes ook toegankelijk via index
    ...mimeTypesArray
  };
  defineProperty(navigator, 'mimeTypes', { get: () => fakeMimeTypes });
  log('navigator.plugins en mimeTypes gespooft op basis van profiel (realistischer). Aantal plugins:', finalPluginsList.length);

  // --- 6. Permissions API (Uitgebreid, Profiel-gestuurd) ---
  // Verwacht `profile.extra_js_props.permissions_states` als { "geolocation": "prompt", "notifications": "granted", ... }
  if (navigator.permissions) {
    const originalPermissionsQuery = navigator.permissions.query.bind(navigator.permissions);
    const permissionStatesFromProfile = profile.extra_js_props?.permissions_states || {};
    defineProperty(navigator.permissions, 'query', {
      value: (parameters) => {
        const name = parameters?.name;
        if (name && permissionStatesFromProfile[name]) {
          log(`Permissions API: Gespoofte status voor '${name}': ${permissionStatesFromProfile[name]}`);
          return Promise.resolve({ state: permissionStatesFromProfile[name], name: name, onchange: null });
        }
        // Fallback naar 'prompt' voor veelvoorkomende permissies als niet in profiel, of origineel
        const commonPermissionsDefaultPrompt = ['geolocation', 'camera', 'microphone', 'midi', 'clipboard-read', 'clipboard-write'];
        if (name && commonPermissionsDefaultPrompt.includes(name)) {
           log(`Permissions API: Fallback 'prompt' status voor '${name}'`);
           return Promise.resolve({ state: 'prompt', name: name, onchange: null });
        }
        log(`Permissions API: Originele query voor '${name}'`);
        return originalPermissionsQuery(parameters);
      }
    });
    log('navigator.permissions.query gepatcht (uitgebreid).');
  }

  // --- 7. WebGL Fingerprint (Profiel-gestuurd voor renderer/vendor strings) ---
  // Verwacht `profile.webgl_vendor` en `profile.webgl_renderer`
  // Verwacht optioneel `profile.extra_js_props.webgl_supported_extensions` (array van strings)
  // en `profile.extra_js_props.webgl_shader_precision_formats` (object met formats)
  try {
    const canvas = document.createElement('canvas');
    let gl = null;
    try { gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl'); } catch (e) { /* ignore */ }

    if (gl) {
      const getParameterProxyHandler = {
        apply(target, ctx, args) {
          const param = args && args.length > 0 ? args[0] : null;
          const RENDERER_INFO_CONSTS = { VENDOR: 0x1F01, RENDERER: 0x1F02 }; // Standaard constanten

          if (param === RENDERER_INFO_CONSTS.VENDOR && profile.webgl_vendor) {
            return profile.webgl_vendor;
          }
          if (param === RENDERER_INFO_CONSTS.RENDERER && profile.webgl_renderer) {
            return profile.webgl_renderer;
          }
          // Fallback voor andere WebGL parameters
          return Reflect.apply(target, ctx, args);
        },
      };
      const proto = Object.getPrototypeOf(gl);
      if (proto && !proto._paramPatched) { // Voorkom dubbel patchen
        defineProperty(proto, 'getParameter', new Proxy(proto.getParameter, getParameterProxyHandler));

        // Patch getSupportedExtensions indien data in profiel
        if (profile.extra_js_props?.webgl_supported_extensions && Array.isArray(profile.extra_js_props.webgl_supported_extensions)) {
          const exts = profile.extra_js_props.webgl_supported_extensions;
          defineProperty(proto, 'getSupportedExtensions', { get: () => () => exts });
        }

        // Patch getExtension (om compatibel te zijn met getSupportedExtensions)
        const originalGetExtension = proto.getExtension;
        defineProperty(proto, 'getExtension', {
          value: function(name) {
            const supportedExts = profile.extra_js_props?.webgl_supported_extensions;
            if (supportedExts && !supportedExts.includes(name)) {
              // Als de profiel-specifieke lijst bestaat en de extensie staat er niet in, retourneer null
              log(`WebGL: getExtension('${name}') -> null (niet in profiel lijst)`);
              return null;
            }
            // Anders, roep de originele functie aan (of retourneer een dummy object als het een bekende debug ext is)
            if (name === 'WEBGL_debug_renderer_info' && (profile.webgl_vendor || profile.webgl_renderer)) {
                 return { UNMASKED_VENDOR_WEBGL: 0x1F01, UNMASKED_RENDERER_WEBGL: 0x1F02 };
            }
            return originalGetExtension.call(this, name);
          }
        });
        proto._paramPatched = true;
        log('WebGL getParameter, getSupportedExtensions, en getExtension gepatcht.');
      }
    }
  } catch (e) { log('WebGL patching error:', e); }

  // --- 8. Canvas Fingerprint Spoofing (Geavanceerdere Ruis) ---
  // Verwacht `profile.extra_js_props.canvas_noise_intensity` (float, bijv. 0.001 voor 0.1%)
  // en `profile.extra_js_props.canvas_noise_rgb_shift` (integer, bijv. 1 of 2)
  if (typeof CanvasRenderingContext2D !== 'undefined') {
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    const noiseIntensity = profile.extra_js_props?.canvas_noise_intensity || 0.0005; // Zeer subtiel standaard
    const rgbShiftMax = Math.max(1, profile.extra_js_props?.canvas_noise_rgb_shift || 1);

    defineProperty(CanvasRenderingContext2D.prototype, 'getImageData', {
      value: function(...args) {
        const imageData = originalGetImageData.apply(this, args);
        const d = imageData.data;
        for (let i = 0; i < d.length; i += 4) {
          if (profileRand() < noiseIntensity) {
            d[i]   = (d[i]   + Math.floor(profileRand() * (2 * rgbShiftMax + 1) - rgbShiftMax)) % 256;
            d[i+1] = (d[i+1] + Math.floor(profileRand() * (2 * rgbShiftMax + 1) - rgbShiftMax)) % 256;
            d[i+2] = (d[i+2] + Math.floor(profileRand() * (2 * rgbShiftMax + 1) - rgbShiftMax)) % 256;
          }
        }
        return imageData;
      }
    });
    log('Canvas 2D getImageData gepatcht met geavanceerdere, profiel-gestuurde ruis.');
  }

  // --- 9. Navigator & Screen Properties (Uitgebreid & Profiel-gestuurd) ---
  const nav = window.navigator;
  const scr = window.screen;

  defineProperty(nav, 'hardwareConcurrency', { get: () => profile.hardware_concurrency || 4 });
  defineProperty(nav, 'deviceMemory', { get: () => profile.device_memory || 8 });
  defineProperty(nav, 'vendor', { get: () => profile.extra_js_props?.navigator_vendor || (isChromeBased ? 'Google Inc.' : 'Mozilla') });
  defineProperty(nav, 'vendorSub', { get: () => '' }); // Meestal leeg
  defineProperty(nav, 'appCodeName', { get: () => 'Mozilla' }); // Standaard
  defineProperty(nav, 'appName', { get: () => (isChromeBased ? 'Netscape' : 'Netscape') }); // Standaard, soms anders voor specifieke browsers
  defineProperty(nav, 'product', { get: () => (isChromeBased ? 'Gecko' : 'Gecko') }); // Kan "WebKit" zijn voor WebKit-based
  defineProperty(nav, 'productSub', { get: () => profile.extra_js_props?.navigator_productSub || '20100101' }); // Typische Gecko-waarde

  // `profile.extra_js_props.connection_info` = { rtt: 50, downlink: 10, effectiveType: '4g', saveData: false }
  if (profile.extra_js_props?.connection_info) {
      defineProperty(nav, 'connection', { get: () => ({ ...profile.extra_js_props.connection_info, onchange: null }) });
      defineProperty(nav, 'mozConnection', { get: () => ({ ...profile.extra_js_props.connection_info, onchange: null }) }); // Voor Firefox
      defineProperty(nav, 'webkitConnection', { get: () => ({ ...profile.extra_js_props.connection_info, onchange: null }) }); // Voor oudere WebKit
  }
  defineProperty(nav, 'maxTouchPoints', { get: () => profile.extra_js_props?.maxTouchPoints || 0 });
  log('Extra navigator properties gespooft (uitgebreid).');

  defineProperty(scr, 'width', { get: () => profile.screen_width || 1920 });
  defineProperty(scr, 'height', { get: () => profile.screen_height || 1080 });
  defineProperty(scr, 'availWidth', { get: () => profile.avail_width || profile.screen_width || 1920 });
  defineProperty(scr, 'availHeight', { get: () => profile.avail_height || (profile.screen_height ? profile.screen_height - (profile.extra_js_props?.screen_taskbar_height || 40) : 1040) });
  defineProperty(scr, 'colorDepth', { get: () => profile.color_depth || 24 });
  defineProperty(scr, 'pixelDepth', { get: () => profile.pixel_depth || 24 });
  defineProperty(scr, 'availLeft', { get: () => 0 }); // Meestal 0
  defineProperty(scr, 'availTop', { get: () => 0 });  // Meestal 0

  // Screen orientation (uitgebreider)
  // `profile.extra_js_props.screen_orientation` = { type: 'landscape-primary', angle: 0 }
  const screenOrientation = profile.extra_js_props?.screen_orientation || { type: 'landscape-primary', angle: 0 };
  if (scr.orientation) {
    defineProperty(scr.orientation, 'type', { get: () => screenOrientation.type });
    defineProperty(scr.orientation, 'angle', { get: () => screenOrientation.angle });
  } else {
    defineProperty(scr, 'orientation', { get: () => ({ type: screenOrientation.type, angle: screenOrientation.angle, onchange: null }) });
  }
  log('Screen properties gespooft (uitgebreid).');

  // Window geometry
  // `profile.extra_js_props.window_chrome_height` (bijv. 80)
  // `profile.extra_js_props.window_chrome_width` (bijv. 10)
  const chromeHeight = profile.extra_js_props?.window_chrome_height || 80;
  const chromeWidth = profile.extra_js_props?.window_chrome_width || 0; // Vaak 0 voor breedte, hangt af van OS
  defineProperty(window, 'outerWidth', { get: () => (profile.viewport_width || 1920) + chromeWidth });
  defineProperty(window, 'outerHeight', { get: () => (profile.viewport_height || 1080) + chromeHeight });
  defineProperty(window, 'innerWidth', { get: () => profile.viewport_width || 1920 }); // Moet matchen met viewport
  defineProperty(window, 'innerHeight', { get: () => profile.viewport_height || 1080 });// Moet matchen met viewport
  defineProperty(window, 'screenX', { get: () => 0 });
  defineProperty(window, 'screenY', { get: () => 0 });
  defineProperty(window, 'screenLeft', { get: () => 0 });
  defineProperty(window, 'screenTop', { get: () => 0 });


  // --- 10. Battery API Spoofing (Verfijnd) ---
  // `profile.extra_js_props.battery_info` = { charging: true, level: 1, chargingTime: 0, dischargingTime: Infinity }
  if (profile.extra_js_props?.spoof_battery !== false) { // Opt-out via profiel
    try {
        const defaultBatteryInfo = { charging: true, level: 1.0, chargingTime: 0, dischargingTime: Infinity };
        const batteryInfo = { ...defaultBatteryInfo, ...(profile.extra_js_props?.battery_info || {}) };
        // Zorg voor plausibele waarden
        if (!batteryInfo.charging && batteryInfo.dischargingTime === Infinity && batteryInfo.level < 1) {
            batteryInfo.dischargingTime = Math.floor(profileRand() * 10000 + 5000); // Random resterende tijd
        }
        if (batteryInfo.charging && batteryInfo.chargingTime === Infinity && batteryInfo.level < 1) {
            batteryInfo.chargingTime = Math.floor(profileRand() * 5000); // Random tijd tot vol
        }

        const batteryManager = {
            ...batteryInfo,
            onchargingchange: null, onchargingtimechange: null,
            ondischargingtimechange: null, onlevelchange: null
        };
        if (nav.getBattery) {
             defineProperty(navigator, 'getBattery', { value: () => Promise.resolve(batteryManager) });
        } else {
             defineProperty(navigator, "getBattery", {
                value: () => Promise.resolve(batteryManager),
                writable: true, enumerable: true
             });
        }
        log('navigator.getBattery gespooft (verfijnd).');
    } catch(e) { log('Battery API patching error:', e); }
  }

  // --- 11. JS Timezone & Locale Details (Intl API) ---
  // `profile.timezone` (bijv. "Europe/Rome")
  // `profile.locale` (bijv. "it-IT") - neem de primaire taalcode
  if (profile.timezone) {
    defineProperty(Date.prototype, 'getTimezoneOffset', {
      value: function() {
        // Dit is een simplificatie. Een accurate getTimezoneOffset vereist
        // kennis van de DST-regels voor de gespoofte timezone en de specifieke datum.
        // Voor veel detecties is een consistente, niet-UTC offset al een verbetering.
        // De `Intl` API is accurater voor daadwerkelijke formatting.
        const tzData = profile.extra_js_props?.timezone_offset_map; // { "Europe/Rome": -60 (winter), -120 (zomer)}
        if (tzData && tzData[profile.timezone]) return tzData[profile.timezone];
        // Fallback naar een generieke offset als geen map (of berekening)
        // Dit is niet ideaal, een lookup tabel per timezone in profile.extra_js_props is beter.
        if (profile.timezone === "Europe/Rome") return -60; // Hardcoded voorbeeld
        return 0; // Fallback UTC
      }
    });
    log(`Date.prototype.getTimezoneOffset (deels) gespooft voor timezone: ${profile.timezone}`);
  }

  if (Intl && typeof Intl.DateTimeFormat === 'function' && profile.timezone && profile.locale) {
    const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
    defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
      value: function() {
        const opts = originalResolvedOptions.call(this);
        opts.timeZone = profile.timezone;
        opts.locale = languages[0]; // Gebruik primaire taal van profiel
        // Optioneel: spoof ook calendar, numberingSystem indien nodig
        if (profile.extra_js_props?.intl_calendar) opts.calendar = profile.extra_js_props.intl_calendar;
        if (profile.extra_js_props?.intl_numberingSystem) opts.numberingSystem = profile.extra_js_props.intl_numberingSystem;
        return opts;
      }
    });
    log(`Intl.DateTimeFormat().resolvedOptions() gespooft voor timezone en locale.`);
  }

  // --- 12. MediaDevices Spoofing ---
  // `profile.extra_js_props.media_devices` = [{ deviceId: "...", kind: "audioinput", label: "...", groupId: "..."}, ...]
  if (navigator.mediaDevices && profile.extra_js_props?.media_devices) {
    const devices = profile.extra_js_props.media_devices.map(d => ({
        deviceId: d.deviceId || seededRandom(profile.name + d.kind + d.label).toString(36).substring(2, 15),
        kind: d.kind,
        label: d.label,
        groupId: d.groupId || seededRandom(profile.name + d.kind).toString(36).substring(2, 10),
        toJSON: function() { return { deviceId: this.deviceId, kind: this.kind, label: this.label, groupId: this.groupId }; }
    }));
    defineProperty(navigator.mediaDevices, 'enumerateDevices', {
      value: () => Promise.resolve(devices)
    });
    log('navigator.mediaDevices.enumerateDevices gespooft.');
  }

  // --- 13. CSS window.matchMedia Spoofing ---
  // `profile.extra_js_props.match_media_results` = { "(prefers-color-scheme: dark)": { matches: true, media: "(prefers-color-scheme: dark)" }, ... }
  if (window.matchMedia && profile.extra_js_props?.match_media_results) {
    const originalMatchMedia = window.matchMedia;
    const results = profile.extra_js_props.match_media_results;
    defineProperty(window, 'matchMedia', {
        value: (query) => {
            if (results[query]) {
                return { ...results[query], addListener: () => {}, removeListener: () => {} }; // Oude API
            }
            // Fallback naar default (of meer generieke spoofing als nodig)
            if (query === '(pointer: fine)') return {matches: !profile.extra_js_props?.maxTouchPoints, media: query};
            if (query === '(hover: hover)') return {matches: !profile.extra_js_props?.maxTouchPoints, media: query};
            return originalMatchMedia(query);
        }
    });
    log('window.matchMedia gespooft.');
  }

  // --- 14. SpeechSynthesis Voices ---
  // `profile.extra_js_props.speech_voices` = [{ name: "Google italiano", lang: "it-IT", localService: true, default: true, voiceURI: "..." }, ...]
  if (window.speechSynthesis && profile.extra_js_props?.speech_voices) {
    const voices = profile.extra_js_props.speech_voices.map(v => ({
        name: v.name, lang: v.lang, localService: v.localService !== false, default: v.default === true, voiceURI: v.voiceURI || v.name
    }));
    defineProperty(window.speechSynthesis, 'getVoices', { get: () => () => voices });
    log('speechSynthesis.getVoices gespooft.');
  }

  // --- 15. `history.length` ---
  // `profile.extra_js_props.history_length` (integer, bijv. 5)
  if (profile.extra_js_props?.history_length && window.history) {
    try {
        defineProperty(window.history, 'length', { get: () => profile.extra_js_props.history_length });
        log(`history.length gespooft naar ${profile.extra_js_props.history_length}.`);
    } catch(e) { log('Kon history.length niet spoofen:', e); }
  }

  // --- Overige bestaande patches (Automation flags, Error.toString, Worker, DPR) ---
  // Worker context: navigator.webdriver patch
  try {
    if (typeof WorkerGlobalScope === 'undefined' && typeof Worker !== 'undefined') { // Alleen voor main thread
        const workerFunc = `
            Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
            // Hier kunnen eventueel andere *lichtgewicht* patches voor de worker context komen
            // Maar pas op, te veel code hier kan de worker vertragen of problemen geven.
            postMessage('worker_webdriver_patched');
        `;
        const blob = new Blob([workerFunc], {type:'application/javascript'});
        const worker = new Worker(URL.createObjectURL(blob));
        worker.onmessage = (e) => { if(e.data === 'worker_webdriver_patched') log('Worker navigator.webdriver gepatcht.'); worker.terminate(); };
        worker.onerror = (e) => { log('Worker patching error:', e); worker.terminate(); };
        // Terminate worker if it takes too long, to prevent resource leaks
        setTimeout(() => { try { worker.terminate(); } catch(e){} }, 2000);
    }
  } catch (e) { log('Algemene Worker patching error:', e); }

  // Function.prototype.toString leakage
  const originalToString = Function.prototype.toString;
  const nativeToStringStr = String(originalToString); // Krijg de string representatie van de native toString

  defineProperty(Function.prototype, 'toString', {
    value: function() {
      // Lijst van functies die we specifiek willen maskeren
      const disguisedFunctions = [
        { func: navigator.getBattery, name: "getBattery"}, // Als gepatcht
        { func: navigator.permissions?.query, name: "query"}, // Als gepatcht
        // Voeg hier meer gepatchte functies toe indien nodig
      ];
      for(const df of disguisedFunctions){
          if(this === df.func) return `function ${df.name || ''}() { [native code] }`;
      }
      // Specifieke check voor webdriver getter
      const descriptor = Object.getOwnPropertyDescriptor(Navigator.prototype, 'webdriver');
      if (this === descriptor?.get) return 'function get webdriver() { [native code] }';

      return originalToString.apply(this, arguments);
    }
  });
  // Patch de toString van onze toString patch zelf om er native uit te zien
  defineProperty(Function.prototype.toString, 'toString', { value: () => nativeToStringStr });
  log('Function.prototype.toString gepatcht (verfijnd).');

  // Automation flags op window & documentElement
  const automationProps = [
    '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', '__fxdriver_evaluate',
    '__driver_unwrapped', '__webdriver_unwrapped', '__selenium_unwrapped', '__fxdriver_unwrapped',
    '_Selenium_IDE_Recorder', '_selenium', 'callSelenium', '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw',
    'driver', 'webdriver', 'selenium', 'calledSelenium', '$cdc_asdjflasutopfhvcZLmcfl_', // Common CDC flag
    '__lastWatirAlert', '__lastWatirConfirm', '__lastWatirPrompt', // Watir
  ];
  automationProps.forEach(prop => {
    if (window[prop]) delete window[prop];
    try { // navigator kan soms geen delete op sommige properties toestaan
      if (navigator[prop]) delete navigator[prop];
    } catch(e) {}
  });
  if (window.document && window.document.documentElement) {
    const attrsToRemove = ['selenium', 'webdriver', 'driver', 'safaridriver'];
    attrsToRemove.forEach(attr => {
        if(window.document.documentElement.hasAttribute(attr)) {
            window.document.documentElement.removeAttribute(attr);
        }
    });
    // Verwijder $cdc_ attributen van documentElement (vaak gebruikt door chromedriver)
    for (const attr of window.document.documentElement.attributes) {
        if (attr.name.startsWith('$cdc_')) {
            window.document.documentElement.removeAttribute(attr.name);
        }
    }
  }
  log('Common automation flags verwijderd/gepatcht (uitgebreid).');

  // Device Pixel Ratio
  // `profile.device_pixel_ratio` (float, bijv. 1.0, 1.5, 2.0)
  const dpr = profile.device_pixel_ratio || window.devicePixelRatio || 1.0;
  try {
    defineProperty(window, 'devicePixelRatio', { get: () => dpr });
    log('window.devicePixelRatio gespooft naar:', dpr);
  } catch (e) { log('Kon devicePixelRatio niet spoofen:', e); }

  // --- Einde Patches ---
  window.stealthPatchesApplied = true;
  window.stealthProfileName = profile.name || "N/A";
  log(`Stealth script volledig toegepast voor profiel: ${window.stealthProfileName}. Versie: Verbeterd 5.0`);
})();