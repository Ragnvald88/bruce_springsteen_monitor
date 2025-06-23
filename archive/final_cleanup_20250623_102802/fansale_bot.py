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
logger = logging.getLogger('FanSaleHybrid')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class FanSaleHybridBot:
    """
    Hybrid Bot - API speed with browser legitimacy
    - Manual login for safety
    - API polling through browser
    - Automatic fallback
    - Minimal data usage
    """
    
    def __init__(self):
        # Configuration
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        # API endpoint (reverse engineered)
        self.api_endpoint = "https://www.fansale.it/json/offers/17844388"
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"
        
        # Smart timing patterns
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
        self.last_api_response = None
        
        self.driver = None

    def setup_driver(self):
        """Minimal browser setup"""
        logger.info("🚀 Setting up hybrid browser...")
        
        options = uc.ChromeOptions()
        
        # Minimal resources
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Stealth
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-logging')
        
        # Profile persistence
        profile_dir = Path("browser_profiles") / "fansale_hybrid"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Proxy
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(15)
        
        logger.info("✅ Browser ready")

    def _get_proxy_config(self):
        """Proxy with aggressive blocking for API mode"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        def block_resources(request):
            # Block everything except API and essential
            block_list = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                         'font', '.woff', '.css', 'analytics', 'google',
                         'facebook', 'tracking', '.mp4']
            
            # Allow our API endpoint
            if 'json/offers' in request.url:
                return
                
            if any(x in request.url.lower() for x in block_list):
                request.abort()
                
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': block_resources,
            'suppress_connection_errors': True
        }

    def wait_for_manual_login(self):
        """Let user login manually - SAFER"""
        logger.info("🔐 Manual login required for safety")
        logger.info("=" * 50)
        
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        print("\n📋 MANUAL LOGIN INSTRUCTIONS:")
        print(f"1. Email: {self.email}")
        print(f"2. Password: {'*' * len(self.password)} (check your .env)")
        print("3. Complete any CAPTCHA if shown")
        print("4. Press Enter here when logged in...")
        print("=" * 50)
        
        input("\n✋ Press Enter after you've logged in manually...")
        
        # Verify login
        if self._is_logged_in():
            logger.info("✅ Login confirmed!")
            return True
        else:
            logger.error("❌ Not logged in yet. Please try again.")
            return False

    def _is_logged_in(self):
        """Check login status"""
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'My fanSALE')] | //a[contains(@href, 'logout')]")
            return True
        except NoSuchElementException:
            return False

    def inject_api_monitor(self):
        """Inject the API polling mechanism"""
        self.driver.execute_script("""
            window.apiMonitor = {
                pollCount: 0,
                lastCheck: 0,
                lastData: null,
                
                checkAPI: async function(url) {
                    try {
                        const response = await fetch(url, {
                            credentials: 'include',  // Important for cookies
                            headers: {
                                'Accept': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        
                        const data = await response.json();
                        this.pollCount++;
                        this.lastCheck = Date.now();
                        this.lastData = data;
                        
                        return {
                            success: true,
                            data: data,
                            hasTickets: Array.isArray(data) && data.length > 0
                        };
                        
                    } catch (error) {
                        return {
                            success: false,
                            error: error.message,
                            hasTickets: false
                        };
                    }
                }
            };
            
            console.log('API Monitor injected');
        """)

    def hunt_hybrid(self):
        """Hybrid hunting - API with fallback"""
        logger.info(f"🎯 HYBRID HUNT MODE ACTIVATED!")
        logger.info(f"Target: {self.api_endpoint}")
        
        # Navigate once to establish context
        self.driver.get(self.target_url)
        time.sleep(2)
        
        # Inject monitor
        self.inject_api_monitor()
        
        consecutive_errors = 0
        
        while True:
            try:
                self.total_polls += 1
                
                # Cache buster for fresh data
                cache_buster = int(time.time() * 1000) + random.randint(0, 999)
                api_url = f"{self.api_endpoint}?_={cache_buster}"
                
                # Poll through browser
                result = self.driver.execute_script(f"""
                    return await window.apiMonitor.checkAPI('{api_url}');
                """)
                
                if result['success']:
                    consecutive_errors = 0
                    
                    if result['hasTickets']:
                        logger.info(f"🎫 TICKETS DETECTED via API!")
                        logger.info(f"Response: {json.dumps(result['data'][:2], indent=2)}")  # Log first 2
                        
                        # Switch to page for purchase
                        self.execute_purchase_from_api()
                        break
                    
                    # Status updates
                    if self.total_polls % 50 == 0:
                        elapsed = time.time() - self.session_start
                        rate = self.total_polls / elapsed
                        data_saved_mb = (self.total_polls * 495) / 1024  # ~495KB saved per poll
                        
                        logger.info(f"📊 Status: {self.total_polls} polls | "
                                  f"{rate:.1f}/sec | "
                                  f"Saved: ~{data_saved_mb:.1f}MB data")
                else:
                    consecutive_errors += 1
                    logger.warning(f"API error: {result.get('error', 'Unknown')}")
                    
                    if consecutive_errors >= 3:
                        logger.warning("API failing, switching to fallback mode...")
                        self.fallback_page_hunt()
                        break
                
                # Human-like timing
                min_wait, max_wait = self.poll_patterns[self.current_pattern]
                wait_time = random.uniform(min_wait, max_wait)
                time.sleep(wait_time)
                
                # Rotate patterns
                self.polls_in_pattern += 1
                if self.polls_in_pattern >= self.max_polls_per_pattern:
                    self.current_pattern = (self.current_pattern + 1) % len(self.poll_patterns)
                    self.polls_in_pattern = 0
                    self.max_polls_per_pattern = random.randint(20, 40)
                
            except JavascriptException as e:
                logger.error(f"JS error: {e}")
                consecutive_errors += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                consecutive_errors += 1
                time.sleep(2)

    def fallback_page_hunt(self):
        """Traditional page refresh fallback"""
        logger.warning("📄 Fallback: Page refresh mode")
        
        check_count = 0
        while True:
            try:
                check_count += 1
                
                # Quick check
                ticket = WebDriverWait(self.driver, 0.3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.ticket_selector))
                )
                
                logger.info(f"🎫 Ticket found via page after {check_count} checks!")
                self.execute_purchase(ticket)
                break
                
            except TimeoutException:
                # Refresh immediately (correct timing!)
                self.driver.refresh()
                
                # Then wait
                time.sleep(random.uniform(1, 2))
                
                if check_count % 10 == 0:
                    logger.info(f"Fallback check #{check_count}")

    def execute_purchase_from_api(self):
        """Execute purchase after API detection"""
        logger.info("⚡ Switching to purchase mode!")
        
        try:
            # Refresh to see tickets on page
            self.driver.refresh()
            
            # Find and click ticket
            ticket = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.ticket_selector))
            )
            self.execute_purchase(ticket)
            
        except Exception as e:
            logger.error(f"Failed to find ticket after API detection: {e}")
            # Continue hunting
            self.fallback_page_hunt()

    def execute_purchase(self, ticket_element):
        """Execute the purchase"""
        logger.info("💳 EXECUTING PURCHASE!")
        
        try:
            # Click ticket
            self.driver.execute_script("arguments[0].click();", ticket_element)
            
            # Click buy button
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.buy_button_selector))
            )
            self.driver.execute_script("arguments[0].click();", buy_button)
            
            logger.info("✅✅✅ TICKET IN CART! Complete payment manually.")
            
            # Keep browser open
            input("\n🎉 Press Enter to close browser...")
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            traceback.print_exc()

    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════╗
        ║         FANSALE HYBRID BOT                   ║
        ║                                              ║
        ║  ✓ Manual login (safer)                     ║
        ║  ✓ API polling (99% less data)              ║
        ║  ✓ Browser auth (legitimate)                ║
        ║  ✓ Auto fallback (reliable)                 ║
        ╚══════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_driver()
            
            # Manual login for safety
            while not self.wait_for_manual_login():
                logger.warning("Please complete login...")
                time.sleep(2)
            
            # Start hunting
            self.hunt_hybrid()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    bot = FanSaleHybridBot()
    bot.run()
