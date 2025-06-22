# stealthmaster/platforms/vivaticket.py
"""Vivaticket.com platform handler."""

import logging
from typing import Dict, Any, List, Optional

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


class VivaticketPlatform(BasePlatformHandler):
    """Handler for Vivaticket.com ticket platform."""
    
    def __init__(self):
        """Initialize Vivaticket handler."""
        super().__init__()
        self.base_url = "https://www.vivaticket.com"
        self.login_url = f"{self.base_url}/it/login"
    
    async def initialize(self, page: Page) -> bool:
        """Initialize Vivaticket-specific setup."""
        try:
            # Navigate to homepage
            await page.goto(self.base_url, wait_until="domcontentloaded")
            
            # Handle cookies
            await self.handle_cookies(page)
            
            # Handle language selection if needed
            await self._ensure_italian_language(page)
            
            # Wait for page to stabilize
            await page.wait_for_timeout(2000)
            
            self._initialized = True
            logger.info("Vivaticket handler initialized")
            return True
            
        except Exception as e:
            logger.error(f"Vivaticket initialization error: {e}")
            return False
    
    async def login(self, page: Page, profile: UserProfile) -> bool:
        """Perform Vivaticket login."""
        try:
            # Vivaticket often doesn't require login for purchase
            # But if needed, navigate to login
            
            # Check if already logged in
            if await self._check_login_status(page):
                logger.info("Already logged into Vivaticket")
                return True
            
            # Navigate to login page
            await page.goto(self.login_url, wait_until="networkidle")
            
            # Email field
            email_selector = 'input[name="username"], input[name="email"], #email'
            if not await self.safe_type(page, email_selector, profile.email):
                logger.error("Failed to enter email")
                return False
            
            # Password field  
            password_selector = 'input[name="password"], #password'
            if not await self.safe_type(page, password_selector, "dummy_password"):
                logger.error("Failed to enter password")
                return False
            
            # Submit button
            submit_selector = 'button[type="submit"], .login-button, #loginButton'
            if not await self.safe_click(page, submit_selector):
                logger.error("Failed to click login button")
                return False
            
            # Wait for login to complete
            await page.wait_for_navigation(timeout=10000)
            
            # Verify login success
            if await self._check_login_status(page):
                logger.info("Successfully logged into Vivaticket")
                return True
            else:
                logger.error("Vivaticket login failed")
                return False
                
        except Exception as e:
            logger.error(f"Vivaticket login error: {e}")
            return False
    
    async def search_tickets(
        self,
        page: Page,
        event: TargetEvent
    ) -> List[Dict[str, Any]]:
        """Search for tickets on Vivaticket."""
        try:
            # Navigate to event URL
            await page.goto(str(event.event_url), wait_until="networkidle")
            
            # Click on "Acquista" (Buy) button
            buy_button_selector = (
                'a[class*="buy"], '
                'button[class*="acquista"], '
                '.event-buy-button, '
                '[data-testid="buy-tickets"]'
            )
            
            await self.safe_click(page, buy_button_selector)
            await page.wait_for_timeout(3000)
            
            # Wait for ticket selection page
            await self.wait_for_element(
                page,
                '.ticket-types, .price-categories, [class*="tipologia"]',
                timeout=10000
            )
            
            # Extract available tickets
            tickets = await self._extract_vivaticket_tickets(page)
            
            # Filter by preferences
            filtered = self.filter_tickets_by_preferences(tickets, event)
            
            logger.info(f"Found {len(filtered)} suitable tickets on Vivaticket")
            return filtered
            
        except Exception as e:
            logger.error(f"Vivaticket ticket search error: {e}")
            return []
    
    async def select_tickets(
        self,
        page: Page,
        tickets: List[Dict[str, Any]],
        quantity: int
    ) -> bool:
        """Select tickets on Vivaticket."""
        try:
            selected = 0
            
            # Vivaticket typically uses quantity selectors
            for ticket in tickets:
                if selected >= quantity:
                    break
                
                element = ticket.get("element")
                if not element:
                    continue
                
                # Find quantity input/selector
                qty_input = await element.query_selector(
                    'input[type="number"], '
                    'select[name*="quantity"], '
                    '.quantity-selector'
                )
                
                if qty_input:
                    # Set quantity
                    remaining = quantity - selected
                    await qty_input.fill(str(remaining))
                    selected += remaining
                else:
                    # Look for + button to increase quantity
                    plus_button = await element.query_selector(
                        'button[class*="plus"], '
                        'button[class*="increment"], '
                        '.quantity-plus'
                    )
                    
                    if plus_button:
                        for _ in range(quantity - selected):
                            await plus_button.click()
                            await page.wait_for_timeout(200)
                            selected += 1
                            
                            if selected >= quantity:
                                break
            
            if selected > 0:
                # Click continue/proceed button
                proceed_button = await self.wait_for_element(
                    page,
                    'button[class*="proceed"], '
                    'button[class*="continua"], '
                    'button[class*="avanti"], '
                    '[data-testid="proceed-button"]'
                )
                
                if proceed_button:
                    await proceed_button.click()
                    logger.info(f"Selected {selected} tickets on Vivaticket")
                    return True
            
            logger.error("Failed to select tickets on Vivaticket")
            return False
            
        except Exception as e:
            logger.error(f"Vivaticket ticket selection error: {e}")
            return False
    
    async def complete_purchase(
        self,
        page: Page,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Complete purchase on Vivaticket."""
        try:
            # Wait for checkout page
            await self.wait_for_element(
                page,
                '.checkout, .riepilogo-ordine, [class*="summary"]',
                timeout=10000
            )
            
            # Fill customer information if not logged in
            if not await self._check_login_status(page):
                await self._fill_customer_info(page, profile)
            
            # Accept terms and conditions
            terms_checkbox = await page.query_selector(
                'input[name*="terms"], '
                'input[name*="condizioni"], '
                '#acceptTerms'
            )
            
            if terms_checkbox:
                is_checked = await terms_checkbox.is_checked()
                if not is_checked:
                    await terms_checkbox.click()
            
            # Select payment method
            await self._select_vivaticket_payment(page, profile)
            
            # Click final purchase button
            purchase_button = await self.wait_for_element(
                page,
                'button[class*="purchase"], '
                'button[class*="acquista"], '
                'button[class*="paga"], '
                '[data-testid="complete-order"]'
            )
            
            if purchase_button:
                await purchase_button.click()
                
                # Handle payment processing
                # This would redirect to payment provider
                await page.wait_for_timeout(5000)
                
                # Wait for confirmation
                confirmation = await self._wait_for_vivaticket_confirmation(page)
                
                if confirmation:
                    return {
                        "success": True,
                        "confirmation_number": confirmation,
                        "platform": "Vivaticket"
                    }
            
            return {"success": False, "error": "Could not complete purchase"}
            
        except Exception as e:
            logger.error(f"Vivaticket purchase error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _ensure_italian_language(self, page: Page) -> None:
        """Ensure the site is in Italian."""
        try:
            # Check current language
            if "/it/" in page.url or "lang=it" in page.url:
                return
            
            # Look for language selector
            lang_selector = await page.query_selector(
                '.language-selector, '
                '[class*="lingua"], '
                'a[href*="/it/"]'
            )
            
            if lang_selector:
                await lang_selector.click()
                await page.wait_for_timeout(2000)
                
        except Exception as e:
            logger.debug(f"Language selection error: {e}")
    
    async def _check_login_status(self, page: Page) -> bool:
        """Check if user is logged in."""
        try:
            # Look for user menu or logout link
            user_indicators = [
                ".user-menu",
                ".user-logged",
                "a[href*='logout']",
                ".il-mio-account"
            ]
            
            for selector in user_indicators:
                if await page.query_selector(selector):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _extract_vivaticket_tickets(self, page: Page) -> List[Dict[str, Any]]:
        """Extract Vivaticket-specific ticket information."""
        try:
            # Get ticket categories/types
            ticket_types = await page.query_selector_all(
                '.ticket-type, '
                '.price-category, '
                '.tipologia-biglietto, '
                '[class*="categoria"]'
            )
            
            ticket_info = []
            
            for ticket_type in ticket_types:
                try:
                    info = await ticket_type.evaluate("""
                        (element) => {
                            const getText = (selector) => {
                                const el = element.querySelector(selector);
                                return el ? el.textContent.trim() : '';
                            };
                            
                            // Get all text content for parsing
                            const fullText = element.textContent;
                            
                            return {
                                name: getText('.category-name, .nome-tipologia, h3, h4'),
                                description: getText('.category-description, .descrizione'),
                                price: getText('.price, .prezzo, [class*="price"]'),
                                available: !element.classList.contains('sold-out') &&
                                          !element.classList.contains('esaurito') &&
                                          !fullText.includes('Esaurito') &&
                                          !fullText.includes('Non disponibile')
                            };
                        }
                    """)
                    
                    if info["available"]:
                        price = self._parse_price(info["price"])
                        
                        # Parse section/category from name
                        name_parts = info["name"].split("-")
                        section = name_parts[0].strip() if name_parts else info["name"]
                        
                        ticket_info.append({
                            "section": section,
                            "category": info["name"],
                            "description": info["description"],
                            "price": price,
                            "price_text": info["price"],
                            "element": ticket_type,
                            "platform": "Vivaticket"
                        })
                        
                except Exception as e:
                    logger.debug(f"Error extracting ticket type: {e}")
            
            return ticket_info
            
        except Exception as e:
            logger.error(f"Vivaticket ticket extraction error: {e}")
            return []
    
    async def _fill_customer_info(self, page: Page, profile: UserProfile) -> None:
        """Fill customer information for guest checkout."""
        try:
            # First name
            await self.safe_type(
                page,
                'input[name*="nome"], input[name*="firstName"], #nome',
                profile.first_name
            )
            
            # Last name
            await self.safe_type(
                page,
                'input[name*="cognome"], input[name*="lastName"], #cognome',
                profile.last_name
            )
            
            # Email
            await self.safe_type(
                page,
                'input[name*="email"], #email',
                profile.email
            )
            
            # Confirm email (if required)
            await self.safe_type(
                page,
                'input[name*="conferma_email"], #conferma_email',
                profile.email,
                clear_first=False
            )
            
            # Phone
            await self.safe_type(
                page,
                'input[name*="telefono"], input[name*="phone"], #telefono',
                profile.phone
            )
            
            # Tax code (codice fiscale) - Italian specific
            # Would need to be in profile
            tax_code_input = await page.query_selector(
                'input[name*="codice_fiscale"], #codice_fiscale'
            )
            
            if tax_code_input:
                # Generate or use stored tax code
                logger.warning("Tax code (codice fiscale) required but not implemented")
                
        except Exception as e:
            logger.error(f"Customer info error: {e}")
    
    async def _select_vivaticket_payment(self, page: Page, profile: UserProfile) -> None:
        """Select payment method on Vivaticket."""
        try:
            # Payment method radio buttons
            if profile.payment_method == "credit_card":
                card_selector = (
                    'input[value*="card"], '
                    'input[value*="carta"], '
                    'label[for*="credit"]'
                )
                await self.safe_click(page, card_selector)
                
            elif profile.payment_method == "paypal":
                paypal_selector = (
                    'input[value*="paypal"], '
                    'label[for*="paypal"]'
                )
                await self.safe_click(page, paypal_selector)
                
            # Note: Actual payment would be handled by payment provider
            
        except Exception as e:
            logger.error(f"Payment selection error: {e}")
    
    async def _wait_for_vivaticket_confirmation(self, page: Page) -> Optional[str]:
        """Wait for Vivaticket order confirmation."""
        try:
            # Wait for confirmation page or success message
            confirmation_selectors = [
                ".conferma-ordine",
                ".order-confirmation",
                ".numero-ordine",
                "[class*='success']",
                "[class*='conferma']"
            ]
            
            for selector in confirmation_selectors:
                element = await self.wait_for_element(
                    page,
                    selector,
                    timeout=15000
                )
                
                if element:
                    # Extract order number
                    page_text = await page.content()
                    
                    # Look for patterns like "Ordine: ABC123" or "N. ABC123"
                    import re
                    patterns = [
                        r'(?:Ordine|Order|Numero)[\s:]+([A-Z0-9]{4,})',
                        r'(?:N\.|#)\s*([A-Z0-9]{4,})',
                        r'([A-Z0-9]{6,})'  # Fallback to any long alphanumeric
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, page_text)
                        if match:
                            return match.group(1)
            
            return None
            
        except Exception:
            return None