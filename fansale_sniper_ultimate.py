import os
import sys
import time
import json
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
Path("session").mkdir(exist_ok=True)

# --- Logging Configuration ---
log_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
file_handler = logging.FileHandler(f'logs/fansale_sniper_ultimate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
logger = logging.getLogger('FanSaleUltimate')
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

class FanSaleSniperUltimate:
    def __init__(self, config):
        self.config = config
        self.state = BotState.INITIALIZING
        self.driver = None
        self.last_session_check_time = 0
        self.session_check_interval = 300
        self.last_proxy_rotation = 0
        self.proxy_rotation_interval = 1800  # 30 minutes
        self.failed_checks = 0
        self.max_failed_checks = 10
        
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        if not self.email or not self.password:
            raise ValueError("FATAL: Missing FANSALE_EMAIL or FANSALE_PASSWORD in .env!")
        
        # Pre-cache selectors for maximum speed
        self.selectors = {
            'ticket': "div[data-qa='ticketToBuy']",
            'buy_button': "button[data-qa='buyNowButton']",
            'cookie_accept': "//button[contains(., 'ACCETTA TUTTI')]",
            'login_check': "//*[contains(text(), 'My fanSALE')] | //a[contains(@href, 'logout')]",
            'email_field': 'input[name="login_email"]',
            'password_field': 'input[name="login_password"]',
            'login_button': '#loginCustomerButton'
        }
        
        # Pre-compiled JavaScript for speed
        self.js_scripts = {
            'check_logged_in': """
                return !!(document.querySelector("*:contains('My fanSALE')") || 
                         document.querySelector("a[href*='logout']"));
            """,
            'check_ticket': f"""
                return !!document.querySelector("{self.selectors['ticket']}");
            """,
            'disable_animations': """
                const style = document.createElement('style');
                style.textContent = `*, *::before, *::after {{
                    animation-duration: 0s !important;
                    transition-duration: 0s !important;
                }}`;
                document.head.appendChild(style);
            """,
            'click_cookie': """
                const btn = document.querySelector("button:contains('ACCETTA TUTTI')");
                if (btn) btn.click();
            """
        }
        
        logger.info("FanSale Sniper Ultimate initialized with optimized settings")

    def run(self):
        """Main bot execution loop"""
        logger.info("🚀 Starting FanSale Sniper Ultimate...")
        try:
            while self.state not in [BotState.SUCCESS, BotState.ERROR]:
                handler = getattr(self, f'_handle_{self.state.value}', None)
                if handler:
                    handler()
                else:
                    logger.error(f"No handler for state: {self.state}")
                    self.state = BotState.ERROR
            
            if self.state == BotState.SUCCESS:
                logger.info("✅✅✅ TICKET SECURED! Browser will remain open for payment. ✅✅✅")
                self._save_success_data()
            else:
                logger.error("❌ Bot stopped due to an error.")
                
        except KeyboardInterrupt:
            logger.info("⏹️ Bot stopped by user.")
        finally:
            if self.driver and self.state == BotState.SUCCESS:
                logger.info("Keeping browser open for 10 minutes...")
                time.sleep(600)
            elif self.driver:
                self.driver.quit()

    def _setup_driver(self):
        """Set up optimized Chrome driver with maximum performance"""
        logger.info("Setting up ULTIMATE performance browser...")
        options = uc.ChromeOptions()
        
        # Performance preferences
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Disable images
            "profile.default_content_settings.popups": 2,
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream": 2,
                "media_stream_mic": 2,
                "media_stream_camera": 2,
                "automatic_downloads": 2,
                "plugins": 2,
            },
            # Reduce bandwidth usage for proxy
            "profile.default_content_settings.cookies": 1,
            "profile.block_third_party_cookies": True,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
        # Ultimate performance flags
        performance_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-gpu',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',
            '--disable-javascript-harmony-shipping',
            '--disable-webgl',
            '--disable-3d-apis',
            '--disable-flash-3d',
            '--disable-flash-stage3d',
            
            # Network optimizations
            '--aggressive-cache-discard',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-features=TranslateUI',
            '--disable-features=BlinkGenPropertyTrees',
            
            # Memory optimizations
            '--memory-pressure-off',
            '--max_old_space_size=4096',
            '--disable-features=RendererCodeIntegrity',
            '--disable-features=OptimizationGuideModelDownloading',
            
            # Disable logging for speed
            '--disable-logging',
            '--log-level=3',
            '--silent',
            
            # Additional speed optimizations
            '--disable-default-apps',
            '--disable-features=VizDisplayCompositor',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--disable-renderer-backgrounding',
            '--disable-sync',
            '--metrics-recording-only',
            '--no-first-run',
            '--password-store=basic',
            '--use-mock-keychain',
            '--disable-features=PasswordImport',
            '--disable-features=Chrome.BrowsingDataLifetimeManager'
        ]
        
        for arg in performance_args:
            options.add_argument(arg)
        
        # Profile persistence for session management
        profile_dir = Path("browser_profiles") / "fansale_ultimate"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # Proxy configuration with optimizations
        proxy_options = self._get_optimized_proxy_options()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(10)  # Aggressive timeout
        
        # Inject performance scripts immediately
        self.driver.execute_script(self.js_scripts['disable_animations'])
        
        logger.info("Ultimate performance browser ready!")

    def _get_optimized_proxy_options(self):
        """Get proxy configuration optimized for speed and bandwidth"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}',
                'no_proxy': 'localhost,127.0.0.1'  # Don't proxy local requests
            },
            'suppress_connection_errors': True,
            'connection_timeout': 10,
            'verify_ssl': False,  # Faster but less secure
            'request_storage_base_dir': None  # Don't store requests to save resources
        }

    def _is_logged_in(self):
        """Ultra-fast login check using cached JavaScript"""
        try:
            # First try the fastest JS method
            result = self.driver.execute_script(self.js_scripts['check_logged_in'])
            if result:
                return True
        except:
            pass
        
        # Fallback to reliable Selenium check
        try:
            self.driver.find_element(By.XPATH, self.selectors['login_check'])
            return True
        except NoSuchElementException:
            return False

    def _handle_cookie_popup(self):
        """Lightning-fast cookie acceptance"""
        try:
            # Try JS first (fastest)
            self.driver.execute_script(self.js_scripts['click_cookie'])
        except:
            # Fallback to Selenium
            try:
                btn = self.driver.find_element(By.XPATH, self.selectors['cookie_accept'])
                btn.click()
            except:
                pass  # No cookie banner

    def _save_session_cookies(self):
        """Save cookies for faster future logins"""
        try:
            cookies = self.driver.get_cookies()
            with open('session/cookies.json', 'w') as f:
                json.dump(cookies, f)
            logger.debug("Session cookies saved")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def _load_session_cookies(self):
        """Load saved cookies to skip login"""
        cookie_file = Path('session/cookies.json')
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
            time.sleep(1)
            return self._is_logged_in()
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def _handle_initializing(self):
        """Initialize bot and driver"""
        self._setup_driver()
        self.state = BotState.CHECKING_SESSION

    def _handle_checking_session(self):
        """Check if we have an active session"""
        logger.info("Checking for existing session...")
        
        # Try to load saved cookies first
        if self._load_session_cookies():
            logger.info("✅ Restored session from cookies!")
            self.state = BotState.MONITORING
            return
            
        # Otherwise navigate to main page
        self.driver.get("https://www.fansale.it/fansale/")
        self._handle_cookie_popup()
        
        if self._is_logged_in():
            logger.info("✅ Already logged in!")
            self._save_session_cookies()
            self.state = BotState.MONITORING
        else:
            logger.info("No active session, need to login")
            self.state = BotState.LOGGING_IN

    def _handle_logging_in(self):
        """Perform ultra-fast login"""
        try:
            logger.info("Executing turbo login...")
            self.driver.get("https://www.fansale.it/fansale/login.htm")
            self._handle_cookie_popup()
            
            # Lightning-fast field filling and submission
            self.driver.execute_script(f"""
                const email = document.querySelector('{self.selectors['email_field']}');
                const password = document.querySelector('{self.selectors['password_field']}');
                const button = document.querySelector('{self.selectors['login_button']}');
                
                if (email) email.value = arguments[0];
                if (password) password.value = arguments[1];
                if (button) button.click();
            """, self.email, self.password)
            
            # Wait for login
            WebDriverWait(self.driver, 10).until(lambda d: self._is_logged_in())
            logger.info("✅ Login successful!")
            self._save_session_cookies()
            self.state = BotState.MONITORING
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.state = BotState.ERROR

    def _handle_monitoring(self):
        """Ultra-optimized ticket monitoring"""
        logger.info("🎯 ULTIMATE MONITORING ACTIVE!")
        
        # Navigate to target URL only once
        if self.driver.current_url != self.config['target_url']:
            self.driver.get(self.config['target_url'])
            self._handle_cookie_popup()
            time.sleep(1)  # Let page stabilize
        
        self.last_session_check_time = time.time()
        check_count = 0
        consecutive_errors = 0
        
        while self.state == BotState.MONITORING:
            try:
                # Periodic session check
                if time.time() - self.last_session_check_time > self.session_check_interval:
                    if not self._is_logged_in():
                        logger.warning("Session expired! Re-authenticating...")
                        self.state = BotState.CHECKING_SESSION
                        return
                    self.last_session_check_time = time.time()
                
                # Proxy rotation check (saves bandwidth)
                if time.time() - self.last_proxy_rotation > self.proxy_rotation_interval:
                    logger.info("Rotating proxy session...")
                    self.driver.delete_all_cookies()
                    self._load_session_cookies()
                    self.last_proxy_rotation = time.time()
                
                check_count += 1
                
                # Ultra-fast JavaScript ticket check
                ticket_found = self.driver.execute_script(self.js_scripts['check_ticket'])
                
                if ticket_found:
                    logger.info(f"🎫 TICKET FOUND after {check_count} checks!")
                    self.state = BotState.PURCHASING
                    consecutive_errors = 0
                else:
                    # Smart refresh strategy
                    if check_count % 5 == 0:  # Full refresh every 5 checks
                        self.driver.refresh()
                        time.sleep(0.5)
                    else:  # Otherwise just wait
                        time.sleep(self.config.get('check_interval', 0.3))
                    
                    consecutive_errors = 0
                    
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Monitoring error #{consecutive_errors}: {e}")
                
                if consecutive_errors >= 3:
                    logger.warning("Multiple errors, performing recovery...")
                    self.driver.get(self.config['target_url'])
                    time.sleep(2)
                    consecutive_errors = 0

    def _handle_purchasing(self):
        """Lightning-fast ticket purchase execution"""
        logger.info("⚡ EXECUTING INSTANT PURCHASE!")
        
        try:
            # Method 1: Direct JavaScript execution (fastest)
            purchase_result = self.driver.execute_script(f"""
                // Click ticket
                const ticket = document.querySelector("{self.selectors['ticket']}");
                if (ticket) {{
                    ticket.click();
                    
                    // Wait a moment then click buy button
                    setTimeout(() => {{
                        const buyBtn = document.querySelector("{self.selectors['buy_button']}");
                        if (buyBtn) {{
                            buyBtn.click();
                            return true;
                        }}
                    }}, 500);
                }}
                return false;
            """)
            
            # Give JS time to execute
            time.sleep(1)
            
            # Verify purchase button was clicked
            try:
                # Check if we're past the ticket selection
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "div.checkout, div.cart, div.payment"))
                )
                self.state = BotState.SUCCESS
                return
            except:
                pass
            
            # Method 2: Selenium fallback
            logger.info("Using Selenium fallback for purchase...")
            ticket = self.driver.find_element(By.CSS_SELECTOR, self.selectors['ticket'])
            ticket.click()
            
            buy_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors['buy_button']))
            )
            buy_button.click()
            
            self.state = BotState.SUCCESS
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            self.failed_checks += 1
            
            if self.failed_checks < self.max_failed_checks:
                logger.warning(f"Returning to monitoring... ({self.failed_checks}/{self.max_failed_checks})")
                self.driver.get(self.config['target_url'])
                self.state = BotState.MONITORING
            else:
                logger.error("Too many failed purchase attempts!")
                self.state = BotState.ERROR

    def _handle_error(self):
        """Handle error state"""
        logger.error("Bot is in error state")
        
    def _save_success_data(self):
        """Save success data for analysis"""
        try:
            success_data = {
                'timestamp': datetime.now().isoformat(),
                'url': self.driver.current_url,
                'title': self.driver.title,
                'config': self.config
            }
            
            success_file = Path('logs/successes.json')
            existing_data = []
            
            if success_file.exists():
                with open(success_file, 'r') as f:
                    existing_data = json.load(f)
            
            existing_data.append(success_data)
            
            with open(success_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
            logger.info("Success data saved!")
            
        except Exception as e:
            logger.error(f"Failed to save success data: {e}")


def load_config():
    """Load configuration with defaults"""
    config_path = Path("config.yaml")
    
    default_config = {
        'target_url': os.getenv('FANSALE_TARGET_URL', 
                               'https://www.fansale.it/fansale/tickets/'),
        'check_interval': 0.3,  # 300ms between checks
        'enable_notifications': False,
        'save_screenshots': False
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Failed to load config.yaml: {e}")
    
    return default_config


def main():
    """Main entry point"""
    try:
        config = load_config()
        bot = FanSaleSniperUltimate(config)
        bot.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
