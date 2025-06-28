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
from collections import defaultdict
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
    refresh_interval: int = 20
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
            data['twocaptcha_api_key'] = "c58050aca5076a2a26ba2eff1c429d4d"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

# ==================== Enhanced Logging ====================

class Logger:
    """Simple colored logging for better visibility"""
    
    # ANSI color codes
    GREEN = '\033[92m'      # Prato A
    BLUE = '\033[94m'       # Prato B  
    YELLOW = '\033[93m'     # Settore
    GRAY = '\033[90m'       # Other
    CYAN = '\033[96m'       # System
    RED = '\033[91m'        # Alert/Error
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    # Emojis for different message types
    EMOJI = {
        'prato_a': '🎫',
        'prato_b': '🎫', 
        'settore': '🎫',
        'other': '🎫',
        'system': '⚙️',
        'alert': '🚨',
        'success': '✅',
        'error': '❌',
        'info': '📢'
    }
    
    @staticmethod
    def get_color(category: str) -> str:
        """Get color for category"""
        colors = {
            'prato_a': Logger.GREEN,
            'prato_b': Logger.BLUE,
            'settore': Logger.YELLOW,
            'other': Logger.GRAY,
            'system': Logger.CYAN,
            'error': Logger.RED,
            'alert': Logger.RED
        }
        return colors.get(category, Logger.RESET)
    
    @staticmethod
    def log(message: str, category: str = 'system', emoji: str = None):
        """Simple colored logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = Logger.get_color(category)
        emoji = emoji or Logger.EMOJI.get(category, '')
        print(f"{color}{timestamp} {emoji} {message}{Logger.RESET}")
    
    @staticmethod
    def alert(message: str):
        """Alert message with emphasis"""
        Logger.log(f"{Logger.BOLD}{message}", 'alert', '🚨')
        # Audio alert
        for _ in range(3):
            print('\a')
            time.sleep(0.3)

# ==================== Statistics Manager ====================

class StatsManager:
    """Simple statistics manager with persistence"""
    def __init__(self, stats_file="fansale_stats_v7.json"):
        self.stats_file = Path(stats_file)
        self.lock = threading.Lock()
        
        # Always start with clean session stats
        self.session_start = time.time()
        self.session_checks = 0
        
        # Load or initialize persistent stats
        self.load_stats()
        
    def load_stats(self):
        """Load stats from file or initialize"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    # Ensure all required fields exist
                    self.all_time_stats = {
                        'total_checks': data.get('all_time', {}).get('total_checks', 0),
                        'tickets_found': {
                            'prato_a': data.get('all_time', {}).get('tickets_found', {}).get('prato_a', 0),
                            'prato_b': data.get('all_time', {}).get('tickets_found', {}).get('prato_b', 0),
                            'settore': data.get('all_time', {}).get('tickets_found', {}).get('settore', 0),
                            'other': data.get('all_time', {}).get('tickets_found', {}).get('other', 0),
                            'total': data.get('all_time', {}).get('tickets_found', {}).get('total', 0)
                        },
                        'purchases_made': data.get('all_time', {}).get('purchases_made', 0),
                        'captchas_encountered': data.get('all_time', {}).get('captchas_encountered', 0),
                        'blocks_encountered': data.get('all_time', {}).get('blocks_encountered', 0)
                    }
                    self.seen_tickets = set(data.get('seen_tickets', []))
            except Exception as e:
                print(f"Error loading stats: {e}")
                self.initialize_stats()
        else:
            self.initialize_stats()
    
    def initialize_stats(self):
        """Initialize fresh stats"""
        self.all_time_stats = {
            'total_checks': 0,
            'tickets_found': {
                'prato_a': 0,
                'prato_b': 0,
                'settore': 0,
                'other': 0,
                'total': 0
            },
            'purchases_made': 0,
            'captchas_encountered': 0,
            'blocks_encountered': 0
        }
        self.seen_tickets = set()
    
    def save_stats(self):
        """Save stats to file"""
        try:
            with self.lock:
                data = {
                    'all_time': self.all_time_stats,
                    'seen_tickets': list(self.seen_tickets),
                    'last_updated': datetime.now().isoformat()
                }
                with open(self.stats_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")
    
    def increment_checks(self):
        """Increment check counter"""
        with self.lock:
            self.session_checks += 1
            self.all_time_stats['total_checks'] += 1
            
    def found_ticket(self, category: str, ticket_hash: str):
        """Record a new ticket found - returns True if new"""
        with self.lock:
            if ticket_hash not in self.seen_tickets:
                self.seen_tickets.add(ticket_hash)
                self.all_time_stats['tickets_found'][category] += 1
                self.all_time_stats['tickets_found']['total'] += 1
                # Save immediately for persistence
                self.save_stats()
                return True
            return False
            
    def made_purchase(self):
        """Record a purchase"""
        with self.lock:
            self.all_time_stats['purchases_made'] += 1
            self.save_stats()
            
    def encountered_captcha(self):
        """Record CAPTCHA encounter"""
        with self.lock:
            self.all_time_stats['captchas_encountered'] += 1
            
    def encountered_block(self):
        """Record block encounter"""
        with self.lock:
            self.all_time_stats['blocks_encountered'] += 1
    
    def get_session_runtime(self):
        """Get current session runtime"""
        return time.time() - self.session_start
        
    def get_session_checks_per_minute(self):
        """Get session checks per minute"""
        runtime = self.get_session_runtime()
        return (self.session_checks / runtime * 60) if runtime > 0 else 0
    
    def get_ticket_stats(self):
        """Get formatted ticket statistics"""
        return self.all_time_stats['tickets_found']
    
    def print_summary(self):
        """Print simple stats summary"""
        runtime = self.get_session_runtime()
        runtime_str = f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"
        checks_per_min = self.get_session_checks_per_minute()
        tickets = self.get_ticket_stats()
        
        print(f"{Logger.CYAN}📊 Session: {runtime_str} | "
              f"Checks: {self.session_checks} ({checks_per_min:.1f}/min) | "
              f"Found: {Logger.GREEN}A:{tickets['prato_a']}{Logger.CYAN} "
              f"{Logger.BLUE}B:{tickets['prato_b']}{Logger.CYAN} "
              f"{Logger.YELLOW}S:{tickets['settore']}{Logger.CYAN} | "
              f"Total: {tickets['total']}{Logger.RESET}")

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

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Simple retry decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# ==================== Main Bot Class ====================

class FanSaleBotV7:
    """Ultimate FanSale Bot with all fixes and enhancements"""
    
    def __init__(self, config: Optional[BotConfig] = None):
        # Load configuration
        self.config = config or BotConfig()
        
        # Use correct environment variable name
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
        
        # Configuration
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_types_to_hunt = set()  # Properly initialized
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Ticket tracking is now handled by StatsManager
        
        # CAPTCHA tracking
        self.captcha_solved_time = {}
        self.captcha_grace_period = self.config.captcha_grace_period
        
        # Statistics with persistence
        self.stats = StatsManager()
        
        # Session tracking
        self.session_start_time = time.time()
        
        # 2Captcha solver
        api_key = self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY', '')
        if api_key:
            self.captcha_solver = TwoCaptchaSolver(api_key)
            self.auto_solve = self.config.auto_solve_captcha
            Logger.log(f"2Captcha configured with API key: {api_key[:8]}...", 'system', '✅')
        else:
            self.captcha_solver = None
            self.auto_solve = False
            Logger.log("No 2Captcha API key - manual CAPTCHA solving only", 'system', '⚠️')


    
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
    
    def extract_full_ticket_info(self, ticket_element: WebElement) -> Dict:
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
            Logger.log( f"Error extracting ticket info: {e}", 'error')
            return {
                'raw_text': str(ticket_element.text) if hasattr(ticket_element, 'text') else '',
                'category': 'other',
                'offer_id': ''
            }
    
    def log_new_ticket(self, ticket_info: Dict, browser_id: int):
        """Log newly discovered ticket - simple and effective"""
        category = ticket_info['category']
        
        # Simple category display
        category_display = {
            'prato_a': 'PRATO A',
            'prato_b': 'PRATO B', 
            'settore': 'SETTORE',
            'other': 'OTHER'
        }.get(category, category.upper())
        
        # Extract price if available
        price_match = re.search(r'€\s*([0-9.,]+)', ticket_info['raw_text'])
        price = price_match.group(1) if price_match else 'N/A'
        
        # Log based on whether we're hunting this type
        if category in self.ticket_types_to_hunt:
            Logger.alert(f"🎯 NEW {category_display} TICKET! Hunter {browser_id} | €{price}")
        else:
            Logger.log(f"Found {category_display} | €{price} | Hunter {browser_id}", category)
    
    def check_captcha_status(self, browser_id: int) -> bool:
        """Check if browser is within CAPTCHA grace period"""
        if browser_id in self.captcha_solved_time:
            time_since_solved = time.time() - self.captcha_solved_time[browser_id]
            if time_since_solved < self.captcha_grace_period:
                remaining = self.captcha_grace_period - time_since_solved
                Logger.log( 
                    f"Hunter {browser_id}: CAPTCHA grace period active ({remaining:.0f}s remaining)")
                return True
        return False
    
    def mark_captcha_solved(self, browser_id: int):
        """Mark CAPTCHA as solved for this browser"""
        self.captcha_solved_time[browser_id] = time.time()
        self.stats.encountered_captcha()
        Logger.log( 
            f"✅ Hunter {browser_id}: CAPTCHA solved! Grace period active for {self.captcha_grace_period}s")
    
    def dismiss_popups(self, driver: uc.Chrome, browser_id: int) -> int:
        """Enhanced popup dismissal - better handling of FanSale popups"""
        dismissed_count = 0
        
        try:
            # Priority 1: "Carica Offerte" button - multiple selectors for better detection
            carica_selectors = [
                "button.js-BotProtectionModalButton1",
                "button:contains('Carica')",
                "button[class*='BotProtection']",
                "div.BotProtectionModal button",
                "button[onclick*='carica']"
            ]
            
            for selector in carica_selectors:
                try:
                    if ':contains' in selector:
                        # Use XPath for text content
                        elements = driver.find_elements(By.XPATH, "//button[contains(text(), 'Carica')]")
                        for carica in elements:
                            if carica.is_displayed():
                                # Try multiple click methods
                                try:
                                    driver.execute_script("arguments[0].click();", carica)
                                except:
                                    try:
                                        carica.click()
                                    except:
                                        ActionChains(driver).move_to_element(carica).click().perform()
                                Logger.log(f"Hunter {browser_id}: Clicked 'Carica' button!", 'system', '📢')
                                dismissed_count += 1
                                break
                    else:
                        carica = driver.find_element(By.CSS_SELECTOR, selector)
                        if carica.is_displayed():
                            driver.execute_script("arguments[0].click();", carica)
                            Logger.log(f"Hunter {browser_id}: Clicked 'Carica Offerte' button", 'system', '📢')
                            dismissed_count += 1
                            time.sleep(0.3)  # Small delay to let page update
                            break
                except:
                    continue
            
            # Priority 2: Generic close buttons if no FanSale-specific popup
            if dismissed_count == 0:
                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR, 
                        "button[aria-label*='close' i], button[aria-label*='chiudi' i], button[class*='close']")
                    if close_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", close_btn)
                        dismissed_count += 1
                except:
                    pass
                
        except Exception as e:
            Logger.log(f"Error in dismiss_popups: {e}", 'error')
            
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
                    Logger.log( "🤖 CAPTCHA detected!")
                    
                    # Try to get sitekey for reCAPTCHA
                    sitekey = None
                    if 'recaptcha' in selector:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        sitekey = elem.get_attribute('data-sitekey')
                    
                    return True, sitekey, driver.current_url
            
            return False, None, None
            
        except Exception as e:
            Logger.log( f"Error detecting CAPTCHA: {e}", 'error')
            return False, None, None
    
    def solve_captcha_automatically(self, driver: uc.Chrome, sitekey: str, pageurl: str, browser_id: int) -> bool:
        """Attempt to solve CAPTCHA automatically using 2captcha"""
        if not self.captcha_solver or not sitekey:
            Logger.log( 
                f"Cannot auto-solve: solver={bool(self.captcha_solver)}, sitekey={bool(sitekey)}", 'warning')
            return False
            
        Logger.log( f"🤖 Hunter {browser_id}: Attempting automatic CAPTCHA solve...")
        
        token = self.captcha_solver.solve_recaptcha(sitekey, pageurl)
        if not token:
            Logger.log( "Failed to get token from 2captcha", 'error')
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
                # Auto-solve successful
                self.mark_captcha_solved(browser_id)
                Logger.log( f"✅ CAPTCHA token injected successfully!")
                return True
            else:
                Logger.log( 
                    "Failed to inject CAPTCHA token - no suitable element found", 'error')
                return False
                
        except Exception as e:
            Logger.log( f"Failed to inject CAPTCHA token: {e}", 'error')
            return False
    
    def wait_for_captcha_solve(self, driver: uc.Chrome, browser_id: int, timeout: int = 120) -> bool:
        """Wait for user to solve CAPTCHA manually or solve automatically"""
        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
        
        if not captcha_detected:
            return True
            
        # Increment CAPTCHA counter
        self.stats.encountered_captcha()
        
        # Try automatic solving first if enabled
        if self.auto_solve and sitekey:
            Logger.log( f"🤖 Attempting automatic CAPTCHA solve with 2captcha...")
            if self.solve_captcha_automatically(driver, sitekey, pageurl, browser_id):
                return True
            else:
                Logger.log( "Automatic solving failed, falling back to manual", 'warning')
                
        # Fall back to manual solving
        Logger.log( f"\n{'='*60}")
        Logger.log( f"🤖 CAPTCHA DETECTED - Hunter {browser_id}")
        Logger.log( f"{'='*60}")
        Logger.log( f"⚠️  MANUAL ACTION REQUIRED!")
        Logger.log( f"Please solve the CAPTCHA in Browser {browser_id}")
        Logger.log( f"Waiting up to {timeout} seconds...")
        Logger.log( f"{'='*60}\n")
        
        # Play alert sound
        for _ in range(5):
            print('\a')
            time.sleep(0.5)
        
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            # Check if CAPTCHA is still present
            if not self.detect_captcha(driver)[0]:
                Logger.log( f"✅ CAPTCHA solved in Browser {browser_id}!")
                self.mark_captcha_solved(browser_id)
                return True
                
            # Also check if we've moved to a new page (indicating success)
            try:
                current_url = driver.current_url.lower()
                if any(x in current_url for x in ['conferma', 'checkout', 'payment', 'cart']):
                    Logger.log( f"✅ Purchase proceeding in Browser {browser_id}!")
                    self.mark_captcha_solved(browser_id)
                    return True
            except:
                pass
                
            time.sleep(check_interval)
            
        Logger.log( f"❌ CAPTCHA timeout in Browser {browser_id}", 'error')
        return False
    
    @retry(max_attempts=3, delay=2.0)
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create browser with undetected-chromedriver"""
        Logger.log( f"🚀 Creating Browser {browser_id}...")
        
        try:
            # Create fresh ChromeOptions for each attempt (cannot be reused)
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
            
            # Additional options for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Create driver with proper version handling
            driver = None
            chrome_version_attempts = [None, 137, 138, 136, 135, 131, 130]
            last_error = None
            
            for version in chrome_version_attempts:
                try:
                    # Create new options for each version attempt
                    if version is not None:
                        # Need fresh options for each attempt
                        options = uc.ChromeOptions()
                        options.add_argument('--disable-blink-features=AutomationControlled')
                        options.add_argument(f'--window-position={x},{y}')
                        options.add_argument(f'--window-size={window_width},{window_height}')
                        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
                        options.add_argument('--no-sandbox')
                        options.add_argument('--disable-dev-shm-usage')
                        options.add_argument('--disable-gpu')
                        options.add_argument('--disable-features=VizDisplayCompositor')
                        
                        Logger.log( 
                            f"Trying Chrome version {version}...")
                        driver = uc.Chrome(
                            options=options,
                            version_main=version,
                            use_subprocess=True,
                            suppress_welcome=True
                        )
                    else:
                        Logger.log( 
                            "Trying with auto-detected Chrome version...")
                        driver = uc.Chrome(
                            options=options,
                            use_subprocess=True,
                            suppress_welcome=True
                        )
                    
                    # If we get here, browser was created successfully
                    break
                    
                except Exception as e:
                    last_error = e
                    if "This version of ChromeDriver only supports Chrome version" in str(e):
                        # Extract the required version from error message
                        import re
                        match = re.search(r'Chrome version (\d+)', str(e))
                        if match:
                            required_version = int(match.group(1))
                            if required_version not in chrome_version_attempts:
                                chrome_version_attempts.insert(1, required_version)
                    continue
            
            if driver is None:
                raise Exception(f"Failed to create browser after trying versions: {chrome_version_attempts}. Last error: {last_error}")
            
            # Set timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            Logger.log( 
                f"✅ Browser {browser_id} created at position ({x}, {y})")
            
            return driver
            
        except Exception as e:
            Logger.log( 
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
        """Clear browser data to bypass blocks - with timeout handling"""
        try:
            Logger.log( 
                f"🧹 Clearing data for Browser {browser_id}...")
            
            # Set shorter timeout for cookie operations
            driver.set_page_load_timeout(10)
            
            try:
                # Try to clear cookies with timeout
                driver.delete_all_cookies()
            except:
                # If cookies fail, continue anyway
                pass
            
            try:
                # Navigate to blank page
                driver.get("about:blank")
                time.sleep(0.5)
            except:
                # If navigation fails, try to refresh
                try:
                    driver.refresh()
                except:
                    pass
            
            # Restore normal timeout
            driver.set_page_load_timeout(30)
            
            Logger.log( f"✅ Browser {browser_id} data cleared")
            self.stats.encountered_block()
            
        except Exception as e:
            Logger.log( f"Failed to clear browser data: {e}", 'error')
            # Don't let this stop the bot
            try:
                driver.set_page_load_timeout(30)
            except:
                pass
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop with all V5 enhancements"""
        Logger.log( f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to event page
        Logger.log( f"📍 Navigating to: {self.target_url}")
        page_start = time.time()
        driver.get(self.target_url)
        page_load_time = time.time() - page_start
        # Removed performance tracking - not actionable
        Logger.log( f"📄 Page loaded in {page_load_time:.2f}s")
        
        # Initial popup dismissal - enhanced will handle Carica button
        time.sleep(2)  # Give page time to fully load
        initial_popups = self.dismiss_popups(driver, browser_id)
        
        # If we found popups, wait and check again
        if initial_popups > 0:
            time.sleep(1)
            additional = self.dismiss_popups(driver, browser_id)
            initial_popups += additional
        
        Logger.log( f"📢 Dismissed {initial_popups} initial popups")
        
        # Verify images are loading - REMOVED: Unnecessary check that adds delay
        # self.verify_image_loading(driver, browser_id)
        
        check_count = 0
        # Staggered refresh times for each browser
        last_refresh = time.time() - (browser_id * 5)  # Stagger initial refreshes
        refresh_interval = 15 + random.randint(-3, 3)  # Faster refresh: 12-18 seconds
        
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
                self.stats.increment_checks()
                
                
                # Popup check - more aggressive checking
                # Check every 10 seconds OR if we haven't found tickets in a while
                popup_check_interval = 10 if local_stats['found'] == 0 else self.config.popup_check_interval
                if time.time() - last_popup_check > popup_check_interval:
                    dismissed = self.dismiss_popups(driver, browser_id)
                    if dismissed > 0:
                        Logger.log( f"Dismissed {dismissed} popups")
                    last_popup_check = time.time()
                
                # Check for 404 blocks
                if self.is_blocked(driver):
                    Logger.log( 
                        f"⚠️ Hunter {browser_id}: Block detected!", 'warning')
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(random.uniform(2.5, 3.5))
                    self.dismiss_popups(driver, browser_id)  # Dismiss any new popups
                    continue
                
                # Session refresh every 15 minutes - skip for now to maximize speed
                # The page refresh every 15 seconds is sufficient
                
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
                            Logger.log( 
                                f"Found tickets with alternative selector: {selector}")
                            break
                
                # Check time removed - not actionable
                
                if tickets:
                    # Check CAPTCHA grace period
                    in_grace_period = self.check_captcha_status(browser_id)
                    
                    for ticket in tickets:
                        try:
                            # Extract full ticket information
                            ticket_info = self.extract_full_ticket_info(ticket)
                            ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                            
                            # Check if this is a new ticket using StatsManager
                            category = ticket_info['category']
                            is_new_ticket = self.stats.found_ticket(category, ticket_hash)
                            
                            if is_new_ticket:
                                # New ticket discovered!
                                local_stats[category] += 1
                                local_stats['found'] += 1
                                
                                # Log the new ticket with full details
                                self.log_new_ticket(ticket_info, browser_id)
                                
                                # FIX #2: Properly check if we should purchase
                                if category in self.ticket_types_to_hunt:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.max_tickets:
                                            # If in grace period, log it
                                            if in_grace_period:
                                                Logger.log( 
                                                    f"🚀 Hunter {browser_id}: CAPTCHA grace period active - fast purchase!")
                                            
                                            if self.purchase_ticket(driver, ticket, browser_id):
                                                self.tickets_secured += 1
                                                self.stats.made_purchase()
                                                
                                                if self.tickets_secured >= self.max_tickets:
                                                    Logger.log( 
                                                        f"🎉 Max tickets secured!")
                                                    return
                                                    
                        except Exception as e:
                            continue
                
                # Periodically test CAPTCHA grace period
                if in_grace_period and check_count - last_captcha_check > 20:  # Every ~minute
                    Logger.log( 
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
                    # Quick popup check after refresh
                    self.dismiss_popups(driver, browser_id)
                
                # Progress update every 10 seconds
                if check_count % 10 == 0 or (time.time() - self.session_start_time) % 10 < 1:
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
                    
                    Logger.log( 
                        f"📊 Hunter {browser_id}: {' | '.join(status_parts)}")
                    
            except TimeoutException:
                Logger.log( 
                    f"Hunter {browser_id}: Page timeout, refreshing...", 'warning')
                driver.refresh()
                time.sleep(random.uniform(1.5, 2.5))
                self.dismiss_popups(driver, browser_id)
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    Logger.log( 
                        f"Hunter {browser_id}: Session died", 'error')
                    break
                Logger.log( 
                    f"Hunter {browser_id}: Browser error, continuing...", 'error')
                time.sleep(5)
                
            except Exception as e:
                Logger.log( 
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
                                Logger.log( 
                                    f"✅ Hunter {browser_id}: Clicked '{text}' on checkout page")
                                return True
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed() and element.is_enabled():
                            # If it's a quantity selector, ensure it's set to 1
                            if 'quantity' in selector.lower() or 'quantita' in selector.lower():
                                driver.execute_script("arguments[0].value = '1';", element)
                                Logger.log( 
                                    f"✅ Hunter {browser_id}: Set quantity to 1")
                            else:
                                driver.execute_script("arguments[0].click();", element)
                                Logger.log( 
                                    f"✅ Hunter {browser_id}: Clicked checkout element")
                                return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            Logger.log( 
                f"Error handling checkout page: {e}", 'error')
            return False

    @retry(max_attempts=2, delay=0.5)
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket with enhanced interaction"""
        try:
            Logger.log( 
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
                Logger.log( 
                    f"✅ Hunter {browser_id}: Clicked ticket via JavaScript")
            except Exception as e1:
                # Method 2: Click on the specific FanSale link/button inside ticket
                try:
                    # Look for the specific FanSale ticket link structure
                    ticket_link = ticket_element.find_element(By.CSS_SELECTOR, "a.Button-inOfferEntryList, a[id*='detailBShowOfferButton']")
                    driver.execute_script("arguments[0].click();", ticket_link)
                    click_success = True
                    Logger.log( 
                        f"✅ Hunter {browser_id}: Clicked FanSale ticket link")
                except:
                    # Fallback to any clickable child
                    try:
                        clickable_child = ticket_element.find_element(By.CSS_SELECTOR, "a, button, [role='button']")
                        driver.execute_script("arguments[0].click();", clickable_child)
                        click_success = True
                        Logger.log( 
                            f"✅ Hunter {browser_id}: Clicked ticket child element")
                    except:
                        pass
                    # Method 3: Action chains
                    try:
                        actions = ActionChains(driver)
                        actions.move_to_element(ticket_element).click().perform()
                        click_success = True
                        Logger.log( 
                            f"✅ Hunter {browser_id}: Clicked ticket via ActionChains")
                    except:
                        # Method 4: Direct click
                        try:
                            ticket_element.click()
                            click_success = True
                            Logger.log( 
                                f"✅ Hunter {browser_id}: Clicked ticket directly")
                        except:
                            pass
            
            if not click_success:
                Logger.log( 
                    f"Failed to click ticket element", 'warning')
                return False
                
            time.sleep(random.uniform(0.8, 1.2))
            
            # Dismiss any new popups that might appear
            self.dismiss_popups(driver, browser_id)
            
            # Essential buy button selectors based on FanSale HTML
            buy_selectors = [
                # Priority 1: FanSale-specific (from handlersfansale.md)
                "button[data-qa='buyNowButton']",
                
                # Priority 2: Common Italian buy buttons
                "button:contains('Acquista')",
                "button:contains('Compra')",
                "button:contains('Procedi')",
                
                # Priority 3: Class-based selectors
                "button[class*='buy']",
                "button[class*='acquista']",
                
                # Priority 4: Generic submit buttons
                "button[type='submit']",
                "input[type='submit']"
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
                        Logger.log( 
                            f"🎯 Hunter {browser_id}: Found buy button with selector: {selector}")
                        
                        # Log button details for debugging
                        btn_text = buy_btn.text.strip() if buy_btn.text else "No text"
                        btn_class = buy_btn.get_attribute('class') or "No class"
                        Logger.log( 
                            f"   Button text: '{btn_text}', Classes: '{btn_class}'")
                        
                        # Scroll to buy button
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                        time.sleep(0.3)
                        
                        # Try to click
                        try:
                            driver.execute_script("arguments[0].click();", buy_btn)
                        except:
                            buy_btn.click()
                            
                        Logger.log( 
                            f"✅ Hunter {browser_id}: Buy button clicked!")
                        
                        # Store current URL to detect navigation
                        initial_url = driver.current_url
                        
                        # Wait for page change or CAPTCHA
                        page_changed = self.wait_for_page_change(driver, initial_url, timeout=3)
                        
                        if page_changed:
                            Logger.log( 
                                f"🎯 Hunter {browser_id}: Navigated to: {driver.current_url}")
                            
                            # Check if we reached checkout/cart page
                            current_url = driver.current_url.lower()
                            if any(keyword in current_url for keyword in ['carrello', 'cart', 'checkout', 'conferma', 'payment']):
                                Logger.log( 
                                    f"🛒 Hunter {browser_id}: Reached checkout page!")
                                # Play success sound
                                print('' * 5)
                        else:
                            # Page didn't change, wait a bit more
                            time.sleep(1)
                        
                        # Check for CAPTCHA
                        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
                        if captcha_detected:
                            Logger.log( 
                                f"🤖 Hunter {browser_id}: CAPTCHA detected after buy click!")
                            self.stats.encountered_captcha()
                            
                            # Try to solve
                            if self.wait_for_captcha_solve(driver, browser_id):
                                Logger.log( 
                                    f"✅ Hunter {browser_id}: Continuing after CAPTCHA")
                                time.sleep(1)
                            else:
                                Logger.log( 
                                    f"❌ Hunter {browser_id}: CAPTCHA not solved", 'warning')
                                return False
                        
                        # Play success alarm sound
                        print('\a' * 3)  # System beep
                        
                        # Take screenshot
                        screenshot_path = f"screenshots/ticket_{browser_id}_{int(time.time())}.png"
                        Path("screenshots").mkdir(exist_ok=True)
                        driver.save_screenshot(screenshot_path)
                        Logger.log( 
                            f"📸 Screenshot saved: {screenshot_path}")
                        
                        return True
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    continue
                    
            Logger.log( 
                f"Hunter {browser_id}: No buy button found", 'warning')
            
            # Take debug screenshot
            debug_path = f"screenshots/debug_{browser_id}_{int(time.time())}.png"
            driver.save_screenshot(debug_path)
            Logger.log( f"📸 Debug screenshot: {debug_path}")
            
            return False
            
        except Exception as e:
            Logger.log( f"Purchase failed: {e}", 'error')
            return False
    
    def show_statistics_dashboard(self):
        """Simple live statistics display"""
        # Just use the simple print_summary method
        self.stats.print_summary()
    
    def configure_ticket_filters(self):
        """Allow user to select which ticket types to hunt for"""
        print(f"\n{Logger.BOLD}🎯 SELECT TICKET TYPES TO HUNT{Logger.RESET}")
        print("=" * 50)
        
        # Available ticket types
        available_types = {
            '1': ('prato_a', 'Prato A', Logger.GREEN),
            '2': ('prato_b', 'Prato B', Logger.BLUE),
            '3': ('prato_all', 'All Prato (A + B)', Logger.CYAN),
            '4': ('settore', 'Settore', Logger.YELLOW),
            '5': ('other', 'Other/Unknown', Logger.GRAY),
            '6': ('all', 'ALL ticket types', Logger.BOLD)
        }
        
        print("\nAvailable ticket categories:")
        for key, (_, display, color) in available_types.items():
            if key == '3':
                print(f"  {color}{key}. {display}{Logger.RESET} ⭐")
            elif key == '4':
                print(f"  {color}{key}. {display}{Logger.RESET} (Seated: Fila/Posto/Anello)")
            elif key == '6':
                print(f"\n  {color}{key}. {display}{Logger.RESET}")
            else:
                print(f"  {color}{key}. {display}{Logger.RESET}")
        
        while True:
            selection = input(f"\n{Logger.BOLD}Enter your choices (e.g., '1,2' or '3' for all Prato):{Logger.RESET} ").strip()
            
            if not selection:
                # Default to all Prato types
                self.ticket_types_to_hunt = {'prato_a', 'prato_b'}
                print(f"{Logger.GREEN}✅ Hunting for all Prato tickets (A + B){Logger.RESET}")
                break
                
            choices = [s.strip() for s in selection.split(',')]
            
            # Check if user selected "all"
            if '6' in choices:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
                print(f"{Logger.GREEN}✅ Hunting for ALL ticket types{Logger.RESET}")
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
                    print(f"{Logger.RED}❌ Invalid choice: {choice}{Logger.RESET}")
            
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
                        selected_display.append(f"{color}{display_name}{Logger.RESET}")
                
                print(f"\n{Logger.GREEN}✅ Selected: {', '.join(selected_display)}{Logger.RESET}")
                break
            else:
                print(f"{Logger.RED}Please enter valid choices (1-6){Logger.RESET}")

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
            print(f"\n{Logger.BOLD}🚀 Starting {self.num_browsers} browser(s)...{Logger.RESET}")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
                # Staggered browser creation
                if i < self.num_browsers:
                    time.sleep(random.uniform(3, 7))
            
            if not self.browsers:
                Logger.log( "❌ No browsers created", 'error')
                return

            Logger.log( f"✅ {len(self.browsers)} browser(s) ready!")
            
            # Quick startup info
            print(f"{Logger.CYAN}💡 Browsers positioned for multi-monitor setup{Logger.RESET}")
            if self.captcha_solver:
                print(f"{Logger.GREEN}✅ Auto-CAPTCHA solving enabled{Logger.RESET}")
            else:
                print(f"{Logger.YELLOW}⚠️  Manual CAPTCHA solving required{Logger.RESET}")
            
            input(f"\n{Logger.BOLD}✋ Press Enter to START HUNTING...{Logger.RESET}")
            
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
            print(f"\n{Logger.GREEN}{Logger.BOLD}🎯 HUNTING ACTIVE! Press Ctrl+C to stop.{Logger.RESET}\n")
            
            try:
                last_update = time.time()
                dashboard_interval = 30  # Show dashboard every 30 seconds
                
                while self.tickets_secured < self.max_tickets:
                    time.sleep(1)
                    
                    # Status update every 30 seconds
                    if time.time() - last_update > dashboard_interval:
                        self.show_statistics_dashboard()
                        last_update = time.time()
                    
                Logger.log( 
                    f"\n{Logger.GREEN}{Logger.BOLD}🎉 SUCCESS! {self.tickets_secured} tickets secured!{Logger.RESET}")
                
            except KeyboardInterrupt:
                Logger.log( 
                    f"\n{Logger.YELLOW}🛑 Stopping...{Logger.RESET}")
                
        except Exception as e:
            Logger.log( f"Fatal error: {e}", 'error')
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            self.shutdown_event.set()
            

            
            for driver in self.browsers:
                try:
                    driver.quit()
                except Exception as e:
                    pass
            
            # Save final stats
            if hasattr(self, 'stats'):
                self.stats.save_stats()
            
            # Show final statistics
            print(f"\n{Logger.BOLD}{Logger.CYAN}📊 FINAL SESSION STATISTICS{Logger.RESET}")
            self.stats.print_summary()
            
            # Show all-time stats
            tickets = self.stats.get_ticket_stats()
            print(f"\n{Logger.BOLD}🎯 ALL-TIME TICKETS:{Logger.RESET} "
                  f"{Logger.GREEN}A:{tickets['prato_a']}{Logger.RESET} | "
                  f"{Logger.BLUE}B:{tickets['prato_b']}{Logger.RESET} | "
                  f"{Logger.YELLOW}S:{tickets['settore']}{Logger.RESET} | "
                  f"Total: {tickets['total']}")


def main():
    """Entry point"""
    print(f"{Logger.BOLD}{'=' * 70}{Logger.RESET}")
    print(f"{Logger.BOLD}{Logger.CYAN}🎫 FANSALE BOT V7{Logger.RESET}")
    print(f"{Logger.BOLD}{'=' * 70}{Logger.RESET}")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
        import requests
    except ImportError as e:
        print(f"\n{Logger.RED}❌ Missing dependency: {e}{Logger.RESET}")
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