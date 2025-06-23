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
Path("data/cookies").mkdir(exist_ok=True, parents=True)

# Logging
logger = logging.getLogger('FanSaleCookieSolution')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class CookieAwareFanSaleBot:
    """
    Enhanced bot that properly handles Akamai _abck cookie generation.
    Based on research findings about sensor data and cookie preservation.
    """
    
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
        
        # Cookie management
        self.abck_cookie = None
        self.cookie_file = Path("data/cookies/fansale_abck.json")
        self.cookie_valid = False
        
        self.driver = None

    def setup_driver(self):
        """Setup browser with anti-detection"""
        logger.info("🚀 Setting up cookie-aware browser...")
        
        options = uc.ChromeOptions()
        
        # Load images for better trust score
        prefs = {
            "profile.managed_default_content_settings.images": 1,  # Load images
            "profile.managed_default_content_settings.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Anti-detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Persistent profile for cookie storage
        profile_dir = Path("browser_profiles") / "fansale_cookie_aware"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
        
        logger.info("✅ Browser ready")

    def check_akamai_cookies(self):
        """Check for Akamai cookies and their validity"""
        cookies = self.driver.get_cookies()
        
        for cookie in cookies:
            if cookie['name'] == '_abck':
                self.abck_cookie = cookie['value']
                # Check if cookie is invalidated (ends with ~0~-1~-1)
                if self.abck_cookie.endswith('~0~-1~-1'):
                    logger.warning("⚠️ _abck cookie is invalidated!")
                    return False
                else:
                    logger.info(f"✅ Valid _abck cookie found: {self.abck_cookie[:20]}...")
                    return True
        
        logger.warning("❌ No _abck cookie found")
        return False

    def save_cookies(self):
        """Save cookies to file for reuse"""
        cookies = self.driver.get_cookies()
        with open(self.cookie_file, 'w') as f:
            json.dump(cookies, f)
        logger.info("💾 Cookies saved")

    def load_cookies(self):
        """Load cookies from file if they exist"""
        if self.cookie_file.exists():
            try:
                with open(self.cookie_file, 'r') as f:
                    cookies = json.load(f)
                
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                
                logger.info("📂 Cookies loaded from file")
                return True
            except:
                logger.warning("Failed to load cookies")
        return False

    def inject_cookie_aware_monitor(self):
        """Inject monitor that uses XMLHttpRequest to preserve cookies"""
        monitor_script = """
        window.cookieAwareMonitor = {
            abckCookie: null,
            requestCount: 0,
            
            // Get current _abck cookie
            getAbckCookie: function() {
                const cookies = document.cookie.split(';');
                for (let cookie of cookies) {
                    const [name, value] = cookie.trim().split('=');
                    if (name === '_abck') {
                        return value;
                    }
                }
                return null;
            },
            
            // Check if cookie is valid
            isCookieValid: function() {
                const abck = this.getAbckCookie();
                if (!abck) return false;
                
                // Cookie is invalid if it ends with ~0~-1~-1
                return !abck.endsWith('~0~-1~-1');
            },
            
            // Make API call using XMLHttpRequest (preserves cookies better)
            checkAPIWithCookies: async function(url) {
                return new Promise((resolve) => {
                    const xhr = new XMLHttpRequest();
                    
                    xhr.onreadystatechange = function() {
                        if (xhr.readyState === 4) {
                            const cookieValid = window.cookieAwareMonitor.isCookieValid();
                            
                            if (xhr.status === 200) {
                                try {
                                    const data = JSON.parse(xhr.responseText);
                                    resolve({
                                        success: true,
                                        data: data,
                                        hasTickets: Array.isArray(data) && data.length > 0,
                                        status: xhr.status,
                                        cookieValid: cookieValid
                                    });
                                } catch (e) {
                                    resolve({
                                        success: false,
                                        error: 'Parse error',
                                        status: xhr.status,
                                        cookieValid: cookieValid
                                    });
                                }
                            } else {
                                resolve({
                                    success: false,
                                    error: `HTTP ${xhr.status}`,
                                    status: xhr.status,
                                    cookieValid: cookieValid
                                });
                            }
                        }
                    };
                    
                    // Use XMLHttpRequest with credentials
                    xhr.open('GET', url, true);
                    xhr.withCredentials = true;  // Important for cookie handling
                    
                    // Headers that preserve session context
                    xhr.setRequestHeader('Accept', 'application/json, text/plain, */*');
                    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                    
                    this.requestCount++;
                    xhr.send();
                });
            },
            
            // Generate sensor-like activity
            generateSensorActivity: function() {
                // Simulate mouse movement
                const mouseEvent = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight,
                    bubbles: true
                });
                document.dispatchEvent(mouseEvent);
                
                // Simulate scroll
                if (Math.random() > 0.5) {
                    window.scrollBy(0, Math.random() * 100 - 50);
                }
                
                // Simulate keyboard presence
                const keyEvent = new KeyboardEvent('keydown', {
                    key: 'Shift',
                    bubbles: true
                });
                document.dispatchEvent(keyEvent);
                
                // Touch screen coordinates (mobile simulation)
                if (window.TouchEvent && Math.random() > 0.7) {
                    const touchEvent = new TouchEvent('touchstart', {
                        touches: [new Touch({
                            identifier: Date.now(),
                            target: document.body,
                            clientX: Math.random() * window.innerWidth,
                            clientY: Math.random() * window.innerHeight
                        })]
                    });
                    document.dispatchEvent(touchEvent);
                }
            }
        };
        
        // Generate sensor activity periodically
        setInterval(() => window.cookieAwareMonitor.generateSensorActivity(), 2000);
        
        // Monitor cookie status
        setInterval(() => {
            const valid = window.cookieAwareMonitor.isCookieValid();
            console.log('Cookie valid:', valid);
        }, 5000);
        """
        
        self.driver.execute_script(monitor_script)

    def build_valid_cookie_session(self):
        """Build a session with valid _abck cookie through natural browsing"""
        logger.info("🍪 Building valid cookie session...")
        
        # Step 1: Visit homepage
        self.driver.get(self.base_url)
        time.sleep(3)
        
        # Step 2: Natural browsing pattern
        browsing_actions = [
            lambda: self.driver.get(f"{self.base_url}/fansale/tickets/concert"),
            lambda: self.driver.get(f"{self.base_url}/fansale/tickets/sport"),
            lambda: self.driver.execute_script("window.scrollTo(0, 500);"),
            lambda: self.driver.execute_script("window.scrollTo(0, 0);"),
        ]
        
        # Perform 3-5 random actions
        for _ in range(random.randint(3, 5)):
            action = random.choice(browsing_actions)
            action()
            time.sleep(random.uniform(2, 4))
            
            # Check if we got a valid cookie
            if self.check_akamai_cookies():
                logger.info("✅ Valid cookie obtained through browsing!")
                self.save_cookies()
                return True
        
        # Step 3: Visit target page
        self.driver.get(self.target_url)
        time.sleep(3)
        
        # Step 4: Interact with page to trigger sensor data collection
        self.driver.execute_script("""
            // Trigger various events that Akamai monitors
            for (let i = 0; i < 10; i++) {
                setTimeout(() => {
                    // Mouse movement
                    document.dispatchEvent(new MouseEvent('mousemove', {
                        clientX: Math.random() * window.innerWidth,
                        clientY: Math.random() * window.innerHeight
                    }));
                    
                    // Scroll
                    if (i % 3 === 0) {
                        window.scrollBy(0, Math.random() * 200 - 100);
                    }
                }, i * 500);
            }
        """)
        
        time.sleep(5)
        
        # Final check
        return self.check_akamai_cookies()

    def hunt_with_cookie_awareness(self):
        """Hunt using cookie-aware approach"""
        logger.info("🎯 COOKIE-AWARE HUNT MODE!")
        
        # Try to load existing cookies first
        self.driver.get(self.base_url)
        if self.load_cookies():
            self.driver.refresh()
            time.sleep(2)
            
            if self.check_akamai_cookies():
                logger.info("✅ Loaded valid cookies from file!")
            else:
                logger.info("🔄 Loaded cookies invalid, rebuilding...")
                self.build_valid_cookie_session()
        else:
            # Build new valid session
            self.build_valid_cookie_session()
        
        # Navigate to target
        self.driver.get(self.target_url)
        time.sleep(2)
        
        # Inject cookie-aware monitor
        self.inject_cookie_aware_monitor()
        
        # Start monitoring
        consecutive_fails = 0
        check_count = 0
        
        while True:
            try:
                check_count += 1
                
                # Build API URL
                cache_buster = int(time.time() * 1000) + random.randint(0, 999)
                api_url = f"{self.api_endpoint}?_={cache_buster}"
                
                # Make cookie-aware API call
                result = self.driver.execute_script(f"""
                    return await window.cookieAwareMonitor.checkAPIWithCookies('{api_url}');
                """)
                
                # Check cookie validity
                if not result.get('cookieValid', False):
                    logger.error("❌ Cookie became invalid! Rebuilding session...")
                    self.build_valid_cookie_session()
                    self.inject_cookie_aware_monitor()
                    consecutive_fails = 0
                    continue
                
                if result['success']:
                    consecutive_fails = 0
                    
                    if result['hasTickets']:
                        logger.info("🎫 TICKETS FOUND!")
                        self.execute_purchase()
                        break
                    
                    if check_count % 10 == 0:
                        logger.info(f"✅ Progress: {check_count} checks with valid cookie")
                        self.save_cookies()  # Periodically save good cookies
                else:
                    consecutive_fails += 1
                    
                    if result.get('status') == 403:
                        logger.error(f"⚠️ 403 error despite valid cookie!")
                        
                        if consecutive_fails >= 3:
                            logger.info("🔄 Rebuilding session due to 403s...")
                            self.driver.delete_all_cookies()
                            self.build_valid_cookie_session()
                            self.inject_cookie_aware_monitor()
                            consecutive_fails = 0
                
                # Smart timing based on success
                if consecutive_fails == 0:
                    wait_time = random.uniform(2, 3)
                else:
                    wait_time = random.uniform(5, 10)
                
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)

    def execute_purchase(self):
        """Execute purchase after detection"""
        logger.info("💳 EXECUTING PURCHASE!")
        
        try:
            # Save current cookies for future use
            self.save_cookies()
            
            # Refresh to see tickets
            self.driver.refresh()
            
            # Find and click ticket
            ticket = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.ticket_selector))
            )
            ticket.click()
            
            # Buy button
            buy_button = WebDriverWait(self.driver, 10).until(
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
        
        # After login, save cookies
        self.save_cookies()
        
        return True

    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════╗
        ║    COOKIE-AWARE FANSALE BOT                 ║
        ║                                              ║
        ║  Based on research findings:                 ║
        ║  ✓ _abck cookie preservation                ║
        ║  ✓ XMLHttpRequest for better cookies        ║
        ║  ✓ Sensor activity generation               ║
        ║  ✓ Cookie validation checks                 ║
        ║  ✓ Session rebuilding on invalidation       ║
        ╚══════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_driver()
            self.manual_login()
            self.hunt_with_cookie_awareness()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    bot = CookieAwareFanSaleBot()
    bot.run()
