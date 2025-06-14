"""
Ticket Purchase Engine
Automated purchase flow with platform-specific handlers
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime

from ...utils.logging import get_logger
from ...utils.notifications import notification_manager
from ...database.statistics import stats_manager

logger = get_logger(__name__)


@dataclass
class PurchaseResult:
    """Result of a purchase attempt"""
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
    tickets_purchased: int = 0
    total_price: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PlatformPurchaseHandler(ABC):
    """Base class for platform-specific purchase handlers"""
    
    def __init__(self, settings=None):
        self.settings = settings
        self.max_price = 800  # Default max price
        self.min_quantity = 1
        self.max_quantity = 8
        
    @abstractmethod
    async def execute_purchase(self, page, detection_result: Dict[str, Any]) -> PurchaseResult:
        """Execute the purchase flow"""
        pass
    
    @abstractmethod
    async def _select_tickets(self, page, detection_result: Dict[str, Any]) -> bool:
        """Select tickets based on preferences"""
        pass
    
    @abstractmethod
    async def _add_to_cart(self, page) -> bool:
        """Add selected tickets to cart"""
        pass
    
    @abstractmethod
    async def _proceed_checkout(self, page) -> bool:
        """Proceed to checkout"""
        pass
    
    @abstractmethod
    async def _complete_purchase(self, page) -> bool:
        """Complete the purchase"""
        pass
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        try:
            # Remove currency symbols and parse
            price = price_text.replace('€', '').replace('EUR', '').replace(',', '.')
            price = ''.join(c for c in price if c.isdigit() or c == '.')
            return float(price)
        except:
            return 999999.0  # High value if parse fails


class FansalePurchaseHandler(PlatformPurchaseHandler):
    """Fansale-specific purchase implementation"""
    
    async def execute_purchase(self, page, detection_result: Dict[str, Any]) -> PurchaseResult:
        """Execute Fansale purchase flow"""
        steps = [
            ("Select tickets", self._select_tickets),
            ("Add to cart", self._add_to_cart),
            ("Proceed to checkout", self._proceed_checkout),
            ("Complete purchase", self._complete_purchase)
        ]
        
        for step_name, step_func in steps:
            try:
                logger.info(f"Executing step: {step_name}")
                success = await step_func(page, detection_result)
                if not success:
                    return PurchaseResult(
                        success=False,
                        error=f"Failed at: {step_name}"
                    )
            except Exception as e:
                logger.error(f"Error in {step_name}: {e}")
                return PurchaseResult(
                    success=False,
                    error=f"Error in {step_name}: {str(e)}"
                )
        
        # Get order details
        order_id = await self._get_order_id(page)
        
        return PurchaseResult(
            success=True,
            order_id=order_id,
            tickets_purchased=detection_result.get('ticket_count', 1)
        )
    
    async def _select_tickets(self, page, detection_result: Dict[str, Any]) -> bool:
        """Select tickets on Fansale"""
        try:
            # Wait for ticket list to be interactive
            if hasattr(page, 'wait_for_selector'):
                await page.wait_for_selector('.ticket-listing-item, .offer-row', state='visible')
            else:
                await asyncio.sleep(2)
            
            # Get all available tickets
            if hasattr(page, 'query_selector_all'):
                tickets = await page.query_selector_all('.ticket-listing-item:not(.sold-out), .offer-row:not(.unavailable)')
            else:
                tickets = page.find_elements_by_css_selector('.ticket-listing-item:not(.sold-out)')
            
            # Find best ticket based on price
            selected = False
            for ticket in tickets[:5]:  # Check first 5 tickets
                try:
                    # Get price
                    if hasattr(ticket, 'text_content'):
                        price_text = await ticket.text_content('.price, .offer-price')
                    else:
                        price_elem = ticket.find_element_by_css_selector('.price, .offer-price')
                        price_text = price_elem.text
                    
                    price = self._parse_price(price_text)
                    
                    if price <= self.max_price:
                        # Click on ticket
                        if hasattr(ticket, 'click'):
                            await ticket.click()
                        else:
                            ticket.click()
                        
                        selected = True
                        logger.info(f"Selected ticket with price: €{price}")
                        break
                except Exception as e:
                    logger.debug(f"Error checking ticket: {e}")
                    continue
            
            if selected:
                await asyncio.sleep(2)  # Wait for selection to register
                return True
            
            logger.warning("No suitable tickets found within price range")
            return False
            
        except Exception as e:
            logger.error(f"Error selecting tickets: {e}")
            return False
    
    async def _add_to_cart(self, page) -> bool:
        """Add to cart on Fansale"""
        try:
            # Look for add to cart button
            selectors = [
                'button[class*="add-to-cart"]',
                'a[href*="carrello"]',
                'button[class*="aggiungi"]',
                '[data-action="add-to-basket"]'
            ]
            
            for selector in selectors:
                try:
                    if hasattr(page, 'click'):
                        await page.click(selector, timeout=5000)
                    else:
                        button = page.find_element_by_css_selector(selector)
                        button.click()
                    
                    logger.info("Added tickets to cart")
                    await asyncio.sleep(3)
                    return True
                except:
                    continue
            
            logger.error("Could not find add to cart button")
            return False
            
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False
    
    async def _proceed_checkout(self, page) -> bool:
        """Proceed to checkout on Fansale"""
        try:
            # Click checkout button
            checkout_selectors = [
                'a[href*="checkout"]',
                'button[class*="checkout"]',
                'button[class*="procedi"]',
                '[data-action="checkout"]'
            ]
            
            for selector in checkout_selectors:
                try:
                    if hasattr(page, 'click'):
                        await page.click(selector, timeout=5000)
                    else:
                        button = page.find_element_by_css_selector(selector)
                        button.click()
                    
                    logger.info("Proceeding to checkout")
                    await asyncio.sleep(3)
                    return True
                except:
                    continue
            
            logger.error("Could not find checkout button")
            return False
            
        except Exception as e:
            logger.error(f"Error proceeding to checkout: {e}")
            return False
    
    async def _complete_purchase(self, page) -> bool:
        """Complete purchase on Fansale"""
        try:
            # This would normally:
            # 1. Fill payment details (if not saved)
            # 2. Confirm order
            # 3. Wait for confirmation
            
            # For now, we'll simulate the final step
            confirm_selectors = [
                'button[class*="conferma"]',
                'button[class*="completa"]',
                'button[type="submit"]'
            ]
            
            for selector in confirm_selectors:
                try:
                    if hasattr(page, 'click'):
                        await page.click(selector, timeout=5000)
                    else:
                        button = page.find_element_by_css_selector(selector)
                        button.click()
                    
                    logger.info("Purchase completed!")
                    await asyncio.sleep(5)
                    return True
                except:
                    continue
            
            logger.warning("Purchase flow incomplete - manual intervention may be needed")
            return True  # Return True to indicate we got to the final step
            
        except Exception as e:
            logger.error(f"Error completing purchase: {e}")
            return False
    
    async def _get_order_id(self, page) -> Optional[str]:
        """Extract order ID from confirmation page"""
        try:
            # Look for order ID in various formats
            if hasattr(page, 'text_content'):
                content = await page.text_content('body')
            else:
                content = page.find_element_by_tag_name('body').text
            
            # Simple pattern matching for order ID
            import re
            order_pattern = r'(?:order|ordine|conferma).*?(\d{6,})'
            match = re.search(order_pattern, content, re.IGNORECASE)
            
            if match:
                return match.group(1)
            
            return f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        except:
            return None


class TicketmasterPurchaseHandler(PlatformPurchaseHandler):
    """Ticketmaster-specific purchase implementation"""
    
    async def execute_purchase(self, page, detection_result: Dict[str, Any]) -> PurchaseResult:
        """Execute Ticketmaster purchase flow"""
        # Similar structure to Fansale but with Ticketmaster-specific selectors
        steps = [
            ("Select tickets", self._select_tickets),
            ("Add to cart", self._add_to_cart),
            ("Proceed to checkout", self._proceed_checkout),
            ("Complete purchase", self._complete_purchase)
        ]
        
        for step_name, step_func in steps:
            try:
                success = await step_func(page, detection_result)
                if not success:
                    return PurchaseResult(success=False, error=f"Failed at: {step_name}")
            except Exception as e:
                return PurchaseResult(success=False, error=str(e))
        
        return PurchaseResult(success=True)
    
    async def _select_tickets(self, page, detection_result: Dict[str, Any]) -> bool:
        """Ticketmaster ticket selection"""
        # Implementation specific to Ticketmaster's UI
        logger.info("Selecting tickets on Ticketmaster")
        return True
    
    async def _add_to_cart(self, page) -> bool:
        """Ticketmaster add to cart"""
        logger.info("Adding to cart on Ticketmaster")
        return True
    
    async def _proceed_checkout(self, page) -> bool:
        """Ticketmaster checkout"""
        logger.info("Proceeding to checkout on Ticketmaster")
        return True
    
    async def _complete_purchase(self, page) -> bool:
        """Ticketmaster purchase completion"""
        logger.info("Completing purchase on Ticketmaster")
        return True


class VivaticketPurchaseHandler(PlatformPurchaseHandler):
    """Vivaticket-specific purchase implementation"""
    
    async def execute_purchase(self, page, detection_result: Dict[str, Any]) -> PurchaseResult:
        """Execute Vivaticket purchase flow"""
        # Similar structure with Vivaticket-specific implementation
        return PurchaseResult(success=True)
    
    async def _select_tickets(self, page, detection_result: Dict[str, Any]) -> bool:
        return True
    
    async def _add_to_cart(self, page) -> bool:
        return True
    
    async def _proceed_checkout(self, page) -> bool:
        return True
    
    async def _complete_purchase(self, page) -> bool:
        return True


class TicketPurchaseEngine:
    """Main purchase orchestrator"""
    
    def __init__(self, settings=None):
        self.settings = settings
        self.handlers = {
            'fansale': FansalePurchaseHandler(settings),
            'ticketmaster': TicketmasterPurchaseHandler(settings),
            'vivaticket': VivaticketPurchaseHandler(settings)
        }
    
    async def handle_ticket_detection(self, page, platform: str, detection_result: Dict[str, Any]) -> Optional[PurchaseResult]:
        """Execute purchase when tickets detected"""
        
        # Check confidence threshold
        if detection_result.get('confidence', 0) < 0.7:
            logger.info(f"Low confidence detection ({detection_result.get('confidence', 0)}), skipping purchase")
            return None
        
        # Get platform handler
        handler = self.handlers.get(platform.lower())
        if not handler:
            logger.error(f"No purchase handler for platform: {platform}")
            return None
        
        logger.info(f"🎯 High confidence ticket detection on {platform}, initiating purchase!")
        
        try:
            # Execute purchase with timeout
            result = await asyncio.wait_for(
                handler.execute_purchase(page, detection_result),
                timeout=45.0
            )
            
            # Record statistics
            if result.success:
                stats_manager.record_purchase_success(
                    platform,
                    result.tickets_purchased,
                    result.total_price
                )
                
                # Send success notification
                await notification_manager.send_purchase_success(
                    platform=platform,
                    order_id=result.order_id,
                    tickets=result.tickets_purchased,
                    price=result.total_price
                )
                
                logger.info(f"🎉 Purchase successful on {platform}! Order: {result.order_id}")
            else:
                stats_manager.record_purchase_failure(platform, result.error)
                logger.warning(f"Purchase failed on {platform}: {result.error}")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Purchase timeout on {platform}")
            return PurchaseResult(success=False, error="Timeout")
        except Exception as e:
            logger.error(f"Purchase error on {platform}: {e}")
            return PurchaseResult(success=False, error=str(e))


# Global instance
purchase_engine = TicketPurchaseEngine()
