#!/usr/bin/env python3
"""
FanSale Bot - Ultimate Single-File Edition
Optimized for speed, stability, and session management
"""

import os
import sys
import time
import random
import logging
import threading
import traceback
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Suppress verbose WebDriver logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('seleniumwire').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from dotenv import load_dotenv
load_dotenv()

# Import enhanced utilities if available
try:
    from utilities.stealth_enhancements import StealthEnhancements
    from utilities.speed_optimizer import SpeedOptimizer, FastTicketChecker
    from utilities.session_manager import SessionManager
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False

# Configure cleaner logging
class CleanFormatter(logging.Formatter):
    """Custom formatter to suppress WebDriver stack traces"""
    def format(self, record):
        msg = str(record.msg)
        if "Stacktrace:" in msg:
            # Extract just the error message
            msg = msg.split('\n')[0]
            record.msg = msg
        return super().format(record)

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Suppress most logs
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)

# Console handler with clean formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(CleanFormatter('%(asctime)s | %(threadName)-10s | %(message)s', datefmt='%H:%M:%S'))
logger.handlers = [console_handler]

# Also log to file
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(CleanFormatter('%(asctime)s | %(threadName)-10s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(file_handler)


class FanSaleBot:
    """The definitive FanSale ticket bot - handles 404s and session management"""
    
    def __init__(self):
        # Load saved configuration
        self.config = self.load_configuration()
        
        # Credentials from env
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
        
        # Apply configuration
        self.num_browsers = self.config.get('num_browsers', 2)
        self.use_proxy = self.config.get('use_proxy', False)
        self.use_auto_login = self.config.get('use_auto_login', True)
        self.max_tickets = self.config.get('max_tickets', 4)
        self.ticket_filters = self.config.get('ticket_filters', [])
        self.filter_mode = self.config.get('filter_mode', 'any')
        self.session_refresh_interval = self.config.get('session_refresh_interval', 900)
        self.clear_profiles_on_start = self.config.get('clear_profiles_on_start', False)
        
        # Browser management
        self.browsers = []
        self.browser_threads = []
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        self.shutdown_event = threading.Event()
        
        # Enhanced statistics tracking
        self.stats = {
            'total_checks': 0,
            'no_ticket_found': 0,
            'tickets_found': 0,
            'successful_checkouts': 0,
            'already_reserved': 0,
            'start_time': None,
            'ticket_categories': {
                'prato_a': 0,
                'prato_b': 0,
                'settore': 0,
                'tribuna': 0,
                'other': 0
            }
        }
        
        # Session management
        self.last_login_check = {}
        self.login_check_interval = 300  # 5 minutes
        self.last_session_refresh = {}
        
        # Enhanced features if available
        if ENHANCED_MODE:
            self.stealth = StealthEnhancements()
            self.optimizer = SpeedOptimizer()
            self.session_manager = SessionManager()
        
    def play_alarm(self, success=True):
        """Play alarm sound when ticket is secured"""
        try:
            if sys.platform == "win32":
                # Windows
                import winsound
                frequency = 1000 if success else 500
                duration = 500
                for _ in range(3):
                    winsound.Beep(frequency, duration)
                    time.sleep(0.1)
            elif sys.platform == "darwin":
                # macOS
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            else:
                # Linux - use system bell
                for _ in range(3):
                    print('\a', end='', flush=True)
                    time.sleep(0.1)
        except:
            # Fallback - just log
            logger.info("🔔🔔🔔 ALARM: TICKET IN CHECKOUT! 🔔🔔🔔")
    
    def save_stats(self):
        """Save statistics to file"""
        stats_file = Path('stats.json')
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def log_stats(self):
        """Log current statistics"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        minutes = int(elapsed // 60)
        
        logger.info("="*60)
        logger.info(f"📊 STATISTICS - Running for {minutes} minutes")
        logger.info(f"   Total Checks: {self.stats['total_checks']}")
        logger.info(f"   No Tickets Found: {self.stats['no_ticket_found']}")
        logger.info(f"   Tickets Detected: {self.stats['tickets_found']}")
        logger.info(f"   Successful Checkouts: {self.stats['successful_checkouts']}")
        logger.info(f"   Already Reserved: {self.stats['already_reserved']}")
        logger.info(f"   Check Rate: {self.stats['total_checks'] / (elapsed / 60):.1f}/min" if elapsed > 0 else "N/A")
        
        if self.ticket_filters:
            logger.info(f"   Active Filters: {', '.join(self.ticket_filters)} ({self.filter_mode})")
        
        logger.info("="*60)
        
        self.save_stats()
    
    def get_proxy_config(self):
        """Get proxy configuration with data-saving features"""
        if not self.use_proxy:
            return None
            
        required_vars = ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'IPROYAL_HOSTNAME', 'IPROYAL_PORT']
        if not all(os.getenv(k) for k in required_vars):
            logger.warning("⚠️  Proxy credentials incomplete. Running without proxy.")
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        # Data-saving request interceptor
        def block_resources(request):
            # Block these resource types to save data
            block_patterns = [
                '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
                'font', '.woff', '.woff2', '.ttf',
                '.css',  # Block CSS when using proxy
                'analytics', 'google-analytics', 'googletagmanager',
                'facebook', 'doubleclick', 'amazon-adsystem',
                'tracking', 'hotjar', 'cloudflare'
            ]
            
            if any(pattern in request.url.lower() for pattern in block_patterns):
                request.abort()
                
        logger.info("🔐 Proxy configured with data-saving mode")
        
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': block_resources,
            'suppress_connection_errors': True
        }
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create a browser with optimal settings and version handling"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        def create_chrome_options():
            """Create fresh ChromeOptions instance"""
            options = uc.ChromeOptions()
            
            # Persistent profile
            profile_dir = Path("browser_profiles") / f"browser_{browser_id}"
            profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
            
            # Apply enhanced stealth if available
            if ENHANCED_MODE:
                for arg in self.stealth.get_enhanced_chrome_options():
                    options.add_argument(arg)
                for arg in self.optimizer.get_performance_chrome_options():
                    options.add_argument(arg)
            
            # Essential stealth options (always enabled)
            stealth_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-infobars',
                '--disable-gpu-sandbox',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
            ]
            
            for arg in stealth_args:
                options.add_argument(arg)
            
            # Data saving when using proxy
            if self.use_proxy:
                prefs = {
                    "profile.managed_default_content_settings": {
                        "images": 2,  # Block images
                        "plugins": 2,  # Block plugins
                        "popups": 2,  # Block popups
                        "geolocation": 2,  # Block location
                        "notifications": 2,  # Block notifications
                        "media_stream": 2,  # Block media
                    }
                }
                options.add_experimental_option("prefs", prefs)
                logger.info(f"  📻 Browser {browser_id}: Data-saving mode enabled")
            
            # Window positioning
            positions = [(0, 0), (420, 0), (840, 0), (0, 350), (420, 350)]
            if browser_id <= len(positions):
                x, y = positions[browser_id - 1]
            else:
                x, y = (0, 0)
            options.add_argument(f'--window-position={x},{y}')
            options.add_argument('--window-size=400,320')
            
            return options
        
        # Get proxy config
        proxy_config = self.get_proxy_config()
        
        # Try multiple approaches for version compatibility
        driver = None
        attempts = [
            (137, "Chrome 137"),      # Try Chrome 137 first (current version)
            (None, "auto-detection"), # Fall back to auto-detection
            (138, "Chrome 138"),      # Try Chrome 138 as last resort
        ]
        
        for version_main, desc in attempts:
            try:
                logger.info(f"🔄 Attempting with {desc}...")
                options = create_chrome_options()
                
                if proxy_config:
                    driver = uc.Chrome(options=options, seleniumwire_options=proxy_config, version_main=version_main)
                else:
                    driver = uc.Chrome(options=options, version_main=version_main)
                
                driver.set_page_load_timeout(20)
                
                # Test if driver works
                driver.execute_script("return navigator.userAgent")
                
                # Inject stealth JavaScript
                if ENHANCED_MODE:
                    driver.execute_script(self.stealth.get_stealth_javascript())
                    driver.execute_script(self.optimizer.get_fast_page_load_script())
                    self.optimizer.optimize_dom_queries(driver)
                else:
                    # Basic stealth
                    driver.execute_script("""
                        // Remove webdriver property
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        // Add chrome object
                        window.chrome = {
                            runtime: {},
                            loadTimes: function() {},
                            csi: function() {},
                            app: {}
                        };
                        
                        // Enhanced stealth
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                        
                        // Console log to verify
                        console.log('Stealth mode activated');
                    """)
                
                logger.info(f"✅ Browser {browser_id} created successfully using {desc}")
                return driver
                
            except Exception as e:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                        
                if "version" in str(e).lower():
                    logger.warning(f"Version mismatch with {desc}")
                    continue
                elif attempt < len(attempts) - 1:
                    continue
                else:
                    # Final attempt failed
                    logger.error(f"❌ Failed to create browser {browser_id}: {e}")
                    
                    if "version" in str(e).lower():
                        logger.error("\n" + "="*60)
                        logger.error("🚨 CHROMEDRIVER VERSION MISMATCH!")
                        logger.error("="*60)
                        logger.error("Please run: python3 fix_chromedriver.py")
                        logger.error("="*60 + "\n")
                    
                    return None
        
        return None
    
    def manual_login(self, browser_id: int, driver: uc.Chrome) -> bool:
        """Handle login for a browser (manual or automatic)"""
        logger.info(f"🔐 Login required for Browser {browser_id}")
        
        try:
            # Check if already logged in
            driver.get(self.target_url)
            time.sleep(2)
            
            
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} already logged in!")
                return True
            
            # Auto-login if enabled and utilities available
            if self.use_auto_login and ENHANCED_MODE:
                logger.info(f"🤖 Attempting automatic login for Browser {browser_id}...")
                if self.session_manager.auto_login(driver, self.email, self.password):
                    driver.get(self.target_url)
                    time.sleep(2)
                    if self.verify_login(driver):
                        logger.info(f"✅ Browser {browser_id} auto-logged in successfully!")
                        self.last_login_check[browser_id] = time.time()
                        self.last_session_refresh[browser_id] = time.time()
                        return True
                logger.warning(f"Auto-login failed for Browser {browser_id}, falling back to manual...")
            
            # Manual login
            driver.get("https://www.fansale.it/fansale/login.htm")
            
            print(f"\n{'='*60}")
            print(f"🔐 LOGIN REQUIRED - BROWSER #{browser_id}")
            print(f"{'='*60}")
            print(f"Email: {self.email}")
            print(f"Password: {'*' * len(self.password)}")
            print(f"{'='*60}\n")
            
            input(f"✋ Press Enter after Browser #{browser_id} is logged in...")
            
            # Navigate back to target
            driver.get(self.target_url)
            time.sleep(2)
            
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} logged in successfully!")
                self.last_login_check[browser_id] = time.time()
                self.last_session_refresh[browser_id] = time.time()
                return True
            else:
                logger.error(f"❌ Browser {browser_id} login verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error for Browser {browser_id}: {e}")
            return False
    
    def verify_login(self, driver: uc.Chrome) -> bool:
        """Verify if browser is logged in - PROPERLY FIXED"""
        try:
            page_source = driver.page_source.lower()
            
            # First check if we're on a login page
            if 'login' in driver.current_url or '/login.htm' in driver.current_url:
                return False
            
            # Look for login button/link that indicates NOT logged in
            not_logged_indicators = [
                'accedi per acquistare',  # Login to purchase
                'effettua il login',      # Please login
                'registrati/accedi',       # Register/Login
                '>login<',                 # Login button
                '>accedi<'                 # Login button in Italian
            ]
            
            # If we find these, we're NOT logged in
            if any(indicator in page_source for indicator in not_logged_indicators):
                return False
            
            # Positive indicators of being logged in
            logged_in_indicators = [
                'il mio fansale',
                'my fansale', 
                'mio account',
                'logout',
                'esci',
                'ciao,'  # Hello, username
            ]
            
            # If we find these, we ARE logged in
            if any(indicator in page_source for indicator in logged_in_indicators):
                return True
                
            # Default to not logged in to be safe
            return False
            
        except:
            return False
    
    def is_blocked(self, driver: uc.Chrome) -> bool:
        """Check if we're getting blocked or 404"""
        try:
            # Check for common block indicators
            page_source = driver.page_source.lower()
            current_url = driver.current_url.lower()
            
            # Check URL for error pages
            if any(indicator in current_url for indicator in ['404', 'error', 'blocked']):
                return True
            
            # Check page title
            if '404' in driver.title.lower() or 'error' in driver.title.lower():
                return True
            
            # Check page content
            blocked_indicators = [
                '404', 'not found', 'access denied', 'forbidden',
                'blocked', 'pagina non trovata', 'errore'
            ]
            
            for indicator in blocked_indicators:
                if indicator in page_source:
                    # Make sure it's not just a "no tickets found" message
                    if 'non sono state trovate' not in page_source and 'sfortunatamente' not in page_source:
                        return True
                    
            return False
            
        except:
            return False
    
    def clear_browser_data(self, driver: uc.Chrome, browser_id: int):
        """Clear browser data to reset session"""
        try:
            logger.info(f"🧹 Clearing browser data for Hunter {browser_id}...")
            
            # Clear cookies
            driver.delete_all_cookies()
            
            # Clear storage via JavaScript
            driver.execute_script("""
                // Clear localStorage
                try { window.localStorage.clear(); } catch(e) {}
                
                // Clear sessionStorage
                try { window.sessionStorage.clear(); } catch(e) {}
                
                // Clear IndexedDB
                if (window.indexedDB && indexedDB.databases) {
                    indexedDB.databases().then(databases => {
                        databases.forEach(db => indexedDB.deleteDatabase(db.name));
                    }).catch(e => {});
                }
            """)
            
            # Navigate to about:blank to fully reset
            driver.get("about:blank")
            time.sleep(1)
            
            logger.info(f"✅ Browser data cleared for Hunter {browser_id}")
            
            # Re-login will be needed
            self.last_login_check[browser_id] = 0
            
        except Exception as e:
            logger.error(f"Failed to clear browser data: {e}")
    
    def refresh_session(self, driver: uc.Chrome, browser_id: int):
        """Refresh browser session to avoid detection/blocks"""
        try:
            logger.info(f"🔄 Refreshing session for Hunter {browser_id}...")
            
            # Clear cookies and storage
            self.clear_browser_data(driver, browser_id)
            
            # Navigate to home page first
            driver.get("https://www.fansale.it")
            time.sleep(2)
            
            # Re-login
            if not self.manual_login(browser_id, driver):
                logger.error(f"Failed to re-login Hunter {browser_id}")
                return False
            
            logger.info(f"✅ Session refreshed for Hunter {browser_id}")
            self.last_session_refresh[browser_id] = time.time()
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh session: {e}")
            return False
    
    def get_ticket_text(self, driver: uc.Chrome, ticket_element) -> str:
        """Extract all text from a ticket element"""
        try:
            # Try multiple methods to get ticket text
            ticket_text = ""
            
            # Method 1: Direct text
            try:
                ticket_text = ticket_element.text
            except:
                pass
            
            # Method 2: JavaScript extraction
            if not ticket_text:
                try:
                    ticket_text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent", ticket_element)
                except:
                    pass
            
            # Method 3: Find all text elements within
            if not ticket_text:
                try:
                    text_elements = ticket_element.find_elements(By.XPATH, ".//*[text()]")
                    ticket_text = " ".join([elem.text for elem in text_elements if elem.text])
                except:
                    pass
            
            return ticket_text.lower() if ticket_text else ""
            
        except Exception as e:
            logger.debug(f"Error extracting ticket text: {e}")
            return ""
    
    def matches_filters(self, driver: uc.Chrome, ticket_element) -> bool:
        """Check if ticket matches the configured filters"""
        # If no filters set, accept all tickets
        if not self.ticket_filters:
            return True
        
        ticket_text = self.get_ticket_text(driver, ticket_element)
        
        if not ticket_text:
            logger.warning("Could not extract text from ticket, skipping...")
            return False
        
        # Log the ticket text for debugging
        logger.debug(f"Ticket text: {ticket_text}")
        
        # Check filters
        if self.filter_mode == 'any':
            # Match if ANY keyword is found
            for keyword in self.ticket_filters:
                if keyword.lower() in ticket_text:
                    logger.info(f"✓ Ticket matches filter: '{keyword}'")
                    return True
            logger.debug(f"✗ Ticket doesn't match any filter: {self.ticket_filters}")
            return False
        else:
            # Match if ALL keywords are found
            for keyword in self.ticket_filters:
                if keyword.lower() not in ticket_text:
                    logger.debug(f"✗ Ticket missing required keyword: '{keyword}'")
                    return False
            logger.info(f"✓ Ticket matches all filters: {self.ticket_filters}")
            return True
    
    def configure_filters(self):
        """Configure ticket filtering options"""
        print("\n🎫 TICKET FILTERING CONFIGURATION")
        print("="*50)
        print("\nCommon sections: Prato, Parterre, Tribuna, Settore")
        print("Examples:")
        print("  - 'Prato A' - for specific prato section")
        print("  - 'Tribuna' - for any tribune seat")
        print("  - 'Settore 1' - for specific sector")
        print("\nLeave empty to accept ALL tickets")
        
        filter_input = input("\nEnter keywords to filter (comma-separated): ").strip()
        
        if filter_input:
            self.ticket_filters = [f.strip() for f in filter_input.split(',') if f.strip()]
            
            if len(self.ticket_filters) > 1:
                mode = input("\nMatch mode - ANY keyword or ALL keywords? (any/all, default: any): ").strip().lower()
                self.filter_mode = 'all' if mode == 'all' else 'any'
            
            print(f"\n✅ Filters configured:")
            print(f"   Keywords: {self.ticket_filters}")
            print(f"   Mode: {self.filter_mode}")
            print(f"   Will {'accept' if self.filter_mode == 'any' else 'only accept'} tickets with {'any of' if self.filter_mode == 'any' else 'all of'} these keywords")
        else:
            self.ticket_filters = []
            print("\n✅ No filters - will accept ALL available tickets")
    
    def hunt_and_buy(self, browser_id: int, driver: uc.Chrome):
        """Core hunting loop for each browser with session management"""
        thread_name = f"Hunter-{browser_id}"
        threading.current_thread().name = thread_name
        
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        check_count = 0
        local_tickets_secured = 0
        consecutive_errors = 0
        self.last_session_refresh[browser_id] = time.time()
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Periodic login check
                if check_count % 100 == 0:  # Check every ~5 minutes at 20 checks/min
                    if not self.verify_login(driver):
                        logger.warning(f"⚠️ Hunter {browser_id}: Login expired, re-logging...")
                        if not self.manual_login(browser_id, driver):
                            logger.error(f"Failed to re-login Hunter {browser_id}")
                            break
                
                # Periodic session refresh to avoid 404s (every 15 minutes)
                if time.time() - self.last_session_refresh.get(browser_id, 0) > self.session_refresh_interval:
                    logger.info(f"🔄 Hunter {browser_id}: Time for session refresh...")
                    if self.refresh_session(driver, browser_id):
                        consecutive_errors = 0
                    continue
                
                # Check if we're blocked
                if self.is_blocked(driver):
                    logger.warning(f"⚠️ Hunter {browser_id}: Detected 404/block - refreshing session...")
                    if self.refresh_session(driver, browser_id):
                        consecutive_errors = 0
                    continue
                
                # Fast ticket detection
                if ENHANCED_MODE and hasattr(self, 'optimizer'):
                    # Use enhanced fast checker
                    if not hasattr(driver, '_fast_checker'):
                        driver._fast_checker = FastTicketChecker(driver)
                    
                    has_tickets, ticket_count = driver._fast_checker.fast_ticket_check()
                    if has_tickets and ticket_count > 0:
                        # Get actual ticket elements for clicking
                        tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                    else:
                        tickets = []
                else:
                    # Fallback to standard detection
                    tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    # Filter tickets based on criteria
                    matching_tickets = []
                    for ticket in tickets:
                        if self.matches_filters(driver, ticket):
                            matching_tickets.append(ticket)
                    
                    if matching_tickets:
                        self.stats['tickets_found'] += 1
                        logger.info(f"🎫 HUNTER {browser_id}: {len(matching_tickets)} MATCHING TICKETS FOUND!")
                        
                        # Try to buy multiple tickets (up to max)
                        for i, ticket in enumerate(matching_tickets):
                            if self.tickets_secured >= self.max_tickets:
                                break
                                
                            if self.purchase_lock.acquire(blocking=False):
                                try:
                                    if self.tickets_secured < self.max_tickets:
                                        success = self.execute_purchase(driver, ticket, browser_id)
                                        if success:
                                            self.tickets_secured += 1
                                            local_tickets_secured += 1
                                            self.stats['successful_checkouts'] += 1
                                            logger.info(f"✅ HUNTER {browser_id}: Secured ticket {self.tickets_secured}/{self.max_tickets}")
                                            
                                            # Play alarm
                                            self.play_alarm()
                                            
                                            # Take screenshot
                                            screenshot_path = f"checkout_{int(time.time())}.png"
                                            driver.save_screenshot(screenshot_path)
                                            logger.info(f"📸 Screenshot saved: {screenshot_path}")
                                finally:
                                    self.purchase_lock.release()
                    else:
                        logger.debug(f"Hunter {browser_id}: {len(tickets)} tickets found but none match filters")
                        self.stats['no_ticket_found'] += 1
                else:
                    self.stats['no_ticket_found'] += 1
                
                # Reset error counter on successful check
                consecutive_errors = 0
                
                # Progress logging
                if check_count % 50 == 0:
                    elapsed = time.time() - self.stats['start_time']
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    logger.info(f"Hunter {browser_id}: {check_count} checks | {rate:.1f}/min | Secured: {local_tickets_secured}")
                
                # Refresh and wait
                driver.refresh()
                
                # Smart wait time based on number of browsers
                if self.num_browsers == 1:
                    wait_time = random.uniform(2.5, 3.5)
                elif self.num_browsers == 2:
                    wait_time = random.uniform(3.5, 4.5)
                elif self.num_browsers == 3:
                    wait_time = random.uniform(4.5, 5.5)
                else:
                    wait_time = random.uniform(5.5, 7.0)
                
                time.sleep(wait_time)
                
            except TimeoutException:
                consecutive_errors += 1
                if consecutive_errors > 5:
                    logger.warning(f"Hunter {browser_id}: Too many timeouts, refreshing session...")
                    if self.refresh_session(driver, browser_id):
                        consecutive_errors = 0
                else:
                    driver.refresh()
                    time.sleep(2)
                
            except WebDriverException as e:
                if "target window already closed" in str(e).lower():
                    logger.warning(f"Hunter {browser_id}: Browser closed")
                    break
                logger.error(f"Hunter {browser_id}: WebDriver error: {e}")
                consecutive_errors += 1
                if consecutive_errors > 3:
                    if self.refresh_session(driver, browser_id):
                        consecutive_errors = 0
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id}: Error: {e}")
                traceback.print_exc()
                time.sleep(5)
        
        logger.info(f"Hunter {browser_id}: Stopped. Secured {local_tickets_secured} tickets.")
    
    def execute_purchase(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Execute the purchase of a ticket"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Bring window to front
            driver.switch_to.window(driver.current_window_handle)
            
            # First, check if this is a real available ticket
            try:
                # Check if ticket has a price (indicates it's available)
                price_element = ticket_element.find_element(By.CSS_SELECTOR, "[class*='price'], [class*='prezzo']")
                logger.info(f"Ticket price found: {price_element.text}")
            except:
                logger.debug(f"No price found on ticket - might be unavailable")
            
            # Click on ticket element
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", ticket_element)
                logger.info("Clicked on ticket element")
            except Exception as e:
                logger.error(f"Failed to click ticket: {e}")
                return False
            
            # Wait for page to load/modal to appear
            time.sleep(2)
            
            # Check if there's a quantity selector (for multiple tickets)
            try:
                quantity_select = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select[name*='quantity'], select[class*='quantity']"))
                )
                # Try to select maximum quantity (up to 4 - already secured)
                remaining_needed = self.max_tickets - self.tickets_secured
                if remaining_needed > 1:
                    try:
                        # Select the maximum available quantity
                        driver.execute_script(f"""
                            var select = arguments[0];
                            var options = select.options;
                            var maxValue = 1;
                            for (var i = 0; i < options.length; i++) {{
                                var val = parseInt(options[i].value);
                                if (val <= {remaining_needed} && val > maxValue) {{
                                    maxValue = val;
                                }}
                            }}
                            select.value = maxValue;
                            select.dispatchEvent(new Event('change'));
                        """, quantity_select)
                        logger.info(f"Selected quantity: {remaining_needed}")
                    except:
                        pass
            except:
                # No quantity selector, proceed with single ticket
                pass
            
            # Try multiple methods to find and click buy button
            buy_button_clicked = False
            
            # Multiple selectors for buy button
            buy_selectors = [
                "button[data-qa='buyNowButton']",
                "button[class*='buy']",
                "button[class*='acquista']",
                "button[class*='purchase']",
                "a[class*='buy']",
                "a[class*='acquista']",
                "//button[contains(text(), 'Acquista')]",
                "//button[contains(text(), 'ACQUISTA')]",
                "//button[contains(text(), 'Compra')]",
                "//a[contains(text(), 'Acquista')]",
                "//button[contains(@class, 'btn') and contains(@class, 'primary')]",
                "//button[contains(@class, 'purchase')]"
            ]
            
            for selector in buy_selectors:
                try:
                    if selector.startswith('//'):
                        buy_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_button)
                    driver.execute_script("arguments[0].click();", buy_button)
                    logger.info(f"✅ Buy button clicked using selector: {selector}")
                    buy_button_clicked = True
                    break
                except:
                    continue
            
            # Check if ticket was already reserved by someone else
            if not buy_button_clicked:
                page_text = driver.page_source.lower()
                
                # Common indicators that ticket is already reserved
                reserved_indicators = [
                    'già riservato', 'already reserved', 'non disponibile',
                    'sold out', 'esaurito', 'not available', 'no longer available',
                    'ticket non più disponibile', 'prenotato'
                ]
                
                if any(indicator in page_text for indicator in reserved_indicators):
                    self.stats['already_reserved'] += 1
                    logger.info(f"⏱️ Hunter {browser_id}: Ticket already reserved by another user (this is normal)")
                    return False
                else:
                    logger.warning(f"❓ Hunter {browser_id}: Buy button not found - page might have changed")
                    return False
            
            # Check if we reached checkout
            time.sleep(2)
            if self.verify_checkout(driver):
                logger.info(f"✅ Hunter {browser_id}: PURCHASE SUCCESSFUL! In checkout!")
                return True
            else:
                return True  # We clicked buy, might be processing
                
        except Exception as e:
            logger.error(f"Purchase failed for Hunter {browser_id}: {e}")
            return False
    
    def verify_checkout(self, driver: uc.Chrome) -> bool:
        """Verify if we're in checkout/cart"""
        try:
            checkout_indicators = [
                'carrello', 'cart', 'checkout', 'pagamento', 'payment',
                'conferma', 'confirm', 'riepilogo', 'summary'
            ]
            
            current_url = driver.current_url.lower()
            page_text = driver.page_source.lower()
            
            for indicator in checkout_indicators:
                if indicator in current_url or indicator in page_text:
                    return True
                    
            return False
            
        except:
            return False
    
    def clear_browser_profiles(self):
        """Clear all browser profiles"""
        profiles_dir = Path("browser_profiles")
        if profiles_dir.exists():
            try:
                shutil.rmtree(profiles_dir)
                logger.info("✅ All browser profiles cleared")
                print("\n✅ Browser profiles cleared successfully!\n")
            except Exception as e:
                logger.error(f"Failed to clear profiles: {e}")
                print(f"\n❌ Error clearing profiles: {e}\n")
        else:
            print("\n📁 No browser profiles found to clear.\n")
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("🎫 FANSALE BOT - ULTIMATE EDITION")
        print("="*60)
        print("\n1. Start Bot")
        print("2. Clear Browser Profiles")
        print("3. Show Statistics")
        print("4. Test Filters (Debug)")
        print("5. Exit")
        print("\nEnter your choice (1-5): ", end='')
    
    def handle_statistics(self):
        """Show statistics from previous runs"""
        stats_file = Path('stats.json')
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                print("\n📊 SAVED STATISTICS:")
                print(f"   Total Checks: {saved_stats.get('total_checks', 0)}")
                print(f"   No Tickets: {saved_stats.get('no_ticket_found', 0)}")
                print(f"   Tickets Found: {saved_stats.get('tickets_found', 0)}")
                print(f"   Successful Checkouts: {saved_stats.get('successful_checkouts', 0)}")
                print(f"   Already Reserved: {saved_stats.get('already_reserved', 0)}")
            except:
                print("\n❌ Error reading statistics")
        else:
            print("\n📊 No statistics found yet. Run the bot first!")
        
        input("\nPress Enter to continue...")
    
    def test_filters(self):
        """Test filters on current page - debug mode"""
        print("\n🔍 FILTER TEST MODE")
        print("="*40)
        
        # Configure filters first
        self.configure_filters()
        
        if not self.ticket_filters:
            print("\nNo filters configured. Exiting test mode.")
            return
        
        print("\nCreating test browser...")
        driver = self.create_browser(1)
        if not driver:
            print("Failed to create browser")
            return
        
        try:
            print("Navigating to target page...")
            driver.get(self.target_url)
            time.sleep(3)
            
            print("\nSearching for tickets...")
            tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
            
            if not tickets:
                print("❌ No tickets found on page")
            else:
                print(f"\n✅ Found {len(tickets)} tickets total")
                
                matching = 0
                for i, ticket in enumerate(tickets):
                    text = self.get_ticket_text(driver, ticket)
                    matches = self.matches_filters(driver, ticket)
                    
                    print(f"\nTicket {i+1}:")
                    print(f"  Text: {text[:100]}..." if len(text) > 100 else f"  Text: {text}")
                    print(f"  Matches: {'✅ YES' if matches else '❌ NO'}")
                    
                    if matches:
                        matching += 1
                
                print(f"\n📊 Summary: {matching}/{len(tickets)} tickets match your filters")
                
        except Exception as e:
            print(f"Error during test: {e}")
            traceback.print_exc()
        finally:
            driver.quit()
            
        input("\nPress Enter to continue...")
    
    def run_bot(self):
        """Main bot execution"""
        print("\n🔧 BOT CONFIGURATION")
        print("="*40)
        
        # Get number of browsers
        while True:
            try:
                num = input("\n🌐 Number of browsers (1-5, recommended 2-3): ").strip()
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 5:
                    break
                print("❌ Please enter 1-5")
            except ValueError:
                print("❌ Invalid number")
        
        # Proxy option
        proxy_choice = input("\n🔐 Use proxy? (y/n, default n): ").strip().lower()
        self.use_proxy = proxy_choice == 'y'
        
        # Auto-login option - DEFAULT TO YES
        if ENHANCED_MODE:
            auto_login_choice = input("
🤖 Use automatic login? (y/n, default y): ").strip().lower()
            # Default to YES if empty or 'y'
            self.use_auto_login = auto_login_choice != 'n'
        else:
            self.use_auto_login = False
            print("\n⚠️  Enhanced utilities not available - manual login only")
        
        # Ticket filtering
        self.configure_filters()
        
        # Calculate expected performance
        if self.num_browsers == 1:
            checks_per_min = 20
        elif self.num_browsers == 2:
            checks_per_min = 30
        elif self.num_browsers == 3:
            checks_per_min = 35
        else:
            checks_per_min = 40
            
        print(f"\n📋 CONFIGURATION:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Proxy: {'✅ Yes (data-saving)' if self.use_proxy else '❌ No'}")
        print(f"   • Auto-login: {'✅ Yes' if self.use_auto_login else '❌ No (manual)'}")
        print(f"   • Expected rate: ~{checks_per_min} checks/minute")
        print(f"   • Max tickets: {self.max_tickets}")
        
        if self.ticket_filters:
            print(f"   • Filters: {', '.join(self.ticket_filters)} ({self.filter_mode} match)")
        else:
            print(f"   • Filters: None (accepting ALL tickets)")
            
        print(f"   • Target: {self.target_url}")
        print(f"   • Session refresh: Every 15 minutes")
        
        try:
            # Create browsers
            print(f"\n🚀 Starting {self.num_browsers} browsers...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if not driver:
                    logger.error(f"Failed to create browser {i}")
                    continue
                    
                # Manual login
                if not self.manual_login(i, driver):
                    logger.error(f"Failed to login browser {i}")
                    driver.quit()
                    continue
                    
                self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created successfully")
                return
                
            logger.info(f"✅ {len(self.browsers)} browsers ready!")
            input("\n✋ Press Enter to START HUNTING...")
            
            # Start statistics
            self.stats['start_time'] = time.time()
            
            # Start hunter threads
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_and_buy,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                self.browser_threads.append(thread)
            
            # Start stats display thread
            def periodic_stats():
                while not self.shutdown_event.is_set():
                    time.sleep(60)  # Every minute
                    self.log_stats()
            
            stats_thread = threading.Thread(target=periodic_stats, daemon=True)
            stats_thread.start()
            
            logger.info("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            # Wait for completion or interrupt
            while self.tickets_secured < self.max_tickets and not self.shutdown_event.is_set():
                time.sleep(1)
                
            if self.tickets_secured >= self.max_tickets:
                logger.info(f"\n🎉 SUCCESS! All {self.max_tickets} tickets secured!")
                self.play_alarm()
                input("\nPress Enter to close browsers and exit...")
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested...")
            
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
            
        finally:
            # Final stats
            self.log_stats()
            
            # Cleanup
            self.shutdown_event.set()
            logger.info("🧹 Cleaning up...")
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
                    
            logger.info("✅ Shutdown complete")
    
    def run(self):
        """Main entry point with menu"""
        while True:
            self.show_menu()
            
            choice = input().strip()
            
            if choice == '1':
                self.run_bot()
            elif choice == '2':
                self.clear_browser_profiles()
            elif choice == '3':
                self.handle_statistics()
            elif choice == '4':
                self.test_filters()
            elif choice == '5':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")


def main():
    """Entry point"""
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install undetected-chromedriver selenium-wire python-dotenv")
        sys.exit(1)
    
    # Check credentials
    load_dotenv()
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        print("❌ Missing credentials!")
        print("\nCreate a .env file with:")
        print("FANSALE_EMAIL=your@email.com")
        print("FANSALE_PASSWORD=yourpassword")
        print("FANSALE_TARGET_URL=https://www.fansale.it/...")
        sys.exit(1)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()
