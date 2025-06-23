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
logger = logging.getLogger('FanSaleAdvanced')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class AdvancedFanSaleBot:
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        # URLs
        self.base_url = "https://www.fansale.it"
        self.api_endpoint = f"{self.base_url}/json/offers/17844388"
        self.target_url = f"{self.base_url}/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Selectors
        self.ticket_selector = "div[data-qa='ticketToBuy']"
        self.buy_button_selector = "button[data-qa='buyNowButton']"
        
        # Anti-detection measures
        self.api_call_count = 0
        self.last_api_success = None
        self.session_age = 0
        self.max_api_calls_per_session = 50  # Rotate session after this
        
        # Timing patterns (longer initial delays)
        self.initial_wait = random.uniform(5, 10)  # Wait before first API call
        self.api_patterns = [
            (2.0, 4.0),   # Slower between calls
            (3.0, 5.0),   
            (2.5, 4.5),
            (4.0, 6.0),
        ]
        
        self.driver = None

    def setup_driver(self):
        """Setup with focus on legitimacy"""
        logger.info("🚀 Setting up advanced browser...")
        
        options = uc.ChromeOptions()
        
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
        
        # Profile
        profile_dir = Path("browser_profiles") / "fansale_advanced"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Proxy
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(20)
        
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
            }
        }

    def inject_advanced_monitor(self):
        """Inject monitor that mimics real page behavior"""
        monitor_script = """
        window.apiMonitor = {
            callCount: 0,
            lastCall: 0,
            
            // Mimic how the actual page might call the API
            checkAPI: async function(url) {
                // Add realistic delay between calls
                const now = Date.now();
                const timeSinceLastCall = now - this.lastCall;
                
                if (timeSinceLastCall < 1000) {
                    // Too fast, wait
                    await new Promise(r => setTimeout(r, 1000 - timeSinceLastCall));
                }
                
                try {
                    // Set proper headers like the real page would
                    const response = await fetch(url, {
                        method: 'GET',
                        credentials: 'include',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache',
                            'Referer': window.location.href,
                            'X-Requested-With': 'XMLHttpRequest',
                            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                            'sec-fetch-dest': 'empty',
                            'sec-fetch-mode': 'cors',
                            'sec-fetch-site': 'same-origin'
                        }
                    });
                    
                    this.callCount++;
                    this.lastCall = now;
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
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
                        status: error.message.includes('HTTP') ? 
                            parseInt(error.message.match(/HTTP (\d+)/)[1]) : 0
                    };
                }
            },
            
            // Simulate page activity
            simulateActivity: function() {
                // Random scrolls
                if (Math.random() > 0.7) {
                    window.scrollBy(0, Math.random() * 100 - 50);
                }
                
                // Random mouse movements
                const event = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            }
        };
        
        // Periodically simulate activity
        setInterval(() => window.apiMonitor.simulateActivity(), 3000);
        """
        
        self.driver.execute_script(monitor_script)

    def establish_page_context(self):
        """Establish legitimate page context before API calls"""
        logger.info("📄 Establishing page context...")
        
        # Navigate to main page first
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Navigate to event page
        self.driver.get(self.target_url)
        time.sleep(3)
        
        # Simulate some page interaction
        self.driver.execute_script("""
            // Scroll around a bit
            window.scrollTo(0, 300);
            setTimeout(() => window.scrollTo(0, 0), 1000);
            
            // Click somewhere neutral
            const body = document.body;
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                clientX: 100,
                clientY: 100
            });
            body.dispatchEvent(clickEvent);
        """)
        
        logger.info(f"⏳ Waiting {self.initial_wait:.1f}s before starting API calls...")
        time.sleep(self.initial_wait)

    def hunt_with_anti_honeypot(self):
        """Hunt with anti-honeypot measures"""
        logger.info("🎯 ADVANCED HUNT MODE!")
        
        # Establish context first
        self.establish_page_context()
        
        # Inject monitor
        self.inject_advanced_monitor()
        
        consecutive_403s = 0
        pattern_index = 0
        
        while True:
            try:
                self.api_call_count += 1
                
                # Check if we should rotate session
                if self.api_call_count >= self.max_api_calls_per_session:
                    logger.warning("🔄 Rotating session to avoid detection...")
                    self.rotate_session()
                    continue
                
                # Build URL with cache buster
                cache_buster = int(time.time() * 1000) + random.randint(0, 999)
                api_url = f"{self.api_endpoint}?_={cache_buster}"
                
                # Make API call
                result = self.driver.execute_script(f"""
                    return await window.apiMonitor.checkAPI('{api_url}');
                """)
                
                if result['success']:
                    consecutive_403s = 0
                    
                    if result['hasTickets']:
                        logger.info("🎫 TICKETS FOUND!")
                        self.execute_purchase()
                        break
                    
                    # Log periodic status
                    if self.api_call_count % 20 == 0:
                        logger.info(f"📊 Status: {self.api_call_count} API calls made")
                        
                else:
                    if result.get('status') == 403:
                        consecutive_403s += 1
                        logger.warning(f"⚠️ 403 error #{consecutive_403s}")
                        
                        if consecutive_403s >= 3:
                            logger.error("🚨 Multiple 403s - Honeypot detected!")
                            
                            # Try recovery strategies
                            if consecutive_403s == 3:
                                logger.info("Strategy 1: Longer wait...")
                                time.sleep(30)
                            elif consecutive_403s == 5:
                                logger.info("Strategy 2: Page refresh...")
                                self.driver.refresh()
                                time.sleep(5)
                                self.inject_advanced_monitor()
                            elif consecutive_403s >= 7:
                                logger.info("Strategy 3: Full session rotation...")
                                self.rotate_session()
                                consecutive_403s = 0
                    else:
                        logger.error(f"API error: {result.get('error')}")
                
                # Human-like timing
                min_wait, max_wait = self.api_patterns[pattern_index % len(self.api_patterns)]
                wait_time = random.uniform(min_wait, max_wait)
                
                # Add extra delay if we're getting 403s
                if consecutive_403s > 0:
                    wait_time *= (1 + consecutive_403s * 0.5)
                
                time.sleep(wait_time)
                pattern_index += 1
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)

    def rotate_session(self):
        """Rotate session by clearing cookies and re-establishing context"""
        logger.info("🔄 Rotating session...")
        
        # Clear all cookies
        self.driver.delete_all_cookies()
        
        # Navigate away and back
        self.driver.get("about:blank")
        time.sleep(2)
        
        # Re-establish context
        self.api_call_count = 0
        self.establish_page_context()
        self.inject_advanced_monitor()

    def execute_purchase(self):
        """Execute purchase after API detection"""
        logger.info("💳 EXECUTING PURCHASE!")
        
        try:
            # Refresh to see tickets
            self.driver.refresh()
            
            # Find and click ticket
            ticket = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.ticket_selector))
            )
            ticket.click()
            
            # Buy button
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.buy_button_selector))
            )
            buy_button.click()
            
            logger.info("✅ TICKET IN CART!")
            input("\nPress Enter to close...")
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")

    def manual_login(self):
        """Manual login for safety"""
        logger.info("🔐 Manual login required")
        
        self.driver.get(f"{self.base_url}/fansale/login.htm")
        
        print(f"\n📋 Login with:")
        print(f"Email: {self.email}")
        print(f"Password: {'*' * len(self.password)}")
        
        input("\n✋ Press Enter after login...")
        
        return True

    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════╗
        ║      ADVANCED FANSALE BOT                    ║
        ║                                              ║
        ║  ✓ Anti-honeypot measures                   ║
        ║  ✓ Session rotation                         ║
        ║  ✓ Proper headers & context                 ║
        ║  ✓ Recovery strategies                      ║
        ╚══════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_driver()
            self.manual_login()
            self.hunt_with_anti_honeypot()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    bot = AdvancedFanSaleBot()
    bot.run()
