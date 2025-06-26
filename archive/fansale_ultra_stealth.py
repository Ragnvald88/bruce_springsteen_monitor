#!/usr/bin/env python3
"""
FanSale Ticket Hunter Bot - Ultra Stealth Version
Advanced anti-detection with human-like behavior
"""

import json
import time
import random
import logging
import hashlib
import os
import sys
import threading
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class BotConfig:
    """Bot configuration with stealth settings"""
    def __init__(self):
        self.browsers_count = 1  # Start with 1 for stealth
        self.max_tickets = 4
        self.refresh_interval = 60  # seconds
        self.session_timeout = 900  # 15 minutes
        
        # Stealth check frequency settings
        self.checks_per_minute = 40  # Much slower for stealth
        self.min_wait = 1.2  # Longer minimum wait
        self.max_wait = 3.5  # More variation
        
        # Human-like behavior
        self.human_mode = True
        self.random_actions = True
        self.mouse_movements = True
        
        # Logging settings
        self.log_level = "INFO"
        self.status_update_interval = 25  # Less frequent updates
        self.detailed_logging = False
        self.debug_mode = False
        
        self.retry_attempts = 2
        self.retry_delay = 0.5
        self.ticket_types_to_hunt = ['prato_b', 'prato_a']
        self.ticket_filters = []
    
    def calculate_wait_time(self):
        """Calculate human-like wait time"""
        base_wait = 60.0 / self.checks_per_minute
        
        # Add more randomization for human-like behavior
        if self.human_mode:
            # Sometimes take longer pauses (human gets distracted)
            if random.random() < 0.1:  # 10% chance
                return random.uniform(5.0, 10.0)  # Long pause
            elif random.random() < 0.2:  # 20% chance
                return random.uniform(3.0, 5.0)  # Medium pause
        
        # Normal variation
        return random.uniform(self.min_wait, self.max_wait)
    
    def to_dict(self):
        return {
            'browsers_count': self.browsers_count,
            'max_tickets': self.max_tickets,
            'refresh_interval': self.refresh_interval,
            'session_timeout': self.session_timeout,
            'checks_per_minute': self.checks_per_minute,
            'min_wait': self.min_wait,
            'max_wait': self.max_wait,
            'human_mode': self.human_mode,
            'random_actions': self.random_actions,
            'mouse_movements': self.mouse_movements,
            'log_level': self.log_level,
            'status_update_interval': self.status_update_interval,
            'detailed_logging': self.detailed_logging,
            'debug_mode': self.debug_mode,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'ticket_types_to_hunt': self.ticket_types_to_hunt,
            'ticket_filters': self.ticket_filters
        }
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Configure logging
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)
logger.handlers.clear()

# Console handler
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('fansale_stealth.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(file_handler)

class StealthBot:
    """Ultra stealth bot with advanced anti-detection"""
    
    def __init__(self):
        self.config = BotConfig()
        self._load_saved_config()
        
        # Target URL
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
            'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388')
        
        # Initialize from config
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_types_to_hunt = self.config.ticket_types_to_hunt
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Tracking
        self.seen_tickets = set()
        self.session_start_time = time.time()
        
        # User agents pool
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def _load_saved_config(self):
        """Load saved configuration"""
        config_file = 'bot_config_stealth.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.config.from_dict(data)
                    logger.info("✅ Loaded saved configuration")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
    
    def _save_config(self):
        """Save current configuration"""
        try:
            with open('bot_config_stealth.json', 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            logger.info("✅ Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def create_stealth_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create ultra-stealth browser"""
        logger.info(f"🥷 Creating stealth browser {browser_id}...")
        
        try:
            # Random user agent
            user_agent = random.choice(self.user_agents)
            
            # Create options
            options = uc.ChromeOptions()
            
            # STEALTH FLAGS
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            
            # Exclude automation switches
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Stealth prefs
            prefs = {
                'credentials_enable_service': False,
                'profile.password_manager_enabled': False,
                'profile.default_content_setting_values.notifications': 2,
                'profile.default_content_settings.popups': 0,
                'profile.managed_default_content_settings.popups': 0
            }
            options.add_experimental_option('prefs', prefs)
            
            # Window size with slight randomization
            width = 1200 + random.randint(-50, 50)
            height = 800 + random.randint(-50, 50)
            options.add_argument(f'--window-size={width},{height}')
            
            # Random window position
            x = random.randint(0, 400)
            y = random.randint(0, 200)
            options.add_argument(f'--window-position={x},{y}')
            
            # Create driver
            driver = uc.Chrome(options=options, version_main=None)
            
            # CRITICAL: Advanced stealth JavaScript injection
            stealth_js = """
            // Overwrite the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}, 
                     description: "Portable Document Format", 
                     filename: "internal-pdf-viewer", 
                     length: 1, 
                     name: "Chrome PDF Plugin"},
                    {0: {type: "application/pdf", suffixes: "pdf", description: "", enabledPlugin: Plugin}, 
                     description: "", 
                     filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", 
                     length: 1, 
                     name: "Chrome PDF Viewer"}
                ]
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
            
            // Mock chrome object
            if (!window.chrome) {
                window.chrome = {};
            }
            window.chrome.runtime = {
                connect: () => {},
                sendMessage: () => {},
                onMessage: {
                    addListener: () => {}
                }
            };
            
            // Mock WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, [parameter]);
            };
            
            // Remove automation indicators
            ['webdriver', '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', 
             '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped', 
             '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder', 
             '_selenium', 'calledSelenium', '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw', 
             'driver-evaluate', 'webdriver-evaluate', 'selenium-evaluate', 
             'webdriverCommand', 'webdriver-evaluate-response', '__webdriverFunc', 
             '__webdriver_script_fn', '__$webdriverAsyncExecutor', '__lastWatirAlert', 
             '__lastWatirConfirm', '__lastWatirPrompt', '$chrome_asyncScriptInfo', 
             '$cdc_asdjflasutopfhvcZLmcfl_'].forEach(prop => {
                delete window[prop];
                delete document[prop];
            });
            """
            
            # Execute stealth script
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            
            # Set realistic viewport
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': width,
                'height': height,
                'deviceScaleFactor': 1,
                'mobile': False,
                'screenOrientation': {'type': 'landscapePrimary', 'angle': 0}
            })
            
            # Set timezone
            driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                'timezoneId': 'Europe/Rome'
            })
            
            # Test navigation
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 3))
            
            logger.info(f"✅ Stealth browser {browser_id} ready")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create stealth browser: {e}")
            return None

    
    def simulate_human_behavior(self, driver):
        """Simulate human-like interactions"""
        if not self.config.random_actions:
            return
        
        try:
            # Random mouse movements
            if self.config.mouse_movements and random.random() < 0.3:
                action = ActionChains(driver)
                
                # Move to random positions
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, 1000)
                    y = random.randint(100, 700)
                    action.move_by_offset(x, y)
                    action.pause(random.uniform(0.1, 0.3))
                
                action.perform()
            
            # Random scrolling
            if random.random() < 0.2:
                scroll_amount = random.randint(100, 500)
                direction = random.choice([1, -1])
                driver.execute_script(f"window.scrollBy(0, {scroll_amount * direction})")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Random tab switching (simulate checking other tabs)
            if random.random() < 0.05:  # 5% chance
                driver.execute_script("window.open('');")
                time.sleep(random.uniform(1, 2))
                driver.switch_to.window(driver.window_handles[0])
                
        except Exception as e:
            logger.debug(f"Human behavior simulation error: {e}")
    
    def is_blocked(self, driver):
        """Check if blocked (conservative detection)"""
        try:
            current_url = driver.current_url.lower()
            
            # Only check for obvious blocks
            if 'access-denied' in current_url or 'blocked' in current_url:
                return True
            
            # Check for Cloudflare challenge
            if driver.find_elements(By.ID, "cf-challenge-running"):
                logger.warning("Cloudflare challenge detected")
                return True
            
            # Check for explicit 404 pages
            if '404' in driver.title and 'non trovata' in driver.title.lower():
                return True
            
            return False
            
        except:
            return False
    
    def extract_ticket_info(self, ticket_element):
        """Extract ticket information"""
        try:
            info = {
                'raw_text': ticket_element.text.strip(),
                'category': 'unknown',
                'price': 'N/A',
                'element': ticket_element
            }
            
            # Categorize
            text_lower = info['raw_text'].lower()
            if 'prato a' in text_lower:
                info['category'] = 'prato_a'
            elif 'prato b' in text_lower:
                info['category'] = 'prato_b'
            elif 'settore' in text_lower or 'tribuna' in text_lower:
                info['category'] = 'settore'
            
            return info
        except:
            return None
    
    def hunt_with_stealth(self, browser_id: int, driver: uc.Chrome):
        """Hunt tickets with human-like behavior"""
        logger.info(f"🎯 Stealth hunter {browser_id} starting...")
        
        # Initial navigation with human-like delay
        logger.info(f"📍 Navigating to target...")
        
        # First go to main site
        driver.get("https://www.fansale.it")
        time.sleep(random.uniform(3, 5))  # Look around
        
        # Then navigate to tickets
        driver.get(self.target_url)
        time.sleep(random.uniform(2, 4))  # Let page load naturally
        
        # Main hunting loop
        check_count = 0
        last_action_time = time.time()
        consecutive_empty = 0
        last_human_action = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                check_count += 1
                
                # Periodic human-like actions
                if time.time() - last_human_action > random.uniform(30, 60):
                    self.simulate_human_behavior(driver)
                    last_human_action = time.time()
                
                # Check for blocks (less frequently)
                if check_count % 50 == 0:
                    if self.is_blocked(driver):
                        logger.warning(f"⚠️ Hunter {browser_id}: Possible block detected")
                        # Take a long break
                        time.sleep(random.uniform(30, 60))
                        driver.refresh()
                        time.sleep(random.uniform(5, 10))
                        continue
                
                # Look for tickets
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    consecutive_empty = 0
                    logger.info(f"👀 Found {len(tickets)} potential tickets")
                    
                    for ticket in tickets:
                        try:
                            # Human-like hover before clicking
                            action = ActionChains(driver)
                            action.move_to_element(ticket)
                            action.pause(random.uniform(0.5, 1.0))
                            action.perform()
                            
                            ticket_info = self.extract_ticket_info(ticket)
                            
                            if ticket_info and ticket_info['category'] in self.ticket_types_to_hunt:
                                logger.info(f"🎯 {ticket_info['category'].upper()} ticket found!")
                                
                                # Human-like click delay
                                time.sleep(random.uniform(0.3, 0.8))
                                
                                try:
                                    # Click with retry
                                    ticket.click()
                                    logger.info("✅ Clicked ticket!")
                                    
                                    # Wait for purchase button
                                    purchase_btn = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, 
                                            "[data-qa='purchaseButton'], button[class*='purchase']"))
                                    )
                                    
                                    # Human pause before purchasing
                                    time.sleep(random.uniform(0.5, 1.5))
                                    purchase_btn.click()
                                    
                                    logger.info("🎉 PURCHASE INITIATED!")
                                    
                                    # Screenshot
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    driver.save_screenshot(f"screenshots/purchase_{timestamp}.png")
                                    
                                    self.tickets_secured += 1
                                    
                                except Exception as e:
                                    logger.error(f"Purchase failed: {e}")
                                    
                        except Exception as e:
                            logger.debug(f"Ticket processing error: {e}")
                else:
                    consecutive_empty += 1
                    
                    # If too many empty, might need to refresh
                    if consecutive_empty > 30:
                        logger.info("Refreshing due to empty results...")
                        driver.refresh()
                        time.sleep(random.uniform(3, 5))
                        consecutive_empty = 0
                
                # Status update
                if check_count % self.config.status_update_interval == 0:
                    rate = (check_count * 60) / (time.time() - self.session_start_time)
                    logger.info(f"Hunter {browser_id} | Checks: {check_count} | "
                               f"Rate: {rate:.1f}/min | Tickets secured: {self.tickets_secured}")
                
                # Human-like variable wait
                wait_time = self.config.calculate_wait_time()
                time.sleep(wait_time)
                
            except TimeoutException:
                logger.warning(f"Hunter {browser_id}: Page timeout")
                time.sleep(random.uniform(5, 10))
                driver.refresh()
                
            except Exception as e:
                logger.error(f"Hunter {browser_id} error: {e}")
                time.sleep(random.uniform(2, 5))
    
    def show_menu(self):
        """Simple menu for stealth bot"""
        while True:
            os.system('clear' if os.name != 'nt' else 'cls')
            
            print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
            print(f"{Colors.BOLD}🥷 FANSALE ULTRA STEALTH BOT{Colors.END}")
            print(f"{Colors.CYAN}{'='*60}{Colors.END}")
            
            print(f"\n{Colors.BOLD}Current Settings:{Colors.END}")
            print(f"  Mode: {'Human-like' if self.config.human_mode else 'Normal'}")
            print(f"  Check rate: ~{self.config.checks_per_minute}/min")
            print(f"  Browsers: {self.config.browsers_count}")
            print(f"  Hunting: {', '.join(self.config.ticket_types_to_hunt)}")
            
            print(f"\n{Colors.BOLD}Options:{Colors.END}")
            print("  1. 🚀 Start Stealth Hunting")
            print("  2. 🎯 Configure Ticket Types")
            print("  3. 🤖 Toggle Human Mode")
            print("  4. ❌ Exit")
            
            choice = input(f"\n{Colors.BOLD}Select (1-4):{Colors.END} ").strip()
            
            if choice == '1':
                return True
            elif choice == '2':
                self.configure_tickets()
            elif choice == '3':
                self.config.human_mode = not self.config.human_mode
                self.config.random_actions = self.config.human_mode
                self.config.mouse_movements = self.config.human_mode
                status = "ON" if self.config.human_mode else "OFF"
                print(f"{Colors.GREEN}✅ Human mode {status}{Colors.END}")
                self._save_config()
                time.sleep(1)
            elif choice == '4':
                return False
    
    def configure_tickets(self):
        """Configure ticket types"""
        print(f"\n{Colors.BOLD}Select ticket types (comma-separated):{Colors.END}")
        print("  1. PRATO A 🟢")
        print("  2. PRATO B 🔵")
        print("  3. SETTORE 🟡")
        print("  4. All types")
        
        choice = input(f"\n{Colors.BOLD}Choice:{Colors.END} ").strip()
        
        if choice == '4':
            self.config.ticket_types_to_hunt = ['prato_a', 'prato_b', 'settore']
        else:
            type_map = {'1': 'prato_a', '2': 'prato_b', '3': 'settore'}
            selected = []
            for c in choice.split(','):
                c = c.strip()
                if c in type_map:
                    selected.append(type_map[c])
            
            if selected:
                self.config.ticket_types_to_hunt = selected
                self.ticket_types_to_hunt = selected
        
        print(f"{Colors.GREEN}✅ Now hunting: {', '.join(self.config.ticket_types_to_hunt)}{Colors.END}")
        self._save_config()
        time.sleep(1)
    
    def run(self):
        """Run the stealth bot"""
        if not self.show_menu():
            print(f"{Colors.CYAN}Goodbye!{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}🥷 Starting ultra stealth mode...{Colors.END}")
        
        # Create stealth browser(s)
        browsers_created = []
        for i in range(1, self.num_browsers + 1):
            browser = self.create_stealth_browser(i)
            if browser:
                browsers_created.append((i, browser))
            else:
                logger.error(f"Failed to create browser {i}")
        
        if not browsers_created:
            logger.error("❌ No browsers created!")
            return
        
        # Start hunting
        threads = []
        for browser_id, driver in browsers_created:
            thread = threading.Thread(
                target=self.hunt_with_stealth,
                args=(browser_id, driver),
                name=f"StealthHunter-{browser_id}"
            )
            thread.start()
            threads.append(thread)
        
        try:
            print(f"\n{Colors.BOLD}🎯 Stealth hunting active...{Colors.END}")
            print(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.END}\n")
            
            while not self.shutdown_event.is_set():
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping stealth hunt...")
        
        # Cleanup
        self.shutdown_event.set()
        
        for thread in threads:
            thread.join(timeout=10)
        
        for browser_id, driver in browsers_created:
            try:
                driver.quit()
            except:
                pass
        
        print(f"\n{Colors.GREEN}✅ Stealth session complete!{Colors.END}")
        print(f"Tickets secured: {self.tickets_secured}")


def main():
    """Main entry point"""
    print(f"{Colors.CYAN}")
    print(r"""
    ███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗
    ██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║
    ███████╗   ██║   █████╗  ███████║██║     ██║   ███████║
    ╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║
    ███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║
    ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝
    """)
    print(f"{Colors.END}")
    print(f"{Colors.BOLD}        🥷 ULTRA STEALTH TICKET HUNTER 🥷{Colors.END}")
    print(f"{Colors.CYAN}     Undetectable • Human-like • Intelligent{Colors.END}\n")
    
    try:
        bot = StealthBot()
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
