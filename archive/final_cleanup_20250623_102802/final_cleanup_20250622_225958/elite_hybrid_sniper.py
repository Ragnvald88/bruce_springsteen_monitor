import os
import sys
import time
import json
import random
import hashlib
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service

# --- Setup ---
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# --- Logging ---
logger = logging.getLogger('EliteSniper')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class EliteFanSaleBot:
    """
    Elite FanSale Bot - Hybrid Approach
    Combines browser automation with smart detection patterns
    """
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Smart timing patterns (mimics human behavior)
        self.check_patterns = [
            # (min_seconds, max_seconds, checks_in_burst)
            (0.8, 1.5, 2),    # Quick double-check
            (3.0, 5.0, 1),    # Pause
            (1.0, 2.0, 3),    # Moderate burst
            (4.0, 7.0, 1),    # Longer pause
            (0.5, 1.2, 2),    # Fast burst
            (2.5, 4.5, 1),    # Medium pause
        ]
        self.current_pattern = 0
        
        # Detection avoidance
        self.last_mouse_move = 0
        self.page_hash = None
        self.no_change_count = 0
        
        self.driver = None

    def setup_driver(self):
        """Setup browser with maximum stealth and minimum data usage"""
        logger.info("🚀 Initializing elite browser...")
        
        options = uc.ChromeOptions()
        
        # Critical data-saving preferences
        prefs = {
            # Block images completely
            "profile.managed_default_content_settings.images": 2,
            # Block other resource-heavy content
            "profile.default_content_setting_values": {
                "media_stream": 2,
                "media_stream_mic": 2,
                "media_stream_camera": 2,
                "notifications": 2,
                "automatic_downloads": 2,
            },
            # Aggressive cache settings
            "disk-cache-size": 4096,
            "media-cache-size": 4096,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Performance flags
        flags = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-gpu',
            '--disable-logging',
            '--disable-plugins',
            '--disable-images',
            '--disable-javascript-harmony-shipping',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-features=TranslateUI',
            '--disable-features=OptimizationGuideModelDownloading',
            '--aggressive-cache-discard',
            '--memory-pressure-off',
        ]
        
        for flag in flags:
            options.add_argument(flag)
        
        # Persistent profile
        profile_dir = Path("browser_profiles") / "elite_fansale"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # IPRoyal proxy
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(8)
        
        # Inject monitoring scripts
        self._inject_monitor_script()
        
        logger.info("✅ Elite browser ready")

    def _get_proxy_config(self):
        """Configure IPRoyal proxy with request filtering"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        def request_interceptor(request):
            # Block unnecessary resources to save proxy data
            block_patterns = [
                '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
                'font', '.css', 'analytics', 'google', 'facebook',
                'tracking', 'advertisement', '.mp4', '.webm'
            ]
            
            for pattern in block_patterns:
                if pattern in request.url.lower():
                    request.abort()
                    
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': request_interceptor,
            'suppress_connection_errors': True
        }

    def _inject_monitor_script(self):
        """Inject JavaScript for ultra-fast ticket detection"""
        monitor_script = """
        window.ticketMonitor = {
            lastCheck: null,
            found: false,
            
            check: function() {
                const ticket = document.querySelector('div[data-qa="ticketToBuy"]');
                if (ticket && !this.found) {
                    this.found = true;
                    // Create a visible flag for Selenium
                    document.body.setAttribute('data-ticket-found', 'true');
                    return true;
                }
                return false;
            },
            
            getPageHash: function() {
                // Quick hash of ticket area content
                const area = document.querySelector('.ticket-listings, .event-tickets, main');
                return area ? area.textContent.length : 0;
            }
        };
        
        // Run check every 200ms (client-side, no network usage)
        setInterval(() => window.ticketMonitor.check(), 200);
        """
        
        try:
            self.driver.execute_script(monitor_script)
        except:
            pass

    def login(self):
        """Fast login with session persistence"""
        logger.info("🔐 Logging in...")
        
        # Try loading saved session first
        if self._load_session():
            logger.info("✅ Session restored!")
            return True
            
        # Otherwise do fresh login
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        time.sleep(1)
        
        # Handle cookies
        try:
            self.driver.execute_script("""
                const btn = document.querySelector('button:contains("ACCETTA")');
                if (btn) btn.click();
            """)
        except:
            pass
        
        # Fast field injection
        self.driver.execute_script(f"""
            document.querySelector('input[name="login_email"]').value = '{self.email}';
            document.querySelector('input[name="login_password"]').value = '{self.password}';
            document.querySelector('#loginCustomerButton').click();
        """)
        
        # Wait for login
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'My fanSALE')]"))
            )
            logger.info("✅ Login successful!")
            self._save_session()
            return True
        except:
            logger.error("❌ Login failed!")
            return False

    def hunt_tickets(self):
        """Smart ticket hunting with human-like patterns"""
        logger.info(f"🎯 Starting hunt: {self.target_url}")
        
        self.driver.get(self.target_url)
        time.sleep(2)  # Let page stabilize
        
        # Inject monitor script on target page
        self._inject_monitor_script()
        
        check_count = 0
        pattern_checks = 0
        
        while True:
            try:
                # Get current pattern timing
                min_wait, max_wait, burst_count = self.check_patterns[self.current_pattern]
                
                # Quick JS check (no network request)
                ticket_found = self.driver.execute_script("""
                    return document.body.getAttribute('data-ticket-found') === 'true';
                """)
                
                if ticket_found:
                    logger.info(f"🎫 TICKET FOUND after {check_count} checks!")
                    self.execute_purchase()
                    break
                
                # Check page hash for changes
                current_hash = self.driver.execute_script("return window.ticketMonitor.getPageHash();")
                
                if current_hash == self.page_hash:
                    self.no_change_count += 1
                    
                    # Smart refresh strategy
                    if self.no_change_count >= 10:  # ~30-50 seconds of no changes
                        logger.info("📄 No changes detected, refreshing...")
                        self.smart_refresh()
                        self.no_change_count = 0
                else:
                    self.page_hash = current_hash
                    self.no_change_count = 0
                
                # Human-like mouse movement occasionally
                if time.time() - self.last_mouse_move > random.uniform(15, 30):
                    self.human_mouse_move()
                    self.last_mouse_move = time.time()
                
                # Pattern-based waiting
                wait_time = random.uniform(min_wait, max_wait)
                time.sleep(wait_time)
                
                check_count += 1
                pattern_checks += 1
                
                # Move to next pattern after burst
                if pattern_checks >= burst_count:
                    self.current_pattern = (self.current_pattern + 1) % len(self.check_patterns)
                    pattern_checks = 0
                    logger.info(f"⏱️ Pattern switch (Check #{check_count})")
                
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                time.sleep(5)
                self.driver.refresh()

    def smart_refresh(self):
        """Intelligent refresh that saves bandwidth"""
        # Method 1: Soft refresh (just ticket area)
        try:
            self.driver.execute_script("""
                // Find and click any refresh button
                const refreshBtn = document.querySelector('[class*="refresh"], [class*="reload"]');
                if (refreshBtn) {
                    refreshBtn.click();
                    return true;
                }
                
                // Or trigger AJAX refresh if available
                if (window.location.reload) {
                    window.location.reload(false);  // From cache
                    return true;
                }
                
                return false;
            """)
        except:
            # Fallback to standard refresh
            self.driver.refresh()
        
        time.sleep(1)
        self._inject_monitor_script()  # Re-inject our monitor

    def human_mouse_move(self):
        """Simulate human mouse movement"""
        try:
            self.driver.execute_script("""
                // Move mouse in natural curve
                const event = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight,
                    bubbles: true
                });
                document.dispatchEvent(event);
            """)
        except:
            pass

    def execute_purchase(self):
        """Lightning-fast ticket purchase"""
        logger.info("⚡ EXECUTING INSTANT PURCHASE!")
        
        try:
            # Click ticket
            self.driver.execute_script("""
                const ticket = document.querySelector('div[data-qa="ticketToBuy"]');
                if (ticket) ticket.click();
            """)
            
            # Wait for buy button
            buy_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="buyNowButton"]'))
            )
            buy_btn.click()
            
            logger.info("✅ TICKET SECURED! Complete payment manually.")
            
            # Keep browser open
            while True:
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"❌ Purchase failed: {e}")

    def _save_session(self):
        """Save cookies for faster future runs"""
        cookies = self.driver.get_cookies()
        with open('browser_profiles/elite_cookies.json', 'w') as f:
            json.dump(cookies, f)

    def _load_session(self):
        """Load saved session"""
        cookie_file = Path('browser_profiles/elite_cookies.json')
        if not cookie_file.exists():
            return False
            
        try:
            self.driver.get("https://www.fansale.it")
            
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
                    
            self.driver.refresh()
            
            # Check if logged in
            return self.driver.execute_script("""
                return !!(document.querySelector('*:contains("My fanSALE")') || 
                         document.querySelector('a[href*="logout"]'));
            """)
        except:
            return False

    def run(self):
        """Main execution"""
        try:
            self.setup_driver()
            self.login()
            self.hunt_tickets()
        except KeyboardInterrupt:
            logger.info("🛑 Stopped by user")
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    # Save credentials to .env first
    env_path = Path('.env')
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write('FANSALE_EMAIL="ronaldhoogenberg@hotmail.com"\n')
            f.write('FANSALE_PASSWORD="Hagappoq221!"\n')
            f.write('# Add your IPRoyal proxy details below:\n')
            f.write('IPROYAL_USERNAME=""\n')
            f.write('IPROYAL_PASSWORD=""\n')
            f.write('IPROYAL_HOSTNAME=""\n')
            f.write('IPROYAL_PORT=""\n')
    
    bot = EliteFanSaleBot()
    bot.run()
