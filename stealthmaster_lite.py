#!/usr/bin/env python3
"""
StealthMaster Lite - Optimized for FanSale & VivaTicket
Fast, efficient ticket monitoring and purchasing
"""

import asyncio
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging
from pathlib import Path
import sys

# Apply distutils patch for Python 3.12+ compatibility
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

# Setup paths
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import existing modules we'll reuse
from src.config import load_settings
from src.utils.logging import setup_logging

# Setup logging
logger = setup_logging("stealthmaster_lite")


class StealthMasterLite:
    """
    Simplified, fast ticket monitor for FanSale & VivaTicket
    - Single browser instance
    - 7-minute session rotation
    - Lightning-fast purchase execution
    - Minimal resource usage
    """
    
    def __init__(self):
        self.settings = load_settings()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.fansale_page: Optional[Page] = None
        self.vivaticket_page: Optional[Page] = None
        
        # Session management
        self.session_start_time = None
        self.session_duration = 420  # 7 minutes in seconds
        
        # Monitoring state
        self.monitoring = False
        self.tickets_found = set()  # Track found tickets to avoid duplicates
        
        # Performance tracking
        self.check_count = 0
        self.last_check_time = 0
        
    async def initialize(self):
        """Initialize browser with optimal settings"""
        logger.info("🚀 Starting StealthMaster Lite...")
        
        # Launch browser
        playwright = await async_playwright().start()
        
        # Browser args for stealth
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests'
        ]
        
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=browser_args,
            channel='chrome'  # Use regular Chrome if available
        )
        
        # Create context
        await self._create_context()
        
        logger.info("✅ Browser initialized")
        
    async def _create_context(self):
        """Create browser context with Italian settings"""
        # Get proxy from settings
        proxy_config = None
        if self.settings.proxy_settings.enabled:
            proxy = self.settings.proxy_settings.primary_pool[0]
            proxy_config = {
                'server': f'http://{proxy.host}:{proxy.port}',
                'username': proxy.username,
                'password': proxy.password
            }
            logger.info(f"🌐 Using proxy: {proxy.host}")
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='it-IT',
            timezone_id='Europe/Rome',
            proxy=proxy_config,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        )
        
        # Apply stealth JavaScript
        await self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Add chrome object
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {}
                };
            }
            
            // Override permissions
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = async (parameters) => {
                if (parameters.name === 'notifications') {
                    return { state: 'default' };
                }
                return originalQuery(parameters);
            };
            
            // Fix navigator properties
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['it-IT', 'it', 'en-US', 'en']
            });
            
            // Mouse movement tracking
            let mouseX = 100;
            let mouseY = 100;
            document.addEventListener('mousemove', (e) => {
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
        """)
        
        self.session_start_time = time.time()
        
    async def _rotate_session(self):
        """Rotate session before detection"""
        logger.info("🔄 Rotating session...")
        
        # Close existing pages
        if self.fansale_page:
            await self.fansale_page.close()
        if self.vivaticket_page:
            await self.vivaticket_page.close()
        
        # Close context
        if self.context:
            await self.context.close()
        
        # Create new context
        await self._create_context()
        
        # Recreate pages
        await self._setup_pages()
        
        logger.info("✅ Session rotated")
        
    async def _setup_pages(self):
        """Setup monitoring pages"""
        # FanSale page
        self.fansale_page = await self.context.new_page()
        await self._setup_fansale()
        
        # VivaTicket page
        self.vivaticket_page = await self.context.new_page()
        await self._setup_vivaticket()
        
    async def _setup_fansale(self):
        """Setup FanSale monitoring"""
        logger.info("🎫 Setting up FanSale...")
        
        # Navigate to FanSale
        await self.fansale_page.goto('https://www.fansale.it', wait_until='networkidle')
        
        # Accept cookies if present
        try:
            cookie_button = await self.fansale_page.wait_for_selector(
                'button:has-text("Accetta"), button:has-text("Accept")',
                timeout=3000
            )
            if cookie_button:
                await cookie_button.click()
        except:
            pass
        
        # Login if needed
        if await self._needs_login_fansale():
            await self._login_fansale()
        
        # Navigate to Bruce Springsteen tickets
        target_url = None
        for target in self.settings.targets:
            if target.platform == 'fansale' and target.enabled:
                target_url = target.url
                break
        
        if target_url:
            await self.fansale_page.goto(target_url, wait_until='networkidle')
            logger.info("✅ FanSale ready")
        
    async def _needs_login_fansale(self) -> bool:
        """Check if FanSale needs login"""
        logout_btn = await self.fansale_page.query_selector('.logout-button, [href*="logout"]')
        return logout_btn is None
        
    async def _login_fansale(self):
        """Quick FanSale login"""
        logger.info("🔐 Logging into FanSale...")
        
        await self.fansale_page.goto('https://www.fansale.it/fansale/login')
        
        # Email
        await self.fansale_page.fill('input[name="email"]', os.getenv('FANSALE_EMAIL'))
        
        # Password
        await self.fansale_page.fill('input[name="password"]', os.getenv('FANSALE_PASSWORD'))
        
        # Submit
        await self.fansale_page.click('button[type="submit"]')
        
        # Wait for login
        await self.fansale_page.wait_for_navigation()
        logger.info("✅ FanSale login successful")
        
    async def _setup_vivaticket(self):
        """Setup VivaTicket monitoring"""
        logger.info("🎫 Setting up VivaTicket...")
        
        # Navigate to VivaTicket
        await self.vivaticket_page.goto('https://www.vivaticket.com/it', wait_until='networkidle')
        
        # Accept cookies if present
        try:
            cookie_button = await self.vivaticket_page.wait_for_selector(
                'button:has-text("Accetta"), button:has-text("Accept")',
                timeout=3000
            )
            if cookie_button:
                await cookie_button.click()
        except:
            pass
        
        # Navigate to target event
        target_url = None
        for target in self.settings.targets:
            if target.platform == 'vivaticket' and target.enabled:
                target_url = target.url
                break
        
        if target_url:
            await self.vivaticket_page.goto(target_url, wait_until='networkidle')
            logger.info("✅ VivaTicket ready")
            
    async def start_monitoring(self):
        """Start monitoring both platforms"""
        logger.info("👀 Starting ticket monitoring...")
        
        self.monitoring = True
        
        # Setup pages initially
        await self._setup_pages()
        
        # Run monitoring loop
        while self.monitoring:
            try:
                # Check session age
                if time.time() - self.session_start_time > self.session_duration:
                    await self._rotate_session()
                
                # Check both platforms
                await asyncio.gather(
                    self._check_fansale(),
                    self._check_vivaticket(),
                    return_exceptions=True
                )
                
                # Quick pause
                await asyncio.sleep(1.5)
                
                self.check_count += 1
                if self.check_count % 20 == 0:
                    logger.info(f"✓ Completed {self.check_count} checks")
                    
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
                
    async def _check_fansale(self):
        """Check FanSale for tickets"""
        if not self.fansale_page:
            return
            
        try:
            # Refresh if needed
            if self.check_count % 10 == 0:
                await self.fansale_page.reload()
            
            # Find ticket offers
            offers = await self.fansale_page.query_selector_all('[data-offer-id]')
            
            for offer in offers:
                offer_id = await offer.get_attribute('data-offer-id')
                
                # Skip if already processed
                if offer_id in self.tickets_found:
                    continue
                
                # Get offer details quickly
                offer_data = await offer.evaluate("""
                    (el) => {
                        const getText = (sel) => {
                            const elem = el.querySelector(sel);
                            return elem ? elem.textContent.trim() : '';
                        };
                        return {
                            price: getText('.moneyValueFormat'),
                            description: getText('.OfferEntry-SeatDescription'),
                            type: el.getAttribute('data-offertype')
                        };
                    }
                """)
                
                # Check if it's a fixed price offer (immediate purchase)
                if 'fisso' in (offer_data.get('type') or '').lower():
                    self.tickets_found.add(offer_id)
                    
                    logger.info(f"🎯 TICKET FOUND on FanSale!")
                    logger.info(f"   {offer_data['description']}")
                    logger.info(f"   Price: €{offer_data['price']}")
                    
                    # Execute purchase
                    await self._purchase_fansale(offer, offer_id)
                    
        except Exception as e:
            logger.debug(f"FanSale check error: {e}")
            
    async def _check_vivaticket(self):
        """Check VivaTicket for tickets"""
        if not self.vivaticket_page:
            return
            
        try:
            # Look for resale tickets
            resale_section = await self.vivaticket_page.query_selector('[class*="resell"], [class*="rivendita"]')
            
            if resale_section:
                # Find available tickets
                tickets = await self.vivaticket_page.query_selector_all('.ticket-available, [class*="disponibile"]')
                
                for ticket in tickets:
                    ticket_id = await ticket.get_attribute('data-ticket-id') or str(time.time())
                    
                    if ticket_id in self.tickets_found:
                        continue
                    
                    # Get ticket info
                    ticket_data = await ticket.evaluate("""
                        (el) => {
                            return {
                                price: el.querySelector('[class*="price"]')?.textContent || '',
                                section: el.querySelector('[class*="settore"]')?.textContent || '',
                                available: !el.classList.contains('sold-out')
                            };
                        }
                    """)
                    
                    if ticket_data['available']:
                        self.tickets_found.add(ticket_id)
                        
                        logger.info(f"🎯 TICKET FOUND on VivaTicket!")
                        logger.info(f"   Section: {ticket_data['section']}")
                        logger.info(f"   Price: {ticket_data['price']}")
                        
                        # Execute purchase
                        await self._purchase_vivaticket(ticket)
                        
        except Exception as e:
            logger.debug(f"VivaTicket check error: {e}")
            
    async def _purchase_fansale(self, offer_element, offer_id: str):
        """Execute FanSale purchase"""
        start_time = time.time()
        
        try:
            # Click the offer
            await offer_element.click()
            
            # Wait for and click Acquista button
            acquista_btn = await self.fansale_page.wait_for_selector(
                'button[data-qa="buyNowButton"], button:has-text("Acquista")',
                timeout=5000
            )
            
            await acquista_btn.click()
            
            # Accept any terms
            try:
                terms = await self.fansale_page.wait_for_selector(
                    'input[type="checkbox"]:not(:checked)',
                    timeout=2000
                )
                if terms:
                    await terms.click()
            except:
                pass
            
            # Confirm purchase
            confirm_btn = await self.fansale_page.wait_for_selector(
                'button[type="submit"]:has-text("Conferma"), button:has-text("Acquista")',
                timeout=5000
            )
            
            await confirm_btn.click()
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"⚡ Purchase executed in {execution_time:.0f}ms")
            
            # Wait for result
            await self.fansale_page.wait_for_timeout(5000)
            
            # Check if we got to payment page
            if 'payment' in self.fansale_page.url or 'pagamento' in self.fansale_page.url:
                logger.info("✅ SUCCESS! Ticket reserved - complete payment manually")
                self.monitoring = False
            
        except Exception as e:
            logger.error(f"FanSale purchase failed: {e}")
            
    async def _purchase_vivaticket(self, ticket_element):
        """Execute VivaTicket purchase"""
        start_time = time.time()
        
        try:
            # Click ticket
            await ticket_element.click()
            
            # Add to cart
            add_btn = await self.vivaticket_page.wait_for_selector(
                'button:has-text("Aggiungi"), button:has-text("Add")',
                timeout=5000
            )
            
            await add_btn.click()
            
            # Proceed to checkout
            checkout_btn = await self.vivaticket_page.wait_for_selector(
                'button:has-text("Procedi"), button:has-text("Checkout")',
                timeout=5000
            )
            
            await checkout_btn.click()
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"⚡ Purchase executed in {execution_time:.0f}ms")
            
            # Wait for result
            await self.vivaticket_page.wait_for_timeout(5000)
            
            # Check if we got to payment
            if 'payment' in self.vivaticket_page.url or 'pagamento' in self.vivaticket_page.url:
                logger.info("✅ SUCCESS! Ticket reserved - complete payment manually")
                self.monitoring = False
                
        except Exception as e:
            logger.error(f"VivaTicket purchase failed: {e}")
            
    async def run(self):
        """Main run method"""
        try:
            await self.initialize()
            await self.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        finally:
            await self.cleanup()
            
    async def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up...")
        
        if self.browser:
            await self.browser.close()
            
        logger.info("✅ Cleanup complete")


async def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════╗
║              STEALTHMASTER LITE - RESALE EDITION           ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Optimized for:                                           ║
║  • FanSale.it resale tickets                             ║
║  • VivaTicket.com resale tickets                         ║
║                                                            ║
║  Features:                                                ║
║  • Single browser instance (fast & efficient)            ║
║  • 7-minute session rotation                             ║
║  • Lightning-fast purchase (<2 seconds)                  ║
║  • Automatic ticket detection                            ║
║                                                            ║
║  Target: Bruce Springsteen - Milano 2025                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app = StealthMasterLite()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
