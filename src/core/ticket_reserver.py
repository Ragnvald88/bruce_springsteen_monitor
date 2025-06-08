# src/core/ticket_reserver.py
"""
StealthMaster AI v3.0 - Ticket Reservation Module
Handles immediate ticket reservation when opportunities are found
"""

import logging
import webbrowser
from typing import Dict, Any, Optional
from playwright.async_api import Page, BrowserContext

from .models import EnhancedTicketOpportunity

logger = logging.getLogger(__name__)


class TicketReserver:
    """Handles immediate ticket reservation when tickets are found"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ticket reserver
        
        Args:
            config: Configuration dict containing settings
        """
        self.config = config
        self.open_browser_mode = config.get('app_settings', {}).get('open_browser_mode', 'both')
        self.reservation_attempts = 0
        self.successful_reservations = 0
        self.platform_stats = {
            'fansale': {'attempts': 0, 'successes': 0},
            'ticketmaster': {'attempts': 0, 'successes': 0},
            'vivaticket': {'attempts': 0, 'successes': 0}
        }
        
    async def attempt_reservation(self, opportunity: EnhancedTicketOpportunity, browser_context: Optional[BrowserContext] = None) -> bool:
        """
        Immediately attempt to reserve a ticket
        
        Args:
            opportunity: EnhancedTicketOpportunity object
            browser_context: Optional existing browser context to use
            
        Returns:
            bool: True if reservation was successful or browser opened
        """
        self.reservation_attempts += 1
        platform = opportunity.platform.lower()
        if platform in self.platform_stats:
            self.platform_stats[platform]['attempts'] += 1
        
        logger.critical("=" * 80)
        logger.critical("🎟️ TICKET FOUND - IMMEDIATE ACTION REQUIRED!")
        logger.critical("=" * 80)
        logger.critical(f"🎸 Event: {opportunity.event_name}")
        logger.critical(f"💰 Price: €{opportunity.price}")
        logger.critical(f"📍 Section: {opportunity.section}")
        logger.critical(f"🎫 Quantity: {opportunity.quantity}")
        logger.critical(f"🌐 Platform: {opportunity.platform}")
        logger.critical(f"🔗 URL: {opportunity.url}")
        logger.critical(f"⏰ Found at: {opportunity.detected_at}")
        logger.critical("=" * 80)
        
        success = False
        
        # 1. Always open in default browser for user visibility
        if self.open_browser_mode in ["default", "both"]:
            try:
                logger.critical("🚀 OPENING IN YOUR DEFAULT BROWSER NOW!")
                webbrowser.open(opportunity.url)
                logger.critical("✅ Browser opened! Check your browser window!")
                success = True
            except Exception as e:
                logger.error(f"❌ Failed to open default browser: {e}")
        
        # 2. Also attempt automated reservation if configured
        if self.open_browser_mode in ["automated", "both"] and browser_context:
            try:
                automated_success = await self._automated_reservation(opportunity, browser_context)
                success = success or automated_success
            except Exception as e:
                logger.error(f"❌ Automated reservation failed: {e}", exc_info=True)
        
        if success:
            self.successful_reservations += 1
            if platform in self.platform_stats:
                self.platform_stats[platform]['successes'] += 1
            logger.critical(f"🎉 Reservation attempt #{self.reservation_attempts} completed!")
        
        return success
    
    async def _automated_reservation(self, opportunity: EnhancedTicketOpportunity, browser_context: BrowserContext) -> bool:
        """
        Attempt automated reservation through browser automation
        
        Args:
            opportunity: Ticket opportunity
            browser_context: Browser context to use
            
        Returns:
            bool: True if automated reservation was successful
        """
        try:
            # Create a new page for reservation
            page = await browser_context.new_page()
            
            # Navigate to ticket URL
            logger.info(f"🤖 Attempting automated reservation for {opportunity.platform}")
            await page.goto(opportunity.url, wait_until='domcontentloaded', timeout=30000)
            
            # Platform-specific reservation logic
            platform = opportunity.platform.lower()
            
            if platform == 'fansale':
                return await self._reserve_fansale(page, opportunity)
            elif platform == 'ticketmaster':
                return await self._reserve_ticketmaster(page, opportunity)
            elif platform == 'vivaticket':
                return await self._reserve_vivaticket(page, opportunity)
            else:
                logger.warning(f"No automated reservation logic for platform: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"Automated reservation error: {e}")
            return False
        finally:
            if 'page' in locals():
                await page.close()
    
    async def _reserve_fansale(self, page: Page, opportunity: EnhancedTicketOpportunity) -> bool:
        """FanSale specific reservation logic"""
        try:
            # Wait for and click add to cart button
            add_to_cart_selector = 'button[data-cy="add-to-cart"], button:has-text("In den Warenkorb")'
            await page.wait_for_selector(add_to_cart_selector, timeout=10000)
            await page.click(add_to_cart_selector)
            
            # Wait for cart confirmation
            await page.wait_for_selector('div[data-cy="cart-confirmation"], div.cart-success', timeout=5000)
            
            # Click proceed to checkout
            checkout_selector = 'button[data-cy="proceed-to-checkout"], button:has-text("Zur Kasse")'
            await page.click(checkout_selector)
            
            logger.info("✅ FanSale: Added to cart and proceeding to checkout")
            return True
            
        except Exception as e:
            logger.error(f"FanSale reservation failed: {e}")
            return False
    
    async def _reserve_ticketmaster(self, page: Page, opportunity: EnhancedTicketOpportunity) -> bool:
        """Ticketmaster specific reservation logic"""
        try:
            # Handle queue if present
            if await page.locator('div[class*="queue"], div[id*="queue"]').count() > 0:
                logger.info("⏳ Waiting in Ticketmaster queue...")
                await page.wait_for_selector('div[class*="queue"]', state='hidden', timeout=300000)
            
            # Click on ticket listing
            ticket_selector = f'div[data-seat-section*="{opportunity.section}"], div:has-text("{opportunity.section}")'
            await page.wait_for_selector(ticket_selector, timeout=20000)
            await page.click(ticket_selector)
            
            # Add to cart
            add_button = 'button[aria-label*="Add to cart"], button:has-text("Add to Cart")'
            await page.wait_for_selector(add_button, timeout=10000)
            await page.click(add_button)
            
            logger.info("✅ Ticketmaster: Ticket selected and added to cart")
            return True
            
        except Exception as e:
            logger.error(f"Ticketmaster reservation failed: {e}")
            return False
    
    async def _reserve_vivaticket(self, page: Page, opportunity: EnhancedTicketOpportunity) -> bool:
        """VivaTicket specific reservation logic"""
        try:
            # Select ticket quantity if needed
            if opportunity.quantity > 1:
                quantity_selector = 'select[name="quantity"], input[type="number"][name="quantity"]'
                if await page.locator(quantity_selector).count() > 0:
                    await page.select_option(quantity_selector, str(opportunity.quantity))
            
            # Click buy button
            buy_button = 'button.btn-buy, button:has-text("Acquista"), button:has-text("Buy")'
            await page.wait_for_selector(buy_button, timeout=10000)
            await page.click(buy_button)
            
            # Confirm selection
            confirm_button = 'button.confirm-selection, button:has-text("Conferma")'
            if await page.locator(confirm_button).count() > 0:
                await page.click(confirm_button)
            
            logger.info("✅ VivaTicket: Ticket selected and proceeding to purchase")
            return True
            
        except Exception as e:
            logger.error(f"VivaTicket reservation failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reservation statistics"""
        return {
            'total_attempts': self.reservation_attempts,
            'successful_reservations': self.successful_reservations,
            'success_rate': (self.successful_reservations / max(1, self.reservation_attempts)) * 100,
            'platform_stats': self.platform_stats
        }