
        // This runs before any page script
        const script = document.createElement('script');
        script.textContent = `
            // Remove all automation artifacts
            delete window.navigator.webdriver;
            delete window.__nightmare;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Perfect Chrome runtime emulation
            if (!window.chrome) window.chrome = {};
            window.chrome.runtime = {
                id: 'legitimate-extension-id',
                connect: () => { throw new Error('Extensions cannot connect to each other'); },
                sendMessage: () => { throw new Error('Extension context required'); }
            };
            
            // Akamai sensor data neutralization
            Object.defineProperty(document, 'hidden', {get: () => false});
            Object.defineProperty(document, 'visibilityState', {get: () => 'visible'});
            
            // Advanced fingerprint consistency
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(param) {
                // Stabilize WebGL fingerprint
                if (param === 37445) return 'Intel Inc.';  // UNMASKED_VENDOR_WEBGL
                if (param === 37446) return 'Intel Iris OpenGL Engine';  // UNMASKED_RENDERER_WEBGL
                return originalGetParameter.apply(this, arguments);
            };
            
            // Battery API
            if ('getBattery' in navigator) {
                navigator.getBattery = async () => ({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1.0,
                    addEventListener: () => {},
                    removeEventListener: () => {},
                    dispatchEvent: () => true
                });
            }
            
            // Consistent hardware properties
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
            Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 0 });
        `;
        document.documentElement.appendChild(script);
        script.remove();
        
        // Listen for commands from our Python controller
        window.addEventListener('message', (event) => {
            if (event.data.type === 'STEALTHMASTER_COMMAND') {
                chrome.runtime.sendMessage(event.data.payload);
            }
        });
        