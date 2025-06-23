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
    
    def __init__(self):
        # Configuration
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        # URLs
        self.api_endpoint = "https://www.fansale.it/json/offers/17844388"
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        self.base_url = "https://www.fansale.it"
        
        # Selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"
        
        # Timing patterns
        self.poll_patterns = [
            (0.3, 0.5),
            (0.5, 0.8),
            (0.8, 1.2),
            (0.4, 0.6),
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
        """Setup browser with optimal settings"""
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
        """Proxy configuration"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        def block_resources(request):
            block_list = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                         'font', '.woff', '.css', 'analytics', 'google',
                         'facebook', 'tracking', '.mp4']
            
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
        """Manual login for safety"""
        logger.info("🔐 Manual login required")
        logger.info("=" * 50)
        
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        print("\n📋 MANUAL LOGIN INSTRUCTIONS:")
        print(f"1. Email: {self.email}")
        print(f"2. Password: {'*' * len(self.password)} (check your .env)")
        print("3. Complete any CAPTCHA if shown")
        print("4. Press Enter here when logged in...")
        print("=" * 50)
        
        input("\n✋ Press Enter after you've logged in manually...")
        
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

    def extract_auth_tokens(self):
        """Extract authentication tokens from the page"""
        logger.info("🔑 Extracting authentication tokens...")
        
        # Navigate to main page to ensure we have all cookies
        self.driver.get(self.target_url)
        time.sleep(2)
        
        # Extract any CSRF tokens or session data
        tokens = self.driver.execute_script("""
            // Look for common CSRF token patterns
            const tokenMeta = document.querySelector('meta[name="csrf-token"]');
            const tokenInput = document.querySelector('input[name="authenticity_token"], input[name="csrf_token"], input[name="_token"]');
            
            // Get all cookies
            const cookies = document.cookie;
            
            // Get session storage
            const sessionData = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                sessionData[key] = sessionStorage.getItem(key);
            }
            
            return {
                csrfToken: tokenMeta ? tokenMeta.content : (tokenInput ? tokenInput.value : null),
                cookies: cookies,
                sessionData: sessionData,
                referrer: document.referrer,
                origin: window.location.origin
            };
        """)
        
        logger.info(f"Tokens extracted: CSRF={tokens.get('csrfToken') is not None}")
        return tokens

    def inject_api_monitor_fixed(self, tokens):
        """Fixed API monitor with proper authentication"""
        self.driver.execute_script("""
            window.apiMonitor = {
                pollCount: 0,
                lastCheck: 0,
                lastData: null,
                tokens: arguments[0],
                
                checkAPI: async function(url) {
                    try {
                        // Build proper headers
                        const headers = {
                            'Accept': 'application/json, text/plain, */*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'same-origin',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Referer': window.location.href,
                            'User-Agent': navigator.userAgent
                        };
                        
                        // Add CSRF token if available
                        if (this.tokens.csrfToken) {
                            headers['X-CSRF-Token'] = this.tokens.csrfToken;
                        }
                        
                        const response = await fetch(url, {
                            method: 'GET',
                            credentials: 'include',  // CRITICAL: Include cookies
                            headers: headers,
                            mode: 'cors',
                            referrerPolicy: 'strict-origin-when-cross-origin'
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const data = await response.json();
                        this.pollCount++;
                        this.lastCheck = Date.now();
                        this.lastData = data;
                        
                        return {
                            success: true,
                            data: data,
                            hasTickets: Array.isArray(data) && data.length > 0,
                            status: response.status
                        };
                        
                    } catch (error) {
                        return {
                            success: false,
                            error: error.message,
                            hasTickets: false,
                            status: error.message.includes('HTTP') ? parseInt(error.message.match(/\d+/)[0]) : 0
                        };
                    }
                }
            };
            
            console.log('Fixed API Monitor injected with auth tokens');
        """, tokens)

    def test_api_access(self):
        """Test if we can access the API"""
        logger.info("🧪 Testing API access...")
        
        test_url = f"{self.api_endpoint}?_={int(time.time() * 1000)}"
        result = self.driver.execute_script(f"""
            return await window.apiMonitor.checkAPI('{test_url}');
        """)
        
        if result['success']:
            logger.info(f"✅ API access successful! Status: {result['status']}")
            return True
        else:
            logger.error(f"❌ API access failed: {result['error']}")
            return False

    def hunt_hybrid_fixed(self):
        """Fixed hybrid hunting with proper auth"""
        logger.info(f"🎯 FIXED HYBRID HUNT MODE!")
        
        # Extract auth tokens
        tokens = self.extract_auth_tokens()
        
        # Inject monitor with tokens
        self.inject_api_monitor_fixed(tokens)
        
        # Test API access
        if not self.test_api_access():
            logger.warning("API access failed, falling back to page refresh mode")
            self.fallback_page_hunt()
            return
        
        consecutive_errors = 0
        
        while True:
            try:
                self.total_polls += 1
                
                # Cache buster
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
                        self.execute_purchase_from_api()
                        break
                    
                    # Status updates
                    if self.total_polls % 50 == 0:
                        elapsed = time.time() - self.session_start
                        rate = self.total_polls / elapsed
                        data_saved_mb = (self.total_polls * 495) / 1024
                        
                        logger.info(f"📊 Status: {self.total_polls} polls | "
                                  f"{rate:.1f}/sec | "
                                  f"Saved: ~{data_saved_mb:.1f}MB data")
                else:
                    consecutive_errors += 1
                    logger.warning(f"API error: {result.get('error', 'Unknown')}")
                    
                    # Check if it's a 403
                    if result.get('status') == 403:
                        logger.error("403 Forbidden - API access blocked")
                        logger.info("Switching to fallback mode...")
                        self.fallback_page_hunt()
                        break
                    
                    if consecutive_errors >= 3:
                        logger.warning("Multiple API failures, switching to fallback...")
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
                # Refresh immediately
                self.driver.refresh()
                
                # Then wait
                time.sleep(random.uniform(1, 2))
                
                if check_count % 10 == 0:
                    logger.info(f"Fallback check #{check_count}")

    def execute_purchase_from_api(self):
        """Execute purchase after API detection"""
        logger.info("⚡ Switching to purchase mode!")
        
        try:
            # Refresh to see tickets
            self.driver.refresh()
            
            # Find and click ticket
            ticket = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.ticket_selector))
            )
            self.execute_purchase(ticket)
            
        except Exception as e:
            logger.error(f"Failed to find ticket after API detection: {e}")
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
        ║      FANSALE HYBRID BOT - FIXED              ║
        ║                                              ║
        ║  ✓ Manual login (safer)                     ║
        ║  ✓ Proper API authentication                ║
        ║  ✓ Automatic 403 fallback                   ║
        ║  ✓ 99% less data usage                      ║
        ╚══════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_driver()
            
            # Manual login
            while not self.wait_for_manual_login():
                logger.warning("Please complete login...")
                time.sleep(2)
            
            # Start hunting with fixed auth
            self.hunt_hybrid_fixed()
            
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
