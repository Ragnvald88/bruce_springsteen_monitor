#!/usr/bin/env python3
"""
FanSale Bot - Enhanced No Login Edition V4
Features:
- No login required
- Ticket type categorization (Prato A, Prato B, Settore)
- Duplicate detection to avoid re-logging same tickets
- Persistent statistics across restarts
- Beautiful terminal logging with ticket details
- V4 Improvements: Auto CAPTCHA solving, popup handling, images VERIFIED enabled
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
from selenium.common.exceptions import TimeoutException, WebDriverException, ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException
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
    captcha_grace_period: int = 300  # 5 minutes after solving CAPTCHA
    twocaptcha_api_key: str = ""  # Optional: for automatic solving
    auto_solve_captcha: bool = False
    
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

# 2Captcha solver class
class TwoCaptchaSolver:
    """Handles automatic CAPTCHA solving via 2captcha service"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        
    def solve_recaptcha(self, sitekey: str, pageurl: str, timeout: int = 180) -> Optional[str]:
        """Solve reCAPTCHA and return token"""
        if not self.api_key:
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
            response = requests.post(submit_url, data=submit_data, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"2captcha submission failed: {result}")
                return None
                
            captcha_id = result.get('request')
            logger.info(f"✅ CAPTCHA submitted, ID: {captcha_id}")
            
            # Wait for solution
            result_url = f"{self.base_url}/res.php"
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                time.sleep(5)
                
                result_data = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = requests.get(result_url, params=result_data, timeout=30)
                result = response.json()
                
                if result.get('status') == 1:
                    token = result.get('request')
                    logger.info("✅ CAPTCHA solved automatically!")
                    return token
                elif result.get('request') != 'CAPCHA_NOT_READY':
                    logger.error(f"2captcha error: {result}")
                    return None
                    
            logger.error("2captcha timeout")
            return None
            
        except Exception as e:
            logger.error(f"2captcha error: {e}")
            return None

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
            elif 'CAPTCHA' in record.msg:
                record.msg = f"{Colors.RED}{Colors.BOLD}{record.msg}{Colors.END}"
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
        
        # CAPTCHA tracking - per browser
        self.captcha_solved_time = {}  # browser_id -> timestamp when CAPTCHA was solved
        self.captcha_grace_period = self.config.captcha_grace_period  # 5 minutes default
        
        # Load persistent statistics using thread-safe manager
        self.stats_file = Path("fansale_stats.json")
        self.stats_manager = StatsManager(self.stats_file)
        self.stats = self.stats_manager.stats
        
        # Performance monitoring
        self.session_start_time = time.time()
        
        # Health monitoring and notifications
        self.health_monitor = HealthMonitor()
        self.notification_manager = NotificationManager(enabled=True)
        
        # 2Captcha solver
        api_key = self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY', '')
        self.captcha_solver = TwoCaptchaSolver(api_key) if api_key else None
        self.auto_solve = self.config.auto_solve_captcha and self.captcha_solver is not None


    def save_stats(self):
        """Save statistics to file"""
        try:
            # Update runtime
            session_time = time.time() - self.session_start_time
            self.stats['all_time_runtime'] += session_time
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
                logger.info(f"✅ Hunter {browser_id}: CAPTCHA grace period active ({remaining:.0f}s remaining)")
                return True
        return False
    
    def mark_captcha_solved(self, browser_id: int):
        """Mark CAPTCHA as solved for this browser"""
        self.captcha_solved_time[browser_id] = time.time()
        self.stats['captchas_solved'] += 1
        self.save_stats()
        logger.info(f"✅ Hunter {browser_id}: CAPTCHA solved! Grace period active for {self.captcha_grace_period}s")
    
    def dismiss_popups(self, driver: uc.Chrome, browser_id: int) -> bool:
        """Detect and dismiss any popups that might appear"""
        dismissed = False
        
        # Common popup selectors
        popup_selectors = [
            # Close buttons
            "button[class*='close']",
            "button[aria-label*='close']",
            "button[aria-label*='Close']",
            "span[class*='close']",
            "div[class*='close-button']",
            "a[class*='close']",
            
            # Modal dismissers
            "button[class*='modal-close']",
            "button[class*='dismiss']",
            
            # Cookie banners
            "button[id*='cookie-accept']",
            "button[class*='cookie-accept']",
            "button[contains(text(), 'Accetta')]",
            
            # Common Italian dismissers
            "button:contains('Chiudi')",
            "button:contains('OK')",
            "button:contains('Continua')",
            
            # X buttons
            "button[aria-label='X']",
            "span[aria-label='X']"
        ]
        
        for selector in popup_selectors:
            try:
                # Try CSS selector first
                if "contains" not in selector:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            try:
                                driver.execute_script("arguments[0].click();", element)
                                logger.info(f"📢 Hunter {browser_id}: Dismissed popup with {selector}")
                                self.stats['popups_dismissed'] += 1
                                self.save_stats()
                                dismissed = True
                                time.sleep(0.5)
                                break
                            except:
                                continue
                else:
                    # Handle text-based selectors
                    text = selector.split("'")[1]
                    xpath = f"//button[contains(text(), '{text}')]"
                    elements = driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            try:
                                driver.execute_script("arguments[0].click();", element)
                                logger.info(f"📢 Hunter {browser_id}: Dismissed popup with text '{text}'")
                                self.stats['popups_dismissed'] += 1
                                self.save_stats()
                                dismissed = True
                                time.sleep(0.5)
                                break
                            except:
                                continue
                                
            except Exception as e:
                continue
                
        # Also try to dismiss by clicking overlay
        try:
            overlays = driver.find_elements(By.CSS_SELECTOR, "div[class*='overlay'], div[class*='backdrop']")
            for overlay in overlays:
                if overlay.is_displayed():
                    driver.execute_script("arguments[0].click();", overlay)
                    logger.info(f"📢 Hunter {browser_id}: Dismissed overlay")
                    dismissed = True
                    break
        except:
            pass
            
        return dismissed
    
    def detect_captcha(self, driver: uc.Chrome) -> tuple[bool, Optional[str], Optional[str]]:
        """Detect if CAPTCHA is present and return sitekey if found"""
        try:
            # Check for reCAPTCHA v2
            recaptcha_elements = driver.find_elements(By.CSS_SELECTOR, "div.g-recaptcha")
            if recaptcha_elements:
                for element in recaptcha_elements:
                    sitekey = element.get_attribute('data-sitekey')
                    if sitekey:
                        return True, sitekey, driver.current_url
                        
            # Check for reCAPTCHA iframe
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            if iframes:
                # Try to extract sitekey from iframe src
                for iframe in iframes:
                    src = iframe.get_attribute('src')
                    if 'k=' in src:
                        sitekey = src.split('k=')[1].split('&')[0]
                        return True, sitekey, driver.current_url
                        
            # Also check for text indicators
            page_text = driver.page_source.lower()
            if any(indicator in page_text for indicator in ['recaptcha', 'captcha', 'verifica che non sei un robot']):
                return True, None, driver.current_url
                
            return False, None, None
        except Exception as e:
            logger.debug(f"Error detecting CAPTCHA: {e}")
            return False, None, None
    
    def solve_captcha_automatically(self, driver: uc.Chrome, sitekey: str, pageurl: str, browser_id: int) -> bool:
        """Attempt to solve CAPTCHA automatically using 2captcha"""
        if not self.captcha_solver or not sitekey:
            return False
            
        logger.info(f"🤖 Hunter {browser_id}: Attempting automatic CAPTCHA solve...")
        
        token = self.captcha_solver.solve_recaptcha(sitekey, pageurl)
        if not token:
            return False
            
        try:
            # Inject the token
            driver.execute_script(f"""
                document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                    Object.entries(___grecaptcha_cfg.clients).forEach(([key, client]) => {{
                        if (client.callback) {{
                            client.callback('{token}');
                        }}
                    }});
                }}
            """)
            
            self.stats['captchas_auto_solved'] += 1
            self.mark_captcha_solved(browser_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to inject CAPTCHA token: {e}")
            return False
    
    def wait_for_captcha_solve(self, driver: uc.Chrome, browser_id: int, timeout: int = 120) -> bool:
        """Wait for user to solve CAPTCHA manually or solve automatically"""
        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
        
        if not captcha_detected:
            return True
            
        # Try automatic solving first if enabled
        if self.auto_solve and sitekey:
            if self.solve_captcha_automatically(driver, sitekey, pageurl, browser_id):
                return True
                
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
                if "conferma" in driver.current_url.lower() or "checkout" in driver.current_url.lower():
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
        """Create stealth browser with multi-monitor support and version handling"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        def create_chrome_options():
            """Create fresh ChromeOptions instance to avoid reuse errors"""
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
            
            # V4: EXPLICITLY VERIFY IMAGES ARE ENABLED
            # NO image blocking preferences here!
            # Images load normally for CAPTCHA visibility
            
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
            
            return options, x, y
        
        try:
            # Create fresh options
            options, x, y = create_chrome_options()
            
            # Try multiple approaches to handle version mismatches
            driver = None
            attempts = [
                (137, "Chrome 137"),       # Try Chrome 137 first (current version)
                (None, "auto-detection"),  # Fall back to auto-detection
                (138, "Chrome 138"),       # Try Chrome 138 as last resort
            ]
            
            for version_main, desc in attempts:
                try:
                    logger.info(f"🔄 Attempting with {desc}...")
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
                    logger.info(f"📸 Images ENABLED for CAPTCHA support")
                    return driver
                    
                except Exception as e:
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    if "version" in str(e).lower():
                        logger.warning(f"Version mismatch with {desc}: {str(e)[:100]}...")
                        # Create new options for next attempt
                        options, x, y = create_chrome_options()
                        continue
                    else:
                        raise
            
            # If all attempts failed, try one more time with driver update
            logger.warning("⚠️ All version attempts failed, trying driver update...")
            
            # Clear driver cache
            import shutil
            cache_dirs = [
                os.path.expanduser("~/.cache/selenium"),
                os.path.expanduser("~/.cache/undetected_chromedriver"),
                os.path.expanduser("~/.wdm"),
            ]
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    try:
                        shutil.rmtree(cache_dir)
                    except:
                        pass
            
            # Try one more time with fresh cache
            options, x, y = create_chrome_options()
            driver = uc.Chrome(options=options, use_subprocess=True)
            driver.set_page_load_timeout(20)
            
            # Inject stealth JavaScript
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            logger.info(f"✅ Browser {browser_id} ready after cache clear")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser {browser_id}: {e}")
            
            # Provide helpful error message
            if "version" in str(e).lower():
                logger.error("\n" + "="*60)
                logger.error("🚨 CHROMEDRIVER VERSION MISMATCH DETECTED!")
                logger.error("="*60)
                logger.error("Please run the following command to fix:")
                logger.error("  python3 fix_chromedriver.py")
                logger.error("="*60 + "\n")
            
            raise
    
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
        # Staggered refresh from V2/V3 for anti-detection
        last_refresh = time.time() - (browser_id * 5)  # Stagger initial refreshes
        refresh_interval = 30 + random.randint(-5, 5)  # Vary between 25-35 seconds
        
        last_session_refresh = time.time()
        local_stats = defaultdict(int)
        
        # CAPTCHA grace period check counter
        last_captcha_check = 0
        
        # Popup check counter
        last_popup_check = time.time()
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Check for popups every 10 seconds
                if time.time() - last_popup_check > 10:
                    self.dismiss_popups(driver, browser_id)
                    last_popup_check = time.time()
                
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
                    
                    # If we're in CAPTCHA grace period, try ALL matching tickets
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
                                                logger.info(f"🚀 Hunter {browser_id}: Attempting purchase in CAPTCHA grace period!")
                                            
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
                
                # Periodically test CAPTCHA grace period by attempting test purchase
                if in_grace_period and check_count - last_captcha_check > 20:  # Every ~minute
                    logger.info(f"🔍 Hunter {browser_id}: Testing CAPTCHA grace period...")
                    last_captcha_check = check_count
                    # This will be tested on next matching ticket
                
                # Keep human-like patterns from V2/V3
                if random.random() < 0.05:  # 5% chance
                    distraction_time = random.uniform(8, 15)
                    logger.debug(f"Hunter {browser_id}: Taking a {distraction_time:.1f}s break (human simulation)")
                    time.sleep(distraction_time)
                else:
                    # Normal refresh timing
                    refresh_time = random.uniform(2.5, 3.5)
                    time.sleep(refresh_time)
                
                # Staggered page refresh per browser
                if time.time() - last_refresh > refresh_interval:
                    driver.refresh()
                    last_refresh = time.time()
                    # Recalculate next refresh interval
                    refresh_interval = 30 + random.randint(-5, 5)
                
                # Progress update every 50 checks
                if check_count % 50 == 0:
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
                    
                    # Add CAPTCHA status to progress
                    captcha_status = " | 🟢 CAPTCHA OK" if in_grace_period else ""
                    logger.info(f"📊 Hunter {browser_id}: {check_count} checks @ {rate:.1f}/min | {local_str}{captcha_status}")
                    
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
        """Attempt to purchase a ticket with CAPTCHA handling"""
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
                    
                    # Wait a moment to see if CAPTCHA appears
                    time.sleep(2)
                    
                    # Check for CAPTCHA
                    captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
                    if captcha_detected:
                        logger.info(f"🤖 Hunter {browser_id}: CAPTCHA detected!")
                        self.stats['captchas_encountered'] += 1
                        self.save_stats()
                        
                        # Try to solve (automatically or manually)
                        if self.wait_for_captcha_solve(driver, browser_id):
                            # CAPTCHA solved, continue with purchase
                            logger.info(f"✅ Hunter {browser_id}: Continuing with purchase after CAPTCHA")
                            time.sleep(1)
                        else:
                            logger.warning(f"❌ Hunter {browser_id}: CAPTCHA not solved, purchase failed")
                            return False
                    
                    # Play success alarm sound
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
        """Display beautiful statistics dashboard"""
        total_runtime = self.stats['all_time_runtime'] + (time.time() - self.session_start_time)
        hours = int(total_runtime // 3600)
        minutes = int((total_runtime % 3600) // 60)
        
        print(f"\n{Colors.BOLD}{'═' * 60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}📊 FANSALE BOT STATISTICS DASHBOARD{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 60}{Colors.END}")
        
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
        
        # CAPTCHA stats
        print(f"\n{Colors.BOLD}🤖 CAPTCHA Stats:{Colors.END}")
        print(f"   Encountered: {self.stats.get('captchas_encountered', 0)}")
        print(f"   Solved Manually: {self.stats.get('captchas_solved', 0)}")
        print(f"   Solved Automatically: {self.stats.get('captchas_auto_solved', 0)}")
        
        if self.stats['total_checks'] > 0:
            rate = self.stats['total_checks'] / (total_runtime / 60) if total_runtime > 0 else 0
            print(f"\n{Colors.BOLD}⚡ Average Rate:{Colors.END} {rate:.1f} checks/min")
        
        print(f"\n{Colors.BOLD}{'═' * 60}{Colors.END}\n")
    
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
        print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 FANSALE BOT - ENHANCED EDITION V4{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 50}{Colors.END}")
        print("\n✨ Features:")
        print("  • No login required")
        print("  • Tracks Prato A, Prato B, and Settore tickets")
        print("  • Avoids duplicate logging")
        print("  • Persistent statistics")
        print(f"  • {Colors.RED}CAPTCHA detection and handling{Colors.END} ✅")
        print(f"  • {Colors.GREEN}CAPTCHA grace period exploitation{Colors.END} ✅")
        print(f"  • {Colors.YELLOW}Automatic CAPTCHA solving (2captcha){Colors.END} ✅")
        print(f"  • {Colors.CYAN}Popup detection and dismissal{Colors.END} ✅")
        print(f"  • {Colors.BOLD}Images ENABLED (verified){Colors.END} ✅")
        
        # Show current stats
        self.show_statistics_dashboard()
        
        # Check for 2captcha configuration
        if self.captcha_solver and self.config.twocaptcha_api_key:
            print(f"\n{Colors.GREEN}✅ 2Captcha configured - automatic solving enabled{Colors.END}")
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
        print(f"\n{Colors.GREEN}⚡ NO LOGIN REQUIRED - Direct ticket hunting!{Colors.END}")
        print(f"{Colors.RED}🤖 CAPTCHA SUPPORT - Auto-solve or manual alerts{Colors.END}")
        print(f"{Colors.CYAN}📢 POPUP HANDLING - Automatically dismisses popups{Colors.END}")
    
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

            logger.info(f"✅ {len(self.browsers)} browser(s) ready!")
            
            # Show tip about monitoring
            print(f"\n{Colors.CYAN}💡 TIP: Browsers are positioned for multi-monitor setups{Colors.END}")
            print(f"{Colors.CYAN}   Move them to your preferred monitors if needed{Colors.END}")
            print(f"\n{Colors.RED}⚠️  CAPTCHA ALERT: If CAPTCHA appears, it will be handled{Colors.END}")
            print(f"{Colors.GREEN}   Auto-solve if configured, or manual alert{Colors.END}")
            print(f"{Colors.CYAN}📢 POPUPS: Will be automatically dismissed{Colors.END}")
            
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
    print(f"{Colors.BOLD}{Colors.CYAN}🎫 FANSALE BOT - ENTERPRISE EDITION V4{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"\n{Colors.GREEN}✨ Features:{Colors.END}")
    print("  • Ticket type tracking (Prato A, B, Settore)")
    print("  • Duplicate detection with notifications")
    print("  • Persistent statistics")
    print("  • Multi-monitor support")
    print("  • Health monitoring")
    print("  • Advanced retry logic")
    print(f"\n{Colors.RED}🚀 V4 Features:{Colors.END}")
    print("  • CAPTCHA detection and handling")
    print("  • Optional automatic CAPTCHA solving (2captcha)")
    print("  • Automatic popup dismissal")
    print("  • Images ENABLED for proper functionality")
    print("  • CAPTCHA grace period exploitation")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"\n{Colors.RED}❌ Missing dependency: {e}{Colors.END}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium requests")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    
    # Load configuration
    config_path = Path("bot_config.json")
    config = BotConfig.from_file(config_path)
    
    # Check for 2captcha key in environment
    if os.getenv('TWOCAPTCHA_API_KEY'):
        config.twocaptcha_api_key = os.getenv('TWOCAPTCHA_API_KEY')
        config.auto_solve_captcha = True
    
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
        print(f"\n{Colors.GREEN}✅ Thank you for using FanSale Bot V4!{Colors.END}")


if __name__ == "__main__":
    main()
