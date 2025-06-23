"""
Advanced stealth improvements for StealthMaster
Implements cutting-edge anti-detection measures
"""

import random
import time
from typing import List, Dict


class StealthEnhancements:
    """Advanced stealth techniques to avoid detection"""
    
    @staticmethod
    def get_enhanced_chrome_options() -> List[str]:
        """Get comprehensive Chrome options for maximum stealth"""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-infobars',
            '--disable-gpu-sandbox',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--force-color-profile=srgb',
            '--disable-features=UserAgentClientHint',
            '--memory-pressure-off',
        ]
    
    @staticmethod
    def get_stealth_javascript() -> str:
        """JavaScript to inject for comprehensive stealth"""
        return """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Fix Chrome object
        if (!window.chrome) window.chrome = {};
        window.chrome.runtime = {
            connect: () => {},
            sendMessage: () => {},
            onMessage: { addListener: () => {} }
        };
        window.chrome.loadTimes = function() {
            return {
                requestTime: Date.now() / 1000 - 100,
                startLoadTime: Date.now() / 1000 - 50,
                commitLoadTime: Date.now() / 1000 - 30,
                finishDocumentLoadTime: Date.now() / 1000 - 10,
                finishLoadTime: Date.now() / 1000 - 5,
                navigationType: 'Other'
            };
        };
        
        // Fix navigator properties
        Object.defineProperty(navigator, 'plugins', {
            get: () => [{name: 'Chrome PDF Plugin'}, {name: 'Chrome PDF Viewer'}, {name: 'Native Client'}]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['it-IT', 'it', 'en-US', 'en']
        });
        
        Object.defineProperty(navigator, 'language', {
            get: () => 'it-IT'
        });
        
        // Canvas fingerprinting protection
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function() {
            const context = originalGetContext.apply(this, arguments);
            if (context && context.fillText) {
                const originalFillText = context.fillText;
                context.fillText = function() {
                    if (Math.random() < 0.01) {
                        context.fillStyle = 'rgba(0,0,0,0.01)';
                        context.fillRect(Math.random() * this.canvas.width, Math.random() * this.canvas.height, 1, 1);
                    }
                    return originalFillText.apply(this, arguments);
                };
            }
            return context;
        };
        
        // WebGL spoofing
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.apply(this, [parameter]);
        };
        
        // Remove automation indicators
        delete window.callPhantom;
        delete window._phantom;
        delete window.__webdriver_script_fn;
        delete window.$cdc_asdjflasutopfhvcZLmcfl_;
        
        console.log('%c✅ Stealth mode activated', 'color: green; font-weight: bold');
        """
    
    @staticmethod
    def random_mouse_movement(driver, duration: float = 1.0):
        """Perform random mouse movements to simulate human behavior"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            viewport_width = driver.execute_script("return window.innerWidth")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            x = random.randint(100, viewport_width - 100)
            y = random.randint(100, viewport_height - 100)
            
            driver.execute_script(f"""
                const event = new MouseEvent('mousemove', {{
                    clientX: {x},
                    clientY: {y},
                    bubbles: true
                }});
                document.dispatchEvent(event);
            """)
            
            time.sleep(random.uniform(0.1, 0.3))
    
    @staticmethod
    def random_scrolling(driver, duration: float = 0.5):
        """Perform random scrolling to simulate human behavior"""
        current_scroll = driver.execute_script("return window.pageYOffset")
        max_scroll = driver.execute_script("return document.body.scrollHeight - window.innerHeight")
        
        if max_scroll > 0:
            target_scroll = current_scroll + random.randint(-200, 200)
            target_scroll = max(0, min(target_scroll, max_scroll))
            
            driver.execute_script(f"""
                window.scrollTo({{
                    top: {target_scroll},
                    behavior: 'smooth'
                }});
            """)
            time.sleep(duration)
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Get a random realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)
