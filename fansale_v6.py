#!/usr/bin/env python3
"""
FanSale Bot V6 - Enhanced Edition
================================
Major improvements:
- Separated logging for Prato A, Prato B, and Settore
- Performance optimizations with DOM caching
- Advanced anti-detection features
- Real-time dashboard with per-category stats
- Smart ticket prioritization
- Event-driven architecture
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
load_dotenv()

# ==================== Configuration ====================

@dataclass
class BotConfig:
    """Enhanced bot configuration with V6 features"""
    browsers_count: int = 2
    max_tickets: int = 2
    refresh_interval: int = 15
    session_timeout: int = 900
    min_wait: float = 0.2  # Ultra-fast: ~150-300 checks/min
    max_wait: float = 0.8  # Ultra-fast: ~150-300 checks/min
    retry_attempts: int = 3
    retry_delay: float = 0.5
    captcha_grace_period: int = 300
    twocaptcha_api_key: str = ""
    auto_solve_captcha: bool = False
    popup_check_interval: int = 240  # 4 minutes
    enable_image_loading: bool = True
    captcha_check_interval: int = 300  # 5 minutes
    
    # V6 New features
    use_mutation_observer: bool = True  # Real-time DOM monitoring
    enable_mouse_simulation: bool = True  # Human-like mouse movements
    smart_refresh: bool = True  # Adaptive refresh timing
    ticket_priority_scoring: bool = True  # Score tickets by desirability
    browser_coordination: bool = True  # Prevent duplicate purchases
    advanced_filtering: bool = True  # Price/section filters
    
    # Performance tuning
    dom_cache_duration: int = 30  # Cache static elements for 30s
    mutation_batch_size: int = 10  # Process mutations in batches
    max_concurrent_checks: int = 5  # Limit concurrent ticket checks
    
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
    """Separate loggers for each ticket category with visual differentiation"""
    
    COLORS = {
        'prato_a': '\033[92m',      # Green
        'prato_b': '\033[94m',      # Blue
        'settore': '\033[93m',      # Yellow
        'other': '\033[90m',        # Gray
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

# ==================== Enhanced Statistics ====================

class EnhancedStatsManager:
    """Advanced statistics with per-category tracking"""
    
    def __init__(self, stats_file: Path = Path("fansale_stats_v6.json")):
        self.stats_file = stats_file
        self.stats = self.load_stats()
        self.session_stats = self._create_session_stats()
        self.lock = threading.Lock()
        
    def _create_session_stats(self) -> Dict:
        """Create fresh session statistics"""
        return {
            'start_time': time.time(),
            'checks_by_category': defaultdict(int),
            'tickets_found_by_category': defaultdict(int),
            'tickets_purchased_by_category': defaultdict(int),
            'response_times': defaultdict(list),
            'detection_times': defaultdict(list),
            'browser_performance': defaultdict(dict),
        }
    
    def load_stats(self) -> Dict:
        """Load persistent statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            'all_time': {
                'total_runtime': 0,
                'total_checks': 0,
                'tickets_by_category': {},
                'purchases_by_category': {},
                'average_response_time': 0,
                'best_hunting_hours': {},
            }
        }
    
    def update_ticket_found(self, category: str, details: Dict):
        """Update stats when ticket is found"""
        with self.lock:
            self.session_stats['tickets_found_by_category'][category] += 1
            self.stats['all_time']['tickets_by_category'][category] += 1
            
            # Track best hunting hours
            hour = datetime.now().hour
            self.stats['all_time']['best_hunting_hours'][str(hour)] += 1
    
    def update_check(self, category: str, response_time: float):
        """Update check statistics"""
        with self.lock:
            self.session_stats['checks_by_category'][category] += 1
            self.session_stats['response_times'][category].append(response_time)
    
    def get_category_stats(self, category: str) -> Dict:
        """Get statistics for specific category"""
        with self.lock:
            return {
                'session_checks': self.session_stats['checks_by_category'].get(category, 0),
                'session_found': self.session_stats['tickets_found_by_category'].get(category, 0),
                'session_purchased': self.session_stats['tickets_purchased_by_category'].get(category, 0),
                'all_time_found': self.stats['all_time']['tickets_by_category'].get(category, 0),
                'avg_response_time': self._calculate_avg_response_time(category),
            }
    
    def _calculate_avg_response_time(self, category: str) -> float:
        """Calculate average response time for category"""
        times = self.session_stats['response_times'].get(category, [])
        return sum(times) / len(times) if times else 0
    
    def save_stats(self):
        """Save statistics to file"""
        with self.lock:
            # Update all-time stats
            runtime = time.time() - self.session_stats['start_time']
            self.stats['all_time']['total_runtime'] += runtime
            
            # Convert defaultdicts to regular dicts for JSON serialization
            stats_to_save = {
                'all_time': {
                    'total_runtime': self.stats['all_time']['total_runtime'],
                    'total_checks': self.stats['all_time']['total_checks'],
                    'tickets_by_category': dict(self.stats['all_time']['tickets_by_category']),
                    'purchases_by_category': dict(self.stats['all_time']['purchases_by_category']),
                    'average_response_time': self.stats['all_time']['average_response_time'],
                    'best_hunting_hours': dict(self.stats['all_time']['best_hunting_hours']),
                }
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats_to_save, f, indent=2)

# ==================== Performance Optimizations ====================

class DOMCache:
    """Cache frequently accessed DOM elements"""
    
    def __init__(self, cache_duration: int = 30):
        self.cache = {}
        self.cache_duration = cache_duration
        self.lock = threading.Lock()
        
    def get(self, key: str, driver: uc.Chrome, selector: str, by: By = By.CSS_SELECTOR) -> List[WebElement]:
        """Get elements from cache or fetch if expired"""
        with self.lock:
            if key in self.cache:
                cached_time, elements = self.cache[key]
                if time.time() - cached_time < self.cache_duration:
                    # Verify elements are still valid
                    try:
                        if elements and elements[0].is_enabled():
                            return elements
                    except:
                        pass
            
            # Fetch fresh elements
            elements = driver.find_elements(by, selector)
            self.cache[key] = (time.time(), elements)
            return elements
    
    def invalidate(self, key: str = None):
        """Invalidate cache entries"""
        with self.lock:
            if key:
                self.cache.pop(key, None)
            else:
                self.cache.clear()

class MutationObserver:
    """Real-time DOM monitoring for instant ticket detection"""
    
    OBSERVER_SCRIPT = """
    if (!window.fansaleMutationObserver) {
        window.fansaleMutationObserver = new MutationObserver(function(mutations) {
            const ticketMutations = [];
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.getAttribute('data-qa') === 'ticketToBuy') {
                            ticketMutations.push({
                                type: 'ticket_added',
                                element: node,
                                timestamp: Date.now()
                            });
                        }
                    });
                }
            });
            
            if (ticketMutations.length > 0) {
                window.fansaleTicketQueue = window.fansaleTicketQueue || [];
                window.fansaleTicketQueue.push(...ticketMutations);
            }
        });
        
        window.fansaleMutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('FanSale Mutation Observer installed');
    }
    
    // Return any pending ticket mutations
    const queue = window.fansaleTicketQueue || [];
    window.fansaleTicketQueue = [];
    return queue;
    """
    
    @staticmethod
    def install(driver: uc.Chrome):
        """Install mutation observer on page"""
        try:
            driver.execute_script(MutationObserver.OBSERVER_SCRIPT)
            return True
        except:
            return False
    
    @staticmethod
    def check_mutations(driver: uc.Chrome) -> List[Dict]:
        """Check for new ticket mutations"""
        try:
            return driver.execute_script("return " + MutationObserver.OBSERVER_SCRIPT)
        except:
            return []

# ==================== Anti-Detection Features ====================

class HumanSimulator:
    """Simulate human-like behavior patterns"""
    
    def __init__(self, driver: uc.Chrome):
        self.driver = driver
        self.last_mouse_move = time.time()
        self.last_scroll = time.time()
        self.action_history = deque(maxlen=100)
        
    def simulate_mouse_movement(self):
        """Simulate natural mouse movements"""
        if time.time() - self.last_mouse_move < random.uniform(5, 15):
            return
            
        try:
            actions = ActionChains(self.driver)
            
            # Get viewport dimensions
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Generate natural curve path
            points = self._generate_bezier_curve(
                start=(random.randint(100, viewport_width-100), 
                       random.randint(100, viewport_height-100)),
                end=(random.randint(100, viewport_width-100), 
                     random.randint(100, viewport_height-100)),
                control_points=2
            )
            
            # Move along path
            for x, y in points:
                actions.move_by_offset(x - actions._pointer_location['x'], 
                                     y - actions._pointer_location['y'])
                actions.pause(random.uniform(0.01, 0.03))
            
            actions.perform()
            self.last_mouse_move = time.time()
            self.action_history.append(('mouse_move', time.time()))
            
        except Exception as e:
            pass
    
    def simulate_scrolling(self):
        """Simulate natural scrolling patterns"""
        if time.time() - self.last_scroll < random.uniform(10, 30):
            return
            
        try:
            # Random scroll amount
            scroll_amount = random.randint(-300, 300)
            
            # Smooth scroll
            self.driver.execute_script(f"""
                window.scrollBy({{
                    top: {scroll_amount},
                    behavior: 'smooth'
                }});
            """)
            
            self.last_scroll = time.time()
            self.action_history.append(('scroll', time.time()))
            
        except:
            pass
    
    def simulate_reading_pause(self):
        """Simulate pauses as if reading content"""
        if random.random() < 0.1:  # 10% chance
            pause_duration = random.gauss(2.5, 0.5)  # Normal distribution around 2.5s
            time.sleep(max(0.5, min(5.0, pause_duration)))
            self.action_history.append(('reading_pause', time.time()))
    
    def _generate_bezier_curve(self, start: Tuple[int, int], end: Tuple[int, int], 
                              control_points: int = 2) -> List[Tuple[int, int]]:
        """Generate smooth bezier curve for mouse movement"""
        try:
            import numpy as np
        except ImportError:
            # Fallback to simple linear path if numpy not installed
            return [start, end]
        
        # Generate random control points
        controls = []
        for _ in range(control_points):
            controls.append((
                random.randint(min(start[0], end[0]), max(start[0], end[0])),
                random.randint(min(start[1], end[1]), max(start[1], end[1]))
            ))
        
        # Create bezier curve
        points = [start] + controls + [end]
        n = len(points) - 1
        
        curve_points = []
        for t in np.linspace(0, 1, 20):  # 20 points along curve
            x = sum(self._bernstein(n, i, t) * points[i][0] for i in range(n + 1))
            y = sum(self._bernstein(n, i, t) * points[i][1] for i in range(n + 1))
            curve_points.append((int(x), int(y)))
        
        return curve_points
    
    def _bernstein(self, n: int, i: int, t: float) -> float:
        """Bernstein polynomial for bezier curves"""
        try:
            from math import comb
            return comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
        except ImportError:
            # Fallback for Python < 3.8
            from math import factorial
            return (factorial(n) / (factorial(i) * factorial(n - i))) * (t ** i) * ((1 - t) ** (n - i))

# ==================== Ticket Management ====================

@dataclass
class TicketInfo:
    """Enhanced ticket information structure"""
    id: str
    category: str
    raw_text: str
    section: str = ""
    row: str = ""
    seat: str = ""
    entrance: str = ""
    ring: str = ""
    price: float = 0.0
    score: float = 0.0
    detected_time: float = field(default_factory=time.time)
    browser_id: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'section': self.section,
            'row': self.row,
            'seat': self.seat,
            'entrance': self.entrance,
            'ring': self.ring,
            'price': self.price,
            'score': self.score,
            'detected_time': self.detected_time,
            'browser_id': self.browser_id
        }

class TicketParser:
    """Enhanced ticket parsing with better categorization"""
    
    CATEGORY_PATTERNS = {
        'prato_a': [
            r'prato\s*(?:gold\s*)?a\b',
            r'prato\s*a\s*gold',
            r'parterre\s*a\b'
        ],
        'prato_b': [
            r'prato\s*(?:gold\s*)?b\b',
            r'prato\s*b\s*gold',
            r'parterre\s*b\b'
        ],
        'settore': [
            r'settore',
            r'tribuna',
            r'anello\s*(?:rosso|blu|verde|giallo)',
            r'fila\s*\d+',
            r'posto\s*\d+',
            r'poltrona',
            r'numerato'
        ]
    }
    
    @classmethod
    def parse_ticket(cls, element: WebElement, browser_id: int) -> TicketInfo:
        """Parse ticket element into structured info"""
        try:
            raw_text = element.text
            ticket_id = hashlib.md5(raw_text.encode()).hexdigest()[:8]
            
            # Categorize ticket
            category = cls._categorize_ticket(raw_text)
            
            # Extract details
            info = TicketInfo(
                id=ticket_id,
                category=category,
                raw_text=raw_text,
                browser_id=browser_id
            )
            
            # Parse specific fields
            cls._extract_details(raw_text, info)
            
            # Calculate score
            info.score = cls._calculate_ticket_score(info)
            
            return info
            
        except Exception as e:
            # Return basic info on error
            return TicketInfo(
                id=hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                category='other',
                raw_text=str(element.text),
                browser_id=browser_id
            )
    
    @classmethod
    def _categorize_ticket(cls, text: str) -> str:
        """Categorize ticket based on text patterns"""
        text_lower = text.lower()
        
        for category, patterns in cls.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return category
        
        return 'other'
    
    @classmethod
    def _extract_details(cls, text: str, info: TicketInfo):
        """Extract detailed information from ticket text"""
        lines = text.split('\n')
        
        for line in lines:
            # Section
            if match := re.search(r'(prato|settore|tribuna|parterre)\s*(.+)', line, re.I):
                info.section = match.group(0).strip()
            
            # Row/Fila
            if match := re.search(r'fila\s*[:\s]*(\w+)', line, re.I):
                info.row = match.group(1)
            
            # Seat/Posto
            if match := re.search(r'posto\s*[:\s]*(\d+)', line, re.I):
                info.seat = match.group(1)
            
            # Entrance/Ingresso
            if match := re.search(r'ingresso\s*[:\s]*(\d+)', line, re.I):
                info.entrance = match.group(1)
            
            # Ring/Anello
            if match := re.search(r'(\d+\s*anello\s*\w+)', line, re.I):
                info.ring = match.group(1)
            
            # Price
            if match := re.search(r'(\d+[,.]?\d*)\s*€', line):
                try:
                    info.price = float(match.group(1).replace(',', '.'))
                except:
                    pass
    
    @classmethod
    def _calculate_ticket_score(cls, info: TicketInfo) -> float:
        """Calculate ticket desirability score"""
        score = 100.0
        
        # Category scoring
        category_scores = {
            'prato_a': 30,
            'prato_b': 25,
            'settore': 20,
            'other': 10
        }
        score += category_scores.get(info.category, 0)
        
        # Price scoring (lower is better)
        if info.price > 0:
            if info.price < 100:
                score += 20
            elif info.price < 150:
                score += 15
            elif info.price < 200:
                score += 10
            elif info.price < 300:
                score += 5
        
        # Seat quality scoring for settore
        if info.category == 'settore':
            # Lower row numbers are better
            try:
                row_num = int(re.search(r'\d+', info.row).group() if info.row else '99')
                if row_num <= 5:
                    score += 15
                elif row_num <= 10:
                    score += 10
                elif row_num <= 20:
                    score += 5
            except:
                pass
            
            # Central seats are better
            try:
                seat_num = int(info.seat) if info.seat else 0
                if 10 <= seat_num <= 30:
                    score += 10
            except:
                pass
        
        return score

# ==================== Main Bot Class ====================

class FanSaleBotV6:
    """Enhanced FanSale Bot with V6 improvements"""
    
    def __init__(self):
        self.config = BotConfig.from_file(Path("bot_config_v6.json"))
        self.target_url = os.getenv('FANSALE_URL', '')
        
        # Debug: Print environment loading
        if not self.target_url:
            print("⚠️ WARNING: FANSALE_URL environment variable not loaded!")
            print("Current working directory:", os.getcwd())
            print("Looking for .env file at:", Path(".env").absolute())
            if Path(".env").exists():
                print("✅ .env file exists")
                # Try reloading
                load_dotenv(override=True)
                self.target_url = os.getenv('FANSALE_URL', '')
                if self.target_url:
                    print("✅ FANSALE_URL loaded after reload:", self.target_url[:50], "...")
            else:
                print("❌ .env file not found!")
        
        # Core components
        self.category_logger = CategoryLogger()
        self.stats_manager = EnhancedStatsManager()
        self.dom_cache = DOMCache(self.config.dom_cache_duration)
        
        # Browser management
        self.browsers = []
        self.browser_simulators = {}
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.coordination_lock = threading.Lock()
        
        # Ticket tracking
        self.seen_tickets = set()
        self.active_purchases = set()
        self.ticket_scores = {}
        self.tickets_secured = 0
        
        # Performance tracking
        self.performance_metrics = defaultdict(lambda: deque(maxlen=100))
        
        # Filters
        self.ticket_filters = {
            'categories': set(),
            'max_price': float('inf'),
            'min_score': 0.0,
            'preferred_sections': set(),
            'excluded_sections': set()
        }
        
        # 2Captcha setup
        self.captcha_solver = None
        if self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY'):
            try:
                from twocaptcha import TwoCaptcha
                api_key = self.config.twocaptcha_api_key or os.getenv('TWOCAPTCHA_API_KEY', '')
                self.captcha_solver = TwoCaptcha(api_key)
                self.category_logger.log_ticket('system', 
                    f"2Captcha configured with API key: {api_key[:8]}...")
            except ImportError:
                self.category_logger.log_ticket('system',
                    "⚠️ 2captcha module not installed. Run: pip install 2captcha-python", 'warning')
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser with V6 enhancements"""
        self.category_logger.log_ticket('system', f"Creating Browser {browser_id}...")
        
        try:
            options = uc.ChromeOptions()
            options.headless = False
            
            # Enhanced stealth options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu-sandbox')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            
            # Performance options
            options.add_argument('--disable-logging')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # Enable images
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 1,
                    'plugins': 1,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2,
                    'media_stream': 2,
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
            driver = uc.Chrome(options=options, version_main=137)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(5)
            
            # Inject advanced stealth scripts
            self._inject_stealth_scripts(driver)
            
            # Create human simulator
            self.browser_simulators[browser_id] = HumanSimulator(driver)
            
            # Navigate to target URL immediately to show it's working
            if self.target_url:
                try:
                    self.category_logger.log_ticket('system',
                        f"🌐 Browser {browser_id}: Loading {self.target_url[:50]}...")
                    driver.get(self.target_url)
                    self.category_logger.log_ticket('system',
                        f"✅ Browser {browser_id} created and loaded at position ({x}, {y})")
                except Exception as e:
                    self.category_logger.log_ticket('system',
                        f"⚠️ Browser {browser_id}: Created but failed to load page: {e}", 'warning')
            else:
                self.category_logger.log_ticket('system', 
                    f"✅ Browser {browser_id} created at position ({x}, {y})")
            
            return driver
            
        except Exception as e:
            self.category_logger.log_ticket('system', 
                f"❌ Failed to create browser {browser_id}: {e}", 'error')
            return None
    
    def _inject_stealth_scripts(self, driver: uc.Chrome):
        """Inject advanced stealth JavaScript"""
        stealth_script = """
        // Remove webdriver traces
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete navigator.__proto__.webdriver;
        
        // Mock plugins realistically
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [];
                for (let i = 0; i < 5; i++) {
                    plugins.push({
                        name: `Chrome Plugin ${i}`,
                        description: `Chromium Plugin ${i}`,
                        filename: `plugin${i}.dll`,
                        version: '1.0.0.0'
                    });
                }
                return plugins;
            }
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'it-IT', 'it']
        });
        
        // Mock hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        
        // Mock device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        
        // Override permission query
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Add chrome object
        window.chrome = {
            runtime: {id: 'aapnijgdinlhnhlmodcfapnahmbfebeb'},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Remove automation flags
        ['webdriver', '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', 
         '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped', 
         '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder', 
         '_selenium', 'calledSelenium', '$chrome_asyncScriptInfo', 
         '$cdc_asdjflasutopfhvcZLmcfl_'].forEach(prop => {
            delete window[prop];
            delete document[prop];
        });
        
        // Override toString methods
        window.navigator.permissions.query.toString = () => 'function query() { [native code] }';
        """
        
        driver.execute_script(stealth_script)
    
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Enhanced hunting loop with V6 features"""
        self.category_logger.log_ticket('system', 
            f"🎯 Hunter {browser_id} starting enhanced hunt...")
        
        # Check if target URL is set
        if not self.target_url:
            self.category_logger.log_ticket('system',
                f"❌ Hunter {browser_id}: No target URL set!", 'error')
            return
        
        # Re-navigate to target (already loaded in create_browser)
        self.category_logger.log_ticket('system',
            f"🔄 Hunter {browser_id}: Refreshing page for hunt...")
        try:
            driver.refresh()  # Just refresh since we already loaded it
            time.sleep(2)
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"⚠️ Hunter {browser_id}: Refresh failed, attempting full navigation: {e}", 'warning')
            try:
                driver.get(self.target_url)
                time.sleep(2)
            except Exception as nav_error:
                self.category_logger.log_ticket('system',
                    f"❌ Hunter {browser_id}: Failed to navigate: {nav_error}", 'error')
                return
        
        # Install mutation observer if enabled
        if self.config.use_mutation_observer:
            MutationObserver.install(driver)
            self.category_logger.log_ticket('system', 
                f"🔍 Mutation Observer installed for Browser {browser_id}")
        
        # Initialize hunting variables
        check_count = 0
        last_refresh = time.time()
        last_captcha_check = time.time()
        last_popup_check = time.time()
        simulator = self.browser_simulators.get(browser_id)
        
        # Category-specific counters
        category_checks = defaultdict(int)
        category_found = defaultdict(int)
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.config.max_tickets:
            try:
                check_start = time.time()
                
                # Human simulation
                if simulator and self.config.enable_mouse_simulation:
                    if random.random() < 0.3:  # 30% chance per iteration
                        simulator.simulate_mouse_movement()
                    if random.random() < 0.2:  # 20% chance
                        simulator.simulate_scrolling()
                
                # Check for mutations first (instant detection)
                if self.config.use_mutation_observer:
                    mutations = MutationObserver.check_mutations(driver)
                    if mutations:
                        self.category_logger.log_ticket('system',
                            f"⚡ Mutation detected! {len(mutations)} new tickets")
                
                # Traditional ticket search
                tickets = self._find_tickets(driver, browser_id)
                
                for ticket_element in tickets:
                    # Parse ticket
                    ticket_info = TicketParser.parse_ticket(ticket_element, browser_id)
                    
                    # Update category check count
                    category_checks[ticket_info.category] += 1
                    
                    # Check if new ticket
                    if ticket_info.id not in self.seen_tickets:
                        self._process_new_ticket(ticket_info, ticket_element, driver, browser_id)
                        category_found[ticket_info.category] += 1
                
                # Update performance metrics
                check_time = time.time() - check_start
                self.performance_metrics[f'browser_{browser_id}_check_time'].append(check_time)
                
                # Periodic tasks
                if time.time() - last_popup_check > self.config.popup_check_interval:
                    self._dismiss_popups(driver, browser_id)
                    last_popup_check = time.time()
                
                if browser_id == 1 and time.time() - last_captcha_check > self.config.captcha_check_interval:
                    self._check_captcha(driver, browser_id)
                    last_captcha_check = time.time()
                
                # Smart refresh
                if self._should_refresh(last_refresh, check_count):
                    driver.refresh()
                    last_refresh = time.time()
                    time.sleep(1)
                    
                    # Reinstall mutation observer
                    if self.config.use_mutation_observer:
                        MutationObserver.install(driver)
                
                # Progress logging every 60 checks
                check_count += 1
                if check_count % 60 == 0:
                    self._log_hunting_progress(browser_id, check_count, 
                                             category_checks, category_found)
                
                # Adaptive wait time
                wait_time = self._calculate_wait_time(check_count, category_found)
                time.sleep(wait_time)
                
            except Exception as e:
                self.category_logger.log_ticket('system',
                    f"❌ Hunter {browser_id} error: {e}", 'error')
                time.sleep(5)
    
    def _find_tickets(self, driver: uc.Chrome, browser_id: int) -> List[WebElement]:
        """Find tickets with caching optimization"""
        cache_key = f"browser_{browser_id}_tickets"
        
        # Try cached elements first
        if self.config.dom_cache_duration > 0:
            tickets = self.dom_cache.get(
                cache_key, 
                driver, 
                "div[data-qa='ticketToBuy']"
            )
        else:
            tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
        
        return tickets
    
    def _process_new_ticket(self, ticket_info: TicketInfo, element: WebElement, 
                           driver: uc.Chrome, browser_id: int):
        """Process newly discovered ticket"""
        # Mark as seen
        self.seen_tickets.add(ticket_info.id)
        
        # Log discovery
        self.category_logger.log_alert(ticket_info.category,
            f"NEW TICKET FOUND by Hunter {browser_id}!")
        self._log_ticket_details(ticket_info)
        
        # Update statistics
        self.stats_manager.update_ticket_found(ticket_info.category, ticket_info.to_dict())
        
        # Check if we should purchase
        if self._should_purchase_ticket(ticket_info):
            self._attempt_purchase(ticket_info, element, driver, browser_id)
    
    def _log_ticket_details(self, ticket: TicketInfo):
        """Log ticket details with enhanced formatting"""
        details = []
        
        if ticket.section:
            details.append(f"Section: {ticket.section}")
        if ticket.entrance:
            details.append(f"Entrance: {ticket.entrance}")
        if ticket.row:
            details.append(f"Row: {ticket.row}")
        if ticket.seat:
            details.append(f"Seat: {ticket.seat}")
        if ticket.ring:
            details.append(f"Ring: {ticket.ring}")
        if ticket.price > 0:
            details.append(f"Price: €{ticket.price:.2f}")
        
        details.append(f"Score: {ticket.score:.1f}")
        
        detail_str = " | ".join(details)
        self.category_logger.log_ticket(ticket.category, f"└─ {detail_str}")
        self.category_logger.log_ticket(ticket.category, "─" * 60)
    
    def _should_purchase_ticket(self, ticket: TicketInfo) -> bool:
        """Determine if ticket should be purchased based on filters"""
        # Check category filter
        if ticket.category not in self.ticket_filters['categories']:
            return False
        
        # Check price filter
        if ticket.price > self.ticket_filters['max_price']:
            return False
        
        # Check score filter
        if ticket.score < self.ticket_filters['min_score']:
            return False
        
        # Check section filters
        if self.ticket_filters['preferred_sections']:
            if not any(pref in ticket.section.lower() 
                      for pref in self.ticket_filters['preferred_sections']):
                return False
        
        if self.ticket_filters['excluded_sections']:
            if any(excl in ticket.section.lower() 
                  for excl in self.ticket_filters['excluded_sections']):
                return False
        
        return True
    
    def _attempt_purchase(self, ticket: TicketInfo, element: WebElement, 
                         driver: uc.Chrome, browser_id: int):
        """Attempt to purchase ticket with coordination"""
        with self.coordination_lock:
            # Check if already being purchased
            if ticket.id in self.active_purchases:
                self.category_logger.log_ticket(ticket.category,
                    f"Ticket already being purchased by another browser")
                return
            
            # Check ticket limit
            if self.tickets_secured >= self.config.max_tickets:
                return
            
            # Mark as active purchase
            self.active_purchases.add(ticket.id)
        
        try:
            self.category_logger.log_ticket(ticket.category,
                f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click ticket
            driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            
            # Look for purchase button
            purchase_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "button[data-qa='ticketCheckoutButton'], " +
                    "button.checkout-button, " +
                    "button[class*='purchase']"))
            )
            
            driver.execute_script("arguments[0].click();", purchase_btn)
            
            # Success!
            self.tickets_secured += 1
            self.stats_manager.session_stats['tickets_purchased_by_category'][ticket.category] += 1
            
            self.category_logger.log_alert(ticket.category,
                f"🎉 TICKET PURCHASED! ({self.tickets_secured}/{self.config.max_tickets})")
            
        except Exception as e:
            self.category_logger.log_ticket(ticket.category,
                f"Purchase failed: {e}", 'error')
        finally:
            # Remove from active purchases
            with self.coordination_lock:
                self.active_purchases.discard(ticket.id)
    
    def _should_refresh(self, last_refresh: float, check_count: int) -> bool:
        """Smart refresh decision based on activity"""
        time_since_refresh = time.time() - last_refresh
        
        if not self.config.smart_refresh:
            return time_since_refresh > self.config.refresh_interval
        
        # Adaptive refresh based on ticket discovery rate
        recent_discoveries = sum(len([m for m in metrics if m > time.time() - 60])
                               for metrics in self.performance_metrics.values()
                               if 'discovery' in str(metrics))
        
        if recent_discoveries > 5:
            # Many discoveries - refresh less often
            return time_since_refresh > self.config.refresh_interval * 1.5
        elif recent_discoveries == 0 and check_count > 100:
            # No discoveries - refresh more often
            return time_since_refresh > self.config.refresh_interval * 0.7
        else:
            return time_since_refresh > self.config.refresh_interval
    
    def _calculate_wait_time(self, check_count: int, category_found: Dict[str, int]) -> float:
        """Calculate adaptive wait time"""
        base_wait = random.uniform(self.config.min_wait, self.config.max_wait)
        
        # Reduce wait if we're finding tickets
        if sum(category_found.values()) > 0:
            base_wait *= 0.7
        
        # Add small random variation
        return base_wait + random.uniform(-0.1, 0.1)
    
    def _log_hunting_progress(self, browser_id: int, check_count: int,
                            category_checks: Dict[str, int], 
                            category_found: Dict[str, int]):
        """Log hunting progress with category breakdown"""
        # Calculate rates
        elapsed = time.time() - self.stats_manager.session_stats['start_time']
        overall_rate = (check_count * 60) / elapsed if elapsed > 0 else 0
        
        # Build category summary
        category_summary = []
        for category in ['prato_a', 'prato_b', 'settore', 'other']:
            checks = category_checks.get(category, 0)
            found = category_found.get(category, 0)
            if checks > 0:
                category_summary.append(
                    f"{category.upper()}: {found}/{checks}"
                )
        
        summary = f"Hunter {browser_id} Progress: "
        summary += f"{check_count} checks @ {overall_rate:.1f}/min | "
        summary += " | ".join(category_summary)
        
        self.category_logger.log_ticket('system', summary)
    
    def _dismiss_popups(self, driver: uc.Chrome, browser_id: int):
        """Dismiss popups with enhanced detection"""
        dismissed = 0
        
        # Popup patterns
        popup_selectors = [
            # Carica Offerte button
            "button.js-BotProtectionModalButton1",
            "button[name='_submit'][value='true']",
            # General popups
            "div[class*='modal']:not([style*='display: none'])",
            "div[class*='popup']:not([style*='display: none'])",
            "div[class*='overlay']:not([style*='display: none'])",
            # Cookie banners
            "div[class*='cookie']",
            "div[class*='gdpr']",
            # Close buttons
            "button[class*='close']:visible",
            "button[aria-label*='close' i]",
            "button[aria-label*='chiudi' i]"
        ]
        
        for selector in popup_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
                        dismissed += 1
                        time.sleep(0.2)
            except:
                pass
        
        if dismissed > 0:
            self.category_logger.log_ticket('system',
                f"📢 Dismissed {dismissed} popups for Browser {browser_id}")
        
        return dismissed
    
    def _check_captcha(self, driver: uc.Chrome, browser_id: int):
        """Check for CAPTCHA presence"""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "div[class*='g-recaptcha']",
            "div[id*='captcha']",
            "#captcha",
            "img[src*='captcha']"
        ]
        
        for selector in captcha_selectors:
            try:
                captcha = driver.find_element(By.CSS_SELECTOR, selector)
                if captcha.is_displayed():
                    self.category_logger.log_alert('system',
                        f"CAPTCHA detected on Browser {browser_id}!")
                    
                    if self.captcha_solver and self.config.auto_solve_captcha:
                        self._solve_captcha_auto(driver, browser_id)
                    else:
                        self._wait_for_manual_captcha(driver, browser_id)
                    
                    return True
            except:
                pass
        
        return False
    
    def _solve_captcha_auto(self, driver: uc.Chrome, browser_id: int):
        """Automatically solve CAPTCHA using 2captcha"""
        try:
            # Get site key
            site_key = driver.find_element(
                By.CSS_SELECTOR, 
                "[data-sitekey]"
            ).get_attribute("data-sitekey")
            
            # Solve
            self.category_logger.log_ticket('system',
                "🤖 Solving CAPTCHA automatically...")
            
            result = self.captcha_solver.recaptcha(
                sitekey=site_key,
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
            
            self.category_logger.log_alert('system',
                "✅ CAPTCHA solved automatically!")
            
        except Exception as e:
            self.category_logger.log_ticket('system',
                f"Auto-solve failed: {e}", 'error')
            self._wait_for_manual_captcha(driver, browser_id)
    
    def _wait_for_manual_captcha(self, driver: uc.Chrome, browser_id: int):
        """Wait for manual CAPTCHA solving"""
        self.category_logger.log_alert('system',
            f"⏳ Waiting for manual CAPTCHA solve on Browser {browser_id}...")
        
        # Wait up to 5 minutes
        for i in range(300):
            if not self._check_captcha(driver, browser_id):
                self.category_logger.log_alert('system',
                    "✅ CAPTCHA solved!")
                break
            time.sleep(1)
    
    def show_live_dashboard(self):
        """Display live statistics dashboard"""
        while not self.shutdown_event.is_set():
            # Clear screen (works on most terminals)
            print("\033[2J\033[H")
            
            # Header
            print("=" * 80)
            print("🎫 FANSALE BOT V6 - LIVE DASHBOARD".center(80))
            print("=" * 80)
            
            # Runtime
            runtime = time.time() - self.stats_manager.session_stats['start_time']
            hours = int(runtime // 3600)
            minutes = int((runtime % 3600) // 60)
            seconds = int(runtime % 60)
            print(f"\n⏱️  Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            print(f"🎯 Tickets Secured: {self.tickets_secured}/{self.config.max_tickets}")
            
            # Category Statistics
            print("\n📊 CATEGORY BREAKDOWN:")
            print("-" * 60)
            
            categories = ['prato_a', 'prato_b', 'settore', 'other']
            headers = ['Category', 'Checks', 'Found', 'Purchased', 'Avg Response']
            
            # Print headers
            print(f"{headers[0]:12} {headers[1]:>10} {headers[2]:>10} {headers[3]:>12} {headers[4]:>13}")
            print("-" * 60)
            
            # Print category stats
            for category in categories:
                stats = self.stats_manager.get_category_stats(category)
                cat_display = category.replace('_', ' ').title()
                
                print(f"{cat_display:12} "
                      f"{stats['session_checks']:>10,} "
                      f"{stats['session_found']:>10} "
                      f"{stats['session_purchased']:>12} "
                      f"{stats['avg_response_time']:>13.3f}s")
            
            # Performance Metrics
            print("\n⚡ PERFORMANCE:")
            print("-" * 60)
            
            # Calculate average check time per browser
            for browser_id in range(1, len(self.browsers) + 1):
                key = f'browser_{browser_id}_check_time'
                if key in self.performance_metrics:
                    times = list(self.performance_metrics[key])
                    if times:
                        avg_time = sum(times) / len(times)
                        rate = 60 / avg_time if avg_time > 0 else 0
                        print(f"Browser {browser_id}: {rate:.1f} checks/min "
                              f"(avg: {avg_time:.3f}s)")
            
            # Active purchases
            if self.active_purchases:
                print(f"\n🛒 Active Purchases: {len(self.active_purchases)}")
            
            # Best hunting hours
            print("\n📈 BEST HUNTING HOURS:")
            best_hours = sorted(
                self.stats_manager.stats['all_time']['best_hunting_hours'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            if best_hours:
                for hour, count in best_hours:
                    print(f"   {hour}:00 - {count} tickets found")
            
            print("\n" + "=" * 80)
            print("Press Ctrl+C to stop...")
            
            time.sleep(5)  # Update every 5 seconds
    
    def configure(self):
        """Interactive configuration with enhanced options"""
        print("\n" + "=" * 60)
        print("🎫 FANSALE BOT V6 - ENHANCED CONFIGURATION".center(60))
        print("=" * 60)
        
        # Show features
        print("\n✨ V6 FEATURES:")
        print("  • Separated logging for each ticket category")
        print("  • Ultra-fast checking (~150-300 checks/min)")
        print("  • Real-time DOM monitoring")
        print("  • Smart ticket prioritization")
        print("  • Human behavior simulation")
        print("  • Advanced filtering options")
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
            self.ticket_filters['categories'] = {'prato_a', 'prato_b', 'settore', 'other'}
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
            
            self.ticket_filters['categories'] = selected
            print(f"✅ Hunting for: {', '.join(selected)}")
        
        # Advanced filters
        if input("\n🔧 Configure advanced filters? (y/N): ").lower() == 'y':
            # Max price
            try:
                max_price = input("💰 Maximum price (€, or Enter for no limit): ").strip()
                if max_price:
                    self.ticket_filters['max_price'] = float(max_price)
                    print(f"✅ Max price set to €{self.ticket_filters['max_price']}")
            except:
                pass
            
            # Min score
            try:
                min_score = input("⭐ Minimum ticket score (0-150, default 0): ").strip()
                if min_score:
                    self.ticket_filters['min_score'] = float(min_score)
                    print(f"✅ Min score set to {self.ticket_filters['min_score']}")
            except:
                pass
        
        # Save configuration
        self.config.save(Path("bot_config_v6.json"))
        
        print("\n📋 CONFIGURATION SUMMARY:")
        print(f"  • Browsers: {self.config.browsers_count}")
        print(f"  • Max tickets: {self.config.max_tickets}")
        print(f"  • Categories: {', '.join(self.ticket_filters['categories'])}")
        print(f"  • Check rate: ~150-300 checks/min per browser")
        print(f"  • Smart features: {'ENABLED' if self.config.use_mutation_observer else 'DISABLED'}")
        print(f"  • Target URL: {self.target_url[:50] if self.target_url else 'NOT SET'}...")
    
    def run(self):
        """Main execution loop"""
        try:
            # Configure
            self.configure()
            
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
            
            # Start dashboard thread
            dashboard_thread = threading.Thread(
                target=self.show_live_dashboard,
                daemon=True
            )
            dashboard_thread.start()
            
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
            
            # Wait for completion
            print("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            try:
                while self.tickets_secured < self.config.max_tickets:
                    time.sleep(1)
                
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
            self.stats_manager.save_stats()
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
            
            print("\n👋 Goodbye!")

# ==================== Entry Point ====================

def main():
    """Entry point with enhanced startup"""
    print("\n" + "=" * 60)
    print("🎫 FANSALE BOT V6 - ENHANCED EDITION".center(60))
    print("=" * 60)
    
    # Check requirements
    if not os.getenv('FANSALE_URL'):
        print("\n❌ ERROR: FANSALE_URL not set in .env file!")
        print("Please set: FANSALE_URL=https://www.fansale.it/fansale/...")
        return
    
    # Check for 2captcha
    if os.getenv('TWOCAPTCHA_API_KEY'):
        print("\n✅ 2Captcha API key found")
    else:
        print("\n⚠️  No 2Captcha API key - manual CAPTCHA solving only")
    
    print(f"\n🎯 Target URL: {os.getenv('FANSALE_URL')[:50]}...")
    
    # Create and run bot
    bot = FanSaleBotV6()
    bot.run()

if __name__ == "__main__":
    main()
