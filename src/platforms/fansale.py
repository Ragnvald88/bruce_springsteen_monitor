# src/platforms/fansale.py - Ultra-Enhanced v6.0 with HTML Intelligence
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
from src.core.models import EnhancedTicketOpportunity, DataUsageTracker
from src.core.enums import PlatformType, PriorityLevel
from src.profiles.models import BrowserProfile
from src.core.errors import BlockedError, PlatformError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

class FansaleMonitor:
    """Revolutionary Fansale monitor with HTML structure intelligence"""
    
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
        
        logger.info(f"FansaleMonitor initialized for {self.event_name}")

    async def initialize(self):
        """Initialize with Fansale-specific ultra-stealth"""
        try:
            logger.info(f"Initializing Fansale ultra-stealth for {self.event_name}")
            
            # Get stealth browser context
            self.browser_context = await self.browser_manager.get_stealth_context(
                self.profile, force_new=False
            )
            
            # Create page with advanced stealth
            self.page = await self.browser_context.new_page()
            
            # Setup Fansale-specific stealth measures
            await self._inject_fansale_stealth()
            await self._setup_intelligent_blocking()
            await self._configure_advanced_behavior()
            await self._setup_api_monitoring()
            
            logger.info(f"Fansale ultra-stealth initialized for {self.event_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Fansale stealth: {e}")
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

    async def check_opportunities(self) -> List[EnhancedTicketOpportunity]:
        """Check for ticket opportunities using advanced HTML intelligence"""
        if not self.page:
            await self.initialize()
        
        opportunities = []
        
        try:
            logger.debug(f"Checking Fansale opportunities for {self.event_name}")
            
            # Navigate with human-like behavior
            await self._navigate_with_human_behavior()
            
            # Wait for content to load
            await self._wait_for_dynamic_content()
            
            # Multiple extraction strategies
            opportunities.extend(await self._extract_from_html_structure())
            opportunities.extend(await self._extract_from_data_attributes())
            opportunities.extend(await self._extract_from_javascript_variables())
            
            # Filter and validate opportunities
            opportunities = await self._filter_opportunities(opportunities)
            
            # Update state
            self.last_check = datetime.now()
            
            if opportunities:
                logger.critical(f"🚀 FOUND {len(opportunities)} FANSALE OPPORTUNITIES FOR {self.event_name}")
                
        except Exception as e:
            logger.error(f"Error checking Fansale opportunities: {e}")
            
            # Recovery attempt
            try:
                await self.page.reload(wait_until='networkidle', timeout=15000)
                await asyncio.sleep(2)
            except:
                pass
        
        return opportunities

    async def _navigate_with_human_behavior(self):
        """Navigate with sophisticated human behavior simulation"""
        # Random pre-navigation delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Navigate with realistic timeout
        await self.page.goto(self.url, wait_until='networkidle', timeout=30000)
        
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
                except:
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
            except:
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
                except:
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
                except:
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
                except:
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
                except:
                    continue

            # Check Fair Deal status
            for fair_deal_selector in self.selectors['fair_deal_indicator']:
                try:
                    fair_deal_element = container.locator(fair_deal_selector).first
                    if await fair_deal_element.count():
                        offer_data['is_fair_deal'] = True
                        break
                except:
                    continue

            # Check certified status
            for certified_selector in self.selectors['certified_indicator']:
                try:
                    certified_element = container.locator(certified_selector).first
                    if await certified_element.count():
                        offer_data['is_certified'] = True
                        break
                except:
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
                except:
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
                        /var\s+\w+\s*=\s*(\{[^}]*offer[^}]*\})/gi,
                        /const\s+\w+\s*=\s*(\{[^}]*price[^}]*\})/gi,
                        /let\s+\w+\s*=\s*(\{[^}]*ticket[^}]*\})/gi
                    ];
                    
                    patterns.forEach(pattern => {
                        const matches = content.match(pattern);
                        if (matches) {
                            matches.forEach(match => {
                                try {
                                    const jsonMatch = match.match(/\{.*\}/);
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
        """Attempt to purchase Fansale ticket with advanced automation"""
        if not self.page:
            logger.error("Cannot attempt purchase: no page available")
            return False
        
        try:
            logger.critical(f"🚀 ATTEMPTING FANSALE PURCHASE: {opportunity.section} - €{opportunity.price}")
            
            # Navigate to offer URL if different
            if opportunity.offer_url != self.page.url:
                await self.page.goto(opportunity.offer_url, wait_until='networkidle', timeout=20000)
            
            # Human-like delay before interaction
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
                logger.critical(f"✅ FANSALE PURCHASE INITIATED: {opportunity.section}")
            else:
                logger.warning(f"❌ Fansale purchase attempt unclear: {opportunity.section}")
            
            return purchase_success
            
        except Exception as e:
            logger.error(f"Fansale purchase attempt failed: {e}")
            return False

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
                except:
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
                except:
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