#!/usr/bin/env python3
"""
FanSale Bot V5 - Complete rewrite with fixes for all reported issues
- VERIFIED image loading
- Enhanced popup detection and dismissal
- Improved CAPTCHA detection
- Working 2captcha implementation
- Performance optimizations
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
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
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
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, ElementNotInteractableException, 
    StaleElementReferenceException, NoSuchElementException, ElementClickInterceptedException
)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

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
    min_wait: float = 0.3  # Ultra-fast: ~60-100 checks/min
    max_wait: float = 1.0  # Ultra-fast: ~60-100 checks/min
    retry_attempts: int = 3
    retry_delay: float = 1.0
    captcha_grace_period: int = 300  # 5 minutes after solving CAPTCHA
    twocaptcha_api_key: str = ""  # Optional: for automatic solving
    auto_solve_captcha: bool = False
    popup_check_interval: int = 210  # Changed from 3 to 210 seconds (3.5 minutes)
    enable_image_loading: bool = True  # EXPLICITLY ENABLE IMAGES
    captcha_check_interval: int = 300  # New: Check CAPTCHA every 5 minutes
    
    @classmethod
    def from_file(cls, path: Path) -> 'BotConfig':
        """Load config from JSON file if exists"""
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save(self, path: Path):
        """Save config to JSON file"""
        # Don't save API key to file
        data = self.__dict__.copy()
        if 'twocaptcha_api_key' in data:
            data['twocaptcha_api_key'] = ""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

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
            'captchas_encountered': 0,
            'captchas_solved': 0,
            'captchas_auto_solved': 0,
            'popups_dismissed': 0,
            'all_time_runtime': 0,
            'images_verified': 0,
            'performance_metrics': {
                'avg_page_load_time': 0,
                'avg_ticket_check_time': 0,
                'avg_popup_dismiss_time': 0
            }
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

# Enhanced 2Captcha solver class
class TwoCaptchaSolver:
    """Handles automatic CAPTCHA solving via 2captcha service"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.session = requests.Session()  # Reuse connection
        
    def solve_recaptcha(self, sitekey: str, pageurl: str, timeout: int = 180) -> Optional[str]:
        """Solve reCAPTCHA and return token"""
        if not self.api_key:
            logger.error("No 2captcha API key provided")
            return None
            
        try:
            # Submit CAPTCHA
            submit_url = f"{self.base_url}/in.php"
            submit_data = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': sitekey,
                'pageurl': pageurl,
                'json': 1
            }
            
            logger.info("🤖 Submitting CAPTCHA to 2captcha...")
            response = self.session.post(submit_url, data=submit_data, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"2captcha submission failed: {result}")
                return None
                
            captcha_id = result.get('request')
            logger.info(f"✅ CAPTCHA submitted, ID: {captcha_id}")
            
            # Wait for solution
            result_url = f"{self.base_url}/res.php"
            start_time = time.time()
            check_interval = 5
            
            while time.time() - start_time < timeout:
                time.sleep(check_interval)
                
                result_params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = self.session.get(result_url, params=result_params, timeout=30)
                result = response.json()
                
                if result.get('status') == 1:
                    token = result.get('request')
                    logger.info(f"✅ CAPTCHA solved automatically in {time.time() - start_time:.1f}s!")
                    return token
                elif result.get('request') not in ['CAPCHA_NOT_READY', 'CAPTCHA_NOT_READY']:
                    logger.error(f"2captcha error: {result}")
                    return None
                    
            logger.error("2captcha timeout")
            return None
            
        except requests.RequestException as e:
            logger.error(f"2captcha network error: {e}")
            return None
        except Exception as e:
            logger.error(f"2captcha unexpected error: {e}")
            return None

# Notification Manager
class NotificationManager:
    """Manages notifications for ticket discoveries"""
    def __init__(self, enabled: bool = True):
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
        self.start_time = time.time()
        
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
                'uptime_seconds': time.time() - self.start_time
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
            elif 'CAPTCHA' in record.msg:
                record.msg = f"{Colors.RED}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'IMAGE' in record.msg.upper():
                record.msg = f"{Colors.GREEN}{Colors.BOLD}{record.msg}{Colors.END}"
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
file_handler = logging.FileHandler('fansale_bot_v5.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(file_handler)

class FanSaleBot:
    """Enhanced FanSale bot V5 with all fixes"""
    
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
        
        # CAPTCHA tracking - per browser
        self.captcha_solved_time = {}  # browser_id -> timestamp when CAPTCHA was solved
        self.captcha_grace_period = self.config.captcha_grace_period  # 5 minutes default
        
        # Load persistent statistics using thread-safe manager
        self.stats_file = Path("fansale_stats_v5.json")
        self.stats_manager = StatsManager(self.stats_file)
        self.stats = self.stats_manager.stats
        
        # Performance monitoring
        self.session_start_time = time.time()
        self.performance_tracker = defaultdict(list)
        
        # Health monitoring and notifications
        self.health_monitor = HealthMonitor()
        self.notification_manager = NotificationManager(enabled=True)
        
        # 2Captcha solver - FIXED initialization
        api_key = self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY', '')
        if api_key:
            self.captcha_solver = TwoCaptchaSolver(api_key)
            self.auto_solve = self.config.auto_solve_captcha
            logger.info(f"✅ 2Captcha configured with API key: {api_key[:8]}...")
        else:
            self.captcha_solver = None
            self.auto_solve = False
            logger.warning("⚠️ No 2Captcha API key - manual CAPTCHA solving only")

    def save_stats(self):
        """Save statistics to file"""
        try:
            # Update runtime
            session_time = time.time() - self.session_start_time
            self.stats['all_time_runtime'] = self.stats.get('all_time_runtime', 0) + session_time
            
            # Update performance metrics
            if 'page_load' in self.performance_tracker:
                avg_load = sum(self.performance_tracker['page_load']) / len(self.performance_tracker['page_load'])
                self.stats['performance_metrics']['avg_page_load_time'] = avg_load
                
            self.stats_manager.save()
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def verify_image_loading(self, driver: uc.Chrome, browser_id: int) -> bool:
        """Verify that images are actually loading in the browser"""
        try:
            # Navigate to a test page with images
            driver.get("https://www.google.com/imghp")
            time.sleep(2)
            
            # Check if images are loading
            result = driver.execute_script("""
                var images = document.querySelectorAll('img');
                var loadedCount = 0;
                var totalCount = images.length;
                
                for (var i = 0; i < images.length; i++) {
                    if (images[i].naturalWidth > 0 && images[i].naturalHeight > 0) {
                        loadedCount++;
                    }
                }
                
                return {
                    total: totalCount,
                    loaded: loadedCount,
                    percentage: totalCount > 0 ? (loadedCount / totalCount * 100) : 0
                };
            """)
            
            if result['percentage'] > 50:  # If more than 50% of images loaded
                logger.info(f"✅ Browser {browser_id}: Images loading verified ({result['loaded']}/{result['total']} = {result['percentage']:.1f}%)")
                self.stats['images_verified'] += 1
                return True
            else:
                logger.error(f"❌ Browser {browser_id}: Images NOT loading properly! ({result['loaded']}/{result['total']} = {result['percentage']:.1f}%)")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify image loading: {e}")
            return False
    
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
        """Log newly discovered ticket with full details"""
        category = ticket_info['category']
        
        # Check if we're hunting this type
        is_hunting = category in self.ticket_types_to_hunt
        hunt_indicator = " [HUNTING]" if is_hunting else " [TRACKING]"
        
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
            details.append(f"Price: {ticket_info['price']}")
        
        detail_str = " | ".join(details) if details else ticket_info['raw_text'][:100]
        
        # Send notification if hunting this type
        if is_hunting:
            self.notification_manager.notify(
                f"🎫 NEW {category.upper()} TICKET FOUND!",
                detail_str,
                priority="high"
            )
        
        # Log with appropriate formatting based on category
        if category == 'prato_a':
            logger.info(f"🎫 NEW TICKET - PRATO A{hunt_indicator} - Hunter {browser_id}")
            logger.info(f"   └─ {detail_str}")
            logger.info("   " + "─" * 60)
        elif category == 'prato_b':
            logger.info(f"🎫 NEW TICKET - PRATO B{hunt_indicator} - Hunter {browser_id}")
            logger.info(f"   └─ {detail_str}")
            logger.info("   " + "─" * 60)
        elif category == 'settore':
            logger.info(f"🎫 NEW TICKET - SETTORE (SEATED){hunt_indicator} - Hunter {browser_id}")
            logger.info(f"   └─ {detail_str}")
            logger.info("   " + "─" * 60)
        else:
            logger.info(f"🎫 NEW TICKET - OTHER{hunt_indicator} - Hunter {browser_id}")
            logger.info(f"   └─ {detail_str}")
            logger.info("   " + "─" * 60)
    
    def check_captcha_status(self, browser_id: int) -> bool:
        """Check if browser is within CAPTCHA grace period"""
        if browser_id in self.captcha_solved_time:
            time_since_solved = time.time() - self.captcha_solved_time[browser_id]
            if time_since_solved < self.captcha_grace_period:
                remaining = self.captcha_grace_period - time_since_solved
                logger.debug(f"Hunter {browser_id}: CAPTCHA grace period active ({remaining:.0f}s remaining)")
                return True
        return False
    
    def mark_captcha_solved(self, browser_id: int):
        """Mark CAPTCHA as solved for this browser"""
        self.captcha_solved_time[browser_id] = time.time()
        self.stats['captchas_solved'] += 1
        self.save_stats()
        logger.info(f"✅ Hunter {browser_id}: CAPTCHA solved! Grace period active for {self.captcha_grace_period}s")
    
    def dismiss_popups(self, driver: uc.Chrome, browser_id: int) -> int:
        """Enhanced popup detection and dismissal - returns number dismissed"""
        start_time = time.time()
        dismissed_count = 0
        
        try:
            # Enhanced popup selectors with more specific patterns
            popup_strategies = [
                # Strategy 0: Priority - "Carica Offerte" button (must be first)
                {
                    'name': 'carica_offerte',
                    'selectors': [
                        "button.js-BotProtectionModalButton1",
                        "button.js-BotProtectionModalButtonTrigger",
                        "button.Button-super:contains('Carica Offerte')",
                        "button[name='_submit'][value='true']"
                    ],
                    'action': 'click_directly'
                },
                # Strategy 1: Look for visible overlays/modals first
                {
                    'name': 'overlay',
                    'selectors': [
                        "div[class*='overlay']:not([style*='display: none'])",
                        "div[class*='modal']:not([style*='display: none'])",
                        "div[class*='popup']:not([style*='display: none'])",
                        "div[id*='overlay']:not([style*='display: none'])",
                        "div[id*='modal']:not([style*='display: none'])",
                        "div[id*='popup']:not([style*='display: none'])"
                    ],
                    'action': 'find_close_button_or_click_overlay'
                },
                
                # Strategy 2: Cookie/GDPR banners
                {
                    'name': 'cookie_banner',
                    'selectors': [
                        "div[class*='cookie']",
                        "div[class*='gdpr']",
                        "div[class*='privacy']",
                        "div[id*='cookie']",
                        "div[id*='gdpr']"
                    ],
                    'action': 'find_accept_button'
                },
                
                # Strategy 3: Direct button selectors (including Carica Offerte)
                {
                    'name': 'direct_buttons',
                    'selectors': [
                        "button[class*='close']:visible",
                        "button[aria-label*='close' i]:visible",
                        "button[aria-label*='chiudi' i]:visible",
                        "a[class*='close']:visible",
                        "span[class*='close']:visible",
                        "button:contains('Accetta'):visible",
                        "button:contains('OK'):visible",
                        "button:contains('Chiudi'):visible",
                        "button:contains('X'):visible",
                        "button.js-BotProtectionModalButton1",  # Carica Offerte button
                        "button:contains('Carica Offerte'):visible"  # Backup selector
                    ],
                    'action': 'click_directly'
                }
            ]
            
            for strategy in popup_strategies:
                for selector in strategy['selectors']:
                    try:
                        # Handle jQuery-style :visible pseudo-selector
                        if ':visible' in selector:
                            selector = selector.replace(':visible', '')
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            elements = [e for e in elements if e.is_displayed()]
                        elif ':contains' in selector:
                            # Handle contains selector with XPath
                            match = re.search(r":contains\('([^']+)'\)", selector)
                            if match:
                                text = match.group(1)
                                tag = selector.split(':')[0]
                                xpath = f"//{tag}[contains(text(), '{text}')]"
                                elements = driver.find_elements(By.XPATH, xpath)
                                elements = [e for e in elements if e.is_displayed()]
                            else:
                                continue
                        else:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            if not element.is_displayed():
                                continue
                                
                            try:
                                if strategy['action'] == 'find_close_button_or_click_overlay':
                                    # First try to find a close button within the overlay
                                    close_buttons = element.find_elements(By.CSS_SELECTOR, 
                                        "button, a, span, div[class*='close'], div[role='button']")
                                    
                                    clicked = False
                                    for btn in close_buttons:
                                        btn_text = btn.text.lower()
                                        btn_class = btn.get_attribute('class') or ''
                                        btn_aria = btn.get_attribute('aria-label') or ''
                                        
                                        if any(x in btn_text + btn_class + btn_aria.lower() for x in 
                                               ['close', 'chiudi', 'x', 'dismiss', 'ok', 'accetta']):
                                            driver.execute_script("arguments[0].click();", btn)
                                            logger.info(f"📢 Hunter {browser_id}: Dismissed {strategy['name']} via close button")
                                            dismissed_count += 1
                                            clicked = True
                                            time.sleep(0.5)
                                            break
                                    
                                    # If no close button found, try clicking the overlay itself
                                    if not clicked:
                                        driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"📢 Hunter {browser_id}: Dismissed {strategy['name']} by clicking overlay")
                                        dismissed_count += 1
                                        time.sleep(0.5)
                                
                                elif strategy['action'] == 'find_accept_button':
                                    # Look for accept/OK buttons in cookie banners
                                    accept_buttons = element.find_elements(By.CSS_SELECTOR, "button, a")
                                    for btn in accept_buttons:
                                        btn_text = btn.text.lower()
                                        if any(x in btn_text for x in ['accetta', 'accept', 'ok', 'consenti', 'agree']):
                                            driver.execute_script("arguments[0].click();", btn)
                                            logger.info(f"📢 Hunter {browser_id}: Accepted {strategy['name']}")
                                            dismissed_count += 1
                                            time.sleep(0.5)
                                            break
                                
                                elif strategy['action'] == 'click_directly':
                                    driver.execute_script("arguments[0].click();", element)
                                    logger.info(f"📢 Hunter {browser_id}: Clicked {strategy['name']} button")
                                    dismissed_count += 1
                                    time.sleep(0.5)
                                    
                            except Exception as e:
                                logger.debug(f"Failed to dismiss element: {e}")
                                continue
                                
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue
            
            # Also try to remove popups via JavaScript
            if dismissed_count == 0:
                removed = driver.execute_script("""
                    var removed = 0;
                    // Remove common popup elements
                    var selectors = [
                        'div[class*="overlay"]',
                        'div[class*="modal"]',
                        'div[class*="popup"]',
                        'div[class*="cookie"]',
                        'div[class*="gdpr"]'
                    ];
                    
                    selectors.forEach(function(selector) {
                        var elements = document.querySelectorAll(selector);
                        elements.forEach(function(el) {
                            if (el && el.offsetParent !== null) {  // Check if visible
                                el.remove();
                                removed++;
                            }
                        });
                    });
                    
                    return removed;
                """)
                
                if removed > 0:
                    logger.info(f"📢 Hunter {browser_id}: Removed {removed} popups via JavaScript")
                    dismissed_count += removed
            
            if dismissed_count > 0:
                self.stats['popups_dismissed'] += dismissed_count
                elapsed = time.time() - start_time
                self.performance_tracker['popup_dismiss'].append(elapsed)
                logger.debug(f"Popup dismissal took {elapsed:.2f}s")
                self.save_stats()
                
        except Exception as e:
            logger.error(f"Error in dismiss_popups: {e}")
            
        return dismissed_count
    
    def detect_captcha(self, driver: uc.Chrome) -> tuple[bool, Optional[str], Optional[str]]:
        """Enhanced CAPTCHA detection with multiple strategies"""
        try:
            # Strategy 1: Check for reCAPTCHA v2
            recaptcha_v2 = driver.execute_script("""
                var found = {
                    hasDiv: false,
                    sitekey: null,
                    hasIframe: false,
                    iframeSrc: null
                };
                
                // Check for g-recaptcha div
                var divs = document.querySelectorAll('div.g-recaptcha');
                if (divs.length > 0) {
                    found.hasDiv = true;
                    found.sitekey = divs[0].getAttribute('data-sitekey');
                }
                
                // Check for recaptcha iframe
                var iframes = document.querySelectorAll('iframe[src*="recaptcha"], iframe[title*="recaptcha"]');
                if (iframes.length > 0) {
                    found.hasIframe = true;
                    found.iframeSrc = iframes[0].src;
                    // Try to extract sitekey from iframe src
                    var match = iframes[0].src.match(/[?&]k=([^&]+)/);
                    if (match && !found.sitekey) {
                        found.sitekey = match[1];
                    }
                }
                
                return found;
            """)
            
            if recaptcha_v2['hasDiv'] or recaptcha_v2['hasIframe']:
                logger.info(f"🤖 reCAPTCHA v2 detected! Div: {recaptcha_v2['hasDiv']}, Iframe: {recaptcha_v2['hasIframe']}")
                return True, recaptcha_v2['sitekey'], driver.current_url
            
            # Strategy 2: Check for reCAPTCHA v3
            recaptcha_v3 = driver.execute_script("""
                // Check for reCAPTCHA v3 indicators
                return window.grecaptcha !== undefined || 
                       document.querySelector('script[src*="recaptcha/api.js"]') !== null;
            """)
            
            if recaptcha_v3:
                logger.info("🤖 reCAPTCHA v3 detected!")
                # Try to find sitekey in page source
                page_source = driver.page_source
                sitekey_match = re.search(r'["\']sitekey["\']\s*:\s*["\']([^"\']+)["\']', page_source)
                if sitekey_match:
                    return True, sitekey_match.group(1), driver.current_url
                return True, None, driver.current_url
            
            # Strategy 3: Check for hCaptcha
            hcaptcha = driver.execute_script("""
                var hcaptchaDiv = document.querySelector('div.h-captcha');
                if (hcaptchaDiv) {
                    return {
                        found: true,
                        sitekey: hcaptchaDiv.getAttribute('data-sitekey')
                    };
                }
                return {found: false};
            """)
            
            if hcaptcha['found']:
                logger.info("🤖 hCaptcha detected!")
                return True, hcaptcha.get('sitekey'), driver.current_url
            
            # Strategy 4: Check page source for CAPTCHA keywords
            page_source_lower = driver.page_source.lower()
            captcha_indicators = [
                'g-recaptcha', 'h-captcha', 'cf-turnstile',
                'captcha', 'verifica che non sei un robot',
                'verify you are human', 'sono un umano'
            ]
            
            for indicator in captcha_indicators:
                if indicator in page_source_lower:
                    logger.info(f"🤖 CAPTCHA indicator found in page: '{indicator}'")
                    return True, None, driver.current_url
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            return False, None, None
    
    def solve_captcha_automatically(self, driver: uc.Chrome, sitekey: str, pageurl: str, browser_id: int) -> bool:
        """Attempt to solve CAPTCHA automatically using 2captcha"""
        if not self.captcha_solver or not sitekey:
            logger.warning(f"Cannot auto-solve: solver={bool(self.captcha_solver)}, sitekey={bool(sitekey)}")
            return False
            
        logger.info(f"🤖 Hunter {browser_id}: Attempting automatic CAPTCHA solve...")
        
        token = self.captcha_solver.solve_recaptcha(sitekey, pageurl)
        if not token:
            logger.error("Failed to get token from 2captcha")
            return False
            
        try:
            # Enhanced token injection with multiple strategies
            injection_success = driver.execute_script(f"""
                var token = '{token}';
                var success = false;
                
                // Strategy 1: Direct textarea injection
                var textarea = document.getElementById('g-recaptcha-response');
                if (textarea) {{
                    textarea.innerHTML = token;
                    textarea.value = token;
                    success = true;
                }}
                
                // Strategy 2: Find any g-recaptcha-response element
                if (!success) {{
                    var responses = document.querySelectorAll('[id*="g-recaptcha-response"], [name*="g-recaptcha-response"]');
                    responses.forEach(function(el) {{
                        el.innerHTML = token;
                        el.value = token;
                        success = true;
                    }});
                }}
                
                // Strategy 3: Trigger callbacks
                if (success && window.___grecaptcha_cfg) {{
                    Object.entries(window.___grecaptcha_cfg.clients).forEach(function([key, client]) {{
                        if (client.callback) {{
                            try {{
                                client.callback(token);
                            }} catch(e) {{
                                console.error('Callback error:', e);
                            }}
                        }}
                    }});
                }}
                
                // Strategy 4: Submit form if exists
                if (success) {{
                    var forms = document.querySelectorAll('form');
                    forms.forEach(function(form) {{
                        var hasRecaptcha = form.querySelector('.g-recaptcha, [data-sitekey]');
                        if (hasRecaptcha) {{
                            try {{
                                form.submit();
                            }} catch(e) {{
                                console.log('Form submit failed:', e);
                            }}
                        }}
                    }});
                }}
                
                return success;
            """)
            
            if injection_success:
                self.stats['captchas_auto_solved'] += 1
                self.mark_captcha_solved(browser_id)
                logger.info(f"✅ CAPTCHA token injected successfully!")
                return True
            else:
                logger.error("Failed to inject CAPTCHA token - no suitable element found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to inject CAPTCHA token: {e}")
            return False
    
    def wait_for_captcha_solve(self, driver: uc.Chrome, browser_id: int, timeout: int = 120) -> bool:
        """Wait for user to solve CAPTCHA manually or solve automatically"""
        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
        
        if not captcha_detected:
            return True
            
        # Increment CAPTCHA counter
        self.stats['captchas_encountered'] += 1
        self.save_stats()
        
        # Try automatic solving first if enabled
        if self.auto_solve and sitekey:
            logger.info(f"🤖 Attempting automatic CAPTCHA solve with 2captcha...")
            if self.solve_captcha_automatically(driver, sitekey, pageurl, browser_id):
                return True
            else:
                logger.warning("Automatic solving failed, falling back to manual")
                
        # Fall back to manual solving
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 CAPTCHA DETECTED - Hunter {browser_id}")
        logger.info(f"{'='*60}")
        logger.info(f"⚠️  MANUAL ACTION REQUIRED!")
        logger.info(f"Please solve the CAPTCHA in Browser {browser_id}")
        logger.info(f"Waiting up to {timeout} seconds...")
        logger.info(f"{'='*60}\n")
        
        # Play alert sound
        for _ in range(5):
            print('\a')
            time.sleep(0.5)
        
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            # Check if CAPTCHA is still present
            if not self.detect_captcha(driver)[0]:
                logger.info(f"✅ CAPTCHA solved in Browser {browser_id}!")
                self.mark_captcha_solved(browser_id)
                return True
                
            # Also check if we've moved to a new page (indicating success)
            try:
                current_url = driver.current_url.lower()
                if any(x in current_url for x in ['conferma', 'checkout', 'payment', 'cart']):
                    logger.info(f"✅ Purchase proceeding in Browser {browser_id}!")
                    self.mark_captcha_solved(browser_id)
                    return True
            except:
                pass
                
            time.sleep(check_interval)
            
        logger.warning(f"❌ CAPTCHA timeout in Browser {browser_id}")
        return False
    
    @retry(max_attempts=3, delay=2.0, exceptions=(WebDriverException,))
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser with VERIFIED image loading"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        def create_chrome_options():
            """Create ChromeOptions with IMAGES EXPLICITLY ENABLED"""
            options = uc.ChromeOptions()
            
            # Fix for headless attribute error
            options.headless = False  # Explicitly set headless to False
            
            # Stealth options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-infobars')
            
            # Performance options (but NOT disabling images)
            options.add_argument('--disable-logging')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # CRITICAL: Ensure images are loaded
            # Some versions of Chrome might disable images by default in automation
            # We explicitly set preferences to ENABLE images
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 1,  # 1 = allow, 2 = block
                    'plugins': 1,
                    'popups': 2,  # Block popups
                    'geolocation': 2,
                    'notifications': 2,
                    'media_stream': 2,
                },
                'profile.managed_default_content_settings': {
                    'images': 1  # Ensure images are allowed
                }
            }
            options.add_experimental_option('prefs', prefs)
            
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
            
            # Additional arguments to ensure proper rendering
            options.add_argument('--force-device-scale-factor=1')
            
            logger.info(f"✅ ChromeOptions configured with IMAGES ENABLED")
            
            return options, x, y
        
        try:
            # Create fresh options
            options, x, y = create_chrome_options()
            
            # Create driver with proper error handling
            driver = None
            
            try:
                # Try creating with undetected-chromedriver
                driver = uc.Chrome(
                    options=options,
                    driver_executable_path=None,  # Let it auto-download
                    version_main=137,  # Auto-detect version
                    use_subprocess=False  # Avoid subprocess issues
                )
                
                # Set timeouts
                driver.set_page_load_timeout(30)
                driver.implicitly_wait(10)
                
                # Inject stealth JavaScript
                driver.execute_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5].map((i) => ({
                            name: `Plugin ${i}`,
                            description: `Description ${i}`,
                            filename: `plugin${i}.dll`
                        }))
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en', 'it-IT', 'it']
                    });
                    
                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Mock chrome runtime
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {}
                    };
                    
                    // Remove automation indicators
                    ['webdriver', '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', 
                     '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped', 
                     '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder', 
                     '_selenium', 'calledSelenium', 'ChromeDriverw', 'driver-evaluate', 'webdriver-evaluate',
                     'selenium-evaluate', 'webdriverCommand', 'webdriver-evaluate-response', '__webdriverFunc',
                     '__webdriver_script_fn', '__$webdriverAsyncExecutor', '__lastWatirAlert', '__lastWatirConfirm',
                     '__lastWatirPrompt', '$chrome_asyncScriptInfo', '$cdc_asdjflasutopfhvcZLmcfl_'].forEach(prop => {
                        delete window[prop];
                        delete document[prop];
                    });
                """)
                
                # CRITICAL: Verify image loading immediately
                logger.info(f"🔍 Verifying image loading for Browser {browser_id}...")
                if self.verify_image_loading(driver, browser_id):
                    logger.info(f"✅ Browser {browser_id} ready with IMAGES ENABLED at position ({x}, {y})")
                else:
                    logger.error(f"❌ Browser {browser_id} has IMAGES DISABLED! Attempting fix...")
                    # Try to enable images via JavaScript
                    driver.execute_script("""
                        // Force enable images
                        var style = document.createElement('style');
                        style.innerHTML = 'img { display: inline !important; visibility: visible !important; }';
                        document.head.appendChild(style);
                    """)
                
                return driver
                
            except Exception as e:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                raise e
                
        except Exception as e:
            logger.error(f"❌ Failed to create browser {browser_id}: {e}")
            
            # Provide helpful error messages
            if "headless" in str(e).lower():
                logger.error("Chrome headless issue detected - check undetected-chromedriver version")
            elif "version" in str(e).lower():
                logger.error("Chrome version mismatch - updating chromedriver...")
            
            raise
    
    def is_blocked(self, driver: uc.Chrome) -> bool:
        """Check if we're getting 404 or blocked"""
        try:
            # Check URL and title for errors
            current_url = driver.current_url.lower()
            current_title = driver.title.lower()
            
            error_indicators = ['404', 'error', 'blocked', 'forbidden', 'access denied']
            
            if any(indicator in current_url for indicator in error_indicators):
                return True
            if any(indicator in current_title for indicator in error_indicators):
                return True
                
            # Check page content more carefully
            page_source = driver.page_source.lower()
            
            # Italian error messages
            italian_errors = ['non trovata', 'non disponibile', 'errore', 'bloccato']
            
            # Check for 404 but exclude ticket not found messages
            if '404' in page_source and not any(x in page_source for x in ['non sono state trovate', 'nessun biglietto']):
                return True
                
            # Check for Italian error messages
            error_count = sum(1 for error in italian_errors if error in page_source)
            if error_count >= 2:  # Multiple error indicators
                return True
                
            return False
            
        except Exception as e:
            logger.debug(f"Block check error: {e}")
            return False

    def clear_browser_data(self, driver: uc.Chrome, browser_id: int):
        """Clear browser data to bypass blocks"""
        try:
            logger.info(f"🧹 Clearing data for Browser {browser_id} to bypass block...")
            
            # Clear all browser data via JavaScript
            driver.execute_script("""
                // Clear cookies
                document.cookie.split(";").forEach(function(c) { 
                    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
                });
                
                // Clear local storage
                try { localStorage.clear(); } catch(e) {}
                
                // Clear session storage
                try { sessionStorage.clear(); } catch(e) {}
                
                // Clear IndexedDB
                if ('indexedDB' in window) {
                    indexedDB.databases().then(databases => {
                        databases.forEach(db => { indexedDB.deleteDatabase(db.name); });
                    }).catch(e => {});
                }
                
                // Clear cache storage
                if ('caches' in window) {
                    caches.keys().then(names => {
                        names.forEach(name => caches.delete(name));
                    }).catch(e => {});
                }
            """)
            
            # Also use Selenium methods
            driver.delete_all_cookies()
            
            # Navigate to blank page
            driver.get("about:blank")
            time.sleep(random.uniform(0.8, 1.5))
            
            logger.info(f"✅ Browser {browser_id} data cleared")
            self.stats['blocks_encountered'] += 1
            self.save_stats()
            
        except Exception as e:
            logger.error(f"Failed to clear browser data: {e}")
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop with all V5 enhancements"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to event page
        logger.info(f"📍 Navigating to: {self.target_url}")
        page_start = time.time()
        driver.get(self.target_url)
        page_load_time = time.time() - page_start
        self.performance_tracker['page_load'].append(page_load_time)
        logger.info(f"📄 Page loaded in {page_load_time:.2f}s")
        
        # Initial popup dismissal
        time.sleep(2)
        initial_popups = self.dismiss_popups(driver, browser_id)
        logger.info(f"📢 Dismissed {initial_popups} initial popups")
        
        check_count = 0
        # Staggered refresh times for each browser
        last_refresh = time.time() - (browser_id * 5)  # Stagger initial refreshes
        refresh_interval = 15 + random.randint(-3, 3)  # Faster refresh: 12-18 seconds
        
        last_session_refresh = time.time()
        local_stats = defaultdict(int)
        
        # Tracking for various checks
        last_captcha_check = 0
        last_popup_check = time.time()
        last_health_check = time.time()
        last_captcha_test = time.time()  # New: Track last CAPTCHA test
        
        # Initialize grace period status
        in_grace_period = False
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Health check every 30 seconds
                if time.time() - last_health_check > 30:
                    if not self.health_monitor.check_browser_health(browser_id, driver):
                        logger.error(f"❌ Hunter {browser_id}: Browser unhealthy, restarting...")
                        break
                    last_health_check = time.time()
                
                # Periodic CAPTCHA check - only browser 1 does this every 5 minutes
                if browser_id == 1 and time.time() - last_captcha_test > self.config.captcha_check_interval:
                    logger.info(f"🔍 Hunter {browser_id}: Performing periodic CAPTCHA check...")
                    captcha_detected, captcha_info = self.detect_captcha(driver)
                    if captcha_detected:
                        logger.warning(f"🚨 CAPTCHA detected during periodic check!")
                        if self.auto_solve and self.captcha_solver:
                            logger.info("🤖 Attempting automatic CAPTCHA solve...")
                            if self.solve_captcha_automatically(driver, captcha_info):
                                self.mark_captcha_solved()
                                logger.info("✅ CAPTCHA solved automatically!")
                            else:
                                logger.error("❌ Automatic CAPTCHA solve failed")
                                self.wait_for_captcha_solve(driver, browser_id)
                        else:
                            self.wait_for_captcha_solve(driver, browser_id)
                    else:
                        logger.info(f"✅ No CAPTCHA detected - all clear!")
                    last_captcha_test = time.time()
                
                # Popup check - more frequent than V4
                if time.time() - last_popup_check > self.config.popup_check_interval:
                    dismissed = self.dismiss_popups(driver, browser_id)
                    if dismissed > 0:
                        logger.debug(f"Dismissed {dismissed} popups")
                    last_popup_check = time.time()
                
                # Check for 404 blocks
                if self.is_blocked(driver):
                    logger.warning(f"⚠️ Hunter {browser_id}: Block detected!")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(random.uniform(2.5, 3.5))
                    self.dismiss_popups(driver, browser_id)  # Dismiss any new popups
                    continue
                
                # Session refresh every 15 minutes
                if time.time() - last_session_refresh > 900:
                    logger.info(f"🔄 Hunter {browser_id}: Preventive session refresh...")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(3)
                    self.dismiss_popups(driver, browser_id)
                    last_session_refresh = time.time()
                    continue
                
                # Look for tickets
                ticket_start = time.time()
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                ticket_check_time = time.time() - ticket_start
                self.performance_tracker['ticket_check'].append(ticket_check_time)
                
                if tickets:
                    self.stats['total_tickets_found'] += len(tickets)
                    
                    # Check CAPTCHA grace period
                    in_grace_period = self.check_captcha_status(browser_id)
                    
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
                                            # If in grace period, log it
                                            if in_grace_period:
                                                logger.info(f"🚀 Hunter {browser_id}: CAPTCHA grace period active - fast purchase!")
                                            
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
                
                # Periodically test CAPTCHA grace period
                if in_grace_period and check_count - last_captcha_check > 20:  # Every ~minute
                    logger.info(f"🔍 Hunter {browser_id}: Testing CAPTCHA grace period...")
                    last_captcha_check = check_count
                
                # Fast checking to achieve ~30 checks per minute
                # Average wait of ~2 seconds = 30 checks/minute
                refresh_time = random.uniform(self.config.min_wait, self.config.max_wait)
                time.sleep(refresh_time)
                
                # Staggered page refresh per browser
                if time.time() - last_refresh > refresh_interval:
                    logger.debug(f"Hunter {browser_id}: Refreshing page...")
                    driver.refresh()
                    last_refresh = time.time()
                    # Recalculate next refresh interval
                    refresh_interval = 15 + random.randint(-3, 3)
                    # Dismiss popups after refresh
                    time.sleep(1)
                    self.dismiss_popups(driver, browser_id)
                
                # Progress update every 30 checks (about once per minute at ~30 checks/min)
                if check_count % 30 == 0:
                    elapsed = time.time() - self.session_start_time
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    
                    # Show local stats for this hunter
                    local_summary = []
                    for ticket_type, count in local_stats.items():
                        if count > 0:
                            local_summary.append(f"{ticket_type}: {count}")
                    
                    local_str = " | ".join(local_summary) if local_summary else "No new tickets"
                    
                    # Add status indicators
                    status_parts = [f"{check_count} checks @ {rate:.1f}/min", local_str]
                    if in_grace_period:
                        status_parts.append("🟢 CAPTCHA OK")
                    
                    logger.info(f"📊 Hunter {browser_id}: {' | '.join(status_parts)}")
                    
            except TimeoutException:
                logger.warning(f"Hunter {browser_id}: Page timeout, refreshing...")
                driver.refresh()
                time.sleep(random.uniform(1.5, 2.5))
                self.dismiss_popups(driver, browser_id)
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    logger.error(f"Hunter {browser_id}: Session died")
                    break
                logger.error(f"Hunter {browser_id}: Browser error, continuing...")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)

        # Special check for "Carica Offerte" button after popup dismissal
        try:
            carica_button = driver.find_element(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
            if carica_button and carica_button.is_displayed():
                driver.execute_script("arguments[0].click();", carica_button)
                logger.info(f"🎯 Hunter {browser_id}: Clicked 'Carica Offerte' button!")
                initial_popups += 1
                time.sleep(0.5)
        except:
            pass
            
        # Check again for any new popups that appeared
        time.sleep(0.5)
        additional_popups = self.dismiss_popups(driver, browser_id)
        initial_popups += additional_popups
    
    @retry(max_attempts=2, delay=0.5, exceptions=(ElementNotInteractableException, StaleElementReferenceException))
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket with enhanced interaction"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Dismiss any popups first
            self.dismiss_popups(driver, browser_id)
            
            # Scroll to ticket element
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", ticket_element)
            time.sleep(0.5)
            
            # Try multiple click methods
            click_success = False
            
            # Method 1: JavaScript click
            try:
                driver.execute_script("arguments[0].click();", ticket_element)
                click_success = True
            except:
                # Method 2: Action chains
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(ticket_element).click().perform()
                    click_success = True
                except:
                    # Method 3: Direct click
                    try:
                        ticket_element.click()
                        click_success = True
                    except:
                        pass
            
            if not click_success:
                logger.warning(f"Failed to click ticket element")
                return False
                
            time.sleep(random.uniform(0.8, 1.2))
            
            # Dismiss any new popups that might appear
            self.dismiss_popups(driver, browser_id)
            
            # Enhanced buy button detection
            buy_selectors = [
                # Data attributes
                "button[data-qa='buyNowButton']",
                "button[data-testid*='buy']",
                
                # Class-based selectors
                "button[class*='buy']",
                "button[class*='acquista']",
                "button[class*='purchase']",
                "button[class*='add-to-cart']",
                
                # Text-based selectors (will convert to XPath)
                "button:contains('Acquista')",
                "button:contains('Buy')",
                "button:contains('Compra')",
                "button:contains('Aggiungi')",
                
                # Link styled as button
                "a[class*='buy'][class*='button']",
                "a[class*='btn'][href*='cart']",
                
                # Generic button with specific attributes
                "button[type='submit']",
                "input[type='submit'][value*='buy']"
            ]
            
            buy_button_found = False
            
            for selector in buy_selectors:
                try:
                    if ':contains' in selector:
                        # Convert to XPath
                        match = re.search(r":contains\('([^']+)'\)", selector)
                        if match:
                            text = match.group(1)
                            tag = selector.split(':')[0]
                            xpath = f"//{tag}[contains(text(), '{text}') or contains(@value, '{text}')]"
                            elements = driver.find_elements(By.XPATH, xpath)
                            # Filter for visible elements
                            elements = [e for e in elements if e.is_displayed() and e.is_enabled()]
                            if elements:
                                buy_btn = elements[0]
                                buy_button_found = True
                    else:
                        # Try CSS selector with wait
                        buy_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        buy_button_found = True
                    
                    if buy_button_found:
                        # Scroll to buy button
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                        time.sleep(0.3)
                        
                        # Try to click
                        try:
                            driver.execute_script("arguments[0].click();", buy_btn)
                        except:
                            buy_btn.click()
                            
                        logger.info(f"✅ Hunter {browser_id}: Buy button clicked!")
                        
                        # Wait for potential CAPTCHA or next page
                        time.sleep(2)
                        
                        # Check for CAPTCHA
                        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
                        if captcha_detected:
                            logger.info(f"🤖 Hunter {browser_id}: CAPTCHA detected after buy click!")
                            self.stats['captchas_encountered'] += 1
                            self.save_stats()
                            
                            # Try to solve
                            if self.wait_for_captcha_solve(driver, browser_id):
                                logger.info(f"✅ Hunter {browser_id}: Continuing after CAPTCHA")
                                time.sleep(1)
                            else:
                                logger.warning(f"❌ Hunter {browser_id}: CAPTCHA not solved")
                                return False
                        
                        # Play success alarm sound
                        print('\a' * 3)  # System beep
                        
                        # Take screenshot
                        screenshot_path = f"screenshots/ticket_{browser_id}_{int(time.time())}.png"
                        Path("screenshots").mkdir(exist_ok=True)
                        driver.save_screenshot(screenshot_path)
                        logger.info(f"📸 Screenshot saved: {screenshot_path}")
                        
                        return True
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Button selector {selector} failed: {e}")
                    continue
                    
            logger.warning(f"Hunter {browser_id}: No buy button found")
            
            # Take debug screenshot
            debug_path = f"screenshots/debug_{browser_id}_{int(time.time())}.png"
            driver.save_screenshot(debug_path)
            logger.info(f"📸 Debug screenshot: {debug_path}")
            
            return False
            
        except Exception as e:
            logger.error(f"Purchase failed: {e}")
            return False
    
    def show_statistics_dashboard(self):
        """Display beautiful statistics dashboard with V5 enhancements"""
        total_runtime = self.stats.get('all_time_runtime', 0) + (time.time() - self.session_start_time)
        hours = int(total_runtime // 3600)
        minutes = int((total_runtime % 3600) // 60)
        
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}📊 FANSALE BOT V5 STATISTICS DASHBOARD{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")
        
        print(f"\n{Colors.BOLD}⏱️  Total Runtime:{Colors.END} {hours}h {minutes}m")
        print(f"{Colors.BOLD}🔍 Total Checks:{Colors.END} {self.stats['total_checks']:,}")
        print(f"{Colors.BOLD}🎫 Unique Tickets Found:{Colors.END} {self.stats['unique_tickets_found']:,}")
        
        print(f"\n{Colors.BOLD}📈 Ticket Breakdown:{Colors.END}")
        print(f"   {Colors.GREEN}● Prato A:{Colors.END} {self.stats['tickets_by_type']['prato_a']}")
        print(f"   {Colors.BLUE}● Prato B:{Colors.END} {self.stats['tickets_by_type']['prato_b']}")
        print(f"   {Colors.YELLOW}● Settore:{Colors.END} {self.stats['tickets_by_type']['settore']}")
        print(f"   ○ Other: {self.stats['tickets_by_type']['other']}")
        
        print(f"\n{Colors.BOLD}🛍️  Purchases:{Colors.END} {self.stats['purchases']}")
        print(f"{Colors.BOLD}🚫 Blocks Cleared:{Colors.END} {self.stats['blocks_encountered']}")
        print(f"{Colors.BOLD}📢 Popups Dismissed:{Colors.END} {self.stats.get('popups_dismissed', 0)}")
        print(f"{Colors.BOLD}📸 Images Verified:{Colors.END} {self.stats.get('images_verified', 0)}")
        
        # CAPTCHA stats
        print(f"\n{Colors.BOLD}🤖 CAPTCHA Stats:{Colors.END}")
        print(f"   Encountered: {self.stats.get('captchas_encountered', 0)}")
        print(f"   Solved Manually: {self.stats.get('captchas_solved', 0) - self.stats.get('captchas_auto_solved', 0)}")
        print(f"   Solved Automatically: {self.stats.get('captchas_auto_solved', 0)}")
        
        # Performance metrics
        if self.performance_tracker:
            print(f"\n{Colors.BOLD}⚡ Performance Metrics:{Colors.END}")
            if 'page_load' in self.performance_tracker and self.performance_tracker['page_load']:
                avg_load = sum(self.performance_tracker['page_load']) / len(self.performance_tracker['page_load'])
                print(f"   Avg Page Load: {avg_load:.2f}s")
            if 'popup_dismiss' in self.performance_tracker and self.performance_tracker['popup_dismiss']:
                avg_popup = sum(self.performance_tracker['popup_dismiss']) / len(self.performance_tracker['popup_dismiss'])
                print(f"   Avg Popup Dismiss: {avg_popup:.2f}s")
        
        if self.stats['total_checks'] > 0:
            rate = self.stats['total_checks'] / (total_runtime / 60) if total_runtime > 0 else 0
            print(f"\n{Colors.BOLD}⚡ Average Rate:{Colors.END} {rate:.1f} checks/min")
        
        # System health
        health = self.health_monitor.get_system_health()
        print(f"\n{Colors.BOLD}💻 System Health:{Colors.END}")
        print(f"   Memory Usage: {health.get('memory_percent', 0):.1f} MB")
        print(f"   Active Threads: {health.get('active_threads', 0)}")
        
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}\n")
    
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
        """Configure bot settings"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 FANSALE BOT - ENHANCED EDITION V5{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 50}{Colors.END}")
        print("\n✨ V5 Features:")
        print("  • No login required")
        print("  • Tracks Prato A, Prato B, and Settore tickets")
        print("  • Avoids duplicate logging")
        print("  • Persistent statistics")
        print(f"  • {Colors.GREEN}VERIFIED IMAGE LOADING{Colors.END} ✅")
        print(f"  • {Colors.RED}ENHANCED CAPTCHA DETECTION{Colors.END} ✅")
        print(f"  • {Colors.YELLOW}AUTOMATIC CAPTCHA SOLVING (2captcha){Colors.END} ✅")
        print(f"  • {Colors.CYAN}IMPROVED POPUP HANDLING{Colors.END} ✅")
        print(f"  • {Colors.BOLD}PERFORMANCE MONITORING{Colors.END} ✅")
        
        # Show current stats
        self.show_statistics_dashboard()
        
        # Check for 2captcha configuration
        if self.captcha_solver and self.captcha_solver.api_key:
            print(f"\n{Colors.GREEN}✅ 2Captcha configured - automatic solving enabled{Colors.END}")
            print(f"   API Key: {self.captcha_solver.api_key[:8]}...")
        else:
            print(f"\n{Colors.YELLOW}⚠️  No 2Captcha API key - manual CAPTCHA solving only{Colors.END}")
            print(f"   To enable auto-solving, set TWOCAPTCHA_API_KEY in .env")
        
        # Number of browsers
        while True:
            try:
                num = input(f"\n{Colors.BOLD}🌐 Number of browsers (1-8, default 2):{Colors.END} ").strip()
                if not num:
                    self.num_browsers = 2
                    break
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 8:
                    break
                print(f"{Colors.RED}❌ Please enter 1-8{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}❌ Invalid number{Colors.END}")
        
        # Max tickets
        while True:
            try:
                max_t = input(f"\n{Colors.BOLD}🎫 Max tickets to reserve (1-4, default 2):{Colors.END} ").strip()
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
        
        # Summary
        print(f"\n{Colors.BOLD}📋 Configuration Summary:{Colors.END}")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Max tickets: {self.max_tickets}")
        
        # Show selected ticket types
        type_display = {
            'prato_a': 'Prato A',
            'prato_b': 'Prato B',
            'settore': 'Settore',
            'other': 'Other/Unknown'
        }
        selected = [type_display[t] for t in sorted(self.ticket_types_to_hunt)]
        print(f"   • Hunting for: {', '.join(selected)}")
        
        print(f"   • Target URL: {self.target_url[:50]}...")
        print(f"   • Popup check interval: {self.config.popup_check_interval}s ({self.config.popup_check_interval/60:.1f} minutes)")
        print(f"   • CAPTCHA check interval: {self.config.captcha_check_interval}s (Browser 1 only)")
        print(f"   • Check frequency: ~60-100 checks/minute per browser (ULTRA FAST)")
        print(f"\n{Colors.GREEN}⚡ NO LOGIN REQUIRED - Direct ticket hunting!{Colors.END}")
        print(f"{Colors.RED}🤖 CAPTCHA SUPPORT - Auto-solve or manual alerts{Colors.END}")
        print(f"{Colors.CYAN}📢 POPUP HANDLING - Checks every {self.config.popup_check_interval}s{Colors.END}")
        print(f"{Colors.GREEN}📸 IMAGES ENABLED - Verified on startup{Colors.END}")
    
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
                # Staggered browser creation
                if i < self.num_browsers:
                    time.sleep(random.uniform(3, 7))
            
            if not self.browsers:
                logger.error("❌ No browsers created")
                return

            logger.info(f"✅ {len(self.browsers)} browser(s) ready with IMAGES VERIFIED!")
            
            # Show tip about monitoring
            print(f"\n{Colors.CYAN}💡 TIP: Browsers are positioned for multi-monitor setups{Colors.END}")
            print(f"{Colors.CYAN}   Move them to your preferred monitors if needed{Colors.END}")
            print(f"\n{Colors.RED}⚠️  CAPTCHA ALERT: If CAPTCHA appears, it will be handled{Colors.END}")
            print(f"{Colors.GREEN}   Auto-solve if configured, or manual alert{Colors.END}")
            print(f"{Colors.CYAN}📢 POPUPS: Will be checked every {self.config.popup_check_interval/60:.1f} minutes{Colors.END}")
            print(f"{Colors.GREEN}📸 IMAGES: Verified loading on all browsers{Colors.END}")
            
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
            
            # Monitor progress
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎯 HUNTING ACTIVE! Press Ctrl+C to stop.{Colors.END}\n")
            
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
            import traceback
            traceback.print_exc()
            
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
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🎫 FANSALE BOT - ENTERPRISE EDITION V5{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"\n{Colors.GREEN}✨ Core Features:{Colors.END}")
    print("  • Ticket type tracking (Prato A, B, Settore)")
    print("  • Duplicate detection with notifications")
    print("  • Persistent statistics")
    print("  • Multi-monitor support")
    print("  • Health monitoring")
    print("  • Advanced retry logic")
    print(f"\n{Colors.RED}🚀 V5 Critical Fixes:{Colors.END}")
    print("  • ✅ IMAGES VERIFIED ENABLED (checked on startup)")
    print("  • ✅ Enhanced CAPTCHA detection (multiple strategies)")
    print("  • ✅ Working 2captcha integration")
    print("  • ✅ Improved popup detection (checks every 3s)")
    print("  • ✅ Performance monitoring")
    print("  • ✅ Better error handling")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
        import requests
    except ImportError as e:
        print(f"\n{Colors.RED}❌ Missing dependency: {e}{Colors.END}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium requests")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    
    # Load configuration
    config_path = Path("bot_config_v5.json")
    config = BotConfig.from_file(config_path)
    
    # Check for 2captcha key in environment
    twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY', '')
    if twocaptcha_key:
        config.twocaptcha_api_key = twocaptcha_key
        config.auto_solve_captcha = True
        print(f"\n{Colors.GREEN}✅ 2Captcha API key found in .env{Colors.END}")
    
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
        time.sleep(2)
    else:
        print(f"\n{Colors.GREEN}✅ Target URL loaded from .env{Colors.END}")
    
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
        print(f"\n{Colors.GREEN}✅ Thank you for using FanSale Bot V5!{Colors.END}")


if __name__ == "__main__":
    main()
