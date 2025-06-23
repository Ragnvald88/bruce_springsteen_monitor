#!/usr/bin/env python3
"""
FanSale Bot - Ultimate Single-File Edition
Optimized for speed, stability, and simplicity
"""

import os
import sys
import time
import random
import logging
import threading
import traceback
import json
import shutil
import winsound  # For Windows alarm
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(threadName)-12s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FanSaleBot')

# Also log to file
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(threadName)-12s | %(message)s'))
logger.addHandler(file_handler)


class FanSaleBot:
    """The definitive FanSale ticket bot - fast, stable, and effective"""
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554")
        
        # Configuration
        self.num_browsers = 1
        self.use_proxy = False
        self.max_tickets = 4  # Maximum tickets to reserve
        
        # Browser management
        self.browsers = []
        self.browser_threads = []
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'no_ticket_found': 0,
            'tickets_found': 0,
            'successful_checkouts': 0,
            'already_reserved': 0,
            'start_time': None
        }
        
        # Login verification
        self.last_login_check = {}
        self.login_check_interval = 300  # 5 minutes
        
    def play_alarm(self, success=True):
        """Play alarm sound when ticket is secured"""
        try:
            if sys.platform == "win32":
                # Windows
                frequency = 1000 if success else 500
                duration = 500
                for _ in range(3):
                    winsound.Beep(frequency, duration)
                    time.sleep(0.1)
            else:
                # Mac/Linux - use system bell
                for _ in range(3):
                    print('\a', end='', flush=True)
                    time.sleep(0.1)
        except:
            logger.info("🔔 ALARM: TICKET IN CHECKOUT!")
    
    def save_stats(self):
        """Save statistics to file"""
        stats_file = Path('stats.json')
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def log_stats(self):
        """Log current statistics"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        minutes = int(elapsed // 60)
        
        logger.info("="*60)
        logger.info(f"📊 STATISTICS - Running for {minutes} minutes")
        logger.info(f"   Total Checks: {self.stats['total_checks']}")
        logger.info(f"   No Tickets Found: {self.stats['no_ticket_found']}")
        logger.info(f"   Tickets Detected: {self.stats['tickets_found']}")
        logger.info(f"   Successful Checkouts: {self.stats['successful_checkouts']}")
        logger.info(f"   Already Reserved: {self.stats['already_reserved']}")
        logger.info(f"   Check Rate: {self.stats['total_checks'] / (elapsed / 60):.1f}/min" if elapsed > 0 else "N/A")
        logger.info("="*60)
        
        self.save_stats()
    
    def get_proxy_config(self):
        """Get proxy configuration with data-saving features"""
        if not self.use_proxy:
            return None
            
        required_vars = ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'IPROYAL_HOSTNAME', 'IPROYAL_PORT']
        if not all(os.getenv(k) for k in required_vars):
            logger.warning("⚠️  Proxy credentials incomplete. Running without proxy.")
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        # Data-saving request interceptor
        def block_resources(request):
            # Block these resource types to save data
            block_patterns = [
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
                'font', '.woff', '.woff2', '.ttf',
                '.css',  # Block CSS when using proxy
                'analytics', 'google-analytics', 'googletagmanager',
                'facebook', 'doubleclick', 'amazon-adsystem',
                'tracking', 'hotjar', 'cloudflare'
            ]
            
            if any(pattern in request.url.lower() for pattern in block_patterns):
                request.abort()
                
        logger.info("🔐 Proxy configured with data-saving mode")
        
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': block_resources,
            'suppress_connection_errors': True
        }
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create a browser with optimal settings"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        options = uc.ChromeOptions()
        
        # Persistent profile
        profile_dir = Path("browser_profiles") / f"browser_{browser_id}"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Essential stealth options (always enabled)
        stealth_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-infobars',
            '--disable-gpu-sandbox',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
        ]
        
        for arg in stealth_args:
            options.add_argument(arg)
        
        # Data saving when using proxy
        if self.use_proxy:
            prefs = {
                "profile.managed_default_content_settings": {
                    "images": 2,  # Block images
                    "plugins": 2,  # Block plugins
                    "popups": 2,  # Block popups
                    "geolocation": 2,  # Block location
                    "notifications": 2,  # Block notifications
                    "media_stream": 2,  # Block media
                }
            }
            options.add_experimental_option("prefs", prefs)
            logger.info(f"  💾 Browser {browser_id}: Data-saving mode enabled")
        
        # Window positioning
        positions = [(0, 0), (420, 0), (840, 0), (0, 350), (420, 350)]
        if browser_id <= len(positions):
            x, y = positions[browser_id - 1]
        else:
            x, y = (0, 0)
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=400,320')
        
        # Create browser
        proxy_config = self.get_proxy_config()
        
        try:
            driver = uc.Chrome(options=options, seleniumwire_options=proxy_config)
            driver.set_page_load_timeout(20)
            
            # Inject stealth JavaScript
            driver.execute_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Console log to verify
                console.log('Stealth mode activated');
            """)
            
            logger.info(f"✅ Browser {browser_id} created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser {browser_id}: {e}")
            return None
    
    def manual_login(self, browser_id: int, driver: uc.Chrome) -> bool:
        """Handle manual login for a browser"""
        logger.info(f"🔐 Manual login required for Browser {browser_id}")
        
        try:
            # Check if already logged in
            driver.get(self.target_url)
            time.sleep(2)
            
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} already logged in!")
                return True
            
            # Need to login
            driver.get("https://www.fansale.it/fansale/login.htm")
            
            print(f"\n{'='*60}")
            print(f"🔐 LOGIN REQUIRED - BROWSER #{browser_id}")
            print(f"{'='*60}")
            print(f"Email: {self.email}")
            print(f"Password: {'*' * len(self.password)}")
            print(f"{'='*60}\n")
            
            input(f"✋ Press Enter after Browser #{browser_id} is logged in...")
            
            # Navigate back to target
            driver.get(self.target_url)
            time.sleep(2)
            
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} logged in successfully!")
                self.last_login_check[browser_id] = time.time()
                return True
            else:
                logger.error(f"❌ Browser {browser_id} login verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error for Browser {browser_id}: {e}")
            return False
    
    def verify_login(self, driver: uc.Chrome) -> bool:
        """Verify if browser is logged in"""
        try:
            # Check for login indicators
            page_source = driver.page_source.lower()
            
            # Logged in indicators
            if any(indicator in page_source for indicator in ['my fansale', 'mio account', 'logout', 'esci']):
                return True
                
            # Not logged in indicators
            if any(indicator in page_source for indicator in ['login', 'accedi', 'registrati']):
                return False
                
            # Default to assuming logged in if on the right page
            return 'fansale.it' in driver.current_url
            
        except:
            return False
    
    def check_login_status(self, browser_id: int, driver: uc.Chrome):
        """Check if re-login is needed (every 5 minutes)"""
        current_time = time.time()
        last_check = self.last_login_check.get(browser_id, 0)
        
        if current_time - last_check > self.login_check_interval:
            if not self.verify_login(driver):
                logger.warning(f"⚠️ Browser {browser_id} logged out! Pausing for re-login...")
                self.manual_login(browser_id, driver)
            else:
                self.last_login_check[browser_id] = current_time
    
    def hunt_and_buy(self, browser_id: int, driver: uc.Chrome):
        """Core hunting loop for each browser"""
        thread_name = f"Hunter-{browser_id}"
        threading.current_thread().name = thread_name
        
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        check_count = 0
        local_tickets_secured = 0
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Periodic login check
                if check_count % 100 == 0:  # Check every ~5 minutes at 20 checks/min
                    self.check_login_status(browser_id, driver)
                
                # Fast ticket detection
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    self.stats['tickets_found'] += 1
                    logger.info(f"🎫 HUNTER {browser_id}: {len(tickets)} TICKETS FOUND!")
                    
                    # Try to buy multiple tickets (up to max)
                    for i, ticket in enumerate(tickets):
                        if self.tickets_secured >= self.max_tickets:
                            break
                            
                        if self.purchase_lock.acquire(blocking=False):
                            try:
                                if self.tickets_secured < self.max_tickets:
                                    success = self.execute_purchase(driver, ticket, browser_id)
                                    if success:
                                        self.tickets_secured += 1
                                        local_tickets_secured += 1
                                        self.stats['successful_checkouts'] += 1
                                        logger.info(f"✅ HUNTER {browser_id}: Secured ticket {self.tickets_secured}/{self.max_tickets}")
                                        
                                        # Play alarm
                                        self.play_alarm()
                                        
                                        # Take screenshot
                                        screenshot_path = f"checkout_{int(time.time())}.png"
                                        driver.save_screenshot(screenshot_path)
                                        logger.info(f"📸 Screenshot saved: {screenshot_path}")
                            finally:
                                self.purchase_lock.release()
                else:
                    self.stats['no_ticket_found'] += 1
                
                # Progress logging
                if check_count % 50 == 0:
                    elapsed = time.time() - self.stats['start_time']
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    logger.info(f"Hunter {browser_id}: {check_count} checks | {rate:.1f}/min | Secured: {local_tickets_secured}")
                
                # Refresh and wait
                driver.refresh()
                
                # Smart wait time based on number of browsers
                if self.num_browsers == 1:
                    wait_time = random.uniform(2.5, 3.5)
                elif self.num_browsers == 2:
                    wait_time = random.uniform(3.5, 4.5)
                elif self.num_browsers == 3:
                    wait_time = random.uniform(4.5, 5.5)
                else:
                    wait_time = random.uniform(5.5, 7.0)
                
                time.sleep(wait_time)
                
            except TimeoutException:
                driver.refresh()
                time.sleep(2)
                
            except WebDriverException as e:
                if "target window already closed" in str(e).lower():
                    logger.warning(f"Hunter {browser_id}: Browser closed")
                    break
                logger.error(f"Hunter {browser_id}: WebDriver error: {e}")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id}: Error: {e}")
                traceback.print_exc()
                time.sleep(5)
        
        logger.info(f"Hunter {browser_id}: Stopped. Secured {local_tickets_secured} tickets.")
    
    def execute_purchase(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Execute the purchase of a ticket"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Bring window to front
            driver.switch_to.window(driver.current_window_handle)
            
            # Click ticket
            driver.execute_script("arguments[0].scrollIntoView(true);", ticket_element)
            driver.execute_script("arguments[0].click();", ticket_element)
            
            # Look for buy button
            buy_button = None
            for selector in ["button[data-qa='buyNowButton']", "button.buy-button", "//button[contains(text(), 'Acquista')]"]:
                try:
                    if selector.startswith('//'):
                        buy_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    break
                except:
                    continue
            
            if buy_button:
                driver.execute_script("arguments[0].click();", buy_button)
                logger.info(f"✅ Hunter {browser_id}: PURCHASE CLICKED! Check browser for checkout.")
                return True
            else:
                # Check if ticket was already reserved
                page_text = driver.page_source.lower()
                if any(term in page_text for term in ['già riservato', 'already reserved', 'non disponibile']):
                    self.stats['already_reserved'] += 1
                    logger.warning(f"⚠️ Hunter {browser_id}: Ticket already reserved by someone else")
                else:
                    logger.error(f"❌ Hunter {browser_id}: Buy button not found")
                return False
                
        except Exception as e:
            logger.error(f"Purchase failed for Hunter {browser_id}: {e}")
            return False
    
    def clear_browser_profiles(self):
        """Clear all browser profiles"""
        profiles_dir = Path("browser_profiles")
        if profiles_dir.exists():
            try:
                shutil.rmtree(profiles_dir)
                logger.info("✅ All browser profiles cleared")
                print("\n✅ Browser profiles cleared successfully!\n")
            except Exception as e:
                logger.error(f"Failed to clear profiles: {e}")
                print(f"\n❌ Error clearing profiles: {e}\n")
        else:
            print("\n📁 No browser profiles found to clear.\n")
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("🎫 FANSALE BOT - ULTIMATE EDITION")
        print("="*60)
        print("\n1. Start Bot")
        print("2. Clear Browser Profiles")
        print("3. Show Statistics")
        print("4. Exit")
        print("\nEnter your choice (1-4): ", end='')
    
    def handle_statistics(self):
        """Show statistics from previous runs"""
        stats_file = Path('stats.json')
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                print("\n📊 SAVED STATISTICS:")
                print(f"   Total Checks: {saved_stats.get('total_checks', 0)}")
                print(f"   No Tickets: {saved_stats.get('no_ticket_found', 0)}")
                print(f"   Tickets Found: {saved_stats.get('tickets_found', 0)}")
                print(f"   Successful Checkouts: {saved_stats.get('successful_checkouts', 0)}")
                print(f"   Already Reserved: {saved_stats.get('already_reserved', 0)}")
            except:
                print("\n❌ Error reading statistics")
        else:
            print("\n📊 No statistics found yet. Run the bot first!")
        
        input("\nPress Enter to continue...")
    
    def run_bot(self):
        """Main bot execution"""
        print("\n🔧 BOT CONFIGURATION")
        print("="*40)
        
        # Get number of browsers
        while True:
            try:
                num = input("\n🌐 Number of browsers (1-5, recommended 2-3): ").strip()
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 5:
                    break
                print("❌ Please enter 1-5")
            except ValueError:
                print("❌ Invalid number")
        
        # Proxy option
        proxy_choice = input("\n🔐 Use proxy? (y/n, default n): ").strip().lower()
        self.use_proxy = proxy_choice == 'y'
        
        # Calculate expected performance
        if self.num_browsers == 1:
            checks_per_min = 20
        elif self.num_browsers == 2:
            checks_per_min = 30
        elif self.num_browsers == 3:
            checks_per_min = 35
        else:
            checks_per_min = 40
            
        print(f"\n📋 CONFIGURATION:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Proxy: {'✅ Yes (data-saving)' if self.use_proxy else '❌ No'}")
        print(f"   • Expected rate: ~{checks_per_min} checks/minute")
        print(f"   • Max tickets: {self.max_tickets}")
        print(f"   • Target: {self.target_url}")
        
        try:
            # Create browsers
            print(f"\n🚀 Starting {self.num_browsers} browsers...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if not driver:
                    logger.error(f"Failed to create browser {i}")
                    continue
                    
                # Manual login
                if not self.manual_login(i, driver):
                    logger.error(f"Failed to login browser {i}")
                    driver.quit()
                    continue
                    
                self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created successfully")
                return
                
            logger.info(f"✅ {len(self.browsers)} browsers ready!")
            input("\n✋ Press Enter to START HUNTING...")
            
            # Start statistics
            self.stats['start_time'] = time.time()
            
            # Start hunter threads
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_and_buy,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                self.browser_threads.append(thread)
            
            # Start stats display thread
            def periodic_stats():
                while not self.shutdown_event.is_set():
                    time.sleep(60)  # Every minute
                    self.log_stats()
            
            stats_thread = threading.Thread(target=periodic_stats, daemon=True)
            stats_thread.start()
            
            logger.info("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            # Wait for completion or interrupt
            while self.tickets_secured < self.max_tickets and not self.shutdown_event.is_set():
                time.sleep(1)
                
            if self.tickets_secured >= self.max_tickets:
                logger.info(f"\n🎉 SUCCESS! All {self.max_tickets} tickets secured!")
                self.play_alarm()
                input("\nPress Enter to close browsers and exit...")
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested...")
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
            
        finally:
            # Final stats
            self.log_stats()
            
            # Cleanup
            self.shutdown_event.set()
            logger.info("🧹 Cleaning up...")
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
                    
            logger.info("✅ Shutdown complete")
    
    def run(self):
        """Main entry point with menu"""
        while True:
            self.show_menu()
            
            choice = input().strip()
            
            if choice == '1':
                self.run_bot()
            elif choice == '2':
                self.clear_browser_profiles()
            elif choice == '3':
                self.handle_statistics()
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")


def main():
    """Entry point"""
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install undetected-chromedriver selenium-wire python-dotenv")
        sys.exit(1)
    
    # Check credentials
    load_dotenv()
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        print("❌ Missing credentials!")
        print("\nCreate a .env file with:")
        print("FANSALE_EMAIL=your@email.com")
        print("FANSALE_PASSWORD=yourpassword")
        print("FANSALE_TARGET_URL=https://www.fansale.it/...")
        sys.exit(1)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()
