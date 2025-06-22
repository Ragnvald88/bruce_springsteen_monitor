#!/usr/bin/env python3
"""
StealthMaster - Advanced Ticket Reservation Bot
A robust, efficient, and stealthy bot for monitoring and reserving tickets on Fansale.it
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
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Python 3.12+ compatibility fix
if sys.version_info >= (3, 12):
    import setuptools._distutils_hack
    setuptools._distutils_hack.ensure_shim()

import yaml
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Import our custom modules
from notifications import Notifier
from captcha_solver import CaptchaSolver

# Load environment variables
load_dotenv()

# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("session").mkdir(exist_ok=True)

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
    """
    Load and validate configuration from YAML file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing validated configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
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
        config.setdefault('browser', {}).setdefault('window_size', [1280, 720])
        config.setdefault('monitoring', {}).setdefault('check_interval', 5)
        config.setdefault('monitoring', {}).setdefault('max_tickets', 4)
        
        logger.info("Configuration loaded successfully")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        raise


class StealthMaster:
    """Main bot class for ticket reservation"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the StealthMaster bot
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.state = BotState.INITIALIZING
        self.driver: Optional[webdriver.Chrome] = None
        
        # Extract credentials from environment
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Missing FANSALE_EMAIL or FANSALE_PASSWORD in environment")
        
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
        
        # Adaptive delay settings
        self.current_delay = config['monitoring']['check_interval']
        self.min_delay = 3
        self.max_delay = 60
        
        # Initialize notification system
        self.notifier = Notifier()
        
        # Initialize CAPTCHA solver
        self.captcha_solver = CaptchaSolver()
        
        logger.info(f"StealthMaster initialized for {self.email}")
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
        logger.info("🚀 StealthMaster starting...")
        
        try:
            # Create driver
            self.create_driver()
            
            # Main state machine loop
            while True:
                try:
                    logger.debug(f"Current state: {self.state.value}")
                    
                    if self.state == BotState.INITIALIZING:
                        self._handle_initializing()
                    
                    elif self.state == BotState.LOGGING_IN:
                        self._handle_login()
                    
                    elif self.state == BotState.MONITORING:
                        self._handle_monitoring()
                    
                    elif self.state == BotState.RESERVING:
                        self._handle_reserving()
                    
                    elif self.state == BotState.BLOCKED:
                        self._handle_blocked()
                    
                    elif self.state == BotState.SOLVING_CAPTCHA:
                        self._handle_captcha()
                    
                    elif self.state == BotState.ERROR:
                        self._handle_error()
                    
                    elif self.state == BotState.SUCCESS:
                        logger.info("✅ Bot completed successfully!")
                        break
                    
                    # Add small delay to prevent CPU spinning
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    logger.info("⏹️ Bot stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in main loop: {e}")
                    logger.debug(traceback.format_exc())
                    self.state = BotState.ERROR
                    
        finally:
            self._cleanup()
    
    def _create_proxy_auth_extension(self) -> Optional[str]:
        """
        Create a Chrome extension for proxy authentication
        
        Returns:
            Path to the created extension zip file, or None if no proxy configured
        """
        if not all([self.proxy_hostname, self.proxy_port, self.proxy_username, self.proxy_password]):
            return None
            
        logger.debug("Creating proxy authentication extension...")
        
        # Create extension files in memory
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Extension",
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

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{self.proxy_username}",
                    password: "{self.proxy_password}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """
        
        # Create temporary zip file
        extension_path = Path(tempfile.gettempdir()) / f"proxy_auth_{os.getpid()}.zip"
        
        with zipfile.ZipFile(extension_path, 'w') as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("background.js", background_js)
        
        logger.debug(f"Proxy extension created at: {extension_path}")
        return str(extension_path)

    def create_driver(self):
        """Create and configure the Chrome driver with stealth settings"""
        logger.info("Creating stealth Chrome driver...")
        
        # Chrome options for stealth
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance options - Block unnecessary resources
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # Block images
                'plugins': 2,  # Block plugins
                'popups': 2,  # Block popups
                'geolocation': 2,  # Block location
                'notifications': 2,  # Block notifications
                'media_stream': 2,  # Block media stream
                'media_stream_mic': 2,  # Block microphone
                'media_stream_camera': 2,  # Block camera
                'protocol_handlers': 2,  # Block protocol handlers
                'ppapi_broker': 2,  # Block PPAPI broker
                'automatic_downloads': 2,  # Block automatic downloads
                'midi_sysex': 2,  # Block MIDI sysex
                'push_messaging': 2,  # Block push messaging
                'ssl_cert_decisions': 2,  # Block SSL cert decisions
                'metro_switch_to_desktop': 2,  # Block metro switch
                'protected_media_identifier': 2,  # Block protected media
                'app_banner': 2,  # Block app banner
                'site_engagement': 2,  # Block site engagement
                'durable_storage': 2  # Block durable storage
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
        
        # Set resource blocking using CDP
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {
            'urls': [
                '*://*.google-analytics.com/*',
                '*://*.googletagmanager.com/*',
                '*://*.facebook.com/*',
                '*://*.doubleclick.net/*',
                '*://*.cloudflare.com/analytics/*',
                '*://*.hotjar.com/*',
                '*://*.fontawesome.com/*',
                '*://*.googleapis.com/fonts/*',
                '*://*.gstatic.com/fonts/*',
                '*.woff',
                '*.woff2',
                '*.ttf',
                '*.otf',
                '*.png',
                '*.jpg',
                '*.jpeg',
                '*.gif',
                '*.webp',
                '*.svg',
                '*.ico'
            ]
        })
        
        # Execute stealth scripts
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Fake plugins array
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override chrome detection
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Remove automation indicators
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            '''
        })
        
        logger.info("✅ Stealth Chrome driver created successfully")
    
    def _handle_initializing(self):
        """Handle initialization state"""
        logger.debug("Initializing bot...")
        
        # Load any existing session
        session_loaded = self._load_session()
        
        if not session_loaded:
            # No session, navigate to target URL
            target_url = self.config['target']['url']
            logger.info(f"Navigating to {target_url}")
            self.driver.get(target_url)
            
            # Wait for page to load
            time.sleep(3)
        
        # Check if we need to login
        if self._is_logged_in():
            logger.info("Already logged in")
            self.state = BotState.MONITORING
        else:
            logger.info("Login required")
            self.state = BotState.LOGGING_IN
    
    def _handle_login(self):
        """Handle login state with robust error handling"""
        logger.info("Starting login process...")
        
        try:
            # Navigate to login page if not already there
            current_url = self.driver.current_url
            if "login" not in current_url:
                logger.debug("Navigating to login page...")
                
                # Look for login button
                try:
                    login_link = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Accedi')]"))
                    )
                    login_link.click()
                    logger.debug("Clicked login button")
                    time.sleep(3)
                except TimeoutException:
                    logger.error("Login button not found")
                    self.state = BotState.ERROR
                    return
            
            # Handle cookie consent if present
            self._handle_cookie_consent()
            
            # Check for TicketOne iframe
            logger.debug("Looking for TicketOne iframe...")
            iframe_found = False
            
            try:
                iframe = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='ticketone.it']"))
                )
                self.driver.switch_to.frame(iframe)
                iframe_found = True
                logger.info("Switched to TicketOne iframe")
            except TimeoutException:
                logger.debug("No TicketOne iframe found, trying direct login")
            
            # Fill login form
            try:
                # Wait for username field
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                username_field.clear()
                username_field.send_keys(self.email)
                logger.debug("Filled username field")
                
                # Fill password field
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(self.password)
                logger.debug("Filled password field")
                
                # Click login button
                login_button = self.driver.find_element(By.ID, "loginCustomerButton")
                login_button.click()
                logger.info("Submitted login form")
                
            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Failed to fill login form: {e}")
                self.state = BotState.ERROR
                return
            
            # Switch back to main content if we were in iframe
            if iframe_found:
                self.driver.switch_to.default_content()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Verify login success
            if self._is_logged_in():
                logger.info("✅ Login successful!")
                self._save_session()  # Save the session immediately
                
                # Navigate back to target URL if needed
                target_url = self.config['target']['url']
                if target_url not in self.driver.current_url:
                    logger.debug(f"Navigating back to target: {target_url}")
                    self.driver.get(target_url)
                    time.sleep(3)
                
                self.state = BotState.MONITORING
            else:
                logger.error("Login verification failed")
                self.consecutive_failures += 1
                
                # Check for specific error messages
                try:
                    error_msg = self.driver.find_element(By.CLASS_NAME, "error-message")
                    logger.error(f"Login error: {error_msg.text}")
                except:
                    pass
                
                if self.consecutive_failures > 3:
                    logger.error("Too many login failures, entering error state")
                    self.state = BotState.ERROR
                else:
                    logger.info("Retrying login...")
                    time.sleep(5)
                    
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            logger.debug(traceback.format_exc())
            self.state = BotState.ERROR
            
            # Always try to switch back to default content
            try:
                self.driver.switch_to.default_content()
            except:
                pass
    
    def _handle_cookie_consent(self):
        """Handle cookie consent popups if they appear"""
        try:
            # Common cookie consent selectors
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[onclick*='accept']",
                "a[id*='accept']",
                "button:contains('Accetta')",
                "button:contains('Accept')",
                "#onetrust-accept-btn-handler",
                "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
            ]
            
            for selector in cookie_selectors:
                try:
                    if selector.startswith("button:contains") or selector.startswith("a:contains"):
                        # Use XPath for text content
                        xpath = f"//{selector.split(':')[0]}[contains(text(), '{selector.split('(')[1].split(')')[0]}')]"
                        cookie_btn = self.driver.find_element(By.XPATH, xpath)
                    else:
                        cookie_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if cookie_btn.is_displayed() and cookie_btn.is_enabled():
                        cookie_btn.click()
                        logger.debug(f"Clicked cookie consent button: {selector}")
                        time.sleep(1)
                        return
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error handling cookie consent: {e}")
    
    def _handle_monitoring(self):
        """Handle monitoring state - continuously check for tickets"""
        self.checks_performed += 1
        
        # Status update
        logger.info(f"🔍 Check #{self.checks_performed} | Reserved: {self.tickets_reserved}/{self.config['monitoring']['max_tickets']} | Delay: {self.current_delay}s")
        
        # Check if we're still logged in
        if not self._is_logged_in():
            logger.warning("Session expired, need to login again")
            self.state = BotState.LOGGING_IN
            return
        
        # Check if we're on the correct page
        current_url = self.driver.current_url
        target_url = self.config['target']['url']
        
        if target_url not in current_url:
            logger.warning(f"Not on target page, navigating back to: {target_url}")
            self.driver.get(target_url)
            time.sleep(3)
            return
        
        # Check for blocking
        if self._is_blocked():
            logger.warning("Detected blocking, entering blocked state")
            self.state = BotState.BLOCKED
            return
        
        # Look for available tickets
        tickets_found = self._find_available_tickets()
        
        if tickets_found:
            logger.info(f"🎫 Found {len(tickets_found)} available tickets!")
            self.state = BotState.RESERVING
            # Store tickets for reservation
            self.available_tickets = tickets_found
            self.consecutive_failures = 0  # Reset failure counter
            self.current_delay = max(self.current_delay * 0.8, self.min_delay)  # Decrease delay on success
        else:
            logger.debug("No tickets found")
            # Adaptive delay - increase slightly on no tickets
            self.current_delay = min(self.current_delay * 1.1, self.max_delay)
        
        # Check if we've reached our goal
        if self.tickets_reserved >= self.config['monitoring']['max_tickets']:
            logger.info("✅ Reached target number of tickets!")
            self.state = BotState.SUCCESS
            return
        
        # Wait before next check with some randomization
        wait_time = self.current_delay + random.uniform(-1, 1)
        logger.debug(f"Waiting {wait_time:.1f}s before next check...")
        time.sleep(wait_time)
        
        # Refresh the page
        self.driver.refresh()
    
    def _handle_reserving(self):
        """Handle reservation state - attempt to reserve found tickets"""
        logger.info("Starting ticket reservation process...")
        
        if not hasattr(self, 'available_tickets') or not self.available_tickets:
            logger.error("No tickets available to reserve")
            self.state = BotState.MONITORING
            return
        
        # Try to reserve each ticket until successful
        for i, ticket_element in enumerate(self.available_tickets):
            if self.tickets_reserved >= self.config['monitoring']['max_tickets']:
                logger.info("Reached maximum tickets limit")
                self.state = BotState.SUCCESS
                return
            
            try:
                logger.info(f"Attempting to reserve ticket {i+1}/{len(self.available_tickets)}")
                
                # Scroll to ticket
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
                time.sleep(0.5)
                
                # Click the ticket
                try:
                    ticket_element.click()
                except:
                    # Try JavaScript click if regular click fails
                    self.driver.execute_script("arguments[0].click();", ticket_element)
                
                logger.debug("Clicked ticket, waiting for page response...")
                time.sleep(2)
                
                # Check if we're on a detail page
                if self._is_on_detail_page():
                    # Look for add to cart button
                    if self._click_add_to_cart():
                        logger.info("✅ Successfully added ticket to cart!")
                        self.tickets_reserved += 1
                        self.last_success_time = datetime.now()
                        
                        # Save session after successful reservation
                        self._save_session()
                        
                        # Send notification
                        try:
                            # Extract ticket info from the page
                            ticket_info = self._extract_ticket_info()
                            self.notifier.send_ticket_reserved(ticket_info)
                        except Exception as e:
                            logger.error(f"Failed to send notification: {e}")
                        
                        # Go back to monitoring
                        self.state = BotState.MONITORING
                        
                        # Navigate back to listing page
                        self.driver.get(self.config['target']['url'])
                        time.sleep(3)
                        return
                    else:
                        logger.warning("Failed to add ticket to cart")
                        # Go back and try next ticket
                        self.driver.back()
                        time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error reserving ticket {i+1}: {e}")
                logger.debug(traceback.format_exc())
                continue
        
        # If we get here, all reservation attempts failed
        logger.error("Failed to reserve any tickets")
        self.consecutive_failures += 1
        self.current_delay = min(self.current_delay * 1.5, self.max_delay)
        self.state = BotState.MONITORING
    
    def _find_available_tickets(self) -> List:
        """
        Find available tickets on the page
        
        Returns:
            List of WebElements representing available tickets
        """
        try:
            # Primary selector for tickets
            tickets = self.driver.find_elements(By.CSS_SELECTOR, ".offer-item:not(.offer-item-sold)")
            
            if tickets:
                logger.debug(f"Found {len(tickets)} tickets with primary selector")
                return tickets[:10]  # Limit to first 10 to avoid too many attempts
            
            # Fallback selectors
            fallback_selectors = [
                "[class*='ticket']:not([class*='sold'])",
                "[class*='offer']:not([class*='sold'])",
                "[data-testid*='ticket']:not([class*='sold'])",
                ".listing-item:not(.sold-out)"
            ]
            
            for selector in fallback_selectors:
                tickets = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if tickets:
                    logger.debug(f"Found {len(tickets)} tickets with selector: {selector}")
                    return tickets[:10]
            
            # JavaScript-based search as last resort
            tickets = self.driver.execute_script("""
                const tickets = [];
                const elements = document.querySelectorAll('div, article, section, li, a');
                
                for (const elem of elements) {
                    const text = elem.textContent || '';
                    
                    // Must contain price and not be sold out
                    if (text.includes('€') && !text.toLowerCase().includes('esaurit') && 
                        !elem.classList.contains('sold-out')) {
                        
                        // Check if it has ticket-related keywords
                        if (text.match(/settore|fila|posto|sector|row|seat|block|tribune/i)) {
                            tickets.push(elem);
                        }
                    }
                }
                
                return tickets.slice(0, 10);
            """)
            
            if tickets:
                logger.debug(f"Found {len(tickets)} tickets with JavaScript search")
                return tickets
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding tickets: {e}")
            return []
    
    def _is_on_detail_page(self) -> bool:
        """Check if we're on a ticket detail page"""
        try:
            # Check URL patterns
            current_url = self.driver.current_url
            detail_patterns = ['/detail/', '/ticket/', '/offer/', '/biglietto/']
            
            for pattern in detail_patterns:
                if pattern in current_url:
                    return True
            
            # Check for add to cart button presence
            cart_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[class*='add-to-cart'], [class*='aggiungi']")
            return len(cart_buttons) > 0
            
        except:
            return False
    
    def _click_add_to_cart(self) -> bool:
        """
        Find and click the add to cart button
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Common add to cart selectors
            selectors = [
                "button[class*='add-to-cart']",
                "button[class*='aggiungi']",
                "button[onclick*='cart']",
                "a[class*='add-to-cart']",
                "button:contains('Aggiungi al carrello')",
                "button:contains('Add to cart')",
                "[data-testid*='add-to-cart']"
            ]
            
            for selector in selectors:
                try:
                    if ":contains" in selector:
                        # XPath for text content
                        text = selector.split("'")[1]
                        elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Scroll to element
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            
                            # Click element
                            try:
                                element.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", element)
                            
                            logger.info("Clicked add to cart button")
                            time.sleep(2)
                            
                            # Verify success
                            return self._verify_cart_addition()
                            
                except Exception as e:
                    logger.debug(f"Failed with selector {selector}: {e}")
                    continue
            
            logger.error("No add to cart button found")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking add to cart: {e}")
            return False
    
    def _verify_cart_addition(self) -> bool:
        """Verify that ticket was successfully added to cart"""
        try:
            # Check for success messages
            success_indicators = [
                "carrello",
                "cart",
                "aggiunto",
                "added",
                "successo",
                "success"
            ]
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for indicator in success_indicators:
                if indicator in page_text:
                    logger.debug(f"Found success indicator: {indicator}")
                    return True
            
            # Check if URL changed to cart
            if "cart" in self.driver.current_url or "carrello" in self.driver.current_url:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying cart addition: {e}")
            return False
    
    def _extract_ticket_info(self) -> Dict[str, Any]:
        """Extract ticket information from the current page"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Extract price
            import re
            price_match = re.search(r'€\s*(\d+(?:[.,]\d+)?)', page_text)
            price = f"€{price_match.group(1)}" if price_match else "Unknown"
            
            # Extract event name from URL or page
            event = "Unknown Event"
            if "bruce-springsteen" in self.driver.current_url.lower():
                event = "Bruce Springsteen"
            else:
                # Try to find event name in page
                h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
                if h1_elements:
                    event = h1_elements[0].text.strip()
            
            # Extract section/seat info
            section = "General Admission"
            section_keywords = ['settore', 'sector', 'fila', 'row', 'posto', 'seat', 'tribune', 'prato']
            for keyword in section_keywords:
                match = re.search(rf'{keyword}[:\s]+([^\s,]+)', page_text, re.IGNORECASE)
                if match:
                    section = match.group(1)
                    break
            
            return {
                'event': event,
                'price': price,
                'section': section,
                'quantity': 1,
                'url': self.driver.current_url
            }
            
        except Exception as e:
            logger.error(f"Error extracting ticket info: {e}")
            return {
                'event': 'Unknown',
                'price': 'Unknown',
                'section': 'Unknown',
                'quantity': 1
            }
    
    def _is_blocked(self) -> bool:
        """Check if we're being blocked or rate limited"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            block_indicators = [
                'access denied',
                'forbidden',
                'rate limit',
                'too many requests',
                'blocked',
                'captcha'
            ]
            
            for indicator in block_indicators:
                if indicator in page_text:
                    logger.warning(f"Block indicator found: {indicator}")
                    return True
            
            # Check for CAPTCHA presence
            captcha_selectors = [
                "[class*='captcha']",
                "[id*='captcha']",
                "iframe[src*='recaptcha']",
                "[class*='challenge']"
            ]
            
            for selector in captcha_selectors:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.warning(f"CAPTCHA detected with selector: {selector}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking for blocks: {e}")
            return False
    
    def _handle_blocked(self):
        """Handle blocked state"""
        logger.warning("Bot is blocked, checking for CAPTCHA...")
        
        # Check if it's a CAPTCHA block
        captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='captcha'], iframe[src*='recaptcha']")
        if captcha_elements:
            logger.info("CAPTCHA detected, switching to CAPTCHA solving state")
            self.state = BotState.SOLVING_CAPTCHA
            return
        
        # Otherwise, wait and retry
        self.consecutive_failures += 1
        wait_time = min(30 * self.consecutive_failures, 300)  # Max 5 minutes
        logger.warning(f"Waiting {wait_time}s before retry...")
        time.sleep(wait_time)
        
        # Try a fresh start
        self.state = BotState.INITIALIZING
    
    def _handle_captcha(self):
        """Handle CAPTCHA solving state"""
        logger.info("Attempting to solve CAPTCHA...")
        
        if not self.captcha_solver.is_configured():
            logger.error("CAPTCHA solver not configured, cannot proceed")
            self.notifier.send_error("CAPTCHA detected but solver not configured!", critical=True)
            self.state = BotState.ERROR
            return
        
        # Try to solve the CAPTCHA
        solution = self.captcha_solver.solve_recaptcha(self.driver)
        
        if solution:
            logger.info("✅ CAPTCHA solved successfully")
            # Wait a bit for the page to process the solution
            time.sleep(5)
            
            # Check if we're still blocked
            if self._is_blocked():
                logger.warning("Still blocked after solving CAPTCHA")
                self.state = BotState.BLOCKED
            else:
                logger.info("CAPTCHA cleared, resuming monitoring")
                self.state = BotState.MONITORING
        else:
            logger.error("Failed to solve CAPTCHA")
            self.consecutive_failures += 1
            
            if self.consecutive_failures > 3:
                self.notifier.send_error("Multiple CAPTCHA solving failures", critical=True)
                self.state = BotState.ERROR
            else:
                # Wait and retry
                time.sleep(30)
                self.state = BotState.MONITORING
    
    def _handle_error(self):
        """Handle error state"""
        logger.error("Bot in error state, attempting recovery...")
        self.consecutive_failures += 1
        
        if self.consecutive_failures > 5:
            logger.error("Too many consecutive failures, exiting...")
            self.state = BotState.SUCCESS  # Exit gracefully
        else:
            time.sleep(10)
            self.state = BotState.INITIALIZING
    
    def _is_logged_in(self) -> bool:
        """Check if user is logged in"""
        # Basic check - will be enhanced in Phase 3.1
        try:
            # Check for login button absence
            login_elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Accedi')]")
            return len(login_elements) == 0
        except:
            return False
    
    def _save_session(self):
        """Save browser cookies to file for session persistence"""
        if not self.driver:
            return
            
        try:
            # Get all cookies
            cookies = self.driver.get_cookies()
            
            # Create session filename based on email
            session_file = Path("session") / f"{self.email.replace('@', '_at_')}.json"
            
            # Save cookies to file
            with open(session_file, 'w') as f:
                json.dump({
                    'cookies': cookies,
                    'url': self.driver.current_url,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            logger.debug(f"Session saved to {session_file}")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def _load_session(self) -> bool:
        """
        Load browser cookies from file to restore session
        
        Returns:
            True if session was loaded successfully, False otherwise
        """
        if not self.driver:
            return False
            
        try:
            # Create session filename based on email
            session_file = Path("session") / f"{self.email.replace('@', '_at_')}.json"
            
            # Check if session file exists
            if not session_file.exists():
                logger.debug("No session file found")
                return False
            
            # Load session data
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is recent (less than 24 hours old)
            timestamp = datetime.fromisoformat(session_data['timestamp'])
            if (datetime.now() - timestamp).total_seconds() > 86400:
                logger.info("Session too old, will create new session")
                return False
            
            # Navigate to the domain first (required for setting cookies)
            self.driver.get("https://www.fansale.it")
            time.sleep(2)
            
            # Add cookies
            for cookie in session_data['cookies']:
                try:
                    # Remove expiry field if it exists (can cause issues)
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Failed to add cookie: {e}")
            
            # Navigate to the saved URL
            if 'url' in session_data:
                self.driver.get(session_data['url'])
                time.sleep(2)
            
            logger.info("Session restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False
    
    def _cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")
        
        # Save session before closing
        self._save_session()
        
        # Close driver
        if self.driver:
            self.driver.quit()
        
        # Log final statistics
        logger.info("📊 Final Statistics:")
        logger.info(f"   Checks performed: {self.checks_performed}")
        logger.info(f"   Tickets reserved: {self.tickets_reserved}")
        logger.info(f"   Last success: {self.last_success_time or 'Never'}")


def main():
    """Main entry point"""
    try:
        # Load configuration
        config = load_config()
        
        # Create and run bot
        with StealthMaster(config) as bot:
            bot.run()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()