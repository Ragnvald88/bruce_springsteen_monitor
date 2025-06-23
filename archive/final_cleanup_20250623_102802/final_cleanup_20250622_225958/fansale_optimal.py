import os
import sys
import time
import random
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Setup
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# Logging
logger = logging.getLogger('FanSaleOptimal')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class OptimalFanSaleBot:
    """
    Optimal approach: Simple, effective, with smart patterns
    Based on v4_PRO with bandwidth optimizations
    """
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Human-like timing (but we WILL refresh!)
        self.refresh_patterns = [
            (1.0, 2.0),   # Fast checks
            (2.0, 4.0),   # Medium checks
            (3.0, 5.0),   # Slower checks
            (1.5, 3.0),   # Mixed
        ]
        self.current_pattern = 0
        self.checks_in_pattern = 0
        self.max_checks_per_pattern = random.randint(3, 7)
        
        self.driver = None

    def setup_driver(self):
        """Optimized driver setup"""
        logger.info("🚀 Setting up optimized browser...")
        
        options = uc.ChromeOptions()
        
        # Data-saving prefs
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Essential performance flags only
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-images')
        
        # Profile persistence (handles cookies automatically)
        profile_dir = Path("browser_profiles") / "fansale_optimal"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Proxy with request blocking
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(10)
        
        logger.info("✅ Browser ready")

    def _get_proxy_config(self):
        """Proxy config with bandwidth saving"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        def block_resources(request):
            # Block bandwidth-heavy resources
            block_list = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                         'font', '.woff', '.woff2', 'analytics', 'google',
                         'facebook', 'doubleclick', '.mp4', '.webm']
            
            if any(pattern in request.url.lower() for pattern in block_list):
                request.abort()
                
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': block_resources,
            'suppress_connection_errors': True
        }

    def login(self):
        """Simple, reliable login"""
        logger.info("🔐 Checking session...")
        
        self.driver.get("https://www.fansale.it/fansale/")
        time.sleep(2)
        
        # Check if already logged in
        if self._is_logged_in():
            logger.info("✅ Already logged in!")
            return True
            
        logger.info("Logging in...")
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        # Handle cookies
        try:
            cookie_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'ACCETTA')]")
            cookie_btn.click()
        except:
            pass
        
        # Fast login with JS
        self.driver.execute_script(f"""
            document.querySelector('input[name="login_email"]').value = arguments[0];
            document.querySelector('input[name="login_password"]').value = arguments[1];
            document.querySelector('#loginCustomerButton').click();
        """, self.email, self.password)
        
        # Verify login
        try:
            WebDriverWait(self.driver, 10).until(lambda d: self._is_logged_in())
            logger.info("✅ Login successful!")
            return True
        except:
            logger.error("❌ Login failed!")
            return False

    def _is_logged_in(self):
        """Check login status"""
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')]")
            return True
        except NoSuchElementException:
            return False

    def hunt_tickets(self):
        """The optimal hunting loop - simple but with smart patterns"""
        logger.info(f"🎯 Hunting at: {self.target_url}")
        
        self.driver.get(self.target_url)
        time.sleep(2)
        
        check_count = 0
        consecutive_errors = 0
        
        while True:
            try:
                check_count += 1
                
                # The KEY: We check for tickets with a SHORT timeout
                # This means we check the CURRENT page quickly
                ticket = WebDriverWait(self.driver, 0.5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-qa='ticketToBuy']"))
                )
                
                # TICKET FOUND!
                logger.info(f"🎫 TICKET FOUND after {check_count} checks!")
                self.execute_purchase(ticket)
                break
                
            except TimeoutException:
                # No ticket on current page - this is normal
                # THE CRITICAL PART: We MUST refresh to get new data!
                
                # Get wait time from current pattern
                min_wait, max_wait = self.refresh_patterns[self.current_pattern]
                wait_time = random.uniform(min_wait, max_wait)
                
                logger.info(f"Check #{check_count} - No tickets. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                
                # REFRESH TO GET NEW DATA FROM SERVER
                self.driver.refresh()
                
                # Pattern management for human-like behavior
                self.checks_in_pattern += 1
                if self.checks_in_pattern >= self.max_checks_per_pattern:
                    self.current_pattern = (self.current_pattern + 1) % len(self.refresh_patterns)
                    self.checks_in_pattern = 0
                    self.max_checks_per_pattern = random.randint(3, 7)
                    logger.info(f"Switching pattern after {check_count} total checks")
                
                consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error #{consecutive_errors}: {e}")
                
                if consecutive_errors >= 3:
                    logger.warning("Multiple errors, reloading page...")
                    self.driver.get(self.target_url)
                    time.sleep(3)
                    consecutive_errors = 0
                else:
                    time.sleep(2)

    def execute_purchase(self, ticket_element):
        """Fast purchase execution"""
        logger.info("⚡ EXECUTING PURCHASE!")
        
        try:
            # Click the ticket
            ticket_element.click()
            
            # Wait for buy button
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='buyNowButton']"))
            )
            
            # Click buy button
            buy_button.click()
            
            logger.info("✅ TICKET IN CART! Complete payment manually.")
            
            # Keep browser open
            while True:
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"❌ Purchase failed: {e}")

    def run(self):
        """Main execution"""
        try:
            self.setup_driver()
            
            if not self.login():
                logger.error("Login failed, exiting...")
                return
                
            self.hunt_tickets()
            
        except KeyboardInterrupt:
            logger.info("🛑 Stopped by user")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    logger.info("""
    ╔══════════════════════════════════════╗
    ║     OPTIMAL FANSALE BOT              ║
    ║     Simple + Smart Patterns          ║
    ║     Based on working v4_PRO logic    ║
    ╚══════════════════════════════════════╝
    """)
    
    bot = OptimalFanSaleBot()
    bot.run()
