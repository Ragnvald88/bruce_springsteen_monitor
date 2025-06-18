"""
Ticket Strike Engine - Lightning-Fast Purchase Execution
========================================================
Executes ticket purchases with maximum speed and reliability
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from playwright.async_api import Page, BrowserContext
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class StrikeResult:
    """Result of a ticket strike attempt"""
    success: bool
    ticket_id: str
    confirmation_number: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0
    stage_reached: str = 'initialization'
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class TicketStrikeEngine:
    """
    Ultra-fast ticket purchase execution
    
    Optimizations:
    - Pre-loaded pages at checkout
    - Pre-filled forms
    - Parallel execution paths
    - Optimistic clicking
    - WebSocket order submission
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.payment_info = config['payment_info']
        self.user_info = config['user_info']
        
        # Pre-computed selectors for speed
        self.selectors = {
            'offer_button': '[data-offer-id="{offer_id}"] a, [data-offer-id="{offer_id}"] button',
            'acquista_button': 'button[data-qa="buyNowButton"], button:has-text("Acquista")',
            'confirm_button': 'button[type="submit"]:has-text("Conferma")',
            'accept_terms': 'input[type="checkbox"][name*="terms"], input[type="checkbox"][name*="condizioni"]',
            'quantity_select': 'select[name="quantity"], input[name="quantity"]',
            'success_indicator': '.confirmation-number, .order-success, [data-qa="confirmationMessage"]'
        }
        
        # Strike statistics
        self.total_strikes = 0
        self.successful_strikes = 0
        self.average_time_ms = 0
        
    async def execute_strike(
        self, 
        page: Page, 
        ticket_offer: 'TicketOffer',
        context: Optional[BrowserContext] = None
    ) -> StrikeResult:
        """
        Execute lightning-fast ticket purchase
        Target: < 2 seconds from detection to confirmation
        """
        start_time = time.time()
        self.total_strikes += 1
        
        try:
            # Stage 1: Navigate to offer (if not already there)
            if ticket_offer.url not in page.url:
                await page.goto(ticket_offer.url, wait_until='domcontentloaded')
            
            # Stage 2: Click offer with optimistic approach
            result = await self._fast_click_offer(page, ticket_offer)
            if not result:
                return StrikeResult(
                    success=False,
                    ticket_id=ticket_offer.offer_id,
                    error_message="Failed to click offer",
                    execution_time_ms=(time.time() - start_time) * 1000,
                    stage_reached='offer_click'
                )
            
            # Stage 3: Handle quantity and options (parallel with next stage)
            quantity_task = asyncio.create_task(
                self._handle_quantity(page, ticket_offer.quantity)
            )
            
            # Stage 4: Click Acquista (don't wait for quantity)
            acquista_clicked = await self._fast_click_acquista(page)
            if not acquista_clicked:
                return StrikeResult(
                    success=False,
                    ticket_id=ticket_offer.offer_id,
                    error_message="Failed to click Acquista",
                    execution_time_ms=(time.time() - start_time) * 1000,
                    stage_reached='acquista_click'
                )
            
            # Ensure quantity was set
            await quantity_task
            
            # Stage 5: Fill payment info (pre-optimized)
            await self._ultra_fast_checkout(page)
            
            # Stage 6: Confirm purchase
            confirmation = await self._confirm_purchase(page)
            
            if confirmation:
                execution_time = (time.time() - start_time) * 1000
                self.successful_strikes += 1
                self._update_average_time(execution_time)
                
                logger.info(f"⚡ STRIKE SUCCESS in {execution_time:.0f}ms! Confirmation: {confirmation}")
                
                return StrikeResult(
                    success=True,
                    ticket_id=ticket_offer.offer_id,
                    confirmation_number=confirmation,
                    execution_time_ms=execution_time,
                    stage_reached='completed'
                )
            else:
                return StrikeResult(
                    success=False,
                    ticket_id=ticket_offer.offer_id,
                    error_message="No confirmation received",
                    execution_time_ms=(time.time() - start_time) * 1000,
                    stage_reached='confirmation'
                )
                
        except Exception as e:
            logger.error(f"Strike failed: {e}")
            return StrikeResult(
                success=False,
                ticket_id=ticket_offer.offer_id,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
                stage_reached='error'
            )
    
    async def _fast_click_offer(self, page: Page, ticket_offer: 'TicketOffer') -> bool:
        """Ultra-fast offer clicking"""
        try:
            # Try multiple selectors in parallel
            selectors = [
                self.selectors['offer_button'].format(offer_id=ticket_offer.offer_id),
                f'[data-offer-id="{ticket_offer.offer_id}"]',
                '.js-Button-inOfferEntryList',
                'a[id*="detailBShowOfferButton"]'
            ]
            
            # Race to find element
            element = None
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        break
                except:
                    continue
            
            if not element:
                return False
            
            # Click immediately
            await element.click(force=True, no_wait_after=True)
            
            # Don't wait for navigation, continue optimistically
            return True
            
        except Exception as e:
            logger.error(f"Error clicking offer: {e}")
            return False
    
    async def _handle_quantity(self, page: Page, quantity: int):
        """Handle quantity selection if needed"""
        try:
            # Look for quantity selector
            qty_element = await page.wait_for_selector(
                self.selectors['quantity_select'],
                timeout=500,
                state='visible'
            )
            
            if qty_element:
                # Set quantity
                tag = await qty_element.evaluate('el => el.tagName')
                if tag == 'SELECT':
                    await qty_element.select_option(str(quantity))
                else:
                    await qty_element.fill(str(quantity))
                    
        except:
            # Quantity might be pre-set or not needed
            pass
    
    async def _fast_click_acquista(self, page: Page) -> bool:
        """Click Acquista button with maximum speed"""
        try:
            # Multiple strategies in parallel
            strategies = [
                # Strategy 1: Wait for selector
                page.wait_for_selector(self.selectors['acquista_button'], timeout=2000),
                
                # Strategy 2: Find by text
                page.get_by_role('button', name='Acquista'),
                
                # Strategy 3: JavaScript click
                page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const acquista = buttons.find(b => 
                            b.textContent.includes('Acquista') || 
                            b.textContent.includes('Buy')
                        );
                        if (acquista) {
                            acquista.click();
                            return true;
                        }
                        return false;
                    }
                """)
            ]
            
            # First successful click wins
            results = await asyncio.gather(*[
                self._try_click_strategy(s) for s in strategies
            ], return_exceptions=True)
            
            return any(r for r in results if r and not isinstance(r, Exception))
            
        except Exception as e:
            logger.error(f"Error clicking Acquista: {e}")
            return False
    
    async def _try_click_strategy(self, strategy) -> bool:
        """Try a click strategy"""
        try:
            if asyncio.iscoroutine(strategy):
                element = await strategy
                if element:
                    await element.click(force=True, no_wait_after=True)
                    return True
            else:
                result = await strategy
                return bool(result)
        except:
            return False
    
    async def _ultra_fast_checkout(self, page: Page):
        """Fill checkout form with maximum speed"""
        try:
            # Pre-compute all form data
            form_fills = [
                ('input[name="firstName"], input[name="nome"]', self.user_info['first_name']),
                ('input[name="lastName"], input[name="cognome"]', self.user_info['last_name']),
                ('input[name="email"]', self.user_info['email']),
                ('input[name="phone"], input[name="telefono"]', self.user_info['phone']),
                ('input[name="address"], input[name="indirizzo"]', self.user_info['address']),
                ('input[name="city"], input[name="citta"]', self.user_info['city']),
                ('input[name="zip"], input[name="cap"]', self.user_info['zip_code']),
                ('input[name="country"], select[name="paese"]', 'IT')
            ]
            
            # Fill all fields in parallel
            tasks = []
            for selector, value in form_fills:
                tasks.append(self._fast_fill_field(page, selector, value))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle checkboxes
            await self._handle_checkboxes(page)
            
            # Payment method (if needed)
            if hasattr(self, 'payment_info'):
                await self._select_payment_method(page)
                
        except Exception as e:
            logger.error(f"Checkout fill error: {e}")
    
    async def _fast_fill_field(self, page: Page, selector: str, value: str):
        """Fill a field as fast as possible"""
        try:
            element = await page.wait_for_selector(selector, timeout=1000)
            if element:
                # Clear and fill in one go
                await element.evaluate(f'el => {{ el.value = "{value}"; el.dispatchEvent(new Event("input", {{bubbles: true}})); }}')
        except:
            pass
    
    async def _handle_checkboxes(self, page: Page):
        """Check all required checkboxes"""
        try:
            # Find all unchecked required checkboxes
            checkboxes = await page.query_selector_all(
                'input[type="checkbox"]:not(:checked)[required], '
                'input[type="checkbox"]:not(:checked)[name*="terms"], '
                'input[type="checkbox"]:not(:checked)[name*="condizioni"]'
            )
            
            # Check them all
            for checkbox in checkboxes:
                await checkbox.click(force=True, no_wait_after=True)
                
        except Exception as e:
            logger.debug(f"Checkbox handling: {e}")
    
    async def _select_payment_method(self, page: Page):
        """Select payment method"""
        try:
            # For FanSale, usually it's pre-selected or only one option
            # Just ensure something is selected
            payment_radio = await page.query_selector(
                'input[type="radio"][name*="payment"]:not(:checked)'
            )
            if payment_radio:
                await payment_radio.click(force=True)
        except:
            pass
    
    async def _confirm_purchase(self, page: Page) -> Optional[str]:
        """Confirm the purchase and get confirmation number"""
        try:
            # Find and click confirm button
            confirm_button = await page.wait_for_selector(
                self.selectors['confirm_button'],
                timeout=2000
            )
            
            if not confirm_button:
                # Try JavaScript approach
                await page.evaluate("""
                    () => {
                        const forms = document.querySelectorAll('form');
                        for (const form of forms) {
                            if (form.action.includes('confirm') || form.action.includes('purchase')) {
                                form.submit();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
            else:
                await confirm_button.click()
            
            # Wait for success indicator
            success_element = await page.wait_for_selector(
                self.selectors['success_indicator'],
                timeout=10000
            )
            
            if success_element:
                # Extract confirmation number
                confirmation = await success_element.inner_text()
                
                # Try to extract just the number
                import re
                match = re.search(r'[A-Z0-9]{6,}', confirmation)
                if match:
                    return match.group()
                
                return confirmation
                
        except Exception as e:
            logger.error(f"Confirmation error: {e}")
            
        return None
    
    def _update_average_time(self, new_time: float):
        """Update average execution time"""
        if self.average_time_ms == 0:
            self.average_time_ms = new_time
        else:
            # Exponential moving average
            self.average_time_ms = 0.8 * self.average_time_ms + 0.2 * new_time
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get strike engine statistics"""
        success_rate = (
            self.successful_strikes / self.total_strikes * 100
            if self.total_strikes > 0 else 0
        )
        
        return {
            'total_strikes': self.total_strikes,
            'successful_strikes': self.successful_strikes,
            'success_rate': success_rate,
            'average_time_ms': self.average_time_ms,
            'target_time_ms': 2000  # Our goal
        }


# Optimized version for parallel strikes
class ParallelStrikeEngine(TicketStrikeEngine):
    """Execute multiple strikes in parallel for better success rate"""
    
    async def execute_parallel_strikes(
        self,
        contexts: List[BrowserContext],
        ticket_offer: 'TicketOffer'
    ) -> StrikeResult:
        """Execute strikes on multiple browser contexts in parallel"""
        
        # Create strike tasks
        tasks = []
        for i, context in enumerate(contexts[:3]):  # Max 3 parallel
            page = await context.new_page()
            task = self.execute_strike(page, ticket_offer, context)
            tasks.append(task)
            
            # Slight delay between strikes to avoid detection
            if i < len(contexts) - 1:
                await asyncio.sleep(0.1)
        
        # Wait for first success or all failures
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            
            if result.success:
                # Cancel remaining tasks
                for t in tasks:
                    if not t.done():
                        t.cancel()
                
                return result
        
        # Return best failure if no success
        return min(results, key=lambda r: r.execution_time_ms)
