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
logger = logging.getLogger('FanSaleFINAL')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class FinalFanSaleBot:
    """
    The FINAL optimized bot - Correct timing + Smart patterns + Bandwidth saving
    Refresh FIRST, sleep AFTER
    """
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Pre-cache selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"
        
        # Human-like patterns (applied AFTER refresh)
        self.wait_patterns = [
            (0.3, 0.8),   # Very fast
            (0.5, 1.2),   # Fast
            (1.0, 2.0),   # Medium
            (1.5, 3.0),   # Slower
            (0.8, 1.5),   # Mixed fast
            (2.0, 3.5),   # Mixed slow
        ]
        self.current_pattern = 0
        self.checks_in_pattern = 0
        self.max_checks_per_pattern = random.randint(4, 8)
        
        self.driver = None

    def setup_driver(self):
        """Optimized driver setup"""
        logger.info("🚀 Setting up FINAL optimized browser...")
        
        options = uc.ChromeOptions()
        
        # Data-saving prefs
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Performance flags
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        
        # Profile persistence
        profile_dir = Path("browser_profiles") / "fansale_final"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Proxy with request blocking
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(10)
        
        logger.info("✅ FINAL browser ready")

    def _get_proxy_config(self):
        """Proxy config with aggressive bandwidth saving"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            logger.warning("No proxy configured - running direct")
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        def block_resources(request):
            # Aggressive blocking to save bandwidth
            block_list = [
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
                'font', '.woff', '.woff2', '.ttf', '.eot',
                'analytics', 'google', 'facebook', 'doubleclick', 'adsystem',
                'tracking', 'metrics', 'telemetry', 'beacon',
                '.mp4', '.webm', '.mp3', '.wav',
                '/cdn-cgi/', 'cloudflare', 'gtm.js', 'gtag',
            ]
            
            url_lower = request.url.lower()
            if any(pattern in url_lower for pattern in block_list):
                request.abort()
                
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': block_resources,
            'suppress_connection_errors': True,
            'verify_ssl': False  # Faster
        }

    def login(self):
        """Fast, reliable login"""
        logger.info("🔐 Checking session...")
        
        self.driver.get("https://www.fansale.it/fansale/")
        time.sleep(2)
        
        # Check if already logged in
        if self._is_logged_in():
            logger.info("✅ Already logged in!")
            return True
            
        logger.info("Performing login...")
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        # Handle cookie popup
        try:
            cookie_btn = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'ACCETTA')]"))
            )
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
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')] | //a[contains(@href, 'logout')]")
            return True
        except NoSuchElementException:
            return False

    def hunt_tickets(self):
        """
        The CORRECT hunting loop:
        1. Check current page quickly
        2. If no ticket, refresh IMMEDIATELY
        3. THEN apply human-like wait
        """
        logger.info(f"🎯 FINAL hunt mode at: {self.target_url}")
        
        self.driver.get(self.target_url)
        time.sleep(2)
        
        check_count = 0
        session_check_time = time.time()
        
        while True:
            try:
                check_count += 1
                
                # Quick check with minimal timeout
                ticket = WebDriverWait(self.driver, 0.3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.ticket_selector))
                )
                
                # TICKET FOUND!
                logger.info(f"🎫 TICKET FOUND after {check_count} checks!")
                self.execute_purchase(ticket)  # Pass element directly (micro-optimization)
                break
                
            except TimeoutException:
                # No ticket - this is the CRITICAL SECTION
                
                # ✅ CORRECT ORDER: Refresh FIRST to get latest data
                self.driver.refresh()
                
                # NOW we can apply human-like wait (AFTER getting fresh data)
                min_wait, max_wait = self.wait_patterns[self.current_pattern]
                wait_time = random.uniform(min_wait, max_wait)
                
                # Only log every 10 checks to reduce console spam
                if check_count % 10 == 0:
                    logger.info(f"Check #{check_count} - Pattern {self.current_pattern+1}/{len(self.wait_patterns)}")
                
                time.sleep(wait_time)
                
                # Pattern rotation for variation
                self.checks_in_pattern += 1
                if self.checks_in_pattern >= self.max_checks_per_pattern:
                    self.current_pattern = (self.current_pattern + 1) % len(self.wait_patterns)
                    self.checks_in_pattern = 0
                    self.max_checks_per_pattern = random.randint(4, 8)
                
                # Periodic session check (every 5 minutes)
                if time.time() - session_check_time > 300:
                    if not self._is_logged_in():
                        logger.warning("Session expired! Re-logging...")
                        self.login()
                        self.driver.get(self.target_url)
                    session_check_time = time.time()
                
            except Exception as e:
                logger.error(f"Error: {e}")
                self.driver.get(self.target_url)
                time.sleep(3)

    def execute_purchase(self, ticket_element):
        """Lightning-fast purchase with passed element"""
        logger.info("⚡ EXECUTING INSTANT PURCHASE!")
        
        try:
            # Click the already-found ticket element (saves lookup time)
            ticket_element.click()
            
            # Wait for buy button
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.buy_button_selector))
            )
            
            # JS click for speed
            self.driver.execute_script("arguments[0].click();", buy_button)
            
            logger.info("✅✅✅ TICKET SECURED! Complete payment manually.")
            
            # Keep browser open
            input("\nPress Enter to close browser...")
                
        except Exception as e:
            logger.error(f"❌ Purchase failed: {e}")
            # Return to monitoring
            self.driver.get(self.target_url)
            self.hunt_tickets()

    def run(self):
        """Main execution"""
        try:
            self.setup_driver()
            
            if not self.login():
                logger.error("Login failed, exiting...")
                return
                
            self.hunt_tickets()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════╗
    ║          FANSALE FINAL BOT                   ║
    ║                                              ║
    ║  ✓ Refresh FIRST (see tickets instantly)    ║
    ║  ✓ Human patterns AFTER (avoid detection)   ║
    ║  ✓ Aggressive bandwidth saving              ║
    ║  ✓ Micro-optimized purchase flow           ║
    ╚══════════════════════════════════════════════╝
    """)
    
    bot = FinalFanSaleBot()
    bot.run()
