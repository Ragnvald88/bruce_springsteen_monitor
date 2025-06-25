#!/usr/bin/env python3
"""
FanSale Ticket Hunter Bot - Fixed Version
Fixes false block detection and ensures fast ticket purchasing
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
