#!/usr/bin/env python3
"""
Save the user's revised script to the main project
"""

import shutil
from pathlib import Path

# The content from the user's paste.txt (document 2)
revised_script_content = '''import os
import sys
import time
import logging
import yaml
import traceback
from enum import Enum
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Basic Setup ---
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# --- Logging Configuration ---
log_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler(f'logs/fansale_sniper_v4_PRO_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
logger = logging.getLogger('FanSaleSniperV4_PRO')
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

class BotState(Enum):
    INITIALIZING = "initializing"
    CHECKING_SESSION = "checking_session"
    LOGGING_IN = "logging_in"
    MONITORING = "monitoring"
    PURCHASING = "purchasing"
    SUCCESS = "success"
    ERROR = "error"

class FanSaleSniperPRO:
    def __init__(self, config):
        self.config = config
        self.state = BotState.INITIALIZING
        self.driver = None
        self.last_session_check_time = 0
        self.session_check_interval = 300 # Check every 5 minutes

        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        if not self.email or not self.password:
            raise ValueError("FATAL: Missing FANSALE_EMAIL or FANSALE_PASSWORD in your .env file!")
        
        # Pre-cache selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"

        logger.info("FanSale Sniper v4 PRO Initialized.")

    def run(self):
        logger.info("🚀 Starting FanSale Sniper Bot v4 PRO...")
        try:
            while self.state not in [BotState.SUCCESS, BotState.ERROR]:
                if self.state == BotState.INITIALIZING: self._handle_initializing()
                elif self.state == BotState.CHECKING_SESSION: self._check_session_and_login()
                elif self.state == BotState.LOGGING_IN: self._perform_login()
                elif self.state == BotState.MONITORING: self._handle_monitoring()
                elif self.state == BotState.PURCHASING: self._handle_purchasing()
            
            if self.state == BotState.SUCCESS:
                logger.info("✅✅✅ TICKET IN CART! The browser will remain open for you to complete payment. ✅✅✅")
            else:
                logger.error("❌ Bot stopped due to an unrecoverable error.")

        except KeyboardInterrupt:
            logger.info("⏹️ Bot stopped by user.")
        finally:
            if self.driver:
                logger.info("Bot is shutting down.")
                if self.state == BotState.SUCCESS:
                    time.sleep(600)
                self.driver.quit()

    def _setup_driver(self):
        logger.info("Setting up PRO stealth browser...")
        options = uc.ChromeOptions()
        
        # Your excellent performance optimizations
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Your excellent performance flags (with the dangerous one removed)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu') # Disabling GPU can improve stability
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        
        # Profile persistence is key
        profile_dir = Path("browser_profiles") / "fansale_user_pro"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        proxy_options = None
        if all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
            proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
            proxy_options = {'proxy': {'http': f'http://{proxy_auth}@{proxy_server}', 'https': f'https://{proxy_auth}@{proxy_server}'}}
            logger.info(f"Configuring browser with IPRoyal proxy: {os.getenv('IPROYAL_HOSTNAME')}")

        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(15)
        logger.info("PRO browser setup complete.")

    def _is_logged_in(self):
        # A fast JS check is great, but reliability is king. 
        # A simple, robust find_element is less prone to errors on different page states.
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')] | //a[contains(@href, 'logout')]")
            return True
        except NoSuchElementException:
            return False

    def _handle_cookie_popup(self):
        try:
            cookie_button = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'ACCETTA TUTTI')]")))
            cookie_button.click()
            logger.info("Cookie banner accepted.")
        except TimeoutException:
            pass # No banner, no problem.

    def _handle_initializing(self):
        self._setup_driver()
        self.state = BotState.CHECKING_SESSION

    def _check_session_and_login(self):
        logger.info("Checking login status...")
        self.driver.get("https://www.fansale.it/fansale/")
        self._handle_cookie_popup()
        if self._is_logged_in():
            logger.info("✅ Session is active. Proceeding to monitoring.")
            self.state = BotState.MONITORING
        else:
            logger.info("No active session. Triggering login process.")
            self.state = BotState.LOGGING_IN

    def _perform_login(self):
        try:
            logger.info("Executing rapid login sequence...")
            # Use your excellent JS injection method for speed
            self.driver.get("https://www.fansale.it/fansale/login.htm")
            self._handle_cookie_popup()
            
            # This is much faster than send_keys
            self.driver.execute_script(f"""
                document.querySelector('input[name="login_email"]').value = arguments[0];
                document.querySelector('input[name="login_password"]').value = arguments[1];
                document.querySelector('#loginCustomerButton').click();
            """, self.email, self.password)
            
            WebDriverWait(self.driver, 10).until(lambda d: self._is_logged_in())
            logger.info("✅ Login successful! Session is now saved.")
            self.state = BotState.MONITORING
        except Exception as e:
            logger.error(f"Error during login: {e}")
            self.state = BotState.ERROR

    def _handle_monitoring(self):
        logger.info(f"🚀 TURBO MONITORING ACTIVATED. Navigating to event page...")
        self.driver.get(self.config['target_url'])
        self.last_session_check_time = time.time()
        
        check_count = 0
        while self.state == BotState.MONITORING:
            try:
                # Periodic session check
                if time.time() - self.last_session_check_time > self.session_check_interval:
                    if not self._is_logged_in():
                        logger.warning("Session expired! Re-login required.")
                        self.state = BotState.CHECKING_SESSION
                        return
                    self.last_session_check_time = time.time()

                check_count += 1
                logger.info(f"Checking for tickets... [Attempt #{check_count}]")
                
                # The reliable WebDriverWait is used. It's fast enough and won't miss the element.
                WebDriverWait(self.driver, self.config['speed']['check_interval_seconds']).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.ticket_selector))
                )

                logger.info("✅✅✅ TICKET DETECTED! INITIATING INSTANT PURCHASE! ✅✅✅")
                self.state = BotState.PURCHASING

            except TimeoutException:
                # THIS IS THE KEY: We must refresh to get new data from the server.
                self.driver.refresh()
            except Exception as e:
                logger.error(f"Monitoring error: {e}. Recovering...")
                self.driver.get(self.config['target_url']) # Full reload on error
                time.sleep(3)

    def _handle_purchasing(self):
        logger.info("⚡ Executing lightning purchase script!")
        try:
            # Using your JS-click idea for maximum speed.
            self.driver.execute_script(f"""
                document.querySelector(arguments[0]).click();
            """, self.ticket_selector)
            
            # Wait for the buy button to appear after the first click
            # WebDriverWait is essential here to ensure the page has transitioned
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.buy_button_selector))
            )
            
            # Final click, also with JS
            self.driver.execute_script("arguments[0].click();", buy_button)
            
            self.state = BotState.SUCCESS

        except Exception as e:
            logger.error(f"Purchase failed: {e}. Likely snatched by another bot. Returning to monitoring.")
            self.driver.get(self.config['target_url'])
            self.state = BotState.MONITORING

def load_config():
    # Using your improved config loader
    config_path = Path("config.yaml")
    if not config_path.is_file():
        logger.warning("config.yaml not found. Using default settings.")
        return {'target_url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554', 'speed': {'check_interval_seconds': 0.5}}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    try:
        config = load_config()
        bot = FanSaleSniperPRO(config)
        bot.run()
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

# Save the user's revised script
output_path = Path("fansale_sniper_v4_PRO.py")
with open(output_path, 'w') as f:
    f.write(revised_script_content)

print(f"✅ Saved your revised script to: {output_path}")
