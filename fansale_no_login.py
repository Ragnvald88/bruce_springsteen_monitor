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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

# Suppress verbose logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement

from dotenv import load_dotenv
load_dotenv()

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
    
    def __init__(self):
        # Get target URL from env or use default
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554")
        
        # Configuration
        self.num_browsers = 1
        self.max_tickets = 4
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
        
        # Load persistent statistics
        self.stats_file = Path("fansale_stats.json")
        self.load_stats()
        
        # Performance monitoring
        self.session_start_time = time.time()

    def load_stats(self):
        """Load persistent statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    # Merge with default stats structure
                    self.stats = {
                        'total_checks': saved_stats.get('total_checks', 0),
                        'total_tickets_found': saved_stats.get('total_tickets_found', 0),
                        'unique_tickets_found': saved_stats.get('unique_tickets_found', 0),
                        'tickets_by_type': {
                            'prato_a': saved_stats.get('tickets_by_type', {}).get('prato_a', 0),
                            'prato_b': saved_stats.get('tickets_by_type', {}).get('prato_b', 0),
                            'settore': saved_stats.get('tickets_by_type', {}).get('settore', 0),
                            'other': saved_stats.get('tickets_by_type', {}).get('other', 0)
                        },
                        'purchases': saved_stats.get('purchases', 0),
                        'blocks_encountered': saved_stats.get('blocks_encountered', 0),
                        'all_time_runtime': saved_stats.get('all_time_runtime', 0)
                    }
                logger.info(f"📊 Loaded stats: {self.stats['unique_tickets_found']} unique tickets tracked historically")
            except Exception as e:
                logger.warning(f"Could not load stats: {e}, starting fresh")
                self.init_fresh_stats()
        else:
            self.init_fresh_stats()
    
    def init_fresh_stats(self):
        """Initialize fresh statistics structure"""
        self.stats = {
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
    
    def save_stats(self):
        """Save statistics to file"""
        try:
            # Update runtime
            session_time = time.time() - self.session_start_time
            self.stats['all_time_runtime'] += session_time
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
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
        # Check for Settore
        elif 'settore' in ticket_lower or 'settore numerato' in ticket_lower:
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
                'category': 'other'
            }
            
            # Get all text from the ticket element
            full_text = ticket_element.text
            ticket_info['raw_text'] = full_text
            
            # Try to extract structured data
            lines = full_text.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                
                # Extract section info
                if any(x in line_lower for x in ['prato', 'settore', 'tribuna', 'parterre']):
                    ticket_info['section'] = line.strip()
                
                # Extract row/fila
                if 'fila' in line_lower or 'row' in line_lower:
                    match = re.search(r'(?:fila|row)\s*[:\s]*(\w+)', line, re.I)
                    if match:
                        ticket_info['row'] = match.group(1)
                
                # Extract seat/posto
                if 'posto' in line_lower or 'seat' in line_lower:
                    match = re.search(r'(?:posto|seat)\s*[:\s]*(\d+)', line, re.I)
                    if match:
                        ticket_info['seat'] = match.group(1)
                
                # Extract price
                if '€' in line or 'eur' in line_lower:
                    match = re.search(r'(\d+[,.]?\d*)\s*€', line)
                    if match:
                        ticket_info['price'] = match.group(0)
            
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
                'category': 'other'
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
        if ticket_info['row']:
            details.append(f"Row: {ticket_info['row']}")
        if ticket_info['seat']:
            details.append(f"Seat: {ticket_info['seat']}")
        if ticket_info['price']:
            details.append(f"Price: {ticket_info['price']}")
        
        detail_str = " | ".join(details) if details else ticket_info['raw_text'][:100]
        
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
            logger.info(f"🎫 NEW TICKET - SETTORE{hunt_indicator} - Hunter {browser_id}")
            logger.info(f"   └─ {detail_str}")
            logger.info("   " + "─" * 60)
        else:
            logger.info(f"🎫 NEW TICKET - OTHER{hunt_indicator} - Hunter {browser_id}")
            logger.info(f"   └─ {detail_str}")
            logger.info("   " + "─" * 60)
    
    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser with multi-monitor support"""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
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
        # Arrange browsers in a grid pattern across monitors
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
        
        try:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(20)
            
            # Inject stealth JavaScript
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
            
            logger.info(f"✅ Browser {browser_id} ready at position ({x}, {y})")
            return driver
            
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
        except:
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
            time.sleep(1)
            
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
        time.sleep(3)
        
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
                    time.sleep(3)
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
                    logger.info(f"📊 Hunter {browser_id}: {check_count} checks @ {rate:.1f}/min | {local_str}")
                    
            except TimeoutException:
                logger.warning(f"Hunter {browser_id}: Page timeout, refreshing...")
                driver.refresh()
                time.sleep(2)
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    logger.error(f"Hunter {browser_id}: Session died")
                    break
                logger.error(f"Hunter {browser_id}: Browser error, continuing...")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                time.sleep(5)
    
    def purchase_ticket(self, driver: uc.Chrome, ticket_element, browser_id: int) -> bool:
        """Attempt to purchase a ticket"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click the ticket
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            driver.execute_script("arguments[0].click();", ticket_element)
            time.sleep(1)
            
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
                    
                except:
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
        
        if self.stats['total_checks'] > 0:
            rate = self.stats['total_checks'] / (total_runtime / 60) if total_runtime > 0 else 0
            print(f"\n{Colors.BOLD}⚡ Average Rate:{Colors.END} {rate:.1f} checks/min")
        
        print(f"\n{Colors.BOLD}{'═' * 60}{Colors.END}\n")
    
    def configure_ticket_filters(self):
        """Configure which ticket types to hunt for"""
        print(f"\n{Colors.BOLD}🎯 TICKET TYPE SELECTION{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 50}{Colors.END}")
        print("\nAvailable ticket types:")
        print(f"  1. {Colors.GREEN}Prato A{Colors.END} - Usually front lawn/standing area")
        print(f"  2. {Colors.BLUE}Prato B{Colors.END} - Usually back lawn/standing area")
        print(f"  3. {Colors.YELLOW}Settore{Colors.END} - Numbered sector seats")
        print(f"  4. {Colors.CYAN}All types{Colors.END} - Hunt for any of the above")
        print(f"  5. {Colors.RED}Other/Unknown{Colors.END} - Tickets that don't match above categories")
        
        while True:
            choice = input(f"\n{Colors.BOLD}Select ticket types to hunt (comma-separated, e.g., 1,2 or 4 for all):{Colors.END} ").strip()
            
            if not choice:
                print(f"{Colors.RED}❌ Please make a selection{Colors.END}")
                continue
                
            try:
                selections = [int(x.strip()) for x in choice.split(',')]
                
                # Validate selections
                if any(s < 1 or s > 5 for s in selections):
                    print(f"{Colors.RED}❌ Invalid selection. Please use numbers 1-5{Colors.END}")
                    continue
                
                # Process selections
                self.ticket_types_to_hunt.clear()
                
                if 4 in selections:  # All types
                    self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore'}
                    print(f"\n{Colors.GREEN}✅ Hunting for: ALL ticket types (Prato A, B, Settore){Colors.END}")
                else:
                    type_map = {
                        1: 'prato_a',
                        2: 'prato_b', 
                        3: 'settore',
                        5: 'other'
                    }
                    
                    for s in selections:
                        if s in type_map:
                            self.ticket_types_to_hunt.add(type_map[s])
                    
                    # Display selected types
                    display_names = {
                        'prato_a': f"{Colors.GREEN}Prato A{Colors.END}",
                        'prato_b': f"{Colors.BLUE}Prato B{Colors.END}",
                        'settore': f"{Colors.YELLOW}Settore{Colors.END}",
                        'other': f"{Colors.RED}Other/Unknown{Colors.END}"
                    }
                    
                    selected_display = [display_names[t] for t in self.ticket_types_to_hunt]
                    print(f"\n{Colors.GREEN}✅ Hunting for: {', '.join(selected_display)}{Colors.END}")
                
                break
                
            except ValueError:
                print(f"{Colors.RED}❌ Invalid input. Please enter numbers separated by commas{Colors.END}")

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
        print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 FANSALE BOT - ENHANCED EDITION{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 50}{Colors.END}")
        print("\n✨ Features:")
        print("  • No login required")
        print("  • Tracks Prato A, Prato B, and Settore tickets")
        print("  • Avoids duplicate logging")
        print("  • Persistent statistics across restarts")
        
        # Show current stats
        self.show_statistics_dashboard()
        
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
        
2

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
                except:
                    pass
            
            # Show final statistics
            print(f"\n{Colors.BOLD}{Colors.CYAN}📊 FINAL SESSION STATISTICS{Colors.END}")
            self.show_statistics_dashboard()


def main():
    """Entry point"""
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🎫 FANSALE BOT - ENHANCED NO LOGIN EDITION{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"\n{Colors.GREEN}✨ Featuring:{Colors.END}")
    print("  • Ticket type tracking (Prato A, B, Settore)")
    print("  • Duplicate detection")
    print("  • Persistent statistics")
    print("  • Multi-monitor support")
    
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
    
    # Check for target URL
    if not os.getenv('FANSALE_TARGET_URL'):
        print(f"\n{Colors.YELLOW}⚠️  No target URL in .env file{Colors.END}")
        print("Using default Bruce Springsteen URL")
        print("To change, add to .env file:")
        print("FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/...")
        time.sleep(2)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()