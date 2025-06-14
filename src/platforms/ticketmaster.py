# stealthmaster/platforms/ticketmaster.py
"""Ticketmaster.it platform handler."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from playwright.async_api import Page

try:
    from ..config import Target as TargetEvent
    from ..profiles.models import Profile as UserProfile
    from .base import BasePlatformHandler
except ImportError:
    from config import Target as TargetEvent
    from profiles.models import Profile as UserProfile
    from platforms.base import BasePlatformHandler

logger = logging.getLogger(__name__)


class TicketmasterPlatform(BasePlatformHandler):
    """Handler for Ticketmaster.it ticket platform."""
    
    def __init__(self):
        """Initialize Ticketmaster handler."""
        super().__init__()
        self.base_url = "https://www.ticketmaster.it"
        self.login_url = f"{self.base_url}/member/login"
    
    async def initialize(self, page: Page) -> bool:
        """Initialize Ticketmaster-specific setup."""
        try:
            # Navigate to homepage
            await page.goto(self.base_url, wait_until="domcontentloaded")
            
            # Handle cookies
            await self.handle_cookies(page)
            
            # Handle Ticketmaster's anti-bot check
            await self._handle_queue_it(page)
            
            # Wait for page to stabilize
            await page.wait_for_timeout(3000)
            
            self._initialized = True
            logger.info("Ticketmaster handler initialized")
            return True
            
        except Exception as e:
            logger.error(f"Ticketmaster initialization error: {e}")
            return False
    
    async def login(self, page: Page, profile: UserProfile) -> bool:
        """Perform Ticketmaster login."""
        try:
            # Navigate to login
            await page.goto(self.login_url, wait_until="networkidle")
            
            # Wait for login form
            await self.wait_for_element(page, 'form[name="loginForm"]')
            
            # Email field
            email_selector = 'input[name="email"], input[id="email"], input[type="email"]'
            if not await self.safe_type(page, email_selector, profile.email):
                logger.error("Failed to enter email")
                return False
            
            # Password field
            password_selector = 'input[name="password"], input[id="password"], input[type="password"]'
            if not await self.safe_type(page, password_selector, "dummy_password"):
                logger.error("Failed to enter password")
                return False
            
            # Remember me checkbox (optional)
            remember_selector = 'input[name="rememberMe"], input[id="rememberMe"]'
            await self.safe_click(page, remember_selector)
            
            # Submit button
            submit_selector = 'button[type="submit"], input[type="submit"], button.submit-button'
            if not await self.safe_click(page, submit_selector):
                logger.error("Failed to click login button")
                return False
            
            # Wait for login to complete
            await page.wait_for_navigation(timeout=15000)
            
            # Check if logged in
            if await self._check_login_success(page):
                logger.info("Successfully logged into Ticketmaster")
                return True
            else:
                logger.error("Ticketmaster login failed")
                return False
                
        except Exception as e:
            logger.error(f"Ticketmaster login error: {e}")
            return False
    
    async def search_tickets(
        self,
        page: Page,
        event: TargetEvent
    ) -> List[Dict[str, Any]]:
        """Search for tickets on Ticketmaster."""
        try:
            # Navigate to event URL
            await page.goto(str(event.event_url), wait_until="networkidle")
            
            # Handle queue if present
            await self._handle_queue_it(page)
            
            # Click on "Find Tickets" or similar
            find_tickets_selector = (
                'button[class*="find-tickets"], '
                'button[class*="buy-tickets"], '
                'a[href*="buy"], '
                '[data-testid="find-tickets-button"]'
            )
            
            await self.safe_click(page, find_tickets_selector)
            await page.wait_for_timeout(2000)
            
            # Wait for ticket map or list
            await self.wait_for_element(
                page,
                '.ticket-map, .ticket-list, [data-testid="ticket-container"]',
                timeout=15000
            )
            
            # Extract ticket information
            tickets = await self._extract_ticketmaster_tickets(page)
            
            # Filter by preferences
            filtered = self.filter_tickets_by_preferences(tickets, event)
            
            logger.info(f"Found {len(filtered)} suitable tickets on Ticketmaster")
            return filtered
            
        except Exception as e:
            logger.error(f"Ticketmaster ticket search error: {e}")
            return []
    
    async def select_tickets(
        self,
        page: Page,
        tickets: List[Dict[str, Any]],
        quantity: int
    ) -> bool:
        """Select tickets on Ticketmaster."""
        try:
            selected = 0
            
            # Ticketmaster often uses interactive seat map
            if await self._is_seat_map_view(page):
                selected = await self._select_from_seat_map(page, tickets, quantity)
            else:
                selected = await self._select_from_list_view(page, tickets, quantity)
            
            if selected > 0:
                # Click continue/add to cart
                continue_button = await self.wait_for_element(
                    page,
                    'button[class*="continue"], button[class*="add-to-cart"], [data-testid="continue-button"]'
                )
                
                if continue_button:
                    await continue_button.click()
                    logger.info(f"Selected {selected} tickets on Ticketmaster")
                    return True
            
            logger.error("Failed to select tickets on Ticketmaster")
            return False
            
        except Exception as e:
            logger.error(f"Ticketmaster ticket selection error: {e}")
            return False
    
    async def complete_purchase(
        self,
        page: Page,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Complete purchase on Ticketmaster."""
        try:
            # Wait for checkout page
            await self.wait_for_element(
                page,
                '.checkout-container, [data-testid="checkout"]',
                timeout=10000
            )
            
            # Ticketmaster checkout flow
            # 1. Delivery method
            await self._select_delivery_method(page)
            
            # 2. Payment information
            await self._fill_payment_info(page, profile)
            
            # 3. Billing information
            await self._fill_billing_info(page, profile)
            
            # 4. Review and confirm
            review_button = await self.wait_for_element(
                page,
                'button[class*="review"], button[class*="continue-to-review"]'
            )
            
            if review_button:
                await review_button.click()
                await page.wait_for_timeout(2000)
            
            # 5. Place order
            place_order_button = await self.wait_for_element(
                page,
                'button[class*="place-order"], button[class*="complete-purchase"], [data-testid="place-order"]'
            )
            
            if place_order_button:
                await place_order_button.click()
                
                # Wait for confirmation
                confirmation = await self._wait_for_confirmation(page)
                
                if confirmation:
                    return {
                        "success": True,
                        "confirmation_number": confirmation,
                        "platform": "Ticketmaster"
                    }
            
            return {"success": False, "error": "Could not complete purchase"}
            
        except Exception as e:
            logger.error(f"Ticketmaster purchase error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_queue_it(self, page: Page) -> None:
        """Handle Queue-it virtual waiting room if present."""
        try:
            # Check for Queue-it
            if "queue-it.net" in page.url or await page.query_selector(".queue-it"):
                logger.info("Detected Queue-it, waiting in virtual queue...")
                
                # Wait for queue to pass
                max_wait = 300  # 5 minutes
                start_time = datetime.now()
                
                while (datetime.now() - start_time).seconds < max_wait:
                    # Check if still in queue
                    if "queue-it.net" not in page.url:
                        logger.info("Passed Queue-it")
                        break
                    
                    # Look for queue position
                    position_element = await page.query_selector(
                        ".queue-position, .your-number-is, [class*='position']"
                    )
                    
                    if position_element:
                        position = await position_element.text_content()
                        logger.info(f"Queue position: {position}")
                    
                    await page.wait_for_timeout(5000)
                    
        except Exception as e:
            logger.error(f"Queue-it handling error: {e}")
    
    async def _check_login_success(self, page: Page) -> bool:
        """Check if login was successful."""
        try:
            # Look for account menu or user name
            user_indicators = [
                ".user-account",
                ".my-account",
                "[data-testid='user-menu']",
                ".signed-in-as"
            ]
            
            for selector in user_indicators:
                if await self.wait_for_element(page, selector, timeout=5000):
                    return True
            
            # Check URL
            if "/member/" not in page.url and "/login" not in page.url:
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _extract_ticketmaster_tickets(self, page: Page) -> List[Dict[str, Any]]:
        """Extract Ticketmaster-specific ticket information."""
        try:
            # Check if seat map or list view
            if await self._is_seat_map_view(page):
                return await self._extract_from_seat_map(page)
            else:
                return await self._extract_from_list_view(page)
                
        except Exception as e:
            logger.error(f"Ticketmaster ticket extraction error: {e}")
            return []
    
    async def _is_seat_map_view(self, page: Page) -> bool:
        """Check if in seat map view."""
        return bool(await page.query_selector(".seat-map, .venue-map, svg.seating-chart"))
    
    async def _extract_from_seat_map(self, page: Page) -> List[Dict[str, Any]]:
        """Extract tickets from interactive seat map."""
        tickets = []
        
        try:
            # Get all available seats
            seats = await page.query_selector_all(
                ".available-seat, .seat:not(.unavailable), [data-status='available']"
            )
            
            for seat in seats:
                try:
                    # Hover to get details
                    await seat.hover()
                    await page.wait_for_timeout(500)
                    
                    # Look for tooltip/popup
                    tooltip = await page.query_selector(
                        ".seat-tooltip, .seat-details, .popover"
                    )
                    
                    if tooltip:
                        info = await tooltip.evaluate("""
                            (element) => {
                                const getText = (selector) => {
                                    const el = element.querySelector(selector);
                                    return el ? el.textContent.trim() : '';
                                };
                                
                                return {
                                    section: getText('.section, [class*="section"]'),
                                    row: getText('.row, [class*="row"]'),
                                    seat: getText('.seat-number, [class*="seat"]'),
                                    price: getText('.price, [class*="price"]')
                                };
                            }
                        """)
                        
                        price = self._parse_price(info["price"])
                        
                        tickets.append({
                            "section": info["section"],
                            "row": info["row"],
                            "seat": info["seat"],
                            "price": price,
                            "price_text": info["price"],
                            "element": seat,
                            "platform": "Ticketmaster"
                        })
                        
                except Exception as e:
                    logger.debug(f"Error extracting seat info: {e}")
            
            return tickets
            
        except Exception as e:
            logger.error(f"Seat map extraction error: {e}")
            return []
    
    async def _extract_from_list_view(self, page: Page) -> List[Dict[str, Any]]:
        """Extract tickets from list view."""
        try:
            tickets = await page.query_selector_all(
                ".ticket-listing, .ticket-option, [data-testid='ticket-listing']"
            )
            
            ticket_info = []
            
            for ticket in tickets:
                try:
                    info = await ticket.evaluate("""
                        (element) => {
                            const getText = (selector) => {
                                const el = element.querySelector(selector);
                                return el ? el.textContent.trim() : '';
                            };
                            
                            return {
                                section: getText('.section-info, .section'),
                                row: getText('.row-info, .row'),
                                seats: getText('.seats-info, .quantity'),
                                price: getText('.price-display, .ticket-price'),
                                available: !element.classList.contains('sold-out') &&
                                          !element.disabled
                            };
                        }
                    """)
                    
                    if info["available"]:
                        price = self._parse_price(info["price"])
                        
                        ticket_info.append({
                            "section": info["section"],
                            "row": info["row"],
                            "seats": info["seats"],
                            "price": price,
                            "price_text": info["price"],
                            "element": ticket,
                            "platform": "Ticketmaster"
                        })
                        
                except Exception as e:
                    logger.debug(f"Error extracting ticket info: {e}")
            
            return ticket_info
            
        except Exception as e:
            logger.error(f"List view extraction error: {e}")
            return []
    
    async def _select_from_seat_map(
        self,
        page: Page,
        tickets: List[Dict[str, Any]],
        quantity: int
    ) -> int:
        """Select tickets from seat map."""
        selected = 0
        
        try:
            for ticket in tickets[:quantity]:
                element = ticket.get("element")
                if element:
                    await element.click()
                    await page.wait_for_timeout(500)
                    
                    # Check if selected
                    is_selected = await element.evaluate(
                        "el => el.classList.contains('selected') || el.getAttribute('data-status') === 'selected'"
                    )
                    
                    if is_selected:
                        selected += 1
                        
                        if selected >= quantity:
                            break
            
            return selected
            
        except Exception as e:
            logger.error(f"Seat map selection error: {e}")
            return selected
    
    async def _select_from_list_view(
        self,
        page: Page,
        tickets: List[Dict[str, Any]],
        quantity: int
    ) -> int:
        """Select tickets from list view."""
        selected = 0
        
        try:
            for ticket in tickets[:quantity]:
                element = ticket.get("element")
                if element:
                    # Look for quantity selector
                    qty_selector = await element.query_selector(
                        'select[name*="quantity"], input[type="number"]'
                    )
                    
                    if qty_selector:
                        # Set quantity
                        await qty_selector.fill(str(quantity - selected))
                    
                    # Click select/add button
                    select_button = await element.query_selector(
                        'button[class*="select"], button[class*="add"]'
                    )
                    
                    if select_button:
                        await select_button.click()
                        selected += quantity
                        break
                    else:
                        # Click the whole element
                        await element.click()
                        selected += 1
                    
                    await page.wait_for_timeout(1000)
                    
                    if selected >= quantity:
                        break
            
            return selected
            
        except Exception as e:
            logger.error(f"List view selection error: {e}")
            return selected
    
    async def _select_delivery_method(self, page: Page) -> None:
        """Select ticket delivery method."""
        try:
            # Usually e-ticket is preferred
            eticket_selector = (
                'input[value*="eticket"], '
                'input[value*="mobile"], '
                'label[for*="electronic"]'
            )
            
            await self.safe_click(page, eticket_selector)
            
            # Continue button
            continue_button = await self.wait_for_element(
                page,
                'button[class*="continue"], button[type="submit"]'
            )
            
            if continue_button:
                await continue_button.click()
                await page.wait_for_timeout(2000)
                
        except Exception as e:
            logger.error(f"Delivery method selection error: {e}")
    
    async def _fill_payment_info(self, page: Page, profile: UserProfile) -> None:
        """Fill payment information."""
        try:
            # This is simplified - real implementation would need proper payment handling
            
            # Select payment type
            if profile.payment_method == "credit_card":
                card_selector = 'input[value="credit_card"], label[for*="card"]'
                await self.safe_click(page, card_selector)
            
            # Note: Actual card details would need secure handling
            logger.warning("Payment info handling not fully implemented")
            
        except Exception as e:
            logger.error(f"Payment info error: {e}")
    
    async def _fill_billing_info(self, page: Page, profile: UserProfile) -> None:
        """Fill billing information."""
        try:
            # Similar to Fansale implementation
            await super()._fill_billing_info(page, profile)
            
        except Exception as e:
            logger.error(f"Billing info error: {e}")
    
    async def _wait_for_confirmation(self, page: Page) -> Optional[str]:
        """Wait for order confirmation."""
        try:
            # Wait for confirmation page
            await self.wait_for_element(
                page,
                '.confirmation, .order-complete, [data-testid="confirmation"]',
                timeout=15000
            )
            
            # Look for order number
            order_selectors = [
                ".order-number",
                ".confirmation-number",
                "[data-testid='order-id']",
                ".reference-number"
            ]
            
            for selector in order_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    
                    # Extract alphanumeric order ID
                    import re
                    match = re.search(r'[A-Z0-9]{6,}', text)
                    if match:
                        return match.group()
            
            return None
            
        except Exception:
            return None
