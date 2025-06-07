# src/core/ticket_reserver.py
"""
Immediate ticket reservation module - opens browser and attempts to reserve tickets
"""

import asyncio
import logging
import webbrowser
from typing import Dict, Any, Optional
from datetime import datetime
from playwright.async_api import Page, BrowserContext

logger = logging.getLogger(__name__)


class TicketReserver:
    """Handles immediate ticket reservation when tickets are found"""
    
    def __init__(self, open_browser_mode: str = "both"):
        """
        Initialize ticket reserver
        
        Args:
            open_browser_mode: "default" (system browser), "automated" (playwright), or "both"
        """
        self.open_browser_mode = open_browser_mode
        self.reservation_attempts = 0
        self.successful_reservations = 0
        
    async def reserve_ticket(self, opportunity: Dict[str, Any], browser_context: Optional[BrowserContext] = None) -> bool:
        """
        Immediately attempt to reserve a ticket
        
        Args:
            opportunity: Ticket opportunity dict with url, platform, etc.
            browser_context: Optional existing browser context to use
            
        Returns:
            bool: True if reservation was successful or browser opened
        """
        self.reservation_attempts += 1
        
        logger.critical("=" * 80)
        logger.critical("🎟️ TICKET FOUND - IMMEDIATE ACTION REQUIRED!")
        logger.critical("=" * 80)
        logger.critical(f"🎸 Event: {opportunity.get('event_name', 'Unknown')}")
        logger.critical(f"💰 Price: €{opportunity.get('price', 'Unknown')}")
        logger.critical(f"📍 Section: {opportunity.get('section', 'Unknown')}")
        logger.critical(f"🎫 Quantity: {opportunity.get('quantity', 1)}")
        logger.critical(f"🌐 Platform: {opportunity.get('platform', 'Unknown')}")
        logger.critical(f"🔗 URL: {opportunity.get('url', 'Unknown')}")
        logger.critical("=" * 80)
        
        success = False
        
        # 1. Always open in default browser for user visibility
        if self.open_browser_mode in ["default", "both"]:
            try:
                logger.critical("🚀 OPENING IN YOUR DEFAULT BROWSER NOW!")
                webbrowser.open(opportunity['url'])
                logger.critical("✅ Browser opened! Check your browser window!")
                success = True
            except Exception as e:
                logger.error(f"❌ Failed to open default browser: {e}")
        
        # 2. Also attempt automated reservation if configured
        if self.open_browser_mode in ["automated", "both"] and browser_context:
            try:
                success = await self._automated_reservation(opportunity, browser_context) or success
            except Exception as e:
                logger.error(f"❌ Automated reservation failed: {e}", exc_info=True)
        
        if success:
            self.successful_reservations += 1
            logger.critical(f"🎉 Reservation attempt #{self.reservation_attempts} completed!")
        
        return success
    
    async def _automated_reservation(self, opportunity: Dict[str, Any], browser_context: BrowserContext) -> bool:
        """
        Attempt automated ticket reservation
        """
        platform = opportunity.get('platform', '').lower()
        
        logger.info(f"🤖 Starting automated reservation for {platform}...")
        
        try:
            page = await browser_context.new_page()
            
            # Navigate to ticket URL
            logger.info(f"🌐 Navigating to {opportunity['url']}...")
            await page.goto(opportunity['url'], wait_until='domcontentloaded', timeout=30000)
            
            # Platform-specific reservation logic
            if platform == 'fansale':
                return await self._reserve_fansale(page, opportunity)
            elif platform == 'ticketmaster':
                return await self._reserve_ticketmaster(page, opportunity)
            elif platform == 'vivaticket':
                return await self._reserve_vivaticket(page, opportunity)
            else:
                logger.warning(f"⚠️ No automated reservation logic for platform: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Automated reservation error: {e}")
            return False
    
    async def _reserve_fansale(self, page: Page, opportunity: Dict[str, Any]) -> bool:
        """FanSale specific reservation logic"""
        logger.info("🎯 Attempting FanSale reservation...")
        
        try:
            # Wait for page to stabilize
            await asyncio.sleep(2)
            
            # Look for add to cart buttons
            selectors = [
                'button[class*="add"]',
                'button[class*="cart"]',
                'button:has-text("Aggiungi")',
                'button:has-text("Carrello")',
                '[data-testid="add-to-cart"]',
                'a[href*="add-to-cart"]'
            ]
            
            for selector in selectors:
                try:
                    button = await page.wait_for_selector(selector, timeout=5000)
                    if button and await button.is_visible():
                        logger.critical(f"🎯 Found reservation button: {selector}")
                        
                        # Highlight button
                        await page.evaluate('''(element) => {
                            element.style.border = "5px solid red";
                            element.style.backgroundColor = "yellow";
                            element.scrollIntoView();
                        }''', button)
                        
                        # Click the button
                        logger.critical("🖱️ CLICKING RESERVATION BUTTON NOW!")
                        await button.click()
                        
                        # Wait for cart or next step
                        await asyncio.sleep(3)
                        
                        # Check if we're in cart or checkout
                        if 'cart' in page.url or 'checkout' in page.url:
                            logger.critical("✅ SUCCESSFULLY ADDED TO CART!")
                            
                            # Look for checkout button
                            checkout_selectors = [
                                'button:has-text("Checkout")',
                                'button:has-text("Procedi")',
                                'a[href*="checkout"]'
                            ]
                            
                            for checkout_sel in checkout_selectors:
                                try:
                                    checkout_btn = await page.wait_for_selector(checkout_sel, timeout=3000)
                                    if checkout_btn:
                                        logger.critical("📦 Found checkout button - ready to complete purchase!")
                                        # In production, we might auto-click this too
                                        await page.evaluate('''(element) => {
                                            element.style.border = "5px solid green";
                                            element.style.backgroundColor = "lightgreen";
                                        }''', checkout_btn)
                                        break
                                except:
                                    continue
                            
                            return True
                        
                        logger.info("⏳ Waiting for cart confirmation...")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Selector {selector} not found: {e}")
                    continue
            
            logger.warning("⚠️ No reservation button found - ticket might be sold out")
            
            # Take screenshot for debugging
            screenshot_path = f"logs/fansale_no_button_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ FanSale reservation error: {e}")
            return False
    
    async def _reserve_ticketmaster(self, page: Page, opportunity: Dict[str, Any]) -> bool:
        """Ticketmaster specific reservation logic"""
        logger.info("🎯 Attempting Ticketmaster reservation...")
        
        try:
            # Ticketmaster often has queue system
            if 'queue' in page.url:
                logger.warning("⏳ In Ticketmaster queue - waiting...")
                await page.wait_for_url_change(timeout=300000)  # 5 min timeout for queue
            
            # Look for ticket selection
            selectors = [
                'button[aria-label*="tickets"]',
                'button:has-text("Get Tickets")',
                'button:has-text("Find Tickets")',
                '[data-testid="event-offer-card"]'
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.critical(f"🎯 Found ticket element: {selector}")
                        await element.click()
                        await asyncio.sleep(2)
                        
                        # Look for quantity selector
                        qty_selector = 'select[name="quantity"], input[type="number"]'
                        qty_element = await page.wait_for_selector(qty_selector, timeout=3000)
                        if qty_element:
                            await qty_element.select_option(str(opportunity.get('quantity', 1)))
                        
                        # Add to cart
                        cart_btn = await page.wait_for_selector('button:has-text("Add")', timeout=3000)
                        if cart_btn:
                            await cart_btn.click()
                            logger.critical("✅ Added to Ticketmaster cart!")
                            return True
                        
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ticketmaster reservation error: {e}")
            return False
    
    async def _reserve_vivaticket(self, _page: Page, _opportunity: Dict[str, Any]) -> bool:
        """VivaTicket specific reservation logic"""
        logger.info("🎯 Attempting VivaTicket reservation...")
        
        try:
            # VivaTicket logic would go here
            # Similar pattern to other platforms
            logger.warning("⚠️ VivaTicket automation not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"❌ VivaTicket reservation error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reservation statistics"""
        return {
            'attempts': self.reservation_attempts,
            'successful': self.successful_reservations,
            'success_rate': self.successful_reservations / max(1, self.reservation_attempts)
        }