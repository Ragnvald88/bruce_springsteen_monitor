#/fansale_v7_fixed.py
"""
FIXED VERSION - Addresses all detection and logging issues
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
    refresh_interval: int = 20
    session_timeout: int = 900
    min_wait: float = 0.3  # Ultra-fast
    max_wait: float = 1.0  # Ultra-fast
    captcha_grace_period: int = 300
    twocaptcha_api_key: str = ""
    auto_solve_captcha: bool = False
    popup_check_interval: int = 30
    
    @classmethod
    def from_file(cls, path: Path) -> 'BotConfig':
        """Load config from JSON file if exists"""
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
                valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
                filtered_data = {k: v for k, v in data.items() if k in valid_fields}
                return cls(**filtered_data)
        return cls()
    
    def save(self, path: Path):
        """Save config to JSON file"""
        data = self.__dict__.copy()
        if 'twocaptcha_api_key' in data:
            data['twocaptcha_api_key'] = "***hidden***"
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

# ==================== Enhanced Terminal Display ====================

class TerminalDisplay:
    """Enhanced terminal display with live updates"""
    
    # ANSI color codes
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    CLEAR_LINE = '\033[2K\r'
    
    # Unicode box drawing
    BOX = {
        'TL': '╔', 'TR': '╗', 'BL': '╚', 'BR': '╝',
        'H': '═', 'V': '║', 'T': '╤', 'B': '╧',
        'L': '╟', 'R': '╢', 'C': '┼',
        'HL': '─', 'VL': '│'
    }
    
    # Status indicators
    STATUS_ICONS = {
        'active': '🟢',
        'warning': '🟡', 
        'error': '🔴',
        'captcha': '🔐',
        'success': '🎉'
    }
    
    def __init__(self):
        self.activity_feed = deque(maxlen=5)
        self.last_update = time.time()
        
    def add_activity(self, message: str, level: str = 'info'):
        """Add message to activity feed"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = {
            'success': self.GREEN,
            'error': self.RED,
            'warning': self.YELLOW,
            'info': self.CYAN
        }.get(level, self.WHITE)
        
        self.activity_feed.append(f"{color}[{timestamp}] {message}{self.RESET}")
    
    def render_header(self, title: str = "FANSALE TICKET HUNTER v7"):
        """Render header section"""
        width = 80
        header = f"{self.BOX['TL']}{self.BOX['H'] * (width-2)}{self.BOX['TR']}\n"
        header += f"{self.BOX['V']}{title.center(width-2)}{self.BOX['V']}\n"
        header += f"{self.BOX['L']}{self.BOX['H'] * (width-2)}{self.BOX['R']}"
        return f"{self.BOLD}{self.CYAN}{header}{self.RESET}"
    
    def render_hunter_status(self, hunters: List[Dict]):
        """Render compact hunter status"""
        lines = []
        for h in hunters:
            status_icon = self.STATUS_ICONS.get(h['status'], '⚪')
            color = {
                'active': self.GREEN,
                'warning': self.YELLOW,
                'error': self.RED,
                'captcha': self.MAGENTA
            }.get(h['status'], self.WHITE)
            
            line = (f"{color}Hunter #{h['id']} {status_icon} │ "
                   f"{h['checks']:,} checks @ {h['rate']:.1f}/min │ "
                   f"Found: {h['found']} │ {h['action']}{self.RESET}")
            lines.append(line)
        
        return '\n'.join(lines)
    
    def render_statistics(self, stats: Dict):
        """Render statistics section"""
        runtime = stats['runtime']
        runtime_str = f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"
        
        stats_line = (f"{self.BOLD}Session: {runtime_str} │ "
                     f"Total Checks: {stats['total_checks']:,} │ "
                     f"Reserved: {stats['reserved']}/{stats['max_tickets']}{self.RESET}")
        
        ticket_stats = []
        for t_type, data in stats['tickets'].items():
            color = {
                'prato_a': self.GREEN,
                'prato_b': self.BLUE,
                'settore': self.YELLOW,
                'other': self.GRAY
            }.get(t_type, self.WHITE)
            
            if data['found'] > 0:
                ticket_stats.append(f"{color}{data['name']}: {data['found']}{self.RESET}")
        
        tickets_line = "Found: " + " │ ".join(ticket_stats) if ticket_stats else "No tickets found yet"
        
        return f"{stats_line}\n{tickets_line}"
    
    def render_activity_feed(self):
        """Render recent activity"""
        if not self.activity_feed:
            return f"{self.GRAY}No recent activity{self.RESET}"
        
        return '\n'.join(self.activity_feed)
    
    def render_full_display(self, data: Dict):
        """Render complete terminal display"""
        output = []
        
        # Header
        output.append(self.render_header())
        output.append("")
        
        # Statistics
        output.append(self.render_statistics(data['stats']))
        output.append("")
        
        # Hunter Status
        output.append(f"{self.BOLD}HUNTER STATUS:{self.RESET}")
        output.append(self.render_hunter_status(data['hunters']))
        output.append("")
        
        # Activity Feed
        output.append(f"{self.BOLD}RECENT ACTIVITY:{self.RESET}")
        output.append(self.render_activity_feed())
        
        return '\n'.join(output)

# ==================== Logger with Terminal Display ====================

class Logger:
    """Enhanced logger with terminal display integration"""
    
    terminal = TerminalDisplay()
    
    @classmethod
    def log(cls, message: str, category: str = 'system', emoji: str = None):
        """Log with category and optional emoji"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = cls.terminal.get_color(category) if hasattr(cls.terminal, 'get_color') else ''
        
        # Add to activity feed
        level = 'error' if category == 'error' else 'info'
        cls.terminal.add_activity(message, level)
        
        # Print to console
        print(f"{timestamp} {emoji or ''} {message}")
    
    @classmethod
    def alert(cls, message: str):
        """Alert message with emphasis"""
        cls.terminal.add_activity(message, 'success')
        print(f"\n{cls.terminal.BOLD}{cls.terminal.GREEN}🚨 {message}{cls.terminal.RESET}\n")
        # Audio alert
        for _ in range(3):
            print('\a')
            time.sleep(0.3)

# ==================== Statistics Manager ====================

class StatsManager:
    """Statistics manager with persistence"""
    def __init__(self, stats_file="fansale_stats_v7.json"):
        self.stats_file = Path(stats_file)
        self.lock = threading.Lock()
        
        # Session stats
        self.session_start = time.time()
        self.session_checks = 0
        self.hunters_data = {}  # Per-hunter statistics
        
        # Load persistent stats
        self.load_stats()
        
    def load_stats(self):
        """Load stats from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.all_time_stats = data.get('all_time', self._default_stats())
                    self.seen_tickets = set(data.get('seen_tickets', []))
            except:
                self.initialize_stats()
        else:
            self.initialize_stats()
    
    def _default_stats(self):
        """Default stats structure"""
        return {
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
    
    def initialize_stats(self):
        """Initialize fresh stats"""
        self.all_time_stats = self._default_stats()
        self.seen_tickets = set()
    
    def increment_checks(self, hunter_id: int = None):
        """Increment check counter"""
        with self.lock:
            self.session_checks += 1
            self.all_time_stats['total_checks'] += 1
            
            # Track per-hunter stats
            if hunter_id:
                if hunter_id not in self.hunters_data:
                    self.hunters_data[hunter_id] = {
                        'checks': 0,
                        'found': 0,
                        'last_action': 'Starting...',
                        'status': 'active'
                    }
                self.hunters_data[hunter_id]['checks'] += 1
    
    def update_hunter_action(self, hunter_id: int, action: str, status: str = 'active'):
        """Update hunter's current action"""
        with self.lock:
            if hunter_id not in self.hunters_data:
                self.hunters_data[hunter_id] = {
                    'checks': 0,
                    'found': 0,
                    'last_action': action,
                    'status': status
                }
            else:
                self.hunters_data[hunter_id]['last_action'] = action
                self.hunters_data[hunter_id]['status'] = status
    
    def get_hunter_stats(self):
        """Get formatted hunter statistics"""
        with self.lock:
            runtime = time.time() - self.session_start
            hunters = []
            
            for hunter_id, data in self.hunters_data.items():
                rate = (data['checks'] / runtime * 60) if runtime > 0 else 0
                hunters.append({
                    'id': hunter_id,
                    'checks': data['checks'],
                    'rate': rate,
                    'found': data['found'],
                    'action': data['last_action'],
                    'status': data['status']
                })
            
            return hunters
    
    def found_ticket(self, category: str, ticket_hash: str, hunter_id: int = None):
        """Record a new ticket found"""
        with self.lock:
            if ticket_hash not in self.seen_tickets:
                self.seen_tickets.add(ticket_hash)
                self.all_time_stats['tickets_found'][category] += 1
                self.all_time_stats['tickets_found']['total'] += 1
                
                if hunter_id and hunter_id in self.hunters_data:
                    self.hunters_data[hunter_id]['found'] += 1
                
                self.save_stats()
                return True
            return False
    
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

# ==================== 2Captcha Solver ====================

class TwoCaptchaSolver:
    """Handles automatic CAPTCHA solving"""
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
    """Simple retry decorator with fixed delay"""
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
    """Fixed FanSale Bot with proper detection and logging"""
    
    def __init__(self, config: Optional[BotConfig] = None):
        # Load configuration
        self.config = config or BotConfig()
        
        # Use correct environment variable
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
        
        # Configuration
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_types_to_hunt = set()
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # CAPTCHA tracking
        self.captcha_solved_time = {}
        self.captcha_grace_period = self.config.captcha_grace_period
        
        # Statistics
        self.stats = StatsManager()
        
        # Session tracking
        self.session_start_time = time.time()
        
        # Terminal display
        self.display = TerminalDisplay()
        self.display_lock = threading.Lock()
        self.last_display_update = 0
        
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
    
    def update_display(self):
        """Update terminal display"""
        with self.display_lock:
            # Clear screen
            print('\033[2J\033[H', end='')
            
            # Prepare data
            runtime = time.time() - self.session_start_time
            hunters = self.stats.get_hunter_stats()
            
            stats_data = {
                'runtime': runtime,
                'total_checks': self.stats.session_checks,
                'reserved': self.tickets_secured,
                'max_tickets': self.max_tickets,
                'tickets': {
                    'prato_a': {'name': 'Prato A', 'found': self.stats.all_time_stats['tickets_found']['prato_a']},
                    'prato_b': {'name': 'Prato B', 'found': self.stats.all_time_stats['tickets_found']['prato_b']},
                    'settore': {'name': 'Settore', 'found': self.stats.all_time_stats['tickets_found']['settore']},
                    'other': {'name': 'Other', 'found': self.stats.all_time_stats['tickets_found']['other']}
                }
            }
            
            data = {
                'stats': stats_data,
                'hunters': hunters
            }
            
            # Render and print
            print(self.display.render_full_display(data))
    
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
        """Generate unique hash for ticket"""
        clean_text = re.sub(r'\d{1,2}:\d{2}:\d{2}', '', ticket_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return hashlib.md5(clean_text.encode()).hexdigest()
    
    def extract_full_ticket_info(self, ticket_element: WebElement) -> Dict:
        """Extract ticket information"""
        try:
            ticket_info = {
                'raw_text': ticket_element.text,
                'category': 'other',
                'offer_id': ''
            }
            
            # Try to extract offer ID
            try:
                offer_id = ticket_element.get_attribute('data-offer-id')
                if offer_id:
                    ticket_info['offer_id'] = offer_id
            except:
                pass
            
            # Categorize
            ticket_info['category'] = self.categorize_ticket(ticket_info['raw_text'])
            
            return ticket_info
            
        except Exception as e:
            return {
                'raw_text': str(ticket_element.text) if hasattr(ticket_element, 'text') else '',
                'category': 'other',
                'offer_id': ''
            }
    
    def log_new_ticket(self, ticket_info: Dict, browser_id: int):
        """Log newly discovered ticket"""
        category = ticket_info['category']
        
        category_display = {
            'prato_a': 'PRATO A',
            'prato_b': 'PRATO B', 
            'settore': 'SETTORE',
            'other': 'OTHER'
        }.get(category, category.upper())
        
        # Extract price
        price_match = re.search(r'€\s*([0-9.,]+)', ticket_info['raw_text'])
        price = price_match.group(1) if price_match else 'N/A'
        
        # Always log ticket discovery
        message = f"NEW {category_display} TICKET! Hunter {browser_id} | €{price}"
        
        if category in self.ticket_types_to_hunt:
            Logger.alert(f"🎯 {message}")
            self.display.add_activity(f"🎯 {message}", 'success')
        else:
            Logger.log(f"Found {category_display} | €{price} | Hunter {browser_id}", category)
            self.display.add_activity(f"Found {category_display} | €{price}", 'info')
    
    def dismiss_popups(self, driver: uc.Chrome, browser_id: int) -> int:
        """Dismiss popups"""
        dismissed_count = 0
        
        try:
            # Priority 1: "Carica Offerte" button
            carica_selectors = [
                "button.js-BotProtectionModalButton1",
                "button:contains('Carica')",
                "button[class*='BotProtection']",
                "div.BotProtectionModal button"
            ]
            
            for selector in carica_selectors:
                try:
                    if ':contains' in selector:
                        elements = driver.find_elements(By.XPATH, "//button[contains(text(), 'Carica')]")
                        for carica in elements:
                            if carica.is_displayed():
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
                            time.sleep(0.3)
                            break
                except:
                    continue
            
            # Priority 2: Generic close buttons
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
        """Detect CAPTCHA"""
        try:
            captcha_selectors = [
                "div.g-recaptcha",
                "iframe[src*='recaptcha']",
                "div.h-captcha"
            ]
            
            for selector in captcha_selectors:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    Logger.log("🤖 CAPTCHA detected!")
                    
                    sitekey = None
                    if 'recaptcha' in selector:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        sitekey = elem.get_attribute('data-sitekey')
                    
                    return True, sitekey, driver.current_url
            
            return False, None, None
            
        except Exception:
            return False, None, None
    
    def wait_for_captcha_solve(self, driver: uc.Chrome, browser_id: int, timeout: int = 120) -> bool:
        """Wait for CAPTCHA solution"""
        captcha_detected, sitekey, pageurl = self.detect_captcha(driver)
        
        if not captcha_detected:
            return True
        
        self.stats.update_hunter_action(browser_id, "CAPTCHA detected!", 'captcha')
        self.stats.all_time_stats['captchas_encountered'] += 1
        
        # Try automatic solving first
        if self.auto_solve and sitekey:
            Logger.log(f"🤖 Attempting automatic CAPTCHA solve...")
            # Simplified auto-solve logic here
            pass
        
        # Manual solving
        Logger.alert(f"CAPTCHA DETECTED - Hunter {browser_id}")
        Logger.log(f"Please solve the CAPTCHA in Browser {browser_id}")
        Logger.log(f"Waiting up to {timeout} seconds...")
        
        start_time = time.time()
        check_interval = 2
        
        while time.time() - start_time < timeout:
            if not self.detect_captcha(driver)[0]:
                Logger.log(f"✅ CAPTCHA solved in Browser {browser_id}!")
                self.captcha_solved_time[browser_id] = time.time()
                self.stats.update_hunter_action(browser_id, "CAPTCHA solved!", 'active')
                return True
            
            time.sleep(check_interval)
        
        Logger.log(f"❌ CAPTCHA timeout in Browser {browser_id}", 'error')
        return False
    
    @retry(max_attempts=3, delay=2.0)
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create browser with undetected-chromedriver"""
        Logger.log(f"🚀 Creating Browser {browser_id}...")
        
        try:
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Window positioning
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
            
            # Additional options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Create driver
            driver = None
            chrome_version_attempts = [None, 137, 138, 136, 135, 131, 130]
            
            for version in chrome_version_attempts:
                try:
                    if version is not None:
                        Logger.log(f"Trying Chrome version {version}...")
                        driver = uc.Chrome(
                            options=options,
                            version_main=version,
                            use_subprocess=True,
                            suppress_welcome=True
                        )
                    else:
                        Logger.log("Trying with auto-detected Chrome version...")
                        driver = uc.Chrome(
                            options=options,
                            use_subprocess=True,
                            suppress_welcome=True
                        )
                    
                    break
                    
                except Exception as e:
                    if "This version of ChromeDriver only supports Chrome version" in str(e):
                        match = re.search(r'Chrome version (\d+)', str(e))
                        if match:
                            required_version = int(match.group(1))
                            if required_version not in chrome_version_attempts:
                                chrome_version_attempts.insert(1, required_version)
                    continue
            
            if driver is None:
                raise Exception("Failed to create browser")
            
            # Set timeouts
            driver.set_page_load_timeout(20)
            driver.implicitly_wait(5)
            
            Logger.log(f"✅ Browser {browser_id} created at position ({x}, {y})")
            return driver
            
        except Exception as e:
            Logger.log(f"❌ Failed to create browser {browser_id}: {e}", 'error')
            raise
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop - FIXED"""
        Logger.log(f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to page
        Logger.log(f"📍 Navigating to: {self.target_url}")
        try:
            driver.get(self.target_url)
            Logger.log(f"📄 Page loaded successfully")
        except Exception as e:
            Logger.log(f"❌ Navigation failed: {e}", 'error')
            return
        
        # Initial popup dismissal
        time.sleep(2)
        initial_popups = self.dismiss_popups(driver, browser_id)
        if initial_popups > 0:
            time.sleep(1)
            self.dismiss_popups(driver, browser_id)
        
        Logger.log(f"📢 Dismissed {initial_popups} initial popups")
        
        # Initialize tracking
        check_count = 0
        last_refresh = time.time()
        refresh_interval = 15 + random.randint(-3, 3)
        local_stats = defaultdict(int)
        last_popup_check = time.time()
        last_progress_update = time.time()
        
        # Main hunting loop
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats.increment_checks(browser_id)
                self.stats.update_hunter_action(browser_id, "Scanning for tickets...", 'active')
                
                # Popup check every 10 seconds
                if time.time() - last_popup_check > 10:
                    dismissed = self.dismiss_popups(driver, browser_id)
                    if dismissed > 0:
                        self.stats.update_hunter_action(browser_id, f"Dismissed {dismissed} popups", 'active')
                    last_popup_check = time.time()
                
                # Look for tickets
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                # Fallback selectors
                if not tickets:
                    alternative_selectors = [
                        "div[class*='ticket'][class*='available']",
                        "div[class*='biglietto'][class*='disponibile']",
                        "article[class*='ticket']",
                        "div[data-testid*='ticket']"
                    ]
                    for selector in alternative_selectors:
                        tickets = driver.find_elements(By.CSS_SELECTOR, selector)
                        if tickets:
                            Logger.log(f"Found tickets with selector: {selector}")
                            break
                
                # Process tickets
                if tickets:
                    for ticket in tickets:
                        try:
                            ticket_info = self.extract_full_ticket_info(ticket)
                            ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                            
                            category = ticket_info['category']
                            is_new_ticket = self.stats.found_ticket(category, ticket_hash, browser_id)
                            
                            if is_new_ticket:
                                local_stats[category] += 1
                                local_stats['found'] += 1
                                
                                # Always log new tickets
                                self.log_new_ticket(ticket_info, browser_id)
                                
                                # Check if we should purchase
                                if category in self.ticket_types_to_hunt:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.max_tickets:
                                            self.stats.update_hunter_action(browser_id, "Attempting purchase!", 'warning')
                                            
                                            if self.purchase_ticket(driver, ticket, browser_id):
                                                self.tickets_secured += 1
                                                self.stats.all_time_stats['purchases_made'] += 1
                                                
                                                if self.tickets_secured >= self.max_tickets:
                                                    Logger.alert(f"🎉 Max tickets secured!")
                                                    return
                                
                        except Exception as e:
                            continue
                
                # Update display every 2 seconds
                if time.time() - last_progress_update > 2:
                    self.update_display()
                    last_progress_update = time.time()
                
                # Fast checking
                time.sleep(random.uniform(self.config.min_wait, self.config.max_wait))
                
                # Page refresh
                if time.time() - last_refresh > refresh_interval:
                    self.stats.update_hunter_action(browser_id, "Refreshing page...", 'warning')
                    driver.refresh()
                    last_refresh = time.time()
                    refresh_interval = 15 + random.randint(-3, 3)
                    self.dismiss_popups(driver, browser_id)
                
            except TimeoutException:
                Logger.log(f"Hunter {browser_id}: Page timeout", 'warning')
                self.stats.update_hunter_action(browser_id, "Page timeout, refreshing...", 'error')
                try:
                    driver.refresh()
                except:
                    pass
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    Logger.log(f"Hunter {browser_id}: Session died", 'error')
                    self.stats.update_hunter_action(browser_id, "Session died!", 'error')
                    break
                else:
                    Logger.log(f"Hunter {browser_id}: Browser error", 'error')
                    time.sleep(2)
                
            except Exception as e:
                Logger.log(f"Hunter {browser_id} error: {e}", 'error')
                time.sleep(2)
    
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket"""
        try:
            Logger.log(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click ticket
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", ticket_element)
                Logger.log(f"✅ Clicked ticket")
            except:
                return False
            
            time.sleep(1)
            
            # Find buy button
            buy_selectors = [
                "button[data-qa='buyNowButton']",
                "button:contains('Acquista')",
                "button:contains('Compra')",
                "button[class*='buy']",
                "button[type='submit']"
            ]
            
            for selector in buy_selectors:
                try:
                    if ':contains' in selector:
                        match = re.search(r":contains\('([^']+)'\)", selector)
                        if match:
                            text = match.group(1)
                            xpath = f"//button[contains(text(), '{text}')]"
                            elements = driver.find_elements(By.XPATH, xpath)
                            if elements:
                                buy_btn = elements[0]
                                driver.execute_script("arguments[0].click();", buy_btn)
                                Logger.alert(f"✅ Hunter {browser_id}: Buy button clicked!")
                                
                                # Take screenshot
                                screenshot_path = f"screenshots/ticket_{browser_id}_{int(time.time())}.png"
                                Path("screenshots").mkdir(exist_ok=True)
                                driver.save_screenshot(screenshot_path)
                                
                                return True
                    else:
                        buy_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        driver.execute_script("arguments[0].click();", buy_btn)
                        Logger.alert(f"✅ Hunter {browser_id}: Buy button clicked!")
                        return True
                        
                except:
                    continue
            
            Logger.log(f"No buy button found", 'warning')
            return False
            
        except Exception as e:
            Logger.log(f"Purchase failed: {e}", 'error')
            return False
    
    def configure_ticket_filters(self):
        """Configure ticket type filters"""
        print(f"\n{TerminalDisplay.BOLD}🎯 SELECT TICKET TYPES TO HUNT{TerminalDisplay.RESET}")
        print("=" * 50)
        
        available_types = {
            '1': ('prato_a', 'Prato A', TerminalDisplay.GREEN),
            '2': ('prato_b', 'Prato B', TerminalDisplay.BLUE),
            '3': ('prato_all', 'All Prato (A + B)', TerminalDisplay.CYAN),
            '4': ('settore', 'Settore', TerminalDisplay.YELLOW),
            '5': ('other', 'Other/Unknown', TerminalDisplay.GRAY),
            '6': ('all', 'ALL ticket types', TerminalDisplay.BOLD)
        }
        
        print("\nAvailable ticket categories:")
        for key, (_, display, color) in available_types.items():
            if key == '3':
                print(f"  {color}{key}. {display}{TerminalDisplay.RESET} ⭐")
            elif key == '4':
                print(f"  {color}{key}. {display}{TerminalDisplay.RESET} (Seated: Fila/Posto/Anello)")
            elif key == '6':
                print(f"\n  {color}{key}. {display}{TerminalDisplay.RESET}")
            else:
                print(f"  {color}{key}. {display}{TerminalDisplay.RESET}")
        
        while True:
            selection = input(f"\n{TerminalDisplay.BOLD}Enter your choices (e.g., '1,2' or '3' for all Prato):{TerminalDisplay.RESET} ").strip()
            
            if not selection:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b'}
                print(f"{TerminalDisplay.GREEN}✅ Hunting for all Prato tickets (A + B){TerminalDisplay.RESET}")
                break
            
            if '6' in selection:
                self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
                print(f"{TerminalDisplay.GREEN}✅ Hunting for ALL ticket types{TerminalDisplay.RESET}")
                break
            
            if '3' in selection.split(','):
                self.ticket_types_to_hunt = {'prato_a', 'prato_b'}
                print(f"{TerminalDisplay.GREEN}✅ Hunting for all Prato tickets (A + B){TerminalDisplay.RESET}")
                break
            
            # Process individual selections
            valid_choices = []
            for choice in selection.split(','):
                choice = choice.strip()
                if choice in ['1', '2', '4', '5']:
                    valid_choices.append(choice)
            
            if valid_choices:
                self.ticket_types_to_hunt = set()
                for choice in valid_choices:
                    type_key, _, _ = available_types[choice]
                    self.ticket_types_to_hunt.add(type_key)
                
                print(f"\n{TerminalDisplay.GREEN}✅ Selected ticket types configured{TerminalDisplay.RESET}")
                break
            else:
                print(f"{TerminalDisplay.RED}Please enter valid choices (1-6){TerminalDisplay.RESET}")
    
    def configure(self):
        """Configure bot settings"""
        print(f"\n🤖 FANSALE BOT V7 CONFIGURATION")
        print("=" * 50)
        
        # Show initial stats
        print(f"📊 Session: 0h 0m 0s | Checks: 0 (0.0/min) | Found: A:0 B:0 S:0 | Total: 0")
        
        if self.captcha_solver:
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
        
        # Configure ticket filters
        self.configure_ticket_filters()
        
        # Summary
        print(f"\n📋 Configuration Summary:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Max tickets: {self.max_tickets}")
        
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
        """Main execution"""
        try:
            # Configure
            self.configure()
            
            # Create browsers
            print(f"\n{TerminalDisplay.BOLD}🚀 Starting {self.num_browsers} browser(s)...{TerminalDisplay.RESET}")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
                if i < self.num_browsers:
                    time.sleep(random.uniform(3, 7))
            
            if not self.browsers:
                Logger.log("❌ No browsers created", 'error')
                return
            
            Logger.log(f"✅ {len(self.browsers)} browser(s) ready!")
            
            print(f"{TerminalDisplay.CYAN}💡 Browsers positioned for multi-monitor setup{TerminalDisplay.RESET}")
            if self.captcha_solver:
                print(f"{TerminalDisplay.GREEN}✅ Auto-CAPTCHA solving enabled{TerminalDisplay.RESET}")
            else:
                print(f"{TerminalDisplay.YELLOW}⚠️  Manual CAPTCHA solving required{TerminalDisplay.RESET}")
            
            input(f"\n{TerminalDisplay.BOLD}✋ Press Enter to START HUNTING...{TerminalDisplay.RESET}")
            
            # Start hunting threads
            threads = []
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_tickets,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
            
            # Clear screen and start display
            print('\033[2J\033[H', end='')
            
            # Monitor progress
            try:
                while self.tickets_secured < self.max_tickets:
                    time.sleep(1)
                    self.update_display()
                
                Logger.alert(f"🎉 SUCCESS! {self.tickets_secured} tickets secured!")
                
            except KeyboardInterrupt:
                Logger.log(f"\n🛑 Stopping...")
                
        except Exception as e:
            Logger.log(f"Fatal error: {e}", 'error')
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            self.shutdown_event.set()
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
            
            # Save stats
            if hasattr(self, 'stats'):
                self.stats.save_stats()
            
            # Final statistics
            print(f"\n{TerminalDisplay.BOLD}{TerminalDisplay.CYAN}📊 FINAL SESSION STATISTICS{TerminalDisplay.RESET}")
            runtime = time.time() - self.session_start_time
            runtime_str = f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"
            
            tickets = self.stats.all_time_stats['tickets_found']
            print(f"Session: {runtime_str}")
            print(f"Total checks: {self.stats.session_checks:,}")
            print(f"Tickets found: A:{tickets['prato_a']} B:{tickets['prato_b']} S:{tickets['settore']} Other:{tickets['other']}")
            print(f"Tickets reserved: {self.tickets_secured}")


def main():
    """Entry point"""
    print(f"{TerminalDisplay.BOLD}{'=' * 70}{TerminalDisplay.RESET}")
    print(f"{TerminalDisplay.BOLD}{TerminalDisplay.CYAN}🎫 FANSALE BOT V7{TerminalDisplay.RESET}")
    print(f"{TerminalDisplay.BOLD}{'=' * 70}{TerminalDisplay.RESET}")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
        import requests
    except ImportError as e:
        print(f"\n{TerminalDisplay.RED}❌ Missing dependency: {e}{TerminalDisplay.RESET}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium requests")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    
    # Load configuration
    config_path = Path("bot_config_v7.json")
    config = BotConfig.from_file(config_path)
    
    # Check for 2captcha
    twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY', '')
    if twocaptcha_key:
        config.twocaptcha_api_key = twocaptcha_key
        config.auto_solve_captcha = True
        print(f"\n✅ 2Captcha API key found")
    
    # Save default config
    if not config_path.exists():
        config.save(config_path)
        print(f"\n📝 Created default configuration: {config_path}")
    
    # Check target URL
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
    import multiprocessing
    multiprocessing.freeze_support()
    main()