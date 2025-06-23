#!/usr/bin/env python3
"""
FanSale Bot - Stealth Edition v3.0
Optimized for speed, stealth, and reliability
Fixed all syntax errors and improved detection avoidance
"""

import os
import sys
import time
import random
import logging
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Suppress verbose logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
logger.handlers = [handler]


class FanSaleBot:
    """Streamlined FanSale bot with focus on speed and stealth"""
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
        
        # Configuration
        self.num_browsers = 1
        self.use_proxy = False
        self.max_tickets = 4
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.tickets_secured = 0
        self.stats = {
            'checks': 0,
            'tickets_found': 0,
            'purchases': 0,
            'start_time': None
        }

    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser instance"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        options = uc.ChromeOptions()
        
        # Stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-infobars')
        
        # Performance
        options.add_argument('--disable-logging')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Window size and position
        positions = [(0, 0), (450, 0), (900, 0)]
        x, y = positions[browser_id - 1] if browser_id <= 3 else (0, 0)
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=450,700')
        
        # Profile persistence
        profile_dir = Path("browser_profiles") / f"browser_{browser_id}"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        try:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(20)
            
            # Inject stealth JavaScript
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                console.log('Stealth mode active');
            """)
            
            logger.info(f"✅ Browser {browser_id} ready")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser: {e}")
            return None

    def verify_login(self, driver: uc.Chrome) -> bool:
        """Check if browser is logged in - FIXED METHOD"""
        try:
            page_source = driver.page_source.lower()
            
            # Check for logged-in indicators
            logged_in_indicators = ['my fansale', 'mio account', 'logout', 'esci', 'il mio fansale']
            if any(indicator in page_source for indicator in logged_in_indicators):
                return True
            
            # Check for login page indicators
            login_indicators = ['login', 'accedi', 'registrati', 'password']
            if any(indicator in page_source for indicator in login_indicators):
                # Make sure we're not just seeing a login link in header
                if 'ticket' not in driver.current_url and 'login' in driver.current_url:
                    return False
                    
            # If we're on the ticket page and no clear login indicators, assume logged in
            return 'tickets' in driver.current_url
            
        except Exception as e:
            logger.debug(f"Login check error: {e}")
            return False
    
    def manual_login(self, browser_id: int, driver: uc.Chrome) -> bool:
        """Handle manual login process"""
        logger.info(f"🔐 Checking login status for Browser {browser_id}...")
        
        try:
            # Navigate to target page first
            driver.get(self.target_url)
            time.sleep(3)
            
            # Check if already logged in - FIXED: Added 'if self.'
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} already logged in!")
                return True
            
            # Need to login
            logger.info(f"📝 Login required for Browser {browser_id}")
            driver.get("https://www.fansale.it/fansale/login.htm")
            
            print(f"\n{'='*60}")
            print(f"🔐 MANUAL LOGIN REQUIRED - Browser #{browser_id}")
            print(f"{'='*60}")
            print(f"Please log in manually in the browser window")
            print(f"Email: {self.email}")
            print(f"{'='*60}\n")
            
            input(f"✋ Press Enter after you've logged in...")
            
            # Navigate back and verify
            driver.get(self.target_url)
            time.sleep(3)
            
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} logged in successfully!")
                return True
            else:
                logger.error(f"❌ Browser {browser_id} login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop - optimized for speed"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        check_count = 0
        last_refresh = time.time()
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['checks'] += 1
                
                # Periodic login check every 5 minutes
                if check_count % 100 == 0:
                    if not self.verify_login(driver):
                        logger.warning(f"⚠️ Hunter {browser_id}: Re-login needed")
                        if not self.manual_login(browser_id, driver):
                            break
                
                # Quick ticket check
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    self.stats['tickets_found'] += 1
                    logger.info(f"🎫 HUNTER {browser_id}: {len(tickets)} TICKETS FOUND!")
                    
                    for ticket in tickets[:self.max_tickets - self.tickets_secured]:
                        if self.purchase_ticket(driver, ticket, browser_id):
                            self.tickets_secured += 1
                            self.stats['purchases'] += 1
                            
                            if self.tickets_secured >= self.max_tickets:
                                logger.info(f"🎉 Max tickets secured!")
                                return
                
                # Smart refresh with jitter
                refresh_time = random.uniform(2.5, 3.5)
                
                # Full page refresh every 30 seconds to avoid stale elements
                if time.time() - last_refresh > 30:
                    driver.refresh()
                    last_refresh = time.time()
                else:
                    # Just wait and re-check
                    time.sleep(refresh_time)
                
                # Log progress
                if check_count % 50 == 0:
                    rate = (check_count * 60) / (time.time() - self.stats['start_time'])
                    logger.info(f"Hunter {browser_id}: {check_count} checks @ {rate:.1f}/min")
                    
            except TimeoutException:
                driver.refresh()
                time.sleep(2)
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    logger.error(f"Hunter {browser_id}: Session died")
                    break
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                time.sleep(5)

    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click ticket
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            driver.execute_script("arguments[0].click();", ticket_element)
            time.sleep(1)
            
            # Find and click buy button
            buy_selectors = [
                "button[data-qa='buyNowButton']",
                "button[class*='buy']",
                "button[class*='acquista']",
                "//button[contains(text(), 'Acquista')]",
                "//button[contains(text(), 'Buy')]"
            ]
            
            for selector in buy_selectors:
                try:
                    if selector.startswith('//'):
                        buy_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    driver.execute_script("arguments[0].click();", buy_btn)
                    logger.info(f"✅ Hunter {browser_id}: Buy button clicked!")
                    
                    # Play alarm
                    print('\a' * 3)  # System beep
                    
                    # Take screenshot
                    driver.save_screenshot(f"ticket_{int(time.time())}.png")
                    
                    return True
                    
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.debug(f"Purchase failed: {e}")
            return False

    def configure(self):
        """Configure bot settings"""
        print("\n🔧 BOT CONFIGURATION")
        print("="*40)
        
        # Number of browsers
        while True:
            try:
                num = input("\n🌐 Number of browsers (1-3, default 1): ").strip()
                if not num:
                    self.num_browsers = 1
                    break
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 3:
                    break
                print("❌ Please enter 1-3")
            except ValueError:
                print("❌ Invalid number")
        
        # Proxy
        proxy = input("\n🔐 Use proxy? (y/n, default n): ").strip().lower()
        self.use_proxy = proxy == 'y'
        
        # Max tickets
        try:
            max_t = input("\n🎫 Max tickets to buy (1-4, default 4): ").strip()
            if max_t:
                self.max_tickets = min(4, max(1, int(max_t)))
        except:
            pass
        
        print(f"\n📋 Configuration:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Proxy: {'Yes' if self.use_proxy else 'No'}")
        print(f"   • Max tickets: {self.max_tickets}")
        print(f"   • Target: {self.target_url}")
    
    def run(self):
        """Main execution"""
        try:
            # Configure
            self.configure()
            
            # Create browsers
            print(f"\n🚀 Starting {self.num_browsers} browsers...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if not driver:
                    continue
                    
                if not self.manual_login(i, driver):
                    driver.quit()
                    continue
                    
                self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created")
                return

            logger.info(f"✅ {len(self.browsers)} browsers ready!")
            input("\n✋ Press Enter to START HUNTING...")
            
            # Start hunting
            self.stats['start_time'] = time.time()
            threads = []
            
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_tickets,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
            
            # Monitor progress
            print("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            try:
                while self.tickets_secured < self.max_tickets:
                    time.sleep(1)
                    
                logger.info(f"\n🎉 SUCCESS! {self.tickets_secured} tickets secured!")
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping...")
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            
        finally:
            # Cleanup
            self.shutdown_event.set()
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
                    
            # Show stats
            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                print(f"\n📊 Final Statistics:")
                print(f"   • Total checks: {self.stats['checks']}")
                print(f"   • Tickets found: {self.stats['tickets_found']}")
                print(f"   • Purchases: {self.stats['purchases']}")
                print(f"   • Runtime: {elapsed/60:.1f} minutes")
                print(f"   • Check rate: {self.stats['checks']/(elapsed/60):.1f}/min")


def main():
    """Entry point"""
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium")
        sys.exit(1)
    
    # Check credentials
    load_dotenv()
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        print("❌ Missing credentials in .env file!")
        sys.exit(1)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()
