"""
StealthMaster AI - Unified Platform Handler
Complete rewrite with maximum stealth and minimal data usage
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

logger = logging.getLogger(__name__)


class UnifiedHandler:
    """
    Completely redesigned handler with:
    - Human-like behavior patterns
    - Minimal resource usage
    - Advanced detection evasion
    - Clear error reporting
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        browser: Browser,
        behavior_engine: HumanBehaviorEngine,
        fingerprint: Dict[str, Any],
        page: Optional[Page] = None,
        context: Optional[BrowserContext] = None,
        detection_callback: Optional[Callable] = None
    ):
        self.config = config
        self.browser = browser
        self.behavior_engine = behavior_engine
        self.fingerprint = fingerprint
        self.page = page
        self.context = context
        self.detection_callback = detection_callback
        
        logger.debug(f"UnifiedHandler.__init__ - page: {page is not None}, context: {context is not None}")
        
        # Platform detection
        self.url = config['url']
        self.platform = self._detect_platform(self.url)
        self.priority = PriorityLevel[config.get('priority', 'NORMAL').upper()]
        
        # Ticket preferences
        self.max_price = config.get('max_price_per_ticket', 1000)
        self.desired_sections = config.get('desired_sections', [])
        self.min_quantity = config.get('min_ticket_quantity', 1)
        self.max_quantity = config.get('max_ticket_quantity', 4)
        
        # Browser state is already set in __init__ parameters
        # Don't reset them here!
        
        # Resource optimization
        self.blocked_resources = {
            'image', 'media', 'font', 'stylesheet',
            'other', 'texttrack', 'manifest', 'eventsource'
        }
        
        # Detection tracking
        self.detection_indicators = []
        self.last_successful_check = datetime.now()
        
        logger.info(f"UnifiedHandler initialized for {self.platform}")
        
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
            
    async def initialize(self):
        """Initialize browser context and page"""
        
        # If page and context not provided, error
        if not self.page or not self.context:
            logger.error(f"Page: {self.page}, Context: {self.context}")
            raise ValueError("Page and context must be provided to UnifiedHandler")
        
        # Set up request interception for resource blocking
        await self.context.route('**/*', self._resource_handler)
        
        # Set up response monitoring
        self.page.on('response', self._response_monitor)
        
        logger.info(f"✅ Handler initialized for {self.platform}")
        
    async def _resource_handler(self, route):
        """Block unnecessary resources to save data"""
        
        request = route.request
        resource_type = request.resource_type
        url = request.url
        
        # Block by resource type
        if resource_type in self.blocked_resources:
            await route.abort()
            return
            
        # Block tracking/analytics
        blocked_domains = [
            'google-analytics', 'googletagmanager', 'doubleclick',
            'facebook', 'hotjar', 'mixpanel', 'segment', 'amplitude',
            'cloudflare-analytics', 'nr-data', 'newrelic',
            'sentry', 'bugsnag', 'rollbar'
        ]
        
        if any(domain in url for domain in blocked_domains):
            await route.abort()
            return
            
        # Continue with request
        await route.continue_()
        
    async def _response_monitor(self, response: Response):
        """Monitor responses for detection indicators"""
        
        status = response.status
        url = response.url
        
        # Check for blocks/challenges
        if status in [403, 429, 503]:
            await self._handle_detection_response(response)
            
        # Check for captcha/challenge pages
        if any(indicator in url.lower() for indicator in ['captcha', 'challenge', 'verify', 'blocked']):
            await self._report_detection(
                type='url_detection',
                severity='high',
                message=f"Challenge URL detected: {url}",
                details={'url': url, 'status': status}
            )
            
    async def _handle_detection_response(self, response: Response):
        """Handle potential bot detection response"""
        
        status = response.status
        url = response.url
        
        # Try to get response text
        try:
            text = await response.text()
            text_lower = text.lower()
        except:
            text_lower = ""
            
        # Determine detection type
        if status == 403:
            if 'cloudflare' in text_lower:
                detection_type = 'cloudflare_block'
                severity = 'critical'
                message = "Cloudflare bot detection"
            else:
                detection_type = 'access_denied'
                severity = 'high'
                message = "Access denied (403)"
                
        elif status == 429:
            detection_type = 'rate_limit'
            severity = 'medium'
            message = "Rate limit detected"
            
        elif status == 503:
            if 'queue-it' in text_lower:
                detection_type = 'queue_it'
                severity = 'low'
                message = "Queue-it waiting room"
            else:
                detection_type = 'service_unavailable'
                severity = 'low'
                message = "Service unavailable"
        else:
            detection_type = 'unknown'
            severity = 'medium'
            message = f"Suspicious response: {status}"
            
        await self._report_detection(
            type=detection_type,
            severity=severity,
            message=message,
            details={
                'url': url,
                'status': status,
                'platform': self.platform
            }
        )
        
    async def _report_detection(self, type: str, severity: str, message: str, details: Dict[str, Any]):
        """Report detection event"""
        
        logger.warning(f"Detection event: {message}")
        
        # Track internally
        self.detection_indicators.append({
            'timestamp': datetime.now(),
            'type': type,
            'severity': severity,
            'message': message
        })
        
        # Report to callback
        if self.detection_callback:
            await self.detection_callback({
                'platform': self.platform,
                'type': type,
                'severity': severity,
                'message': message,
                'details': details
            })
            
        # Take action based on severity
        if severity == 'critical':
            raise BlockedError(f"Critical detection: {message}")
            
    async def check_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Check for tickets with human-like behavior"""
        
        opportunities = []
        
        try:
            # Initial page load if needed
            if self.page.url == 'about:blank' or not self._is_on_target_page():
                await self._navigate_to_target()
                
            # Human-like page interaction
            await self._human_like_page_scan()
            
            # Extract tickets based on platform
            if self.platform == 'fansale':
                opportunities = await self._extract_fansale_tickets()
            elif self.platform == 'ticketmaster':
                opportunities = await self._extract_ticketmaster_tickets()
            elif self.platform == 'vivaticket':
                opportunities = await self._extract_vivaticket_tickets()
                
            # Filter by preferences
            opportunities = self._filter_opportunities(opportunities)
            
            # Update success timestamp
            if opportunities:
                self.last_successful_check = datetime.now()
                
            return opportunities
            
        except Exception as e:
            logger.error(f"Check tickets error: {e}")
            
            # Check if it's a detection
            if any(keyword in str(e).lower() for keyword in ['blocked', 'captcha', 'forbidden']):
                await self._report_detection(
                    type='error_detection',
                    severity='high',
                    message=str(e),
                    details={'error': type(e).__name__}
                )
                
            raise
            
    def _is_on_target_page(self) -> bool:
        """Check if we're on the target page"""
        
        current_url = self.page.url
        target_domain = urlparse(self.url).netloc
        current_domain = urlparse(current_url).netloc
        
        return target_domain == current_domain
        
    async def _navigate_to_target(self):
        """Navigate to target page with human behavior"""
        
        logger.info(f"Navigating to {self.url}")
        
        # Random delay before navigation
        await self.behavior_engine.wait_human_duration(0.5, 2.0)
        
        # Navigate
        response = await self.page.goto(
            self.url,
            wait_until='domcontentloaded',
            timeout=30000
        )
        
        # Check response
        if response and response.status >= 400:
            await self._handle_detection_response(response)
            
        # Wait for page to stabilize
        await self.behavior_engine.wait_human_duration(2.0, 4.0)
        
        # Accept cookies if present
        await self._handle_cookie_banner()
        
    async def _handle_cookie_banner(self):
        """Handle cookie consent banners"""
        
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accetta")',
            'button:has-text("OK")',
            '[class*="cookie"] button',
            '[id*="cookie"] button'
        ]
        
        for selector in cookie_selectors:
            try:
                button = await self.page.query_selector(selector)
                if button and await button.is_visible():
                    await self.behavior_engine.click_element(self.page, selector)
                    logger.debug("Accepted cookies")
                    break
            except:
                pass
                
    async def _human_like_page_scan(self):
        """Scan page like a human would"""
        
        # Read main content areas
        content_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '#content', '.tickets'
        ]
        
        for selector in content_selectors:
            if await self.page.query_selector(selector):
                await self.behavior_engine.read_page_section(self.page, selector)
                break
                
        # Scroll naturally
        scroll_amount = random.randint(200, 600)
        await self.behavior_engine.scroll_page(self.page, "down", scroll_amount)
        
        # Pause to "look"
        await self.behavior_engine.wait_human_duration(1.0, 3.0)
        
        # Occasional distraction
        await self.behavior_engine.simulate_distraction()
        
    async def _extract_fansale_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Extract tickets from Fansale"""
        
        opportunities = []
        
        # Fansale-specific selectors
        ticket_selector = '.offer-list-item, .ticket-offer'
        
        # Wait for tickets to load
        try:
            await self.page.wait_for_selector(ticket_selector, timeout=5000)
        except:
            logger.debug("No tickets found on page")
            return opportunities
            
        # Extract ticket data
        tickets = await self.page.query_selector_all(ticket_selector)
        
        for ticket in tickets[:20]:  # Limit to prevent overload
            try:
                # Extract data
                price_text = await ticket.query_selector('.price, .offer-price')
                section_text = await ticket.query_selector('.sector, .section')
                quantity_text = await ticket.query_selector('.quantity, .tickets-amount')
                
                if not price_text:
                    continue
                    
                # Parse values
                price = self._parse_price(await price_text.text_content())
                section = await section_text.text_content() if section_text else "General"
                quantity = self._parse_quantity(await quantity_text.text_content()) if quantity_text else 1
                
                # Create opportunity
                opportunity = EnhancedTicketOpportunity(
                    id=f"fansale_{hash(f'{section}{price}{quantity}')}",
                    platform=PlatformType.FANSALE,
                    event_name=self.config.get('event_name', 'Unknown'),
                    url=self.url,
                    offer_url=self.page.url,
                    section=section.strip(),
                    price=price,
                    quantity=quantity,
                    detected_at=datetime.now(),
                    priority=self.priority,
                    confidence_score=0.9,
                    detection_method='dom',
                    metadata={}
                )
                
                opportunities.append(opportunity)
                
            except Exception as e:
                logger.debug(f"Error extracting ticket: {e}")
                
        return opportunities
        
    async def _extract_ticketmaster_tickets(self) -> List[EnhancedTicketOpportunity]:
        """Extract tickets from Ticketmaster"""
        
        opportunities = []
        
        # Ticketmaster uses dynamic loading
        # First check if we're in queue
        if await self.page.query_selector('[class*="queue"], [class*="waiting"]'):
            logger.info("In Ticketmaster queue")
            return opportunities
            
        # Look for ticket listings
        ticket_selector = '[class*="ticket"], [class*="listing"], .event-ticket'
        
        try:
            await self.page.wait_for_selector(ticket_selector, timeout=5000)
        except:
            return opportunities
            
        # Similar extraction logic as Fansale
        # ... (implement based on actual Ticketmaster structure)
        
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
            
        # Remove currency symbols and spaces
        price_text = price_text.replace('€', '').replace('$', '').replace(',', '.')
        
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
            'personality': self.behavior_engine.personality.value,
            'detection_count': len(self.detection_indicators),
            'last_success': self.last_successful_check.isoformat(),
            'behavior_stats': self.behavior_engine.get_behavior_stats()
        }