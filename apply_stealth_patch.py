#!/usr/bin/env python3
"""
Stealth patch for FanSale bot - adds missing anti-detection features
"""

def get_stealth_script():
    """Returns the complete stealth JavaScript to inject"""
    return """
    // 1. Remove webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    // 2. Remove automation indicators
    ['__webdriver_evaluate', '__selenium_evaluate', '__webdriver_script_function',
     '__webdriver_script_func', '__webdriver_script_fn', '__fxdriver_evaluate',
     '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate',
     '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder',
     '_selenium', 'calledSelenium', '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw',
     'driver-evaluate', 'webdriver-evaluate', 'selenium-evaluate',
     'webdriverCommand', 'webdriver-evaluate-response', '__webdriverFunc',
     '__webdriver_script_fn', '__$webdriverAsyncExecutor', '__lastWatirAlert',
     '__lastWatirConfirm', '__lastWatirPrompt', '$chrome_asyncScriptInfo',
     '$cdc_asdjflasutopfhvcZLmcfl_'].forEach(prop => {
        delete window[prop];
        delete document[prop];
    });
    
    // 3. Fix Chrome runtime
    window.chrome = {
        runtime: {
            connect: () => {},
            sendMessage: () => {},
            onMessage: {
                addListener: () => {}
            }
        },
        loadTimes: function() {},
        csi: function() {},
        app: {}
    };
    
    // 4. Add plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {
                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf"},
                description: "Portable Document Format",
                filename: "internal-pdf-viewer",
                length: 1,
                name: "Chrome PDF Plugin"
            },
            {
                0: {type: "application/pdf", suffixes: "pdf"},
                description: "",
                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                length: 1,
                name: "Chrome PDF Viewer"
            }
        ]
    });
    
    // 5. Fix WebGL vendor/renderer
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter.apply(this, [parameter]);
    };
    
    // 6. Fix permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // 7. Fix navigator properties
    Object.defineProperty(navigator, 'languages', {
        get: () => ['it-IT', 'it', 'en-US', 'en']
    });
    
    Object.defineProperty(navigator, 'platform', {
        get: () => 'MacIntel'
    });
    
    // 8. Fix screen properties
    Object.defineProperty(screen, 'availTop', {get: () => 0});
    Object.defineProperty(screen, 'availLeft', {get: () => 0});
    
    // 9. Remove CDC properties
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    """

def apply_enhanced_stealth(driver):
    """Apply all stealth patches to a driver instance"""
    
    # 1. Inject main stealth script
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': get_stealth_script()
    })
    
    # 2. Override user agent properly
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": driver.execute_script("return navigator.userAgent").replace("Headless", "")
    })
    
    # 3. Set timezone to Italy
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
        'timezoneId': 'Europe/Rome'
    })
    
    # 4. Set geolocation (Milan, Italy)
    driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
        'latitude': 45.4642,
        'longitude': 9.1900,
        'accuracy': 100
    })
    
    # 5. Enable touch (mobile compatibility)
    driver.execute_cdp_cmd('Emulation.setTouchEmulationEnabled', {
        'enabled': False
    })
    
    return driver

if __name__ == "__main__":
    print("Stealth patch module loaded successfully!")
    print("\nUsage:")
    print("from apply_stealth_patch import apply_enhanced_stealth")
    print("driver = apply_enhanced_stealth(driver)")