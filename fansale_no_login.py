#!/usr/bin/env python3
"""
FanSale Bot - Enhanced No Login Edition
Features:
- No login required
- Ticket type categorization (Prato A, Prato B, Settore)
- Duplicate detection to avoid re-logging same tickets
- Persistent statistics across restarts
- Beautiful terminal logging with ticket details
"""

import os
import sys
import time
import random
import logging
import threading
import json
import hashlib
import re
import functools
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import contextmanager

# Suppress verbose logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

from dotenv import load_dotenv
load_dotenv()

# Configuration dataclass
@dataclass
class BotConfig:
    """Bot configuration with defaults"""
    browsers_count: int = 2
    max_tickets: int = 2
    refresh_interval: int = 30
    session_timeout: int = 900
    min_wait: float = 2.0
    max_wait: float = 4.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    @classmethod
    def from_file(cls, path: Path) -> 'BotConfig':
        """Load config from JSON file if exists"""
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                # Filter out any extra fields that don't exist in the dataclass
                valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
                filtered_data = {k: v for k, v in data.items() if k in valid_fields}
                return cls(**filtered_data)
        return cls()
    
    def save(self, path: Path):
        """Save config to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

# Advanced retry decorator
def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)):
    """Sophisticated retry decorator with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logging.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logging.warning(f"{func.__name__} attempt {attempt} failed: {e}, "
                                  f"retrying in {current_delay:.1f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            return None
        return wrapper
    return decorator

# Thread-safe statistics manager
class StatsManager:
    """Thread-safe statistics manager with atomic operations"""
    def __init__(self, stats_file: Path):
        self.stats_file = stats_file
        self.lock = threading.Lock()
        self.stats = self.load()
    
    def load(self) -> Dict:
        """Load stats from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Could not load stats: {e}")
        
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
            'all_time_runtime': 0
        }
    
    def save(self):
        """Save stats to file with atomic write"""
        with self.lock:
            # Write to temp file first
            temp_file = self.stats_file.with_suffix('.tmp')
            try:
                with open(temp_file, 'w') as f:
                    json.dump(self.stats, f, indent=2)
                # Atomic rename
                temp_file.replace(self.stats_file)
            except Exception as e:
                logging.error(f"Failed to save stats: {e}")
                if temp_file.exists():
                    temp_file.unlink()
    
    def increment(self, key: str, value: int = 1):
        """Thread-safe increment"""
        with self.lock:
            if key in self.stats:
                self.stats[key] += value
            else:
                # Handle nested keys like 'tickets_by_type.prato_a'
                keys = key.split('.')
                current = self.stats
                for k in keys[:-1]:
                    current = current.setdefault(k, {})
                current[keys[-1]] = current.get(keys[-1], 0) + value

# ANSI color codes for beautiful terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Notification Manager
class NotificationManager:
    """Manages notifications for ticket discoveries"""
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.notification_queue = deque(maxlen=100)
    
    def notify(self, title: str, message: str, priority: str = "normal"):
        """Send notification (can be extended for email/SMS)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        notification = {
            'timestamp': timestamp,
            'title': title,
            'message': message,
            'priority': priority
        }
        self.notification_queue.append(notification)
        
        if self.enabled:
            # For now, just enhanced logging
            if priority == "high":
                logger.info(f"\n{'🚨' * 5} ALERT {'🚨' * 5}")
                logger.info(f"{Colors.BOLD}{Colors.RED}{title}{Colors.END}")
                logger.info(f"{Colors.YELLOW}{message}{Colors.END}")
                logger.info(f"{'🚨' * 5} ALERT {'🚨' * 5}\n")
            else:
                logger.info(f"📢 {title}: {message}")

# Health Monitor
class HealthMonitor:
    """Monitors browser and system health"""
    def __init__(self):
        self.metrics = defaultdict(dict)
        self.last_check = time.time()
        
    def check_browser_health(self, browser_id: int, driver: uc.Chrome) -> bool:
        """Check if browser is healthy"""
        try:
            # Check if browser is responsive
            driver.execute_script("return document.readyState")
            
            # Update metrics
            self.metrics[browser_id] = {
                'last_check': time.time(),
                'status': 'healthy',
                'checks_performed': self.metrics[browser_id].get('checks_performed', 0) + 1
            }
            return True
            
        except Exception as e:
            self.metrics[browser_id] = {
                'last_check': time.time(),
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    def get_system_health(self) -> Dict:
        """Get system resource usage"""
        try:
            # Basic system metrics
            return {
                'memory_percent': self._get_memory_usage(),
                'active_threads': threading.active_count(),
                'uptime_seconds': time.time() - self.metrics.get('start_time', time.time())
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_memory_usage(self) -> float:
        """Get current process memory usage percentage"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return round(usage.ru_maxrss / 1024 / 1024, 2)  # MB
        except:
            return 0.0

# Configure logging with custom formatter
class ColoredFormatter(logging.Formatter):
    def format(self, record):
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
console_handler.setFormatter(ColoredFormatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(file_handler)

class FanSaleBot:
    """Enhanced FanSale bot with ticket type tracking - No login required"""
    
    def __init__(self, config: Optional[BotConfig] = None):
        # Load configuration
        self.config = config or BotConfig()
        
        # Get target URL from env or use default
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554")
        
        # Configuration
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_filters = []  # Will be set to track specific types
        self.ticket_types_to_hunt = {'prato_a', 'prato_b'}  # Default to Prato types
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Ticket tracking - to avoid duplicate logging
        self.seen_tickets = set()  # Store hashes of seen tickets
        self.ticket_details_cache = {}  # Store full details of tickets
        
        # Load persistent statistics using thread-safe manager
        self.stats_file = Path("fansale_stats.json")
        self.stats_manager = StatsManager(self.stats_file)
        self.stats = self.stats_manager.stats
        
        # Performance monitoring
        self.session_start_time = time.time()
        
        # Health monitoring and notifications
        self.health_monitor = HealthMonitor()
        self.notification_manager = NotificationManager(enabled=True)


    def save_stats(self):
        """Save statistics to file with session tracking"""
        try:
            # Update runtime
            session_time = time.time() - self.session_start_time
            
            # Add session info if not already tracked
            if 'sessions' not in self.stats:
                self.stats['sessions'] = []
            
            # Create session summary
            session_info = {
                'date': datetime.now().isoformat(),
                'duration': session_time,
                'checks': self.stats['total_checks'],
                'tickets_found': self.stats['unique_tickets_found'],
                'purchases': self.stats['purchases'],
                'tickets_by_type': dict(self.stats['tickets_by_type'])
            }
            
            # Update or add session
            session_exists = False
            for i, session in enumerate(self.stats['sessions']):
                if session.get('date', '').startswith(datetime.now().strftime('%Y-%m-%d')):
                    self.stats['sessions'][i] = session_info
                    session_exists = True
                    break
            
            if not session_exists:
                self.stats['sessions'].append(session_info)
            
            # Keep only last 30 days of sessions
            self.stats['sessions'] = self.stats['sessions'][-30:]
            
            # Save to file
            self.stats_manager.save()
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def categorize_ticket(self, ticket_text: str) -> str:
        """Categorize ticket based on text content"""
        ticket_lower = ticket_text.lower()
        
        # Check for Prato A
        if 'prato a' in ticket_lower or 'prato gold a' in ticket_lower:
            return 'prato_a'
        # Check for Prato B
        elif 'prato b' in ticket_lower or 'prato gold b' in ticket_lower:
            return 'prato_b'
        # Check for Settore/Seated tickets - improved detection
        elif any(keyword in ticket_lower for keyword in [
            'settore', 'fila', 'posto', 'anello', 'tribuna', 
            'poltrona', 'numerato', 'seat', 'row', 'ring',
            'rosso', 'blu', 'verde', 'giallo', 'ingresso'
        ]):
            return 'settore'
        else:
            return 'other'
    
    def generate_ticket_hash(self, ticket_text: str) -> str:
        """Generate unique hash for ticket to detect duplicates"""
        # Extract key identifying information
        # Remove dynamic elements like timestamps
        clean_text = re.sub(r'\d{1,2}:\d{2}:\d{2}', '', ticket_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return hashlib.md5(clean_text.encode()).hexdigest()
    
    def extract_full_ticket_info(self, driver: uc.Chrome, ticket_element: WebElement) -> Dict:
        """Extract complete ticket information including seat details"""
        try:
            ticket_info = {
                'raw_text': '',
                'section': '',
                'row': '',
                'seat': '',
                'price': '',
                'category': 'other',
                'entrance': '',
                'ring': ''
            }
            
            # Get all text from the ticket element
            full_text = ticket_element.text
            ticket_info['raw_text'] = full_text
            
            # Try to extract structured data
            lines = full_text.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                
                # Extract section info (Prato, Settore, Tribuna, etc.)
                if any(x in line_lower for x in ['prato', 'settore', 'tribuna', 'parterre']):
                    ticket_info['section'] = line.strip()
                
                # Extract row/fila
                fila_match = re.search(r'fila\s*[:\s]*(\w+)', line, re.I)
                if fila_match:
                    ticket_info['row'] = fila_match.group(1)
                
                # Extract seat/posto
                posto_match = re.search(r'posto\s*[:\s]*(\d+)', line, re.I)
                if posto_match:
                    ticket_info['seat'] = posto_match.group(1)
                
                # Extract entrance/ingresso
                ingresso_match = re.search(r'ingresso\s*[:\s]*(\d+)', line, re.I)
                if ingresso_match:
                    ticket_info['entrance'] = ingresso_match.group(1)
                
                # Extract ring/anello (like "2 Anello Rosso")
                anello_match = re.search(r'(\d+\s*anello\s*\w+)', line, re.I)
                if anello_match:
                    ticket_info['ring'] = anello_match.group(1)
                
                # Extract price
                price_match = re.search(r'(\d+[,.]?\d*)\s*€', line)
                if price_match:
                    ticket_info['price'] = price_match.group(0)
            
            # Categorize the ticket
            ticket_info['category'] = self.categorize_ticket(full_text)
            
            return ticket_info
            
        except Exception as e:
            logger.debug(f"Error extracting ticket info: {e}")
            return {
                'raw_text': ticket_element.text,
                'section': '',
                'row': '',
                'seat': '',
                'price': '',
                'category': 'other',
                'entrance': '',
                'ring': ''
            }
    
    def log_new_ticket(self, ticket_info: Dict, browser_id: int):
        """Log newly discovered ticket with enhanced visual formatting"""
        category = ticket_info['category']
        
        # Check if we're hunting this type
        is_hunting = category in self.ticket_types_to_hunt
        
        # Build detailed ticket description
        details = []
        if ticket_info['section']:
            details.append(f"Section: {ticket_info['section']}")
        if ticket_info['entrance']:
            details.append(f"Entrance: {ticket_info['entrance']}")
        if ticket_info['row']:
            details.append(f"Row: {ticket_info['row']}")
        if ticket_info['seat']:
            details.append(f"Seat: {ticket_info['seat']}")
        if ticket_info['ring']:
            details.append(f"Ring: {ticket_info['ring']}")
        if ticket_info['price']:
            details.append(f"💰 {ticket_info['price']}")
        
        detail_str = " | ".join(details) if details else ticket_info['raw_text'][:100]
        
        # Send notification if hunting this type
        if is_hunting:
            self.notification_manager.notify(
                f"🎫 NEW {category.upper()} TICKET FOUND!",
                detail_str,
                priority="high"
            )
        
        # Enhanced visual formatting based on category
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if category == 'prato_a':
            # Red alert for Prato A
            print(f"\n{Colors.RED}{'═' * 70}{Colors.END}")
            print(f"{Colors.RED}🔴 PRATO A DISCOVERED! {'[🎯 HUNTING]' if is_hunting else '[👀 TRACKING]'} - Browser {browser_id} - {timestamp}{Colors.END}")
            print(f"{Colors.RED}{'═' * 70}{Colors.END}")
            logger.info(f"{Colors.RED}{Colors.BOLD}🎫 NEW TICKET - PRATO A{' [HUNTING]' if is_hunting else ' [TRACKING]'} - Hunter {browser_id}{Colors.END}")
            
        elif category == 'prato_b':
            # Blue alert for Prato B
            print(f"\n{Colors.BLUE}{'═' * 70}{Colors.END}")
            print(f"{Colors.BLUE}🔵 PRATO B DISCOVERED! {'[🎯 HUNTING]' if is_hunting else '[👀 TRACKING]'} - Browser {browser_id} - {timestamp}{Colors.END}")
            print(f"{Colors.BLUE}{'═' * 70}{Colors.END}")
            logger.info(f"{Colors.BLUE}{Colors.BOLD}🎫 NEW TICKET - PRATO B{' [HUNTING]' if is_hunting else ' [TRACKING]'} - Hunter {browser_id}{Colors.END}")
            
        elif category == 'settore':
            # Yellow alert for Settore
            print(f"\n{Colors.YELLOW}{'═' * 70}{Colors.END}")
            print(f"{Colors.YELLOW}🟡 SETTORE DISCOVERED! {'[🎯 HUNTING]' if is_hunting else '[👀 TRACKING]'} - Browser {browser_id} - {timestamp}{Colors.END}")
            print(f"{Colors.YELLOW}{'═' * 70}{Colors.END}")
            logger.info(f"{Colors.YELLOW}{Colors.BOLD}🎫 NEW TICKET - SETTORE (SEATED){' [HUNTING]' if is_hunting else ' [TRACKING]'} - Hunter {browser_id}{Colors.END}")
            
        else:
            # White for other
            print(f"\n{Colors.WHITE}{'─' * 70}{Colors.END}")
            print(f"⚪ Other ticket found {'[🎯 HUNTING]' if is_hunting else '[👀 TRACKING]'} - Browser {browser_id} - {timestamp}")
            print(f"{Colors.WHITE}{'─' * 70}{Colors.END}")
            logger.info(f"🎫 NEW TICKET - OTHER{' [HUNTING]' if is_hunting else ' [TRACKING]'} - Hunter {browser_id}")
        
        # Display details with nice formatting
        print(f"📍 {detail_str}")
        logger.info(f"   └─ {detail_str}")
        
        # Visual separator
        if is_hunting:
            print(f"{Colors.GREEN}{'─' * 70}{Colors.END}\n")
        else:
            print(f"{'─' * 70}\n")
    
    @retry(max_attempts=3, delay=2.0, exceptions=(WebDriverException,))
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser with multi-monitor support and version handling"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        try:
            # Try multiple approaches to handle version mismatches
            driver = None
            attempts = [
                (None, "auto-detection"),  # Try auto-detection first
                (137, "Chrome 137"),       # Then Chrome 137
                (136, "Chrome 136"),       # Chrome 136
                (138, "Chrome 138"),       # Chrome 138 as last resort
            ]
            
            for version_main, desc in attempts:
                try:
                    logger.info(f"🔄 Attempting with {desc}...")
                    
                    # IMPORTANT: Create fresh options for each attempt to avoid reuse error
                    options = uc.ChromeOptions()
                    
                    # Stealth options
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--disable-features=TranslateUI')
                    options.add_argument('--disable-infobars')
                    
                    # Performance
                    options.add_argument('--disable-logging')
                    options.add_argument('--disable-background-timer-throttling')
                    
                    # Multi-monitor window positioning
                    window_width = 450
                    window_height = 800
                    monitor_width = 1920  # Adjust based on your monitor resolution
                    
                    # Calculate position for multi-monitor setup
                    col = (browser_id - 1) % 4
                    row = (browser_id - 1) // 4
                    x = col * (window_width + 10)  # 10px gap between windows
                    y = row * 100  # Vertical offset for rows
                    
                    # If x position exceeds primary monitor, place on next monitor
                    monitor_num = x // monitor_width
                    x = x % monitor_width + (monitor_num * monitor_width)
                    
                    options.add_argument(f'--window-position={x},{y}')
                    options.add_argument(f'--window-size={window_width},{window_height}')
                    
                    # Profile persistence for cookies/storage
                    profile_dir = Path("browser_profiles") / f"browser_{browser_id}"
                    profile_dir.mkdir(parents=True, exist_ok=True)
                    options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
                    
                    # Create driver
                    driver = uc.Chrome(options=options, version_main=version_main)
                    driver.set_page_load_timeout(20)
                    
                    # Test if driver works
                    driver.execute_script("return navigator.userAgent")
                    
                    # Inject stealth JavaScript
                    driver.execute_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.chrome = {runtime: {}};
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                        Object.defineProperty(navigator, 'permissions', {
                            get: () => ({
                                query: () => Promise.resolve({state: 'granted'})
                            })
                        });
                    """)
                    
                    logger.info(f"✅ Browser {browser_id} ready at position ({x}, {y}) using {desc}")
                    return driver
                    
                except Exception as e:
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    if "version" in str(e).lower() or "chromedriver" in str(e).lower():
                        logger.warning(f"Failed with {desc}: {str(e)[:100]}...")
                        continue
                    else:
                        # For non-version related errors, log and continue
                        logger.warning(f"Error with {desc}: {str(e)[:100]}...")
                        continue
            
            # If all attempts failed
            logger.error(f"❌ All Chrome versions failed for Browser {browser_id}")
            
            # Provide helpful error message
            logger.error("\n" + "="*60)
            logger.error("🚨 CHROMEDRIVER VERSION MISMATCH DETECTED!")
            logger.error("="*60)
            logger.error("Please run one of the following commands:")
            logger.error("  1. python3 fix_chromedriver.py")
            logger.error("  2. python3 cleanup_chrome.py (if processes stuck)")
            logger.error("="*60 + "\n")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser {browser_id}: {e}")
            return None
    
    def is_blocked(self, driver: uc.Chrome) -> bool:
        """Check if we're getting 404 or blocked"""
        try:
            # Check URL and title for errors
            if any(x in driver.current_url.lower() for x in ['404', 'error', 'blocked']):
                return True
            if any(x in driver.title.lower() for x in ['404', 'error', 'non trovata']):
                return True
                
            # Check page content
            page_source = driver.page_source.lower()
            if '404' in page_source and 'non sono state trovate' not in page_source:
                return True
                
            return False
        except Exception as e:
            logger.debug(f"Block check error: {e}")
            return False

    def clear_browser_data(self, driver: uc.Chrome, browser_id: int):
        """Clear browser data to bypass blocks"""
        try:
            logger.info(f"🧹 Clearing data for Browser {browser_id} to bypass block...")
            
            # Clear all browser data
            driver.delete_all_cookies()
            driver.execute_script("""
                localStorage.clear();
                sessionStorage.clear();
                if (window.caches) {
                    caches.keys().then(names => {
                        names.forEach(name => caches.delete(name));
                    });
                }
            """)
            
            # Navigate to blank page
            driver.get("about:blank")
            time.sleep(random.uniform(0.8, 1.5))
            
            logger.info(f"✅ Browser {browser_id} data cleared")
            self.stats['blocks_encountered'] += 1
            self.save_stats()
            
        except Exception as e:
            logger.error(f"Failed to clear browser data: {e}")
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop with ticket type tracking and duplicate detection"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to event page
        logger.info(f"📍 Navigating to: {self.target_url}")
        driver.get(self.target_url)
        time.sleep(random.uniform(2.5, 3.5))
        
        check_count = 0
        last_refresh = time.time()
        last_session_refresh = time.time()
        local_stats = defaultdict(int)
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Check for 404 blocks
                if self.is_blocked(driver):
                    logger.warning(f"⚠️ Hunter {browser_id}: 404 block detected!")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(random.uniform(2.5, 3.5))
                    continue
                
                # Session refresh every 15 minutes
                if time.time() - last_session_refresh > 900:
                    logger.info(f"🔄 Hunter {browser_id}: Preventive session refresh...")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(3)
                    last_session_refresh = time.time()
                    continue
                
                # Look for tickets
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    self.stats['total_tickets_found'] += len(tickets)
                    
                    for ticket in tickets:
                        try:
                            # Extract full ticket information
                            ticket_info = self.extract_full_ticket_info(driver, ticket)
                            ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                            
                            # Check if this is a new ticket (not seen before)
                            if ticket_hash not in self.seen_tickets:
                                # New ticket discovered!
                                self.seen_tickets.add(ticket_hash)
                                self.ticket_details_cache[ticket_hash] = ticket_info
                                
                                # Update statistics
                                self.stats['unique_tickets_found'] += 1
                                category = ticket_info['category']
                                self.stats['tickets_by_type'][category] += 1
                                local_stats[category] += 1
                                
                                # Log the new ticket with full details
                                self.log_new_ticket(ticket_info, browser_id)
                                
                                # Save stats after finding new ticket
                                self.save_stats()
                                
                                # Attempt purchase if it matches our selected target categories
                                if category in self.ticket_types_to_hunt:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.max_tickets:
                                            if self.purchase_ticket(driver, ticket, browser_id):
                                                self.tickets_secured += 1
                                                self.stats['purchases'] += 1
                                                self.save_stats()
                                                
                                                if self.tickets_secured >= self.max_tickets:
                                                    logger.info(f"🎉 Max tickets secured!")
                                                    return
                                                    
                        except Exception as e:
                            logger.debug(f"Error processing ticket: {e}")
                            continue
                
                # Smart refresh strategy
                refresh_time = random.uniform(2.5, 3.5)
                
                # Full page refresh every 30 seconds
                if time.time() - last_refresh > 30:
                    driver.refresh()
                    last_refresh = time.time()
                else:
                    time.sleep(refresh_time)
                
                # Progress update every 50 checks
                if check_count % 25 == 0:
                    elapsed = time.time() - self.session_start_time
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    
                    # Show local stats for this hunter
                    local_summary = []
                    if local_stats['prato_a'] > 0:
                        local_summary.append(f"Prato A: {local_stats['prato_a']}")
                    if local_stats['prato_b'] > 0:
                        local_summary.append(f"Prato B: {local_stats['prato_b']}")
                    if local_stats['settore'] > 0:
                        local_summary.append(f"Settore: {local_stats['settore']}")
                    if local_stats['other'] > 0:
                        local_summary.append(f"Other: {local_stats['other']}")
                    
                    local_str = " | ".join(local_summary) if local_summary else "No new tickets"
                    # Animated spinner
                    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                    spinner = spinners[check_count // 25 % len(spinners)]
                    
                    # Speed indicator
                    if rate > 40:
                        speed_icon = '🚀'
                        speed_color = Colors.GREEN
                    elif rate > 20:
                        speed_icon = '⚡'
                        speed_color = Colors.YELLOW
                    else:
                        speed_icon = '🐌'
                        speed_color = Colors.RED
                    
                    # Enhanced status line with colors
                    status_line = f"{spinner} Browser {browser_id} | {check_count:>4} checks | {speed_icon} {speed_color}{rate:>4.1f}/min{Colors.END} | {local_str}"
                    
                    logger.info(status_line)
                    
            except TimeoutException:
                logger.warning(f"Hunter {browser_id}: Page timeout, refreshing...")
                driver.refresh()
                time.sleep(random.uniform(1.5, 2.5))
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    logger.error(f"Hunter {browser_id}: Session died")
                    break
                logger.error(f"Hunter {browser_id}: Browser error, continuing...")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                time.sleep(5)
    
    @retry(max_attempts=2, delay=0.5, exceptions=(ElementNotInteractableException, StaleElementReferenceException))
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click the ticket
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            driver.execute_script("arguments[0].click();", ticket_element)
            time.sleep(random.uniform(0.8, 1.2))
            
            # Find and click buy button
            buy_selectors = [
                "button[data-qa='buyNowButton']",
                "button[class*='buy']",
                "button[class*='acquista']",
                "//button[contains(text(), 'Acquista')]",
                "//button[contains(text(), 'Buy')]"
            ]
            
            for selector in buy_selectors:
                try:
                    if selector.startswith('//'):
                        buy_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    driver.execute_script("arguments[0].click();", buy_btn)
                    logger.info(f"✅ Hunter {browser_id}: Buy button clicked!")
                    
                    # Play alarm sound
                    print('\a' * 3)  # System beep
                    
                    # Take screenshot
                    screenshot_path = f"screenshots/ticket_{int(time.time())}.png"
                    Path("screenshots").mkdir(exist_ok=True)
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                    
                    return True
                    
                except Exception as e:
                    continue
                    
            logger.warning(f"Hunter {browser_id}: Couldn't find buy button")
            return False
            
        except Exception as e:
            logger.debug(f"Purchase failed: {e}")
            return False
    
    def show_statistics_dashboard(self):
        """Display beautiful statistics dashboard with enhanced visuals"""
        total_runtime = self.stats['all_time_runtime'] + (time.time() - self.session_start_time)
        hours = int(total_runtime // 3600)
        minutes = int((total_runtime % 3600) // 60)
        
        # Enhanced header with box drawing characters
        print(f"\n{Colors.CYAN}╔{'═' * 58}╗{Colors.END}")
        print(f"{Colors.CYAN}║{Colors.END}{Colors.BOLD}{Colors.CYAN}{'📊 FANSALE BOT STATISTICS DASHBOARD'.center(58)}{Colors.END}{Colors.CYAN}║{Colors.END}")
        print(f"{Colors.CYAN}╚{'═' * 58}╝{Colors.END}")
        
        # Runtime and checks section
        print(f"\n{Colors.BOLD}⏱️  Total Runtime:{Colors.END} {Colors.GREEN}{hours}h {minutes}m{Colors.END}")
        print(f"{Colors.BOLD}🔍 Total Checks:{Colors.END} {Colors.YELLOW}{self.stats['total_checks']:,}{Colors.END}")
        print(f"{Colors.BOLD}🎫 Unique Tickets:{Colors.END} {Colors.MAGENTA}{self.stats['unique_tickets_found']:,}{Colors.END}")
        
        # Ticket breakdown with progress bars
        print(f"\n{Colors.BOLD}📈 Ticket Categories:{Colors.END}")
        max_tickets = max(self.stats['tickets_by_type'].values()) if any(self.stats['tickets_by_type'].values()) else 1
        
        for category, count in self.stats['tickets_by_type'].items():
            if category == 'prato_a':
                color = Colors.RED
                emoji = '🔴'
                label = 'Prato A'
            elif category == 'prato_b':
                color = Colors.BLUE
                emoji = '🔵'
                label = 'Prato B'
            elif category == 'settore':
                color = Colors.YELLOW
                emoji = '🟡'
                label = 'Settore'
            else:
                color = Colors.WHITE
                emoji = '⚪'
                label = 'Other'
            
            # Create visual bar
            bar_length = int((count / max_tickets) * 20) if max_tickets > 0 else 0
            bar = '█' * bar_length + '░' * (20 - bar_length)
            
            print(f"   {emoji} {label:8} {color}{bar}{Colors.END} {count:3}")
        
        # Performance metrics
        print(f"\n{Colors.BOLD}📊 Performance Metrics:{Colors.END}")
        print(f"   💳 Purchases: {Colors.GREEN}{self.stats['purchases']}{Colors.END}")
        print(f"   🚫 Blocks Cleared: {Colors.YELLOW}{self.stats['blocks_encountered']}{Colors.END}")
        
        if self.stats['total_checks'] > 0:
            rate = self.stats['total_checks'] / (total_runtime / 60) if total_runtime > 0 else 0
            # Visual speed indicator
            if rate > 40:
                speed_color = Colors.GREEN
                speed_emoji = '🚀'
            elif rate > 20:
                speed_color = Colors.YELLOW
                speed_emoji = '⚡'
            else:
                speed_color = Colors.RED
                speed_emoji = '🐌'
            
            print(f"   {speed_emoji} Check Rate: {speed_color}{rate:.1f} checks/min{Colors.END}")
        
        print(f"\n{Colors.CYAN}{'─' * 60}{Colors.END}")

    def show_daily_statistics(self):
        """Display daily ticket statistics in a beautiful table format"""
        print(f"\n{Colors.CYAN}╔{'═' * 58}╗{Colors.END}")
        print(f"{Colors.CYAN}║{Colors.END}{Colors.BOLD}{Colors.CYAN}{'📅 DAILY TICKET DISCOVERY HISTORY'.center(58)}{Colors.END}{Colors.CYAN}║{Colors.END}")
        print(f"{Colors.CYAN}╠{'═' * 58}╣{Colors.END}")
        
        # Group statistics by day
        daily_stats = defaultdict(lambda: {
            'prato_a': 0, 'prato_b': 0, 'settore': 0, 'other': 0, 'total': 0
        })
        
        # Mock data for demonstration (in real implementation, this would come from session history)
        today = datetime.now().date()
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            if i == 0:  # Today
                daily_stats[date_str] = {
                    'prato_a': self.stats['tickets_by_type']['prato_a'],
                    'prato_b': self.stats['tickets_by_type']['prato_b'],
                    'settore': self.stats['tickets_by_type']['settore'],
                    'other': self.stats['tickets_by_type']['other'],
                    'total': self.stats['unique_tickets_found']
                }
            elif i < 3:  # Mock some data for recent days
                daily_stats[date_str] = {
                    'prato_a': random.randint(0, 2),
                    'prato_b': random.randint(0, 3),
                    'settore': random.randint(0, 5),
                    'other': random.randint(0, 2),
                    'total': 0
                }
                daily_stats[date_str]['total'] = sum([
                    daily_stats[date_str]['prato_a'],
                    daily_stats[date_str]['prato_b'],
                    daily_stats[date_str]['settore'],
                    daily_stats[date_str]['other']
                ])
        
        # Table header
        print(f"{Colors.CYAN}║{Colors.END} {'Date':^12} │ {'🔴 A':^6} │ {'🔵 B':^6} │ {'🟡 S':^6} │ {'⚪ O':^6} │ {'Total':^7} {Colors.CYAN}║{Colors.END}")
        print(f"{Colors.CYAN}╟{'─' * 14}┼{'─' * 8}┼{'─' * 8}┼{'─' * 8}┼{'─' * 8}┼{'─' * 9}╢{Colors.END}")
        
        # Display daily data
        for date_str in sorted(daily_stats.keys(), reverse=True)[:7]:
            stats = daily_stats[date_str]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Highlight today
            if date_obj == today:
                date_display = f"{Colors.GREEN}{Colors.BOLD}Today{Colors.END}".ljust(20)
            elif date_obj == today - timedelta(days=1):
                date_display = "Yesterday"
            else:
                date_display = date_obj.strftime("%a %d %b")
            
            # Color code based on total tickets
            if stats['total'] == 0:
                total_color = Colors.RED
            elif stats['total'] < 5:
                total_color = Colors.YELLOW
            else:
                total_color = Colors.GREEN
            
            print(f"{Colors.CYAN}║{Colors.END} {date_display:^12} │ {stats['prato_a']:^6} │ {stats['prato_b']:^6} │ {stats['settore']:^6} │ {stats['other']:^6} │ {total_color}{stats['total']:^7}{Colors.END} {Colors.CYAN}║{Colors.END}")
        
        print(f"{Colors.CYAN}╚{'═' * 58}╝{Colors.END}")
        
        # Summary stats
        total_all_time = sum(self.stats['tickets_by_type'].values())
        if total_all_time > 0:
            print(f"\n{Colors.BOLD}📊 All-Time Summary:{Colors.END}")
            print(f"   🎯 Most Found: ", end="")
            max_type = max(self.stats['tickets_by_type'].items(), key=lambda x: x[1])
            type_names = {'prato_a': 'Prato A', 'prato_b': 'Prato B', 'settore': 'Settore', 'other': 'Other'}
            print(f"{Colors.GREEN}{type_names[max_type[0]]} ({max_type[1]} tickets){Colors.END}")
            print(f"   📈 Success Rate: {Colors.YELLOW}{(self.stats['purchases'] / total_all_time * 100):.1f}%{Colors.END}" if total_all_time > 0 else "")

    def show_daily_statistics(self):
        """Display tickets found per day in a beautiful table"""
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        # Group tickets by date
        daily_stats = defaultdict(lambda: {'prato_a': 0, 'prato_b': 0, 'settore': 0, 'other': 0, 'total': 0})
        
        # Parse session data if available
        if 'sessions' in self.stats:
            for session in self.stats.get('sessions', []):
                try:
                    date = datetime.fromisoformat(session.get('start', '')).date()
                    daily_stats[date]['total'] += session.get('tickets_found', 0)
                except:
                    pass
        
        # Add current stats
        today = datetime.now().date()
        for category, count in self.stats['tickets_by_type'].items():
            daily_stats[today][category] = count
            daily_stats[today]['total'] = self.stats['unique_tickets_found']
        
        # Display table
        print(f"\n{Colors.MAGENTA}╔{'═' * 58}╗{Colors.END}")
        print(f"{Colors.MAGENTA}║{Colors.END}{Colors.BOLD}{'📅 DAILY TICKET DISCOVERIES'.center(58)}{Colors.END}{Colors.MAGENTA}║{Colors.END}")
        print(f"{Colors.MAGENTA}╠{'═' * 58}╣{Colors.END}")
        print(f"{Colors.MAGENTA}║{Colors.END} {'Date':^12} │ {'🔴 A':^6} │ {'🔵 B':^6} │ {'🟡 S':^6} │ {'⚪ O':^6} │ {'Total':^6} {Colors.MAGENTA}║{Colors.END}")
        print(f"{Colors.MAGENTA}╟{'─' * 58}╢{Colors.END}")
        
        # Sort dates and show last 7 days
        sorted_dates = sorted(daily_stats.keys(), reverse=True)[:7]
        
        for date in sorted_dates:
            stats = daily_stats[date]
            date_str = date.strftime("%d/%m/%Y")
            
            # Highlight today
            if date == today:
                date_str = f"{Colors.GREEN}{date_str}{Colors.END}"
            
            print(f"{Colors.MAGENTA}║{Colors.END} {date_str:^12} │ {stats['prato_a']:^6} │ {stats['prato_b']:^6} │ {stats['settore']:^6} │ {stats['other']:^6} │ {Colors.BOLD}{stats['total']:^6}{Colors.END} {Colors.MAGENTA}║{Colors.END}")
        
        print(f"{Colors.MAGENTA}╚{'═' * 58}╝{Colors.END}")
        
        # Fun fact
        total_all_time = sum(d['total'] for d in daily_stats.values())
        if total_all_time > 0:
            best_day = max(daily_stats.items(), key=lambda x: x[1]['total'])
            print(f"\n{Colors.CYAN}💡 Best day: {best_day[0].strftime('%d/%m/%Y')} with {best_day[1]['total']} tickets!{Colors.END}")
    
    def configure_ticket_filters(self):
        """Allow user to select which ticket types to hunt for"""
        print(f"\n{Colors.BOLD}🎯 SELECT TICKET TYPES TO HUNT{Colors.END}")
        print("=" * 50)
        
        # Available ticket types
        available_types = {
            '1': ('prato_a', 'Prato A', Colors.GREEN),
            '2': ('prato_b', 'Prato B', Colors.BLUE),
            '3': ('prato_all', 'All Prato (A + B)', Colors.CYAN),
            '4': ('settore', 'Settore', Colors.YELLOW),
            '5': ('other', 'Other/Unknown', Colors.CYAN),
            '6': ('all', 'ALL ticket types', Colors.BOLD)
        }
        
        print("\nAvailable ticket categories:")
        for key, (_, display, color) in available_types.items():
            if key == '3':
                print(f"  {color}{key}. {display}{Colors.END} ⭐")
            elif key == '4':
                print(f"  {color}{key}. {display}{Colors.END} (Seated: Fila/Posto/Anello)")
            elif key == '6':
                print(f"\n  {color}{key}. {display}{Colors.END}")
            else:
                print(f"  {color}{key}. {display}{Colors.END}")
        
        while True:
            selection = input(f"\n{Colors.BOLD}Enter your choices (e.g., '1,2' or '3' for all Prato):{Colors.END} ").strip()
            
            if not selection:
                # Default to all Prato types
                self.ticket_types_to_hunt = {'prato_a', 'prato_b'}
                print(f"{Colors.GREEN}✅ Hunting for all Prato tickets (A + B){Colors.END}")
                break
                
            choices = [s.strip() for s in selection.split(',')]
            
            # Check if user selected "all"
            if '6' in choices:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
                print(f"{Colors.GREEN}✅ Hunting for ALL ticket types{Colors.END}")
                break
            
            # Check if user selected "all prato"
            if '3' in choices:
                # Remove individual prato selections if "all prato" is selected
                choices = [c for c in choices if c not in ['1', '2']]
                if '3' in choices:
                    choices.remove('3')
                    choices.extend(['1', '2'])  # Add both Prato types
            
            # Validate selections
            valid_choices = []
            for choice in choices:
                if choice in ['1', '2', '4', '5']:
                    valid_choices.append(choice)
                else:
                    print(f"{Colors.RED}❌ Invalid choice: {choice}{Colors.END}")
            
            if valid_choices:
                # Convert to ticket types
                self.ticket_types_to_hunt = set()
                selected_display = []
                
                # Remove duplicates and sort
                valid_choices = sorted(set(valid_choices))
                
                for choice in valid_choices:
                    if choice in ['1', '2', '4', '5']:  # Skip '3' as it's been expanded
                        type_key, display_name, color = available_types[choice]
                        self.ticket_types_to_hunt.add(type_key)
                        selected_display.append(f"{color}{display_name}{Colors.END}")
                
                print(f"\n{Colors.GREEN}✅ Selected: {', '.join(selected_display)}{Colors.END}")
                break
            else:
                print(f"{Colors.RED}Please enter valid choices (1-6){Colors.END}")

    def configure(self):
        """Configure bot settings with enhanced visual display"""
        # Clear screen for clean start
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # ASCII Art Header
        print(f"{Colors.CYAN}")
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║   _____ _____ _____ _____ _____ ___     _____ _____ _____    ║")
        print("║  |   __|  _  |   | |   __|  _  |   |   |   __| __  |     |   ║")
        print("║  |   __|     | | | |__   |     |   |   |   __| __ -|  |  |   ║")
        print("║  |__|  |__|__|_|___|_____|__|__|___|   |_____|_____|_____|   ║")
        print("║                                                               ║")
        print("║              🎫 ENHANCED TICKET HUNTER v2.0 🎫                ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")
        
        print(f"\n{Colors.GREEN}✨ Features:{Colors.END}")
        print("  • No login required - Direct ticket hunting")
        print("  • Multi-category tracking (Prato A/B, Settore)")
        print("  • Intelligent duplicate detection")
        print("  • Persistent statistics & session history")
        print("  • Real-time visual alerts")
        
        # Show daily statistics
        self.show_daily_statistics()
        
        # Show current stats
        self.show_statistics_dashboard()
        
        # Number of browsers with visual indicator
        print(f"\n{Colors.BOLD}🌐 BROWSER CONFIGURATION{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.END}")
        
        while True:
            try:
                num = input(f"{Colors.BOLD}Number of browsers (1-8, default 2):{Colors.END} ").strip()
                if not num:
                    self.num_browsers = 2
                    break
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 8:
                    break
                print(f"{Colors.RED}❌ Please enter 1-8{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}❌ Invalid number{Colors.END}")
        
        # Visual browser layout preview
        print(f"\n{Colors.CYAN}Browser Layout Preview:{Colors.END}")
        for i in range(1, self.num_browsers + 1):
            col = (i - 1) % 4
            monitor = (col // 2) + 1
            print(f"  Browser {i} → Monitor {monitor}")
        
        # Max tickets
        print(f"\n{Colors.BOLD}🎫 TICKET CONFIGURATION{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.END}")
        
        while True:
            try:
                max_t = input(f"{Colors.BOLD}Max tickets to reserve (1-4, default 2):{Colors.END} ").strip()
                if not max_t:
                    self.max_tickets = 2
                    break
                self.max_tickets = int(max_t)
                if 1 <= self.max_tickets <= 4:
                    break
                print(f"{Colors.RED}❌ Please enter 1-4{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}❌ Invalid number{Colors.END}")
        
        # Configure ticket type filters
        self.configure_ticket_filters()
        
        # Enhanced summary with visual elements
        print(f"\n{Colors.GREEN}╔{'═' * 58}╗{Colors.END}")
        print(f"{Colors.GREEN}║{Colors.END}{Colors.BOLD}{'📋 CONFIGURATION SUMMARY'.center(58)}{Colors.END}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.GREEN}╠{'═' * 58}╣{Colors.END}")
        
        print(f"{Colors.GREEN}║{Colors.END} 🌐 Browsers: {Colors.YELLOW}{self.num_browsers}{Colors.END} {'browser' if self.num_browsers == 1 else 'browsers':<44} {Colors.GREEN}║{Colors.END}")
        print(f"{Colors.GREEN}║{Colors.END} 🎫 Max Tickets: {Colors.YELLOW}{self.max_tickets}{Colors.END} {'ticket' if self.max_tickets == 1 else 'tickets':<42} {Colors.GREEN}║{Colors.END}")
        
        # Show selected ticket types with emojis
        type_display = {
            'prato_a': '🔴 Prato A',
            'prato_b': '🔵 Prato B',
            'settore': '🟡 Settore',
            'other': '⚪ Other'
        }
        selected = [type_display[t] for t in sorted(self.ticket_types_to_hunt)]
        hunting_str = ', '.join(selected)
        
        print(f"{Colors.GREEN}║{Colors.END} 🎯 Hunting: {hunting_str:<45} {Colors.GREEN}║{Colors.END}")
        print(f"{Colors.GREEN}║{Colors.END} 🔗 URL: {self.target_url[:48] + '...' if len(self.target_url) > 48 else self.target_url:<51} {Colors.GREEN}║{Colors.END}")
        print(f"{Colors.GREEN}╚{'═' * 58}╝{Colors.END}")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}⚡ READY TO HUNT! No login required - Direct ticket access!{Colors.END}")
    
    def run(self):
        """Main execution with enhanced tracking"""
        try:
            # Configure
            self.configure()
            
            # Create browsers
            print(f"\n{Colors.BOLD}🚀 Starting {self.num_browsers} browser(s)...{Colors.END}")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created")
                return

            logger.info(f"✅ {len(self.browsers)} browser(s) ready!")
            
            # Show tip about monitoring
            print(f"\n{Colors.CYAN}💡 TIP: Browsers are positioned for multi-monitor setups{Colors.END}")
            print(f"{Colors.CYAN}   Move them to your preferred monitors if needed{Colors.END}")
            
            input(f"\n{Colors.BOLD}✋ Press Enter to START HUNTING...{Colors.END}")
            
            # Start hunting
            threads = []
            
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_tickets,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
            
            # Monitor progress with enhanced display
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎯 HUNTING ACTIVE! Press Ctrl+C to stop.{Colors.END}\n")
            
            # Display hunting targets
            print(f"{Colors.CYAN}╔{'═' * 58}╗{Colors.END}")
            print(f"{Colors.CYAN}║{Colors.END}{Colors.BOLD}{'🎯 ACTIVELY HUNTING FOR:'.center(58)}{Colors.END}{Colors.CYAN}║{Colors.END}")
            print(f"{Colors.CYAN}╠{'═' * 58}╣{Colors.END}")
            
            type_emojis = {
                'prato_a': '🔴 PRATO A - Standing Area (Front)',
                'prato_b': '🔵 PRATO B - Standing Area (Back)',
                'settore': '🟡 SETTORE - Seated Sections',
                'other': '⚪ OTHER - Miscellaneous Tickets'
            }
            
            for ticket_type in self.ticket_types_to_hunt:
                print(f"{Colors.CYAN}║{Colors.END} {type_emojis.get(ticket_type, ticket_type):<56} {Colors.CYAN}║{Colors.END}")
            
            print(f"{Colors.CYAN}╚{'═' * 58}╝{Colors.END}\n")
            
            try:
                last_update = time.time()
                while self.tickets_secured < self.max_tickets:
                    time.sleep(1)
                    
                    # Status update every 60 seconds
                    if time.time() - last_update > 60:
                        self.show_statistics_dashboard()
                        last_update = time.time()
                    
                logger.info(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SUCCESS! {self.tickets_secured} tickets secured!{Colors.END}")
                
            except KeyboardInterrupt:
                logger.info(f"\n{Colors.YELLOW}🛑 Stopping...{Colors.END}")
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            
        finally:
            # Cleanup
            self.shutdown_event.set()
            
            # Save final stats
            self.save_stats()
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except Exception as e:
                    logger.debug(f"Error closing browser: {e}")
            
            # Show final statistics
            print(f"\n{Colors.BOLD}{Colors.CYAN}📊 FINAL SESSION STATISTICS{Colors.END}")
            self.show_statistics_dashboard()


def main():
    """Enhanced entry point with configuration support"""
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🎫 FANSALE BOT - ENTERPRISE EDITION{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"\n{Colors.GREEN}✨ Features:{Colors.END}")
    print("  • Ticket type tracking (Prato A, B, Settore)")
    print("  • Duplicate detection with notifications")
    print("  • Persistent statistics")
    print("  • Multi-monitor support")
    print("  • Health monitoring")
    print("  • Advanced retry logic")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"\n{Colors.RED}❌ Missing dependency: {e}{Colors.END}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    
    # Load configuration
    config_path = Path("bot_config.json")
    config = BotConfig.from_file(config_path)
    
    # Save default config if not exists
    if not config_path.exists():
        config.save(config_path)
        print(f"\n{Colors.YELLOW}📝 Created default configuration: {config_path}{Colors.END}")
    
    # Check for target URL
    if not os.getenv('FANSALE_TARGET_URL'):
        print(f"\n{Colors.YELLOW}⚠️  No target URL in .env file{Colors.END}")
        print("Using default Bruce Springsteen URL")
        print("To change, add to .env file:")
        print("FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/...")
        time.sleep(random.uniform(1.5, 2.5))
    
    # Run bot with configuration
    bot = FanSaleBot(config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Graceful shutdown initiated...{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Fatal error: {e}{Colors.END}")
        logging.exception("Fatal error in main")
    finally:
        print(f"\n{Colors.GREEN}✅ Thank you for using FanSale Bot!{Colors.END}")


if __name__ == "__main__":
    main()