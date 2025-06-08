# src/stealth/stealth_integration.py
"""
StealthMaster AI v3.0 - Stealth Integration Module
Consolidates all stealth measures for easy application
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any, List
from playwright.async_api import Browser, BrowserContext, Page, Playwright

from .advanced_fingerprint import AdvancedFingerprint
from .cdp_bypass_engine import CDPBypassEngine
from .ultra_stealth import UltraStealthEngine

logger = logging.getLogger(__name__)


class StealthIntegration:
    """Integrates stealth measures for undetectable browser automation"""
    
    @staticmethod
    async def create_stealth_browser(playwright: Playwright, headless: bool = True) -> Browser:
        """Create a browser with maximum stealth capabilities"""
        
        if not headless:
            logger.info("Running in headful mode for maximum stealth")
            
        # Launch with comprehensive anti-detection arguments
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-http2',
                '--force-http1',
                '--aggressive-cache-discard',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--password-store=basic',
                '--use-mock-keychain',
                '--force-color-profile=srgb',
                '--disable-features=UserAgentClientHint',
                '--window-size=1920,1080',
                '--start-maximized',
            ],
            ignore_default_args=['--enable-automation'],
            channel='chrome',  # Use real Chrome
        )
        
        return browser
        
    @staticmethod
    async def create_stealth_context(
        browser: Browser,
        proxy_config: Optional[Dict] = None,
        fingerprint: Optional[Dict[str, Any]] = None
    ) -> BrowserContext:
        """Create a context with all stealth measures applied"""
        
        # Use fingerprint data if provided, otherwise use defaults
        if fingerprint:
            viewport = fingerprint.get('viewport', {'width': 1920, 'height': 1080})
            user_agent = fingerprint.get('userAgent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            locale = fingerprint.get('locale', 'en-US')
            timezone = fingerprint.get('timezone', 'America/New_York')
        else:
            viewport = {'width': 1920, 'height': 1080}
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            locale = 'en-US'
            timezone = 'America/New_York'
        
        # Base context options
        context_options = {
            'viewport': viewport,
            'screen': {'width': viewport['width'], 'height': viewport['height']},
            'user_agent': user_agent,
            'locale': locale,
            'timezone_id': timezone,
            'permissions': ['geolocation', 'notifications'],
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},
            'color_scheme': 'light',
            'reduced_motion': 'no-preference',
            'forced_colors': 'none',
            'bypass_csp': True,
            'ignore_https_errors': True,
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': f'{locale},en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            }
        }
        
        # Add proxy if provided
        if proxy_config:
            context_options['proxy'] = proxy_config
            logger.info(f"Using proxy: {proxy_config.get('server')}")
        
        # Create context
        context = await browser.new_context(**context_options)
        
        # Add stealth scripts to all pages
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Mock chrome runtime
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {}
                }
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        logger.info("Created stealth context with advanced fingerprinting")
        return context
    
    @staticmethod
    async def apply_page_stealth(page: Page) -> None:
        """Apply comprehensive stealth measures to a page"""
        
        # 1. Apply UltraStealthEngine features
        await UltraStealthEngine.apply_ultra_stealth(page)
        
        # 2. Additional advanced anti-detection measures
        await page.add_init_script("""
        // StealthMaster AI v3.0 - Advanced Evasion
        (() => {
            // Override CDP detection
            if (window.chrome && window.chrome.runtime) {
                const originalSendMessage = window.chrome.runtime.sendMessage;
                window.chrome.runtime.sendMessage = function(...args) {
                    // Block CDP detection messages
                    if (args[0] && typeof args[0] === 'object' && args[0].cmd === 'CDP.detect') {
                        return;
                    }
                    return originalSendMessage.apply(this, args);
                };
            }
            
            // Advanced WebRTC leak prevention
            const webRTCValue = {
                candidate: "",
                sdpMLineIndex: 0,
                sdpMid: "",
                usernameFragment: null
            };
            
            Object.defineProperty(RTCIceCandidate.prototype, 'candidate', {
                get: function() {
                    return webRTCValue.candidate;
                }
            });
            
            const origRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(...args) {
                const pc = new origRTCPeerConnection(...args);
                pc.createDataChannel = new Proxy(pc.createDataChannel, {
                    apply: function(target, thisArg, argumentsList) {
                        return Reflect.apply(target, thisArg, argumentsList);
                    }
                });
                return pc;
            };
            window.RTCPeerConnection.prototype = origRTCPeerConnection.prototype;
            
            // Spoof hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 4 + Math.floor(Math.random() * 4) * 2, // 4, 6, 8, 10
                configurable: false
            });
            
            // Spoof device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => Math.pow(2, 2 + Math.floor(Math.random() * 3)), // 4, 8, 16
                configurable: false
            });
            
            // Override Intl.DateTimeFormat
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = new Proxy(originalDateTimeFormat, {
                construct(target, args) {
                    args[0] = 'en-US';
                    return new target(...args);
                }
            });
            
            // Prevent font fingerprinting
            const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth');
            const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
            
            Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
                ...originalOffsetWidth,
                get: function() {
                    const width = originalOffsetWidth.get.apply(this, arguments);
                    const isTestElement = this.id && this.id.includes('font-test');
                    if (isTestElement) {
                        return width + (Math.random() < 0.5 ? -1 : 1);
                    }
                    return width;
                }
            });
            
            // Spoof screen properties
            const screenProps = {
                availWidth: 1920,
                availHeight: 1040,
                width: 1920,
                height: 1080,
                colorDepth: 24,
                pixelDepth: 24,
                availLeft: 0,
                availTop: 40,
                orientation: {
                    angle: 0,
                    type: 'landscape-primary'
                }
            };
            
            for (const [prop, value] of Object.entries(screenProps)) {
                Object.defineProperty(screen, prop, {
                    get: () => value,
                    configurable: false
                });
            }
            
            // Override MediaDevices
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                navigator.mediaDevices.enumerateDevices = async () => {
                    return [
                        {
                            deviceId: "default",
                            kind: "audioinput",
                            label: "Default - Microphone",
                            groupId: crypto.randomUUID()
                        },
                        {
                            deviceId: "default",
                            kind: "audiooutput",
                            label: "Default - Speakers",
                            groupId: crypto.randomUUID()
                        }
                    ];
                };
            }
            
            // Timezone spoofing consistency
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return 300; // EST timezone offset
            };
            
            // Performance API noise
            const originalNow = performance.now;
            performance.now = function() {
                return originalNow.call(this) + (Math.random() * 0.01 - 0.005);
            };
        })();
        """)
        
        logger.debug("Applied comprehensive stealth measures with UltraStealthEngine integration")