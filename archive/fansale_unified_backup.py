#!/usr/bin/env python3
"""
FanSale Bot - Unified Edition
Single script with all options: browser count, proxy, auto-timing
"""

import os
import sys
import time
import random
import logging
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
import shutil

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from dotenv import load_dotenv
load_dotenv()

# Configure logging with clean format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FanSaleBot')


class FanSaleBot:
    """Unified bot with dynamic browser count and smart timing"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Configuration (set by user)
        self.num_browsers = 1
        self.use_proxy = False
        self.use_lite_mode = False
        
        # Browser management
        self.hunters = []
        self.purchase_browser = None
        self.ticket_queue = Queue()
        self.threads = []
        
        # Stats
        self.start_time = None
        self.total_checks = 0
        
    def calculate_refresh_timing(self):
        """Calculate optimal refresh timing based on browser count"""
        # Target: ~3-4 total refreshes per minute to stay safe
        if self.num_browsers == 1:
            return (15, 20)  # Single browser: conservative
        elif self.num_browsers <= 3:
            return (20, 30)  # 2-3 browsers: moderate
        elif self.num_browsers <= 5:
            return (30, 45)  # 4-5 browsers: distributed
        else:
            return (45, 60)  # 6+ browsers: very distributed
            
    def get_proxy_config(self):
        """Get proxy configuration if enabled"""
        if not self.use_proxy:
            return None
            
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            logger.warning("⚠️  Proxy credentials not found in .env")
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            }
        }
    def setup_purchase_browser(self):
        """Setup persistent purchase browser (always logged in)"""
        logger.info("💳 Setting up purchase browser...")
        
        options = uc.ChromeOptions()
        
        # Persistent profile for purchase browser
        profile_dir = Path("browser_profiles") / "purchase_browser"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Standard options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Position on the right
        options.add_argument('--window-position=1200,100')
        options.add_argument('--window-size=700,800')
        
        # Apply lite mode if requested
        if self.use_lite_mode:
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
            }
            options.add_experimental_option("prefs", prefs)
        
        # Proxy
        proxy_config = self.get_proxy_config()
        
        self.purchase_browser = uc.Chrome(options=options, seleniumwire_options=proxy_config)
        self.purchase_browser.set_page_load_timeout(20)
        
        # Login to purchase browser
        logger.info("🔐 Please login to the PURCHASE browser")
        self.purchase_browser.get("https://www.fansale.it/fansale/login.htm")
        
        print("\n" + "="*60)
        print("LOGIN TO PURCHASE BROWSER (This stays logged in)")
        print("="*60)
        print(f"Email: {self.email}")
        print(f"Password: {'*' * len(self.password)}")
        print("\n⚠️  This browser will stay open for instant ticket purchase")
        
        input("\n✋ Press Enter after successful login...")
        
        # Navigate to listing page
        self.purchase_browser.get(self.target_url)
        logger.info("✅ Purchase browser ready!")
        
    def create_hunter_browser(self, browser_id):
        """Create a single hunter browser"""
        options = uc.ChromeOptions()
        
        # Unique profile
        profile_dir = Path("browser_profiles") / f"hunter_{browser_id}"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Standard options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Calculate position (grid layout)
        positions_x = [0, 400, 800, 0, 400, 800, 0, 400, 800, 1200]
        positions_y = [0, 0, 0, 300, 300, 300, 600, 600, 600, 400]
        
        x = positions_x[browser_id - 1] if browser_id <= 10 else 0
        y = positions_y[browser_id - 1] if browser_id <= 10 else 0
        
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=350,250')  # Smaller windows
        
        # Apply lite mode if requested
        if self.use_lite_mode:
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_settings.fonts": 2,
            }
            options.add_experimental_option("prefs", prefs)
            logger.info(f"  Hunter {browser_id}: Lite mode enabled (no images/CSS)")
        
        # Proxy
        proxy_config = self.get_proxy_config()
        
        driver = uc.Chrome(options=options, seleniumwire_options=proxy_config)
        driver.set_page_load_timeout(20)
        
        return driver
    def hunt_tickets(self, browser_id, driver, refresh_range):
        """Hunt for tickets in a specific browser"""
        logger.info(f"🔍 Hunter {browser_id}: Starting ({refresh_range[0]}-{refresh_range[1]}s intervals)")
        
        # Navigate to target
        driver.get(self.target_url)
        time.sleep(2)
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                self.total_checks += 1
                
                # Check for tickets
                if self.use_lite_mode:
                    # Lite mode: check in page source
                    page_source = driver.page_source.lower()
                    has_tickets = 'data-qa="tickettobuy"' in page_source
                else:
                    # Normal mode: check elements
                    tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                    has_tickets = len(tickets) > 0
                
                if has_tickets:
                    logger.info(f"🎫 Hunter {browser_id}: TICKETS FOUND!")
                    self.ticket_queue.put({
                        'browser_id': browser_id,
                        'url': driver.current_url,
                        'time': datetime.now()
                    })
                
                # Progress update
                if check_count % 20 == 0:
                    logger.info(f"   Hunter {browser_id}: {check_count} checks")
                
                # Refresh
                driver.refresh()
                
                # Smart wait
                wait_time = random.uniform(*refresh_range)
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                time.sleep(5)
                
    def handle_found_tickets(self):
        """Monitor queue and handle ticket purchases"""
        seen_tickets = set()
        
        while True:
            try:
                if not self.ticket_queue.empty():
                    ticket_info = self.ticket_queue.get()
                    
                    # Avoid duplicates
                    ticket_key = f"{ticket_info['time'].minute}"
                    if ticket_key not in seen_tickets:
                        seen_tickets.add(ticket_key)
                        
                        logger.info("🚨 OPENING IN PURCHASE BROWSER!")
                        
                        # Navigate purchase browser to ticket URL
                        self.purchase_browser.get(ticket_info['url'])
                        
                        try:
                            # Try to auto-click ticket
                            ticket = WebDriverWait(self.purchase_browser, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='ticketToBuy']"))
                            )
                            ticket.click()
                            
                            # Try buy button
                            buy_button = WebDriverWait(self.purchase_browser, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='buyNowButton']"))
                            )
                            buy_button.click()
                            
                            logger.info("✅ TICKET IN CART! Complete checkout!")
                            
                            # Take screenshot
                            self.purchase_browser.save_screenshot(f"ticket_{int(time.time())}.png")
                            
                        except TimeoutException:
                            logger.warning("⚠️  Couldn't auto-click - complete manually!")
                
                # Clean old entries
                current_minute = datetime.now().minute
                seen_tickets = {k for k in seen_tickets if int(k) >= current_minute - 2}
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ticket handler error: {e}")
                time.sleep(1)
    def display_stats(self):
        """Display running statistics"""
        while True:
            try:
                time.sleep(30)
                
                if self.start_time:
                    elapsed = int(time.time() - self.start_time)
                    rate = self.total_checks / (elapsed / 60) if elapsed > 0 else 0
                    
                    logger.info(f"📊 Stats: {elapsed//60}m {elapsed%60}s | Checks: {self.total_checks} | Rate: {rate:.1f}/min")
                    
            except Exception:
                pass
                
    def run(self):
        """Main execution"""
        # Get user configuration
        print("\n" + "="*60)
        print("FANSALE BOT - UNIFIED EDITION")
        print("="*60)
        
        # Browser count
        while True:
            try:
                num = input("\n🌐 How many hunter browsers? (1-10, recommended 3-5): ").strip()
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 10:
                    break
                print("❌ Please enter a number between 1 and 10")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Proxy option
        proxy_choice = input("\n🔐 Use proxy? (y/n, default: n): ").strip().lower()
        self.use_proxy = proxy_choice == 'y'
        
        # Lite mode option (for data saving)
        if self.use_proxy:
            lite_choice = input("\n💾 Use lite mode to save data? (y/n, default: n): ").strip().lower()
            self.use_lite_mode = lite_choice == 'y'
        
        # Calculate timing
        refresh_range = self.calculate_refresh_timing()
        total_rate = self.num_browsers * (60 / ((refresh_range[0] + refresh_range[1]) / 2))
        
        print(f"\n📊 Configuration:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Refresh: {refresh_range[0]}-{refresh_range[1]}s per browser")
        print(f"   • Total rate: ~{total_rate:.1f} checks/minute")
        print(f"   • Proxy: {'Yes' if self.use_proxy else 'No'}")
        print(f"   • Lite mode: {'Yes' if self.use_lite_mode else 'No'}")
        
        try:
            # Setup purchase browser first
            self.setup_purchase_browser()
            
            # Create hunter browsers
            logger.info(f"\n🚀 Starting {self.num_browsers} hunter browsers...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_hunter_browser(i)
                self.hunters.append(driver)
                
                # Start hunting thread
                thread = threading.Thread(
                    target=self.hunt_tickets,
                    args=(i, driver, refresh_range),
                    daemon=True
                )
                thread.start()
                self.threads.append(thread)
                
                # Stagger starts
                time.sleep(2)
            
            logger.info(f"✅ All {self.num_browsers} hunters active!")
            
            # Start monitoring threads
            monitor_thread = threading.Thread(target=self.handle_found_tickets, daemon=True)
            monitor_thread.start()
            
            stats_thread = threading.Thread(target=self.display_stats, daemon=True)
            stats_thread.start()
            
            self.start_time = time.time()
            
            # Keep running
            logger.info("\n🎯 Hunting active! Press Ctrl+C to stop.\n")
            
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
            
            # Close all browsers
            for driver in self.hunters:
                try:
                    driver.quit()
                except:
                    pass
                    
            if self.purchase_browser:
                try:
                    self.purchase_browser.quit()
                except:
                    pass
                    
            logger.info("✅ All browsers closed")
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()