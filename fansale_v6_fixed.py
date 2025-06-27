#!/usr/bin/env python3
"""
FanSale Bot V6 - FIXED VERSION
================================
This version properly incorporates V5's working logic with V6's enhancements
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
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, field
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.remote.webelement import WebElement
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables
load_dotenv(override=True)

# ==================== Configuration ====================

@dataclass
class BotConfig:
    """Bot configuration with defaults"""
    browsers_count: int = 2
    max_tickets: int = 2
    refresh_interval: int = 15
    session_timeout: int = 900
    min_wait: float = 0.3  # Ultra-fast
    max_wait: float = 1.0  # Ultra-fast
    retry_attempts: int = 3
    retry_delay: float = 0.5
    captcha_grace_period: int = 300
    twocaptcha_api_key: str = ""
    auto_solve_captcha: bool = False
    popup_check_interval: int = 210  # 3.5 minutes
    enable_image_loading: bool = True
    captcha_check_interval: int = 300  # 5 minutes
    
    # V6 features
    enable_mouse_simulation: bool = True
    smart_refresh: bool = True
    ticket_priority_scoring: bool = True
    browser_coordination: bool = True
    
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
        data = self.__dict__.copy()
        if 'twocaptcha_api_key' in data:
            data['twocaptcha_api_key'] = ""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

# ==================== Enhanced Logging ====================

class CategoryLogger:
    """Separate loggers for each ticket category"""
    
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
        """Create separate loggers for each category"""
        categories = ['prato_a', 'prato_b', 'settore', 'other', 'system']
        
        for category in categories:
            logger = logging.getLogger(f'fansale.{category}')
            logger.setLevel(logging.INFO)
            logger.propagate = False
            
            # Console handler with color
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                CategoryFormatter(category, self.COLORS)
            )
            logger.addHandler(console_handler)
            
            # File handler
            file_handler = logging.FileHandler(
                f'fansale_v6_{category}.log',
                encoding='utf-8'
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)
            
            self.loggers[category] = logger
    
    def log_ticket(self, category: str, message: str, level='info'):
        """Log message to appropriate category logger"""
        if category in self.loggers:
            getattr(self.loggers[category], level)(message)
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
    """Statistics manager with category tracking"""
    
    def __init__(self, stats_file: Path = Path("fansale_stats_v6.json")):
        self.stats_file = stats_file
        self.stats = self.load_stats()
        self.lock = threading.Lock()
        
    def load_stats(self) -> Dict:
        """Load persistent statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        
        return {
            'all_time_runtime': 0,
            'total_checks': 0,
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
            'popups_dismissed': 0,
            'captchas_encountered': 0,
            'captchas_solved': 0,
            'captchas_auto_solved': 0,
            'session_start': time.time()
        }
    
    def update(self, key: str, value: Any = 1):
        """Update a statistic"""
        with self.lock:
            if isinstance(self.stats.get(key), dict) and isinstance(value, dict):
                for k, v in value.items():
                    self.stats[key][k] = self.stats[key].get(k, 0) + v
            else:
                self.stats[key] = self.stats.get(key, 0) + value
    
    def save(self):
        """Save statistics to file"""
        with self.lock:
            # Update runtime
            self.stats['all_time_runtime'] = time.time() - self.stats.get('session_start', time.time())
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self.lock:
            return self.stats.copy()

# ==================== Anti-Detection ====================

class HumanSimulator:
    """Simulate human-like behavior"""
    
    def __init__(self, driver: uc.Chrome):
        self.driver = driver
        self.last_mouse_move = time.time()
        self.last_scroll = time.time()
        
    def simulate_mouse_movement(self):
        """Simulate natural mouse movements"""
        if time.time() - self.last_mouse_move < random.uniform(5, 15):
            return
            
        try:
            actions = ActionChains(self.driver)
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Random movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, viewport_width - 100)
                y = random.randint(100, viewport_height - 100)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.1, 0.3))
            
            actions.perform()
            self.last_mouse_move = time.time()
            
        except:
            pass
    
    def simulate_scrolling(self):
        """Simulate natural scrolling"""
        if time.time() - self.last_scroll < random.uniform(10, 30):
            return
            
        try:
            scroll_amount = random.randint(-300, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            self.last_scroll = time.time()
        except:
            pass

# ==================== Helper Functions ====================

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """Retry decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# ==================== Main Bot Class ====================

class FanSaleBotV6:
    """Enhanced FanSale Bot with V6 improvements"""
    
    def __init__(self):
        # Load configuration
        self.config = BotConfig.from_file(Path("bot_config_v6.json"))
        self.target_url = os.getenv('FANSALE_URL', '')
        
        # Check environment
        if not self.target_url:
            print("\n❌ ERROR: FANSALE_URL not set in .env file!")
            print("Please set: FANSALE_URL=https://www.fansale.it/fansale/...")
            sys.exit(1)
        
        # Initialize components
        self.category_logger = CategoryLogger()
        self.stats_manager = StatsManager()
        
        # Browser management
        self.browsers = []
        self.browser_simulators = {}
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        
        # Ticket tracking
        self.seen_tickets = set()
        self.tickets_secured = 0
        self.captcha_solved_time = {}
        
        # Filters
        self.ticket_types_to_hunt = set()
        
        # Performance tracking
        self.performance_tracker = defaultdict(list)
        self.session_start_time = time.time()
        
        # 2Captcha setup
        self.captcha_solver = None
        api_key = self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY', '')
        if api_key:
            try:
                from twocaptcha import TwoCaptcha
                self.captcha_solver = TwoCaptcha(api_key)
                self.category_logger.log_ticket('system', 
                    f"✅ 2Captcha configured with API key: {api_key[:8]}...")
            except ImportError:
                self.category_logger.log_ticket('system',
                    "⚠️ 2captcha module not installed. Run: pip install 2captcha-python", 'warning')
        
        self.category_logger.log_ticket('system', 
            f"🎯 Target URL: {self.target_url[:50]}...")
    
    def dismiss_popups(self, driver: uc.Chrome, browser_id: int) -> int:
        """Enhanced popup detection and dismissal from V5"""
        start_time = time.time()
        dismissed_count = 0
        
        try:
            # Enhanced popup selectors with strategies (from V5)
            popup_strategies = [
                # Strategy 0: Priority - "Carica Offerte" button (must be first)
                {
                    'name': 'carica_offerte',
                    'selectors': [
                        "button.js-BotProtectionModalButton1",
                        "button.js-BotProtectionModalButtonTrigger",
                        "button[name='_submit'][value='true']"
                    ],
                    'action': 'click_directly'
                },
                # Strategy 1: Look for visible overlays/modals
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
                # Strategy 3: Direct button selectors
                {
                    'name': 'direct_buttons',
                    'selectors': [
                        "button[class*='close']",
                        "button[aria-label*='close' i]",
                        "button[aria-label*='chiudi' i]",
                        "a[class*='close']",
                        "span[class*='close']"
                    ],
                    'action': 'click_directly'
                }
            ]
            
            for strategy in popup_strategies:
                for selector in strategy['selectors']:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            if not element.is_displayed():
                                continue
                                
                            try:
                                if strategy['action'] == 'find_close_button_or_click_overlay':
                                    # Try to find close button within overlay
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
                                            self.category_logger.log_ticket('system',
                                                f"📢 Hunter {browser_id}: Dismissed {strategy['name']} via close button")
                                            dismissed_count += 1
                                            clicked = True
                                            time.sleep(0.5)
                                            break
                                    
                                    # If no close button found, try clicking overlay
                                    if not clicked:
                                        driver.execute_script("arguments[0].click();", element)
                                        self.category_logger.log_ticket('system',
                                            f"📢 Hunter {browser_id}: Dismissed {strategy['name']} by clicking overlay")
                                        dismissed_count += 1
                                        time.sleep(0.5)
                                
                                elif strategy['action'] == 'find_accept_button':
                                    # Look for accept/OK buttons in cookie banners
                                    accept_buttons = element.find_elements(By.CSS_SELECTOR, "button, a")
                                    for btn in accept_buttons:
                                        btn_text = btn.text.lower()
                                        if any(x in btn_text for x in ['accetta', 'accept', 'ok', 'consenti', 'agree']):
                                            driver.execute_script("arguments[0].click();", btn)
                                            self.category_logger.log_ticket('system',
                                                f"📢 Hunter {browser_id}: Accepted {strategy['name']}")
                                            dismissed_count += 1
                                            time.sleep(0.5)
                                            break
                                
                                elif strategy['action'] == 'click_directly':
                                    driver.execute_script("arguments[0].click();", element)
                                    self.category_logger.log_ticket('system',
                                        f"📢 Hunter {browser_id}: Clicked {strategy['name']} button")
                                    dismissed_count += 1
                                    time.sleep(0.5)
                                    
                            except Exception as e:
                                pass
                                
                    except Exception as e:
                        pass
            
            # JavaScript fallback (from V5)
            if dismissed_count == 0:
                removed = driver.execute_script("""
                    var removed = 0;
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
                            if (el && el.offsetParent !== null) {
                                el.remove();
                                removed++;
                            }
                        });
                    });
                    
                    return removed;
                """)
                
                if removed > 0:
                    self.category_logger.log_ticket('system',
                        f"📢 Hunter {browser_id}: Removed {removed} popups via JavaScript")
                    dismissed_count += removed
            
            if dismissed_count > 0:
                self.stats_manager.update('popups_dismissed', dismissed_count)
                self.stats_manager.save()
                
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"Error in dismiss_popups: {e}", 'error')
            
        return dismissed_count
    
    def detect_captcha(self, driver: uc.Chrome) -> Tuple[bool, Optional[Dict]]:
        """Enhanced CAPTCHA detection from V5"""
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
                    var match = iframes[0].src.match(/[?&]k=([^&]+)/);
                    if (match && !found.sitekey) {
                        found.sitekey = match[1];
                    }
                }
                
                return found;
            """)
            
            if recaptcha_v2['hasDiv'] or recaptcha_v2['hasIframe']:
                self.category_logger.log_ticket('system',
                    f"🤖 reCAPTCHA v2 detected! Div: {recaptcha_v2['hasDiv']}, Iframe: {recaptcha_v2['hasIframe']}")
                return True, {'type': 'recaptcha_v2', 'sitekey': recaptcha_v2['sitekey']}
            
            # Strategy 2: Check for reCAPTCHA v3
            recaptcha_v3 = driver.execute_script("""
                return window.grecaptcha !== undefined || 
                       document.querySelector('script[src*="recaptcha/api.js"]') !== null;
            """)
            
            if recaptcha_v3:
                self.category_logger.log_ticket('system', "🤖 reCAPTCHA v3 detected!")
                page_source = driver.page_source
                sitekey_match = re.search(r'["\'"]sitekey["\'"]\\s*:\\s*["\'"]([^"\']+)["\'"]', page_source)
                sitekey = sitekey_match.group(1) if sitekey_match else None
                return True, {'type': 'recaptcha_v3', 'sitekey': sitekey}
            
            # Strategy 3: Check page source for CAPTCHA keywords
            page_source_lower = driver.page_source.lower()
            captcha_indicators = [
                'g-recaptcha', 'h-captcha', 'cf-turnstile',
                'captcha', 'verifica che non sei un robot',
                'verify you are human', 'sono un umano'
            ]
            
            for indicator in captcha_indicators:
                if indicator in page_source_lower:
                    self.category_logger.log_ticket('system',
                        f"🤖 CAPTCHA indicator found: '{indicator}'")
                    return True, {'type': 'unknown', 'indicator': indicator}
            
            return False, None
            
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"Error detecting CAPTCHA: {e}", 'error')
            return False, None
    
    def solve_captcha_automatically(self, driver: uc.Chrome, captcha_info: Dict) -> bool:
        """Automatically solve CAPTCHA using 2captcha"""
        if not self.captcha_solver:
            return False
            
        try:
            self.category_logger.log_ticket('system', "🤖 Solving CAPTCHA automatically...")
            
            if captcha_info.get('type') == 'recaptcha_v2' and captcha_info.get('sitekey'):
                result = self.captcha_solver.recaptcha(
                    sitekey=captcha_info['sitekey'],
                    url=driver.current_url
                )
                
                # Inject solution
                driver.execute_script(f"""
                    document.getElementById('g-recaptcha-response').innerHTML = '{result['code']}';
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        Object.entries(___grecaptcha_cfg.clients).forEach(([key, client]) => {{
                            if (client.callback) {{
                                client.callback('{result['code']}');
                            }}
                        }});
                    }}
                """)
                
                self.category_logger.log_alert('system', "✅ CAPTCHA solved automatically!")
                self.stats_manager.update('captchas_auto_solved')
                return True
                
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"Auto-solve failed: {e}", 'error')
            
        return False
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser"""
        self.category_logger.log_ticket('system', f"🚀 Creating Browser {browser_id}...")
        
        try:
            options = uc.ChromeOptions()
            options.headless = False
            
            # Stealth options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-infobars')
            
            # Performance options
            options.add_argument('--disable-logging')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            
            # Enable images
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 1,
                    'plugins': 1,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2,
                },
                'profile.managed_default_content_settings': {
                    'images': 1
                }
            }
            options.add_experimental_option('prefs', prefs)
            
            # Window positioning
            window_width = 450
            window_height = 800
            col = (browser_id - 1) % 4
            row = (browser_id - 1) // 4
            x = col * (window_width + 10)
            y = row * 100
            
            options.add_argument(f'--window-position={x},{y}')
            options.add_argument(f'--window-size={window_width},{window_height}')
            
            # Create browser
            driver = uc.Chrome(options=options, version_main=None)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            # Inject stealth scripts
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                delete navigator.__proto__.webdriver;
            """)
            
            # Create human simulator if enabled
            if self.config.enable_mouse_simulation:
                self.browser_simulators[browser_id] = HumanSimulator(driver)
            
            self.category_logger.log_ticket('system', 
                f"✅ Browser {browser_id} created at position ({x}, {y})")
            
            return driver
            
        except Exception as e:
            self.category_logger.log_ticket('system', 
                f"❌ Failed to create browser {browser_id}: {e}", 'error')
            return None
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop with V5 logic and V6 enhancements"""
        self.category_logger.log_ticket('system', 
            f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to event page
        self.category_logger.log_ticket('system',
            f"📍 Navigating to: {self.target_url}")
        try:
            page_start = time.time()
            driver.get(self.target_url)
            page_load_time = time.time() - page_start
            self.performance_tracker['page_load'].append(page_load_time)
            self.category_logger.log_ticket('system',
                f"📄 Page loaded in {page_load_time:.2f}s")
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"❌ Failed to navigate: {e}", 'error')
            return
        
        # Initial popup dismissal
        time.sleep(1)
        initial_popups = self.dismiss_popups(driver, browser_id)
        
        # Special handling for "Carica Offerte" button (from V5)
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
        
        self.category_logger.log_ticket('system',
            f"📢 Dismissed {initial_popups} initial popups")
        
        # Initialize tracking variables
        check_count = 0
        last_refresh = time.time() - (browser_id * 5)
        refresh_interval = 15 + random.randint(-3, 3)
        last_session_refresh = time.time()
        last_popup_check = time.time()
        last_captcha_test = time.time()
        
        # Category-specific tracking
        local_stats = defaultdict(int)
        
        # Get human simulator if enabled
        simulator = self.browser_simulators.get(browser_id)
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.config.max_tickets:
            try:
                check_count += 1
                self.stats_manager.update('total_checks')
                
                # Human simulation
                if simulator and self.config.enable_mouse_simulation:
                    if random.random() < 0.1:
                        simulator.simulate_mouse_movement()
                    if random.random() < 0.05:
                        simulator.simulate_scrolling()
                
                # Periodic CAPTCHA check (browser 1 only)
                if browser_id == 1 and time.time() - last_captcha_test > self.config.captcha_check_interval:
                    self.category_logger.log_ticket('system',
                        f"🔍 Hunter {browser_id}: Performing periodic CAPTCHA check...")
                    captcha_detected, captcha_info = self.detect_captcha(driver)
                    if captcha_detected:
                        self.category_logger.log_alert('system',
                            f"CAPTCHA detected during periodic check!")
                        self.stats_manager.update('captchas_encountered')
                        
                        if self.captcha_solver and self.config.auto_solve_captcha:
                            if self.solve_captcha_automatically(driver, captcha_info):
                                self.captcha_solved_time[browser_id] = time.time()
                            else:
                                self.wait_for_manual_captcha(driver, browser_id)
                        else:
                            self.wait_for_manual_captcha(driver, browser_id)
                    else:
                        self.category_logger.log_ticket('system',
                            f"✅ No CAPTCHA detected - all clear!")
                    last_captcha_test = time.time()
                
                # Popup check
                if time.time() - last_popup_check > self.config.popup_check_interval:
                    dismissed = self.dismiss_popups(driver, browser_id)
                    if dismissed > 0:
                        self.category_logger.log_ticket('system',
                            f"Dismissed {dismissed} popups")
                    last_popup_check = time.time()
                
                # Check for 404 blocks
                if self.is_blocked(driver):
                    self.category_logger.log_ticket('system',
                        f"⚠️ Hunter {browser_id}: Block detected!", 'warning')
                    self.stats_manager.update('blocks_encountered')
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(random.uniform(2.5, 3.5))
                    self.dismiss_popups(driver, browser_id)
                    continue
                
                # Session refresh every 15 minutes
                if time.time() - last_session_refresh > 900:
                    self.category_logger.log_ticket('system',
                        f"🔄 Hunter {browser_id}: Preventive session refresh...")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(3)
                    self.dismiss_popups(driver, browser_id)
                    last_session_refresh = time.time()
                    continue
                
                # Look for tickets (NO CACHING!)
                ticket_start = time.time()
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                ticket_check_time = time.time() - ticket_start
                self.performance_tracker['ticket_check'].append(ticket_check_time)
                
                if tickets:
                    # Check CAPTCHA grace period
                    in_grace_period = browser_id in self.captcha_solved_time and \
                                    time.time() - self.captcha_solved_time[browser_id] < self.config.captcha_grace_period
                    
                    for ticket in tickets:
                        try:
                            # Extract ticket information
                            ticket_info = self.extract_ticket_info(ticket)
                            ticket_hash = hashlib.md5(ticket_info['raw_text'].encode()).hexdigest()[:8]
                            
                            # Check if new ticket
                            if ticket_hash not in self.seen_tickets:
                                # New ticket found!
                                self.seen_tickets.add(ticket_hash)
                                
                                # Update statistics
                                self.stats_manager.update('unique_tickets_found')
                                category = ticket_info['category']
                                self.stats_manager.update('tickets_by_type', {category: 1})
                                local_stats[category] += 1
                                
                                # Log the new ticket
                                self.log_new_ticket(ticket_info, browser_id)
                                
                                # Save stats
                                self.stats_manager.save()
                                
                                # Attempt purchase if it matches our filters
                                if category in self.ticket_types_to_hunt:
                                    with self.purchase_lock:
                                        if self.tickets_secured < self.config.max_tickets:
                                            if in_grace_period:
                                                self.category_logger.log_ticket('system',
                                                    f"🚀 Hunter {browser_id}: CAPTCHA grace period active!")
                                            
                                            if self.purchase_ticket(driver, ticket, browser_id, ticket_info):
                                                self.tickets_secured += 1
                                                self.stats_manager.update('purchases')
                                                self.stats_manager.update('purchases_by_type', {category: 1})
                                                self.stats_manager.save()
                                                
                                                if self.tickets_secured >= self.config.max_tickets:
                                                    self.category_logger.log_alert('system',
                                                        f"🎉 Max tickets secured!")
                                                    return
                                            
                        except Exception as e:
                            pass
                
                # Wait time
                refresh_time = random.uniform(self.config.min_wait, self.config.max_wait)
                time.sleep(refresh_time)
                
                # Page refresh
                if time.time() - last_refresh > refresh_interval:
                    driver.refresh()
                    last_refresh = time.time()
                    refresh_interval = 15 + random.randint(-3, 3)
                    time.sleep(1)
                    self.dismiss_popups(driver, browser_id)
                
                # Progress update
                if check_count % 60 == 0:
                    elapsed = time.time() - self.session_start_time
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    
                    # Category summary
                    summary = []
                    for cat in ['prato_a', 'prato_b', 'settore', 'other']:
                        if local_stats[cat] > 0:
                            summary.append(f"{cat.upper()}: {local_stats[cat]}")
                    
                    status = f"Hunter {browser_id}: {check_count} checks @ {rate:.1f}/min"
                    if summary:
                        status += f" | {' | '.join(summary)}"
                    
                    self.category_logger.log_ticket('system', f"📊 {status}")
                
            except Exception as e:
                self.category_logger.log_ticket('system',
                    f"Hunter {browser_id} error: {e}", 'error')
                time.sleep(5)
    
    def extract_ticket_info(self, ticket_element: WebElement) -> Dict:
        """Extract ticket information"""
        try:
            ticket_info = {
                'raw_text': ticket_element.text,
                'category': 'other',
                'section': '',
                'row': '',
                'seat': '',
                'entrance': '',
                'ring': '',
                'price': ''
            }
            
            # Get text
            full_text = ticket_element.text
            ticket_info['raw_text'] = full_text
            
            # Categorize
            ticket_lower = full_text.lower()
            if 'prato a' in ticket_lower or 'prato gold a' in ticket_lower:
                ticket_info['category'] = 'prato_a'
            elif 'prato b' in ticket_lower or 'prato gold b' in ticket_lower:
                ticket_info['category'] = 'prato_b'
            elif any(keyword in ticket_lower for keyword in [
                'settore', 'fila', 'posto', 'anello', 'tribuna', 
                'poltrona', 'numerato', 'seat', 'row', 'ring',
                'rosso', 'blu', 'verde', 'giallo', 'ingresso'
            ]):
                ticket_info['category'] = 'settore'
            
            # Extract details
            lines = full_text.split('\n')
            for line in lines:
                line_lower = line.lower()
                
                # Section
                if any(x in line_lower for x in ['prato', 'settore', 'tribuna', 'parterre']):
                    ticket_info['section'] = line.strip()
                
                # Row
                fila_match = re.search(r'fila\s*[:s]*(\w+)', line, re.I)
                if fila_match:
                    ticket_info['row'] = fila_match.group(1)
                
                # Seat
                posto_match = re.search(r'posto\s*[:s]*(\d+)', line, re.I)
                if posto_match:
                    ticket_info['seat'] = posto_match.group(1)
                
                # Entrance
                ingresso_match = re.search(r'ingresso\s*[:s]*(\d+)', line, re.I)
                if ingresso_match:
                    ticket_info['entrance'] = ingresso_match.group(1)
                
                # Ring
                anello_match = re.search(r'(\d+\s*anello\s*\w+)', line, re.I)
                if anello_match:
                    ticket_info['ring'] = anello_match.group(1)
                
                # Price
                price_match = re.search(r'(\d+[,.]?\d*)\s*€', line)
                if price_match:
                    ticket_info['price'] = price_match.group(0)
            
            return ticket_info
            
        except Exception as e:
            return {
                'raw_text': str(ticket_element.text),
                'category': 'other',
                'section': '', 'row': '', 'seat': '',
                'entrance': '', 'ring': '', 'price': ''
            }
    
    def log_new_ticket(self, ticket_info: Dict, browser_id: int):
        """Log newly discovered ticket with category-specific logging"""
        category = ticket_info['category']
        
        # Check if we're hunting this type
        is_hunting = category in self.ticket_types_to_hunt
        hunt_indicator = " [HUNTING]" if is_hunting else " [TRACKING]"
        
        # Build details
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
        
        # Alert if hunting
        if is_hunting:
            self.category_logger.log_alert(category,
                f"NEW TICKET FOUND by Hunter {browser_id}!")
        
        # Log details
        self.category_logger.log_ticket(category,
            f"NEW TICKET{hunt_indicator} - Hunter {browser_id}")
        self.category_logger.log_ticket(category, f"└─ {detail_str}")
        self.category_logger.log_ticket(category, "─" * 60)
    
    def purchase_ticket(self, driver: uc.Chrome, ticket_element: WebElement, 
                       browser_id: int, ticket_info: Dict) -> bool:
        """Attempt to purchase ticket"""
        try:
            category = ticket_info['category']
            self.category_logger.log_ticket(category,
                f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click ticket
            driver.execute_script("arguments[0].scrollIntoView(true);", ticket_element)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", ticket_element)
            time.sleep(0.5)
            
            # Look for purchase button
            purchase_selectors = [
                "button[data-qa='ticketCheckoutButton']",
                "button.checkout-button",
                "button[class*='purchase']",
                "button[class*='buy']",
                "button[class*='compra']"
            ]
            
            for selector in purchase_selectors:
                try:
                    purchase_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if purchase_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", purchase_btn)
                        
                        # Success!
                        self.category_logger.log_alert(category,
                            f"🎉 TICKET PURCHASED! Hunter {browser_id}")
                        return True
                except:
                    pass
            
            self.category_logger.log_ticket(category,
                f"❌ Purchase failed - no checkout button found", 'error')
            return False
            
        except Exception as e:
            self.category_logger.log_ticket(ticket_info['category'],
                f"❌ Purchase error: {e}", 'error')
            return False
    
    def is_blocked(self, driver: uc.Chrome) -> bool:
        """Check if blocked (404 page)"""
        try:
            # Check for 404 in title
            if '404' in driver.title:
                return True
            
            # Check for common block indicators
            page_source = driver.page_source.lower()
            block_indicators = [
                'access denied',
                'accesso negato',
                'blocked',
                'error 404',
                'page not found',
                'pagina non trovata'
            ]
            
            return any(indicator in page_source for indicator in block_indicators)
            
        except:
            return False
    
    def clear_browser_data(self, driver: uc.Chrome, browser_id: int):
        """Clear browser data to reset session"""
        try:
            self.category_logger.log_ticket('system',
                f"🧹 Hunter {browser_id}: Clearing browser data...")
            
            # Clear cookies
            driver.delete_all_cookies()
            
            # Clear local storage
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            
            self.category_logger.log_ticket('system',
                f"✅ Hunter {browser_id}: Browser data cleared")
            
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"Failed to clear browser data: {e}", 'error')
    
    def wait_for_manual_captcha(self, driver: uc.Chrome, browser_id: int):
        """Wait for manual CAPTCHA solving"""
        self.category_logger.log_alert('system',
            f"⏳ Waiting for manual CAPTCHA solve on Browser {browser_id}...")
        
        # Wait up to 5 minutes
        for i in range(300):
            captcha_detected, _ = self.detect_captcha(driver)
            if not captcha_detected:
                self.category_logger.log_alert('system',
                    f"✅ CAPTCHA solved on Browser {browser_id}!")
                self.captcha_solved_time[browser_id] = time.time()
                self.stats_manager.update('captchas_solved')
                break
            time.sleep(1)
    
    def show_statistics_dashboard(self):
        """Display beautiful statistics dashboard"""
        stats = self.stats_manager.get_stats()
        runtime = time.time() - self.session_start_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        
        print("\n" + "═" * 70)
        print("📊 FANSALE BOT V6 STATISTICS DASHBOARD".center(70))
        print("═" * 70)
        
        print(f"\n⏱️  Total Runtime: {hours}h {minutes}m")
        print(f"🔍 Total Checks: {stats.get('total_checks', 0):,}")
        print(f"🎫 Unique Tickets Found: {stats.get('unique_tickets_found', 0):,}")
        
        print(f"\n📈 Ticket Breakdown:")
        print(f"   {CategoryLogger.COLORS['prato_a']}● Prato A:{CategoryLogger.COLORS['reset']} {stats['tickets_by_type'].get('prato_a', 0)}")
        print(f"   {CategoryLogger.COLORS['prato_b']}● Prato B:{CategoryLogger.COLORS['reset']} {stats['tickets_by_type'].get('prato_b', 0)}")
        print(f"   {CategoryLogger.COLORS['settore']}● Settore:{CategoryLogger.COLORS['reset']} {stats['tickets_by_type'].get('settore', 0)}")
        print(f"   ○ Other: {stats['tickets_by_type'].get('other', 0)}")
        
        print(f"\n🛍️  Purchases: {stats.get('purchases', 0)}")
        if stats.get('purchases', 0) > 0:
            print(f"   Prato A: {stats['purchases_by_type'].get('prato_a', 0)}")
            print(f"   Prato B: {stats['purchases_by_type'].get('prato_b', 0)}")
            print(f"   Settore: {stats['purchases_by_type'].get('settore', 0)}")
        
        print(f"🚫 Blocks Cleared: {stats.get('blocks_encountered', 0)}")
        print(f"📢 Popups Dismissed: {stats.get('popups_dismissed', 0)}")
        
        print(f"\n🤖 CAPTCHA Stats:")
        print(f"   Encountered: {stats.get('captchas_encountered', 0)}")
        print(f"   Solved Manually: {stats.get('captchas_solved', 0) - stats.get('captchas_auto_solved', 0)}")
        print(f"   Solved Automatically: {stats.get('captchas_auto_solved', 0)}")
        
        if stats['total_checks'] > 0:
            rate = stats['total_checks'] / (runtime / 60) if runtime > 0 else 0
            print(f"\n⚡ Average Rate: {rate:.1f} checks/min")
        
        print("\n" + "═" * 70 + "\n")
    
    def configure(self):
        """Interactive configuration"""
        print("\n" + "=" * 60)
        print("🎫 FANSALE BOT V6 - CONFIGURATION".center(60))
        print("=" * 60)
        
        # Show features
        print("\n✨ V6 FEATURES:")
        print("  • Separated logging for each ticket category")
        print("  • Ultra-fast checking (60-300 checks/min)")
        print("  • Smart ticket prioritization")
        print("  • Human behavior simulation")
        print("  • Live statistics dashboard")
        
        # Number of browsers
        while True:
            try:
                num = input(f"\n🌐 Number of browsers (1-8, default {self.config.browsers_count}): ").strip()
                if not num:
                    break
                self.config.browsers_count = int(num)
                if 1 <= self.config.browsers_count <= 8:
                    break
                print("❌ Please enter 1-8")
            except ValueError:
                print("❌ Invalid number")
        
        # Max tickets
        while True:
            try:
                max_t = input(f"\n🎫 Max tickets (1-4, default {self.config.max_tickets}): ").strip()
                if not max_t:
                    break
                self.config.max_tickets = int(max_t)
                if 1 <= self.config.max_tickets <= 4:
                    break
                print("❌ Please enter 1-4")
            except ValueError:
                print("❌ Invalid number")
        
        # Category selection
        print("\n🎯 SELECT TICKET CATEGORIES TO HUNT:")
        print("  1. Prato A")
        print("  2. Prato B")
        print("  3. Settore (Seated)")
        print("  4. Other/Unknown")
        print("  5. ALL categories")
        
        choice = input("\nEnter your choices (e.g., '1,2' or '5' for all): ").strip()
        
        if '5' in choice:
            self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
            print("✅ Hunting for ALL ticket types")
        else:
            selected = set()
            if '1' in choice:
                selected.add('prato_a')
            if '2' in choice:
                selected.add('prato_b')
            if '3' in choice:
                selected.add('settore')
            if '4' in choice:
                selected.add('other')
            
            self.ticket_types_to_hunt = selected
            print(f"✅ Hunting for: {', '.join(selected)}")
        
        # Save configuration
        self.config.save(Path("bot_config_v6.json"))
        
        print("\n📋 CONFIGURATION SUMMARY:")
        print(f"  • Browsers: {self.config.browsers_count}")
        print(f"  • Max tickets: {self.config.max_tickets}")
        print(f"  • Categories: {', '.join(self.ticket_types_to_hunt)}")
        print(f"  • Target URL: {self.target_url[:50]}...")
    
    def run(self):
        """Main execution loop"""
        try:
            # Configure
            self.configure()
            
            # Show current stats
            self.show_statistics_dashboard()
            
            # Create browsers
            print(f"\n🚀 Starting {self.config.browsers_count} browsers...")
            
            for i in range(1, self.config.browsers_count + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
                    time.sleep(random.uniform(2, 4))
            
            if not self.browsers:
                print("❌ No browsers created!")
                return
            
            print(f"\n✅ {len(self.browsers)} browsers ready!")
            print("\n💡 TIP: Browsers are positioned for multi-monitor setups")
            print("⚠️  CAPTCHA ALERT: Auto-solve if configured, or manual alert")
            print(f"📢 POPUPS: Will be checked every {self.config.popup_check_interval/60:.1f} minutes")
            
            input("\n✋ Press Enter to START HUNTING...\n")
            
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
            
            print("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            # Monitor progress
            try:
                last_update = time.time()
                while self.tickets_secured < self.config.max_tickets:
                    time.sleep(1)
                    
                    # Status update every 60 seconds
                    if time.time() - last_update > 60:
                        self.show_statistics_dashboard()
                        last_update = time.time()
                
                print(f"\n🎉 SUCCESS! {self.tickets_secured} tickets secured!")
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
        
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            self.shutdown_event.set()
            self.stats_manager.save()
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
            
            # Show final stats
            print("\n📊 FINAL SESSION STATISTICS")
            self.show_statistics_dashboard()

# ==================== Entry Point ====================

def main():
    """Entry point"""
    print("\n" + "=" * 60)
    print("🎫 FANSALE BOT V6 - FIXED EDITION".center(60))
    print("=" * 60)
    
    # Create and run bot
    bot = FanSaleBotV6()
    bot.run()

if __name__ == "__main__":
    main()
