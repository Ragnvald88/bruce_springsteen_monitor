#/fansale_v7_ultimate.py
"""
adds speed improvements
"""

import os
import sys
import time
import json
import random
import hashlib
import logging
import threading
import re
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
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

# ==================== Configuration ====================

@dataclass
class BotConfig:
    """Bot configuration with defaults"""
    browsers_count: int = 2
    max_tickets: int = 2
    refresh_interval: int = 30
    session_timeout: int = 900
    min_wait: float = 0.3  # Ultra-fast
    max_wait: float = 1.0  # Ultra-fast
    # Retry config removed - using decorator directly
    captcha_grace_period: int = 300
    twocaptcha_api_key: str = ""
    auto_solve_captcha: bool = False
    popup_check_interval: int = 30  # 30 seconds for more responsive popup handling
    captcha_check_interval: int = 300  # 5 minutes
    
    @classmethod
    def from_file(cls, path: Path) -> 'BotConfig':
        """Load config from JSON file if exists"""
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                # Filter out any unknown parameters from old config files
                valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
                filtered_data = {k: v for k, v in data.items() if k in valid_fields}
                return cls(**filtered_data)
        return cls()
    
    def save(self, path: Path):
        """Save config to JSON file"""
        data = self.__dict__.copy()
        if 'twocaptcha_api_key' in data:
            data['twocaptcha_api_key'] = ""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

# ==================== Enhanced Logging ====================

class CategoryLogger:
    """Separate loggers for each ticket category with visual differentiation"""
    
    COLORS = {
        'prato_a': '\033[92m',      # Green
        'prato_b': '\033[94m',      # Blue
        'settore': '\033[93m',      # Yellow
        'other': '\033[90m',        # Gray
        'system': '\033[96m',       # Cyan
        'reset': '\033[0m',
        'bold': '\033[1m',
        'alert': '\033[91m',        # Red
    }
    
    def __init__(self):
        self.loggers = {}
        self.setup_loggers()
        
    def setup_loggers(self):
        """Create logger with console output only (no separate files)"""
        categories = ['prato_a', 'prato_b', 'settore', 'other', 'system']
        
        # Single file logger for all categories
        file_logger = logging.getLogger('fansale.all')
        file_logger.setLevel(logging.INFO)
        file_logger.handlers.clear()
        
        # Single file handler
        file_handler = logging.FileHandler(
            'fansale_v7.log',
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        file_logger.addHandler(file_handler)
        
        # Category-specific console loggers
        for category in categories:
            logger = logging.getLogger(f'fansale.{category}')
            logger.setLevel(logging.INFO)
            logger.handlers.clear()
            
            # Console handler with color
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                CategoryFormatter(category, self.COLORS)
            )
            logger.addHandler(console_handler)
            
            self.loggers[category] = logger
    
    def log_ticket(self, category: str, message: str, level='info'):
        """Log message to console and single file"""
        if category in self.loggers:
            # Console output with color
            getattr(self.loggers[category], level)(message)
            # File output without color
            file_logger = logging.getLogger('fansale.all')
            getattr(file_logger, level)(f"[{category.upper()}] {message}")
        else:
            self.loggers['system'].warning(f"Unknown category: {category}")
    
    def log_alert(self, category: str, message: str):
        """Log alert message with special formatting"""
        color = self.COLORS.get(category, self.COLORS['alert'])
        formatted = f"{self.COLORS['bold']}{color}🚨 ALERT: {message}{self.COLORS['reset']}"
        print(formatted)
        self.log_ticket(category, message, 'warning')

class CategoryFormatter(logging.Formatter):
    """Custom formatter with category-specific colors"""
    
    def __init__(self, category: str, colors: Dict[str, str]):
        super().__init__()
        self.category = category
        self.colors = colors
        
    def format(self, record):
        color = self.colors.get(self.category, self.colors['reset'])
        prefix = {
            'prato_a': '🎫[PRATO A]',
            'prato_b': '🎫[PRATO B]',
            'settore': '🎫[SETTORE]',
            'other': '🎫[OTHER]',
            'system': '⚙️[SYSTEM]'
        }.get(self.category, '📝')
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"{color}{timestamp} {prefix} {record.getMessage()}{self.colors['reset']}"

# ==================== Statistics Manager ====================

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
            'purchases_by_type': {
                'prato_a': 0,
                'prato_b': 0,
                'settore': 0,
                'other': 0
            },
            'blocks_encountered': 0,
            'captchas_encountered': 0,
            'captchas_solved': 0,
            'captchas_auto_solved': 0,
            'popups_dismissed': 0,
            'all_time_runtime': 0,
                    }
    
    def save(self):
        """Save stats to file with atomic write"""
        with self.lock:
            temp_file = self.stats_file.with_suffix('.tmp')
            try:
                with open(temp_file, 'w') as f:
                    json.dump(self.stats, f, indent=2)
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

# ==================== 2Captcha Solver ====================

class TwoCaptchaSolver:
    """Handles automatic CAPTCHA solving via 2captcha service"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
        self.session = requests.Session()
        
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
            
            response = self.session.post(submit_url, data=submit_data, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                return None
                
            captcha_id = result.get('request')
            
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
                    return result.get('request')
                elif result.get('request') not in ['CAPCHA_NOT_READY', 'CAPTCHA_NOT_READY']:
                    return None
                    
            return None
            
        except Exception:
            return None

# ==================== Helper Functions ====================

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)):
    """Sophisticated retry decorator with exponential backoff"""
    def decorator(func):
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

# ==================== Main Bot Class ====================

class FanSaleBotV7:
    """Ultimate FanSale Bot with all fixes and enhancements"""
    
    def __init__(self, config: Optional[BotConfig] = None):
        # Load configuration
        self.config = config or BotConfig()
        
        # FIX #1: Use correct environment variable name
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
        
        # Configuration
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_types_to_hunt = set()  # FIX #2: Properly initialized
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Ticket tracking
        self.seen_tickets = set()
        self.ticket_details_cache = {}
        
        # CAPTCHA tracking
        self.captcha_solved_time = {}
        self.captcha_grace_period = self.config.captcha_grace_period
        
        # Logging
        self.category_logger = CategoryLogger()
        
        # Statistics
        self.stats_file = Path("fansale_stats_v7.json")
        self.stats_manager = StatsManager(self.stats_file)
        self.stats = self.stats_manager.stats
        
        # Performance monitoring
        self.session_start_time = time.time()
        # Performance tracking removed - not actionable
        
        # 2Captcha solver
        api_key = self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY', '')
        if api_key:
            self.captcha_solver = TwoCaptchaSolver(api_key)
            self.auto_solve = self.config.auto_solve_captcha
            self.category_logger.log_ticket('system', f"✅ 2Captcha configured with API key: {api_key[:8]}...")
        else:
            self.captcha_solver = None
            self.auto_solve = False
            self.category_logger.log_ticket('system', "⚠️ No 2Captcha API key - manual CAPTCHA solving only", 'warning')

    def save_stats(self):
        """Save statistics to file"""
        try:
            session_time = time.time() - self.session_start_time
            self.stats['all_time_runtime'] = self.stats.get('all_time_runtime', 0) + session_time
            
            
                
            self.stats_manager.save()
        except Exception as e:
            self.category_logger.log_ticket('system', f"Failed to save stats: {e}", 'error')
    
    # Method removed - browsers load images by default
    
    def categorize_ticket(self, ticket_text: str) -> str:
        """Categorize ticket based on text content"""
        ticket_lower = ticket_text.lower()
        
        if 'prato a' in ticket_lower or 'prato gold a' in ticket_lower:
            return 'prato_a'
        elif 'prato b' in ticket_lower or 'prato gold b' in ticket_lower:
            return 'prato_b'
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
        clean_text = re.sub(r'\d{1,2}:\d{2}:\d{2}', '', ticket_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return hashlib.md5(clean_text.encode()).hexdigest()
    
    def extract_full_ticket_info(self, driver: uc.Chrome, ticket_element: WebElement) -> Dict:
        """Extract only essential ticket information"""
        try:
            ticket_info = {
                'raw_text': ticket_element.text,
                'category': 'other',
                'offer_id': ''
            }
            
            # Try to extract offer ID if available
            try:
                offer_id = ticket_element.get_attribute('data-offer-id')
                if offer_id:
                    ticket_info['offer_id'] = offer_id
            except:
                pass
            
            # Categorize based on text
            ticket_info['category'] = self.categorize_ticket(ticket_info['raw_text'])
            
            return ticket_info
            
        except Exception as e:
            self.category_logger.log_ticket('system', f"Error extracting ticket info: {e}", 'error')
            return {
                'raw_text': ticket_element.text,
                'category': self.categorize_ticket(ticket_element.text),
                'offer_id': ''
            }
    
    def log_new_ticket(self, ticket_info: Dict, browser_id: int):
        """Log newly discovered ticket"""
        category = ticket_info['category']
        is_hunting = category in self.ticket_types_to_hunt
        
        if is_hunting:
            self.category_logger.log_alert(category,
                f"NEW TICKET FOUND by Hunter {browser_id}!")
        
        self.category_logger.log_ticket(category,
            f"🎫 NEW {category.upper()} ticket - Hunter {browser_id}")
    
    def check_captcha_status(self, browser_id: int) -> bool:
        """Check if browser is within CAPTCHA grace period"""
        if browser_id in self.captcha_solved_time:
            time_since_solved = time.time() - self.captcha_solved_time[browser_id]
            if time_since_solved < self.captcha_grace_period:
                remaining = self.captcha_grace_period - time_since_solved
                self.category_logger.log_ticket('system', 
                    f"Hunter {browser_id}: CAPTCHA grace period active ({remaining:.0f}s remaining)")
                return True
        return False
    
    def mark_captcha_solved(self, browser_id: int):
        """Mark CAPTCHA as solved for this browser"""
        self.captcha_solved_time[browser_id] = time.time()
        self.stats['captchas_solved'] += 1
        self.save_stats()
        self.category_logger.log_ticket('system', 
            f"✅ Hunter {browser_id}: CAPTCHA solved! Grace period active for {self.captcha_grace_period}s")
    
    def dismiss_popups(self, driver: uc.Chrome, browser_id: int) -> int:
        """Simple popup dismissal - most popups just need a click"""
        dismissed_count = 0
        
        try:
            # Priority 1: "Carica Offerte" button (most important)
            try:
                carica = driver.find_element(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
                if carica.is_displayed():
                    driver.execute_script("arguments[0].click();", carica)
                    self.category_logger.log_ticket('system', f"📢 Hunter {browser_id}: Clicked 'Carica Offerte' button")
                    dismissed_count += 1
                    time.sleep(0.5)
            except:
                pass
            
            # Priority 2: Common close buttons
            close_selectors = [
                "button[aria-label*='close' i]",
                "button[aria-label*='chiudi' i]", 
                "button[class*='close']",
                "a[class*='close']"
            ]
            
            for selector in close_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            driver.execute_script("arguments[0].click();", elem)
                            dismissed_count += 1
                            break
                except:
                    continue
            
            # Priority 3: Accept cookies if needed
            if dismissed_count == 0:
                try:
                    accept_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accetta') or contains(text(), 'OK')]")
                    for btn in accept_btns:
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            dismissed_count += 1
                            break
                except:
                    pass
                
        except Exception as e:
            self.category_logger.log_ticket('system', f"Error in dismiss_popups: {e}", 'error')
            
        return dismissed_count
    
    def detect_captcha(self, driver: uc.Chrome) -> tuple[bool, Optional[str], Optional[str]]:
        """Simple CAPTCHA detection"""
        try:
            # Check for common CAPTCHA elements
            captcha_selectors = [
                "div.g-recaptcha",
                "iframe[src*='recaptcha']",
                "div.h-captcha"
            ]
            
            for selector in captcha_selectors:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    self.category_logger.log_ticket('system', "🤖 CAPTCHA detected!")
                    
                    # Try to get sitekey for reCAPTCHA
                    sitekey = None
                    if 'recaptcha' in selector:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        sitekey = elem.get_attribute('data-sitekey')
                    
                    return True, sitekey, driver.current_url
            
            return False, None, None
            
        except Exception as e:
            self.category_logger.log_ticket('system', f"Error detecting CAPTCHA: {e}", 'error')
            return False, None, None
    
    def solve_captcha_automatically(self, driver: uc.Chrome, sitekey: str, pageurl: str, browser_id: int) -> bool:
        """Attempt to solve CAPTCHA automatically using 2captcha"""
        if not self.captcha_solver or not sitekey:
            self.category_logger.log_ticket('system', 
                f"Cannot auto-solve: solver={bool(self.captcha_solver)}, sitekey={bool(sitekey)}", 'warning')
            return False
            
        self.category_logger.log_ticket('system', f"🤖 Hunter {browser_id}: Attempting automatic CAPTCHA solve...")
        
        token = self.captcha_solver.solve_recaptcha(sitekey, pageurl)
        if not token:
            self.category_logger.log_ticket('system', "Failed to get token from 2captcha", 'error')
            return False
            
        try:
            # Simple token injection - most sites just need the textarea filled
            injection_success = driver.execute_script(f"""
                var token = '{token}';
                var success = false;
                
                // Find and fill the response textarea
                var textarea = document.getElementById('g-recaptcha-response');
                if (textarea) {{
                    textarea.innerHTML = token;
                    textarea.value = token;
                    success = true;
                }}
                
                // Try to trigger the callback if it exists
                if (success && window.___grecaptcha_cfg) {{
                    Object.values(window.___grecaptcha_cfg.clients).forEach(function(client) {{
                        if (client.callback) {{
                            try {{
                                client.callback(token);
                            }} catch(e) {{}}
                        }}
                    }});
                }}
                
                return success;
            """)
            
            if injection_success:
                self.stats['captchas_auto_solved'] += 1
                self.mark_captcha_solved(browser_id)
                self.category_logger.log_ticket('system', f"✅ CAPTCHA token injected successfully!")
                return True
            else:
                self.category_logger.log_ticket('system', 
                    "Failed to inject CAPTCHA token - no suitable element found", 'error')
                return False
                
        except Exception as e:
            self.category_logger.log_ticket('system', f"Failed to inject CAPTCHA token: {e}", 'error')
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
            self.category_logger.log_ticket('system', f"🤖 Attempting automatic CAPTCHA solve with 2captcha...")
            if self.solve_captcha_automatically(driver, sitekey, pageurl, browser_id):
                return True
            else:
                self.category_logger.log_ticket('system', "Automatic solving failed, falling back to manual", 'warning')
                
        # Fall back to manual solving
        self.category_logger.log_ticket('system', f"\n{'='*60}")
        self.category_logger.log_ticket('system', f"🤖 CAPTCHA DETECTED - Hunter {browser_id}")
        self.category_logger.log_ticket('system', f"{'='*60}")
        self.category_logger.log_ticket('system', f"⚠️  MANUAL ACTION REQUIRED!")
        self.category_logger.log_ticket('system', f"Please solve the CAPTCHA in Browser {browser_id}")
        self.category_logger.log_ticket('system', f"Waiting up to {timeout} seconds...")
        self.category_logger.log_ticket('system', f"{'='*60}\n")
        
        # Play alert sound
        for _ in range(5):
            print('\a')
            time.sleep(0.5)
        
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            # Check if CAPTCHA is still present
            if not self.detect_captcha(driver)[0]:
                self.category_logger.log_ticket('system', f"✅ CAPTCHA solved in Browser {browser_id}!")
                self.mark_captcha_solved(browser_id)
                return True
                
            # Also check if we've moved to a new page (indicating success)
            try:
                current_url = driver.current_url.lower()
                if any(x in current_url for x in ['conferma', 'checkout', 'payment', 'cart']):
                    self.category_logger.log_ticket('system', f"✅ Purchase proceeding in Browser {browser_id}!")
                    self.mark_captcha_solved(browser_id)
                    return True
            except:
                pass
                
            time.sleep(check_interval)
            
        self.category_logger.log_ticket('system', f"❌ CAPTCHA timeout in Browser {browser_id}", 'error')
        return False
    
    @retry(max_attempts=3, delay=2.0, exceptions=(WebDriverException,))
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create browser with undetected-chromedriver"""
        self.category_logger.log_ticket('system', f"🚀 Creating Browser {browser_id}...")
        
        try:
            options = uc.ChromeOptions()
            
            # Basic stealth options (undetected-chromedriver handles most of this)
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Window positioning for multi-monitor
            window_width = 450
            window_height = 800
            col = (browser_id - 1) % 4
            row = (browser_id - 1) // 4
            x = col * (window_width + 10)
            y = row * 100
            
            options.add_argument(f'--window-position={x},{y}')
            options.add_argument(f'--window-size={window_width},{window_height}')
            
            # Profile persistence
            profile_dir = Path("browser_profiles") / f"browser_{browser_id}"
            profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
            
            # Create driver - let undetected-chromedriver handle version detection
            try:
                driver = uc.Chrome(
                    options=options,
                    use_subprocess=True,
                    suppress_welcome=True
                )
            except Exception:
                # Fallback to version 137 if auto-detect fails
                driver = uc.Chrome(
                    options=options,
                    version_main=137,
                    use_subprocess=True,
                    suppress_welcome=True
                )
            
            # Set timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            self.category_logger.log_ticket('system', 
                f"✅ Browser {browser_id} created at position ({x}, {y})")
            
            return driver
            
        except Exception as e:
            self.category_logger.log_ticket('system', 
                f"❌ Failed to create browser {browser_id}: {e}", 'error')
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
            return False

    def clear_browser_data(self, driver: uc.Chrome, browser_id: int):
        """Clear browser data to bypass blocks - simplified"""
        try:
            self.category_logger.log_ticket('system', 
                f"🧹 Clearing data for Browser {browser_id}...")
            
            # Just clear cookies and navigate to blank
            driver.delete_all_cookies()
            driver.get("about:blank")
            time.sleep(1)
            
            self.category_logger.log_ticket('system', f"✅ Browser {browser_id} data cleared")
            self.stats['blocks_encountered'] += 1
            self.save_stats()
            
        except Exception as e:
            self.category_logger.log_ticket('system', f"Failed to clear browser data: {e}", 'error')
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop with all V5 enhancements"""
        self.category_logger.log_ticket('system', f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to event page
        self.category_logger.log_ticket('system', f"📍 Navigating to: {self.target_url}")
        page_start = time.time()
        driver.get(self.target_url)
        page_load_time = time.time() - page_start
        # Removed performance tracking - not actionable
        self.category_logger.log_ticket('system', f"📄 Page loaded in {page_load_time:.2f}s")
        
        # Initial popup dismissal
        time.sleep(0.5)
        initial_popups = self.dismiss_popups(driver, browser_id)
        
        # Special handling for "Carica Offerte" button
        try:
            carica_button = driver.find_element(By.CSS_SELECTOR, "button.js-BotProtectionModalButton1")
            if carica_button and carica_button.is_displayed():
                driver.execute_script("arguments[0].click();", carica_button)
                self.category_logger.log_ticket('system', 
                    f"🎯 Hunter {browser_id}: Clicked 'Carica Offerte' button!")
                initial_popups += 1
                time.sleep(0.5)
                # Check for any new popups after clicking
                additional = self.dismiss_popups(driver, browser_id)
                initial_popups += additional
        except:
            pass
        
        self.category_logger.log_ticket('system', f"📢 Dismissed {initial_popups} initial popups")
        
        # Verify images are loading - REMOVED: Unnecessary check that adds delay
        # self.verify_image_loading(driver, browser_id)
        
        check_count = 0
        # Staggered refresh times for each browser
        last_refresh = time.time() - (browser_id * 5)  # Stagger initial refreshes
        refresh_interval = 15 + random.randint(-3, 3)  # Faster refresh: 12-18 seconds
        
        last_session_refresh = time.time()
        local_stats = defaultdict(int)
        
        # Tracking for various checks
        last_captcha_check = 0
        last_popup_check = time.time()
        last_captcha_test = time.time()  # New: Track last CAPTCHA test
        
        # Initialize grace period status
        in_grace_period = False
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['total_checks'] += 1
                
                # Periodic CAPTCHA check - only browser 1 does this every 5 minutes
                # Skip this check if we're in the first 30 seconds to allow faster initial checking
                if browser_id == 1 and time.time() - last_captcha_test > self.config.captcha_check_interval and check_count > 30:
                    self.category_logger.log_ticket('system', 
                        f"🔍 Hunter {browser_id}: Performing periodic CAPTCHA check...")
                    captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
                    if captcha_detected:
                        self.category_logger.log_alert('system', f"CAPTCHA detected during periodic check!")
                        if self.auto_solve and self.captcha_solver and sitekey:
                            self.category_logger.log_ticket('system', "🤖 Attempting automatic CAPTCHA solve...")
                            if self.solve_captcha_automatically(driver, sitekey, pageurl, browser_id):
                                self.mark_captcha_solved(browser_id)
                                self.category_logger.log_ticket('system', "✅ CAPTCHA solved automatically!")
                            else:
                                self.category_logger.log_ticket('system', "❌ Automatic CAPTCHA solve failed", 'error')
                                self.wait_for_captcha_solve(driver, browser_id)
                        else:
                            self.wait_for_captcha_solve(driver, browser_id)
                    else:
                        self.category_logger.log_ticket('system', f"✅ No CAPTCHA detected - all clear!")
                    last_captcha_test = time.time()
                
                # Popup check - more frequent than V4
                if time.time() - last_popup_check > self.config.popup_check_interval:
                    dismissed = self.dismiss_popups(driver, browser_id)
                    if dismissed > 0:
                        self.category_logger.log_ticket('system', f"Dismissed {dismissed} popups")
                    last_popup_check = time.time()
                
                # Check for 404 blocks
                if self.is_blocked(driver):
                    self.category_logger.log_ticket('system', 
                        f"⚠️ Hunter {browser_id}: Block detected!", 'warning')
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(random.uniform(2.5, 3.5))
                    self.dismiss_popups(driver, browser_id)  # Dismiss any new popups
                    continue
                
                # Session refresh every 15 minutes
                if time.time() - last_session_refresh > 900:
                    self.category_logger.log_ticket('system', 
                        f"🔄 Hunter {browser_id}: Preventive session refresh...")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(1)  # Reduced from 3 seconds for faster checking
                    self.dismiss_popups(driver, browser_id)
                    last_session_refresh = time.time()
                    continue
                
                # Look for tickets - NO CACHING
                # Primary selector
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                # Fallback selectors if no tickets found with primary
                if not tickets:
                    # Try alternative selectors
                    alternative_selectors = [
                        "div[class*='ticket'][class*='available']",
                        "div[class*='biglietto'][class*='disponibile']",
                        "article[class*='ticket']",
                        "div[data-testid*='ticket']"
                    ]
                    for selector in alternative_selectors:
                        tickets = driver.find_elements(By.CSS_SELECTOR, selector)
                        if tickets:
                            self.category_logger.log_ticket('system', 
                                f"Found tickets with alternative selector: {selector}")
                            break
                
                # Check time removed - not actionable
                
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
                                
                                # FIX #2: Properly check if we should purchase
                                if category in self.ticket_types_to_hunt:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.max_tickets:
                                            # If in grace period, log it
                                            if in_grace_period:
                                                self.category_logger.log_ticket('system', 
                                                    f"🚀 Hunter {browser_id}: CAPTCHA grace period active - fast purchase!")
                                            
                                            if self.purchase_ticket(driver, ticket, browser_id):
                                                self.tickets_secured += 1
                                                self.stats['purchases'] += 1
                                                self.stats['purchases_by_type'][category] += 1
                                                self.save_stats()
                                                
                                                if self.tickets_secured >= self.max_tickets:
                                                    self.category_logger.log_ticket('system', 
                                                        f"🎉 Max tickets secured!")
                                                    return
                                                    
                        except Exception as e:
                            continue
                
                # Periodically test CAPTCHA grace period
                if in_grace_period and check_count - last_captcha_check > 20:  # Every ~minute
                    self.category_logger.log_ticket('system', 
                        f"🔍 Hunter {browser_id}: Testing CAPTCHA grace period...")
                    last_captcha_check = check_count
                
                # Fast checking to achieve ~30 checks per minute
                refresh_time = random.uniform(self.config.min_wait, self.config.max_wait)
                time.sleep(refresh_time)
                
                # Staggered page refresh per browser
                if time.time() - last_refresh > refresh_interval:
                    driver.refresh()
                    last_refresh = time.time()
                    # Recalculate next refresh interval
                    refresh_interval = 15 + random.randint(-3, 3)
                    # Dismiss popups after refresh
                    time.sleep(1)
                    self.dismiss_popups(driver, browser_id)
                
                # Progress update every 60 checks (about once per minute at ~60+ checks/min)
                if check_count % 60 == 0:
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
                    
                    self.category_logger.log_ticket('system', 
                        f"📊 Hunter {browser_id}: {' | '.join(status_parts)}")
                    
            except TimeoutException:
                self.category_logger.log_ticket('system', 
                    f"Hunter {browser_id}: Page timeout, refreshing...", 'warning')
                driver.refresh()
                time.sleep(random.uniform(1.5, 2.5))
                self.dismiss_popups(driver, browser_id)
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    self.category_logger.log_ticket('system', 
                        f"Hunter {browser_id}: Session died", 'error')
                    break
                self.category_logger.log_ticket('system', 
                    f"Hunter {browser_id}: Browser error, continuing...", 'error')
                time.sleep(5)
                
            except Exception as e:
                self.category_logger.log_ticket('system', 
                    f"Hunter {browser_id} error: {e}", 'error')
                import traceback
                traceback.print_exc()
                time.sleep(5)
    
    def wait_for_page_change(self, driver: uc.Chrome, initial_url: str, timeout: int = 5) -> bool:
        """Wait for page URL to change, indicating navigation occurred"""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.current_url != initial_url
            )
            return True
        except TimeoutException:
            return False

    def handle_checkout_page(self, driver: uc.Chrome, browser_id: int) -> bool:
        """Handle the checkout page after clicking buy button"""
        try:
            current_url = driver.current_url.lower()
            
            # Look for common checkout elements
            checkout_selectors = [
                # Quantity selectors
                "select[name*='quantity']",
                "input[name*='quantity']",
                "select[name*='quantita']",
                
                # Proceed/Continue buttons
                "button:contains('Procedi')",
                "button:contains('Continua')",
                "button:contains('Conferma')",
                "button:contains('Continue')",
                "button:contains('Proceed')",
                "button[type='submit']"
            ]
            
            # Try to find and click proceed button
            for selector in checkout_selectors:
                try:
                    if ':contains' in selector:
                        # Convert to XPath
                        match = re.search(r":contains\('([^']+)'\)", selector)
                        if match:
                            text = match.group(1)
                            xpath = f"//button[contains(text(), '{text}')]"
                            elements = driver.find_elements(By.XPATH, xpath)
                            elements = [e for e in elements if e.is_displayed() and e.is_enabled()]
                            if elements:
                                driver.execute_script("arguments[0].click();", elements[0])
                                self.category_logger.log_ticket('system', 
                                    f"✅ Hunter {browser_id}: Clicked '{text}' on checkout page")
                                return True
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed() and element.is_enabled():
                            # If it's a quantity selector, ensure it's set to 1
                            if 'quantity' in selector.lower() or 'quantita' in selector.lower():
                                driver.execute_script("arguments[0].value = '1';", element)
                                self.category_logger.log_ticket('system', 
                                    f"✅ Hunter {browser_id}: Set quantity to 1")
                            else:
                                driver.execute_script("arguments[0].click();", element)
                                self.category_logger.log_ticket('system', 
                                    f"✅ Hunter {browser_id}: Clicked checkout element")
                                return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            self.category_logger.log_ticket('system', 
                f"Error handling checkout page: {e}", 'error')
            return False

    @retry(max_attempts=2, delay=0.5, exceptions=(ElementNotInteractableException, StaleElementReferenceException))
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket with enhanced interaction"""
        try:
            self.category_logger.log_ticket('system', 
                f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Dismiss any popups first
            self.dismiss_popups(driver, browser_id)
            
            # Scroll to ticket element
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", ticket_element)
            time.sleep(0.5)
            
            # Try multiple click methods
            click_success = False
            
            # Method 1: JavaScript click (most reliable)
            try:
                driver.execute_script("arguments[0].click();", ticket_element)
                click_success = True
                self.category_logger.log_ticket('system', 
                    f"✅ Hunter {browser_id}: Clicked ticket via JavaScript")
            except Exception as e1:
                # Method 2: Click on the specific FanSale link/button inside ticket
                try:
                    # Look for the specific FanSale ticket link structure
                    ticket_link = ticket_element.find_element(By.CSS_SELECTOR, "a.Button-inOfferEntryList, a[id*='detailBShowOfferButton']")
                    driver.execute_script("arguments[0].click();", ticket_link)
                    click_success = True
                    self.category_logger.log_ticket('system', 
                        f"✅ Hunter {browser_id}: Clicked FanSale ticket link")
                except:
                    # Fallback to any clickable child
                    try:
                        clickable_child = ticket_element.find_element(By.CSS_SELECTOR, "a, button, [role='button']")
                        driver.execute_script("arguments[0].click();", clickable_child)
                        click_success = True
                        self.category_logger.log_ticket('system', 
                            f"✅ Hunter {browser_id}: Clicked ticket child element")
                    except:
                        pass
                    # Method 3: Action chains
                    try:
                        actions = ActionChains(driver)
                        actions.move_to_element(ticket_element).click().perform()
                        click_success = True
                        self.category_logger.log_ticket('system', 
                            f"✅ Hunter {browser_id}: Clicked ticket via ActionChains")
                    except:
                        # Method 4: Direct click
                        try:
                            ticket_element.click()
                            click_success = True
                            self.category_logger.log_ticket('system', 
                                f"✅ Hunter {browser_id}: Clicked ticket directly")
                        except:
                            pass
            
            if not click_success:
                self.category_logger.log_ticket('system', 
                    f"Failed to click ticket element", 'warning')
                return False
                
            time.sleep(random.uniform(0.8, 1.2))
            
            # Dismiss any new popups that might appear
            self.dismiss_popups(driver, browser_id)
            
            # Enhanced buy button detection with Italian-specific selectors
            buy_selectors = [
                # Priority 1: FanSale-specific data attributes
                "button[data-qa='buyNowButton']",
                "button[data-qa='ticketCheckoutButton']",
                "button[data-testid*='buy']",
                "button[data-testid*='acquista']",
                
                # Priority 2: Italian text-based selectors (will convert to XPath)
                "button:contains('Acquista')",
                "button:contains('Acquista ora')",
                "button:contains('Compra')",
                "button:contains('Compra ora')",
                "button:contains('Prenota')",
                "button:contains('Procedi')",
                "button:contains('Aggiungi al carrello')",
                "button:contains('Vai al carrello')",
                
                # Priority 3: Class-based selectors
                "button[class*='buy']",
                "button[class*='acquista']",
                "button[class*='purchase']",
                "button[class*='checkout']",
                "button[class*='cart']",
                "button[class*='carrello']",
                
                # Priority 4: English text alternatives
                "button:contains('Buy')",
                "button:contains('Buy Now')",
                "button:contains('Purchase')",
                "button:contains('Add to Cart')",
                "button:contains('Checkout')",
                
                # Priority 5: Link styled as button
                "a[class*='buy'][class*='button']",
                "a[class*='btn'][href*='cart']",
                "a[class*='btn'][href*='checkout']",
                "a[class*='btn'][href*='acquista']",
                
                # Priority 6: Generic button with specific attributes
                "button[type='submit']",
                "input[type='submit'][value*='buy']",
                "input[type='submit'][value*='acquista']"
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
                        self.category_logger.log_ticket('system', 
                            f"🎯 Hunter {browser_id}: Found buy button with selector: {selector}")
                        
                        # Log button details for debugging
                        btn_text = buy_btn.text.strip() if buy_btn.text else "No text"
                        btn_class = buy_btn.get_attribute('class') or "No class"
                        self.category_logger.log_ticket('system', 
                            f"   Button text: '{btn_text}', Classes: '{btn_class}'")
                        
                        # Scroll to buy button
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                        time.sleep(0.3)
                        
                        # Try to click
                        try:
                            driver.execute_script("arguments[0].click();", buy_btn)
                        except:
                            buy_btn.click()
                            
                        self.category_logger.log_ticket('system', 
                            f"✅ Hunter {browser_id}: Buy button clicked!")
                        
                        # Store current URL to detect navigation
                        initial_url = driver.current_url
                        
                        # Wait for page change or CAPTCHA
                        page_changed = self.wait_for_page_change(driver, initial_url, timeout=3)
                        
                        if page_changed:
                            self.category_logger.log_ticket('system', 
                                f"🎯 Hunter {browser_id}: Navigated to: {driver.current_url}")
                            
                            # Check if we reached checkout/cart page
                            current_url = driver.current_url.lower()
                            if any(keyword in current_url for keyword in ['carrello', 'cart', 'checkout', 'conferma', 'payment']):
                                self.category_logger.log_ticket('system', 
                                    f"🛒 Hunter {browser_id}: Reached checkout page!")
                                # Play success sound
                                print('' * 5)
                        else:
                            # Page didn't change, wait a bit more
                            time.sleep(1)
                        
                        # Check for CAPTCHA
                        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
                        if captcha_detected:
                            self.category_logger.log_ticket('system', 
                                f"🤖 Hunter {browser_id}: CAPTCHA detected after buy click!")
                            self.stats['captchas_encountered'] += 1
                            self.save_stats()
                            
                            # Try to solve
                            if self.wait_for_captcha_solve(driver, browser_id):
                                self.category_logger.log_ticket('system', 
                                    f"✅ Hunter {browser_id}: Continuing after CAPTCHA")
                                time.sleep(1)
                            else:
                                self.category_logger.log_ticket('system', 
                                    f"❌ Hunter {browser_id}: CAPTCHA not solved", 'warning')
                                return False
                        
                        # Play success alarm sound
                        print('\a' * 3)  # System beep
                        
                        # Take screenshot
                        screenshot_path = f"screenshots/ticket_{browser_id}_{int(time.time())}.png"
                        Path("screenshots").mkdir(exist_ok=True)
                        driver.save_screenshot(screenshot_path)
                        self.category_logger.log_ticket('system', 
                            f"📸 Screenshot saved: {screenshot_path}")
                        
                        return True
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    continue
                    
            self.category_logger.log_ticket('system', 
                f"Hunter {browser_id}: No buy button found", 'warning')
            
            # Take debug screenshot
            debug_path = f"screenshots/debug_{browser_id}_{int(time.time())}.png"
            driver.save_screenshot(debug_path)
            self.category_logger.log_ticket('system', f"📸 Debug screenshot: {debug_path}")
            
            return False
            
        except Exception as e:
            self.category_logger.log_ticket('system', f"Purchase failed: {e}", 'error')
            return False
    
    def show_statistics_dashboard(self):
        """Show live statistics dashboard"""
        elapsed = time.time() - self.session_start_time
        runtime_str = f"{int(elapsed//3600)}h {int((elapsed%3600)//60)}m {int(elapsed%60)}s"
        
        # Calculate rates
        checks_per_min = (self.stats['total_checks'] / elapsed * 60) if elapsed > 0 else 0
        
        print(f"\n{CategoryLogger.COLORS['bold']}{'='*60}{CategoryLogger.COLORS['reset']}")
        print(f"{CategoryLogger.COLORS['system']}📊 LIVE STATISTICS DASHBOARD{CategoryLogger.COLORS['reset']}")
        print(f"{'='*60}")
        
        # Session info
        print(f"\n🕐 Session Runtime: {runtime_str}")
        print(f"🔍 Total Checks This Session: {self.stats['total_checks']:,}")
        print(f"⚡ Check Rate: {checks_per_min:.1f}/min")
        
        # Ticket stats
        print(f"\n🎫 Tickets Found: {self.stats['total_tickets_found']:,}")
        print(f"✨ Unique Tickets: {self.stats['unique_tickets_found']:,}")
        
        # By category
        print("\n📊 By Category:")
        for cat in ['prato_a', 'prato_b', 'settore', 'other']:
            count = self.stats['tickets_by_type'].get(cat, 0)
            if count > 0:
                color = getattr(CategoryLogger.COLORS, cat, CategoryLogger.COLORS['other'])
                cat_display = cat.replace('_', ' ').title()
                print(f"   {color}{cat_display}: {count}{CategoryLogger.COLORS['reset']}")
        
        # Purchase stats
        if self.stats['purchases'] > 0:
            print(f"\n🛒 Purchases: {self.stats['purchases']}")
            for cat, count in self.stats['purchases_by_type'].items():
                if count > 0:
                    cat_display = cat.replace('_', ' ').title()
                    print(f"   {cat_display}: {count}")
        
        # Other stats
        print(f"\n⚠️  Blocks Encountered: {self.stats.get('blocks_encountered', 0)}")
        print(f"🤖 CAPTCHAs: {self.stats.get('captchas_encountered', 0)}")
        if self.stats.get('captchas_solved', 0) > 0:
            print(f"   Solved: {self.stats['captchas_solved']}")
        
        
        
        print(f"\n{CategoryLogger.COLORS['bold']}{'='*60}{CategoryLogger.COLORS['reset']}")
    
    def configure_ticket_filters(self):
        """Allow user to select which ticket types to hunt for"""
        print(f"\n{CategoryLogger.COLORS['bold']}🎯 SELECT TICKET TYPES TO HUNT{CategoryLogger.COLORS['reset']}")
        print("=" * 50)
        
        # Available ticket types
        available_types = {
            '1': ('prato_a', 'Prato A', CategoryLogger.COLORS['prato_a']),
            '2': ('prato_b', 'Prato B', CategoryLogger.COLORS['prato_b']),
            '3': ('prato_all', 'All Prato (A + B)', CategoryLogger.COLORS['system']),
            '4': ('settore', 'Settore', CategoryLogger.COLORS['settore']),
            '5': ('other', 'Other/Unknown', CategoryLogger.COLORS['other']),
            '6': ('all', 'ALL ticket types', CategoryLogger.COLORS['bold'])
        }
        
        print("\nAvailable ticket categories:")
        for key, (_, display, color) in available_types.items():
            if key == '3':
                print(f"  {color}{key}. {display}{CategoryLogger.COLORS['reset']} ⭐")
            elif key == '4':
                print(f"  {color}{key}. {display}{CategoryLogger.COLORS['reset']} (Seated: Fila/Posto/Anello)")
            elif key == '6':
                print(f"\n  {color}{key}. {display}{CategoryLogger.COLORS['reset']}")
            else:
                print(f"  {color}{key}. {display}{CategoryLogger.COLORS['reset']}")
        
        while True:
            selection = input(f"\n{CategoryLogger.COLORS['bold']}Enter your choices (e.g., '1,2' or '3' for all Prato):{CategoryLogger.COLORS['reset']} ").strip()
            
            if not selection:
                # Default to all Prato types
                self.ticket_types_to_hunt = {'prato_a', 'prato_b'}
                print(f"{CategoryLogger.COLORS['prato_a']}✅ Hunting for all Prato tickets (A + B){CategoryLogger.COLORS['reset']}")
                break
                
            choices = [s.strip() for s in selection.split(',')]
            
            # Check if user selected "all"
            if '6' in choices:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
                print(f"{CategoryLogger.COLORS['prato_a']}✅ Hunting for ALL ticket types{CategoryLogger.COLORS['reset']}")
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
                    print(f"{CategoryLogger.COLORS['alert']}❌ Invalid choice: {choice}{CategoryLogger.COLORS['reset']}")
            
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
                        selected_display.append(f"{color}{display_name}{CategoryLogger.COLORS['reset']}")
                
                print(f"\n{CategoryLogger.COLORS['prato_a']}✅ Selected: {', '.join(selected_display)}{CategoryLogger.COLORS['reset']}")
                break
            else:
                print(f"{CategoryLogger.COLORS['alert']}Please enter valid choices (1-6){CategoryLogger.COLORS['reset']}")

    def configure(self):
        """Configure bot settings"""
        print(f"\n🤖 FANSALE BOT V7 CONFIGURATION")
        print("=" * 50)
        
        # Show current stats
        self.show_statistics_dashboard()
        
        # Check for 2captcha
        if self.captcha_solver and self.captcha_solver.api_key:
            print(f"\n✅ 2Captcha configured")
        else:
            print(f"\n⚠️  No 2Captcha key - manual CAPTCHA only")
        
        # Number of browsers
        while True:
            try:
                num = input(f"\n🌐 Number of browsers (1-8, default 2): ").strip()
                if not num:
                    self.num_browsers = 2
                    break
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 8:
                    break
                print("Please enter 1-8")
            except ValueError:
                print("Invalid number")
        
        # Max tickets
        while True:
            try:
                max_t = input(f"\n🎫 Max tickets to reserve (1-4, default 2): ").strip()
                if not max_t:
                    self.max_tickets = 2
                    break
                self.max_tickets = int(max_t)
                if 1 <= self.max_tickets <= 4:
                    break
                print("Please enter 1-4")
            except ValueError:
                print("Invalid number")
        
        # Configure ticket type filters
        self.configure_ticket_filters()
        
        # Summary
        print(f"\n📋 Configuration Summary:")
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
    def run(self):
        """Main execution with enhanced tracking"""
        try:
            # Configure
            self.configure()
            
            # Create browsers
            print(f"\n{CategoryLogger.COLORS['bold']}🚀 Starting {self.num_browsers} browser(s)...{CategoryLogger.COLORS['reset']}")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
                # Staggered browser creation
                if i < self.num_browsers:
                    time.sleep(random.uniform(3, 7))
            
            if not self.browsers:
                self.category_logger.log_ticket('system', "❌ No browsers created", 'error')
                return

            self.category_logger.log_ticket('system', f"✅ {len(self.browsers)} browser(s) ready!")
            
            # Show tip about monitoring
            print(f"\n{CategoryLogger.COLORS['system']}💡 TIP: Browsers are positioned for multi-monitor setups{CategoryLogger.COLORS['reset']}")
            print(f"{CategoryLogger.COLORS['system']}   Move them to your preferred monitors if needed{CategoryLogger.COLORS['reset']}")
            print(f"\n{CategoryLogger.COLORS['alert']}⚠️  CAPTCHA ALERT: If CAPTCHA appears, it will be handled{CategoryLogger.COLORS['reset']}")
            print(f"{CategoryLogger.COLORS['prato_a']}   Auto-solve if configured, or manual alert{CategoryLogger.COLORS['reset']}")
            print(f"{CategoryLogger.COLORS['system']}📢 POPUPS: Will be checked every {self.config.popup_check_interval/60:.1f} minutes{CategoryLogger.COLORS['reset']}")
            print(f"{CategoryLogger.COLORS['prato_a']}📸 IMAGES: Verified loading on all browsers{CategoryLogger.COLORS['reset']}")
            
            input(f"\n{CategoryLogger.COLORS['bold']}✋ Press Enter to START HUNTING...{CategoryLogger.COLORS['reset']}")
            
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
            print(f"\n{CategoryLogger.COLORS['prato_a']}{CategoryLogger.COLORS['bold']}🎯 HUNTING ACTIVE! Press Ctrl+C to stop.{CategoryLogger.COLORS['reset']}\n")
            
            try:
                last_update = time.time()
                while self.tickets_secured < self.max_tickets:
                    time.sleep(1)
                    
                    # Status update every 60 seconds
                    if time.time() - last_update > 60:
                        self.show_statistics_dashboard()
                        last_update = time.time()
                    
                self.category_logger.log_ticket('system', 
                    f"\n{CategoryLogger.COLORS['prato_a']}{CategoryLogger.COLORS['bold']}🎉 SUCCESS! {self.tickets_secured} tickets secured!{CategoryLogger.COLORS['reset']}")
                
            except KeyboardInterrupt:
                self.category_logger.log_ticket('system', 
                    f"\n{CategoryLogger.COLORS['settore']}🛑 Stopping...{CategoryLogger.COLORS['reset']}")
                
        except Exception as e:
            self.category_logger.log_ticket('system', f"Fatal error: {e}", 'error')
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
                    pass
            
            # Show final statistics
            print(f"\n{CategoryLogger.COLORS['bold']}{CategoryLogger.COLORS['system']}📊 FINAL SESSION STATISTICS{CategoryLogger.COLORS['reset']}")
            self.show_statistics_dashboard()


def main():
    """Entry point"""
    print(f"{CategoryLogger.COLORS['bold']}{'=' * 70}{CategoryLogger.COLORS['reset']}")
    print(f"{CategoryLogger.COLORS['bold']}{CategoryLogger.COLORS['system']}🎫 FANSALE BOT V7{CategoryLogger.COLORS['reset']}")
    print(f"{CategoryLogger.COLORS['bold']}{'=' * 70}{CategoryLogger.COLORS['reset']}")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
        import requests
    except ImportError as e:
        print(f"\n{CategoryLogger.COLORS['alert']}❌ Missing dependency: {e}{CategoryLogger.COLORS['reset']}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium requests")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    
    # Load configuration
    config_path = Path("bot_config_v7.json")
    config = BotConfig.from_file(config_path)
    
    # Check for 2captcha key
    twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY', '')
    if twocaptcha_key:
        config.twocaptcha_api_key = twocaptcha_key
        config.auto_solve_captcha = True
        print(f"\n✅ 2Captcha API key found")
    
    # Save default config if not exists
    if not config_path.exists():
        config.save(config_path)
        print(f"\n📝 Created default configuration: {config_path}")
    
    # Check for target URL
    if not os.getenv('FANSALE_TARGET_URL'):
        print(f"\n⚠️  No target URL in .env file")
        print("Using default URL. To change, add to .env:")
        print("FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/...")
    else:
        print(f"\n✅ Target URL loaded from .env")
    
    # Run bot
    bot = FanSaleBotV7(config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print(f"\n👋 Graceful shutdown...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Fatal error in main")
    finally:
        print(f"\n✅ Thank you for using FanSale Bot!")


if __name__ == "__main__":
    # Fix for Python 3.13 multiprocessing
    import multiprocessing
    multiprocessing.freeze_support()
    main()