# src/platforms/ticketmaster.py - STEALTHMASTER AI ENHANCED v6.0
from __future__ import annotations

import asyncio
import logging
import random
import re
import time
import json
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

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

class TicketmasterMonitor:
    """🎸 STEALTHMASTER AI ENHANCED - Revolutionary Ticketmaster monitor with ultimate stealth"""
    
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
        
        # State management
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.last_check = None
        self.api_headers = {}
        
        # 🛡️ StealthMaster AI Integration
        self.stealth_integration = get_bruce_stealth_integration()
        self.session_id: Optional[str] = None
        
        # Advanced detection patterns
        self.api_patterns = {
            'inventory': r'/api/v\d+/inventory',
            'events': r'/api/v\d+/events/[^/]+/offers',
            'discovery': r'/discovery/v\d+/events',
            'graphql': r'/graphql'
        }
        
        # Adaptive selectors with fallbacks
        self.selectors = {
            'loading': [
                '.loading-indicator', '.spinner', '[data-testid="loading"]'
            ],
            'no_tickets': [
                'text=No tickets available',
                'text=Sold Out',
                '.sold-out-message',
                '[data-testid="sold-out"]'
            ],
            'ticket_cards': [
                '[data-testid="ticket-card"]',
                '.ticket-listing',
                '.offer-card',
                '.tm-offer'
            ],
            'price': [
                '[data-testid="price"]',
                '.price-display',
                '.cost',
                '.ticket-price'
            ],
            'section': [
                '[data-testid="section"]',
                '.section-name',
                '.seating-info'
            ],
            'buy_button': [
                'button:text("Buy")',
                'button:text("Select")',
                '[data-testid="buy-button"]',
                '.purchase-btn'
            ]
        }
        
        logger.info(f"TicketmasterMonitor initialized for {self.event_name}")

    async def initialize(self):
        """Initialize with Ticketmaster-specific stealth"""
        try:
            logger.info(f"Initializing Ticketmaster stealth for {self.event_name}")
            
            # Get stealth browser context
            self.browser_context = await self.browser_manager.get_stealth_context(
                self.profile, force_new=False
            )
            
            # Create page with advanced stealth
            self.page = await self.browser_context.new_page()
            
            # Setup Ticketmaster-specific stealth with TLS fingerprinting
            
            # CRITICAL: Inject TLS fingerprint BEFORE any page loads
            from ..utils.tls_fingerprint import inject_tls_fingerprint_for_browser_context
            try:
                # Convert BrowserProfile to DynamicProfile-like object for TLS injection
                profile_snapshot = {
                    'tls_ja3': getattr(self.profile, 'tls_ja3', '771,4865-4866-4867-49195-49199'),
                    'h2_header_table_size': getattr(self.profile, 'h2_header_table_size', 65536),
                    'h2_max_streams': getattr(self.profile, 'h2_max_streams', 1000),
                    'h2_window_size': getattr(self.profile, 'h2_window_size', 6291456),
                    'accept_language': ','.join(self.profile.languages_override) if hasattr(self.profile, 'languages_override') else 'en-US,en;q=0.9',
                    'user_agent': self.profile.user_agent,
                    'browser_name': 'chrome',
                    'browser_version': 'latest'
                }
                
                # Create mock profile object for TLS injection
                class MockProfile:
                    def __init__(self, snapshot):
                        self.id = getattr(self.profile, 'profile_id', 'unknown')
                        self._snapshot = snapshot
                    
                    def get_fingerprint_snapshot(self):
                        return self._snapshot
                
                mock_profile = MockProfile(profile_snapshot)
                await inject_tls_fingerprint_for_browser_context(self.browser_context, mock_profile)
                logger.info("🛡️ Ticketmaster TLS fingerprint injected successfully")
                
            except Exception as e:
                logger.warning(f"⚠️ Ticketmaster TLS fingerprint injection failed: {e}")
            
            await self._inject_ticketmaster_stealth()
            await self._setup_api_interception()
            await self._configure_human_behavior()
            
            logger.info(f"Ticketmaster stealth initialized for {self.event_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ticketmaster stealth: {e}")
            raise

    async def _inject_ticketmaster_stealth(self):
        """Inject Ticketmaster-specific anti-detection measures"""
        await self.page.add_init_script("""
        // Ticketmaster bot detection bypass
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Override fetch to add realistic headers
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            };
            
            return originalFetch(url, { ...options, headers });
        };
        
        // Ticketmaster API response interception
        const originalXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            this.__url = url;
            return originalXHROpen.call(this, method, url, ...args);
        };
        
        const originalXHRSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function(data) {
            // Add realistic timing
            const delay = Math.random() * 100 + 50;
            setTimeout(() => {
                originalXHRSend.call(this, data);
            }, delay);
        };
        
        // Device properties spoofing
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4 + Math.floor(Math.random() * 4)
        });
        
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 4 + Math.random() * 4
        });
        
        // Advanced canvas protection
        const canvas2DContext = CanvasRenderingContext2D.prototype;
        const originalFillText = canvas2DContext.fillText;
        canvas2DContext.fillText = function(text, x, y, maxWidth) {
            const noise = () => (Math.random() - 0.5) * 0.001;
            return originalFillText.call(this, text, x + noise(), y + noise(), maxWidth);
        };
        
        // WebRTC leak protection
        if (window.RTCPeerConnection) {
            const originalCreateDataChannel = RTCPeerConnection.prototype.createDataChannel;
            RTCPeerConnection.prototype.createDataChannel = function(label, options) {
                console.debug('WebRTC data channel creation blocked for stealth');
                throw new Error('WebRTC disabled for privacy');
            };
        }
        
        // Battery API spoofing
        if (navigator.getBattery) {
            navigator.getBattery = async () => ({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 0.8 + Math.random() * 0.2,
                onchargingchange: null,
                onchargingtimechange: null,
                ondischargingtimechange: null,
                onlevelchange: null
            });
        }
        """)

    async def _setup_api_interception(self):
        """Setup intelligent API request monitoring"""
        async def handle_response(response):
            url = response.url
            
            # Capture Ticketmaster API responses
            if 'ticketmaster.com' in url or 'ticketmaster.it' in url:
                try:
                    # Check for inventory APIs
                    if any(re.search(pattern, url) for pattern in self.api_patterns.values()):
                        content_type = response.headers.get('content-type', '')
                        
                        if 'application/json' in content_type:
                            try:
                                data = await response.json()
                                await self._process_api_response(url, data)
                            except:
                                pass
                
                    # Extract headers for future requests
                    if '/api/' in url:
                        for header, value in response.headers.items():
                            if header.lower() in ['x-tm-api-key', 'authorization', 'x-csrf-token']:
                                self.api_headers[header] = value
                                
                except Exception as e:
                    logger.debug(f"Error processing response from {url}: {e}")
        
        self.page.on('response', handle_response)

    async def _process_api_response(self, url: str, data: dict):
        """Process API responses for ticket opportunities"""
        try:
            # Check for offers/inventory data
            if '_embedded' in data:
                events = data['_embedded'].get('events', [])
                for event in events:
                    if 'priceRanges' in event:
                        await self._extract_from_price_ranges(event)
            
            # Check for direct inventory
            if 'offers' in data:
                await self._extract_from_offers(data['offers'])
                
            # Check for GraphQL responses
            if 'data' in data and 'event' in data['data']:
                await self._extract_from_graphql(data['data']['event'])
                
        except Exception as e:
            logger.debug(f"Error processing API data: {e}")

    async def _extract_from_price_ranges(self, event_data: dict):
        """Extract opportunities from price range data"""
        try:
            price_ranges = event_data.get('priceRanges', [])
            for price_range in price_ranges:
                min_price = price_range.get('min', 0)
                max_price = price_range.get('max', 0)
                currency = price_range.get('currency', 'EUR')
                
                if min_price <= self.max_price:
                    logger.info(f"🎯 TICKETMASTER API HIT: {event_data.get('name')} - €{min_price}-€{max_price}")
                    
        except Exception as e:
            logger.debug(f"Error extracting from price ranges: {e}")

    async def _configure_human_behavior(self):
        """Configure realistic human browsing behavior"""
        # Set realistic viewport
        await self.page.set_viewport_size({
            'width': self.profile.viewport_width,
            'height': self.profile.viewport_height
        })
        
        # Setup request interception for optimization
        await self.page.route('**/*', self._handle_request)
        
        # Add realistic user behavior tracking
        await self.page.add_init_script("""
        let mouseMovements = 0;
        let keystrokes = 0;
        let scrolls = 0;
        let focusChanges = 0;
        
        document.addEventListener('mousemove', () => mouseMovements++);
        document.addEventListener('keydown', () => keystrokes++);
        document.addEventListener('scroll', () => scrolls++);
        document.addEventListener('focus', () => focusChanges++);
        document.addEventListener('blur', () => focusChanges++);
        
        window.getBehaviorMetrics = () => ({
            mouseMovements, keystrokes, scrolls, focusChanges,
            uptime: Date.now() - window.__stealth_initialized__.timestamp
        });
        """)

    async def _handle_request(self, route):
        """Intelligent request handling with blocking and optimization"""
        request = route.request
        url = request.url
        
        # Allow Ticketmaster core requests
        if any(domain in url for domain in ['ticketmaster.com', 'ticketmaster.it', 'livenation.com']):
            await route.continue_()
            return
        
        # Block unnecessary resources for speed
        if request.resource_type in ['image', 'media', 'font']:
            if not any(x in url for x in ['logo', 'icon', 'avatar']):
                await route.abort()
                return
        
        # Block tracking and analytics
        tracking_domains = [
            'google-analytics.com', 'googletagmanager.com', 'doubleclick.net',
            'facebook.com', 'connect.facebook.net', 'hotjar.com',
            'mixpanel.com', 'segment.com', 'amplitude.com'
        ]
        
        if any(domain in url for domain in tracking_domains):
            await route.abort()
            return
        
        # Continue with request
        await route.continue_()

    async def check_opportunities(self) -> List[EnhancedTicketOpportunity]:
        """Check for ticket opportunities with advanced strategies"""
        if not self.page:
            await self.initialize()
        
        opportunities = []
        
        try:
            logger.debug(f"Checking Ticketmaster opportunities for {self.event_name}")
            
            # Navigate with human-like behavior
            await self._navigate_humanlike()
            
            # Wait for dynamic content
            await self._wait_for_content_load()
            
            # Try multiple detection strategies
            opportunities.extend(await self._check_dom_listings())
            opportunities.extend(await self._check_api_data())
            opportunities.extend(await self._check_json_ld())
            
            # Update last check time
            self.last_check = datetime.now()
            
            if opportunities:
                logger.critical(f"🚀 FOUND {len(opportunities)} OPPORTUNITIES FOR {self.event_name}")
                
        except Exception as e:
            logger.error(f"Error checking Ticketmaster opportunities: {e}")
            
            # Recovery attempt
            try:
                await self.page.reload(wait_until='networkidle', timeout=15000)
            except:
                pass
        
        return opportunities

    async def _navigate_humanlike(self):
        """Navigate to target URL with human-like behavior"""
        # Add random delay before navigation
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Navigate with realistic wait
        await self.page.goto(self.url, wait_until='networkidle', timeout=30000)
        
        # Simulate human reading time
        await asyncio.sleep(random.uniform(2.0, 5.0))
        
        # Random mouse movement
        viewport = await self.page.viewport_size()
        if viewport:
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Random scrolling
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 600)
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(1.0, 2.0))

    async def _wait_for_content_load(self):
        """Wait for dynamic content to load"""
        try:
            # Wait for loading indicators to disappear
            for selector in self.selectors['loading']:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.wait_for_selector(selector, state='hidden', timeout=10000)
                except:
                    pass
            
            # Wait for ticket content
            ticket_selectors = self.selectors['ticket_cards']
            for selector in ticket_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Content load wait timeout: {e}")

    async def _check_dom_listings(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities from DOM"""
        opportunities = []
        
        try:
            # Find ticket cards
            ticket_cards = []
            for selector in self.selectors['ticket_cards']:
                try:
                    cards = await self.page.locator(selector).all()
                    if cards:
                        ticket_cards = cards
                        break
                except:
                    continue
            
            if not ticket_cards:
                logger.debug("No ticket cards found in DOM")
                return opportunities
            
            logger.debug(f"Found {len(ticket_cards)} ticket cards")
            
            for i, card in enumerate(ticket_cards):
                try:
                    # Extract price
                    price = 0.0
                    price_text = "N/A"
                    
                    for price_selector in self.selectors['price']:
                        try:
                            price_element = card.locator(price_selector).first
                            if await price_element.count():
                                price_text = await price_element.inner_text()
                                # Extract numeric price
                                price_match = re.search(r'(\d+[.,]\d+|\d+)', price_text.replace(',', '.'))
                                if price_match:
                                    price = float(price_match.group(1))
                                break
                        except:
                            continue
                    
                    if price == 0 or price > self.max_price:
                        continue
                    
                    # Extract section
                    section = "General Admission"
                    for section_selector in self.selectors['section']:
                        try:
                            section_element = card.locator(section_selector).first
                            if await section_element.count():
                                section = await section_element.inner_text()
                                break
                        except:
                            continue
                    
                    # Check if section matches desired sections
                    if self.desired_sections:
                        section_lower = section.lower()
                        if not any(desired.lower() in section_lower for desired in self.desired_sections):
                            continue
                    
                    # Create opportunity
                    opportunity = EnhancedTicketOpportunity(
                        id=f"tm_{int(time.time())}_{i}",
                        platform=PlatformType.TICKETMASTER,
                        event_name=self.event_name,
                        url=self.url,
                        offer_url=self.page.url,
                        section=section,
                        price=price,
                        quantity=1,
                        detected_at=datetime.now(),
                        priority=self.priority,
                        confidence_score=0.9,
                        detection_method='dom_scraping',
                        metadata={
                            'price_text': price_text,
                            'card_index': i
                        }
                    )
                    
                    opportunities.append(opportunity)
                    logger.warning(f"🎯 TICKETMASTER DOM HIT: {section} - €{price}")
                    
                except Exception as e:
                    logger.debug(f"Error processing ticket card {i}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in DOM listings check: {e}")
        
        return opportunities

    async def _check_api_data(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities from API data in page"""
        opportunities = []
        
        try:
            # Look for embedded JSON data
            api_data = await self.page.evaluate("""
            () => {
                const data = [];
                
                // Check for embedded API responses
                const scripts = document.querySelectorAll('script[type="application/json"]');
                scripts.forEach(script => {
                    try {
                        const json = JSON.parse(script.textContent);
                        data.push(json);
                    } catch (e) {}
                });
                
                // Check for window data
                if (window.__INITIAL_STATE__) data.push(window.__INITIAL_STATE__);
                if (window.__PRELOADED_STATE__) data.push(window.__PRELOADED_STATE__);
                if (window.TM) data.push(window.TM);
                
                return data;
            }
            """)
            
            for data in api_data:
                await self._extract_from_nested_data(data, opportunities)
                
        except Exception as e:
            logger.debug(f"Error checking API data: {e}")
        
        return opportunities

    async def _extract_from_nested_data(self, data: Any, opportunities: List):
        """Recursively extract opportunities from nested data"""
        if isinstance(data, dict):
            try:
                # Look for price information
                if 'price' in data or 'cost' in data:
                    price_val = data.get('price') or data.get('cost')
                    if isinstance(price_val, (int, float)) and price_val <= self.max_price:
                        section = data.get('section', data.get('sectionName', 'Unknown'))

                        opportunity = EnhancedTicketOpportunity(
                            id=f"tm_api_{int(time.time())}_{hash(str(data))}",
                            platform=PlatformType.TICKETMASTER,
                            event_name=self.event_name,
                            url=self.url,
                            offer_url=self.page.url,
                            section=section,
                            price=price_val,
                            quantity=1,
                            detected_at=datetime.now(),
                            priority=self.priority,
                            confidence_score=0.95,
                            detection_method='api_extraction',
                            metadata={
                                'api_source': 'unknown',
                                'raw_data': str(data)[:200]
                            }
                        )

                        opportunities.append(opportunity)
            except Exception as e:
                logger.debug(f"Error processing nested data: {e}")

    async def _check_json_ld(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities from JSON-LD structured data"""
        opportunities = []
        
        try:
            json_ld_data = await self.page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                const data = [];
                scripts.forEach(script => {
                    try {
                        const json = JSON.parse(script.textContent);
                        data.push(json);
                    } catch (e) {}
                });
                return data;
            }
            """)
            
            for data in json_ld_data:
                if isinstance(data, dict) and data.get('@type') == 'Event':
                    # Extract offers from structured data
                    offers = data.get('offers', [])
                    if not isinstance(offers, list):
                        offers = [offers]
                    
                    for offer in offers:
                        if isinstance(offer, dict) and 'price' in offer:
                            price = float(offer['price'])
                            if price <= self.max_price:
                                logger.info(f"🎯 TICKETMASTER JSON-LD HIT: €{price}")
                                
        except Exception as e:
            logger.debug(f"Error checking JSON-LD: {e}")
        
        return opportunities

    async def attempt_purchase(self, opportunity: EnhancedTicketOpportunity) -> bool:
        """Attempt to purchase a ticket with advanced automation"""
        if not self.page:
            logger.error("Cannot attempt purchase: no page available")
            return False
        
        try:
            logger.critical(f"🚀 ATTEMPTING TICKETMASTER PURCHASE: {opportunity.section} - €{opportunity.price}")
            
            # Navigate to offer URL if different
            if opportunity.offer_url != self.page.url:
                await self.page.goto(opportunity.offer_url, wait_until='networkidle', timeout=20000)
            
            # Human-like delay before interaction
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Look for buy/select buttons
            buy_selectors = [
                'button:text("Buy Now")', 'button:text("Select")', 'button:text("Buy")',
                '[data-testid="buy-button"]', '[data-testid="select-button"]',
                '.purchase-btn', '.select-btn', '.buy-now-btn'
            ]
            
            button_clicked = False
            for selector in buy_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.count() and await button.is_visible():
                        # Realistic interaction delay
                        await asyncio.sleep(random.uniform(0.8, 1.5))
                        
                        # Scroll to button if needed
                        await button.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.3, 0.7))
                        
                        # Click with human-like behavior
                        await button.click()
                        logger.info(f"Clicked buy button: {selector}")
                        button_clicked = True
                        break
                        
                except Exception as e:
                    logger.debug(f"Failed to click {selector}: {e}")
                    continue
            
            if not button_clicked:
                logger.warning("No buy button found or clickable")
                return False
            
            # Wait for response/navigation
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check for success indicators
            success = await self._verify_purchase_progress()
            
            if success:
                logger.critical(f"✅ PURCHASE INITIATED SUCCESSFULLY: {opportunity.section}")
            else:
                logger.warning(f"❌ Purchase attempt unclear: {opportunity.section}")
            
            return success
            
        except Exception as e:
            logger.error(f"Purchase attempt failed: {e}")
            return False

    async def _verify_purchase_progress(self) -> bool:
        """Verify if purchase process was initiated"""
        try:
            # Look for purchase flow indicators
            progress_indicators = [
                'text=Checkout', 'text=Payment', 'text=Review Order',
                'text=Confirm Purchase', 'text=Cart', 'text=Basket',
                '[data-testid="checkout"]', '[data-testid="cart"]',
                '.checkout-page', '.payment-page', '.cart-page'
            ]
            
            for indicator in progress_indicators:
                try:
                    if await self.page.locator(indicator).count() > 0:
                        logger.info(f"Purchase progress indicator found: {indicator}")
                        return True
                except:
                    continue
            
            # Check URL for purchase flow
            current_url = self.page.url.lower()
            purchase_url_indicators = ['checkout', 'payment', 'cart', 'basket', 'order']
            
            if any(indicator in current_url for indicator in purchase_url_indicators):
                logger.info(f"Purchase flow URL detected: {current_url}")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error verifying purchase progress: {e}")
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
            logger.error(f"Error during cleanup: {e}")

# Legacy compatibility functions
async def monitor(*args, **kwargs):
    """Legacy monitor function for backward compatibility"""
    return []

async def check_ticketmaster_event(page, profile, target_cfg, gui_q=None):
    """Legacy function - redirects to new monitor class"""
    logger.warning("Using legacy check_ticketmaster_event - please update to TicketmasterMonitor class")
    
    # Create temporary monitor instance
    monitor = TicketmasterMonitor(target_cfg, profile, None, None, None)
    monitor.page = page
    
    return await monitor.check_opportunities()