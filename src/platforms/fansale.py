# src/platforms/fansale.py - STEALTHMASTER AI ENHANCED v7.0 
from __future__ import annotations

import asyncio
import logging
import random
import re
import time
import json
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import Page, BrowserContext, Error as PlaywrightError

# Core imports
from ..core.models import EnhancedTicketOpportunity, DataUsageTracker
from ..core.enums import PlatformType, PriorityLevel
from ..profiles.models import BrowserProfile
from ..core.errors import BlockedError, PlatformError

# StealthMaster AI Integration
from ..core.stealth.stealth_integration import get_bruce_stealth_integration

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

class FansaleMonitor:
    """🎸 STEALTHMASTER AI ENHANCED - Revolutionary Fansale monitor with ultimate stealth"""
    
    def __init__(self, config: Dict[str, Any], profile: BrowserProfile, 
                 browser_manager, connection_manager, cache):
        self.config = config
        self.profile = profile
        self.browser_manager = browser_manager
        self.connection_manager = connection_manager
        self.cache = cache
        
        # Target configuration
        self.event_name = config.get('event_name', 'Unknown Event')
        self.url = config['url']
        self.priority = PriorityLevel[config.get('priority', 'NORMAL').upper()]
        self.max_price = config.get('max_price_per_ticket', 1000.0)
        self.desired_sections = config.get('desired_sections', [])
        self.fair_deal_only = config.get('fair_deal_only', False)
        self.certified_only = config.get('certified_only', False)
        
        # State management
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.last_check = None
        self.detected_offers = set()
        
        # 🛡️ StealthMaster AI Integration
        self.stealth_integration = get_bruce_stealth_integration()
        self.session_id: Optional[str] = None
        
        # Advanced selectors based on HTML analysis
        self.selectors = {
            'offer_containers': [
                'div.EventEntry.js-EventEntry',
                'div[data-offer-id]',
                '.EventEntry-isClickable',
                '.OfferEntry'
            ],
            'no_tickets': [
                'text=Nessun biglietto disponibile',
                'text=Sold Out',
                'text=Esaurito',
                '.no-offers-message',
                '.sold-out'
            ],
            'price_elements': [
                '.OfferEntry-PriceSmall .moneyValueFormat',
                '.CurrencyAndMoneyValueFormat .moneyValueFormat',
                'span.moneyValueFormat',
                '.price-value'
            ],
            'currency_elements': [
                '.OfferEntry-PriceSmall .currencyFormat',
                '.CurrencyAndMoneyValueFormat .currencyFormat',
                'span.currencyFormat'
            ],
            'section_elements': [
                '.OfferEntry-SeatDescription',
                '[data-seatdescriptionforarialabel]',
                '.seat-description',
                '.section-info'
            ],
            'quantity_elements': [
                '.NumberOfTicketsInOffer',
                '[data-splitting-possibilities]',
                '.ticket-quantity'
            ],
            'offer_type_elements': [
                '.OfferEntry-PurchaseTypeAndPrice span[title]',
                '[data-offertype]',
                '.offer-type'
            ],
            'buy_button': [
                '.Button-inOfferEntryList',
                'a[data-track][role="button"]',
                '.js-Button-inOfferEntryList',
                '.purchase-button'
            ],
            'fair_deal_indicator': [
                '.FairDealIcon.js-FairDealIcon',
                '[data-fairdeal="true"]',
                '.fair-deal-icon'
            ],
            'certified_indicator': [
                '.TicketcheckIcon.js-TicketcheckIcon',
                '[data-certified="true"]',
                '.ticketcheck-icon'
            ],
            'loading_indicators': [
                '.loading-spinner',
                '.loader',
                '.sk-circle'
            ]
        }
        
        # 🥷 STEALTHMASTER AI REAL-TIME EFFECTIVENESS TRACKER
        self.stealth_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'blocked_requests': 0,
            'captcha_encounters': 0,
            'recovery_attempts': 0,
            'successful_recoveries': 0,
            'average_response_time': 0.0,
            'stealth_effectiveness': 100.0,
            'last_detection': None,
            'consecutive_successes': 0,
            'risk_level': 'LOW',
            'session_start': datetime.now(),
            'fingerprint_changes': 0,
            'proxy_rotations': 0
        }
        
        logger.info(f"FansaleMonitor initialized for {self.event_name}")
        logger.info(f"🥷 StealthMaster AI Tracker: ACTIVE")

    async def initialize(self):
        """🛡️ STEALTHMASTER AI ENHANCED - Initialize with ultimate anti-detection"""
        try:
            from ..utils.live_status_logger import (
                log_browser_status, 
                start_operation, 
                update_operation_progress,
                complete_operation,
                log_auth_status,
                get_live_status_logger
            )
            
            # Initialize StealthMaster AI with live status integration
            live_logger = get_live_status_logger()
            self.stealth_integration = get_bruce_stealth_integration(live_logger)
            
            # Initialize detection monitoring
            from ..core.detection_monitor import get_detection_monitor, DetectionEventType
            self.detection_monitor = get_detection_monitor()
            
            start_operation("fansale_stealthmaster_init", f"🛡️ StealthMaster AI: Initializing FanSale for {self.event_name}", 25.0)
            
            logger.critical("🚀 STEALTHMASTER AI FANSALE INITIALIZATION STARTING")
            logger.critical(f"   📋 Event: {self.event_name}")
            logger.critical(f"   🌐 URL: {self.url}")
            logger.critical(f"   👤 Profile: {getattr(self.profile, 'profile_id', 'unknown')}")
            logger.critical("   🛡️ STEALTHMASTER AI PROTECTION ACTIVE")
            
            update_operation_progress("fansale_stealthmaster_init", 30.0, "Creating StealthMaster AI context...")
            log_browser_status("🛡️ StealthMaster AI: Creating FanSale context", True)
            
            # Convert BrowserProfile to legacy format for StealthEngine
            legacy_profile = {
                'id': getattr(self.profile, 'profile_id', 'fansale_profile'),
                'device_type': 'desktop',  # FanSale optimized for desktop
                'os': getattr(self.profile, 'os', 'Windows 11'),
                'browser': getattr(self.profile, 'browser_name', 'Chrome'),
                'browser_version': getattr(self.profile, 'browser_version', '121.0.6167.85'),
                'screen_width': getattr(self.profile, 'screen_width', 1920),
                'screen_height': getattr(self.profile, 'screen_height', 1080),
                'viewport_width': getattr(self.profile, 'viewport_width', 1820),
                'viewport_height': getattr(self.profile, 'viewport_height', 930),
                'hardware_concurrency': getattr(self.profile, 'hardware_concurrency', 8),
                'device_memory': getattr(self.profile, 'device_memory', 16),
                'user_agent': self.profile.user_agent,
                'locale': 'it-IT',  # FanSale is Italian platform
                'languages': ['it-IT', 'it', 'en-US', 'en'],
                'timezone': 'Europe/Rome',
                'gpu_vendor': getattr(self.profile, 'gpu_vendor', 'NVIDIA'),
                'gpu_model': getattr(self.profile, 'gpu_model', 'GeForce RTX 3060')
            }
            
            update_operation_progress("fansale_stealthmaster_init", 50.0, "Applying advanced anti-detection...")
            
            # 🛡️ CREATE STEALTHMASTER AI PROTECTED BROWSER CONTEXT
            logger.critical("   🛡️ Creating StealthMaster AI protected context...")
            self.browser_context = await self.stealth_integration.create_stealth_browser_context(
                browser=self.browser_manager.browser,
                legacy_profile=legacy_profile,
                platform="fansale"
            )
            
            # Extract session ID for tracking
            session_stats = self.stealth_integration.get_all_session_stats()
            if session_stats:
                self.session_id = session_stats[-1]['session_id']
                logger.critical(f"   ✅ StealthMaster AI Session: {self.session_id}")
            
            log_browser_status("🛡️ StealthMaster AI context created successfully", True)
            
            update_operation_progress("fansale_stealthmaster_init", 70.0, "Creating protected browser page...")
            
            # Create page with StealthMaster AI protection
            logger.info("   📄 Creating StealthMaster AI protected page...")
            self.page = await self.browser_context.new_page()
            logger.info("   ✅ Protected browser page created successfully")
            log_browser_status("Protected browser page created successfully", True)
            
            # Additional FanSale-specific enhancements
            logger.info("   🇮🇹 Applying FanSale-specific optimizations...")
            await self._setup_intelligent_blocking()
            await self._configure_advanced_behavior()
            await self._setup_api_monitoring()
            logger.info("   ✅ FanSale optimizations applied successfully")
            
            update_operation_progress("fansale_stealthmaster_init", 85.0, "Performing StealthMaster AI authentication...")
            
            # Perform authentication with StealthMaster AI protection
            logger.critical("   🔐 STARTING STEALTHMASTER AI ENHANCED AUTHENTICATION...")
            auth_success = await self._perform_authentication()
            if auth_success:
                logger.critical("   🎉 FANSALE AUTHENTICATION SUCCESSFUL!")
                log_auth_status("FanSale", True, {"event": self.event_name})
            else:
                logger.error("   ❌ FANSALE AUTHENTICATION FAILED!")
                log_auth_status("FanSale", False, {"event": self.event_name})
            
            complete_operation("fansale_init", auth_success, 
                              f"FanSale ready for {self.event_name}" if auth_success else "FanSale initialization failed")
            
            logger.critical("🎯 FANSALE BROWSER READY FOR TICKET HUNTING!")
            logger.critical("   👀 Browser windows should now be visible")
            logger.critical("   🔍 Watch for authentication and ticket detection")
            log_browser_status(f"FanSale ready for ticket hunting: {self.event_name}", True)
            
        except Exception as e:
            logger.error(f"💥 FAILED TO INITIALIZE FANSALE BROWSER: {e}")
            raise

    async def _inject_fansale_stealth(self):
        """Inject Fansale-specific anti-detection measures"""
        await self.page.add_init_script("""
        // Ultimate Fansale stealth package
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Advanced canvas fingerprinting protection
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            if (type === '2d') {
                const context = originalGetContext.call(this, type, ...args);
                if (context) {
                    // Sophisticated noise injection
                    const originalFillText = context.fillText;
                    context.fillText = function(text, x, y, maxWidth) {
                        const noise = () => (Math.random() - 0.5) * 0.0001;
                        return originalFillText.call(this, text, x + noise(), y + noise(), maxWidth);
                    };
                    
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function(sx, sy, sw, sh) {
                        const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
                        const data = imageData.data;
                        
                        // Add Gaussian noise to 0.001% of pixels
                        for (let i = 0; i < data.length; i += 4) {
                            if (Math.random() < 0.00001) {
                                const noise = Math.floor((Math.random() - 0.5) * 4);
                                data[i] = Math.max(0, Math.min(255, data[i] + noise));
                                data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                                data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                            }
                        }
                        return imageData;
                    };
                }
                return context;
            }
            return originalGetContext.call(this, type, ...args);
        };
        
        // Dynamic screen properties with realistic variations
        const originalScreen = screen;
        Object.defineProperty(window, 'screen', {
            get: () => new Proxy(originalScreen, {
                get: (target, prop) => {
                    if (prop === 'availHeight') {
                        return target.availHeight + Math.floor((Math.random() - 0.5) * 8);
                    }
                    if (prop === 'width' || prop === 'height') {
                        return target[prop] + Math.floor((Math.random() - 0.5) * 4);
                    }
                    if (prop === 'colorDepth') {
                        return [16, 24, 32][Math.floor(Math.random() * 3)];
                    }
                    return target[prop];
                }
            })
        });
        
        // Advanced plugin array with realistic entries
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    {
                        name: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        description: 'Portable Document Format'
                    },
                    {
                        name: 'Chromium PDF Plugin', 
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        description: 'Portable Document Format'
                    },
                    {
                        name: 'Microsoft Edge PDF Plugin',
                        filename: 'pdf',
                        description: 'pdf'
                    }
                ];
                
                // Add refresh method
                plugins.refresh = () => {};
                plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                
                return plugins;
            }
        });
        
        // Hardware concurrency randomization
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => [2, 4, 6, 8, 12, 16][Math.floor(Math.random() * 6)]
        });
        
        // Device memory spoofing
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => [2, 4, 6, 8][Math.floor(Math.random() * 4)]
        });
        
        // Language array randomization
        const languages = ['it-IT', 'it', 'en-US', 'en'];
        Object.defineProperty(navigator, 'languages', {
            get: () => {
                const shuffled = [...languages];
                for (let i = shuffled.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
                }
                return shuffled.slice(0, 2 + Math.floor(Math.random() * 3));
            }
        });
        
        // Performance timing protection
        const originalPerformanceNow = performance.now;
        performance.now = function() {
            return originalPerformanceNow.call(this) + (Math.random() - 0.5) * 0.001;
        };
        
        // Memory usage simulation
        if (performance.memory) {
            const baseUsed = Math.floor(Math.random() * 20000000) + 30000000;
            Object.defineProperty(performance.memory, 'usedJSHeapSize', {
                get: () => baseUsed + Math.floor((Math.random() - 0.5) * 2000000)
            });
            
            Object.defineProperty(performance.memory, 'totalJSHeapSize', {
                get: () => performance.memory.usedJSHeapSize + Math.floor(Math.random() * 10000000)
            });
        }
        
        // WebRTC protection
        if (window.RTCPeerConnection) {
            const originalCreateDataChannel = RTCPeerConnection.prototype.createDataChannel;
            RTCPeerConnection.prototype.createDataChannel = function() {
                throw new Error('WebRTC disabled for privacy');
            };
        }
        
        // Battery API realistic simulation
        if (navigator.getBattery) {
            navigator.getBattery = async () => ({
                charging: Math.random() > 0.3,
                chargingTime: Math.random() > 0.5 ? 0 : Math.random() * 3600,
                dischargingTime: Math.random() * 28800 + 3600,
                level: 0.2 + Math.random() * 0.8,
                onchargingchange: null,
                onchargingtimechange: null,
                ondischargingtimechange: null,
                onlevelchange: null
            });
        }
        
        // User activation simulation
        Object.defineProperty(navigator, 'userActivation', {
            get: () => ({
                hasBeenActive: true,
                isActive: Math.random() > 0.2
            })
        });
        
        console.log('🛡️ Fansale ultra-stealth package loaded');
        """)

    async def _setup_intelligent_blocking(self):
        """Setup intelligent resource blocking for speed and stealth"""
        await self.page.route('**/*', self._handle_request)

    async def _handle_request(self, route):
        """Intelligent request handling with optimization"""
        request = route.request
        url = request.url
        resource_type = request.resource_type
        
        # Always allow Fansale core requests
        if any(domain in url for domain in ['fansale.it', 'fansale.de', 'fansale.com', 'eventim.de']):
            await route.continue_()
            return
        
        # Block unnecessary resources for speed
        if resource_type in ['image', 'media', 'font']:
            if not any(x in url for x in ['logo', 'icon', 'favicon', 'avatar']):
                await route.abort()
                return
        
        # Block tracking and analytics (stealth)
        tracking_patterns = [
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
            'facebook.com', 'connect.facebook.net', 'hotjar.com',
            'mixpanel.com', 'segment.com', 'amplitude.com', 'quantcast.com',
            'scorecardresearch.com', 'outbrain.com', 'taboola.com'
        ]
        
        if any(pattern in url for pattern in tracking_patterns):
            await route.abort()
            return
        
        # Block ads
        ad_patterns = [
            'googlesyndication.com', 'adsystem.com', 'adsense.com',
            'amazon-adsystem.com', 'media.net', 'criteo.com'
        ]
        
        if any(pattern in url for pattern in ad_patterns):
            await route.abort()
            return
        
        # Continue with request
        await route.continue_()

    async def _configure_advanced_behavior(self):
        """Configure advanced human-like behavior simulation"""
        # Set realistic viewport
        await self.page.set_viewport_size({
            'width': self.profile.viewport_width,
            'height': self.profile.viewport_height
        })
        
        # Add behavior tracking
        await self.page.add_init_script("""
        // Advanced behavior simulation
        let behaviorMetrics = {
            mouseMovements: 0,
            clicks: 0,
            scrolls: 0,
            keystrokes: 0,
            focusChanges: 0,
            startTime: Date.now(),
            lastActivity: Date.now()
        };
        
        // Event listeners for behavior tracking
        document.addEventListener('mousemove', (e) => {
            behaviorMetrics.mouseMovements++;
            behaviorMetrics.lastActivity = Date.now();
        });
        
        document.addEventListener('click', (e) => {
            behaviorMetrics.clicks++;
            behaviorMetrics.lastActivity = Date.now();
        });
        
        document.addEventListener('scroll', (e) => {
            behaviorMetrics.scrolls++;
            behaviorMetrics.lastActivity = Date.now();
        });
        
        document.addEventListener('keydown', (e) => {
            behaviorMetrics.keystrokes++;
            behaviorMetrics.lastActivity = Date.now();
        });
        
        document.addEventListener('focus', () => behaviorMetrics.focusChanges++);
        document.addEventListener('blur', () => behaviorMetrics.focusChanges++);
        
        window.getBehaviorMetrics = () => ({
            ...behaviorMetrics,
            sessionDuration: Date.now() - behaviorMetrics.startTime,
            timeSinceLastActivity: Date.now() - behaviorMetrics.lastActivity
        });
        """)

    async def _setup_api_monitoring(self):
        """Setup API response monitoring for ticket data"""
        async def handle_response(response):
            try:
                url = response.url
                
                # Monitor Fansale API endpoints
                if ('fansale' in url or 'eventim' in url) and response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/json' in content_type:
                        try:
                            data = await response.json()
                            await self._process_api_response(url, data)
                        except Exception as e:
                            logger.debug(f"Error parsing JSON from {url}: {e}")
            
            except Exception as e:
                logger.debug(f"Error handling response: {e}")
        
        self.page.on('response', handle_response)

    async def _process_api_response(self, url: str, data: dict):
        """Process API responses for ticket data"""
        try:
            # Look for offer data in API responses
            if isinstance(data, dict):
                # Check for offers array
                if 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, list):
                        logger.debug(f"Found {len(offers)} offers in API response")
                
                # Check for embedded data
                if 'data' in data and isinstance(data['data'], dict):
                    embedded_data = data['data']
                    if 'offers' in embedded_data:
                        logger.debug(f"Found embedded offers in API response")
        
        except Exception as e:
            logger.debug(f"Error processing API response: {e}")

    async def _handle_blocked_response(self, response_status: int = None, page_content: str = "") -> bool:
        """Handle blocked responses and implement recovery strategies"""
        try:
            logger.warning(f"🚫 Handling blocked response: status={response_status}")
            
            # 🛡️ ENHANCED FANSALE-SPECIFIC BLOCKING PATTERNS
            blocking_indicators = [
                # Standard blocking patterns
                'blocked', 'forbidden', 'access denied', 'not authorized',
                'captcha', 'robot', 'bot', 'verification', 'security check',
                'too many requests', 'rate limit', 'banned', 'suspended',
                
                # FanSale-specific patterns (Italian + English)
                'accesso negato', 'accesso bloccato', 'troppi tentativi',
                'verifica richiesta', 'controllo sicurezza', 'sessione scaduta',
                'account sospeso', 'attività sospetta', 'riprova più tardi',
                'temporarily unavailable', 'service unavailable',
                'unusual activity', 'automated traffic', 'please wait',
                
                # Advanced detection patterns
                'cloudflare', 'ddos-guard', 'incapsula', 'imperva',
                'challenge', 'checking your browser', 'moment please',
                'enable javascript', 'enable cookies', 'security check',
                'human verification', 'prove you are human'
            ]
            
            content_lower = page_content.lower()
            is_blocked = any(indicator in content_lower for indicator in blocking_indicators)
            
            # Status code based detection
            if response_status in [403, 429, 503, 521, 525]:
                is_blocked = True
            
            if is_blocked:
                logger.error(f"🛑 FanSale blocking detected! Status: {response_status}")
                
                # Mark profile as potentially compromised
                if hasattr(self.profile, 'record_usage'):
                    self.profile.record_usage(
                        success=False, 
                        platform="fansale", 
                        error=f"Blocked (HTTP {response_status})",
                        detected=True
                    )
                
                # Implement recovery strategies
                recovery_success = await self._attempt_blocking_recovery()
                
                # If recovery failed, trigger profile rotation
                if not recovery_success and hasattr(self.connection_manager, 'mark_client_compromised'):
                    await self.connection_manager.mark_client_compromised(self.profile)
                    logger.warning("🔄 Marked FanSale profile for rotation due to blocking")
                
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling blocked response: {e}")
            return False
    
    async def _attempt_blocking_recovery(self) -> bool:
        """Attempt to recover from blocking situation"""
        try:
            logger.info("🔄 Attempting FanSale blocking recovery...")
            
            # Strategy 1: Clear cookies and restart session
            if self.page:
                await self.page.context.clear_cookies()
                logger.info("Cleared FanSale cookies")
            
            # Strategy 2: Wait with human-like delay
            wait_time = random.uniform(30, 90)  # 30-90 seconds
            logger.info(f"Waiting {wait_time:.1f}s for FanSale cooldown...")
            await asyncio.sleep(wait_time)
            
            # Strategy 3: Navigate to main page to reset session
            if self.page:
                await self.page.goto("https://www.fansale.it/", 
                                   wait_until='networkidle', 
                                   timeout=30000)
                await asyncio.sleep(random.uniform(2, 5))
            
            # Strategy 4: Check if recovery was successful
            recovery_test = await self._test_fansale_access()
            
            if recovery_test:
                logger.info("✅ FanSale blocking recovery successful")
                return True
            else:
                logger.warning("❌ FanSale blocking recovery failed")
                return False
                
        except Exception as e:
            logger.error(f"FanSale recovery attempt failed: {e}")
            return False
    
    async def _test_fansale_access(self) -> bool:
        """Test if FanSale access is restored"""
        try:
            if not self.page:
                return False
            
            # Try to access a simple FanSale page
            start_time = time.time()
            response = await self.page.goto("https://www.fansale.it/", 
                                          wait_until='domcontentloaded',
                                          timeout=15000)
            load_time = (time.time() - start_time) * 1000
            
            if response and response.status < 400:
                # Check page content for blocking indicators
                content = await self.page.content()
                
                # Check for various blocking indicators
                blocked_indicators = ['blocked', 'forbidden', 'access denied', 'bot detected']
                captcha_indicators = ['captcha', 'recaptcha', 'challenge']
                queue_indicators = ['queue', 'waiting room', 'please wait']
                
                is_blocked = any(indicator in content.lower() for indicator in blocked_indicators)
                has_captcha = any(indicator in content.lower() for indicator in captcha_indicators)
                in_queue = any(indicator in content.lower() for indicator in queue_indicators)
                
                # Log detection event
                if is_blocked:
                    self.detection_monitor.log_event(
                        event_type=DetectionEventType.ACCESS_DENIED,
                        platform="fansale",
                        profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                        success=False,
                        details={"reason": "blocked", "status_code": response.status, "load_time_ms": load_time}
                    )
                elif has_captcha:
                    self.detection_monitor.log_event(
                        event_type=DetectionEventType.CAPTCHA_TRIGGERED,
                        platform="fansale",
                        profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                        success=False,
                        details={"status_code": response.status, "load_time_ms": load_time}
                    )
                elif in_queue:
                    self.detection_monitor.log_event(
                        event_type=DetectionEventType.QUEUE_ENTERED,
                        platform="fansale",
                        profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                        success=False,
                        details={"status_code": response.status, "load_time_ms": load_time}
                    )
                else:
                    # Successful access
                    self.detection_monitor.log_event(
                        event_type=DetectionEventType.ACCESS_GRANTED,
                        platform="fansale",
                        profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                        success=True,
                        details={"status_code": response.status, "load_time_ms": load_time}
                    )
                
                is_accessible = not (is_blocked or has_captcha or in_queue)
                return is_accessible
            
            return False
            
        except Exception as e:
            logger.debug(f"FanSale access test failed: {e}")
            return False
    
    async def _detect_captcha_or_verification(self) -> bool:
        """Detect if FanSale is showing captcha or verification challenges"""
        try:
            if not self.page:
                return False
            
            # Common captcha/verification selectors
            captcha_selectors = [
                'iframe[src*="captcha"]', 'iframe[src*="recaptcha"]',
                '.captcha', '.recaptcha', '.hcaptcha',
                '[data-captcha]', '[id*="captcha"]',
                'text=Verify you are human', 'text=Security check',
                'text=Verifica di sicurezza', 'text=Controllo sicurezza'
            ]
            
            for selector in captcha_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.count() > 0:
                        logger.warning(f"🤖 FanSale captcha/verification detected: {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue
            
            # Check page title and content
            try:
                title = await self.page.title()
                if any(word in title.lower() for word in ['captcha', 'verification', 'security']):
                    logger.warning(f"🤖 FanSale verification in title: {title}")
                    return True
            except Exception as e:
                logger.debug(f"Error in exception handler: {e}")
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Captcha detection error: {e}")
            return False

    async def _perform_authentication(self):
        """Perform FanSale authentication to access protected content"""
        try:
            # 🔐 STEALTHMASTER AI AUTHENTICATION PROTOCOL
            logger.info("🔐 INITIATING FANSALE AUTHENTICATION PROTOCOL")
            
            # Load credentials from environment
            import os
            email = os.getenv('FANSALE_EMAIL')
            password = os.getenv('FANSALE_PASSWORD')
            
            if not email or not password:
                logger.error("❌ AUTHENTICATION FAILED: Missing credentials")
                logger.error("   💡 Set FANSALE_EMAIL and FANSALE_PASSWORD in .env file")
                return False
            
            # Log credential status (safely)
            logger.info(f"   📧 Email: {email[:3]}***@{email.split('@')[1] if '@' in email else '???'}")
            logger.info(f"   🔑 Password: {'*' * len(password)} ({len(password)} chars)")
            
            # Navigate to login page with stealth
            logger.info("   🎭 Navigating to login page with stealth protocols...")
            auth_start = time.time()
            await self._navigate_to_login_page()
            
            # Perform login process with detailed tracking
            logger.info("   🚀 Executing automated login sequence...")
            login_success = await self._execute_login(email, password)
            
            auth_time = time.time() - auth_start
            
            if login_success:
                logger.critical("🎉 FANSALE AUTHENTICATION SUCCESS!")
                logger.critical(f"   ⏱️  Login completed in {auth_time:.2f}s")
                logger.critical(f"   🎫 Ready for ticket acquisition operations")
                
                # Record successful authentication
                if hasattr(self.profile, 'record_usage'):
                    self.profile.record_usage(
                        success=True,
                        platform="fansale_auth",
                        response_time_ms=int(auth_time * 1000),
                        detected=False
                    )
                return True
            else:
                logger.error("❌ FANSALE AUTHENTICATION FAILED")
                logger.error(f"   ⏱️  Failed after {auth_time:.2f}s")
                logger.error("   🔧 Check credentials or account status")
                
                # Record failed authentication
                if hasattr(self.profile, 'record_usage'):
                    self.profile.record_usage(
                        success=False,
                        platform="fansale_auth",
                        error="Login failed",
                        response_time_ms=int(auth_time * 1000),
                        detected=False
                    )
                return False
                
        except Exception as e:
            logger.error(f"🚨 AUTHENTICATION PROTOCOL ERROR: {e}")
            logger.error("   🔧 This may indicate a blocking or detection issue")
            return False

    async def _navigate_to_login_page(self):
        """Navigate to FanSale login page with human behavior"""
        try:
            # First visit main page to establish session
            await self.page.goto("https://www.fansale.it/", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            # Look for login link/button
            login_selectors = [
                'a[href*="/login"]',
                'a[href*="/accedi"]', 
                'button:text("Accedi")',
                'a:text("Accedi")',
                '.login-link',
                '.user-login',
                '#login-button'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_element = self.page.locator(selector).first
                    if await login_element.count() and await login_element.is_visible():
                        # Scroll to and click login
                        await login_element.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        await login_element.click()
                        login_clicked = True
                        logger.debug(f"Clicked login using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Login selector {selector} failed: {e}")
                    continue
            
            if not login_clicked:
                # Direct navigation to login page as fallback
                await self.page.goto("https://www.fansale.it/login", wait_until='networkidle', timeout=30000)
            
            # Wait for login page to load
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            logger.debug("Successfully navigated to FanSale login page")
            
        except Exception as e:
            logger.error(f"Failed to navigate to login page: {e}")
            raise

    async def _execute_login(self, email: str, password: str) -> bool:
        """Execute the login process with human-like behavior"""
        try:
            # Wait for login form to be visible
            await self._wait_for_login_form()
            
            # Fill email field
            email_filled = await self._fill_email_field(email)
            if not email_filled:
                logger.error("Failed to fill email field")
                return False
            
            # Fill password field
            password_filled = await self._fill_password_field(password)
            if not password_filled:
                logger.error("Failed to fill password field")
                return False
            
            # Submit form
            submitted = await self._submit_login_form()
            if not submitted:
                logger.error("Failed to submit login form")
                return False
            
            # Verify login success
            return await self._verify_login_success()
            
        except Exception as e:
            logger.error(f"Login execution failed: {e}")
            return False

    async def _wait_for_login_form(self):
        """Wait for login form elements to be available"""
        form_selectors = [
            'form[action*="login"]',
            'form#login-form',
            '.login-form',
            'form:has(input[type="email"], input[type="password"])'
        ]
        
        for selector in form_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=10000)
                logger.debug(f"Login form found with selector: {selector}")
                return
            except:
                continue
        
        # Fallback - just wait for email/password inputs
        await self.page.wait_for_selector('input[type="email"], input[name*="email"]', timeout=10000)

    async def _fill_email_field(self, email: str) -> bool:
        """Fill email field with human-like typing"""
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[id*="email"]',
            'input[placeholder*="email"]',
            'input[placeholder*="Email"]'
        ]
        
        for selector in email_selectors:
            try:
                email_field = self.page.locator(selector).first
                if await email_field.count() and await email_field.is_visible():
                    # Clear field first
                    await email_field.click()
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await email_field.clear()
                    
                    # Type email with realistic timing
                    await self._type_with_human_timing(email_field, email)
                    logger.debug(f"Successfully filled email field: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Email field {selector} failed: {e}")
                continue
        
        return False

    async def _fill_password_field(self, password: str) -> bool:
        """Fill password field with human-like typing"""
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[id*="password"]',
            'input[placeholder*="password"]',
            'input[placeholder*="Password"]'
        ]
        
        for selector in password_selectors:
            try:
                password_field = self.page.locator(selector).first
                if await password_field.count() and await password_field.is_visible():
                    # Clear field first
                    await password_field.click()
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await password_field.clear()
                    
                    # Type password with realistic timing
                    await self._type_with_human_timing(password_field, password)
                    logger.debug(f"Successfully filled password field: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Password field {selector} failed: {e}")
                continue
        
        return False

    async def _type_with_human_timing(self, element, text: str):
        """Type text with human-like timing and occasional corrections"""
        for i, char in enumerate(text):
            # Realistic typing speed with variation
            delay = random.uniform(0.05, 0.15)
            
            # Occasional slower typing (thinking)
            if random.random() < 0.1:
                delay += random.uniform(0.2, 0.5)
            
            await element.type(char, delay=delay * 1000)
            
            # Very rare typing mistakes (backspace + retype)
            if random.random() < 0.02 and i > 0:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await element.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.2))
                await element.type(char, delay=delay * 1000)

    async def _submit_login_form(self) -> bool:
        """Submit login form with multiple strategies"""
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:text("Accedi")',
            'button:text("Login")',
            'button:text("Entra")',
            '.login-button',
            '.submit-button',
            'form button:last-child'
        ]
        
        # Try clicking submit button
        for selector in submit_selectors:
            try:
                submit_button = self.page.locator(selector).first
                if await submit_button.count() and await submit_button.is_visible():
                    await submit_button.scroll_into_view_if_needed()
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    await submit_button.click()
                    logger.debug(f"Clicked submit button: {selector}")
                    
                    # Wait for navigation/response
                    await self.page.wait_for_load_state('networkidle', timeout=15000)
                    return True
            except Exception as e:
                logger.debug(f"Submit button {selector} failed: {e}")
                continue
        
        # Fallback: try Enter key on password field
        try:
            password_field = self.page.locator('input[type="password"]').first
            if await password_field.count():
                await password_field.press('Enter')
                await self.page.wait_for_load_state('networkidle', timeout=15000)
                return True
        except Exception as e:
            logger.debug(f"Enter key fallback failed: {e}")
        
        return False

    async def _verify_login_success(self) -> bool:
        """Verify if login was successful"""
        try:
            # Wait a moment for page to update
            await asyncio.sleep(2.0)
            
            # Check current URL for login success indicators
            current_url = self.page.url.lower()
            
            # If still on login page, probably failed
            if 'login' in current_url and 'error' not in current_url:
                # Check for error messages
                error_selectors = [
                    '.error', '.alert-danger', '.login-error',
                    ':text("Credenziali non valide")',
                    ':text("Email o password errati")',
                    ':text("Invalid credentials")'
                ]
                
                for selector in error_selectors:
                    try:
                        if await self.page.locator(selector).count() > 0:
                            logger.warning("Login error message detected")
                            return False
                    except:
                        continue
                
                # Still on login page without clear error - might be failed
                logger.warning("Still on login page - login may have failed")
                return False
            
            # Look for login success indicators
            success_indicators = [
                # Account/profile links
                'a[href*="/account"]', 'a[href*="/profilo"]', 'a[href*="/profile"]',
                # Logout links
                'a[href*="/logout"]', 'a[href*="/esci"]',
                # User menu/dropdown
                '.user-menu', '.account-menu', '.profile-menu',
                # User name/email display
                ':text("Benvenuto")', ':text("Ciao")', ':text("Welcome")'
            ]
            
            for indicator in success_indicators:
                try:
                    if await self.page.locator(indicator).count() > 0:
                        logger.info(f"Login success indicator found: {indicator}")
                        # Log successful login
                        self.detection_monitor.log_event(
                            event_type=DetectionEventType.LOGIN_SUCCESS,
                            platform="fansale",
                            profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                            success=True,
                            details={"indicator": indicator, "url": current_url}
                        )
                        return True
                except Exception as e:
                    logger.debug(f"Error checking selector {indicator}: {e}")
                    continue
            
            # Check if we're redirected to a different page (likely success)
            if not any(term in current_url for term in ['login', 'accedi', 'signin']):
                logger.info("Redirected away from login page - likely successful")
                self.detection_monitor.log_event(
                    event_type=DetectionEventType.LOGIN_SUCCESS,
                    platform="fansale",
                    profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                    success=True,
                    details={"method": "redirect", "url": current_url}
                )
                return True
            
            # Try to navigate to the target event page to test access
            try:
                await self.page.goto(self.url, wait_until='networkidle', timeout=20000)
                await asyncio.sleep(2.0)
                
                # Check if we can access the page without being redirected to login
                final_url = self.page.url.lower()
                if 'login' not in final_url:
                    logger.info("Successfully accessed target page after login")
                    return True
            except Exception as e:
                logger.debug(f"Error in exception handler: {e}")
                pass
            
            logger.warning("Could not verify login success definitively")
            # Log login failure
            self.detection_monitor.log_event(
                event_type=DetectionEventType.LOGIN_FAILED,
                platform="fansale",
                profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                success=False,
                details={"reason": "verification_failed", "url": current_url}
            )
            return False
            
        except Exception as e:
            logger.error(f"Error verifying login success: {e}")
            # Log login error
            self.detection_monitor.log_event(
                event_type=DetectionEventType.LOGIN_FAILED,
                platform="fansale",
                profile_id=getattr(self.profile, 'profile_id', 'unknown'),
                success=False,
                details={"error": str(e)}
            )
            return False

    async def check_opportunities(self) -> List[EnhancedTicketOpportunity]:
        """Check for ticket opportunities using advanced HTML intelligence with enhanced blocking detection"""
        if not self.page:
            await self.initialize()
        
        from ..utils.live_status_logger import (
            log_network_status, 
            log_ticket_status, 
            start_operation, 
            update_operation_progress,
            complete_operation
        )
        
        opportunities = []
        start_time = time.time()
        
        try:
            start_operation("ticket_check", f"Checking tickets for {self.event_name}", 10.0)
            
            # 🥷 STEALTHMASTER AI ENHANCED LOGGING
            logger.info(f"🔍 FANSALE STEALTH SCAN: {self.event_name}")
            logger.info(f"   📍 URL: {self.url}")
            logger.info(f"   👤 Profile: {getattr(self.profile, 'profile_id', 'unknown')}")
            logger.info(f"   🌐 Proxy: {bool(getattr(self.profile, 'proxy_config', None))}")
            
            update_operation_progress("ticket_check", 30.0, "Navigating to FanSale page...")
            
            # Navigate with human-like behavior and capture response
            logger.info("   🎭 Executing stealth navigation...")
            response = await self._navigate_with_human_behavior()
            
            update_operation_progress("ticket_check", 60.0, "Analyzing page response...")
            
            # 🛡️ STEALTHMASTER AI ENHANCED METRICS LOGGING
            if response:
                response_time = time.time() - start_time
                logger.info(f"   📊 RESPONSE: HTTP {response.status} in {response_time:.2f}s")
                log_network_status(f"FanSale page load", response.status, response_time * 1000)
                
                # Get page fingerprint info
                page_content = await self.page.content()
                content_size = len(page_content)
                title = await self.page.title()
                
                logger.info(f"   📄 Page: '{title[:50]}...' ({content_size:,} bytes)")
                
                # 🛡️ StealthMaster AI Success Tracking
                if response.status == 200:
                    if self.session_id:
                        self.stealth_integration.track_operation_success(
                            platform="fansale",
                            session_id=self.session_id,
                            success=True,
                            details={
                                "operation": "page_load",
                                "response_time": response_time,
                                "status_code": response.status,
                                "content_size": content_size
                            }
                        )
                    logger.info("   🎯 StealthMaster AI: Page load SUCCESS tracked")
                else:
                    if self.session_id:
                        self.stealth_integration.track_operation_success(
                            platform="fansale",
                            session_id=self.session_id,
                            success=False,
                            details={
                                "operation": "page_load",
                                "response_time": response_time,
                                "status_code": response.status,
                                "error": f"HTTP {response.status}"
                            }
                        )
                    logger.warning("   ⚠️ StealthMaster AI: Page load FAILURE tracked")
                
                # 🔍 ADVANCED BLOCKING DETECTION WITH DETAILED LOGGING
                is_accessible = await self._handle_blocked_response(
                    response_status=response.status,
                    page_content=page_content
                )
                
                if not is_accessible:
                    logger.error("🚫 FANSALE STEALTH BREACH DETECTED!")
                    logger.error(f"   ❌ Status: {response.status}")
                    logger.error(f"   ❌ Profile compromised: {getattr(self.profile, 'profile_id', 'unknown')}")
                    log_network_status(f"FanSale access BLOCKED", response.status, response_time * 1000, blocked=True)
                    self._update_stealth_metrics(blocked=True, response_time=response_time)
                    self._log_stealth_effectiveness()
                    complete_operation("ticket_check", False, "Access blocked by FanSale")
                    return []
                else:
                    logger.info("   ✅ STEALTH STATUS: UNDETECTED")
                    log_network_status(f"FanSale access successful", response.status, response_time * 1000)
                    self._update_stealth_metrics(success=True, response_time=response_time)
            else:
                logger.warning("   ⚠️  No response object received")
                log_network_status("FanSale navigation", None, None)
                
            update_operation_progress("ticket_check", 80.0, "Scanning for tickets...")
            
            # 🕵️ CAPTCHA & VERIFICATION DETECTION
            logger.info("   🔎 Scanning for captcha/verification challenges...")
            has_captcha = await self._detect_captcha_or_verification()
            if has_captcha:
                logger.warning("🤖 CAPTCHA CHALLENGE DETECTED!")
                logger.warning("   🔄 Initiating stealth recovery protocol...")
                self.stealth_metrics['captcha_encounters'] += 1
                self.stealth_metrics['recovery_attempts'] += 1
                recovery_success = await self._attempt_blocking_recovery()
                if not recovery_success:
                    logger.error("❌ STEALTH RECOVERY FAILED - MISSION ABORTED")
                    self._update_risk_level('HIGH')
                    return []
                else:
                    logger.info("✅ STEALTH RECOVERY SUCCESSFUL")
                    self.stealth_metrics['successful_recoveries'] += 1
                    self._update_risk_level('MEDIUM')
            else:
                logger.info("   ✅ No verification challenges detected")
            
            # 📥 CONTENT LOADING WITH DETAILED TRACKING
            logger.info("   ⏳ Waiting for dynamic content...")
            await self._wait_for_dynamic_content()
            logger.info("   ✅ Content loaded")
            
            # 🎯 MULTI-STRATEGY TICKET EXTRACTION
            total_found = 0
            logger.info("   🔍 Beginning ticket hunt with multiple strategies...")
            
            # Strategy 1: HTML Structure
            logger.info("   🌐 Strategy 1: HTML structure analysis...")
            try:
                html_opportunities = await self._extract_from_html_structure()
                opportunities.extend(html_opportunities)
                total_found += len(html_opportunities)
                logger.info(f"      Found {len(html_opportunities)} via HTML structure")
            except Exception as e:
                logger.warning(f"      HTML extraction failed: {e}")
            
            # Strategy 2: Data Attributes  
            logger.info("   🏷️  Strategy 2: Data attributes mining...")
            try:
                data_opportunities = await self._extract_from_data_attributes()
                opportunities.extend(data_opportunities)
                new_found = len(data_opportunities)
                total_found += new_found
                logger.info(f"      Found {new_found} via data attributes")
            except Exception as e:
                logger.warning(f"      Data attributes extraction failed: {e}")
            
            # Strategy 3: JavaScript Variables
            logger.info("   📜 Strategy 3: JavaScript variables analysis...")
            try:
                js_opportunities = await self._extract_from_javascript_variables()
                opportunities.extend(js_opportunities)
                new_found = len(js_opportunities)
                total_found += new_found
                logger.info(f"      Found {new_found} via JavaScript variables")
            except Exception as e:
                logger.warning(f"      JavaScript extraction failed: {e}")
            
            # 🎯 OPPORTUNITY FILTERING & VALIDATION
            raw_count = len(opportunities)
            logger.info(f"   📊 Raw opportunities found: {raw_count}")
            opportunities = await self._filter_opportunities(opportunities)
            filtered_count = len(opportunities)
            
            if raw_count != filtered_count:
                logger.info(f"   🔧 Filtered {raw_count - filtered_count} invalid opportunities")
            
            # 📈 PERFORMANCE METRICS & STATE UPDATE
            total_time = time.time() - start_time
            self.last_check = datetime.now()
            
            # Record detailed metrics
            if hasattr(self.profile, 'record_usage'):
                self.profile.record_usage(
                    success=True,
                    platform="fansale",
                    response_time_ms=int(total_time * 1000),
                    detected=False
                )
            
            # 🎉 RESULTS ANNOUNCEMENT
            if opportunities:
                logger.critical("🚨🚨🚨 BRUCE SPRINGSTEEN TICKETS FOUND! 🚨🚨🚨")
                logger.critical(f"   🎫 COUNT: {len(opportunities)} opportunities")
                for i, opp in enumerate(opportunities[:3], 1):  # Show first 3
                    logger.critical(f"   #{i}: {opp.section} - €{opp.price} ({opp.quantity} tickets)")
                logger.critical(f"   ⏱️  Scan completed in {total_time:.2f}s")
                logger.critical("   🚀 Preparing for automated ticket acquisition...")
                
                # Log to live status system
                log_ticket_status(self.event_name, len(opportunities), {
                    "scan_time": total_time,
                    "top_price": min(opp.price for opp in opportunities),
                    "total_tickets": sum(opp.quantity for opp in opportunities)
                })
                complete_operation("ticket_check", True, f"TICKETS FOUND! {len(opportunities)} opportunities")
                
            else:
                logger.info(f"   📭 No tickets found (scan time: {total_time:.2f}s)")
                log_ticket_status(self.event_name, 0, {"scan_time": total_time})
                complete_operation("ticket_check", True, f"No tickets available (checked in {total_time:.1f}s)")
                
        except Exception as e:
            logger.error(f"Error checking Fansale opportunities: {e}")
            log_network_status("FanSale check failed", None, None, blocked=False)
            complete_operation("ticket_check", False, f"Error: {str(e)[:50]}")
            
            # Record failure
            if hasattr(self.profile, 'record_usage'):
                self.profile.record_usage(
                    success=False,
                    platform="fansale",
                    error=str(e),
                    detected=False
                )
            
            # Enhanced recovery attempt
            try:
                logger.info("🔄 Attempting FanSale page recovery...")
                
                # Check if this might be a blocking issue
                if "timeout" in str(e).lower() or "network" in str(e).lower():
                    recovery_success = await self._attempt_blocking_recovery()
                    if recovery_success:
                        logger.info("✅ FanSale recovery successful, retrying...")
                        # Recursive retry (but only once)
                        if not hasattr(self, '_retry_attempted'):
                            self._retry_attempted = True
                            return await self.check_opportunities()
                else:
                    # Simple page reload for other errors
                    await self.page.reload(wait_until='networkidle', timeout=15000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
            except Exception as recovery_error:
                logger.debug(f"Recovery attempt failed: {recovery_error}")
            finally:
                # Reset retry flag
                if hasattr(self, '_retry_attempted'):
                    delattr(self, '_retry_attempted')
        
        return opportunities

    async def _navigate_with_human_behavior(self):
        """Navigate with sophisticated human behavior simulation"""
        # Random pre-navigation delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Navigate with realistic timeout and capture response
        response = await self.page.goto(self.url, wait_until='networkidle', timeout=30000)
        
        # Simulate human reading/loading time
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Random mouse movements
        viewport = await self.page.viewport_size()
        if viewport:
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                await self.page.mouse.move(x, y, steps=random.randint(5, 15))
                await asyncio.sleep(random.uniform(0.3, 1.0))
        
        # Random scrolling behavior
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 800)
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(1.0, 2.5))
        
        return response

    async def _wait_for_dynamic_content(self):
        """Wait for dynamic content with intelligent detection"""
        try:
            # Wait for loading indicators to disappear
            for selector in self.selectors['loading_indicators']:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.wait_for_selector(selector, state='hidden', timeout=10000)
                    logger.debug(f"Waited for loading indicator: {selector}")
                except:
                    pass
            
            # Wait for offer containers to appear
            offer_found = False
            for selector in self.selectors['offer_containers']:
                try:
                    await self.page.wait_for_selector(selector, timeout=8000)
                    offer_found = True
                    logger.debug(f"Found offers with selector: {selector}")
                    break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue
            
            if not offer_found:
                logger.debug("No offer containers found - checking for no tickets message")
                
                # Check if no tickets available
                for selector in self.selectors['no_tickets']:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=3000)
                        if element:
                            logger.info("No tickets available message detected")
                            break
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Content load wait completed with: {e}")

    async def _extract_from_html_structure(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities using sophisticated HTML structure analysis"""
        opportunities = []
        
        try:
            # Find all offer containers
            offer_containers = []
            for selector in self.selectors['offer_containers']:
                try:
                    containers = await self.page.locator(selector).all()
                    if containers:
                        offer_containers = containers
                        logger.debug(f"Found {len(containers)} offers with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not offer_containers:
                logger.debug("No offer containers found in HTML structure")
                return opportunities
            
            logger.info(f"Processing {len(offer_containers)} offer containers")
            
            for i, container in enumerate(offer_containers):
                try:
                    # Extract offer data with multiple fallback strategies
                    offer_data = await self._extract_offer_data(container, i)
                    
                    if offer_data and self._validate_offer_data(offer_data):
                        opportunity = self._create_opportunity_from_data(offer_data, i)
                        if opportunity:
                            opportunities.append(opportunity)
                            logger.warning(f"🎯 FANSALE HTML HIT: {offer_data['section']} - €{offer_data['price']}")
                    
                except Exception as e:
                    logger.debug(f"Error processing offer container {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in HTML structure extraction: {e}")
        
        return opportunities

    async def _extract_offer_data(self, container, index: int) -> Optional[Dict[str, Any]]:
        """Extract comprehensive offer data from container"""
        try:
            offer_data = {
                'container_index': index,
                'price': 0.0,
                'currency': '€',
                'section': 'Unknown',
                'quantity': 1,
                'offer_type': 'Unknown',
                'is_fair_deal': False,
                'is_certified': False,
                'offer_id': None,
                'buy_url': None
            }
            
            # Extract offer ID from data attributes
            try:
                offer_id_attr = await container.get_attribute('data-offer-id')
                if offer_id_attr:
                    offer_data['offer_id'] = offer_id_attr
            except Exception as e:
                logger.debug(f"Error in exception handler: {e}")
                pass
            
            # Extract price with multiple strategies
            price_extracted = False
            for price_selector in self.selectors['price_elements']:
                try:
                    price_element = container.locator(price_selector).first
                    if await price_element.count():
                        price_text = await price_element.inner_text()
                        # Parse price (handle Italian format with comma)
                        price_match = re.search(r'(\d+(?:[.,]\d+)?)', price_text.replace('.', '').replace(',', '.'))
                        if price_match:
                            offer_data['price'] = float(price_match.group(1))
                            price_extracted = True
                            break
                except Exception as e:
                    logger.debug(f"Price extraction failed for {price_selector}: {e}")
                    continue
            
            if not price_extracted:
                logger.debug(f"Could not extract price for offer {index}")
                return None

            # Extract currency
            for currency_selector in self.selectors['currency_elements']:
                try:
                    currency_element = container.locator(currency_selector).first
                    if await currency_element.count():
                        currency_text = await currency_element.inner_text()
                        if currency_text.strip():
                            offer_data['currency'] = currency_text.strip()
                            break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            # Extract section/seat description
            for section_selector in self.selectors['section_elements']:
                try:
                    section_element = container.locator(section_selector).first
                    if await section_element.count():
                        section_text = await section_element.inner_text()
                        if section_text.strip():
                            offer_data['section'] = section_text.strip()
                            break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            # Extract quantity
            for quantity_selector in self.selectors['quantity_elements']:
                try:
                    quantity_element = container.locator(quantity_selector).first
                    if await quantity_element.count():
                        quantity_text = await quantity_element.inner_text()
                        quantity_match = re.search(r'(\d+)', quantity_text)
                        if quantity_match:
                            offer_data['quantity'] = int(quantity_match.group(1))
                            break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            # Extract offer type
            for type_selector in self.selectors['offer_type_elements']:
                try:
                    type_element = container.locator(type_selector).first
                    if await type_element.count():
                        type_text = await type_element.inner_text()
                        if type_text.strip():
                            offer_data['offer_type'] = type_text.strip()
                            break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            # Check Fair Deal status
            for fair_deal_selector in self.selectors['fair_deal_indicator']:
                try:
                    fair_deal_element = container.locator(fair_deal_selector).first
                    if await fair_deal_element.count():
                        offer_data['is_fair_deal'] = True
                        break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            # Check certified status
            for certified_selector in self.selectors['certified_indicator']:
                try:
                    certified_element = container.locator(certified_selector).first
                    if await certified_element.count():
                        offer_data['is_certified'] = True
                        break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            # Extract buy URL
            for buy_selector in self.selectors['buy_button']:
                try:
                    buy_element = container.locator(buy_selector).first
                    if await buy_element.count():
                        href = await buy_element.get_attribute('href')
                        if href:
                            # Convert relative URL to absolute
                            offer_data['buy_url'] = urljoin(self.page.url, href)
                            break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue

            return offer_data

        except Exception as e:
            logger.debug(f"Error extracting offer data from container {index}: {e}")
            return None

    async def _extract_from_data_attributes(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities from data attributes"""
        opportunities = []
        
        try:
            # Look for elements with data attributes
            data_elements = await self.page.evaluate("""
            () => {
                const elements = document.querySelectorAll('[data-offer-id], [data-price], [data-splitting-possibilities]');
                const data = [];
                
                elements.forEach((element, index) => {
                    const rect = element.getBoundingClientRect();
                    
                    // Only process visible elements
                    if (rect.width > 0 && rect.height > 0) {
                        const attributes = {};
                        
                        // Extract all data attributes
                        for (let attr of element.attributes) {
                            if (attr.name.startsWith('data-')) {
                                attributes[attr.name] = attr.value;
                            }
                        }
                        
                        // Extract text content
                        const textContent = element.textContent || '';
                        
                        data.push({
                            index: index,
                            attributes: attributes,
                            textContent: textContent.substring(0, 500),
                            className: element.className
                        });
                    }
                });
                
                return data;
            }
            """)
            
            for element_data in data_elements:
                try:
                    attrs = element_data['attributes']
                    
                    # Extract price from data attributes
                    price = 0.0
                    if 'data-splitting-possibility-prices' in attrs:
                        price_str = attrs['data-splitting-possibility-prices']
                        try:
                            price = float(price_str.replace(',', '.'))
                        except:
                            continue
                    
                    if price <= 0 or price > self.max_price:
                        continue
                    
                    # Extract section from aria label or text content
                    section = "Unknown Section"
                    if 'data-seatdescriptionforarialabel' in attrs:
                        section = attrs['data-seatdescriptionforarialabel']
                    elif element_data['textContent']:
                        # Try to extract section from text content
                        text = element_data['textContent']
                        # Look for patterns like "INGRESSO 8 | Fila 9 | Posto 31"
                        section_match = re.search(r'(INGRESSO\s+\d+|Settore\s+\w+|[A-Z]+\s+\d+)', text)
                        if section_match:
                            section = section_match.group(1)
                    
                    # Check Fair Deal status
                    is_fair_deal = attrs.get('data-fairdeal') == 'true'
                    is_certified = attrs.get('data-certified') == 'true'
                    
                    # Apply filters
                    if self.fair_deal_only and not is_fair_deal:
                        continue
                    
                    if self.certified_only and not is_certified:
                        continue
                    
                    if self.desired_sections:
                        section_lower = section.lower()
                        if not any(desired.lower() in section_lower for desired in self.desired_sections):
                            continue
                    
                    # Create opportunity
                    offer_id = attrs.get('data-offer-id', f'fansale_data_{int(time.time())}_{element_data["index"]}')
                    
                    if offer_id in self.detected_offers:
                        continue
                    
                    self.detected_offers.add(offer_id)
                    
                    opportunity = EnhancedTicketOpportunity(
                        id=offer_id,
                        platform=PlatformType.FANSALE,
                        event_name=self.event_name,
                        url=self.url,
                        offer_url=self.page.url,
                        section=section,
                        price=price,
                        quantity=int(attrs.get('data-splitting-possibilities', 1)),
                        detected_at=datetime.now(),
                        priority=self.priority,
                        confidence_score=0.93,
                        detection_method='data_attributes',
                        metadata={
                            'is_fair_deal': is_fair_deal,
                            'is_certified': is_certified,
                            'offer_type': attrs.get('data-offertype', 'Unknown'),
                            'element_index': element_data['index']
                        }
                    )
                    
                    opportunities.append(opportunity)
                    logger.warning(f"🎯 FANSALE DATA ATTR HIT: {section} - €{price}")
                    
                except Exception as e:
                    logger.debug(f"Error processing data element: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in data attributes extraction: {e}")
        
        return opportunities

    async def _extract_from_javascript_variables(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities from JavaScript variables"""
        opportunities = []
        
        try:
            # Look for JavaScript variables containing offer data
            js_data = await self.page.evaluate("""
            () => {
                const data = [];
                
                // Check common variable names
                const varNames = [
                    'eventData', 'offerData', 'ticketData', 'fansaleData',
                    'pageData', 'initialData', 'appData'
                ];
                
                varNames.forEach(varName => {
                    if (window[varName]) {
                        try {
                            data.push({
                                source: varName,
                                data: window[varName]
                            });
                        } catch (e) {}
                    }
                });
                
                // Look for data in script tags
                const scripts = document.querySelectorAll('script:not([src])');
                scripts.forEach((script, index) => {
                    const content = script.textContent;
                    
                    // Look for variable assignments with offer data
                    const patterns = [
                        /var\\s+\\w+\\s*=\\s*(\\{[^}]*offer[^}]*\\})/gi,
                        /const\\s+\\w+\\s*=\\s*(\\{[^}]*price[^}]*\\})/gi,
                        /let\\s+\\w+\\s*=\\s*(\\{[^}]*ticket[^}]*\\})/gi
                    ];
                    
                    patterns.forEach(pattern => {
                        const matches = content.match(pattern);
                        if (matches) {
                            matches.forEach(match => {
                                try {
                                    const jsonMatch = match.match(/\\{.*\\}/);
                                    if (jsonMatch) {
                                        const json = JSON.parse(jsonMatch[0]);
                                        data.push({
                                            source: `script_${index}`,
                                            data: json
                                        });
                                    }
                                } catch (e) {}
                            });
                        }
                    });
                });
                
                return data;
            }
            """)
            
            for js_item in js_data:
                try:
                    source = js_item['source']
                    data = js_item['data']
                    
                    await self._process_js_data(data, source, opportunities)
                    
                except Exception as e:
                    logger.debug(f"Error processing JS data: {e}")
                    
        except Exception as e:
            logger.error(f"Error in JavaScript variables extraction: {e}")
        
        return opportunities

    async def _process_js_data(self, data: Any, source: str, opportunities: List):
        """Process JavaScript data recursively"""
        try:
            if isinstance(data, dict):
                # Look for offer-like structures
                if self._is_offer_data(data):
                    opportunity = self._create_opportunity_from_js_data(data, source)
                    if opportunity:
                        opportunities.append(opportunity)
                        logger.warning(f"🎯 FANSALE JS HIT: {opportunity.section} - €{opportunity.price}")
                
                # Recursively process nested objects
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        await self._process_js_data(value, f"{source}.{key}", opportunities)
            
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    await self._process_js_data(item, f"{source}[{i}]", opportunities)
                    
        except Exception as e:
            logger.debug(f"Error processing JS data recursively: {e}")

    def _is_offer_data(self, data: dict) -> bool:
        """Check if data structure looks like an offer"""
        offer_indicators = [
            'price', 'cost', 'amount', 'section', 'seat', 'offer',
            'ticket', 'quantity', 'available', 'fairDeal'
        ]
        
        keys = [k.lower() for k in data.keys()]
        return any(indicator in ' '.join(keys) for indicator in offer_indicators)

    def _create_opportunity_from_js_data(self, data: dict, source: str) -> Optional[EnhancedTicketOpportunity]:
        """Create opportunity from JavaScript data"""
        try:
            # Extract price
            price = 0.0
            price_keys = ['price', 'cost', 'amount', 'value']
            for key in price_keys:
                if key in data:
                    try:
                        price = float(data[key])
                        break
                    except:
                        continue
            
            if price <= 0 or price > self.max_price:
                return None
            
            # Extract section
            section = "JavaScript Data"
            section_keys = ['section', 'sector', 'area', 'seat', 'location']
            for key in section_keys:
                if key in data and isinstance(data[key], str):
                    section = data[key]
                    break
            
            # Extract other metadata
            quantity = int(data.get('quantity', data.get('qty', 1)))
            is_fair_deal = data.get('fairDeal', data.get('fair_deal', False))
            is_certified = data.get('certified', data.get('ticketcheck', False))
            
            # Apply filters
            if self.fair_deal_only and not is_fair_deal:
                return None
            
            if self.certified_only and not is_certified:
                return None
            
            if self.desired_sections:
                section_lower = section.lower()
                if not any(desired.lower() in section_lower for desired in self.desired_sections):
                    return None
            
            # Create opportunity
            opportunity_id = f"fansale_js_{hash(str(data))}_{int(time.time())}"
            
            if opportunity_id in self.detected_offers:
                return None
            
            self.detected_offers.add(opportunity_id)
            
            return EnhancedTicketOpportunity(
                id=opportunity_id,
                platform=PlatformType.FANSALE,
                event_name=self.event_name,
                url=self.url,
                offer_url=self.page.url,
                section=section,
                price=price,
                quantity=quantity,
                detected_at=datetime.now(),
                priority=self.priority,
                confidence_score=0.85,
                detection_method='javascript_variables',
                metadata={
                    'source': source,
                    'is_fair_deal': is_fair_deal,
                    'is_certified': is_certified,
                    'raw_data': str(data)[:200]
                }
            )
            
        except Exception as e:
            logger.debug(f"Error creating opportunity from JS data: {e}")
            return None

    async def _filter_opportunities(self, opportunities: List[EnhancedTicketOpportunity]) -> List[EnhancedTicketOpportunity]:
        """Filter and deduplicate opportunities"""
        try:
            if not opportunities:
                return opportunities
            
            # Remove duplicates based on fingerprint
            seen_fingerprints = set()
            filtered = []
            
            for opp in opportunities:
                if opp.fingerprint not in seen_fingerprints:
                    seen_fingerprints.add(opp.fingerprint)
                    filtered.append(opp)
            
            # Sort by confidence score and price
            filtered.sort(key=lambda x: (x.confidence_score, -x.price), reverse=True)
            
            logger.info(f"Filtered {len(opportunities)} -> {len(filtered)} opportunities")
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error filtering opportunities: {e}")
            return opportunities

    async def attempt_purchase(self, opportunity: EnhancedTicketOpportunity) -> bool:
        """Attempt to purchase Fansale ticket with advanced automation and manual handoff"""
        if not self.page:
            logger.error("Cannot attempt purchase: no page available")
            return False
        
        try:
            logger.critical("🚨🚨🚨 BRUCE SPRINGSTEEN TICKETS FOUND! 🚨🚨🚨")
            logger.critical("🎸🎸🎸 AUTOMATED PURCHASE SEQUENCE STARTING 🎸🎸🎸")
            logger.critical(f"🎫 TICKET: {opportunity.section} - €{opportunity.price}")
            logger.critical(f"🎯 QUANTITY: {opportunity.quantity}")
            logger.critical(f"📍 URL: {opportunity.offer_url}")
            
            # Make browser window prominent
            await self._make_browser_prominent()
            
            # Navigate to offer URL if different
            if opportunity.offer_url != self.page.url:
                logger.critical("🔄 Navigating to ticket page...")
                await self.page.goto(opportunity.offer_url, wait_until='networkidle', timeout=20000)
                logger.critical("✅ Navigation complete!")
            
            # Human-like delay before interaction
            logger.info("⏳ Simulating human reading time...")
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Look for buy buttons with multiple strategies
            purchase_success = False
            
            # Strategy 1: Click direct buy button
            buy_selectors = [
                '.Button-inOfferEntryList', '.js-Button-inOfferEntryList',
                'a[role="button"][data-track]', '.purchase-button',
                'button:text("Acquista")', 'button:text("Buy")',
                '.buy-btn', '.acquista-btn'
            ]
            
            for selector in buy_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.count() and await button.is_visible():
                        # Scroll to button
                        await button.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1.0))
                        
                        # Click with realistic timing
                        await button.click()
                        logger.info(f"Clicked Fansale buy button: {selector}")
                        
                        # Wait for navigation/response
                        await self.page.wait_for_load_state('networkidle', timeout=15000)
                        
                        purchase_success = await self._verify_fansale_purchase()
                        if purchase_success:
                            break
                        
                except Exception as e:
                    logger.debug(f"Failed to click {selector}: {e}")
                    continue
            
            # Strategy 2: Try offer container click if direct button failed
            if not purchase_success:
                try:
                    # Look for clickable offer containers
                    container_selectors = [
                        f'[data-offer-id="{opportunity.metadata.get("original_offer_id")}"]',
                        '.EventEntry.js-EventEntry.EventEntry-isClickable',
                        '.offer-container.clickable'
                    ]
                    
                    for selector in container_selectors:
                        try:
                            container = self.page.locator(selector).first
                            if await container.count() and await container.is_visible():
                                await container.click()
                                await self.page.wait_for_load_state('networkidle', timeout=10000)
                                
                                purchase_success = await self._verify_fansale_purchase()
                                if purchase_success:
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Container click failed for {selector}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Container click strategy failed: {e}")
            
            if purchase_success:
                logger.critical("🎉🎉🎉 FANSALE PURCHASE INITIATED! 🎉🎉🎉")
                logger.critical(f"🎫 TICKET RESERVED: {opportunity.section}")
                logger.critical("🚨 MANUAL COMPLETION REQUIRED:")
                logger.critical("   1. Browser window should be visible")
                logger.critical("   2. Complete payment manually")
                logger.critical("   3. Ticket is RESERVED for limited time")
                logger.critical("   4. DO NOT CLOSE BROWSER WINDOW")
                await self._send_purchase_notification(opportunity)
            else:
                logger.warning(f"⚠️  Fansale purchase attempt status unclear: {opportunity.section}")
                logger.warning("🔍 Check browser window for status")
            
            return purchase_success
            
        except Exception as e:
            logger.error(f"💥 Fansale purchase attempt failed: {e}")
            return False
    
    async def _make_browser_prominent(self):
        """Make browser window prominent and visible"""
        try:
            # Bring window to front
            await self.page.bring_to_front()
            
            # Set window title to alert user
            await self.page.evaluate("""
                document.title = '🚨 BRUCE SPRINGSTEEN TICKETS FOUND! 🚨 - ' + document.title;
            """)
            
            # Create visual alert on page
            await self.page.evaluate("""
                // Create alert banner
                const alertBanner = document.createElement('div');
                alertBanner.id = 'bruce-alert-banner';
                alertBanner.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 60px;
                    background: linear-gradient(90deg, #ff0000, #ffa500, #ff0000);
                    color: white;
                    font-size: 20px;
                    font-weight: bold;
                    text-align: center;
                    line-height: 60px;
                    z-index: 999999;
                    animation: flash 1s infinite;
                `;
                alertBanner.innerHTML = '🚨 BRUCE SPRINGSTEEN TICKETS FOUND! COMPLETE PURCHASE MANUALLY! 🚨';
                
                // Add flashing animation
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes flash {
                        0%, 50% { opacity: 1; }
                        51%, 100% { opacity: 0.3; }
                    }
                `;
                document.head.appendChild(style);
                document.body.appendChild(alertBanner);
            """)
            
            logger.critical("🎆 Browser window made prominent with visual alerts!")
            
        except Exception as e:
            logger.debug(f"Failed to make browser prominent: {e}")
    
    async def _send_purchase_notification(self, opportunity: EnhancedTicketOpportunity):
        """Send purchase notification and instructions"""
        try:
            # Log detailed instructions
            logger.critical("📋 MANUAL PURCHASE INSTRUCTIONS:")
            logger.critical("=" * 60)
            logger.critical(f"🎫 Event: {self.event_name}")
            logger.critical(f"🎪 Section: {opportunity.section}")
            logger.critical(f"💰 Price: €{opportunity.price}")
            logger.critical(f"📊 Quantity: {opportunity.quantity}")
            logger.critical(f"⭐ Confidence: {opportunity.confidence_score:.1%}")
            logger.critical("=" * 60)
            logger.critical("🚨 URGENT ACTIONS REQUIRED:")
            logger.critical("   1. ✅ Check browser window is visible")
            logger.critical("   2. 💳 Complete payment form")
            logger.critical("   3. ✔️  Confirm purchase")
            logger.critical("   4. 📧 Check for confirmation email")
            logger.critical("   5. 🚫 DO NOT CLOSE BROWSER")
            logger.critical("=" * 60)
            
            # Optional: System notification (platform dependent)
            try:
                import subprocess
                import sys
                
                if sys.platform == "darwin":  # macOS
                    subprocess.run([
                        "osascript", "-e", 
                        f'display notification "Bruce Springsteen tickets found! Complete purchase manually." with title "🎸 TICKET ALERT 🎸"'
                    ])
                elif sys.platform.startswith("linux"):  # Linux
                    subprocess.run([
                        "notify-send", "🎸 TICKET ALERT 🎸", 
                        "Bruce Springsteen tickets found! Complete purchase manually."
                    ])
                # Windows notification would need additional setup
                    
            except Exception as notify_error:
                logger.debug(f"System notification failed: {notify_error}")
                
        except Exception as e:
            logger.debug(f"Failed to send purchase notification: {e}")

    async def _verify_fansale_purchase(self) -> bool:
        """Verify if Fansale purchase process was initiated"""
        try:
            # Fansale-specific success indicators
            success_indicators = [
                'text=Carrello', 'text=Cart', 'text=Checkout', 'text=Warenkorb',
                'text=Pagamento', 'text=Payment', 'text=Bezahlung',
                '.checkout-page', '.cart-page', '.payment-step',
                '[data-step="payment"]', '[data-step="checkout"]'
            ]
            
            for indicator in success_indicators:
                try:
                    if await self.page.locator(indicator).count() > 0:
                        logger.info(f"Fansale purchase indicator found: {indicator}")
                        return True
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue
            
            # Check URL for purchase flow
            current_url = self.page.url.lower()
            purchase_url_indicators = [
                'checkout', 'payment', 'cart', 'carrello', 'warenkorb',
                'bezahlung', 'pagamento', 'kasse'
            ]
            
            if any(indicator in current_url for indicator in purchase_url_indicators):
                logger.info(f"Fansale purchase flow URL detected: {current_url}")
                return True
            
            # Check for purchase confirmation elements
            confirmation_selectors = [
                '.purchase-confirmation', '.order-summary',
                '.ticket-selection', '.seat-selection'
            ]
            
            for selector in confirmation_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        logger.info(f"Fansale confirmation element: {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Error verifying Fansale purchase: {e}")
            return False

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.browser_context:
                await self.browser_context.close()
                self.browser_context = None
                
        except Exception as e:
            logger.error(f"Error during Fansale cleanup: {e}")

# Legacy compatibility functions
async def monitor(*args, **kwargs):
    """Legacy monitor function for backward compatibility"""
    return []

async def check_fansale_event(page, profile, target_cfg, gui_q=None):
    """Legacy function - redirects to new monitor class"""
    logger.warning("Using legacy check_fansale_event - please update to FansaleMonitor class")
    
    # Create temporary monitor instance
    monitor = FansaleMonitor(target_cfg, profile, None, None, None)
    monitor.page = page
    
    return await monitor.check_opportunities()
            
            # Extract currency
    def _validate_offer_data(self, offer_data: Dict[str, Any]) -> bool:
        """Validate extracted offer data"""
        try:
            # Price validation
            if offer_data['price'] <= 0 or offer_data['price'] > self.max_price:
                return False
            
            # Fair Deal filter
            if self.fair_deal_only and not offer_data['is_fair_deal']:
                return False
            
            # Certified filter
            if self.certified_only and not offer_data['is_certified']:
                return False
            
            # Section filter
            if self.desired_sections:
                section_lower = offer_data['section'].lower()
                if not any(desired.lower() in section_lower for desired in self.desired_sections):
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error validating offer data: {e}")
            return False

    def _create_opportunity_from_data(self, offer_data: Dict[str, Any], index: int) -> Optional[EnhancedTicketOpportunity]:
        """Create EnhancedTicketOpportunity from extracted data"""
        try:
            # Generate unique ID
            offer_id = offer_data.get('offer_id', f'fansale_{int(time.time())}_{index}')
            
            # Check if already detected
            if offer_id in self.detected_offers:
                return None
            
            self.detected_offers.add(offer_id)
            
            # Create opportunity
            opportunity = EnhancedTicketOpportunity(
                id=offer_id,
                platform=PlatformType.FANSALE,
                event_name=self.event_name,
                url=self.url,
                offer_url=offer_data.get('buy_url', self.page.url),
                section=offer_data['section'],
                price=offer_data['price'],
                quantity=offer_data['quantity'],
                detected_at=datetime.now(),
                priority=self.priority,
                confidence_score=0.95,
                detection_method='html_structure_intelligence',
                metadata={
                    'currency': offer_data['currency'],
                    'offer_type': offer_data['offer_type'],
                    'is_fair_deal': offer_data['is_fair_deal'],
                    'is_certified': offer_data['is_certified'],
                    'container_index': offer_data['container_index'],
                    'original_offer_id': offer_data.get('offer_id')
                }
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating opportunity from data: {e}")
    
    def _update_stealth_metrics(self, success: bool = None, blocked: bool = False, 
                               response_time: float = 0.0, detected: bool = False):
        """Update stealth effectiveness metrics with detailed tracking"""
        try:
            self.stealth_metrics['total_requests'] += 1
            
            if success is not None:
                if success:
                    self.stealth_metrics['successful_requests'] += 1
                    self.stealth_metrics['consecutive_successes'] += 1
                else:
                    self.stealth_metrics['consecutive_successes'] = 0
            
            if blocked:
                self.stealth_metrics['blocked_requests'] += 1
                self.stealth_metrics['last_detection'] = datetime.now()
                self.stealth_metrics['consecutive_successes'] = 0
            
            if detected:
                self.stealth_metrics['last_detection'] = datetime.now()
            
            # Update average response time
            if response_time > 0:
                total_time = self.stealth_metrics['average_response_time'] * (self.stealth_metrics['total_requests'] - 1)
                self.stealth_metrics['average_response_time'] = (total_time + response_time) / self.stealth_metrics['total_requests']
            
            # Calculate stealth effectiveness percentage
            if self.stealth_metrics['total_requests'] > 0:
                success_rate = self.stealth_metrics['successful_requests'] / self.stealth_metrics['total_requests']
                block_rate = self.stealth_metrics['blocked_requests'] / self.stealth_metrics['total_requests']
                
                # Stealth effectiveness considers both success rate and lack of blocking
                self.stealth_metrics['stealth_effectiveness'] = max(0.0, min(100.0, 
                    (success_rate * 100) - (block_rate * 50)  # Blocking heavily penalized
                ))
            
            # Update risk level based on recent performance
            self._update_risk_level_from_metrics()
            
        except Exception as e:
            logger.debug(f"Error updating stealth metrics: {e}")
    
    def _log_stealth_effectiveness(self):
        """Log comprehensive stealth effectiveness analysis"""
        try:
            metrics = self.stealth_metrics
            session_duration = (datetime.now() - metrics['session_start']).total_seconds() / 60  # minutes
            
            logger.info("🥷 STEALTHMASTER AI EFFECTIVENESS REPORT")
            logger.info("=" * 50)
            logger.info(f"   📊 SESSION DURATION: {session_duration:.1f} minutes")
            logger.info(f"   🎯 TOTAL REQUESTS: {metrics['total_requests']}")
            logger.info(f"   ✅ SUCCESSFUL: {metrics['successful_requests']} ({metrics['successful_requests']/max(1,metrics['total_requests'])*100:.1f}%)")
            logger.info(f"   🚫 BLOCKED: {metrics['blocked_requests']} ({metrics['blocked_requests']/max(1,metrics['total_requests'])*100:.1f}%)")
            logger.info(f"   🤖 CAPTCHA ENCOUNTERS: {metrics['captcha_encounters']}")
            logger.info(f"   🔄 RECOVERY ATTEMPTS: {metrics['recovery_attempts']}")
            logger.info(f"   ✨ SUCCESSFUL RECOVERIES: {metrics['successful_recoveries']}")
            logger.info(f"   ⚡ AVG RESPONSE TIME: {metrics['average_response_time']:.2f}ms")
            logger.info(f"   🔥 CONSECUTIVE SUCCESSES: {metrics['consecutive_successes']}")
            logger.info(f"   🎭 FINGERPRINT CHANGES: {metrics['fingerprint_changes']}")
            logger.info(f"   🌐 PROXY ROTATIONS: {metrics['proxy_rotations']}")
            
            # Stealth effectiveness score
            effectiveness = metrics['stealth_effectiveness']
            if effectiveness >= 90:
                status = "🟢 EXCELLENT"
            elif effectiveness >= 75:
                status = "🟡 GOOD"
            elif effectiveness >= 50:
                status = "🟠 MODERATE"
            else:
                status = "🔴 COMPROMISED"
            
            logger.critical(f"   🛡️  STEALTH EFFECTIVENESS: {effectiveness:.1f}% - {status}")
            logger.critical(f"   ⚠️  RISK LEVEL: {metrics['risk_level']}")
            
            # Last detection warning
            if metrics['last_detection']:
                time_since = (datetime.now() - metrics['last_detection']).total_seconds() / 60
                logger.warning(f"   🚨 LAST DETECTION: {time_since:.1f} minutes ago")
            else:
                logger.info(f"   🎉 NO DETECTIONS THIS SESSION")
            
            logger.info("=" * 50)
            
            # Performance recommendations
            if effectiveness < 70:
                logger.warning("🔧 STEALTH RECOMMENDATIONS:")
                if metrics['blocked_requests'] > metrics['successful_requests'] * 0.3:
                    logger.warning("   • Consider rotating profiles more frequently")
                    logger.warning("   • Implement longer delays between requests")
                if metrics['captcha_encounters'] > 3:
                    logger.warning("   • Review behavioral patterns for human-likeness")
                    logger.warning("   • Consider using different browser fingerprints")
                if metrics['average_response_time'] > 5000:
                    logger.warning("   • Network may be throttled or detected")
                    logger.warning("   • Consider proxy rotation")
                    
        except Exception as e:
            logger.debug(f"Error logging stealth effectiveness: {e}")
    
    def _update_risk_level(self, level: str = None):
        """Update risk level with automatic assessment if no level provided"""
        try:
            if level:
                self.stealth_metrics['risk_level'] = level
            else:
                self._update_risk_level_from_metrics()
                
        except Exception as e:
            logger.debug(f"Error updating risk level: {e}")
    
    def _update_risk_level_from_metrics(self):
        """Automatically determine risk level from current metrics"""
        try:
            metrics = self.stealth_metrics
            
            # Calculate risk factors
            if metrics['total_requests'] == 0:
                self.stealth_metrics['risk_level'] = 'LOW'
                return
            
            block_rate = metrics['blocked_requests'] / metrics['total_requests']
            success_rate = metrics['successful_requests'] / metrics['total_requests']
            recent_captchas = metrics['captcha_encounters']
            consecutive_failures = metrics['total_requests'] - metrics['successful_requests'] - metrics['consecutive_successes']
            
            # Time since last detection
            time_since_detection = float('inf')
            if metrics['last_detection']:
                time_since_detection = (datetime.now() - metrics['last_detection']).total_seconds() / 60  # minutes
            
            # Risk assessment logic
            risk_score = 0
            
            # Blocking rate (most critical factor)
            if block_rate >= 0.5:
                risk_score += 40
            elif block_rate >= 0.3:
                risk_score += 25
            elif block_rate >= 0.1:
                risk_score += 10
            
            # Success rate
            if success_rate < 0.3:
                risk_score += 30
            elif success_rate < 0.5:
                risk_score += 20
            elif success_rate < 0.7:
                risk_score += 10
            
            # Recent captcha encounters
            if recent_captchas >= 5:
                risk_score += 20
            elif recent_captchas >= 3:
                risk_score += 15
            elif recent_captchas >= 1:
                risk_score += 5
            
            # Consecutive failures
            if consecutive_failures >= 10:
                risk_score += 15
            elif consecutive_failures >= 5:
                risk_score += 10
            elif consecutive_failures >= 3:
                risk_score += 5
            
            # Time since last detection (good if long time)
            if time_since_detection < 5:  # Very recent detection
                risk_score += 20
            elif time_since_detection < 15:
                risk_score += 10
            elif time_since_detection < 60:
                risk_score += 5
            # No penalty if > 60 minutes
            
            # Determine risk level
            if risk_score >= 60:
                risk_level = 'CRITICAL'
            elif risk_score >= 40:
                risk_level = 'HIGH'
            elif risk_score >= 20:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            self.stealth_metrics['risk_level'] = risk_level
            
            # Log risk level changes
            if hasattr(self, '_last_risk_level') and self._last_risk_level != risk_level:
                logger.warning(f"🚨 RISK LEVEL CHANGED: {self._last_risk_level} → {risk_level}")
                logger.warning(f"   📊 Risk Score: {risk_score}/100")
                logger.warning(f"   🚫 Block Rate: {block_rate:.1%}")
                logger.warning(f"   ✅ Success Rate: {success_rate:.1%}")
            
            self._last_risk_level = risk_level
            
        except Exception as e:
            logger.debug(f"Error updating risk level from metrics: {e}")
            self.stealth_metrics['risk_level'] = 'UNKNOWN'