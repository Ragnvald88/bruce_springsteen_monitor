"""
Unified Handler v4.0 - Fixes blocking issues and improves detection evasion
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Page, Response
from ..core.models import EnhancedTicketOpportunity
from ..core.enums import PlatformType, PriorityLevel
from ..core.human_behavior_engine import HumanBehaviorEngine
from ..core.errors import BlockedError
from ..stealth.enhanced_stealth_v4 import EnhancedStealthV4

logger = logging.getLogger(__name__)


class UnifiedHandlerV4:
    """
    Enhanced handler with improved anti-detection and monitoring
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        browser: Browser,
        behavior_engine: HumanBehaviorEngine,
        fingerprint: Dict[str, Any],
        page: Optional[Page] = None,
        context: Optional[BrowserContext] = None,
        detection_callback: Optional[Callable] = None,
        purchase_tracker: Optional[Any] = None
    ):
        self.config = config
        self.browser = browser
        self.behavior_engine = behavior_engine
        self.fingerprint = fingerprint
        self.page = page
        self.context = context
        self.detection_callback = detection_callback
        self.purchase_tracker = purchase_tracker
        
        # Platform detection
        self.url = config['url']
        self.platform = self._detect_platform(self.url)
        self.priority = PriorityLevel[config.get('priority', 'NORMAL').upper()]
        
        # Ticket preferences
        self.max_price = config.get('max_price_per_ticket', 1000)
        self.desired_sections = config.get('desired_sections', [])
        self.min_quantity = config.get('min_ticket_quantity', 1)
        self.max_quantity = config.get('max_ticket_quantity', 4)
        
        # Enhanced resource blocking for stealth
        self.blocked_resources = {
            'image', 'media', 'font', 'stylesheet',
            'other', 'texttrack', 'manifest', 'eventsource',
            'websocket'  # Block WebSocket to prevent tracking
        }
        
        # Tracking
        self.detection_indicators = []
        self.last_successful_check = datetime.now()
        self.consecutive_failures = 0
        self.session_id = f"{self.platform}_{int(time.time())}"
        
        # Platform-specific settings
        self.platform_config = self._get_platform_config()
        
        logger.info(f"UnifiedHandlerV4 initialized for {self.platform}")
        
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'fansale' in domain:
            return 'fansale'
        elif 'ticketmaster' in domain:
            return 'ticketmaster'
        elif 'vivaticket' in domain:
            return 'vivaticket'
        else:
            return 'unknown'
            
    def _get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        configs = {
            'fansale': {
                'wait_time': (3, 5),
                'scroll_behavior': 'smooth',
                'cookie_accept_delay': (1, 2),
                'max_retry': 3,
                'selectors': {
                    'tickets': '.offer-list-item, .ticket-offer, [data-testid="offer-item"]',
                    'price': '.price, .offer-price, [data-testid="price"]',
                    'section': '.sector, .section, [data-testid="section"]',
                    'quantity': '.quantity, .tickets-amount, [data-testid="quantity"]',
                    'cookie': 'button[data-testid="cookie-accept"], button:has-text("Accetta")'
                }
            },
            'ticketmaster': {
                'wait_time': (4, 6),
                'scroll_behavior': 'natural',
                'cookie_accept_delay': (2, 3),
                'max_retry': 2,
                'selectors': {
                    'tickets': '[data-testid="listing"], .ticket-listing, .event-ticket',
                    'price': '[data-testid="price"], .price-range, .ticket-price',
                    'section': '[data-testid="section"], .section-name',
                    'quantity': '[data-testid="quantity"], .ticket-quantity',
                    'queue': '.queue-it, [class*="queue"], #queueItEngine',
                    'cookie': '#onetrust-accept-btn-handler, button[title="Accept"]'
                }
            },
            'vivaticket': {
                'wait_time': (2, 4),
                'scroll_behavior': 'quick',
                'cookie_accept_delay': (1, 2),
                'max_retry': 3,
                'selectors': {
                    'tickets': '.ticket-item, .event-ticket',
                    'price': '.ticket-price',
                    'section': '.ticket-section',
                    'quantity': '.ticket-qty',
                    'cookie': '.cookie-accept, #acceptCookies'
                }
            }
        }
        
        return configs.get(self.platform, configs['fansale'])
        
    async def initialize(self):
        """Initialize browser context and page with enhanced stealth"""
        
        if not self.page or not self.context:
            raise ValueError("Page and context must be provided to UnifiedHandlerV4")
            
        # Apply enhanced stealth v4
        await EnhancedStealthV4.apply_ultra_stealth(self.page, self.context)
        
        # Set up request interception
        await self._setup_request_interception()
        
        # Configure page settings
        await self._configure_page_settings()
        
        logger.info(f"UnifiedHandlerV4 initialized with enhanced stealth for {self.platform}")
        
    async def _setup_request_interception(self):
        """Set up request interception for resource blocking"""
        
        async def handle_route(route):
            request = route.request
            resource_type = request.resource_type
            url = request.url
            
            # Block tracking and analytics
            blocked_domains = [
                'google-analytics.com', 'googletagmanager.com',
                'doubleclick.net', 'facebook.com', 'twitter.com',
                'hotjar.com', 'segment.com', 'mixpanel.com',
                'amplitude.com', 'heap.io', 'fullstory.com',
                'sentry.io', 'bugsnag.com', 'datadog.com'
            ]
            
            if any(domain in url for domain in blocked_domains):
                await route.abort()
                return
                
            # Block resource types
            if resource_type in self.blocked_resources:
                await route.abort()
                return
                
            # Continue with request
            await route.continue_()
            
        await self.page.route('**/*', handle_route)
        
    async def _configure_page_settings(self):
        """Configure page settings for stealth"""
        
        # Set viewport to common resolution
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864}
        ]
        viewport = random.choice(viewports)
        await self.page.set_viewport_size(viewport)
        
        # Set extra HTTP headers
        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        await self.page.set_extra_http_headers(headers)
        
    async def check_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Check for tickets with enhanced anti-detection"""
        
        opportunities = []
        
        try:
            # Check if we need to navigate
            if self.page.url == 'about:blank' or not self._is_on_target_page():
                await self._navigate_with_stealth()
                
            # Check for blocks before proceeding
            if await self._check_for_blocks():
                logger.warning(f"Block detected on {self.platform}")
                await self._handle_block_recovery()
                return opportunities
                
            # Platform-specific ticket extraction
            if self.platform == 'fansale':
                opportunities = await self._extract_fansale_tickets()
            elif self.platform == 'ticketmaster':
                opportunities = await self._extract_ticketmaster_tickets()
            elif self.platform == 'vivaticket':
                opportunities = await self._extract_vivaticket_tickets()
                
            # Track opportunities if tracker available
            if self.purchase_tracker and opportunities:
                await self.purchase_tracker.track_opportunities(self.platform, opportunities)
                
            # Filter by preferences
            opportunities = self._filter_opportunities(opportunities)
            
            # Update success metrics
            self.last_successful_check = datetime.now()
            self.consecutive_failures = 0
            
            logger.info(f"{self.platform}: Found {len(opportunities)} tickets")
            
        except BlockedError as e:
            logger.error(f"Blocked on {self.platform}: {e}")
            self.consecutive_failures += 1
            await self._handle_block_recovery()
        except Exception as e:
            logger.error(f"Error checking {self.platform}: {e}")
            self.consecutive_failures += 1
            
        return opportunities
        
    def _is_on_target_page(self) -> bool:
        """Check if we're on the target page"""
        current_url = self.page.url.lower()
        target_url = self.url.lower()
        
        # Handle redirects and variations
        return (target_url in current_url or 
                urlparse(current_url).netloc == urlparse(target_url).netloc)
                
    async def _navigate_with_stealth(self):
        """Navigate to target URL with stealth precautions"""
        
        logger.info(f"Navigating to {self.platform} with enhanced stealth")
        
        # Random delay before navigation
        await asyncio.sleep(random.uniform(1, 3))
        
        # Navigate with timeout
        try:
            response = await self.page.goto(
                self.url,
                wait_until='networkidle',
                timeout=30000
            )
            
            # Check response
            if response and response.status >= 400:
                await self._handle_detection_response(response)
                
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            raise
            
        # Wait for page to stabilize
        wait_min, wait_max = self.platform_config['wait_time']
        await self.behavior_engine.wait_human_duration(wait_min, wait_max)
        
        # Handle cookies
        await self._handle_cookie_banner()
        
        # Perform human-like actions
        await self._perform_human_actions()
        
    async def _check_for_blocks(self) -> bool:
        """Check if we're blocked or in a challenge"""
        
        # Check page content for block indicators
        block_indicators = [
            'access denied', 'blocked', 'forbidden',
            'cloudflare', 'challenge', 'captcha',
            'verify you are human', 'unusual activity',
            'bot detection', 'security check'
        ]
        
        try:
            page_content = await self.page.content()
            page_text = page_content.lower()
            
            for indicator in block_indicators:
                if indicator in page_text:
                    logger.warning(f"Block indicator found: {indicator}")
                    return True
                    
            # Check URL for challenge pages
            current_url = self.page.url.lower()
            if any(x in current_url for x in ['challenge', 'captcha', 'verify']):
                return True
                
            # Platform-specific checks
            if self.platform == 'ticketmaster':
                # Check for queue-it
                if await self.page.query_selector(self.platform_config['selectors'].get('queue', '')):
                    logger.info("In Ticketmaster queue")
                    return False  # Queue is not a block
                    
        except Exception as e:
            logger.error(f"Error checking for blocks: {e}")
            
        return False
        
    async def _handle_block_recovery(self):
        """Handle recovery from blocks"""
        
        logger.info(f"Initiating block recovery for {self.platform}")
        
        # Report to detection callback
        if self.detection_callback:
            await self.detection_callback({
                'platform': self.platform,
                'type': 'block_recovery',
                'severity': 'high',
                'message': f"Block detected, attempting recovery",
                'details': {'consecutive_failures': self.consecutive_failures}
            })
            
        # Wait before retry
        wait_time = min(60 * (2 ** self.consecutive_failures), 300)  # Exponential backoff, max 5 min
        logger.info(f"Waiting {wait_time}s before retry")
        await asyncio.sleep(wait_time)
        
        # Clear cookies and storage
        await self.context.clear_cookies()
        await self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        
        # Navigate away and back
        await self.page.goto('about:blank')
        await asyncio.sleep(random.uniform(2, 5))
        
    async def _handle_cookie_banner(self):
        """Handle cookie consent banners"""
        
        cookie_selector = self.platform_config['selectors'].get('cookie', '')
        if not cookie_selector:
            return
            
        try:
            # Wait for cookie banner
            cookie_button = await self.page.wait_for_selector(
                cookie_selector,
                timeout=5000,
                state='visible'
            )
            
            if cookie_button:
                # Human-like delay
                delay_min, delay_max = self.platform_config['cookie_accept_delay']
                await asyncio.sleep(random.uniform(delay_min, delay_max))
                
                # Click with human behavior
                await self.behavior_engine.click_element(self.page, cookie_selector)
                logger.debug("Accepted cookies")
                
        except:
            # No cookie banner or timeout
            pass
            
    async def _perform_human_actions(self):
        """Perform human-like actions on the page"""
        
        # Random scroll
        scroll_amount = random.randint(100, 500)
        await self.behavior_engine.scroll_page(self.page, "down", scroll_amount)
        
        # Random mouse movement
        viewport = self.page.viewport_size
        if viewport:
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                await self.page.mouse.move(x, y, steps=random.randint(10, 20))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
        # Occasional pause
        if random.random() < 0.3:
            await asyncio.sleep(random.uniform(1, 3))
            
    async def _extract_fansale_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Extract tickets from Fansale with improved selectors"""
        
        opportunities = []
        selectors = self.platform_config['selectors']
        
        try:
            # Wait for tickets to load
            await self.page.wait_for_selector(selectors['tickets'], timeout=10000)
            
            # Extract ticket data
            tickets = await self.page.query_selector_all(selectors['tickets'])
            logger.debug(f"Found {len(tickets)} ticket elements on Fansale")
            
            for i, ticket in enumerate(tickets[:20]):  # Limit to prevent overload
                try:
                    # Extract data with multiple selector options
                    price_elem = await ticket.query_selector(selectors['price'])
                    section_elem = await ticket.query_selector(selectors['section'])
                    quantity_elem = await ticket.query_selector(selectors['quantity'])
                    
                    if not price_elem:
                        continue
                        
                    # Get text content
                    price_text = await price_elem.text_content()
                    section_text = await section_elem.text_content() if section_elem else "General"
                    quantity_text = await quantity_elem.text_content() if quantity_elem else "1"
                    
                    # Parse values
                    price = self._parse_price(price_text)
                    section = section_text.strip()
                    quantity = self._parse_quantity(quantity_text)
                    
                    # Get ticket URL if available
                    ticket_link = await ticket.query_selector('a')
                    offer_url = await ticket_link.get_attribute('href') if ticket_link else self.page.url
                    if offer_url and not offer_url.startswith('http'):
                        offer_url = f"https://www.fansale.it{offer_url}"
                    
                    # Create opportunity
                    opportunity = EnhancedTicketOpportunity(
                        id=f"fansale_{self.session_id}_{i}",
                        platform=PlatformType.FANSALE,
                        event_name=self.config.get('event_name', 'Unknown'),
                        url=self.url,
                        offer_url=offer_url,
                        section=section,
                        price=price,
                        quantity=quantity,
                        detected_at=datetime.now(),
                        priority=self.priority,
                        confidence_score=0.9,
                        detection_method='dom',
                        metadata={'session': self.session_id}
                    )
                    
                    opportunities.append(opportunity)
                    
                except Exception as e:
                    logger.debug(f"Error extracting ticket {i}: {e}")
                    
        except Exception as e:
            logger.debug(f"No tickets found on Fansale: {e}")
            
        return opportunities
        
    async def _extract_ticketmaster_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Extract tickets from Ticketmaster"""
        
        opportunities = []
        selectors = self.platform_config['selectors']
        
        try:
            # Check if in queue
            if await self.page.query_selector(selectors.get('queue', '')):
                logger.info("In Ticketmaster queue - waiting")
                return opportunities
                
            # Wait for tickets
            await self.page.wait_for_selector(selectors['tickets'], timeout=10000)
            
            # Extract tickets
            tickets = await self.page.query_selector_all(selectors['tickets'])
            logger.debug(f"Found {len(tickets)} ticket elements on Ticketmaster")
            
            # Similar extraction logic as Fansale
            # ... (implement based on actual Ticketmaster structure)
            
        except Exception as e:
            logger.debug(f"No tickets found on Ticketmaster: {e}")
            
        return opportunities
        
    async def _extract_vivaticket_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Extract tickets from Vivaticket"""
        
        # Similar to other platforms
        # ... (implement based on actual Vivaticket structure)
        
        return []
        
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        if not price_text:
            return 0.0
            
        # Remove currency symbols and normalize
        price_text = price_text.replace('€', '').replace('EUR', '')
        price_text = price_text.replace('$', '').replace('USD', '')
        price_text = price_text.replace(',', '.').strip()
        
        # Extract number
        import re
        numbers = re.findall(r'[\d.]+', price_text)
        
        if numbers:
            try:
                return float(numbers[0])
            except:
                pass
                
        return 0.0
        
    def _parse_quantity(self, quantity_text: str) -> int:
        """Parse quantity from text"""
        if not quantity_text:
            return 1
            
        import re
        numbers = re.findall(r'\d+', quantity_text)
        
        if numbers:
            try:
                return int(numbers[0])
            except:
                pass
                
        return 1
        
    def _filter_opportunities(self, opportunities: List[EnhancedTicketOpportunity]) -> List[EnhancedTicketOpportunity]:
        """Filter opportunities by preferences"""
        
        filtered = []
        
        for opp in opportunities:
            # Price filter
            if opp.price > self.max_price:
                continue
                
            # Quantity filter
            if opp.quantity < self.min_quantity or opp.quantity > self.max_quantity:
                continue
                
            # Section filter
            if self.desired_sections:
                section_lower = opp.section.lower()
                if not any(desired.lower() in section_lower for desired in self.desired_sections):
                    continue
                    
            filtered.append(opp)
            
        return filtered
        
    async def _handle_detection_response(self, response: Response):
        """Handle potential bot detection response"""
        
        status = response.status
        url = response.url
        
        # Determine detection type
        detection_type = 'unknown'
        severity = 'medium'
        message = f"HTTP {status} response"
        
        if status == 403:
            detection_type = 'access_denied'
            severity = 'high'
            message = "Access denied (403)"
        elif status == 429:
            detection_type = 'rate_limit'
            severity = 'medium'
            message = "Rate limit detected"
        elif status >= 500:
            detection_type = 'server_error'
            severity = 'low'
            message = f"Server error ({status})"
            
        # Report detection
        if self.detection_callback:
            await self.detection_callback({
                'platform': self.platform,
                'type': detection_type,
                'severity': severity,
                'message': message,
                'details': {
                    'url': url,
                    'status': status,
                    'session': self.session_id
                }
            })
            
        # Take action based on severity
        if severity == 'high':
            raise BlockedError(f"Critical detection: {message}")
            
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return {
            'platform': self.platform,
            'session': self.session_id,
            'personality': self.behavior_engine.personality.value,
            'detection_count': len(self.detection_indicators),
            'consecutive_failures': self.consecutive_failures,
            'last_success': self.last_successful_check.isoformat(),
            'behavior_stats': self.behavior_engine.get_behavior_stats()
        }