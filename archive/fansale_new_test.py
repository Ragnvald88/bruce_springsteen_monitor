#!/usr/bin/env python3
"""
FanSale Bot - PROFESSIONAL COMMAND CENTER EDITION
The definitive bot based on the anonymous, self-cleaning strategy,
now with a professional, real-time terminal interface.
"""

import os
import sys
import time
import random
import logging
import threading
import traceback
from pathlib import Path
import shutil
import json
from datetime import datetime
from typing import Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from dotenv import load_dotenv
load_dotenv()

# --- Professional Terminal UI and Logging ---

class Color:
    """Colors for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Global lock for printing to avoid mixed output
print_lock = threading.Lock()

# Custom logger setup
logger = logging.getLogger('FanSalePRO')
logger.setLevel(logging.INFO)
logger.propagate = False # Prevent double logging

# Remove all handlers if any exist
if logger.hasHandlers():
    logger.handlers.clear()

# Add our custom handler
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(f"{Color.BLUE}%(asctime)s{Color.ENDC} | {Color.CYAN}%(threadName)-12s{Color.ENDC} | %(message)s", datefmt='%H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


class FanSaleProBot:
    """The definitive anonymous, self-cleaning hunter bot with a professional UI."""
    
    def __init__(self):
        self.target_url = "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"
        
        # User Configuration
        self.num_browsers = 1
        self.use_proxy = False
        
        # Core Components
        self.browsers = []
        self.threads = []
        self.purchase_lock = threading.Lock()
        self.ticket_secured = False
        self.shutdown_event = threading.Event()
        
        # Real-time Status Tracking
        self.hunter_statuses = {}
        self.stats = {
            'total_checks': 0,
            'tickets_found': 0,
            'purchase_attempts': 0,
            'session_cleans': 0,
            'start_time': time.time()
        }

    def get_proxy_config(self):
        """Builds proxy configuration."""
        if not self.use_proxy:
            return None
        required_vars = ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'IPROYAL_HOSTNAME', 'IPROYAL_PORT']
        if not all(os.getenv(k) for k in required_vars):
            logger.warning("Proxy credentials not found. Running direct.")
            return None
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        return {'proxy': {'http': f'http://{proxy_auth}@{proxy_server}', 'https': f'https://{proxy_auth}@{proxy_server}'}}

    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Creates a single anonymous browser instance."""
        self.update_status(browser_id, "Setting up...")
        options = uc.ChromeOptions()
        profile_dir = Path("browser_profiles") / f"anonymous_hunter_{browser_id}"
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
        profile_dir.mkdir(parents=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        prefs = {"profile.managed_default_content_settings.images": 2, "profile.managed_default_content_settings.popups": 2}
        options.add_experimental_option("prefs", prefs)
        positions_x = [0, 450, 900, 1350, 1800]
        positions_y = [0, 0, 0, 0, 0]
        x = positions_x[browser_id - 1] if browser_id <= 5 else 0
        y = positions_y[browser_id - 1] if browser_id <= 5 else 0
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=450,350')
        proxy_config = self.get_proxy_config()
        try:
            driver = uc.Chrome(options=options, seleniumwire_options=proxy_config)
            driver.set_page_load_timeout(20)
            self.update_status(browser_id, "Ready")
            return driver
        except Exception as e:
            self.update_status(browser_id, f"{Color.FAIL}CREATE FAILED{Color.ENDC}")
            logger.error(f"Failed to create browser {browser_id}: {e}")
            return None

    def clear_browser_data(self, driver: uc.Chrome):
        """Clears all session data for a fresh start."""
        try:
            driver.get("about:blank")
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
            return True
        except Exception:
            return False

    def hunt_and_buy(self, browser_id: int, driver: uc.Chrome):
        """Core loop for each anonymous browser, with self-cleaning and status updates."""
        threading.current_thread().name = f"Hunter-{browser_id}"
        self.update_status(browser_id, "Navigating...")
        driver.get(self.target_url)
        session_start_time = time.time()
        check_count = 0

        while not self.shutdown_event.is_set():
            try:
                if time.time() - session_start_time > 540: # 9 minutes
                    self.update_status(browser_id, f"{Color.WARNING}Self-Cleaning...{Color.ENDC}")
                    if self.clear_browser_data(driver):
                        self.stats['session_cleans'] += 1
                        driver.get(self.target_url)
                        session_start_time = time.time()
                        self.update_status(browser_id, "Cleaned")
                    else:
                        self.update_status(browser_id, f"{Color.FAIL}Clean Failed{Color.ENDC}")
                        break
                
                check_count += 1
                self.stats['total_checks'] += 1
                self.update_status(browser_id, f"Checking... #{check_count}")
                
                ticket = WebDriverWait(driver, 0.4).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa='ticketToBuy']"))
                )

                self.update_status(browser_id, f"{Color.GREEN}TICKET FOUND!{Color.ENDC}")
                self.stats['tickets_found'] += 1
                
                if self.purchase_lock.acquire(blocking=False):
                    if not self.ticket_secured:
                        self.ticket_secured = True
                        self.stats['purchase_attempts'] += 1
                        self.execute_purchase(browser_id, driver, ticket)
                    else:
                        self.purchase_lock.release()
                
                time.sleep(1)

            except TimeoutException:
                if not self.ticket_secured:
                    self.update_status(browser_id, "Refreshing...")
                    driver.refresh()
                    time.sleep(random.uniform(1.5, 3.5))
                else:
                    break
            except WebDriverException as e:
                if "target window already closed" in str(e).lower():
                    self.update_status(browser_id, f"{Color.FAIL}Closed{Color.ENDC}")
                    break
                self.update_status(browser_id, f"{Color.FAIL}Error...{Color.ENDC}")
                logger.error(f"WebDriver error: {e}")
                time.sleep(5)
                if self.clear_browser_data(driver): driver.get(self.target_url)
            except Exception as e:
                self.update_status(browser_id, f"{Color.FAIL}Error...{Color.ENDC}")
                logger.error(f"Unexpected error: {e}")
                traceback.print_exc()
                time.sleep(5)
        
        self.update_status(browser_id, f"{Color.BLUE}Stopped{Color.ENDC}")

    def execute_purchase(self, browser_id: int, driver: uc.Chrome, ticket_element):
        """The final purchase sequence."""
        self.update_status(browser_id, f"{Color.GREEN}{Color.BOLD}PURCHASING...{Color.ENDC}")
        with print_lock:
            logger.info(f"{Color.GREEN}{Color.BOLD}🔥 TICKET DETECTED! Hunter {browser_id} is attempting purchase...{Color.ENDC}")
        try:
            driver.switch_to.window(driver.current_window_handle)
            driver.execute_script("arguments[0].click();", ticket_element)
            
            # The bot's job is done. Get the user to the checkout page.
            self.update_status(browser_id, f"{Color.GREEN}CLICKED!{Color.ENDC}")
            with print_lock:
                logger.info(f"{Color.GREEN}{Color.BOLD}✅✅✅ PURCHASE INITIATED! PROCEED TO CHECKOUT IN BROWSER #{browser_id} NOW! ✅✅✅{Color.ENDC}")
            self.shutdown_event.set()

        except Exception as e:
            self.update_status(browser_id, f"{Color.FAIL}Purchase Failed{Color.ENDC}")
            logger.error(f"Purchase failed: {e}. Releasing lock.")
            self.ticket_secured = False 
            self.purchase_lock.release()
            driver.get(self.target_url)
            
    def display_live_dashboard(self):
        """Displays a live, updating dashboard of all hunter statuses."""
        while not self.shutdown_event.is_set():
            with print_lock:
                # Move cursor up to overwrite previous dashboard
                sys.stdout.write(f"\033[{self.num_browsers + 5}A")
                sys.stdout.flush()

                print(f"{Color.BOLD} FanSale Command Center{Color.ENDC} {' ' * 50}")
                print(f"================================================================")
                
                for i in range(1, self.num_browsers + 1):
                    status = self.hunter_statuses.get(i, "Initializing...")
                    print(f" {Color.CYAN}Hunter-{i}:{Color.ENDC} {status}{' ' * (40 - len(status))}")
                
                print(f"================================================================")
                elapsed = time.time() - self.stats['start_time']
                rate = (self.stats['total_checks'] / elapsed) if elapsed > 0 else 0
                stats_line = (f" {Color.BOLD}Checks:{Color.ENDC} {self.stats['total_checks']} | "
                              f"{Color.BOLD}Found:{Color.ENDC} {self.stats['tickets_found']} | "
                              f"{Color.BOLD}Rate:{Color.ENDC} {rate:.1f}/sec | "
                              f"{Color.BOLD}Cleans:{Color.ENDC} {self.stats['session_cleans']} | "
                              f"{Color.BOLD}Uptime:{Color.ENDC} {int(elapsed // 60)}m {int(elapsed % 60)}s")
                print(f"{stats_line}{' ' * (65 - len(stats_line))}")
                
            time.sleep(0.5)

    def update_status(self, browser_id, status_text):
        """Thread-safe method to update hunter status."""
        self.hunter_statuses[browser_id] = status_text

    def run(self):
        """Main execution flow."""
        print(f"{Color.BOLD}{Color.GREEN}" + "="*60)
        print("      FANSALE BOT - PROFESSIONAL COMMAND CENTER")
        print("="*60 + f"{Color.ENDC}\n")
        
        while True:
            try:
                num = input(f" {Color.BOLD}🌐 How many anonymous browsers? (1-5): {Color.ENDC}").strip()
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 5: break
                print(f" {Color.FAIL}❌ Please enter a number between 1 and 5.{Color.ENDC}")
            except ValueError:
                print(f" {Color.FAIL}❌ Invalid number.{Color.ENDC}")

        proxy_choice = input(f" {Color.BOLD}🔐 Use proxy for all browsers? (y/n): {Color.ENDC}").strip().lower()
        self.use_proxy = proxy_choice == 'y'
        
        print("\n" + "="*60)
        print(" This bot operates ANONYMOUSLY. No login is required.")
        print(" Each browser will self-clean every 9 minutes to avoid blocks.")
        print("="*60)
        input(f"{Color.BOLD}✋ Press Enter to begin the hunt...{Color.ENDC}")

        try:
            # Clear console and prepare dashboard
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n" * (self.num_browsers + 5))
            
            dashboard_thread = threading.Thread(target=self.display_live_dashboard, daemon=True)
            dashboard_thread.start()

            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if not driver:
                    self.shutdown_event.set()
                    return
                self.browsers.append(driver)

            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(target=self.hunt_and_buy, args=(i + 1, driver))
                thread.start()
                self.threads.append(thread)
            
            # Keep main thread alive until shutdown
            self.shutdown_event.wait()
            
            with print_lock:
                 logger.info("Purchase initiated or shutdown requested. The winning browser will stay open.")
                 logger.info("You have 10 minutes to complete the checkout.")
            time.sleep(600)

        except KeyboardInterrupt:
            with print_lock:
                logger.info("\n🛑 Shutting down...")
        except Exception as e:
            with print_lock:
                logger.error(f"A fatal error occurred: {e}")
                traceback.print_exc()
        finally:
            self.shutdown_event.set()
            with print_lock:
                # Final dashboard update
                self.display_live_dashboard() 
                print("\n")
                logger.info("Cleaning up all browser instances...")
            for driver in self.browsers:
                try: driver.quit()
                except: pass
            logger.info("✅ All browsers closed.")

if __name__ == "__main__":
    bot = FanSaleProBot()
    bot.run()
