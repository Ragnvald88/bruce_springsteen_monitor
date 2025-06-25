"""
🚀 FanSale Enhanced Bot - No Login Edition
Enhanced multi-monitor support, options menu, and proxy capabilities
"""

import os
import sys
import json
import time
import random
import hashlib
import logging
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from functools import wraps
import shutil

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============= CONFIGURATION =============
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "bot_config.json"
STATS_FILE = BASE_DIR / "fansale_stats.json"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
PROFILES_DIR = BASE_DIR / "browser_profiles"

# Create directories
SCREENSHOTS_DIR.mkdir(exist_ok=True)
PROFILES_DIR.mkdir(exist_ok=True)

# ============= ENHANCED CONFIGURATION =============
@dataclass
class EnhancedBotConfig:
    """Enhanced bot configuration with all features"""
    # Browser Settings
    browsers_count: int = 2
    use_proxy: bool = False
    clear_profiles_on_start: bool = False
    
    # Ticket Settings
    max_tickets: int = 2
    ticket_filters: List[str] = None
    filter_mode: str = "any"  # "any" or "all"
    
    # Timing Settings
    refresh_interval: int = 30
    session_timeout: int = 900
    min_wait: float = 2.0
    max_wait: float = 4.0
    
    # Retry Settings
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Monitor Settings
    monitor_width: int = 1920
    monitor_height: int = 1080
    browsers_per_row: int = 2
    
    # Target URL
    target_url: str = ""
    
    def __post_init__(self):
        if self.ticket_filters is None:
            self.ticket_filters = []
        if not self.target_url:
            self.target_url = os.getenv('FANSALE_TARGET_URL', 
                "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
    
    @classmethod
    def from_file(cls, path: Path) -> 'EnhancedBotConfig':
        """Load config from JSON file if exists"""
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save(self, path: Path):
        """Save config to JSON file"""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)


# ============= UTILITIES =============
def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator for flaky operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


class StatsManager:
    """Manage persistent statistics with thread safety"""
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.lock = threading.Lock()
        self.stats = self.load()
    
    def load(self) -> dict:
        """Load stats from file"""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            'total_checks': 0,
            'total_tickets_found': 0,
            'unique_tickets_found': 0,
            'tickets_by_type': {
                'prato_a': 0,
                'prato_b': 0,
                'settore': 0,
                'other': 0
            },
            'purchases': 0,
            'blocks_encountered': 0,
            'all_time_runtime': 0.0,
            'sessions': []
        }
    
    def save(self):
        """Save stats to file"""
        with self.lock:
            with open(self.filepath, 'w') as f:
                json.dump(self.stats, f, indent=2)
    
    def update(self, key: str, value: any):
        """Thread-safe update"""
        with self.lock:
            if isinstance(value, dict) and key in self.stats and isinstance(self.stats[key], dict):
                self.stats[key].update(value)
            else:
                self.stats[key] = value


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class NotificationManager:
    """Handle notifications and alerts"""
    @staticmethod
    def play_alarm():
        """Play system alert sound"""
        if sys.platform == "darwin":  # macOS
            os.system("afplay /System/Library/Sounds/Glass.aiff")
        elif sys.platform == "win32":  # Windows
            import winsound
            winsound.Beep(1000, 500)
        else:  # Linux
            os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || echo -e '\\a'")
    
    @staticmethod
    def desktop_notification(title: str, message: str):
        """Send desktop notification"""
        try:
            if sys.platform == "darwin":
                os.system(f'''osascript -e 'display notification "{message}" with title "{title}"' ''')
            elif sys.platform == "win32":
                # Windows notifications require additional setup
                pass
            else:  # Linux
                os.system(f'notify-send "{title}" "{message}"')
        except Exception:
            pass


class ProxyManager:
    """Manage proxy configuration"""
    def __init__(self):
        self.enabled = False
        self.config = None
        self.load_from_env()
    
    def load_from_env(self):
        """Load proxy settings from environment"""
        username = os.getenv('IPROYAL_USERNAME')
        password = os.getenv('IPROYAL_PASSWORD')
        hostname = os.getenv('IPROYAL_HOSTNAME')
        port = os.getenv('IPROYAL_PORT')
        
        if all([username, password, hostname, port]):
            self.config = {
                'proxy': {
                    'http': f'http://{username}:{password}@{hostname}:{port}',
                    'https': f'https://{username}:{password}@{hostname}:{port}',
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
    
    def get_proxy_string(self) -> Optional[str]:
        """Get proxy string for Chrome"""
        if self.enabled and self.config:
            proxy = self.config['proxy']['http']
            # Extract host:port from the proxy URL
            if '@' in proxy:
                return proxy.split('@')[1]
        return None
    
    def get_auth(self) -> Optional[Tuple[str, str]]:
        """Get proxy authentication"""
        if self.enabled and self.config:
            proxy = self.config['proxy']['http']
            if '@' in proxy:
                auth_part = proxy.split('//')[1].split('@')[0]
                username, password = auth_part.split(':')
                return username, password
        return None


# ============= LOGGING SETUP =============
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA
    }
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Colors.END}"
        return super().format(record)


# Configure logging
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(file_handler)


# ============= MAIN BOT CLASS =============
class FanSaleEnhancedBot:
    """Enhanced FanSale Bot with all requested features"""
    
    def __init__(self):
        # Load configuration
        self.config = EnhancedBotConfig.from_file(CONFIG_FILE)
        
        # Browser management
        self.browsers = []
        self.browser_threads = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Tracking
        self.seen_tickets: Set[str] = set()
        self.ticket_details_cache: Dict[str, dict] = {}
        
        # Managers
        self.stats_manager = StatsManager(STATS_FILE)
        self.stats = self.stats_manager.stats
        self.proxy_manager = ProxyManager()
        self.notification_manager = NotificationManager()
        
        # Session tracking
        self.session_start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def save_stats(self):
        """Save statistics"""
        self.stats_manager.save()
    
    def categorize_ticket(self, text: str) -> str:
        """Categorize ticket based on text content"""
        text_lower = text.lower()
        
        # Check for specific categories
        if 'prato' in text_lower:
            if 'prato a' in text_lower:
                return 'prato_a'
            elif 'prato b' in text_lower:
                return 'prato_b'
            else:
                # Default prato to prato_b if not specified
                return 'prato_b'
        elif any(term in text_lower for term in ['settore', 'tribuna', 'anello']):
            return 'settore'
        else:
            return 'other'
    
    def clear_browser_profiles(self):
        """Clear all browser profile data"""
        if PROFILES_DIR.exists():
            try:
                shutil.rmtree(PROFILES_DIR)
                PROFILES_DIR.mkdir(exist_ok=True)
                logger.info("✅ Browser profiles cleared")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to clear profiles: {e}")
                return False
        return True
    
    def calculate_browser_position(self, browser_id: int) -> Tuple[int, int]:
        """Calculate optimal browser window position for multi-monitor setup"""
        browsers_per_row = self.config.browsers_per_row
        browser_width = self.config.monitor_width // browsers_per_row
        browser_height = self.config.monitor_height
        
        # Calculate position
        row = (browser_id - 1) // browsers_per_row
        col = (browser_id - 1) % browsers_per_row
        
        x = col * browser_width
        y = row * 50  # Small vertical offset for each row
        
        return x, y, browser_width, browser_height
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create browser with enhanced multi-monitor support"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        options = uc.ChromeOptions()
        
        # Enhanced stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance optimizations
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-blink-features')
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 1,
        }
        options.add_experimental_option('prefs', prefs)
        
        # User agent
        options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
        
        # Profile directory
        profile_dir = PROFILES_DIR / f"profile_{browser_id}"
        profile_dir.mkdir(exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir}')
        
        # Proxy configuration
        if self.config.use_proxy and self.proxy_manager.enabled:
            proxy_string = self.proxy_manager.get_proxy_string()
            if proxy_string:
                options.add_argument(f'--proxy-server={proxy_string}')
                logger.info(f"🔐 Using proxy: {proxy_string}")
        
        # Calculate window position
        x, y, width, height = self.calculate_browser_position(browser_id)
        
        # Try multiple Chrome versions
        for version in [None, 137, 136, 138]:
            try:
                logger.info(f"🔄 Attempting with Chrome {version or 'auto-detected'}...")
                
                driver = uc.Chrome(
                    options=options,
                    version_main=version,
                    driver_executable_path=None
                )
                
                # Position and size window
                driver.set_window_position(x, y)
                driver.set_window_size(width, height)
                
                # Handle proxy authentication if needed
                if self.config.use_proxy and self.proxy_manager.enabled:
                    auth = self.proxy_manager.get_auth()
                    if auth:
                        # Note: Chrome doesn't support proxy auth directly
                        # Would need extension or other method for auth
                        pass
                
                logger.info(f"✅ Browser {browser_id} ready at position ({x}, {y}) - Monitor {(col // self.config.browsers_per_row) + 1}")
                return driver
                
            except Exception as e:
                logger.warning(f"Failed with version {version}: {str(e)[:100]}")
                if version == 138:  # Last attempt
                    logger.error(f"❌ All Chrome versions failed for Browser {browser_id}")
                    return None
        
        return None
    
    def is_blocked(self, driver: uc.Chrome) -> bool:
        """Check if we're blocked (404 page)"""
        try:
            if "404" in driver.title:
                return True
            error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '404')]")
            return len(error_elements) > 0
        except Exception:
            return False
    
    def clear_browser_data(self, driver: uc.Chrome, browser_id: int):
        """Clear browser data to bypass blocks"""
        try:
            logger.info(f"🧹 Clearing data for Browser {browser_id}...")
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            logger.info(f"✅ Browser {browser_id} data cleared")
        except Exception as e:
            logger.error(f"Error clearing browser data: {e}")
    
    def matches_filters(self, ticket_text: str) -> bool:
        """Check if ticket matches configured filters"""
        if not self.config.ticket_filters:
            return True
        
        text_lower = ticket_text.lower()
        
        if self.config.filter_mode == "any":
            return any(filter_word.lower() in text_lower for filter_word in self.config.ticket_filters)
        else:  # "all"
            return all(filter_word.lower() in text_lower for filter_word in self.config.ticket_filters)
    
    def extract_ticket_info(self, driver: uc.Chrome, ticket_element) -> dict:
        """Extract detailed ticket information"""
        try:
            raw_text = ticket_element.text
            
            # Extract price
            price_element = ticket_element.find_element(By.CSS_SELECTOR, "div[data-qa='offer-price'] span")
            price = price_element.text if price_element else "Unknown"
            
            # Extract details
            info_parts = raw_text.split('\n')
            
            return {
                'raw_text': raw_text,
                'price': price,
                'category': self.categorize_ticket(raw_text),
                'timestamp': datetime.now().isoformat(),
                'info_parts': info_parts,
                'matches_filter': self.matches_filters(raw_text)
            }
        except Exception as e:
            logger.debug(f"Error extracting ticket info: {e}")
            return {
                'raw_text': ticket_element.text,
                'category': 'other',
                'matches_filter': False
            }
    
    def generate_ticket_hash(self, text: str) -> str:
        """Generate unique hash for ticket"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def log_new_ticket(self, ticket_info: dict, browser_id: int):
        """Log new ticket discovery"""
        category = ticket_info['category']
        category_colors = {
            'prato_a': Colors.RED + Colors.BOLD,
            'prato_b': Colors.YELLOW + Colors.BOLD,
            'settore': Colors.CYAN + Colors.BOLD,
            'other': Colors.WHITE
        }
        
        color = category_colors.get(category, Colors.WHITE)
        logger.info(f"{color}🎫 NEW TICKET - {category.upper()} - Browser {browser_id}{Colors.END}")
        
        # Log details
        for line in ticket_info['info_parts'][:3]:  # First 3 lines
            if line.strip():
                logger.info(f"   └─ {line}")
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to target
        driver.get(self.config.target_url)
        time.sleep(random.uniform(2.5, 3.5))
        
        check_count = 0
        last_refresh = time.time()
        last_session_refresh = time.time()
        local_stats = defaultdict(int)
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.config.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Check for blocks
                if self.is_blocked(driver):
                    logger.warning(f"⚠️ Hunter {browser_id}: Block detected!")
                    self.stats['blocks_encountered'] += 1
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.config.target_url)
                    time.sleep(random.uniform(2.5, 3.5))
                    continue
                
                # Session refresh
                if time.time() - last_session_refresh > self.config.session_timeout:
                    logger.info(f"🔄 Hunter {browser_id}: Session refresh...")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.config.target_url)
                    time.sleep(3)
                    last_session_refresh = time.time()
                    continue
                
                # Look for tickets
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    self.stats['total_tickets_found'] += len(tickets)
                    
                    for ticket in tickets:
                        try:
                            # Extract info
                            ticket_info = self.extract_ticket_info(driver, ticket)
                            ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                            
                            # Check if new
                            if ticket_hash not in self.seen_tickets:
                                self.seen_tickets.add(ticket_hash)
                                self.ticket_details_cache[ticket_hash] = ticket_info
                                
                                # Update stats
                                self.stats['unique_tickets_found'] += 1
                                category = ticket_info['category']
                                self.stats['tickets_by_type'][category] += 1
                                local_stats[category] += 1
                                
                                # Log discovery
                                self.log_new_ticket(ticket_info, browser_id)
                                
                                # Notify if matches filter
                                if ticket_info['matches_filter']:
                                    self.notification_manager.play_alarm()
                                    self.notification_manager.desktop_notification(
                                        "Ticket Found!",
                                        f"{category.upper()} ticket available!"
                                    )
                                
                                # Save stats
                                self.save_stats()
                                
                                # Attempt purchase if desired
                                if ticket_info['matches_filter']:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.config.max_tickets:
                                            if self.purchase_ticket(driver, ticket, browser_id):
                                                self.tickets_secured += 1
                                                self.stats['purchases'] += 1
                                                self.save_stats()
                                                
                                                if self.tickets_secured >= self.config.max_tickets:
                                                    logger.info("🎉 Max tickets secured!")
                                                    return
                        
                        except Exception as e:
                            logger.debug(f"Error processing ticket: {e}")
                            continue
                
                # Refresh strategy
                refresh_time = random.uniform(self.config.min_wait, self.config.max_wait)
                
                if time.time() - last_refresh > self.config.refresh_interval:
                    driver.refresh()
                    last_refresh = time.time()
                else:
                    time.sleep(refresh_time)
                
                # Progress update
                if check_count % 50 == 0:
                    elapsed = time.time() - self.session_start_time
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    
                    # Local summary
                    summary_parts = []
                    for cat in ['prato_a', 'prato_b', 'settore', 'other']:
                        if local_stats[cat] > 0:
                            summary_parts.append(f"{cat.replace('_', ' ').title()}: {local_stats[cat]}")
                    
                    summary = " | ".join(summary_parts) if summary_parts else "No tickets found"
                    logger.info(f"📊 Hunter {browser_id}: {check_count} checks @ {rate:.1f}/min | {summary}")
            
            except TimeoutException:
                logger.warning(f"Hunter {browser_id}: Timeout, refreshing...")
                driver.refresh()
                time.sleep(random.uniform(1.5, 2.5))
            
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    logger.error(f"Hunter {browser_id}: Session died")
                    break
                logger.error(f"Hunter {browser_id}: Browser error")
                time.sleep(5)
            
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                time.sleep(5)
    
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase/reserve ticket"""
        try:
            logger.info(f"💳 Browser {browser_id}: Attempting purchase...")
            
            # Click the ticket
            driver.execute_script("arguments[0].click();", ticket_element)
            time.sleep(1)
            
            # Look for checkout button
            checkout_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='add-to-cart']"))
            )
            
            if checkout_btn:
                driver.execute_script("arguments[0].click();", checkout_btn)
                logger.info(f"✅ Browser {browser_id}: Ticket reserved!")
                
                # Take screenshot
                screenshot_path = SCREENSHOTS_DIR / f"purchase_{self.session_id}_{browser_id}.png"
                driver.save_screenshot(str(screenshot_path))
                
                return True
        
        except Exception as e:
            logger.debug(f"Purchase failed: {e}")
        
        return False
    
    def show_statistics_dashboard(self):
        """Display statistics dashboard"""
        runtime = time.time() - self.session_start_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}📊 SESSION STATISTICS{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        
        print(f"⏱️  Runtime: {hours}h {minutes}m")
        print(f"🔍 Total Checks: {self.stats['total_checks']:,}")
        print(f"🎫 Unique Tickets Found: {self.stats['unique_tickets_found']}")
        print(f"💳 Purchases: {self.stats['purchases']}")
        print(f"🚫 Blocks Encountered: {self.stats['blocks_encountered']}")
        
        print(f"\n{Colors.BOLD}Ticket Breakdown:{Colors.END}")
        for cat, count in self.stats['tickets_by_type'].items():
            if count > 0:
                print(f"  • {cat.replace('_', ' ').title()}: {count}")
        
        if self.stats['total_checks'] > 0:
            rate = (self.stats['total_checks'] * 60) / runtime if runtime > 0 else 0
            print(f"\n⚡ Check Rate: {rate:.1f} checks/minute")
        
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    def configure_menu(self):
        """Enhanced configuration menu"""
        while True:
            print(f"\n{Colors.BOLD}{Colors.CYAN}⚙️  CONFIGURATION MENU{Colors.END}")
            print(f"{Colors.CYAN}{'='*50}{Colors.END}")
            print("1. Browser Settings")
            print("2. Ticket Filters")
            print("3. Proxy Settings")
            print("4. Monitor Setup")
            print("5. Advanced Settings")
            print("6. Save & Return")
            print("7. Cancel")
            
            choice = input(f"\n{Colors.BOLD}Select option:{Colors.END} ").strip()
            
            if choice == '1':
                self.configure_browsers()
            elif choice == '2':
                self.configure_filters()
            elif choice == '3':
                self.configure_proxy()
            elif choice == '4':
                self.configure_monitors()
            elif choice == '5':
                self.configure_advanced()
            elif choice == '6':
                self.config.save(CONFIG_FILE)
                print(f"{Colors.GREEN}✅ Configuration saved!{Colors.END}")
                break
            elif choice == '7':
                print(f"{Colors.YELLOW}❌ Configuration cancelled{Colors.END}")
                break
    
    def configure_browsers(self):
        """Configure browser settings"""
        print(f"\n{Colors.BOLD}🌐 BROWSER SETTINGS{Colors.END}")
        
        # Number of browsers
        while True:
            try:
                num = input(f"Number of browsers (1-8, current: {self.config.browsers_count}): ").strip()
                if not num:
                    break
                num = int(num)
                if 1 <= num <= 8:
                    self.config.browsers_count = num
                    break
                print(f"{Colors.RED}Please enter 1-8{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}Invalid number{Colors.END}")
        
        # Clear profiles
        clear = input(f"Clear browser profiles on start? (y/n, current: {'Yes' if self.config.clear_profiles_on_start else 'No'}): ").strip().lower()
        if clear in ['y', 'n']:
            self.config.clear_profiles_on_start = (clear == 'y')
    
    def configure_filters(self):
        """Configure ticket filters"""
        print(f"\n{Colors.BOLD}🎫 TICKET FILTERS{Colors.END}")
        
        # Max tickets
        while True:
            try:
                max_t = input(f"Max tickets to purchase (1-4, current: {self.config.max_tickets}): ").strip()
                if not max_t:
                    break
                max_t = int(max_t)
                if 1 <= max_t <= 4:
                    self.config.max_tickets = max_t
                    break
                print(f"{Colors.RED}Please enter 1-4{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}Invalid number{Colors.END}")
        
        # Filter keywords
        print(f"\nCurrent filters: {', '.join(self.config.ticket_filters) if self.config.ticket_filters else 'None'}")
        print("Enter filter keywords (comma-separated) or press Enter to keep current:")
        filters = input("Filters: ").strip()
        if filters:
            self.config.ticket_filters = [f.strip() for f in filters.split(',') if f.strip()]
        
        # Filter mode
        if self.config.ticket_filters:
            mode = input(f"Filter mode - any/all (current: {self.config.filter_mode}): ").strip().lower()
            if mode in ['any', 'all']:
                self.config.filter_mode = mode
    
    def configure_proxy(self):
        """Configure proxy settings"""
        print(f"\n{Colors.BOLD}🔐 PROXY SETTINGS{Colors.END}")
        
        if self.proxy_manager.config:
            print(f"{Colors.GREEN}✅ Proxy credentials loaded from .env{Colors.END}")
            use = input(f"Use proxy? (y/n, current: {'Yes' if self.config.use_proxy else 'No'}): ").strip().lower()
            if use in ['y', 'n']:
                self.config.use_proxy = (use == 'y')
                self.proxy_manager.enabled = self.config.use_proxy
        else:
            print(f"{Colors.YELLOW}⚠️  No proxy credentials found in .env{Colors.END}")
            print("Add IPROYAL_* variables to .env file to enable proxy")
    
    def configure_monitors(self):
        """Configure monitor setup"""
        print(f"\n{Colors.BOLD}🖥️  MONITOR SETUP{Colors.END}")
        
        # Browsers per row
        while True:
            try:
                bpr = input(f"Browsers per row (1-4, current: {self.config.browsers_per_row}): ").strip()
                if not bpr:
                    break
                bpr = int(bpr)
                if 1 <= bpr <= 4:
                    self.config.browsers_per_row = bpr
                    break
                print(f"{Colors.RED}Please enter 1-4{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}Invalid number{Colors.END}")
        
        # Monitor dimensions
        print(f"\nCurrent monitor size: {self.config.monitor_width}x{self.config.monitor_height}")
        print("Press Enter to keep current or enter new dimensions:")
        
        width = input("Monitor width: ").strip()
        if width and width.isdigit():
            self.config.monitor_width = int(width)
        
        height = input("Monitor height: ").strip()
        if height and height.isdigit():
            self.config.monitor_height = int(height)
    
    def configure_advanced(self):
        """Configure advanced settings"""
        print(f"\n{Colors.BOLD}⚡ ADVANCED SETTINGS{Colors.END}")
        
        # Refresh interval
        while True:
            try:
                ref = input(f"Page refresh interval in seconds (10-120, current: {self.config.refresh_interval}): ").strip()
                if not ref:
                    break
                ref = int(ref)
                if 10 <= ref <= 120:
                    self.config.refresh_interval = ref
                    break
                print(f"{Colors.RED}Please enter 10-120{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}Invalid number{Colors.END}")
        
        # Session timeout
        while True:
            try:
                timeout = input(f"Session refresh timeout in seconds (300-1800, current: {self.config.session_timeout}): ").strip()
                if not timeout:
                    break
                timeout = int(timeout)
                if 300 <= timeout <= 1800:
                    self.config.session_timeout = timeout
                    break
                print(f"{Colors.RED}Please enter 300-1800{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}Invalid number{Colors.END}")
    
    def show_main_menu(self):
        """Show main menu"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 FANSALE ENHANCED BOT{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}")
        print("1. Start Hunting")
        print("2. Configure Settings")
        print("3. View Statistics")
        print("4. Clear Browser Profiles")
        print("5. Exit")
        
        return input(f"\n{Colors.BOLD}Select option:{Colors.END} ").strip()
    
    def run(self):
        """Main execution loop"""
        try:
            while True:
                choice = self.show_main_menu()
                
                if choice == '1':
                    # Start hunting
                    self.start_hunting()
                    break
                elif choice == '2':
                    # Configure
                    self.configure_menu()
                elif choice == '3':
                    # Statistics
                    self.show_statistics_dashboard()
                    input("\nPress Enter to continue...")
                elif choice == '4':
                    # Clear profiles
                    if self.clear_browser_profiles():
                        print(f"{Colors.GREEN}✅ Browser profiles cleared!{Colors.END}")
                    input("\nPress Enter to continue...")
                elif choice == '5':
                    # Exit
                    print(f"{Colors.YELLOW}👋 Goodbye!{Colors.END}")
                    return
                else:
                    print(f"{Colors.RED}Invalid option{Colors.END}")
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.END}")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.cleanup()
    
    def start_hunting(self):
        """Start the hunting process"""
        try:
            # Clear profiles if configured
            if self.config.clear_profiles_on_start:
                self.clear_browser_profiles()
            
            # Create browsers
            print(f"\n{Colors.BOLD}🚀 Starting {self.config.browsers_count} browser(s)...{Colors.END}")
            
            for i in range(1, self.config.browsers_count + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created")
                return
            
            logger.info(f"✅ {len(self.browsers)} browser(s) ready!")
            
            # Show tips
            print(f"\n{Colors.CYAN}💡 TIPS:{Colors.END}")
            print(f"{Colors.CYAN}• Browsers are positioned for multi-monitor setups{Colors.END}")
            print(f"{Colors.CYAN}• Move them to your preferred monitors if needed{Colors.END}")
            print(f"{Colors.CYAN}• Press Ctrl+C to stop hunting{Colors.END}")
            
            input(f"\n{Colors.BOLD}✋ Press Enter to START HUNTING...{Colors.END}")
            
            # Start hunting threads
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_tickets,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                self.browser_threads.append(thread)
            
            # Monitor progress
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎯 HUNTING ACTIVE!{Colors.END}\n")
            
            last_update = time.time()
            while self.tickets_secured < self.config.max_tickets:
                time.sleep(1)
                
                # Periodic updates
                if time.time() - last_update > 60:
                    self.show_statistics_dashboard()
                    last_update = time.time()
            
            logger.info(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SUCCESS! {self.tickets_secured} tickets secured!{Colors.END}")
        
        except KeyboardInterrupt:
            logger.info(f"\n{Colors.YELLOW}🛑 Stopping...{Colors.END}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.shutdown_event.set()
        
        # Update runtime
        runtime = time.time() - self.session_start_time
        self.stats['all_time_runtime'] += runtime
        
        # Save session info
        session_info = {
            'id': self.session_id,
            'start': datetime.fromtimestamp(self.session_start_time).isoformat(),
            'duration': runtime,
            'checks': self.stats['total_checks'],
            'tickets_found': self.stats['unique_tickets_found'],
            'purchases': self.stats['purchases']
        }
        
        if 'sessions' not in self.stats:
            self.stats['sessions'] = []
        self.stats['sessions'].append(session_info)
        
        # Keep only last 10 sessions
        self.stats['sessions'] = self.stats['sessions'][-10:]
        
        # Save final stats
        self.save_stats()
        
        # Close browsers
        for driver in self.browsers:
            try:
                driver.quit()
            except Exception as e:
                logger.debug(f"Error closing browser: {e}")
        
        # Show final statistics
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 FINAL SESSION STATISTICS{Colors.END}")
        self.show_statistics_dashboard()


# ============= MAIN ENTRY POINT =============
def main():
    """Main entry point"""
    bot = FanSaleEnhancedBot()
    bot.run()


if __name__ == "__main__":
    main()
