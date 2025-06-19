#!/usr/bin/env python3
"""
Fansale Ticket Monitor - Focused, stable, and effective
"""

import asyncio
import time
import random
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Fix Python 3.12+ compatibility
import sys
if sys.version_info >= (3, 12):
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('fansale_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FansaleMonitor:
    """Focused monitor for Fansale.it ticket detection"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.driver = None
        self.session_start = datetime.now()
        self.tickets_found = 0
        self.last_check = None
        self.blocked_count = 0
        self.cookies_path = Path("data/cookies/fansale_cookies.json")
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)
        
    def create_driver(self) -> uc.Chrome:
        """Create optimized undetected Chrome instance"""
        options = uc.ChromeOptions()
        
        # Essential options only - less is more
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Random realistic window size
        width = random.randint(1366, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Realistic user agent
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        options.add_argument(f'--user-agent={user_agent}')
        
        # Proxy configuration if provided
        if self.config.get('proxy'):
            proxy = self.config['proxy']
            # Create proxy extension
            from src.utils.proxy_auth_extension import create_proxy_auth_extension
            ext_path = create_proxy_auth_extension(
                proxy['username'], 
                proxy['password'],
                proxy['host'], 
                proxy['port']
            )
            options.add_extension(ext_path)
            logger.info(f"Using proxy: {proxy['host']}:{proxy['port']}")
        
        # Create driver with minimal detection surface
        driver = uc.Chrome(options=options, version_main=None)
        
        # Apply minimal stealth patches
        driver.execute_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fix chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Remove automation indicators
            ['__webdriver_evaluate', '__selenium_evaluate', '__webdriver_script_function',
             '__webdriver_script_func', '__webdriver_script_fn', '__fxdriver_evaluate',
             '__driver_unwrapped', '__webdriver_unwrapped', '__driver_evaluate',
             '__selenium_unwrapped', '__fxdriver_unwrapped'].forEach(prop => {
                delete window[prop];
                delete document[prop];
            });
        """)
        
        return driver
    
    def save_cookies(self):
        """Save cookies for session persistence"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_path, 'w') as f:
                json.dump(cookies, f)
            logger.debug(f"Saved {len(cookies)} cookies")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
    
    def load_cookies(self):
        """Load saved cookies"""
        if not self.cookies_path.exists():
            return False
            
        try:
            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)
            
            # Navigate to domain first
            self.driver.get("https://www.fansale.it")
            time.sleep(2)
            
            # Add cookies
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Cookie error: {e}")
            
            logger.info(f"Loaded {len(cookies)} cookies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def handle_cookie_banner(self):
        """Handle cookie consent banner"""
        try:
            # Wait for cookie button
            cookie_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
            )
            cookie_btn.click()
            logger.info("✓ Cookie banner accepted")
            time.sleep(1)
        except TimeoutException:
            logger.debug("No cookie banner found")
        except Exception as e:
            logger.debug(f"Cookie banner error: {e}")
    
    def check_if_blocked(self) -> bool:
        """Check if we're blocked"""
        try:
            page_source = self.driver.page_source.lower()
            blocked_indicators = ['access denied', 'blocked', 'forbidden', '_abck', 'akamai']
            
            for indicator in blocked_indicators:
                if indicator in page_source:
                    self.blocked_count += 1
                    logger.warning(f"⚠️  Blocked detected! ({indicator}) Count: {self.blocked_count}")
                    return True
                    
            # Also check for specific Fansale blocks
            if "edgesuite" in page_source or "akam" in page_source:
                self.blocked_count += 1
                logger.warning(f"⚠️  Akamai block detected! Count: {self.blocked_count}")
                return True
                
        except Exception as e:
            logger.error(f"Error checking block: {e}")
            
        return False
    
    def extract_ticket_info(self, ticket_element) -> Dict:
        """Extract detailed ticket information"""
        info = {
            'title': 'Unknown',
            'price': 'Unknown',
            'quantity': 'Unknown',
            'section': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Extract title
            title_elem = ticket_element.find_element(By.CSS_SELECTOR, ".offer-title, .listing-title")
            info['title'] = title_elem.text.strip()
        except:
            pass
            
        try:
            # Extract price
            price_elem = ticket_element.find_element(By.CSS_SELECTOR, ".offer-price, .price")
            info['price'] = price_elem.text.strip()
        except:
            pass
            
        try:
            # Extract quantity
            qty_elem = ticket_element.find_element(By.CSS_SELECTOR, ".offer-quantity, .quantity")
            info['quantity'] = qty_elem.text.strip()
        except:
            pass
            
        try:
            # Extract section/category
            section_elem = ticket_element.find_element(By.CSS_SELECTOR, ".offer-category, .category")
            info['section'] = section_elem.text.strip()
        except:
            pass
            
        return info
    
    def check_for_tickets(self) -> List[Dict]:
        """Check for available tickets"""
        tickets_found = []
        
        # Multiple selectors for different page layouts
        selectors = [
            ".offer-item",
            ".listing-item", 
            "[class*='offer']",
            ".ticket-item",
            ".event-offer"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        # Check if element is visible and has content
                        if element.is_displayed() and element.text.strip():
                            ticket_info = self.extract_ticket_info(element)
                            tickets_found.append(ticket_info)
                    
                    if tickets_found:
                        break
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
        
        return tickets_found
    
    def notify_tickets_found(self, tickets: List[Dict]):
        """Send notifications when tickets are found"""
        self.tickets_found += len(tickets)
        
        logger.info("=" * 50)
        logger.info(f"🎫 TICKETS FOUND! Total: {len(tickets)}")
        logger.info("=" * 50)
        
        for i, ticket in enumerate(tickets, 1):
            logger.info(f"Ticket {i}:")
            logger.info(f"  Title: {ticket['title']}")
            logger.info(f"  Price: {ticket['price']}")
            logger.info(f"  Quantity: {ticket['quantity']}")
            logger.info(f"  Section: {ticket['section']}")
            logger.info("-" * 30)
        
        # Here you can add email/SMS/Discord notifications
        # For now, just beep
        print('\a')  # System beep
    
    def human_like_behavior(self):
        """Simulate human-like behavior"""
        actions = [
            lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);"),
            lambda: self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);"),
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
            lambda: time.sleep(random.uniform(0.5, 1.5))
        ]
        
        # Execute 1-2 random actions
        for _ in range(random.randint(1, 2)):
            random.choice(actions)()
            time.sleep(random.uniform(0.5, 1.0))
    
    async def monitor(self):
        """Main monitoring loop"""
        logger.info(f"Starting Fansale monitor for: {self.config['url']}")
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # Create driver if needed
                if not self.driver:
                    logger.info("Creating new browser instance...")
                    self.driver = self.create_driver()
                    time.sleep(random.uniform(2, 4))
                
                # Try to load cookies first
                cookies_loaded = self.load_cookies()
                
                # Navigate to target URL
                logger.info(f"Navigating to: {self.config['url']}")
                self.driver.get(self.config['url'])
                time.sleep(random.uniform(3, 5))
                
                # Handle cookie banner if not using saved cookies
                if not cookies_loaded:
                    self.handle_cookie_banner()
                
                # Check if blocked
                if self.check_if_blocked():
                    # Implement exponential backoff
                    wait_time = min(300, 60 * (2 ** self.blocked_count))
                    logger.warning(f"Blocked! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    
                    # Recreate browser after multiple blocks
                    if self.blocked_count >= 3:
                        logger.info("Too many blocks, recreating browser...")
                        self.driver.quit()
                        self.driver = None
                        self.blocked_count = 0
                    continue
                
                # Reset retry count on successful load
                retry_count = 0
                
                # Main monitoring loop
                check_count = 0
                while True:
                    check_count += 1
                    self.last_check = datetime.now()
                    
                    # Check for tickets
                    tickets = self.check_for_tickets()
                    
                    if tickets:
                        self.notify_tickets_found(tickets)
                        # Burst mode - check more frequently
                        interval = random.uniform(5, 10)
                    else:
                        logger.info(f"Check #{check_count}: No tickets found")
                        # Normal interval
                        interval = random.uniform(
                            self.config.get('interval', 30) - 5,
                            self.config.get('interval', 30) + 5
                        )
                    
                    # Save cookies periodically
                    if check_count % 10 == 0:
                        self.save_cookies()
                    
                    # Human-like behavior every few checks
                    if check_count % 3 == 0:
                        self.human_like_behavior()
                    
                    # Wait before next check
                    logger.info(f"Next check in {interval:.0f}s...")
                    time.sleep(interval)
                    
                    # Refresh page
                    self.driver.refresh()
                    time.sleep(random.uniform(2, 4))
                    
            except KeyboardInterrupt:
                logger.info("Stopping monitor...")
                break
                
            except WebDriverException as e:
                retry_count += 1
                logger.error(f"Browser error (attempt {retry_count}/{max_retries}): {e}")
                
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                self.driver = None
                
                if retry_count < max_retries:
                    wait_time = 30 * retry_count
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(10)
        
        # Cleanup
        if self.driver:
            self.driver.quit()
        
        # Final stats
        runtime = datetime.now() - self.session_start
        logger.info("=" * 50)
        logger.info(f"Session ended. Runtime: {runtime}")
        logger.info(f"Total tickets found: {self.tickets_found}")
        logger.info("=" * 50)


def main():
    """Run the Fansale monitor"""
    config = {
        'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
        'interval': 30,
        'proxy': {
            'host': 'geo.iproyal.com',
            'port': '12321',
            'username': 'Doqe2Sm9Yjl1MrZd',
            'password': 'dNbFYaRftANFAJqH'
        }
    }
    
    monitor = FansaleMonitor(config)
    asyncio.run(monitor.monitor())


if __name__ == "__main__":
    main()
