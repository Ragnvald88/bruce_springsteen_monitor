#!/usr/bin/env python3
"""
FanSale.it Ticket Monitor - Optimized for Bruce Springsteen Milano
High-speed ticket monitoring with anti-detection measures
"""

import asyncio
import time
import random
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import os
from dotenv import load_dotenv
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FanSaleMonitor:
    """High-performance ticket monitor with anti-detection measures"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.bruce_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Performance optimizations
        self.parallel_contexts = 3  # Multiple browser contexts for redundancy
        self.check_interval = 1.5  # Faster checking
        self.use_lightweight_mode = True  # Block unnecessary resources
        
        # Anti-detection
        self.session_rotation_interval = 5 * 60  # Rotate every 5 minutes
        self.contexts: List[BrowserContext] = []
        self.last_rotation = time.time()
        
        # State management
        self.tickets_found: Set[str] = set()  # Track found tickets to avoid duplicates
        self.purchase_in_progress = False
        
    async def create_optimized_context(self, browser: Browser) -> BrowserContext:
        """Create lightweight browser context optimized for speed"""
        
        # Randomize fingerprint
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864}
        ]
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        context = await browser.new_context(
            viewport=random.choice(viewports),
            user_agent=random.choice(user_agents),
            locale='it-IT',
            timezone_id='Europe/Rome',
            ignore_https_errors=True,
            java_script_enabled=True,
            extra_http_headers={
                'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        )
        
        # Block unnecessary resources for speed
        if self.use_lightweight_mode:
            await context.route("**/*", lambda route: 
                route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"]
                else route.continue_()
            )
        
        # Anti-detection script
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = {runtime: {}};
            
            // Randomize canvas fingerprint
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.01;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
        """)
        
        return context
    
    async def fast_login(self, page: Page) -> bool:
        """Optimized login process"""
        try:
            # Check if already logged in
            await page.goto(self.bruce_url, wait_until='domcontentloaded', timeout=15000)
            
            if await page.query_selector('.user-menu, [href*="logout"]'):
                return True
            
            # Fast navigation to login
            await page.goto('https://www.fansale.it/fansale/login', wait_until='domcontentloaded')
            
            # Quick form fill
            await page.fill('input[type="email"]', self.email, timeout=5000)
            await page.fill('input[type="password"]', self.password, timeout=5000)
            
            # Submit and wait for navigation
            await asyncio.gather(
                page.click('button[type="submit"]'),
                page.wait_for_navigation(wait_until='domcontentloaded', timeout=10000)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def check_tickets_fast(self, page: Page) -> List[Dict]:
        """Ultra-fast ticket checking"""
        tickets = []
        
        try:
            # Go directly to URL if not there
            if page.url != self.bruce_url:
                await page.goto(self.bruce_url, wait_until='domcontentloaded', timeout=10000)
            else:
                # Just reload for fresh data
                await page.reload(wait_until='domcontentloaded', timeout=10000)
            
            # Fast ticket detection
            await page.wait_for_selector('[data-offer-id], .OfferEntry', timeout=5000)
            
            # Get all offers in one go
            offers_data = await page.evaluate("""
                () => {
                    const offers = [];
                    document.querySelectorAll('[data-offer-id]').forEach(offer => {
                        const priceElem = offer.querySelector('.moneyValueFormat');
                        const seatElem = offer.querySelector('.OfferEntry-SeatDescription');
                        const quantityElem = offer.querySelector('.NumberOfTicketsInOffer');
                        
                        offers.push({
                            id: offer.getAttribute('data-offer-id'),
                            price: priceElem ? priceElem.innerText : '',
                            seat: seatElem ? seatElem.innerText : '',
                            quantity: quantityElem ? quantityElem.innerText : '1',
                            isFixedPrice: offer.getAttribute('data-offertype')?.includes('fisso') || false
                        });
                    });
                    return offers;
                }
            """)
            
            # Filter new tickets
            for offer in offers_data:
                if offer['id'] and offer['id'] not in self.tickets_found:
                    self.tickets_found.add(offer['id'])
                    tickets.append(offer)
                    logger.info(f"🎫 NEW TICKET: {offer['seat']} - {offer['price']} - Qty: {offer['quantity']}")
            
            return tickets
            
        except Exception as e:
            logger.debug(f"Check error: {e}")
            return []
    
    async def instant_purchase(self, page: Page, offer_id: str) -> bool:
        """Lightning-fast ticket purchase"""
        if self.purchase_in_progress:
            return False
            
        self.purchase_in_progress = True
        try:
            # Click the offer
            await page.click(f'[data-offer-id="{offer_id}"]', timeout=3000)
            
            # Quick purchase flow
            await page.wait_for_selector('button[data-qa="purchase-button"], .buy-button', timeout=5000)
            await page.click('button[data-qa="purchase-button"], .buy-button')
            
            # Complete checkout
            logger.info(f"✅ Purchase initiated for offer {offer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            return False
        finally:
            self.purchase_in_progress = False
    
    async def monitor_worker(self, context: BrowserContext, worker_id: int):
        """Individual monitoring worker"""
        page = await context.new_page()
        
        # Login once
        if not await self.fast_login(page):
            logger.error(f"Worker {worker_id} login failed")
            return
        
        logger.info(f"Worker {worker_id} started monitoring")
        
        while True:
            try:
                # Check for session rotation
                if time.time() - self.last_rotation > self.session_rotation_interval:
                    logger.info(f"Worker {worker_id} needs rotation")
                    break
                
                # Fast ticket check
                tickets = await self.check_tickets_fast(page)
                
                # Instant purchase on fixed price tickets
                for ticket in tickets:
                    if ticket.get('isFixedPrice'):
                        asyncio.create_task(self.instant_purchase(page, ticket['id']))
                
                # Brief delay
                await asyncio.sleep(self.check_interval + random.random() * 0.5)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(2)
    
    async def run(self):
        """Main monitoring loop with parallel workers"""
        async with async_playwright() as p:
            # Use Chromium for best compatibility
            browser = await p.chromium.launch(
                headless=True,  # Headless for speed
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-blink-features',
                    '--disable-ipc-flooding-protection'
                ]
            )
            
            while True:
                try:
                    # Create parallel contexts
                    contexts = []
                    for i in range(self.parallel_contexts):
                        context = await self.create_optimized_context(browser)
                        contexts.append(context)
                    
                    # Start parallel workers
                    workers = []
                    for i, context in enumerate(contexts):
                        worker = asyncio.create_task(self.monitor_worker(context, i))
                        workers.append(worker)
                    
                    # Wait for rotation interval
                    await asyncio.sleep(self.session_rotation_interval)
                    
                    # Cancel workers
                    for worker in workers:
                        worker.cancel()
                    
                    # Close contexts
                    for context in contexts:
                        await context.close()
                    
                    self.last_rotation = time.time()
                    logger.info("Session rotation completed")
                    
                except Exception as e:
                    logger.error(f"Main loop error: {e}")
                    await asyncio.sleep(5)

async def main():
    """Entry point"""
    monitor = FanSaleMonitor()
    
    if not monitor.email or not monitor.password:
        logger.error("Please set FANSALE_EMAIL and FANSALE_PASSWORD in .env file")
        return
    
    logger.info("🚀 Starting FanSale monitor - Bruce Springsteen Milano")
    logger.info(f"Email: {monitor.email}")
    logger.info(f"Parallel contexts: {monitor.parallel_contexts}")
    logger.info(f"Check interval: {monitor.check_interval}s")
    
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())