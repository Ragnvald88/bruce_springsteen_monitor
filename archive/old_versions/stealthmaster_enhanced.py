#!/usr/bin/env python3
"""
StealthMaster Enhanced - Advanced Ticket Reservation Bot with Maximum Stealth
Enhanced version with comprehensive anti-detection measures
"""

import os
import sys
import time
import json
import logging
import random
import traceback
import zipfile
import tempfile
import numpy as np
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Python 3.12+ compatibility fix
if sys.version_info >= (3, 12):
    try:
        import setuptools._distutils_hack
        setuptools._distutils_hack.ensure_shim()
    except ImportError:
        pass

import yaml
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Import our custom modules
from notifications import Notifier
from captcha_solver import CaptchaSolver
from stealth_improvements import StealthEnhancements

# Load environment variables
load_dotenv()

# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("session").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# Configure logging
log_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(
    f'logs/stealthmaster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

# Configure root logger
logger = logging.getLogger('StealthMaster')
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class BotState(Enum):
    """Enumeration of possible bot states"""
    INITIALIZING = "initializing"
    LOGGING_IN = "logging_in"
    MONITORING = "monitoring"
    RESERVING = "reserving"
    BLOCKED = "blocked"
    SOLVING_CAPTCHA = "solving_captcha"
    ERROR = "error"
    SUCCESS = "success"


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load and validate configuration from YAML file"""
    logger.debug(f"Loading configuration from {config_path}")
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Validate required fields
        required_fields = ['target', 'browser', 'monitoring']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in config: {field}")
        
        # Set defaults
        config.setdefault('browser', {}).setdefault('headless', False)
        config.setdefault('browser', {}).setdefault('window_size', [1920, 1080])
        config.setdefault('browser', {}).setdefault('use_persistent_profile', True)
        config.setdefault('monitoring', {}).setdefault('check_interval', 5)
        config.setdefault('monitoring', {}).setdefault('max_tickets', 4)
        config.setdefault('anti_detection', {}).setdefault('human_typing', True)
        config.setdefault('anti_detection', {}).setdefault('mouse_movements', True)
        config.setdefault('anti_detection', {}).setdefault('random_delays', True)
        
        logger.info("Configuration loaded successfully")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        raise


class StealthMasterEnhanced:
    """Enhanced bot class with advanced anti-detection measures"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the StealthMaster bot"""
        self.config = config
        self.state = BotState.INITIALIZING
        self.driver: Optional[webdriver.Chrome] = None
        self.stealth = StealthEnhancements()
        
        # Extract credentials from environment
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Missing FANSALE_EMAIL or FANSALE_PASSWORD in environment")
        
        # Track last login check time
        self.last_login_check = datetime.now()
        self.login_check_interval = 300  # 5 minutes in seconds
        
        # Extract proxy settings if available
        self.proxy_username = os.getenv('IPROYAL_USERNAME')
        self.proxy_password = os.getenv('IPROYAL_PASSWORD')
        self.proxy_hostname = os.getenv('IPROYAL_HOSTNAME')
        self.proxy_port = os.getenv('IPROYAL_PORT')
        
        # Bot statistics
        self.checks_performed = 0
        self.tickets_reserved = 0
        self.consecutive_failures = 0
        self.last_success_time = None
        
        # Adaptive delay settings with human variance
        base_interval = config['monitoring']['check_interval']
        self.current_delay = base_interval + random.uniform(0, 2)
        self.min_delay = 3
        self.max_delay = 60
        
        # Initialize notification system
        self.notifier = Notifier()
        
        # Initialize CAPTCHA solver
        self.captcha_solver = CaptchaSolver()
        
        logger.info(f"StealthMaster Enhanced initialized for {self.email}")
        logger.debug(f"Target URL: {config['target']['url']}")
        logger.debug(f"Max tickets: {config['monitoring']['max_tickets']}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure driver is closed"""
        if self.driver:
            self.driver.quit()
    
    def run(self):
        """Main bot execution loop"""
        logger.info("🚀 StealthMaster Enhanced starting...")
        
        try:
            # Run detection tests if enabled
            if self.config.get('testing', {}).get('run_detection_tests', True):
                self._run_initial_detection_tests()
            
            # Main state machine
            while True:
                try:
                    if self.state == BotState.INITIALIZING:
                        self._handle_initializing()
                    elif self.state == BotState.LOGGING_IN:
                        self._handle_login()
                    elif self.state == BotState.MONITORING:
                        self._handle_monitoring()
                    elif self.state == BotState.RESERVING:
                        self._handle_reservation()
                    elif self.state == BotState.BLOCKED:
                        self._handle_blocked()
                    elif self.state == BotState.SOLVING_CAPTCHA:
                        self._handle_captcha()
                    elif self.state == BotState.ERROR:
                        self._handle_error()
                    elif self.state == BotState.SUCCESS:
                        logger.info("✅ Successfully reserved tickets!")
                        break
                    
                    # Human-like delay between actions
                    if self.config['anti_detection']['random_delays']:
                        time.sleep(self.stealth.human_like_delay(100, 500))
                    
                except KeyboardInterrupt:
                    logger.info("⏹️ Bot stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    self.state = BotState.ERROR
                    self.consecutive_failures += 1
                    
                    if self.consecutive_failures > 5:
                        logger.error("Too many consecutive failures, exiting")
                        break
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
    
    def _create_proxy_auth_extension(self) -> Optional[str]:
        """Create Chrome extension for proxy authentication"""
        if not all([self.proxy_hostname, self.proxy_port, self.proxy_username, self.proxy_password]):
            return None
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        """
        
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{self.proxy_hostname}",
                    port: parseInt({self.proxy_port})
                }},
                bypassList: ["localhost"]
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        chrome.webRequest.onAuthRequired.addListener(
            function(details) {{
                return {{
                    authCredentials: {{
                        username: "{self.proxy_username}",
                        password: "{self.proxy_password}"
                    }}
                }};
            }},
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """
        
        pluginfile = tempfile.mktemp('.zip')
        
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)
        
        return pluginfile
    
    def _setup_driver(self):
        """Set up Chrome driver with enhanced stealth options"""
        logger.info("Setting up enhanced stealth Chrome driver...")
        
        # Create Chrome options
        options = uc.ChromeOptions()
        
        # Add all enhanced stealth arguments
        enhanced_args = self.stealth.get_enhanced_chrome_options()
        for arg in enhanced_args:
            try:
                options.add_argument(arg)
            except Exception as e:
                logger.debug(f"Could not add argument {arg}: {e}")
        
        # Set user agent
        user_agent = self.stealth.get_random_user_agent()
        options.add_argument(f'--user-agent={user_agent}')
        
        # Browser profile persistence
        if self.config['browser'].get('use_persistent_profile', True):
            profile_dir = Path("browser_profiles") / self.config['browser'].get('profile_name', 'fansale_user')
            profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--user-data-dir={profile_dir}')
            options.add_argument('--profile-directory=Default')
            logger.info(f"Using persistent profile: {profile_dir}")
        
        # Preferences
        prefs = {
            'profile.default_content_setting_values': {
                'notifications': 2,
                'geolocation': 2,
                'media_stream': 2,
                'media_stream_mic': 2,
                'media_stream_camera': 2,
                'protocol_handlers': 2,
                'ppapi_broker': 2,
                'automatic_downloads': 2,
                'midi_sysex': 2,
                'push_messaging': 2,
                'ssl_cert_decisions': 2,
                'metro_switch_to_desktop': 2,
                'protected_media_identifier': 2,
                'app_banner': 2,
                'site_engagement': 2,
                'durable_storage': 2
            },
            'profile.managed_default_content_settings': {
                'images': 1  # Allow images from main domain
            }
        }
        options.add_experimental_option('prefs', prefs)
        options.page_load_strategy = 'eager'
        
        # Window size
        window_size = self.config['browser']['window_size']
        options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        # Headless mode if configured
        if self.config['browser'].get('headless', False):
            options.add_argument('--headless=new')
        
        # Add proxy authentication extension if proxy is configured
        proxy_extension_path = self._create_proxy_auth_extension()
        if proxy_extension_path:
            options.add_extension(proxy_extension_path)
            logger.info("Proxy authentication extension loaded")
        
        # Create driver
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
        
        # Execute comprehensive stealth JavaScript
        stealth_js = self.stealth.get_stealth_javascript()
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_js
        })
        
        # Smart resource blocking (not too aggressive)
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {
            'urls': [
                '*://*.google-analytics.com/*',
                '*://*.googletagmanager.com/*',
                '*://*.doubleclick.net/*',
                '*://*.facebook.com/tr/*',
                '*://*.hotjar.com/*',
                '*://*.newrelic.com/*',
                '*://*.amplitude.com/*',
                '*://*.mixpanel.com/*',
                '*://*.segment.io/*',
                '*://*.sentry.io/*',
                # Don't block images/CSS from main domain
            ]
        })
        
        logger.info("✅ Enhanced stealth Chrome driver created successfully")
    
    def _run_initial_detection_tests(self):
        """Run detection tests on startup"""
        if not self.driver:
            self._setup_driver()
        
        logger.info("Running detection tests...")
        
        # Navigate to a test page
        self.driver.get("https://httpbin.org/headers")
        time.sleep(2)
        
        # Run tests
        results = self.stealth.test_detection(self.driver)
        analysis = self.stealth.analyze_detection_results(results)
        
        logger.info(f"Detection test score: {analysis['score']}/100 ({analysis['status']})")
        
        if analysis['issues']:
            logger.warning("Detection issues found:")
            for issue in analysis['issues']:
                logger.warning(f"  - {issue}")
        
        # Log detailed results
        logger.debug("Detection test results:")
        for test_name, result in results.items():
            logger.debug(f"  {test_name}: {result}")
    
    def _handle_initializing(self):
        """Handle initialization state"""
        logger.debug("Initializing bot...")
        
        # Set up driver if not already created
        if not self.driver:
            self._setup_driver()
        
        # Load any existing session
        session_loaded = self._load_session()
        
        if not session_loaded:
            self.state = BotState.LOGGING_IN
        else:
            # Verify session is still valid
            if self._check_login_status():
                logger.info("✅ Session restored successfully")
                self.state = BotState.MONITORING
            else:
                logger.warning("Session expired, need to log in again")
                self.state = BotState.LOGGING_IN
    
    def _handle_login(self):
        """Handle login process with human-like behavior"""
        logger.info("Logging in to Fansale...")
        
        try:
            # Navigate to login page
            self.driver.get("https://www.fansale.it/login")
            
            # Random mouse movements while page loads
            if self.config['anti_detection']['mouse_movements']:
                self.stealth.random_mouse_movement(self.driver, duration=1.5)
            
            # Handle cookie popup
            self._handle_cookie_popup()
            
            # Wait for and find login form elements
            wait = WebDriverWait(self.driver, 20)
            
            # Email field - use Fansale-specific selector
            email_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='loginEmail']"))
            )
            
            # Random delay before typing
            time.sleep(self.stealth.human_like_delay(500, 1500))
            
            # Click email field
            email_field.click()
            time.sleep(self.stealth.human_like_delay(100, 300))
            
            # Type email with human-like speed
            if self.config['anti_detection']['human_typing']:
                self.stealth.human_like_typing(email_field, self.email, self.driver)
            else:
                email_field.send_keys(self.email)
            
            # Tab to password field
            time.sleep(self.stealth.human_like_delay(200, 500))
            email_field.send_keys(Keys.TAB)
            
            # Password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, "[data-qa='loginPassword']")
            time.sleep(self.stealth.human_like_delay(100, 300))
            
            # Type password
            if self.config['anti_detection']['human_typing']:
                self.stealth.human_like_typing(password_field, self.password, self.driver)
            else:
                password_field.send_keys(self.password)
            
            # Random scrolling
            if self.config['anti_detection']['mouse_movements']:
                self.stealth.random_scrolling(self.driver, duration=0.5)
            
            # Find and click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "[data-qa='loginSubmit']")
            
            # Human-like pause before clicking
            time.sleep(self.stealth.human_like_delay(300, 800))
            
            # Click login button
            login_button.click()
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if login was successful
            if self._check_login_status():
                logger.info("✅ Login successful!")
                self._save_session()
                self.state = BotState.MONITORING
                self.consecutive_failures = 0
            else:
                # Check for CAPTCHA
                if self._detect_captcha():
                    logger.warning("CAPTCHA detected during login")
                    self.state = BotState.SOLVING_CAPTCHA
                else:
                    logger.error("Login failed!")
                    self.state = BotState.ERROR
                    self.consecutive_failures += 1
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.state = BotState.ERROR
            self.consecutive_failures += 1
    
    def _handle_cookie_popup(self):
        """Handle cookie consent popup"""
        try:
            # Multiple possible cookie button selectors
            cookie_selectors = [
                "//button[contains(text(), 'ACCETTA TUTTI I COOKIE')]",
                "//button[contains(text(), 'Accetta tutti i cookie')]",
                "//button[contains(text(), 'Accetta tutto')]",
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(@class, 'cookie') and contains(@class, 'accept')]",
                "//button[@id='onetrust-accept-btn-handler']",
                "//button[@class='optanon-allow-all']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = self.driver.find_element(By.XPATH, selector)
                    if cookie_button.is_displayed():
                        time.sleep(self.stealth.human_like_delay(500, 1000))
                        cookie_button.click()
                        logger.info("Cookie popup accepted")
                        time.sleep(1)
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"No cookie popup found or error: {e}")
    
    def _handle_monitoring(self):
        """Handle ticket monitoring with adaptive behavior"""
        # Check if we need to verify login status
        time_since_login_check = (datetime.now() - self.last_login_check).seconds
        if time_since_login_check >= self.login_check_interval:
            logger.info("Checking login status...")
            if not self._check_login_status():
                logger.warning("Session expired, logging in again...")
                self.state = BotState.LOGGING_IN
                return
            self.last_login_check = datetime.now()
        
        logger.debug(f"Checking for tickets (#{self.checks_performed + 1})...")
        
        try:
            # Navigate to target URL if not already there
            current_url = self.driver.current_url
            target_url = self.config['target']['url']
            
            # More flexible URL matching
            if not any(part in current_url for part in ['bruce-springsteen', 'tickets', 'fansale']):
                self.driver.get(target_url)
                time.sleep(2)
            else:
                # Refresh the page
                self.driver.refresh()
            
            # Random mouse movement while page loads
            if self.config['anti_detection']['mouse_movements']:
                self.stealth.random_mouse_movement(self.driver, duration=0.5)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Check for tickets using Fansale-specific selector
            try:
                ticket_elements = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-qa='ticketToBuy']"))
                )
                
                if ticket_elements:
                    num_tickets = len(ticket_elements)
                    logger.info(f"🎫 Found {num_tickets} ticket(s) available!")
                    
                    # Check if within our limit
                    if num_tickets <= self.config['monitoring']['max_tickets']:
                        self.state = BotState.RESERVING
                        self.notifier.send_notification(
                            f"🎫 {num_tickets} ticket(s) found for {self.config['target']['event_name']}!",
                            priority='high'
                        )
                    else:
                        logger.info(f"Too many tickets ({num_tickets}), waiting for better options...")
                else:
                    logger.debug("No tickets found")
            
            except TimeoutException:
                # Check for "no tickets" message
                no_tickets_text = "Sfortunatamente non sono state trovate offerte adeguate"
                page_source = self.driver.page_source
                
                if no_tickets_text in page_source:
                    logger.debug("No tickets available (Italian message found)")
                else:
                    logger.debug("Page loaded but no tickets found")
            
            # Update statistics
            self.checks_performed += 1
            self.consecutive_failures = 0
            
            # Adaptive delay with randomization
            if self.config['anti_detection']['random_delays']:
                delay = self.current_delay + random.uniform(-1, 2)
                delay = max(self.min_delay, min(delay, self.max_delay))
            else:
                delay = self.current_delay
            
            logger.debug(f"Waiting {delay:.1f} seconds before next check...")
            time.sleep(delay)
        
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            self.consecutive_failures += 1
            
            # Adaptive delay increase on failure
            self.current_delay = min(self.current_delay * 1.5, self.max_delay)
            
            if self.consecutive_failures > 3:
                self.state = BotState.ERROR
    
    def _handle_reservation(self):
        """Handle ticket reservation process"""
        logger.info("🎯 Attempting to reserve tickets...")
        
        try:
            # Find buy button using Fansale-specific selector
            buy_button = self.driver.find_element(By.CSS_SELECTOR, "[data-qa='buyNowButton']")
            
            # Human-like pause before clicking
            time.sleep(self.stealth.human_like_delay(300, 800))
            
            # Click buy button
            buy_button.click()
            logger.info("✅ Clicked buy button!")
            
            # Wait for reservation confirmation or next step
            time.sleep(3)
            
            # Check if reservation was successful
            if self._check_reservation_success():
                self.tickets_reserved += 1
                self.last_success_time = datetime.now()
                self.state = BotState.SUCCESS
                
                self.notifier.send_notification(
                    f"🎉 Successfully reserved tickets for {self.config['target']['event_name']}!",
                    priority='urgent'
                )
            else:
                # Check for CAPTCHA
                if self._detect_captcha():
                    logger.warning("CAPTCHA detected during reservation")
                    self.state = BotState.SOLVING_CAPTCHA
                else:
                    logger.warning("Reservation might have failed, returning to monitoring")
                    self.state = BotState.MONITORING
        
        except NoSuchElementException:
            logger.error("Buy button not found!")
            self.state = BotState.MONITORING
        except Exception as e:
            logger.error(f"Reservation error: {e}")
            self.state = BotState.ERROR
    
    def _handle_captcha(self):
        """Handle CAPTCHA solving"""
        logger.info("Solving CAPTCHA...")
        
        if self.captcha_solver.solve_captcha(self.driver):
            logger.info("✅ CAPTCHA solved successfully")
            # Return to previous state
            self.state = BotState.MONITORING
        else:
            logger.error("Failed to solve CAPTCHA")
            self.state = BotState.ERROR
    
    def _handle_blocked(self):
        """Handle being blocked"""
        logger.warning("Bot appears to be blocked, implementing countermeasures...")
        
        # Clear cookies and cache
        self.driver.delete_all_cookies()
        
        # Wait with exponential backoff
        wait_time = min(300, 60 * (2 ** self.consecutive_failures))
        logger.info(f"Waiting {wait_time} seconds before retry...")
        time.sleep(wait_time)
        
        # Try with new session
        self.driver.quit()
        self._setup_driver()
        self.state = BotState.LOGGING_IN
    
    def _handle_error(self):
        """Handle error state"""
        logger.error("Bot in error state")
        
        if self.consecutive_failures < 3:
            logger.info("Attempting recovery...")
            time.sleep(10)
            self.state = BotState.MONITORING
        else:
            logger.error("Too many failures, resetting...")
            if self.driver:
                self.driver.quit()
            self._setup_driver()
            self.state = BotState.LOGGING_IN
            self.consecutive_failures = 0
    
    def _check_login_status(self) -> bool:
        """Check if user is logged in"""
        try:
            # Check for logout button or user menu
            logout_indicators = [
                "//a[contains(@href, '/logout')]",
                "//button[contains(text(), 'Logout')]",
                "//span[contains(@class, 'user-name')]",
                "//div[contains(@class, 'user-menu')]"
            ]
            
            for indicator in logout_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element:
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
            return False
    
    def _check_reservation_success(self) -> bool:
        """Check if reservation was successful"""
        try:
            success_indicators = [
                "conferma",
                "successo",
                "riservato",
                "pagamento",
                "payment",
                "reserved",
                "success"
            ]
            
            page_source = self.driver.page_source.lower()
            
            for indicator in success_indicators:
                if indicator in page_source:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking reservation success: {e}")
            return False
    
    def _detect_captcha(self) -> bool:
        """Detect if CAPTCHA is present"""
        try:
            captcha_indicators = [
                "//iframe[contains(@src, 'recaptcha')]",
                "//div[contains(@class, 'g-recaptcha')]",
                "//div[contains(@id, 'captcha')]",
                "//img[contains(@src, 'captcha')]"
            ]
            
            for indicator in captcha_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element:
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            logger.debug(f"Error detecting CAPTCHA: {e}")
            return False
    
    def _save_session(self):
        """Save browser session"""
        try:
            cookies = self.driver.get_cookies()
            with open('session/cookies.json', 'w') as f:
                json.dump(cookies, f)
            logger.debug("Session saved")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def _load_session(self) -> bool:
        """Load browser session"""
        try:
            if not os.path.exists('session/cookies.json'):
                return False
            
            # Navigate to domain first
            self.driver.get("https://www.fansale.it")
            
            # Load cookies
            with open('session/cookies.json', 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Could not add cookie: {e}")
            
            # Refresh to apply cookies
            self.driver.refresh()
            logger.debug("Session loaded")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False


def main():
    """Main entry point"""
    try:
        # Load configuration
        config = load_config()
        
        # Create and run bot
        with StealthMasterEnhanced(config) as bot:
            bot.run()
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()