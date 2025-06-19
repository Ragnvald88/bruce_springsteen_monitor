# Enhanced FanSale handler optimizations
"""
This file contains optimizations to be added to the existing fansale.py
DO NOT replace the original file - these are enhancements
"""

# Add these methods to the FansalePlatform class in src/platforms/fansale.py

async def fast_ticket_check(self, page: Page) -> List[Dict[str, Any]]:
    """
    Ultra-fast ticket availability check
    Optimized for speed over completeness
    """
    tickets = []
    
    try:
        # Use the most efficient selector
        offers = await page.query_selector_all('[data-offer-id][data-offertype*="fisso"]')
        
        # Batch evaluate for speed
        if offers:
            tickets_data = await page.evaluate("""
                () => {
                    const offers = document.querySelectorAll('[data-offer-id][data-offertype*="fisso"]');
                    return Array.from(offers).map(el => ({
                        id: el.getAttribute('data-offer-id'),
                        price: el.querySelector('.moneyValueFormat')?.textContent || '',
                        desc: el.querySelector('.OfferEntry-SeatDescription')?.textContent || '',
                        link: el.querySelector('a')?.href || ''
                    }));
                }
            """)
            
            for data in tickets_data:
                if data['id'] and data['price']:
                    tickets.append({
                        'offer_id': data['id'],
                        'price_text': data['price'],
                        'description': data['desc'],
                        'url': data['link'],
                        'platform': 'fansale'
                    })
                    
    except Exception as e:
        logger.debug(f"Fast check error: {e}")
        
    return tickets

async def instant_purchase(self, page: Page, offer_id: str) -> bool:
    """
    Execute purchase in under 2 seconds
    Optimized for speed with parallel actions
    """
    try:
        # Direct navigation to offer
        offer_url = f"{page.url}?offerId={offer_id}"
        
        # Navigate and prepare for Acquista button in parallel
        await page.goto(offer_url, wait_until='domcontentloaded')
        
        # Immediately look for and click Acquista
        await page.click('button[data-qa="buyNowButton"]', timeout=2000)
        
        # Handle any checkboxes without waiting
        page.evaluate("""
            () => {
                document.querySelectorAll('input[type="checkbox"]:not(:checked)').forEach(cb => cb.click());
            }
        """)
        
        # Click confirm/purchase
        await page.click('button[type="submit"]:not(:disabled)', timeout=2000)
        
        return True
        
    except Exception as e:
        logger.error(f"Instant purchase failed: {e}")
        return False

async def warmup_for_speed(self, page: Page):
    """
    Warmup page for maximum speed
    Pre-loads critical resources
    """
    try:
        # Pre-execute critical JavaScript
        await page.evaluate("""
            () => {
                // Pre-compile selectors
                document.querySelector('[data-offer-id]');
                document.querySelector('.moneyValueFormat');
                document.querySelector('button[data-qa="buyNowButton"]');
                
                // Warm up event listeners
                const clickEvent = new MouseEvent('click', {bubbles: true});
                
                // Cache jQuery if available
                if (window.$) {
                    window.$('[data-offer-id]').length;
                }
            }
        """)
        
        # Trigger any lazy-loaded content
        await page.evaluate("window.scrollTo(0, 500)")
        await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        
    except Exception as e:
        logger.debug(f"Warmup error: {e}")

# Anti-detection improvements
async def simulate_human_browsing(self, page: Page):
    """
    Quick human-like actions to avoid detection
    """
    try:
        # Random mouse movement
        x = 400 + (100 * (await page.evaluate("Math.random()") - 0.5))
        y = 300 + (100 * (await page.evaluate("Math.random()") - 0.5))
        await page.mouse.move(x, y)
        
        # Random scroll
        scroll = await page.evaluate("Math.floor(Math.random() * 200)")
        await page.evaluate(f"window.scrollBy(0, {scroll})")
        
    except:
        pass

# Session management
async def check_session_health(self, page: Page) -> bool:
    """
    Quick check if session is still valid
    """
    try:
        # Check for bot protection modal
        bot_modal = await page.query_selector('.js-BotProtectionModal:not(.hidden)')
        if bot_modal:
            logger.warning("Bot protection detected!")
            return False
            
        # Check if still logged in
        user_menu = await page.query_selector('.user-menu, .logout-button')
        return user_menu is not None
        
    except:
        return False
