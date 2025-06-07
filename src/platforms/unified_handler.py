# src/platforms/unified_handler.py
"""
Unified Platform Handler - StealthMaster AI v2.0
Single powerful engine handling all ticketing platforms with maximum efficiency
"""

import asyncio
import logging
import time
import json
import re
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from abc import ABC, abstractmethod

from playwright.async_api import Page, BrowserContext, Response
from ..core.models import EnhancedTicketOpportunity
from ..core.enums import PlatformType, PriorityLevel
from ..profiles.models import BrowserProfile
from ..core.errors import BlockedError, PlatformError
from src.core.stealth.stealth_engine import get_stealthmaster_engine

logger = logging.getLogger(__name__)


class UnifiedTicketingHandler:
    """Single handler for all ticketing platforms with intelligent adaptation"""
    
    def __init__(self, config: Dict[str, Any], profile: BrowserProfile, 
                 browser_manager, connection_manager, cache):
        self.config = config
        self.profile = profile
        self.browser_manager = browser_manager
        self.connection_manager = connection_manager
        self.cache = cache
        
        # Detect platform from URL
        self.platform = self._detect_platform(config['url'])
        self.platform_adapter = self._get_platform_adapter()
        
        # Common configuration
        self.event_name = config.get('event_name', 'Unknown Event')
        self.url = config['url']
        self.priority = PriorityLevel[config.get('priority', 'NORMAL').upper()]
        self.max_price = config.get('max_price_per_ticket', 1000.0)
        self.desired_sections = config.get('desired_sections', [])
        
        # State management
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.detected_opportunities = set()
        
        # StealthMaster AI Engine
        self.stealth_engine = get_stealthmaster_engine()
        
        # Performance tracking
        self.scan_metrics = {
            'scans': 0,
            'opportunities_found': 0,
            'blocks_encountered': 0,
            'avg_scan_time': 0
        }
    
    def _detect_platform(self, url: str) -> PlatformType:
        """Intelligently detect platform from URL"""
        domain_mapping = {
            'fansale': PlatformType.FANSALE,
            'ticketmaster': PlatformType.TICKETMASTER,
            'vivaticket': PlatformType.VIVATICKET
        }
        
        for keyword, platform in domain_mapping.items():
            if keyword in url.lower():
                return platform
        
        raise ValueError(f"Unknown platform for URL: {url}")
    
    def _get_platform_adapter(self) -> 'PlatformAdapter':
        """Get platform-specific adapter"""
        adapters = {
            PlatformType.FANSALE: FansaleAdapter(),
            PlatformType.TICKETMASTER: TicketmasterAdapter(),
            PlatformType.VIVATICKET: VivaticketAdapter()
        }
        
        return adapters.get(self.platform, DefaultAdapter())
    
    async def initialize(self) -> None:
        """Initialize unified handler with StealthMaster AI protection"""
        logger.info(f"🚀 Initializing Unified Handler for {self.platform.value}")
        
        # Create stealth browser context
        self.browser_context = await self.browser_manager.create_context(self.profile)
        self.page = await self.browser_context.new_page()
        
        # Apply StealthMaster AI v2.0 protection
        await self.stealth_engine.apply_ultimate_stealth(
            self.browser_manager.browser,
            self.browser_context,
            self.page,
            self.platform.value
        )
        
        # Platform-specific initialization
        await self.platform_adapter.initialize(self.page, self.config)
        
        # Set up intelligent request interception
        await self._setup_intelligent_networking()
        
        # Perform authentication if needed
        if self.config.get('authentication', {}).get('enabled'):
            await self._perform_unified_authentication()
        
        logger.info(f"✅ Unified Handler ready for {self.event_name}")
    
    async def check_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Unified ticket checking with platform adaptation"""
        start_time = time.time()
        self.scan_metrics['scans'] += 1
        
        try:
            # Navigate if needed
            if self.page.url != self.url:
                await self._navigate_with_stealth()
            
            # Wait for platform-specific content
            await self.platform_adapter.wait_for_content(self.page)
            
            # Extract opportunities using unified extraction
            opportunities = await self._extract_opportunities()
            
            # Update metrics
            scan_time = time.time() - start_time
            self._update_scan_metrics(scan_time, len(opportunities))
            
            if opportunities:
                logger.critical(f"🎯 TICKETS FOUND on {self.platform.value}!")
                logger.critical(f"   Found {len(opportunities)} opportunities in {scan_time:.2f}s")
                
                # Log top opportunities
                for i, opp in enumerate(opportunities[:3], 1):
                    logger.critical(f"   #{i}: {opp.section} - €{opp.price}")
            
            return opportunities
            
        except BlockedError:
            self.scan_metrics['blocks_encountered'] += 1
            await self._handle_block_detection()
            raise
        except Exception as e:
            logger.error(f"Check failed: {e}")
            raise
    
    async def _navigate_with_stealth(self) -> None:
        """Navigate to URL with human-like behavior"""
        logger.info(f"Navigating to {self.url}")
        
        # Random pre-navigation delay
        await asyncio.sleep(0.5 + random.random() * 1.5)
        
        # Navigate with realistic timeout
        await self.page.goto(
            self.url,
            wait_until='domcontentloaded',
            timeout=30000
        )
        
        # Simulate human page scanning
        await self._simulate_human_scanning()
    
    async def _simulate_human_scanning(self) -> None:
        """Simulate human page scanning behavior"""
        # Scroll patterns
        scroll_positions = [0.2, 0.5, 0.3, 0.7, 0.4]
        
        for position in scroll_positions:
            target_y = int(await self.page.evaluate("document.body.scrollHeight") * position)
            
            await self.page.evaluate(f"""
                window.scrollTo({{
                    top: {target_y},
                    behavior: 'smooth'
                }});
            """)
            
            await asyncio.sleep(0.5 + random.random() * 1.0)
        
        # Return to relevant section
        await self.page.evaluate("""
            const ticketSection = document.querySelector('[class*="ticket"], [class*="offer"], [id*="ticket"]');
            if (ticketSection) {
                ticketSection.scrollIntoView({behavior: 'smooth', block: 'center'});
            }
        """)
    
    async def _extract_opportunities(self) -> List[EnhancedTicketOpportunity]:
        """Extract opportunities using multiple methods"""
        opportunities = []
        
        # Method 1: DOM extraction
        dom_opportunities = await self._extract_from_dom()
        opportunities.extend(dom_opportunities)
        
        # Method 2: API interception
        api_opportunities = await self._extract_from_api()
        opportunities.extend(api_opportunities)
        
        # Method 3: JavaScript variables
        js_opportunities = await self._extract_from_javascript()
        opportunities.extend(js_opportunities)
        
        # Deduplicate and filter
        unique_opportunities = self._deduplicate_opportunities(opportunities)
        filtered = self._apply_filters(unique_opportunities)
        
        return filtered
    
    async def _extract_from_dom(self) -> List[EnhancedTicketOpportunity]:
        """Extract tickets from DOM using platform-specific selectors"""
        selectors = self.platform_adapter.get_ticket_selectors()
        opportunities = []
        
        for selector_group in selectors:
            try:
                elements = await self.page.query_selector_all(selector_group['container'])
                
                for element in elements[:50]:  # Limit to prevent overload
                    try:
                        # Extract using platform adapter
                        data = await self.platform_adapter.extract_ticket_data(
                            self.page, element, selector_group
                        )
                        
                        if data and self._validate_ticket_data(data):
                            opportunity = self._create_opportunity(data, 'dom')
                            opportunities.append(opportunity)
                            
                    except Exception as e:
                        logger.debug(f"Element extraction error: {e}")
                        
            except Exception as e:
                logger.debug(f"Selector group error: {e}")
        
        return opportunities
    
    async def _extract_from_api(self) -> List[EnhancedTicketOpportunity]:
        """Extract from intercepted API responses"""
        # This would be populated by response interception
        return self.platform_adapter.parse_api_responses(self._api_responses)
    
    async def _extract_from_javascript(self) -> List[EnhancedTicketOpportunity]:
        """Extract from JavaScript variables"""
        js_extraction_script = self.platform_adapter.get_js_extraction_script()
        
        try:
            js_data = await self.page.evaluate(js_extraction_script)
            if js_data:
                return self.platform_adapter.parse_js_data(js_data)
        except Exception as e:
            logger.debug(f"JS extraction error: {e}")
        
        return []
    
    def _validate_ticket_data(self, data: Dict[str, Any]) -> bool:
        """Validate extracted ticket data"""
        required_fields = ['price', 'section']
        return all(field in data and data[field] is not None for field in required_fields)
    
    def _create_opportunity(self, data: Dict[str, Any], source: str) -> EnhancedTicketOpportunity:
        """Create opportunity object from data"""
        opportunity_id = f"{self.platform.value}_{source}_{hash(json.dumps(data, sort_keys=True))}"
        
        return EnhancedTicketOpportunity(
            id=opportunity_id,
            platform=self.platform,
            event_name=self.event_name,
            url=self.url,
            offer_url=self.page.url,
            section=data.get('section', 'Unknown'),
            price=float(data.get('price', 0)),
            quantity=int(data.get('quantity', 1)),
            detected_at=datetime.now(),
            priority=self.priority,
            confidence_score=data.get('confidence', 0.8),
            detection_method=source,
            metadata=data.get('metadata', {})
        )
    
    def _deduplicate_opportunities(self, opportunities: List[EnhancedTicketOpportunity]) -> List[EnhancedTicketOpportunity]:
        """Remove duplicate opportunities"""
        seen = set()
        unique = []
        
        for opp in opportunities:
            key = (opp.platform, opp.section, opp.price, opp.quantity)
            if key not in seen:
                seen.add(key)
                unique.append(opp)
        
        return unique
    
    def _apply_filters(self, opportunities: List[EnhancedTicketOpportunity]) -> List[EnhancedTicketOpportunity]:
        """Apply user-defined filters"""
        filtered = []
        
        for opp in opportunities:
            # Price filter
            if opp.price > self.max_price:
                continue
            
            # Section filter
            if self.desired_sections:
                section_lower = opp.section.lower()
                if not any(desired.lower() in section_lower for desired in self.desired_sections):
                    continue
            
            # Platform-specific filters
            if self.platform_adapter.apply_custom_filter(opp, self.config):
                filtered.append(opp)
        
        return filtered
    
    async def _setup_intelligent_networking(self) -> None:
        """Set up intelligent request handling"""
        self._api_responses = []
        
        async def handle_response(response: Response) -> None:
            """Intelligently handle responses"""
            url = response.url
            
            # Check if it's an API endpoint
            if self.platform_adapter.is_api_endpoint(url):
                try:
                    data = await response.json()
                    self._api_responses.append({
                        'url': url,
                        'data': data,
                        'timestamp': time.time()
                    })
                except:
                    pass
            
            # Check for blocks
            if response.status in [403, 429, 503]:
                logger.warning(f"Potential block detected: {response.status}")
                await self._handle_block_response(response)
        
        # Set up response handler
        self.page.on('response', handle_response)
        
        # Set up request interception for optimization
        await self.page.route('**/*', self._optimize_request)
    
    async def _optimize_request(self, route) -> None:
        """Optimize requests for speed and stealth"""
        request = route.request
        resource_type = request.resource_type
        url = request.url
        
        # Block unnecessary resources
        block_patterns = [
            'google-analytics', 'doubleclick', 'facebook',
            'hotjar', 'mixpanel', 'segment', 'amplitude'
        ]
        
        if any(pattern in url for pattern in block_patterns):
            await route.abort()
            return
        
        # Optimize images/media
        if resource_type in ['image', 'media', 'font']:
            if not self.platform_adapter.is_critical_resource(url):
                await route.abort()
                return
        
        # Add platform-specific headers
        headers = request.headers.copy()
        headers.update(self.platform_adapter.get_custom_headers())
        
        await route.continue_(headers=headers)
    
    async def _perform_unified_authentication(self) -> None:
        """Unified authentication handler"""
        auth_config = self.config.get('authentication', {}).get('platforms', {}).get(self.platform.value)
        
        if not auth_config:
            logger.warning(f"No auth config for {self.platform.value}")
            return
        
        logger.info(f"🔐 Performing authentication for {self.platform.value}")
        
        # Navigate to login page
        login_url = self.platform_adapter.get_login_url(self.url)
        await self.page.goto(login_url)
        
        # Wait for login form
        await self.platform_adapter.wait_for_login_form(self.page)
        
        # Perform human-like login
        await self._human_like_login(auth_config)
        
        # Verify login success
        success = await self.platform_adapter.verify_login_success(self.page)
        
        if success:
            logger.info(f"✅ Authentication successful for {self.platform.value}")
        else:
            logger.error(f"❌ Authentication failed for {self.platform.value}")
    
    async def _human_like_login(self, auth_config: Dict[str, Any]) -> None:
        """Perform login with human-like behavior"""
        username = auth_config.get('username', '')
        password = auth_config.get('password', '')
        
        # Find and fill username
        username_selector = self.platform_adapter.get_username_selector()
        await self._human_like_type(username_selector, username)
        
        # Tab to password field
        await self.page.keyboard.press('Tab')
        await asyncio.sleep(0.5 + random.random() * 0.5)
        
        # Fill password
        password_selector = self.platform_adapter.get_password_selector()
        await self._human_like_type(password_selector, password)
        
        # Submit form
        await asyncio.sleep(1 + random.random())
        submit_selector = self.platform_adapter.get_submit_selector()
        await self.page.click(submit_selector)
    
    async def _human_like_type(self, selector: str, text: str) -> None:
        """Type with human-like speed and patterns"""
        await self.page.click(selector)
        await asyncio.sleep(0.3)
        
        for char in text:
            await self.page.keyboard.type(char)
            # Variable delay between keystrokes
            delay = random.uniform(0.05, 0.15)
            if random.random() < 0.1:  # 10% chance of longer pause
                delay += random.uniform(0.2, 0.5)
            await asyncio.sleep(delay)
    
    async def _handle_block_detection(self) -> None:
        """Handle detection and implement recovery"""
        logger.warning(f"🚨 Block detected on {self.platform.value}")
        
        # Increase stealth
        await self.page.evaluate("""
            window.__stealthConfig = window.__stealthConfig || {};
            window.__stealthConfig.stealthLevel = 'maximum';
            window.__stealthConfig.activityRate *= 0.5;
        """)
        
        # Platform-specific recovery
        await self.platform_adapter.handle_block_recovery(self.page)
        
        # Cool down period
        cooldown = 30 + random.random() * 30
        logger.info(f"Cooling down for {cooldown:.1f} seconds")
        await asyncio.sleep(cooldown)
    
    async def _handle_block_response(self, response: Response) -> None:
        """Handle blocked responses"""
        if response.status == 429:
            retry_after = response.headers.get('retry-after')
            if retry_after:
                logger.info(f"Rate limited - waiting {retry_after} seconds")
                await asyncio.sleep(int(retry_after))
    
    def _update_scan_metrics(self, scan_time: float, opportunities_found: int) -> None:
        """Update performance metrics"""
        self.scan_metrics['opportunities_found'] += opportunities_found
        
        # Update average scan time
        total_scans = self.scan_metrics['scans']
        prev_avg = self.scan_metrics['avg_scan_time']
        self.scan_metrics['avg_scan_time'] = (prev_avg * (total_scans - 1) + scan_time) / total_scans
        
        # Log performance
        if total_scans % 10 == 0:
            logger.info(f"Performance: {total_scans} scans, "
                       f"avg {self.scan_metrics['avg_scan_time']:.2f}s, "
                       f"{self.scan_metrics['opportunities_found']} opportunities found")


class PlatformAdapter(ABC):
    """Abstract base for platform-specific adaptations"""
    
    @abstractmethod
    def get_ticket_selectors(self) -> List[Dict[str, str]]:
        """Get platform-specific selectors"""
        pass
    
    @abstractmethod
    def extract_ticket_data(self, page: Page, element, selectors: Dict) -> Dict[str, Any]:
        """Extract ticket data from element"""
        pass
    
    @abstractmethod
    def is_api_endpoint(self, url: str) -> bool:
        """Check if URL is an API endpoint"""
        pass
    
    def apply_custom_filter(self, opportunity: EnhancedTicketOpportunity, config: Dict) -> bool:
        """Apply platform-specific filters"""
        return True
    
    def get_custom_headers(self) -> Dict[str, str]:
        """Get platform-specific headers"""
        return {}


class FansaleAdapter(PlatformAdapter):
    """Fansale-specific adaptations"""
    
    def get_ticket_selectors(self) -> List[Dict[str, str]]:
        return [
            {
                'container': 'div[class*="offer-list"] > div[class*="offer"]',
                'price': '[class*="price"]',
                'section': '[class*="category"], [class*="section"]',
                'quantity': '[class*="quantity"], [class*="numero"]'
            },
            {
                'container': 'ul[class*="ticket"] li',
                'price': '.prezzo, .price',
                'section': '.categoria, .settore',
                'quantity': '.quantita'
            }
        ]
    
    async def extract_ticket_data(self, page: Page, element, selectors: Dict) -> Dict[str, Any]:
        """Extract Fansale ticket data"""
        data = {}
        
        try:
            # Price extraction with Italian format handling
            price_elem = await element.query_selector(selectors['price'])
            if price_elem:
                price_text = await price_elem.inner_text()
                price_text = price_text.replace('€', '').replace('.', '').replace(',', '.').strip()
                data['price'] = float(price_text)
            
            # Section extraction
            section_elem = await element.query_selector(selectors['section'])
            if section_elem:
                data['section'] = await section_elem.inner_text()
            
            # Quantity
            qty_elem = await element.query_selector(selectors['quantity'])
            if qty_elem:
                qty_text = await qty_elem.inner_text()
                data['quantity'] = int(re.search(r'\d+', qty_text).group() if re.search(r'\d+', qty_text) else 1)
            else:
                data['quantity'] = 1
            
            # Fansale-specific: Check for fair deal
            fair_deal = await element.query_selector('[class*="fair-deal"]')
            data['metadata'] = {
                'is_fair_deal': fair_deal is not None,
                'platform': 'fansale'
            }
            
        except Exception as e:
            logger.debug(f"Fansale extraction error: {e}")
        
        return data
    
    def is_api_endpoint(self, url: str) -> bool:
        patterns = ['/api/', '/ajax/', 'getOffers', 'loadTickets']
        return any(pattern in url for pattern in patterns)
    
    def get_login_url(self, base_url: str) -> str:
        return "https://www.fansale.it/fansale/login"
    
    def get_js_extraction_script(self) -> str:
        return """
        (() => {
            const tickets = [];
            
            // Check for Angular/React data
            if (window.__INITIAL_STATE__) {
                const state = window.__INITIAL_STATE__;
                if (state.offers) {
                    state.offers.forEach(offer => {
                        tickets.push({
                            price: offer.price,
                            section: offer.category,
                            quantity: offer.quantity,
                            metadata: {source: 'initial_state'}
                        });
                    });
                }
            }
            
            // Check jQuery data
            if (window.jQuery && jQuery._data) {
                jQuery('[data-offer]').each((i, el) => {
                    const data = jQuery(el).data();
                    if (data.offer) {
                        tickets.push({
                            price: data.offer.price,
                            section: data.offer.section,
                            quantity: data.offer.qty || 1,
                            metadata: {source: 'jquery_data'}
                        });
                    }
                });
            }
            
            return tickets;
        })();
        """


class TicketmasterAdapter(PlatformAdapter):
    """Ticketmaster-specific adaptations"""
    
    def get_ticket_selectors(self) -> List[Dict[str, str]]:
        return [
            {
                'container': '[data-testid="event-offer-card"]',
                'price': '[class*="price"]',
                'section': '[class*="section"], [class*="seating"]',
                'quantity': 'select[name="quantity"]'
            },
            {
                'container': 'div[class*="quick-picks"] button',
                'price': '[class*="price"]',
                'section': '[class*="section"]',
                'quantity': '[class*="quantity"]'
            }
        ]
    
    async def extract_ticket_data(self, page: Page, element, selectors: Dict) -> Dict[str, Any]:
        """Extract Ticketmaster ticket data"""
        data = {}
        
        try:
            # Get offer data attribute if available
            offer_data = await element.get_attribute('data-offer')
            if offer_data:
                parsed = json.loads(offer_data)
                data.update(parsed)
            
            # Fallback to DOM extraction
            if 'price' not in data:
                price_elem = await element.query_selector(selectors['price'])
                if price_elem:
                    price_text = await price_elem.inner_text()
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        data['price'] = float(price_match.group())
            
            # Section info
            if 'section' not in data:
                section_elem = await element.query_selector(selectors['section'])
                if section_elem:
                    data['section'] = await section_elem.inner_text()
            
            # Row info
            row_elem = await element.query_selector('[class*="row"]')
            if row_elem:
                row_text = await row_elem.inner_text()
                data['metadata'] = {'row': row_text}
            
        except Exception as e:
            logger.debug(f"Ticketmaster extraction error: {e}")
        
        return data
    
    def is_api_endpoint(self, url: str) -> bool:
        patterns = ['/api/', '/discovery/', '/inventory/', '/commerce/']
        return any(pattern in url for pattern in patterns)
    
    def parse_api_responses(self, responses: List[Dict]) -> List[EnhancedTicketOpportunity]:
        """Parse Ticketmaster API responses"""
        opportunities = []
        
        for response in responses:
            if '/inventory' in response['url']:
                data = response['data']
                if '_embedded' in data and 'offers' in data['_embedded']:
                    for offer in data['_embedded']['offers']:
                        # Parse offer structure
                        pass
        
        return opportunities


class VivaticketAdapter(PlatformAdapter):
    """Vivaticket-specific adaptations"""
    
    def get_ticket_selectors(self) -> List[Dict[str, str]]:
        return [
            {
                'container': 'div[class*="ticket-option"]',
                'price': '[class*="price"], .prezzo',
                'section': '[class*="sector"], .settore',
                'quantity': '[class*="quantity"]'
            }
        ]
    
    async def extract_ticket_data(self, page: Page, element, selectors: Dict) -> Dict[str, Any]:
        """Extract Vivaticket ticket data"""
        # Similar implementation to Fansale
        return {}
    
    def is_api_endpoint(self, url: str) -> bool:
        return '/api/' in url or '/webapi/' in url


class DefaultAdapter(PlatformAdapter):
    """Default adapter for unknown platforms"""
    
    def get_ticket_selectors(self) -> List[Dict[str, str]]:
        return [
            {
                'container': '[class*="ticket"], [class*="offer"]',
                'price': '[class*="price"]',
                'section': '[class*="section"]',
                'quantity': '[class*="quantity"]'
            }
        ]
    
    async def extract_ticket_data(self, page: Page, element, selectors: Dict) -> Dict[str, Any]:
        return {}
    
    def is_api_endpoint(self, url: str) -> bool:
        return '/api/' in url