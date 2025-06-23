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
from selenium.webdriver.common.action_chains import ActionChains

# Setup
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# Logging
logger = logging.getLogger('FanSaleHybrid')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class FanSaleHybridBot:
    """
    Hybrid Bot v2 - Works with Akamai protection
    - Lets Akamai JavaScript run naturally
    - Waits for valid cookies before API calls
    - Simulates human behavior
    """
    
    def __init__(self):
        # Configuration
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        # URLs
        self.api_endpoint = "https://www.fansale.it/json/offers/17844388"
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"
        
        # Timing patterns
        self.poll_patterns = [
            (0.8, 1.5),   # Slower to avoid detection
            (1.2, 2.0),   
            (1.5, 2.5),   
            (1.0, 1.8),   
        ]
        
        # Tracking
        self.warmup_complete = False
        self.api_ready = False
        self.last_mouse_move = 0
        
        self.driver = None

    def setup_driver(self):
        """Setup browser with anti-detection"""
        logger.info("🚀 Setting up stealth browser...")
        
        options = uc.ChromeOptions()
        
        # Minimal interference with Akamai
        prefs = {
            "profile.managed_default_content_settings.images": 1,  # Load images (Akamai checks)
            "profile.managed_default_content_settings.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Stealth but not too aggressive
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Profile persistence
        profile_dir = Path("browser_profiles") / "fansale_akamai"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Window size (Akamai checks this)
        options.add_argument('--window-size=1920,1080')
        
        # Proxy
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(20)
        
        # Important: Set viewport size
        self.driver.set_window_size(1920, 1080)
        
        logger.info("✅ Browser ready")

    def _get_proxy_config(self):
        """Proxy configuration"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'suppress_connection_errors': True
        }

    def simulate_human_behavior(self):
        """Simulate human mouse movements and scrolling"""
        try:
            # Random mouse movement
            action = ActionChains(self.driver)
            
            # Move to random coordinates
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            
            # Human-like curve movement
            action.move_by_offset(x, y)
            action.pause(random.uniform(0.1, 0.3))
            action.move_by_offset(-x//2, -y//2)
            action.perform()
            
            # Random scroll
            scroll_amount = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.2, 0.5))
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_amount//2});")
            
        except:
            pass  # Don't fail on behavior simulation

    def warmup_browser(self):
        """Warm up browser and let Akamai sensors initialize"""
        logger.info("🔥 Browser warmup for Akamai...")
        
        # Visit main page first
        self.driver.get("https://www.fansale.it")
        time.sleep(3)
        
        # Simulate some browsing
        self.simulate_human_behavior()
        time.sleep(2)
        
        # Visit target page
        self.driver.get(self.target_url)
        time.sleep(3)
        
        # More human behavior
        for _ in range(3):
            self.simulate_human_behavior()
            time.sleep(random.uniform(1, 2))
        
        logger.info("✅ Warmup complete - Akamai should have generated tokens")
        self.warmup_complete = True

    def wait_for_manual_login(self):
        """Manual login for safety"""
        logger.info("🔐 Manual login required")
        logger.info("=" * 50)
        
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        print("\n📋 MANUAL LOGIN INSTRUCTIONS:")
        print(f"1. Email: {self.email}")
        print(f"2. Password: {'*' * len(self.password)}")
        print("3. Complete any CAPTCHA")
        print("4. Press Enter when logged in...")
        print("=" * 50)
        
        input("\n✋ Press Enter after login...")
        
        if self._is_logged_in():
            logger.info("✅ Login confirmed!")
            return True
        return False

    def _is_logged_in(self):
        """Check login status"""
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')] | //a[contains(@href, 'logout')]")
            return True
        except NoSuchElementException:
            return False

    def check_akamai_cookies(self):
        """Check if we have valid Akamai cookies"""
        cookies = self.driver.get_cookies()
        
        # Look for Akamai cookies
        akamai_cookies = {}
        for cookie in cookies:
            if cookie['name'] in ['_abck', 'ak_bmsc', 'bm_sv', 'bm_sz']:
                akamai_cookies[cookie['name']] = cookie['value']
        
        # Check if _abck is valid
        if '_abck' in akamai_cookies:
            abck = akamai_cookies['_abck']
            # Invalid cookies end with ~0~-1~-1
            if not abck.endswith('~0~-1~-1') and not abck.endswith('~-1~-1'):
                logger.info(f"✅ Valid Akamai cookies found: {list(akamai_cookies.keys())}")
                return True
        
        logger.warning("❌ No valid Akamai cookies yet")
        return False

    def inject_api_monitor(self):
        """Inject API monitor that includes Akamai cookies"""
        self.driver.execute_script("""
            window.apiMonitor = {
                checkAPI: async function(url) {
                    try {
                        // Let browser handle all cookies including Akamai
                        const response = await fetch(url, {
                            method: 'GET',
                            credentials: 'include',
                            headers: {
                                'Accept': 'application/json',
                                'Referer': window.location.href,
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                        
                        const data = await response.json();
                        
                        return {
                            success: response.ok,
                            status: response.status,
                            data: data,
                            hasTickets: Array.isArray(data) && data.length > 0
                        };
                        
                    } catch (error) {
                        return {
                            success: false,
                            error: error.message,
                            status: 0
                        };
                    }
                }
            };
            
            console.log('API Monitor with Akamai support injected');
        """)

    def hunt_hybrid_akamai(self):
        """Hunt with Akamai protection awareness"""
        logger.info("🎯 AKAMAI-AWARE HYBRID HUNT!")
        
        # First, warm up and generate Akamai tokens
        if not self.warmup_complete:
            self.warmup_browser()
        
        # Check for valid cookies
        attempts = 0
        while not self.check_akamai_cookies() and attempts < 5:
            logger.info(f"Waiting for Akamai cookies... (attempt {attempts+1}/5)")
            self.simulate_human_behavior()
            time.sleep(3)
            self.driver.refresh()
            time.sleep(2)
            attempts += 1
        
        if not self.check_akamai_cookies():
            logger.error("Failed to get valid Akamai cookies!")
            return self.fallback_page_hunt()
        
        # Inject monitor
        self.inject_api_monitor()
        
        # Start hunting
        poll_count = 0
        consecutive_403s = 0
        
        while True:
            try:
                poll_count += 1
                
                # Human behavior every ~10 polls
                if poll_count % 10 == 0:
                    self.simulate_human_behavior()
                
                # API check
                cache_buster = int(time.time() * 1000)
                api_url = f"{self.api_endpoint}?_={cache_buster}"
                
                result = self.driver.execute_script(f"""
                    return await window.apiMonitor.checkAPI('{api_url}');
                """)
                
                if result['success']:
                    consecutive_403s = 0
                    
                    if result['hasTickets']:
                        logger.info("🎫 TICKETS FOUND via API!")
                        self.execute_purchase_from_api()
                        break
                    
                    if poll_count % 20 == 0:
                        logger.info(f"📊 Poll #{poll_count} - No tickets yet")
                        
                elif result['status'] == 403:
                    consecutive_403s += 1
                    logger.warning(f"403 error #{consecutive_403s}")
                    
                    if consecutive_403s >= 3:
                        logger.warning("Multiple 403s - refreshing page to regenerate tokens")
                        self.driver.refresh()
                        time.sleep(3)
                        self.simulate_human_behavior()
                        time.sleep(2)
                        consecutive_403s = 0
                else:
                    logger.warning(f"API error: {result.get('error', 'Unknown')}")
                
                # Human-like timing
                pattern = self.poll_patterns[poll_count % len(self.poll_patterns)]
                wait_time = random.uniform(pattern[0], pattern[1])
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(2)

    def fallback_page_hunt(self):
        """Traditional page monitoring as fallback"""
        logger.warning("📄 Using page refresh fallback")
        
        check_count = 0
        while True:
            try:
                check_count += 1
                
                # Human behavior
                if check_count % 5 == 0:
                    self.simulate_human_behavior()
                
                # Check for tickets
                ticket = WebDriverWait(self.driver, 0.5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.ticket_selector))
                )
                
                logger.info(f"🎫 Ticket found after {check_count} checks!")
                self.execute_purchase(ticket)
                break
                
            except TimeoutException:
                self.driver.refresh()
                time.sleep(random.uniform(2, 3))

    def execute_purchase_from_api(self):
        """Execute purchase after API detection"""
        logger.info("💳 Switching to purchase mode!")
        
        try:
            # Refresh to see tickets
            self.driver.refresh()
            
            # Find and click
            ticket = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.ticket_selector))
            )
            self.execute_purchase(ticket)
            
        except Exception as e:
            logger.error(f"Failed to find ticket: {e}")
            self.fallback_page_hunt()

    def execute_purchase(self, ticket_element):
        """Execute purchase"""
        logger.info("⚡ EXECUTING PURCHASE!")
        
        try:
            # Click ticket
            self.driver.execute_script("arguments[0].click();", ticket_element)
            
            # Click buy
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.buy_button_selector))
            )
            self.driver.execute_script("arguments[0].click();", buy_button)
            
            logger.info("✅✅✅ SUCCESS! Complete payment manually.")
            input("\nPress Enter to close...")
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")

    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════╗
        ║      FANSALE HYBRID BOT v2 (AKAMAI)         ║
        ║                                              ║
        ║  ✓ Handles Akamai protection                ║
        ║  ✓ Generates valid cookies                  ║
        ║  ✓ Human behavior simulation                ║
        ║  ✓ Smart API polling                        ║
        ╚══════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_driver()
            
            # Manual login
            while not self.wait_for_manual_login():
                time.sleep(2)
            
            # Start hunting with Akamai awareness
            self.hunt_hybrid_akamai()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    bot = FanSaleHybridBot()
    bot.run()
