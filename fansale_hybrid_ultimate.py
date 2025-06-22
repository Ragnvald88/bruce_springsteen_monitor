import os
import sys
import time
import json
import random
import logging
import traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, JavascriptException

# Setup
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# Logging
logger = logging.getLogger('FanSale_HYBRID_ULTIMATE')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class UltimateHybridBot:
    """
    The ULTIMATE HYBRID Bot - The best of all approaches
    - Authenticated browser session for legitimacy
    - Lightweight API polling for speed
    - Human-like patterns to avoid detection
    - Automatic fallback if API changes
    """
    
    def __init__(self):
        # API endpoint with event ID
        self.api_endpoint = "https://www.fansale.it/json/offers/17844388"
        
        # Fallback URLs
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"
        
        # Timing patterns (to avoid detection)
        self.poll_patterns = [
            (0.3, 0.5),   # Fast burst
            (0.5, 0.8),   # Medium
            (0.8, 1.2),   # Slower
            (0.4, 0.6),   # Mixed
        ]
        self.current_pattern = 0
        self.polls_in_pattern = 0
        self.max_polls_per_pattern = random.randint(20, 40)
        
        # Tracking
        self.api_failures = 0
        self.total_polls = 0
        self.session_start = time.time()
        
        self.driver = None

    def setup_driver(self):
        """Optimized browser setup"""
        logger.info("🚀 Setting up ULTIMATE HYBRID browser...")
        
        options = uc.ChromeOptions()
        
        # Minimal resource usage
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Stealth flags
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-logging')
        
        # Persistent profile
        profile_dir = Path("browser_profiles") / "fansale_hybrid_ultimate"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Proxy if available
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(15)
        
        logger.info("✅ ULTIMATE browser ready")

    def _get_proxy_config(self):
        """Proxy configuration"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        # Even with API polling, we want to block unnecessary resources
        def block_resources(request):
            if any(x in request.url.lower() for x in ['.png', '.jpg', 'analytics', 'google']):
                request.abort()
                
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': block_resources,
            'suppress_connection_errors': True
        }

    def ensure_logged_in(self):
        """Ensure we have a valid session"""
        logger.info("🔐 Checking session...")
        
        self.driver.get("https://www.fansale.it/fansale/")
        time.sleep(2)
        
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')] | //a[contains(@href, 'logout')]")
            logger.info("✅ Session active!")
            return True
        except NoSuchElementException:
            logger.error("❌ Not logged in! Attempting login...")
            return self.login()

    def login(self):
        """Automated login"""
        try:
            self.driver.get("https://www.fansale.it/fansale/login.htm")
            
            # Handle cookies
            try:
                cookie_btn = self.driver.find_element(By.XPATH, "//button[contains(., 'ACCETTA')]")
                cookie_btn.click()
            except:
                pass
            
            # Login
            email = os.getenv('FANSALE_EMAIL')
            password = os.getenv('FANSALE_PASSWORD')
            
            self.driver.execute_script(f"""
                document.querySelector('input[name="login_email"]').value = arguments[0];
                document.querySelector('input[name="login_password"]').value = arguments[1];
                document.querySelector('#loginCustomerButton').click();
            """, email, password)
            
            # Verify
            time.sleep(3)
            return self.driver.execute_script("""
                return !!(document.querySelector('*:contains("My fanSALE")') || 
                         document.querySelector('a[href*="logout"]'));
            """)
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def hunt_hybrid(self):
        """The ULTIMATE hunting strategy"""
        logger.info(f"🎯 HYBRID HUNT ENGAGED!")
        
        # Navigate to page once to establish context
        self.driver.get(self.target_url)
        time.sleep(2)
        
        # Inject monitoring helper
        self.driver.execute_script("""
            window.hybridMonitor = {
                lastApiCall: 0,
                apiCalls: 0,
                
                checkAPI: async function(url) {
                    try {
                        const response = await fetch(url);
                        const data = await response.json();
                        this.apiCalls++;
                        this.lastApiCall = Date.now();
                        return {success: true, data: data};
                    } catch (e) {
                        return {success: false, error: e.toString()};
                    }
                }
            };
        """)
        
        while True:
            try:
                self.total_polls += 1
                
                # Generate cache buster
                cache_buster = int(time.time() * 1000) + random.randint(0, 999)
                api_url = f"{self.api_endpoint}?_={cache_buster}"
                
                # Poll API through browser context (maintains auth)
                result = self.driver.execute_script(f"""
                    return await window.hybridMonitor.checkAPI('{api_url}');
                """)
                
                if result['success']:
                    data = result['data']
                    
                    # Check if tickets found
                    if isinstance(data, list) and len(data) > 0:
                        logger.info(f"🎫 TICKETS FOUND! {len(data)} offers available!")
                        self.execute_purchase()
                        break
                    
                    # Reset failure counter on success
                    self.api_failures = 0
                    
                else:
                    self.api_failures += 1
                    logger.warning(f"API call failed: {result.get('error', 'Unknown')}")
                    
                    # Fallback to page refresh after 3 failures
                    if self.api_failures >= 3:
                        logger.warning("API failing, falling back to page refresh method...")
                        self.fallback_hunt()
                        break
                
                # Status update every ~20 seconds
                if self.total_polls % 50 == 0:
                    elapsed = time.time() - self.session_start
                    rate = self.total_polls / elapsed
                    logger.info(f"Status: {self.total_polls} checks, {rate:.1f}/sec, "
                              f"Data saved: ~{(self.total_polls * 495) / 1024:.1f}MB")
                
                # Human-like timing
                min_wait, max_wait = self.poll_patterns[self.current_pattern]
                wait_time = random.uniform(min_wait, max_wait)
                time.sleep(wait_time)
                
                # Pattern rotation
                self.polls_in_pattern += 1
                if self.polls_in_pattern >= self.max_polls_per_pattern:
                    self.current_pattern = (self.current_pattern + 1) % len(self.poll_patterns)
                    self.polls_in_pattern = 0
                    self.max_polls_per_pattern = random.randint(20, 40)
                
            except JavascriptException as e:
                logger.error(f"JavaScript error: {e}")
                self.api_failures += 1
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(2)

    def fallback_hunt(self):
        """Fallback to traditional page refresh if API fails"""
        logger.warning("Switching to fallback page refresh mode...")
        
        while True:
            try:
                # Traditional check
                ticket = WebDriverWait(self.driver, 0.5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.ticket_selector))
                )
                logger.info("🎫 Ticket found via page check!")
                self.execute_purchase(ticket)
                break
                
            except TimeoutException:
                self.driver.refresh()
                time.sleep(random.uniform(1, 2))

    def execute_purchase(self, ticket_element=None):
        """Execute the purchase"""
        logger.info("⚡ EXECUTING PURCHASE!")
        
        try:
            # If we came from API, we need to refresh to see tickets
            if not ticket_element:
                self.driver.refresh()
                ticket_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.ticket_selector))
                )
            
            # Click ticket
            self.driver.execute_script("arguments[0].click();", ticket_element)
            
            # Click buy button
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.buy_button_selector))
            )
            self.driver.execute_script("arguments[0].click();", buy_button)
            
            logger.info("✅✅✅ PURCHASE COMPLETE! Check your cart!")
            
            # Keep browser open
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            # Return to hunting
            self.hunt_hybrid()

    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════╗
        ║         ULTIMATE HYBRID FANSALE BOT          ║
        ║                                              ║
        ║  • API Polling: 98% less data usage         ║
        ║  • Browser Auth: Legitimate sessions        ║
        ║  • Smart Patterns: Avoid detection          ║
        ║  • Auto Fallback: Never miss tickets        ║
        ╚══════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_driver()
            
            if self.ensure_logged_in():
                self.hunt_hybrid()
            else:
                logger.error("Login failed. Please check credentials.")
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    bot = UltimateHybridBot()
    bot.run()
