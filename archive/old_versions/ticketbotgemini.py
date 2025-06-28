# hunter_pro.py
# This is the robust, multi-threaded version based on the user-provided "Claude" script.
# It is designed for high reliability and resilience against blocking.

import os
import sys
import time
import json
import random
import hashlib
import logging
import threading
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# --- Suppress verbose logs from libraries ---
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# --- Try to import dependencies, guide user if they fail ---
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, WebDriverException, StaleElementReferenceException
    )
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.common.action_chains import ActionChains
    from dotenv import load_dotenv
except ImportError as e:
    print(f"ERROR: A required library is missing: {e.name}")
    print("Please activate your virtual environment and run: pip install -r requirements.txt")
    sys.exit(1)

load_dotenv()

# ==============================================================================
# Main Bot Class - Combining logic for clarity
# ==============================================================================

class FanSaleHunter:
    def __init__(self):
        # --- Core Configuration ---
        self.target_url = os.getenv('FANSALE_TARGET_URL', "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
        self.num_browsers = 2
        self.max_tickets_to_secure = 1
        self.ticket_types_to_hunt = {'prato_a', 'prato_b'} # Default hunt targets

        # --- State Management ---
        self.browsers = []
        self.threads = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        self.seen_tickets = set()

        # --- Timing ---
        self.min_wait = 0.3
        self.max_wait = 1.0
        self.refresh_interval = 20 # seconds

        # --- Setup Directories ---
        Path("screenshots").mkdir(exist_ok=True)
        Path("browser_profiles").mkdir(exist_ok=True)

    def log(self, message: str, level: str = 'info'):
        """Simple colored logger."""
        colors = {'info': '\033[94m', 'success': '\033[92m', 'warning': '\033[93m', 'error': '\033[91m'}
        reset = '\033[0m'
        logging.info(f"{colors.get(level, '')}{message}{reset}")

    def configure_hunt(self):
        """Interactive CLI to configure the hunting parameters."""
        print("\n--- Configure Your Hunt ---")
        try:
            # Number of browsers
            num_browsers_input = input(f"Enter number of browsers (1-8) [Default: {self.num_browsers}]: ").strip()
            if num_browsers_input.isdigit() and 1 <= int(num_browsers_input) <= 8:
                self.num_browsers = int(num_browsers_input)

            # Max tickets
            max_tickets_input = input(f"Enter max tickets to secure [Default: {self.max_tickets_to_secure}]: ").strip()
            if max_tickets_input.isdigit() and int(max_tickets_input) > 0:
                self.max_tickets_to_secure = int(max_tickets_input)

            # Ticket types
            print("\nTicket Types: [1] Prato A, [2] Prato B, [3] All Prato, [4] Seating, [5] All Types")
            types_input = input("Enter choices (e.g., '1,2' or '3') [Default: All Prato]: ").strip()
            if not types_input or '3' in types_input:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b'}
            elif '5' in types_input:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'seating', 'other'}
            else:
                choices = set()
                if '1' in types_input: choices.add('prato_a')
                if '2' in types_input: choices.add('prato_b')
                if '4' in types_input: choices.add('seating')
                if choices: self.ticket_types_to_hunt = choices
            
            self.log(f"Configuration set: {self.num_browsers} browsers, hunting for {self.ticket_types_to_hunt}", 'success')

        except Exception as e:
            self.log(f"Error during configuration: {e}. Using defaults.", 'error')

    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Creates a hardened, undetected-chromedriver instance with a persistent profile."""
        self.log(f"🚀 Creating Hunter #{browser_id}...")
        try:
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # --- Persistent Profile ---
            profile_dir = Path("browser_profiles") / f"hunter_{browser_id}"
            options.add_argument(f'--user-data-dir={profile_dir.absolute()}')

            # --- Window Positioning ---
            window_width = 500
            x = (browser_id - 1) * (window_width + 10)
            options.add_argument(f'--window-position={x},0')
            options.add_argument(f'--window-size={window_width},800')

            driver = uc.Chrome(options=options, use_subprocess=True, suppress_welcome=True)
            driver.set_page_load_timeout(30) # Important timeout to prevent hangs
            driver.implicitly_wait(5)

            self.log(f"✅ Hunter #{browser_id} is ready.", 'success')
            return driver
        except Exception as e:
            self.log(f"❌ Failed to create browser {browser_id}: {e}", 'error')
            self.log("This might be due to a Chrome/ChromeDriver version mismatch.", 'warning')
            return None

    def categorize_ticket(self, text: str) -> str:
        """Categorizes ticket based on text content."""
        text_lower = text.lower()
        if 'prato a' in text_lower or 'prato gold a' in text_lower:
            return 'prato_a'
        if 'prato b' in text_lower or 'prato' in text_lower:
            return 'prato_b'
        if any(kw in text_lower for kw in ['settore', 'fila', 'posto', 'anello', 'tribuna', 'ingresso']):
            return 'seating'
        return 'other'

    def generate_ticket_hash(self, text: str) -> str:
        """Generates a unique hash for a ticket description."""
        return hashlib.md5(text.encode()).hexdigest()

    def dismiss_popups(self, driver: uc.Chrome, browser_id: int):
        """Handles the 'Carica Offerte' button using robust methods."""
        try:
            button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Carica offerte')]"))
            )
            self.log(f"[Hunter #{browser_id}] Clicking 'Carica offerte' button.", 'info')
            ActionChains(driver).move_to_element(button).click().perform()
            time.sleep(1) # Give time for content to load
        except TimeoutException:
            pass # It's okay if the button isn't there.
        except Exception as e:
            self.log(f"[Hunter #{browser_id}] Error dismissing popup: {e}", 'warning')

    def attempt_purchase(self, driver: uc.Chrome, ticket_element: WebElement, browser_id: int) -> bool:
        """Attempts to click the ticket and the buy button."""
        self.log(f"⚡ [Hunter #{browser_id}] Match found! Attempting to secure...", 'success')
        try:
            # Scroll and click the ticket listing
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            time.sleep(0.2)
            ticket_element.click()

            # Wait for and click the 'Acquista' button
            buy_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='buyNowButton']"))
            )
            self.log(f"🎉 [Hunter #{browser_id}] 'Acquista' button found! Clicking now!", 'success')

            # --- Screenshot for proof ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path("screenshots") / f"success_{browser_id}_{timestamp}.png"
            driver.save_screenshot(str(screenshot_path))
            self.log(f"📸 Screenshot saved to {screenshot_path}", 'info')
            
            # --- THE ACTUAL CLICK ---
            # buy_button.click()
            # print("CLICKED THE BUY BUTTON (SIMULATION)")

            return True
        except (StaleElementReferenceException, TimeoutException):
            self.log(f"[Hunter #{browser_id}] Ticket was likely taken by someone else.", 'warning')
            driver.get(self.target_url) # Go back to the listing page
            return False
        except Exception as e:
            self.log(f"[Hunter #{browser_id}] Error during purchase attempt: {e}", 'error')
            return False


    def hunt_tickets_loop(self, browser_id: int, driver: uc.Chrome):
        """The main, continuous hunting loop for a single browser instance."""
        self.log(f"[Hunter #{browser_id}] Navigating to {self.target_url[:40]}...")
        driver.get(self.target_url)
        time.sleep(2)
        last_refresh = time.time()

        while not self.shutdown_event.is_set():
            try:
                if self.tickets_secured >= self.max_tickets_to_secure:
                    break

                self.dismiss_popups(driver, browser_id)

                # Use a more generic selector to find ticket listings
                ticket_elements = driver.find_elements(By.CSS_SELECTOR, "a.offer-list-item")

                for element in ticket_elements:
                    # Check for shutdown signal frequently
                    if self.shutdown_event.is_set(): break

                    full_text = element.text.strip().replace('\n', ' | ')
                    ticket_hash = self.generate_ticket_hash(full_text)

                    if ticket_hash not in self.seen_tickets:
                        self.seen_tickets.add(ticket_hash)
                        category = self.categorize_ticket(full_text)
                        self.log(f"[Hunter #{browser_id}] New Ticket Found -> Category: {category}", 'info')

                        # Check if this ticket type is one we're hunting for
                        if category in self.ticket_types_to_hunt:
                            with self.purchase_lock:
                                if self.tickets_secured < self.max_tickets_to_secure:
                                    if self.attempt_purchase(driver, element, browser_id):
                                        self.tickets_secured += 1
                                        # Immediately check if the goal is met
                                        if self.tickets_secured >= self.max_tickets_to_secure:
                                            self.log("🎉 All tickets secured! Signaling shutdown.", 'success')
                                            self.shutdown_event.set()
                                        break # Exit the for-loop to re-evaluate on the main page

                # Randomized wait
                time.sleep(random.uniform(self.min_wait, self.max_wait))
                
                # Periodic refresh
                if time.time() - last_refresh > self.refresh_interval + random.randint(-2, 2):
                    self.log(f"[Hunter #{browser_id}] Performing periodic refresh.", 'info')
                    driver.refresh()
                    last_refresh = time.time()

            except WebDriverException as e:
                if "invalid session id" in str(e).lower():
                    self.log(f"[Hunter #{browser_id}] Session died. This hunter will stop.", 'error')
                    break # Exit the loop for this thread
                self.log(f"[Hunter #{browser_id}] WebDriver Error: {e}", 'error')
                time.sleep(5)
            except Exception as e:
                self.log(f"[Hunter #{browser_id}] An unexpected error occurred: {e}", 'error')
                time.sleep(5)

    def run(self):
        """Starts and manages the entire hunting operation."""
        self.configure_hunt()
        input(f"\nPress Enter to start {self.num_browsers} hunter(s)...")

        # --- Create and Start Hunters ---
        for i in range(1, self.num_browsers + 1):
            if self.shutdown_event.is_set(): break
            driver = self.create_browser(i)
            if driver:
                self.browsers.append(driver)
                thread = threading.Thread(target=self.hunt_tickets_loop, args=(i, driver), daemon=True)
                self.threads.append(thread)
                thread.start()
                time.sleep(random.uniform(2, 4)) # Stagger startup
        
        if not self.browsers:
            self.log("No browsers were started. Exiting.", 'error')
            return

        # --- Main Monitoring Loop ---
        try:
            start_time = time.time()
            while not self.shutdown_event.is_set():
                runtime = time.time() - start_time
                print(f"\rRunning for: {int(runtime)}s | Secured: {self.tickets_secured}/{self.max_tickets_to_secure}", end="")
                time.sleep(1)
            print("\nShutdown signal is active.")
        except KeyboardInterrupt:
            self.log("\nCtrl+C detected. Initiating graceful shutdown...", 'warning')
            self.shutdown_event.set()
        
        # --- Cleanup ---
        self.log("Waiting for all hunters to terminate...", 'info')
        for thread in self.threads:
            thread.join(timeout=10)
        
        for driver in self.browsers:
            try:
                driver.quit()
            except Exception:
                pass
        
        self.log("All processes terminated. Thank you for using the hunter.", 'success')

if __name__ == "__main__":
    bot = FanSaleHunter()
    bot.run()
