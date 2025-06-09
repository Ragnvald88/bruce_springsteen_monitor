# stealthmaster/platforms/fansale.py
"""Fansale.it platform handler."""

import logging
from typing import Dict, Any, List, Optional

from playwright.async_api import Page

from stealthmaster.config import TargetEvent, UserProfile
from ..platforms.base import BasePlatformHandler

logger = logging.getLogger(__name__)


class FansaleHandler(BasePlatformHandler):
    """Handler for Fansale.it ticket platform."""
    
    def __init__(self):
        """Initialize Fansale handler."""
        super().__init__()
        self.base_url = "https://www.fansale.it"
        self.login_url = f"{self.base_url}/fansale/login"
    
    async def initialize(self, page: Page) -> bool:
        """Initialize Fansale-specific setup."""
        try:
            # Navigate to homepage
            await page.goto(self.base_url, wait_until="domcontentloaded")
            
            # Handle cookies
            await self.handle_cookies(page)
            
            # Wait for page to stabilize
            await page.wait_for_timeout(2000)
            
            self._initialized = True
            logger.info("Fansale handler initialized")
            return True
            
        except Exception as e:
            logger.error(f"Fansale initialization error: {e}")
            return False
    
    async def login(self, page: Page, profile: UserProfile) -> bool:
        """Perform Fansale login."""
        try:
            # Navigate to login
            await page.goto(self.login_url, wait_until="networkidle")
            
            # Email field
            email_selector = 'input[name="email"], input[type="email"], #email'
            if not await self.safe_type(page, email_selector, profile.email):
                logger.error("Failed to enter email")
                return False
            
            # Password field
            password_selector = 'input[name="password"], input[type="password"], #password'
            if not await self.safe_type(page, password_selector, "dummy_password"):  # Use actual password
                logger.error("Failed to enter password")
                return False
            
            # Submit button
            submit_selector = 'button[type="submit"], input[type="submit"], .login-button'
            if not await self.safe_click(page, submit_selector):
                logger.error("Failed to click login button")
                return False
            
            # Wait for login to complete
            await page.wait_for_navigation(timeout=10000)
            
            # Check if logged in
            if await self._check_login_success(page):
                logger.info("Successfully logged into Fansale")
                return True
            else:
                logger.error("Fansale login failed")
                return False
                
        except Exception as e:
            logger.error(f"Fansale login error: {e}")
            return False
    
    async def search_tickets(
        self,
        page: Page,
        event: TargetEvent
    ) -> List[Dict[str, Any]]:
        """Search for tickets on Fansale."""
        try:
            # Navigate to event URL
            await page.goto(str(event.event_url), wait_until="networkidle")
            
            # Wait for ticket listings
            ticket_selector = ".ticket-item, .listing-item, [data-testid='ticket-listing']"
            await self.wait_for_element(page, ticket_selector)
            
            # Extract ticket information
            tickets = await self._extract_fansale_tickets(page)
            
            # Filter by preferences
            filtered = self.filter_tickets_by_preferences(tickets, event)
            
            logger.info(f"Found {len(filtered)} suitable tickets on Fansale")
            return filtered
            
        except Exception as e:
            logger.error(f"Fansale ticket search error: {e}")
            return []
    
    async def select_tickets(
        self,
        page: Page,
        tickets: List[Dict[str, Any]],
        quantity: int
    ) -> bool:
        """Select tickets on Fansale."""
        try:
            selected = 0
            
            for ticket in tickets[:quantity]:
                # Click on ticket
                element = ticket.get("element")
                if element:
                    await element.click()
                    await page.wait_for_timeout(1000)
                    
                    # Look for add to cart button
                    add_button = await self.wait_for_element(
                        page,
                        ".add-to-cart, button[class*='cart'], [data-testid='add-ticket']"
                    )
                    
                    if add_button:
                        await add_button.click()
                        selected += 1
                        
                        if selected >= quantity:
                            break
            
            if selected > 0:
                logger.info(f"Selected {selected} tickets on Fansale")
                return True
            else:
                logger.error("Failed to select any tickets on Fansale")
                return False
                
        except Exception as e:
            logger.error(f"Fansale ticket selection error: {e}")
            return False
    
    async def complete_purchase(
        self,
        page: Page,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Complete purchase on Fansale."""
        try:
            # Navigate to checkout
            checkout_button = await self.wait_for_element(
                page,
                ".checkout-button, button[class*='checkout'], [href*='checkout']"
            )
            
            if not checkout_button:
                return {"success": False, "error": "Checkout button not found"}
            
            await checkout_button.click()
            await page.wait_for_navigation()
            
            # Fill billing information
            await self._fill_billing_info(page, profile)
            
            # Select payment method
            await self._select_payment_method(page, profile)
            
            # Confirm purchase
            confirm_button = await self.wait_for_element(
                page,
                ".confirm-purchase, button[class*='confirm'], [data-testid='confirm-order']"
            )
            
            if confirm_button:
                await confirm_button.click()
                
                # Wait for confirmation
                confirmation = await self._wait_for_confirmation(page)
                
                if confirmation:
                    return {
                        "success": True,
                        "confirmation_number": confirmation,
                        "platform": "Fansale"
                    }
            
            return {"success": False, "error": "Purchase could not be completed"}
            
        except Exception as e:
            logger.error(f"Fansale purchase error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_login_success(self, page: Page) -> bool:
        """Check if login was successful."""
        try:
            # Look for user menu or logout button
            user_indicators = [
                ".user-menu",
                ".logout-button",
                "[data-testid='user-account']",
                ".my-account"
            ]
            
            for selector in user_indicators:
                if await self.wait_for_element(page, selector, timeout=3000):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _extract_fansale_tickets(self, page: Page) -> List[Dict[str, Any]]:
        """Extract Fansale-specific ticket information."""
        try:
            tickets = await page.query_selector_all(".ticket-item, .listing-item")
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
                                section: getText('.sector, .section-name'),
                                row: getText('.row, .row-number'),
                                seat: getText('.seat, .seat-number'),
                                price: getText('.price, .ticket-price'),
                                seller: getText('.seller-name, .vendor'),
                                available: !element.classList.contains('sold-out')
                            };
                        }
                    """)
                    
                    if info["available"]:
                        price = self._parse_price(info["price"])
                        
                        ticket_info.append({
                            "section": info["section"],
                            "row": info["row"],
                            "seat": info["seat"],
                            "price": price,
                            "price_text": info["price"],
                            "seller": info["seller"],
                            "element": ticket,
                            "platform": "Fansale"
                        })
                        
                except Exception as e:
                    logger.debug(f"Error extracting Fansale ticket: {e}")
            
            return ticket_info
            
        except Exception as e:
            logger.error(f"Fansale ticket extraction error: {e}")
            return []
    
    async def _fill_billing_info(self, page: Page, profile: UserProfile) -> None:
        """Fill billing information on checkout."""
        try:
            # First name
            await self.safe_type(
                page,
                'input[name="firstName"], #firstName',
                profile.first_name
            )
            
            # Last name
            await self.safe_type(
                page,
                'input[name="lastName"], #lastName',
                profile.last_name
            )
            
            # Email (might be pre-filled)
            await self.safe_type(
                page,
                'input[name="email"], #email',
                profile.email,
                clear_first=False
            )
            
            # Phone
            await self.safe_type(
                page,
                'input[name="phone"], #phone',
                profile.phone
            )
            
            # Address fields
            if profile.billing_address:
                await self.safe_type(
                    page,
                    'input[name="address"], #address',
                    profile.billing_address.get("street", "")
                )
                
                await self.safe_type(
                    page,
                    'input[name="city"], #city',
                    profile.billing_address.get("city", "")
                )
                
                await self.safe_type(
                    page,
                    'input[name="zipCode"], #zipCode',
                    profile.billing_address.get("zip", "")
                )
                
        except Exception as e:
            logger.error(f"Error filling billing info: {e}")
    
    async def _select_payment_method(self, page: Page, profile: UserProfile) -> None:
        """Select payment method."""
        try:
            # Click on payment method
            payment_selector = f'input[value="{profile.payment_method}"], ' \
                             f'label[for="{profile.payment_method}"]'
            
            await self.safe_click(page, payment_selector)
            
            # If credit card, might need to fill details
            if profile.payment_method == "credit_card" and profile.card_details:
                # This would need proper payment integration
                logger.warning("Credit card form handling not implemented")
                
        except Exception as e:
            logger.error(f"Error selecting payment method: {e}")
    
    async def _wait_for_confirmation(self, page: Page) -> Optional[str]:
        """Wait for purchase confirmation."""
        try:
            # Wait for confirmation page
            confirmation_selectors = [
                ".confirmation-number",
                ".order-number",
                "[data-testid='confirmation-id']",
                ".success-message"
            ]
            
            for selector in confirmation_selectors:
                element = await self.wait_for_element(page, selector, timeout=10000)
                if element:
                    text = await element.text_content()
                    
                    # Extract confirmation number
                    import re
                    match = re.search(r'[A-Z0-9]{6,}', text)
                    if match:
                        return match.group()
            
            return None
            
        except Exception:
            return None