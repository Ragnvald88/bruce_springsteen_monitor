#stealthmaster/fansale_no_login_fixed.py
"""
Fansale ticket hunting bot
"""

import json
import time
import random
import logging
import hashlib
import os
import sys
import threading
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class BotConfig:
    """Bot configuration with all settings"""
    def __init__(self):
        self.browsers_count = 2
        self.max_tickets = 4
        self.refresh_interval = 60  # seconds
        self.session_timeout = 900  # 15 minutes
        
        # Check frequency settings
        self.checks_per_minute = 120  # Default: 2 checks per second
        self.min_wait = 0.4  # Minimum wait between checks
        self.max_wait = 0.6  # Maximum wait between checks
        
        # Logging settings
        self.log_level = "INFO"
        self.status_update_interval = 50  # Update status every N checks
        self.detailed_logging = False
        self.debug_mode = False  # NEW: For debugging ticket detection
        
        self.retry_attempts = 2
        self.retry_delay = 0.5
        self.ticket_types_to_hunt = ['prato_b', 'prato_a']
        self.ticket_filters = []
    
    def calculate_wait_time(self):
        """Calculate wait time based on desired checks per minute"""
        # Calculate base wait time for desired rate
        base_wait = 60.0 / self.checks_per_minute
        
        # Add some randomization within min/max bounds
        return max(self.min_wait, min(self.max_wait, 
                   base_wait + random.uniform(-0.1, 0.1)))
    
    def to_dict(self):
        return {
            'browsers_count': self.browsers_count,
            'max_tickets': self.max_tickets,
            'refresh_interval': self.refresh_interval,
            'session_timeout': self.session_timeout,
            'checks_per_minute': self.checks_per_minute,
            'min_wait': self.min_wait,
            'max_wait': self.max_wait,
            'log_level': self.log_level,
            'status_update_interval': self.status_update_interval,
            'detailed_logging': self.detailed_logging,
            'debug_mode': self.debug_mode,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'ticket_types_to_hunt': self.ticket_types_to_hunt,
            'ticket_filters': self.ticket_filters
        }
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Enhanced retry decorator
def retry(max_attempts=3, delay=1.0, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                        time.sleep(delay)
                    else:
                        raise
            return None
        return wrapper
    return decorator

# Statistics Manager
class StatsManager:
    """Manages bot statistics with persistence"""
    def __init__(self, stats_file='fansale_stats_fixed.json'):
        self.stats_file = stats_file
        self.stats = self.load_stats()
    
    def load_stats(self):
        """Load statistics from file"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'total_checks': 0,
            'total_tickets_found': 0,
            'unique_tickets_found': 0,
            'tickets_by_type': {'prato_a': 0, 'prato_b': 0, 'settore': 0},
            'purchases': 0,
            'blocks_encountered': 0,
            'all_time_runtime': 0.0,
            'sessions': []
        }
    
    def save_stats(self):
        """Save statistics to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

# Color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Notification Manager
class NotificationManager:
    """Handles system notifications for important events"""
    
    @staticmethod
    def send_notification(title, message):
        """Send desktop notification"""
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{message}" with title "{title}"'
                ])
            elif sys.platform.startswith('linux'):
                subprocess.run(['notify-send', title, message])
            # Windows would use win10toast or similar
        except:
            pass  # Fail silently if notifications not available

# Health Monitor
class HealthMonitor:
    """Monitors bot health and performance"""
    def __init__(self):
        self.start_time = time.time()
        self.check_counts = {}
        self.error_counts = {}
        self.last_ticket_time = {}
    
    def record_check(self, browser_id):
        self.check_counts[browser_id] = self.check_counts.get(browser_id, 0) + 1
    
    def record_error(self, browser_id, error_type):
        if browser_id not in self.error_counts:
            self.error_counts[browser_id] = {}
        self.error_counts[browser_id][error_type] = \
            self.error_counts[browser_id].get(error_type, 0) + 1
    
    def get_health_status(self):
        """Get overall health status"""
        runtime = time.time() - self.start_time
        total_checks = sum(self.check_counts.values())
        total_errors = sum(sum(errors.values()) for errors in self.error_counts.values())
        
        if runtime > 0:
            checks_per_minute = (total_checks / runtime) * 60
            error_rate = total_errors / max(total_checks, 1)
            
            return {
                'runtime': runtime,
                'total_checks': total_checks,
                'checks_per_minute': checks_per_minute,
                'total_errors': total_errors,
                'error_rate': error_rate,
                'status': 'healthy' if error_rate < 0.1 else 'degraded'
            }
        
        return {'status': 'starting'}

# Enhanced Colored Formatter with log levels
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and improved formatting"""
    
    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.RED + Colors.BOLD
    }
    
    def format(self, record):
        # Add color based on level
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.END}"
        
        # Color specific message patterns
        if record.levelname == 'INFO':
            if 'PRATO A' in record.msg:
                record.msg = f"{Colors.GREEN}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'PRATO B' in record.msg:
                record.msg = f"{Colors.BLUE}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'SETTORE' in record.msg:
                record.msg = f"{Colors.YELLOW}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'NEW TICKET' in record.msg:
                record.msg = f"{Colors.CYAN}{Colors.BOLD}{record.msg}{Colors.END}"
            elif '🎫' in record.msg:
                record.msg = f"{Colors.BOLD}{record.msg}{Colors.END}"
        
        return super().format(record)

# Configure logging
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)
logger.handlers.clear()

# Console handler with colors
console_handler = logging.StreamHandler()
console_formatter = ColoredFormatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('fansale_bot.log')
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

class FanSaleBot:
    """Main bot class with fixed block detection and fast purchasing"""
    
    def __init__(self):
        # Load configuration
        self.config = BotConfig()
        self._load_saved_config()
        
        # Apply log level from config
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Target URL from environment or default
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
            'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388')
        
        # Initialize from config
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_filters = self.config.ticket_filters
        self.ticket_types_to_hunt = self.config.ticket_types_to_hunt
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Tracking
        self.seen_tickets = set()
        self.ticket_details_cache = {}
        
        # Statistics
        self.stats_file = 'fansale_stats_fixed.json'
        self.stats_manager = StatsManager(self.stats_file)
        self.stats = self.stats_manager.stats
        
        # Session tracking
        self.session_start_time = time.time()
        
        # Health monitoring
        self.health_monitor = HealthMonitor()
        self.notification_manager = NotificationManager()

    
    def _load_saved_config(self):
        """Load saved configuration"""
        config_file = 'bot_config_fixed.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.config.from_dict(data)
                    logger.info("✅ Loaded saved configuration")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
    
    def _save_config(self):
        """Save current configuration"""
        try:
            with open('bot_config_fixed.json', 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            logger.info("✅ Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _keep_browser_alive(self, driver, browser_id):
        """Check if browser is still responsive"""
        try:
            driver.execute_script("return 1")
            return True
        except:
            logger.error(f"Browser {browser_id} is not responsive")
            return False
    
    def detect_chrome_version(self):
        """Detect installed Chrome version"""
        try:
            if sys.platform == 'darwin':
                result = subprocess.run(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    capture_output=True, text=True
                )
            elif sys.platform == 'win32':
                result = subprocess.run(
                    [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--version"],
                    capture_output=True, text=True
                )
            else:
                result = subprocess.run(
                    ["google-chrome", "--version"],
                    capture_output=True, text=True
                )
            
            if result.returncode == 0:
                version_string = result.stdout.strip()
                version_parts = version_string.split()[-1].split('.')
                if version_parts:
                    return int(version_parts[0])
        except Exception as e:
            logger.debug(f"Could not detect Chrome version: {e}")
        
        return None
    
    def save_stats(self):
        """Save statistics with session info"""
        try:
            # Update session info
            session_runtime = time.time() - self.session_start_time
            current_session = {
                'start_time': datetime.fromtimestamp(self.session_start_time).isoformat(),
                'runtime': session_runtime,
                'tickets_found': self.stats['unique_tickets_found'],
                'purchases': self.stats['purchases'],
                'checks': self.stats['total_checks']
            }
            
            # Keep only last 10 sessions
            if 'sessions' not in self.stats:
                self.stats['sessions'] = []
            
            # Update or add current session
            if self.stats['sessions'] and \
               self.stats['sessions'][-1]['start_time'] == current_session['start_time']:
                self.stats['sessions'][-1] = current_session
            else:
                self.stats['sessions'].append(current_session)
                if len(self.stats['sessions']) > 10:
                    self.stats['sessions'] = self.stats['sessions'][-10:]
            
            # Update all-time runtime
            self.stats['all_time_runtime'] = sum(s['runtime'] for s in self.stats['sessions'])
            
            # Save to file
            self.stats_manager.stats = self.stats
            self.stats_manager.save_stats()
            
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def categorize_ticket(self, ticket_text):
        """Categorize ticket based on text content"""
        text_lower = ticket_text.lower()
        
        if 'prato a' in text_lower:
            return 'prato_a'
        elif 'prato b' in text_lower:
            return 'prato_b'
        elif 'settore' in text_lower or 'tribuna' in text_lower:
            return 'settore'
        else:
            return 'settore'
    
    def generate_ticket_hash(self, ticket_text):
        """Generate unique hash for ticket identification"""
        # Normalize text by removing extra spaces and converting to lowercase
        normalized = ' '.join(ticket_text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def extract_full_ticket_info(self, driver, ticket_element):
        """Extract comprehensive ticket information"""
        try:
            ticket_info = {
                'raw_text': '',
                'price': 'N/A',
                'location': 'N/A',
                'quantity': 1,
                'category': 'unknown',
                'element': ticket_element,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get raw text
            try:
                ticket_info['raw_text'] = ticket_element.text.strip()
            except:
                ticket_info['raw_text'] = 'Text extraction failed'
            
            # Extract price
            try:
                price_elem = ticket_element.find_element(By.CSS_SELECTOR, "[data-qa='ticketPrice']")
                ticket_info['price'] = price_elem.text.strip()
            except:
                pass
            
            # Extract location details
            try:
                location_elem = ticket_element.find_element(By.CSS_SELECTOR, "[data-qa='ticketLocation']")
                ticket_info['location'] = location_elem.text.strip()
            except:
                pass
            
            # Extract quantity
            try:
                quantity_elem = ticket_element.find_element(By.CSS_SELECTOR, "[data-qa='ticketQuantity']")
                qty_text = quantity_elem.text.strip()
                if qty_text.isdigit():
                    ticket_info['quantity'] = int(qty_text)
            except:
                pass
            
            # Categorize based on full text
            full_text = f"{ticket_info['raw_text']} {ticket_info['location']}"
            ticket_info['category'] = self.categorize_ticket(full_text)
            
            return ticket_info
            
        except Exception as e:
            logger.error(f"Error extracting ticket info: {e}")
            return {
                'raw_text': 'Error extracting info',
                'price': 'N/A',
                'location': 'N/A',
                'quantity': 1,
                'category': 'unknown',
                'element': ticket_element,
                'timestamp': datetime.now().isoformat()
            }
    
    def log_new_ticket(self, ticket_info, browser_id):
        """Log newly discovered ticket with emojis and colors"""
        category = ticket_info['category']
        
        # Choose emoji and color based on category
        if category == 'prato_a':
            emoji = '🟢'
            category_display = f"{Colors.GREEN}{Colors.BOLD}PRATO A{Colors.END}"
        elif category == 'prato_b':
            emoji = '🔵'
            category_display = f"{Colors.BLUE}{Colors.BOLD}PRATO B{Colors.END}"
        else:
            emoji = '🟡'
            category_display = f"{Colors.YELLOW}{Colors.BOLD}SETTORE{Colors.END}"
        
        # Build log message
        log_parts = [
            f"\n{Colors.CYAN}{'='*60}{Colors.END}",
            f"{emoji} {Colors.BOLD}NEW TICKET FOUND!{Colors.END} {emoji}",
            f"Browser: {browser_id} | Type: {category_display}",
            f"Price: {Colors.BOLD}{ticket_info['price']}{Colors.END}",
            f"Location: {ticket_info['location']}",
            f"Quantity: {ticket_info['quantity']}",
            f"Time: {datetime.now().strftime('%H:%M:%S')}",
            f"{Colors.CYAN}{'='*60}{Colors.END}"
        ]
        
        # Log to console
        for line in log_parts:
            logger.info(line)
        
        # Send notification for matching tickets
        if category in self.ticket_types_to_hunt:
            self.notification_manager.send_notification(
                "🎫 FanSale Ticket Found!",
                f"{category.upper()} ticket available - {ticket_info['price']}"
            )
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create browser with optimized configuration and NO POPUPS"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Detect Chrome version once
                if not hasattr(self, '_chrome_version'):
                    self._chrome_version = self.detect_chrome_version()
                    if self._chrome_version:
                        logger.info(f"🔍 Detected Chrome version: {self._chrome_version}")
                
                # Create fresh options for each retry
                options = uc.ChromeOptions()
                
                # Workaround for undetected_chromedriver v3.5.3 bug
                if not hasattr(options, 'headless'):
                    options.headless = False
                
                # CRITICAL FLAGS TO PREVENT POPUPS
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-notifications')  # Disable notifications
                options.add_argument('--disable-popup-blocking')  # But allow our actions
                options.add_argument('--disable-save-password-bubble')  # No password prompts
                options.add_argument('--disable-translate')  # No translation bar
                options.add_argument('--disable-features=TranslateUI')
                options.add_argument('--disable-infobars')  # No info bars
                
                # Preferences to disable popups
                prefs = {
                    'profile.default_content_setting_values.notifications': 2,
                    'profile.default_content_settings.popups': 0,
                    'profile.managed_default_content_settings.popups': 0,
                    'credentials_enable_service': False,
                    'profile.password_manager_enabled': False,
                    'translate': {'enabled': False}
                }
                options.add_experimental_option('prefs', prefs)
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Window positioning
                if browser_id == 1:
                    x, y = 50, 50
                elif browser_id == 2:
                    x, y = 550, 150
                else:
                    x = 50 + ((browser_id - 1) * 500)
                    y = 50 + ((browser_id - 1) // 3 * 400)
                
                logger.info(f"🖥️  Browser {browser_id} will appear at position ({x}, {y})")
                options.add_argument(f'--window-position={x},{y}')
                options.add_argument(f'--window-size=450,800')
                
                # Use temp dir for profile to avoid conflicts
                temp_dir = tempfile.mkdtemp(prefix=f"browser_{browser_id}_")
                options.add_argument(f'--user-data-dir={temp_dir}')
                
                # Create driver with version hint for faster startup
                logger.info("Creating Chrome instance...")
                
                if self._chrome_version:
                    driver = uc.Chrome(options=options, version_main=self._chrome_version, 
                                     headless=False, use_subprocess=False)
                else:
                    driver = uc.Chrome(options=options, headless=False, use_subprocess=False)
                
                # Set page load timeout
                driver.set_page_load_timeout(15)
                
                # Quick test
                driver.get("data:text/html,<h1>Browser Ready</h1>")
                
                logger.info(f"✅ Browser {browser_id} ready at position ({x}, {y})")
                return driver
                
            except AttributeError as e:
                if "headless" in str(e):
                    logger.error(f"⚠️ ChromeOptions headless attribute issue: {e}")
                    # Try minimal Chrome instance
                    try:
                        logger.info("Trying minimal Chrome instance...")
                        driver = uc.Chrome(headless=False, use_subprocess=False)
                        driver.set_window_position(x, y)
                        driver.set_window_size(450, 800)
                        logger.info(f"✅ Browser {browser_id} ready (minimal config)")
                        return driver
                    except Exception as e2:
                        logger.error(f"❌ Minimal approach also failed: {e2}")
                else:
                    raise
                    
            except Exception as e:
                logger.error(f"❌ Browser creation attempt {retry + 1} failed: {e}")
                
                if retry < max_retries - 1:
                    logger.info(f"🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    # Final failure - provide guidance
                    if "version" in str(e).lower():
                        logger.error("\n" + "="*60)
                        logger.error("🔧 CHROMEDRIVER VERSION ISSUE")
                        logger.error("Try: python3 fix_chromedriver.py")
                        logger.error("="*60 + "\n")
                    elif "chrome not reachable" in str(e).lower():
                        logger.error("\n" + "="*60)
                        logger.error("🔧 CHROME PROCESS ISSUE")
                        logger.error("Try: python3 cleanup_chrome.py")
                        logger.error("="*60 + "\n")
                    
                    return None

    
    def is_blocked(self, driver):
        """Fixed block detection - matches original logic"""
        try:
            # Check URL for specific error patterns
            current_url = driver.current_url.lower()
            if any(x in current_url for x in ['404', 'error', 'blocked']):
                logger.debug(f"Block detected in URL: {current_url}")
                return True
            
            # Check title for Italian error messages
            title_lower = driver.title.lower()
            if any(x in title_lower for x in ['404', 'error', 'non trovata']):
                logger.debug(f"Block detected in title: {driver.title}")
                return True
            
            # Check page content for 404 ONLY if it's not "no tickets found"
            page_source = driver.page_source.lower()
            if '404' in page_source and 'non sono state trovate' not in page_source:
                # Additional check: make sure it's actually a 404 page
                if 'page not found' in page_source or 'pagina non trovata' in page_source:
                    logger.debug("404 error page detected")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Block check error: {e}")
            return False
    
    def clear_browser_data(self, driver, browser_id):
        """Clear browser data to avoid detection"""
        try:
            logger.info(f"🧹 Clearing data for Browser {browser_id}...")
            
            # Clear cookies
            driver.delete_all_cookies()
            
            # Clear local storage
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            
            # Clear cache via DevTools
            driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
            
            logger.info(f"✅ Browser {browser_id} data cleared")
            
        except Exception as e:
            logger.error(f"Error clearing browser data: {e}")
    
    def _get_random_user_agent(self):
        """Get random user agent for variety"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(user_agents)
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop with FAST ticket detection and purchasing"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        logger.info(f"📊 Target rate: {self.config.checks_per_minute} checks/minute")
        
        # Navigate to event page
        logger.info(f"📍 Navigating to: {self.target_url}")
        
        for nav_attempt in range(3):
            try:
                if not self._keep_browser_alive(driver, browser_id):
                    logger.error(f"Browser {browser_id} session dead")
                    return
                
                driver.get(self.target_url)
                time.sleep(random.uniform(1.0, 1.5))  # Give page time to load
                
                if "fansale" in driver.current_url.lower():
                    logger.info(f"✅ Browser {browser_id} successfully navigated")
                    break
                else:
                    logger.warning(f"Navigation attempt {nav_attempt + 1} failed")
                    
            except Exception as e:
                logger.error(f"Navigation error: {e}")
                if nav_attempt < 2:
                    time.sleep(2)
                else:
                    return
        
        # Main hunting loop
        check_count = 0
        last_status_update = 0
        last_session_refresh = time.time()
        local_stats = {'prato_a': 0, 'prato_b': 0, 'settore': 0}
        consecutive_errors = 0
        empty_checks = 0  # Track empty results
        last_block_check = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                self.health_monitor.record_check(browser_id)
                
                # Only check for blocks periodically (not every check)
                if time.time() - last_block_check > 30:  # Check every 30 seconds
                    if self.is_blocked(driver):
                        logger.warning(f"⚠️ Hunter {browser_id}: Block detected!")
                        self.stats['blocks_encountered'] += 1
                        self.health_monitor.record_error(browser_id, 'block')
                        self.clear_browser_data(driver, browser_id)
                        driver.get(self.target_url)
                        time.sleep(random.uniform(2.0, 3.0))
                        last_block_check = time.time()
                        continue
                    last_block_check = time.time()
                
                # Session refresh
                if time.time() - last_session_refresh > self.config.session_timeout:
                    logger.info(f"🔄 Hunter {browser_id}: Session refresh...")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(3)
                    last_session_refresh = time.time()
                    continue
                
                # Look for tickets - CORE FUNCTIONALITY
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                # Debug mode logging
                if self.config.debug_mode and check_count % 10 == 0:
                    logger.debug(f"Browser {browser_id}: Found {len(tickets)} ticket elements")
                    if not tickets:
                        # Check if we're on the right page
                        if "tickets" in driver.current_url:
                            logger.debug("On tickets page but no tickets found")
                        else:
                            logger.warning(f"Not on tickets page! URL: {driver.current_url}")
                
                if tickets:
                    empty_checks = 0  # Reset empty counter
                    self.stats['total_tickets_found'] += len(tickets)
                    
                    for ticket in tickets:
                        try:
                            ticket_info = self.extract_full_ticket_info(driver, ticket)
                            ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                            
                            if ticket_hash not in self.seen_tickets:
                                # NEW TICKET DISCOVERED!
                                self.seen_tickets.add(ticket_hash)
                                self.ticket_details_cache[ticket_hash] = ticket_info
                                
                                self.stats['unique_tickets_found'] += 1
                                category = ticket_info['category']
                                self.stats['tickets_by_type'][category] += 1
                                local_stats[category] += 1
                                
                                self.log_new_ticket(ticket_info, browser_id)
                                self.save_stats()
                                
                                # FAST PURCHASE ATTEMPT
                                if category in self.ticket_types_to_hunt:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.max_tickets:
                                            logger.info(f"🎯 ATTEMPTING TO SECURE {category.upper()} TICKET!")
                                            
                                            # Click immediately!
                                            try:
                                                # Scroll into view first
                                                driver.execute_script("arguments[0].scrollIntoView(true);", ticket)
                                                time.sleep(0.1)  # Brief pause for scroll
                                                
                                                # Click the ticket
                                                ticket.click()
                                                logger.info("✅ Clicked on ticket!")
                                                
                                                # Wait for and click purchase button
                                                try:
                                                    purchase_btn = WebDriverWait(driver, 5).until(
                                                        EC.element_to_be_clickable((By.CSS_SELECTOR, 
                                                            "[data-qa='purchaseButton'], button[class*='purchase'], button[class*='buy']"))
                                                    )
                                                    purchase_btn.click()
                                                    logger.info("✅ PURCHASE BUTTON CLICKED!")
                                                    
                                                    # Take screenshot
                                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                    screenshot_path = f"screenshots/purchase_{timestamp}.png"
                                                    os.makedirs("screenshots", exist_ok=True)
                                                    driver.save_screenshot(screenshot_path)
                                                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                                                    
                                                    self.tickets_secured += 1
                                                    self.stats['purchases'] += 1
                                                    self.save_stats()
                                                    
                                                    logger.info(f"🎉 TICKET SECURED! ({self.tickets_secured}/{self.max_tickets})")
                                                    
                                                    if self.tickets_secured >= self.max_tickets:
                                                        logger.info("🏁 Maximum tickets secured! Shutting down...")
                                                        self.shutdown_event.set()
                                                        return
                                                        
                                                except TimeoutException:
                                                    logger.warning("Purchase button not found in time")
                                                except Exception as e:
                                                    logger.error(f"Purchase flow error: {e}")
                                                    
                                            except Exception as e:
                                                logger.error(f"Failed to click ticket: {e}")
                                
                        except Exception as e:
                            logger.error(f"Error processing ticket: {e}")
                else:
                    # Track empty results
                    empty_checks += 1
                    
                    # If too many empty checks, might be a soft block
                    if empty_checks > 100:
                        logger.warning(f"Browser {browser_id}: Many empty results, possible soft block")
                        empty_checks = 0
                        # Do a light refresh
                        driver.refresh()
                        time.sleep(2)
                
                # Reset error count on successful check
                consecutive_errors = 0
                
                # Status update at configured interval
                if check_count - last_status_update >= self.config.status_update_interval:
                    last_status_update = check_count
                    elapsed = time.time() - self.session_start_time
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    
                    # Build status
                    local_summary = []
                    if local_stats['prato_a'] > 0:
                        local_summary.append(f"PA:{local_stats['prato_a']}")
                    if local_stats['prato_b'] > 0:
                        local_summary.append(f"PB:{local_stats['prato_b']}")
                    if local_stats['settore'] > 0:
                        local_summary.append(f"S:{local_stats['settore']}")
                    
                    status = " | ".join(local_summary) if local_summary else "Hunting..."
                    
                    # Speed indicator
                    if rate > self.config.checks_per_minute * 1.2:
                        speed_icon = '🚀'
                    elif rate > self.config.checks_per_minute * 0.8:
                        speed_icon = '✅'
                    else:
                        speed_icon = '⚠️'
                    
                    logger.info(f"Browser {browser_id} | Checks: {check_count:>5} | "
                               f"{speed_icon} {rate:>4.0f}/min | {status}")
                
                # Use configured wait time
                wait_time = self.config.calculate_wait_time()
                time.sleep(wait_time)
                
            except TimeoutException:
                consecutive_errors += 1
                logger.warning(f"Hunter {browser_id}: Timeout (#{consecutive_errors})")
                self.health_monitor.record_error(browser_id, 'timeout')
                
                if consecutive_errors > 5:
                    logger.error(f"Hunter {browser_id}: Too many errors, refreshing...")
                    driver.refresh()
                    consecutive_errors = 0
                    
                time.sleep(random.uniform(1.0, 2.0))
                
            except WebDriverException as e:
                consecutive_errors += 1
                error_str = str(e).lower()
                
                if "net::err" in error_str:
                    logger.error(f"Hunter {browser_id}: Network error")
                    self.health_monitor.record_error(browser_id, 'network')
                elif "invalid session" in error_str:
                    logger.error(f"Hunter {browser_id}: Session died")
                    self.health_monitor.record_error(browser_id, 'session')
                    break
                else:
                    logger.error(f"Hunter {browser_id}: Browser error")
                    self.health_monitor.record_error(browser_id, 'browser')
                    
                time.sleep(2.0)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Hunter {browser_id} unexpected error: {e}")
                self.health_monitor.record_error(browser_id, 'unknown')
                time.sleep(1.0)

    
    def show_statistics_dashboard(self):
        """Enhanced statistics dashboard"""
        os.system('clear' if os.name != 'nt' else 'cls')
        
        print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}📊 FANSALE BOT STATISTICS DASHBOARD{Colors.END}")
        print(f"{Colors.CYAN}{'='*70}{Colors.END}\n")
        
        # Session info
        session_runtime = time.time() - self.session_start_time
        print(f"{Colors.BOLD}Current Session:{Colors.END}")
        print(f"  Runtime: {self._format_duration(session_runtime)}")
        print(f"  Checks: {self.stats['total_checks']:,}")
        print(f"  Rate: {(self.stats['total_checks'] / session_runtime * 60):.1f} checks/min")
        
        # All-time stats
        print(f"\n{Colors.BOLD}All-Time Statistics:{Colors.END}")
        print(f"  Total Runtime: {self._format_duration(self.stats['all_time_runtime'])}")
        print(f"  Total Checks: {self.stats['total_checks']:,}")
        print(f"  Unique Tickets Found: {self.stats['unique_tickets_found']}")
        print(f"  Purchases: {self.stats['purchases']}")
        print(f"  Blocks Encountered: {self.stats['blocks_encountered']}")
        
        # Ticket breakdown
        print(f"\n{Colors.BOLD}Tickets by Type:{Colors.END}")
        for ticket_type, count in self.stats['tickets_by_type'].items():
            emoji = {'prato_a': '🟢', 'prato_b': '🔵', 'settore': '🟡'}.get(ticket_type, '⚪')
            print(f"  {emoji} {ticket_type.upper()}: {count}")
        
        # Health status
        health = self.health_monitor.get_health_status()
        if health['status'] != 'starting':
            print(f"\n{Colors.BOLD}System Health:{Colors.END}")
            status_color = Colors.GREEN if health['status'] == 'healthy' else Colors.YELLOW
            print(f"  Status: {status_color}{health['status'].upper()}{Colors.END}")
            print(f"  Error Rate: {health.get('error_rate', 0)*100:.1f}%")
    
    def _format_duration(self, seconds):
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def configure_performance(self):
        """Configure performance settings"""
        print(f"\n{Colors.BOLD}⚡ PERFORMANCE CONFIGURATION{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}")
        
        print(f"\nCurrent settings:")
        print(f"  Checks per minute: {self.config.checks_per_minute}")
        print(f"  Min wait: {self.config.min_wait}s")
        print(f"  Max wait: {self.config.max_wait}s")
        
        print(f"\n{Colors.BOLD}Presets:{Colors.END}")
        print("  1. Conservative (60 checks/min) - Safest")
        print("  2. Balanced (120 checks/min) - Recommended")
        print("  3. Aggressive (240 checks/min) - Faster but riskier")
        print("  4. Custom")
        print("  5. Back")
        
        choice = input(f"\n{Colors.BOLD}Select option:{Colors.END} ").strip()
        
        if choice == '1':
            self.config.checks_per_minute = 60
            self.config.min_wait = 0.8
            self.config.max_wait = 1.2
            print(f"{Colors.GREEN}✅ Conservative mode set{Colors.END}")
        elif choice == '2':
            self.config.checks_per_minute = 120
            self.config.min_wait = 0.4
            self.config.max_wait = 0.6
            print(f"{Colors.GREEN}✅ Balanced mode set{Colors.END}")
        elif choice == '3':
            self.config.checks_per_minute = 240
            self.config.min_wait = 0.2
            self.config.max_wait = 0.3
            print(f"{Colors.YELLOW}⚠️ Aggressive mode set - monitor for blocks!{Colors.END}")
        elif choice == '4':
            try:
                cpm = int(input("Checks per minute (30-600): "))
                self.config.checks_per_minute = max(30, min(600, cpm))
                print(f"{Colors.GREEN}✅ Set to {self.config.checks_per_minute} checks/min{Colors.END}")
            except:
                print(f"{Colors.RED}Invalid input{Colors.END}")
        
        self._save_config()
    
    def configure_ticket_filters(self):
        """Configure ticket type selection"""
        print(f"\n{Colors.BOLD}🎫 TICKET TYPE CONFIGURATION{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}")
        
        # Show current selection
        print(f"\n{Colors.BOLD}Currently hunting:{Colors.END}")
        for ticket_type in self.config.ticket_types_to_hunt:
            emoji = {'prato_a': '🟢', 'prato_b': '🔵', 'settore': '🟡'}.get(ticket_type, '⚪')
            print(f"  {emoji} {ticket_type.upper()}")
        
        print(f"\n{Colors.BOLD}Available ticket types:{Colors.END}")
        print("  1. PRATO A (Field A) 🟢")
        print("  2. PRATO B (Field B) 🔵")
        print("  3. SETTORE (Sector/Tribune) 🟡")
        print("  4. All types")
        print("  5. Back")
        
        choice = input(f"\n{Colors.BOLD}Select types to hunt (comma-separated):{Colors.END} ").strip()
        
        if choice == '5':
            return
        elif choice == '4':
            self.config.ticket_types_to_hunt = ['prato_a', 'prato_b', 'settore']
            print(f"{Colors.GREEN}✅ Hunting all ticket types{Colors.END}")
        else:
            type_map = {'1': 'prato_a', '2': 'prato_b', '3': 'settore'}
            selected = []
            
            for c in choice.split(','):
                c = c.strip()
                if c in type_map:
                    selected.append(type_map[c])
            
            if selected:
                self.config.ticket_types_to_hunt = selected
                self.ticket_types_to_hunt = selected
                print(f"{Colors.GREEN}✅ Now hunting: {', '.join(selected)}{Colors.END}")
            else:
                print(f"{Colors.RED}No valid types selected{Colors.END}")
        
        self._save_config()
    
    def show_menu(self):
        """Main menu"""
        while True:
            os.system('clear' if os.name != 'nt' else 'cls')
            
            print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
            print(f"{Colors.BOLD}🎯 FANSALE TICKET HUNTER - FIXED{Colors.END}")
            print(f"{Colors.CYAN}{'='*60}{Colors.END}")
            
            # Show current config summary
            print(f"\n{Colors.BOLD}Current Configuration:{Colors.END}")
            print(f"  Browsers: {self.config.browsers_count}")
            print(f"  Check rate: {self.config.checks_per_minute}/min")
            print(f"  Hunting: {', '.join(self.config.ticket_types_to_hunt)}")
            print(f"  Max tickets: {self.config.max_tickets}")
            
            print(f"\n{Colors.BOLD}Menu:{Colors.END}")
            print("  1. 🚀 Start Hunting")
            print("  2. ⚙️  Configure Settings")
            print("  3. 📊 View Statistics")
            print("  4. 🐛 Toggle Debug Mode")
            print("  5. ❌ Exit")
            
            choice = input(f"\n{Colors.BOLD}Select option (1-5):{Colors.END} ").strip()
            
            if choice == '1':
                return True  # Start hunting
            elif choice == '2':
                self.configure_settings()
            elif choice == '3':
                self.show_statistics_dashboard()
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.END}")
            elif choice == '4':
                self.config.debug_mode = not self.config.debug_mode
                status = "ON" if self.config.debug_mode else "OFF"
                print(f"{Colors.GREEN}✅ Debug mode {status}{Colors.END}")
                self._save_config()
                time.sleep(1)
            elif choice == '5':
                return False  # Exit
            else:
                print(f"{Colors.RED}Invalid option{Colors.END}")
                time.sleep(1)
    
    def configure_settings(self):
        """Settings menu"""
        while True:
            print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
            print(f"{Colors.BOLD}⚙️  CONFIGURATION MENU{Colors.END}")
            print(f"{Colors.CYAN}{'='*60}{Colors.END}")
            
            print(f"\n{Colors.BOLD}Settings:{Colors.END}")
            print("  1. 🎫 Ticket Types")
            print("  2. ⚡ Performance")
            print("  3. 🌐 Number of Browsers")
            print("  4. 🎯 Max Tickets")
            print("  5. ← Back")
            
            choice = input(f"\n{Colors.BOLD}Select option:{Colors.END} ").strip()
            
            if choice == '1':
                self.configure_ticket_filters()
            elif choice == '2':
                self.configure_performance()
            elif choice == '3':
                try:
                    count = int(input("Number of browsers (1-5): "))
                    self.config.browsers_count = max(1, min(5, count))
                    self.num_browsers = self.config.browsers_count
                    print(f"{Colors.GREEN}✅ Set to {self.config.browsers_count} browser(s){Colors.END}")
                    self._save_config()
                except:
                    print(f"{Colors.RED}Invalid input{Colors.END}")
                time.sleep(1)
            elif choice == '4':
                try:
                    max_t = int(input(f"Max tickets to purchase (1-10): "))
                    self.config.max_tickets = max(1, min(10, max_t))
                    self.max_tickets = self.config.max_tickets
                    print(f"{Colors.GREEN}✅ Max tickets set to {self.config.max_tickets}{Colors.END}")
                    self._save_config()
                except:
                    print(f"{Colors.RED}Invalid input{Colors.END}")
                time.sleep(1)
            elif choice == '5':
                break
            else:
                print(f"{Colors.RED}Invalid option{Colors.END}")
                time.sleep(1)
    
    def run(self):
        """Main run method"""
        print_banner()
        
        # Show menu
        if not self.show_menu():
            print(f"\n{Colors.CYAN}Goodbye!{Colors.END}")
            return
        
        # Start hunting
        print(f"\n{Colors.BOLD}🚀 Starting {self.num_browsers} browser(s)...{Colors.END}")
        
        # Create browsers
        with ThreadPoolExecutor(max_workers=self.num_browsers) as executor:
            browser_futures = []
            
            for i in range(1, self.num_browsers + 1):
                future = executor.submit(self.create_browser, i)
                browser_futures.append((i, future))
            
            # Collect created browsers
            for browser_id, future in browser_futures:
                try:
                    browser = future.result(timeout=30)
                    if browser:
                        self.browsers.append((browser_id, browser))
                    else:
                        logger.error(f"Failed to create browser {browser_id}")
                except Exception as e:
                    logger.error(f"Error creating browser {browser_id}: {e}")
        
        if not self.browsers:
            logger.error("❌ No browsers created. Exiting...")
            return
        
        logger.info(f"✅ {len(self.browsers)} browser(s) ready!")
        
        # Start hunting threads
        hunt_threads = []
        for browser_id, driver in self.browsers:
            thread = threading.Thread(
                target=self.hunt_tickets,
                args=(browser_id, driver),
                name=f"Hunter-{browser_id}"
            )
            thread.start()
            hunt_threads.append(thread)
        
        # Monitor loop
        try:
            print(f"\n{Colors.BOLD}🎯 Hunting in progress...{Colors.END}")
            print(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.END}\n")
            
            while not self.shutdown_event.is_set():
                time.sleep(5)
                
                # Check if all threads are alive
                alive_threads = sum(1 for t in hunt_threads if t.is_alive())
                if alive_threads == 0:
                    logger.warning("All hunting threads have stopped!")
                    break
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested...")
        
        # Cleanup
        self.shutdown_event.set()
        
        # Wait for threads to finish
        logger.info("Waiting for hunters to finish...")
        for thread in hunt_threads:
            thread.join(timeout=10)
        
        # Close browsers
        logger.info("Closing browsers...")
        for browser_id, driver in self.browsers:
            try:
                driver.quit()
                logger.info(f"Browser {browser_id} closed")
            except:
                pass
        
        # Final statistics
        session_runtime = time.time() - self.session_start_time
        total_checks = self.stats['total_checks']
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}📊 SESSION SUMMARY{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"Runtime: {self._format_duration(session_runtime)}")
        print(f"Total Checks: {total_checks:,}")
        print(f"Average Rate: {(total_checks / session_runtime * 60):.1f} checks/min")
        print(f"Unique Tickets Found: {self.stats['unique_tickets_found']}")
        print(f"Purchases: {self.stats['purchases']}")
        print(f"Blocks Encountered: {self.stats['blocks_encountered']}")
        
        # Save final stats
        self.save_stats()
        
        print(f"\n{Colors.GREEN}✅ Session complete!{Colors.END}")


def print_banner():
    """Print stylish banner"""
    os.system('clear' if os.name != 'nt' else 'cls')
    
    print(f"{Colors.CYAN}")
    print(r"""
    ███████╗ █████╗ ███╗   ██╗███████╗ █████╗ ██╗     ███████╗
    ██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗██║     ██╔════╝
    █████╗  ███████║██╔██╗ ██║███████╗███████║██║     █████╗  
    ██╔══╝  ██╔══██║██║╚██╗██║╚════██║██╔══██║██║     ██╔══╝  
    ██║     ██║  ██║██║ ╚████║███████║██║  ██║███████╗███████╗
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
    """)
    print(f"{Colors.END}")
    print(f"{Colors.BOLD}             🎫 TICKET HUNTER v2.0 - FIXED 🎫{Colors.END}")
    print(f"{Colors.CYAN}           Fast • Reliable • No False Blocks{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")


def main():
    """Main entry point"""
    try:
        bot = FanSaleBot()
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n{Colors.CYAN}Thank you for using FanSale Bot!{Colors.END}")


if __name__ == "__main__":
    main()
