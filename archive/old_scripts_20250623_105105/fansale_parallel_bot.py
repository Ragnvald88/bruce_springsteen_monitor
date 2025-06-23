#!/usr/bin/env python3
"""
FanSale Parallel Multi-Browser Bot
4 browsers hunting simultaneously at reduced rates
5th browser always ready for instant purchase
"""

import os
import time
import random
import logging
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
import webbrowser

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | [%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)

class HunterBrowser:
    """Individual hunter browser with own profile"""
    
    def __init__(self, browser_id, refresh_interval_range):
        self.id = browser_id
        self.refresh_interval_range = refresh_interval_range
        self.profile_name = f"hunter_{browser_id}"
        self.driver = None
        self.logger = logging.getLogger(f'Hunter-{browser_id}')
        self.is_running = True
        self.check_count = 0
        self.last_check = time.time()
        
    def setup(self):
        """Setup browser with unique profile"""
        self.logger.info("🌐 Starting...")
        
        options = uc.ChromeOptions()
        
        # Unique profile for each browser
        profile_dir = Path("browser_profiles") / self.profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Position windows in grid
        positions = [(0, 0), (650, 0), (0, 450), (650, 450)]
        x, y = positions[self.id - 1] if self.id <= 4 else (1300, 225)
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=600,400')
        
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(20)
        
    def check_for_tickets(self):
        """Check if tickets are available"""
        try:
            tickets = self.driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
            return len(tickets) > 0
        except:
            return False
    def hunt(self, ticket_queue):
        """Hunt for tickets with reduced frequency"""
        self.logger.info(f"🎯 Hunting with {self.refresh_interval_range[0]}-{self.refresh_interval_range[1]}s intervals")
        
        while self.is_running:
            try:
                self.check_count += 1
                
                # Check for tickets
                if self.check_for_tickets():
                    self.logger.info("🎫 TICKETS FOUND!")
                    ticket_queue.put({
                        'browser_id': self.id,
                        'url': self.driver.current_url,
                        'time': datetime.now()
                    })
                    # Keep checking - don't stop!
                
                # Log progress every 20 checks
                if self.check_count % 20 == 0:
                    self.logger.info(f"✓ {self.check_count} checks completed")
                
                # Refresh page
                self.driver.refresh()
                
                # Random wait within interval range
                wait_time = random.uniform(*self.refresh_interval_range)
                time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"Error: {e}")
                time.sleep(5)
    
    def cleanup(self):
        """Close browser"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

class ParallelFanSaleBot:
    """Coordinates multiple browsers hunting in parallel"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Browser configuration
        self.num_hunters = 4
        self.hunters = []
        self.purchase_browser = None
        
        # Thread management
        self.threads = []
        self.ticket_queue = Queue()
        
        # Calculate refresh intervals for each browser
        # Total target: ~4 refreshes/min across all browsers
        # Each browser: ~1 refresh/min (12-16 seconds)
        self.base_interval = (12, 16)  # seconds
        
        self.logger = logging.getLogger('ParallelBot')
        
    def setup_all_browsers(self):
        """Setup all hunter browsers"""
        self.logger.info("🚀 Setting up parallel browser system...")
        
        # Create hunter browsers with staggered intervals
        for i in range(1, self.num_hunters + 1):
            # Slightly vary intervals to avoid synchronized refreshes
            min_interval = self.base_interval[0] + (i-1) * 1
            max_interval = self.base_interval[1] + (i-1) * 1
            
            browser = HunterBrowser(i, (min_interval, max_interval))
            browser.setup()
            self.hunters.append(browser)
            
        # Setup purchase browser (always ready)
        self.setup_purchase_browser()
        
        self.logger.info(f"✅ {self.num_hunters} hunters + 1 purchase browser ready")
    def setup_purchase_browser(self):
        """Setup dedicated purchase browser"""
        self.logger.info("💳 Setting up purchase browser...")
        
        options = uc.ChromeOptions()
        
        # Purchase browser profile
        profile_dir = Path("browser_profiles") / "purchase_browser"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Position on the right
        options.add_argument('--window-position=1300,225')
        options.add_argument('--window-size=600,400')
        
        self.purchase_browser = uc.Chrome(options=options)
        self.purchase_browser.set_page_load_timeout(20)
        
    def manual_login_all(self):
        """Login to all browsers"""
        # First login to purchase browser
        self.logger.info("🔐 Login to PURCHASE browser first...")
        self.login_single_browser(self.purchase_browser, "PURCHASE")
        
        # Then login to hunters
        for i, hunter in enumerate(self.hunters, 1):
            self.logger.info(f"🔐 Login to Hunter {i}...")
            self.login_single_browser(hunter.driver, f"HUNTER {i}")
            
    def login_single_browser(self, driver, browser_name):
        """Login to a single browser"""
        driver.get("https://www.fansale.it/fansale/login.htm")
        
        print(f"\n{'='*50}")
        print(f"LOGIN REQUIRED - {browser_name} BROWSER")
        print(f"{'='*50}")
        print(f"Email: {self.email}")
        print(f"Password: {'*' * len(self.password)}")
        
        input(f"\n✋ Press Enter after login for {browser_name}...")
        
        # Auto-navigate to listing page after login
        self.logger.info(f"📍 {browser_name}: Navigating to listing...")
        driver.get(self.target_url)
        time.sleep(2)
        
    def monitor_tickets(self):
        """Monitor ticket queue and handle purchases"""
        self.logger.info("👀 Monitoring for tickets...")
        
        tickets_found = set()  # Track found tickets to avoid duplicates
        
        while True:
            try:
                # Check queue (non-blocking)
                if not self.ticket_queue.empty():
                    ticket_info = self.ticket_queue.get()
                    
                    # Avoid duplicate alerts
                    ticket_key = f"{ticket_info['browser_id']}_{ticket_info['time'].minute}"
                    if ticket_key not in tickets_found:
                        tickets_found.add(ticket_key)
                        
                        self.logger.info(f"🚨 TICKETS FOUND by Hunter {ticket_info['browser_id']}!")
                        self.logger.info(f"🔗 URL: {ticket_info['url']}")
                        
                        # Open in purchase browser
                        self.logger.info("💳 Opening in purchase browser...")
                        self.purchase_browser.get(ticket_info['url'])
                        
                        # Try to click ticket
                        try:
                            ticket = WebDriverWait(self.purchase_browser, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='ticketToBuy']"))
                            )
                            ticket.click()
                            
                            # Try buy button
                            buy_button = WebDriverWait(self.purchase_browser, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='buyNowButton']"))
                            )
                            buy_button.click()
                            
                            self.logger.info("✅ TICKET IN CART! Complete purchase manually!")
                            
                            # Also open in default browser for backup
                            webbrowser.open(ticket_info['url'])
                            
                        except TimeoutException:
                            self.logger.warning("⚠️ Couldn't auto-click, complete manually!")
                
                # Clean old entries (older than 2 minutes)
                current_minute = datetime.now().minute
                tickets_found = {k for k in tickets_found if int(k.split('_')[1]) >= current_minute - 2}
                
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                time.sleep(1)
    def start_hunting(self):
        """Start all hunters in parallel threads"""
        self.logger.info("🏁 Starting parallel hunting...")
        
        # Start each hunter in its own thread
        for hunter in self.hunters:
            thread = threading.Thread(
                target=hunter.hunt,
                args=(self.ticket_queue,),
                name=f"Hunter-{hunter.id}"
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            
            # Stagger starts slightly
            time.sleep(3)
        
        self.logger.info(f"✅ All {self.num_hunters} hunters active!")
        
    def display_stats(self):
        """Display hunting statistics"""
        start_time = time.time()
        
        while True:
            try:
                time.sleep(30)  # Update every 30 seconds
                
                elapsed = int(time.time() - start_time)
                total_checks = sum(h.check_count for h in self.hunters)
                avg_rate = total_checks / (elapsed / 60) if elapsed > 0 else 0
                
                print(f"\n📊 STATS | Time: {elapsed//60}m {elapsed%60}s | Total Checks: {total_checks} | Rate: {avg_rate:.1f}/min")
                for h in self.hunters:
                    print(f"   Hunter {h.id}: {h.check_count} checks")
                print()
                
            except Exception as e:
                self.logger.error(f"Stats error: {e}")
                
    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════════════════════════╗
        ║                 FANSALE PARALLEL MULTI-BROWSER BOT               ║
        ╠══════════════════════════════════════════════════════════════════╣
        ║                                                                  ║
        ║  Strategy: 4 browsers hunting in parallel                       ║
        ║                                                                  ║
        ║  • Each browser: ~1 refresh every 12-16 seconds                ║
        ║  • Combined rate: ~4 refreshes/minute                           ║
        ║  • Continuous coverage (no gaps!)                               ║
        ║  • 5th browser always ready for instant purchase               ║
        ║                                                                  ║
        ║  Advantages over sequential:                                    ║
        ║  • 4x better chance of catching brief availability             ║
        ║  • If one gets blocked, others continue                        ║
        ║  • Each browser gets own rate limit allowance                  ║
        ║                                                                  ║
        ║  Note: You'll need to login to 5 browsers                      ║
        ╚══════════════════════════════════════════════════════════════════╝
        """)
        
        try:
            # Setup all browsers
            self.setup_all_browsers()
            
            # Login to all
            self.manual_login_all()
            
            # Start hunting threads
            self.start_hunting()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_tickets)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Start stats thread
            stats_thread = threading.Thread(target=self.display_stats)
            stats_thread.daemon = True
            stats_thread.start()
            
            # Keep main thread alive
            self.logger.info("🎯 Parallel hunting active! Press Ctrl+C to stop.")
            
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Stopping all browsers...")
            
            # Stop all hunters
            for hunter in self.hunters:
                hunter.cleanup()
                
            # Close purchase browser
            if self.purchase_browser:
                self.purchase_browser.quit()
                
            self.logger.info("✅ All browsers closed")
            
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    bot = ParallelFanSaleBot()
    bot.run()