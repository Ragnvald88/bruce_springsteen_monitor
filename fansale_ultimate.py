#!/usr/bin/env python3
"""
FanSale Ultimate Bot - Fast ticket hunting with real-time UI and persistent settings
Enhanced with menu system, live statistics, and configuration options
"""

import os
import sys
import time
import json
import random
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

import requests
from dotenv import load_dotenv
from colorama import init, Fore, Style, Back

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

class SettingsManager:
    """Handles persistent bot configuration"""
    
    def __init__(self):
        self.settings_file = Path("bot_settings.json")
        self.default_settings = {
            "num_browsers": 2,
            "max_tickets": 2,
            "ticket_types": ["all"],
            "min_wait": 0.3,
            "max_wait": 1.0,
            "refresh_interval": 15,
            "use_proxy": False,
            "proxy_host": "",
            "proxy_port": "",
            "proxy_user": "",
            "proxy_pass": "",
            "log_level": "info",
            "show_stats": True,
            "sound_alerts": True,
            "auto_screenshot": True
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or create defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    # Merge with defaults to handle new settings
                    return {**self.default_settings, **saved}
            except:
                pass
        return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def update(self, key, value):
        """Update a setting and save"""
        self.settings[key] = value
        self.save_settings()
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)

class StatsTracker:
    """Tracks real-time statistics"""
    
    def __init__(self):
        self.stats = {
            "start_time": time.time(),
            "total_checks": 0,
            "tickets_found": defaultdict(int),
            "tickets_secured": 0,
            "last_check_time": time.time(),
            "checks_per_minute": 0,
            "active_browsers": 0,
            "unique_tickets_seen": 0
        }
        self.lock = threading.Lock()
        self.check_times = []
    
    def record_check(self):
        """Record a ticket check"""
        with self.lock:
            self.stats["total_checks"] += 1
            self.stats["last_check_time"] = time.time()
            self.check_times.append(time.time())
            # Keep only last minute of checks
            cutoff = time.time() - 60
            self.check_times = [t for t in self.check_times if t > cutoff]
            self.stats["checks_per_minute"] = len(self.check_times)
    
    def found_ticket(self, category):
        """Record a found ticket"""
        with self.lock:
            self.stats["tickets_found"][category] += 1
            self.stats["unique_tickets_seen"] += 1
    
    def secured_ticket(self):
        """Record a secured ticket"""
        with self.lock:
            self.stats["tickets_secured"] += 1
    
    def get_stats(self):
        """Get current statistics"""
        with self.lock:
            return self.stats.copy()
    
    def get_runtime(self):
        """Get formatted runtime"""
        elapsed = time.time() - self.stats["start_time"]
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

class TerminalUI:
    """Handles terminal display and menus"""
    
    @staticmethod
    def clear():
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_header():
        """Print stylish header"""
        TerminalUI.clear()
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}  🎯 FanSale Ultimate Bot - Enhanced Edition")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    @staticmethod
    def main_menu():
        """Display main menu"""
        TerminalUI.print_header()
        print(f"{Fore.GREEN}[1] {Fore.WHITE}🚀 Run Bot")
        print(f"{Fore.GREEN}[2] {Fore.WHITE}⚙️  Settings")
        print(f"{Fore.GREEN}[3] {Fore.WHITE}📊 View Statistics")
        print(f"{Fore.GREEN}[4] {Fore.WHITE}📖 Help")
        print(f"{Fore.GREEN}[5] {Fore.WHITE}🚪 Exit\n")
        return input(f"{Fore.YELLOW}Select option: {Fore.WHITE}")
    
    @staticmethod
    def settings_menu(settings):
        """Display settings menu"""
        TerminalUI.print_header()
        print(f"{Fore.CYAN}⚙️  Bot Settings\n")
        
        print(f"{Fore.GREEN}[1] {Fore.WHITE}Browsers: {Fore.YELLOW}{settings.get('num_browsers')}")
        print(f"{Fore.GREEN}[2] {Fore.WHITE}Max Tickets: {Fore.YELLOW}{settings.get('max_tickets')}")
        print(f"{Fore.GREEN}[3] {Fore.WHITE}Ticket Types: {Fore.YELLOW}{', '.join(settings.get('ticket_types'))}")
        print(f"{Fore.GREEN}[4] {Fore.WHITE}Check Speed: {Fore.YELLOW}{settings.get('min_wait')}-{settings.get('max_wait')}s")
        print(f"{Fore.GREEN}[5] {Fore.WHITE}Refresh Interval: {Fore.YELLOW}{settings.get('refresh_interval')}s")
        print(f"{Fore.GREEN}[6] {Fore.WHITE}Proxy: {Fore.YELLOW}{'Enabled' if settings.get('use_proxy') else 'Disabled'}")
        print(f"{Fore.GREEN}[7] {Fore.WHITE}Sound Alerts: {Fore.YELLOW}{'On' if settings.get('sound_alerts') else 'Off'}")
        print(f"{Fore.GREEN}[8] {Fore.WHITE}Auto Screenshot: {Fore.YELLOW}{'On' if settings.get('auto_screenshot') else 'Off'}")
        print(f"{Fore.GREEN}[9] {Fore.WHITE}Back to Main Menu\n")
        
        return input(f"{Fore.YELLOW}Select option: {Fore.WHITE}")
    
    @staticmethod
    def live_stats_header():
        """Print live statistics header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}  📊 Live Hunting Statistics")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

class FanSaleUltimate:
    """Enhanced FanSale bot with UI and persistent settings"""
    
    def __init__(self):
        self.target_url = os.getenv('FANSALE_TARGET_URL', '').strip()
        self.twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY', '').strip()
        
        # Managers
        self.settings = SettingsManager()
        self.stats = StatsTracker()
        
        # Runtime state
        self.browsers = []
        self.threads = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        self.seen_tickets = set()
        
        # CAPTCHA state
        self.captcha_grace_period = 300
        self.last_captcha_solve = 0
        
        # Display state
        self.display_lock = threading.Lock()
        self.last_log_time = time.time()
    
    def log(self, message, level='info', browser_id=None):
        """Enhanced logging with real-time display"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        colors = {
            'info': Fore.CYAN,
            'success': Fore.GREEN,
            'warning': Fore.YELLOW,
            'error': Fore.RED,
            'alert': Fore.MAGENTA + Style.BRIGHT,
            'ticket': Fore.GREEN + Style.BRIGHT
        }
        color = colors.get(level, Fore.WHITE)
        
        with self.display_lock:
            # Clear line and print
            print(f"\r{' '*80}\r", end='')  # Clear current line
            if browser_id is not None:
                print(f"{color}[{timestamp}] [Browser {browser_id}] {message}{Style.RESET_ALL}")
            else:
                print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")
            
            # Sound alert for important events
            if level == 'alert' and self.settings.get('sound_alerts'):
                try:
                    if sys.platform == 'darwin':
                        subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])
                    elif sys.platform.startswith('linux'):
                        subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])
                    elif sys.platform == 'win32':
                        import winsound
                        winsound.Beep(1000, 500)
                except:
                    pass
    
    def display_live_stats(self):
        """Display live statistics in terminal"""
        while not self.shutdown_event.is_set():
            try:
                stats = self.stats.get_stats()
                runtime = self.stats.get_runtime()
                
                with self.display_lock:
                    # Move cursor to stats area
                    print(f"\033[s", end='')  # Save cursor position
                    print(f"\033[10;0H", end='')  # Move to line 10
                    
                    # Print stats box
                    print(f"\n{Fore.CYAN}{'─'*60}")
                    print(f"{Fore.WHITE}⏱️  Runtime: {Fore.YELLOW}{runtime}")
                    print(f"{Fore.WHITE}🔍 Total Checks: {Fore.YELLOW}{stats['total_checks']:,}")
                    print(f"{Fore.WHITE}⚡ Checks/min: {Fore.YELLOW}{stats['checks_per_minute']}")
                    print(f"{Fore.WHITE}🎫 Unique Tickets: {Fore.YELLOW}{stats['unique_tickets_seen']}")
                    print(f"{Fore.WHITE}✅ Secured: {Fore.GREEN}{stats['tickets_secured']}")
                    
                    # Ticket breakdown
                    if stats['tickets_found']:
                        print(f"\n{Fore.WHITE}📊 Tickets Found by Type:")
                        for category, count in stats['tickets_found'].items():
                            color = Fore.GREEN if category == 'prato_a' else Fore.YELLOW
                            print(f"   {color}• {category.upper()}: {count}")
                    
                    print(f"{Fore.CYAN}{'─'*60}")
                    print(f"\033[u", end='', flush=True)  # Restore cursor position
                
                time.sleep(1)
            except:
                time.sleep(1)
    
    def configure_settings(self):
        """Interactive settings configuration"""
        while True:
            choice = TerminalUI.settings_menu(self.settings)
            
            if choice == '1':
                try:
                    num = int(input(f"\n{Fore.GREEN}Number of browsers (1-8): {Fore.WHITE}"))
                    self.settings.update('num_browsers', max(1, min(8, num)))
                    self.log("Browsers updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '2':
                try:
                    num = int(input(f"\n{Fore.GREEN}Max tickets to secure: {Fore.WHITE}"))
                    self.settings.update('max_tickets', max(1, num))
                    self.log("Max tickets updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '3':
                print(f"\n{Fore.YELLOW}Select ticket types:")
                print("[1] Prato A")
                print("[2] Prato B")
                print("[3] Settore")
                print("[4] Other")
                print("[5] All types")
                
                selection = input(f"\n{Fore.GREEN}Enter choices (e.g., 1,2,3): {Fore.WHITE}")
                type_map = {
                    '1': 'prato_a',
                    '2': 'prato_b',
                    '3': 'settore',
                    '4': 'other',
                    '5': 'all'
                }
                
                selected = []
                for c in selection.split(','):
                    c = c.strip()
                    if c in type_map:
                        selected.append(type_map[c])
                
                if selected:
                    self.settings.update('ticket_types', selected)
                    self.log("Ticket types updated", 'success')
                time.sleep(1)
                
            elif choice == '4':
                try:
                    min_wait = float(input(f"\n{Fore.GREEN}Min wait time (seconds): {Fore.WHITE}"))
                    max_wait = float(input(f"{Fore.GREEN}Max wait time (seconds): {Fore.WHITE}"))
                    self.settings.update('min_wait', max(0.1, min_wait))
                    self.settings.update('max_wait', max(min_wait, max_wait))
                    self.log("Check speed updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '5':
                try:
                    interval = int(input(f"\n{Fore.GREEN}Page refresh interval (seconds): {Fore.WHITE}"))
                    self.settings.update('refresh_interval', max(5, interval))
                    self.log("Refresh interval updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '6':
                use_proxy = input(f"\n{Fore.GREEN}Enable proxy? (y/n): {Fore.WHITE}").lower() == 'y'
                self.settings.update('use_proxy', use_proxy)
                
                if use_proxy:
                    host = input(f"{Fore.GREEN}Proxy host: {Fore.WHITE}")
                    port = input(f"{Fore.GREEN}Proxy port: {Fore.WHITE}")
                    user = input(f"{Fore.GREEN}Proxy username (optional): {Fore.WHITE}")
                    pwd = input(f"{Fore.GREEN}Proxy password (optional): {Fore.WHITE}")
                    
                    self.settings.update('proxy_host', host)
                    self.settings.update('proxy_port', port)
                    self.settings.update('proxy_user', user)
                    self.settings.update('proxy_pass', pwd)
                
                self.log("Proxy settings updated", 'success')
                time.sleep(1)
                
            elif choice == '7':
                self.settings.update('sound_alerts', not self.settings.get('sound_alerts'))
                self.log(f"Sound alerts {'enabled' if self.settings.get('sound_alerts') else 'disabled'}", 'success')
                time.sleep(1)
                
            elif choice == '8':
                self.settings.update('auto_screenshot', not self.settings.get('auto_screenshot'))
                self.log(f"Auto screenshot {'enabled' if self.settings.get('auto_screenshot') else 'disabled'}", 'success')
                time.sleep(1)
                
            elif choice == '9':
                break
    
    def categorize_ticket(self, text):
        """Categorize ticket type from text"""
        text_lower = text.lower()
        
        if 'prato a' in text_lower:
            return 'prato_a'
        elif 'prato b' in text_lower:
            return 'prato_b'
        elif any(f'settore {i}' in text_lower for i in range(1, 30)):
            return 'settore'
        else:
            return 'other'
    
    def generate_ticket_hash(self, text):
        """Generate unique hash for ticket"""
        clean_text = ''.join(c for c in text if c.isalnum() or c.isspace())
        return hashlib.md5(clean_text.encode()).hexdigest()
    
    def create_browser(self, browser_id):
        """Create undetected Chrome instance with optional proxy"""
        options = uc.ChromeOptions()
        
        # Essential options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Proxy configuration
        if self.settings.get('use_proxy'):
            proxy_host = self.settings.get('proxy_host')
            proxy_port = self.settings.get('proxy_port')
            proxy_user = self.settings.get('proxy_user')
            proxy_pass = self.settings.get('proxy_pass')
            
            if proxy_host and proxy_port:
                if proxy_user and proxy_pass:
                    proxy_string = f"{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
                else:
                    proxy_string = f"{proxy_host}:{proxy_port}"
                options.add_argument(f'--proxy-server={proxy_string}')
        
        # Language settings
        options.add_argument('--lang=it-IT')
        prefs = {
            'intl.accept_languages': 'it-IT,it;q=0.9,en;q=0.8',
            'profile.default_content_setting_values.notifications': 2
        }
        options.add_experimental_option('prefs', prefs)
        
        # Window positioning
        window_width, window_height = 1200, 900
        positions = [
            (0, 0), (600, 0), (1200, 0),
            (0, 450), (600, 450), (1200, 450),
            (0, 900), (600, 900)
        ]
        if browser_id < len(positions):
            x, y = positions[browser_id]
            options.add_argument(f'--window-position={x},{y}')
        options.add_argument(f'--window-size={window_width},{window_height}')
        
        # Try multiple Chrome versions
        chrome_versions = [None, 131, 130, 129, 128]
        
        for version in chrome_versions:
            try:
                self.log(f"Creating browser {browser_id} (v{version or 'auto'})...", 'info')
                
                driver = uc.Chrome(
                    options=options,
                    version_main=version,
                    use_subprocess=True
                )
                
                # Apply stealth scripts
                stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['it-IT', 'it', 'en']});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({query: () => Promise.resolve({state: 'granted'})})
                });
                """
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': stealth_js})
                
                return driver
                
            except Exception as e:
                self.log(f"Failed with v{version}: {str(e)[:50]}", 'warning')
                continue
        
        raise Exception("Failed to create browser with any Chrome version")
    
    def dismiss_popups(self, driver):
        """Dismiss FanSale-specific popups"""
        dismissed = 0
        
        selectors = [
            "button.js-BotProtectionModalButton1",
            "button[class*='BotProtection']",
            "//button[contains(text(), 'Carica')]",
            "button[aria-label*='close']",
            "button[class*='modal-close']"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                        dismissed += 1
                    except:
                        pass
            except:
                pass
        
        return dismissed
    
    def detect_captcha(self, driver):
        """Check if CAPTCHA is present"""
        if time.time() - self.last_captcha_solve < self.captcha_grace_period:
            return False
        
        captcha_indicators = [
            "iframe[src*='recaptcha']",
            "div[class*='g-recaptcha']",
            "#recaptcha",
            "div[class*='captcha']"
        ]
        
        for selector in captcha_indicators:
            try:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    return True
            except:
                pass
        
        return False
    
    def solve_captcha(self, driver, browser_id):
        """Handle CAPTCHA (auto or manual)"""
        self.log(f"CAPTCHA detected!", 'warning', browser_id)
        
        if self.twocaptcha_key:
            try:
                # Find site key
                site_key = None
                for method in [
                    lambda: driver.find_element(By.CSS_SELECTOR, "[data-sitekey]").get_attribute("data-sitekey"),
                    lambda: driver.execute_script("return document.querySelector('[data-sitekey]').dataset.sitekey"),
                    lambda: driver.execute_script("return grecaptcha.execute.toString().match(/sitekey:'([^']+)'/)[1]")
                ]:
                    try:
                        site_key = method()
                        if site_key:
                            break
                    except:
                        pass
                
                if not site_key:
                    raise Exception("Could not find site key")
                
                # Request solution from 2captcha
                self.log("Requesting CAPTCHA solution from 2captcha...", 'info', browser_id)
                response = requests.post('http://2captcha.com/in.php', data={
                    'key': self.twocaptcha_key,
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': driver.current_url
                })
                
                if response.text.startswith('OK|'):
                    captcha_id = response.text.split('|')[1]
                    
                    # Poll for result
                    for _ in range(30):
                        time.sleep(5)
                        result = requests.get(f'http://2captcha.com/res.php?key={self.twocaptcha_key}&action=get&id={captcha_id}')
                        
                        if result.text == 'CAPCHA_NOT_READY':
                            continue
                        elif result.text.startswith('OK|'):
                            token = result.text.split('|')[1]
                            
                            # Inject token
                            driver.execute_script(f"""
                                document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                                    for (let key in ___grecaptcha_cfg.clients) {{
                                        if (___grecaptcha_cfg.clients[key].callback) {{
                                            ___grecaptcha_cfg.clients[key].callback('{token}');
                                        }}
                                    }}
                                }}
                            """)
                            
                            self.log("CAPTCHA solved automatically!", 'success', browser_id)
                            self.last_captcha_solve = time.time()
                            return True
                        else:
                            break
                            
            except Exception as e:
                self.log(f"Auto-solve failed: {e}", 'error', browser_id)
        
        # Manual fallback
        self.log("MANUAL CAPTCHA REQUIRED! Solve it in the browser!", 'alert', browser_id)
        self.log(f"You have 2 minutes to solve the CAPTCHA in Browser {browser_id}", 'warning')
        
        # Wait for manual solve
        start_time = time.time()
        while time.time() - start_time < 120:
            if not self.detect_captcha(driver):
                self.log("CAPTCHA solved manually!", 'success', browser_id)
                self.last_captcha_solve = time.time()
                return True
            time.sleep(2)
        
        self.log("CAPTCHA timeout!", 'error', browser_id)
        return False
    
    def attempt_purchase(self, driver, ticket_element, browser_id):
        """Attempt to click ticket and buy"""
        try:
            # Click the ticket
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            time.sleep(0.2)
            
            # Try multiple click methods
            clicked = False
            
            # Method 1: JavaScript click
            try:
                driver.execute_script("arguments[0].click();", ticket_element)
                clicked = True
            except:
                pass
            
            # Method 2: Find and click link inside
            if not clicked:
                try:
                    link = ticket_element.find_element(By.CSS_SELECTOR, "a")
                    driver.execute_script("arguments[0].click();", link)
                    clicked = True
                except:
                    pass
            
            # Method 3: ActionChains
            if not clicked:
                try:
                    ActionChains(driver).move_to_element(ticket_element).click().perform()
                    clicked = True
                except:
                    pass
            
            if not clicked:
                return False
            
            # Wait for buy button
            buy_selectors = [
                "button[data-qa='buyNowButton']",
                "//button[contains(text(), 'Acquista')]",
                "//button[contains(text(), 'Compra')]",
                "button[class*='buy']",
                "button[class*='acquista']",
                "//button[contains(@class, 'primary') and not(@disabled)]"
            ]
            
            for selector in buy_selectors:
                try:
                    if selector.startswith('//'):
                        buy_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Click buy button
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                    time.sleep(0.1)
                    driver.execute_script("arguments[0].click();", buy_btn)
                    
                    self.log(f"BUY BUTTON CLICKED!", 'alert', browser_id)
                    
                    # Take screenshot if enabled
                    if self.settings.get('auto_screenshot'):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        Path("screenshots").mkdir(exist_ok=True)
                        screenshot_path = f"screenshots/purchase_{browser_id}_{timestamp}.png"
                        driver.save_screenshot(screenshot_path)
                        self.log(f"Screenshot saved: {screenshot_path}", 'info', browser_id)
                    
                    # Check for CAPTCHA
                    time.sleep(1)
                    if self.detect_captcha(driver):
                        if not self.solve_captcha(driver, browser_id):
                            return False
                    
                    return True
                    
                except TimeoutException:
                    continue
                except Exception:
                    continue
            
            self.log(f"No buy button found", 'warning', browser_id)
            return False
            
        except Exception as e:
            self.log(f"Purchase failed - {str(e)[:50]}", 'error', browser_id)
            return False
    
    def hunt_tickets(self, browser_id, driver):
        """Main hunting loop for a browser"""
        self.log(f"Hunter starting...", 'success', browser_id)
        
        # Navigate to target
        try:
            driver.get(self.target_url)
            self.log(f"Page loaded", 'info', browser_id)
        except Exception as e:
            self.log(f"Navigation failed - {e}", 'error', browser_id)
            return
        
        # Initial setup
        time.sleep(2)
        self.dismiss_popups(driver)
        
        last_refresh = time.time()
        last_popup_check = time.time()
        
        # Main loop
        while not self.shutdown_event.is_set():
            try:
                # Check if we've secured enough tickets
                if self.tickets_secured >= self.settings.get('max_tickets'):
                    break
                
                # Record check
                self.stats.record_check()
                
                # Periodic popup dismissal
                if time.time() - last_popup_check > 10:
                    self.dismiss_popups(driver)
                    last_popup_check = time.time()
                
                # Find tickets
                tickets = []
                ticket_selectors = [
                    "div[data-qa='ticketToBuy']",
                    "a.offer-list-item",
                    "div[class*='ticket'][class*='available']",
                    "article[class*='ticket']",
                    "div[class*='offerta']"
                ]
                
                for selector in ticket_selectors:
                    try:
                        found = driver.find_elements(By.CSS_SELECTOR, selector)
                        if found:
                            tickets.extend(found)
                            break
                    except:
                        pass
                
                # Process tickets
                for ticket in tickets:
                    if self.shutdown_event.is_set():
                        break
                    
                    try:
                        # Extract ticket info
                        ticket_text = ticket.text.strip()
                        if not ticket_text:
                            continue
                        
                        # Check if new
                        ticket_hash = self.generate_ticket_hash(ticket_text)
                        if ticket_hash in self.seen_tickets:
                            continue
                        
                        self.seen_tickets.add(ticket_hash)
                        
                        # Categorize
                        category = self.categorize_ticket(ticket_text)
                        self.stats.found_ticket(category)
                        
                        # Log new ticket with special formatting
                        self.log(f"NEW TICKET: {category.upper()} - {ticket_text[:50]}...", 'ticket', browser_id)
                        
                        # Check if we should buy
                        ticket_types = self.settings.get('ticket_types')
                        if 'all' in ticket_types or category in ticket_types:
                            with self.purchase_lock:
                                if self.tickets_secured < self.settings.get('max_tickets'):
                                    if self.attempt_purchase(driver, ticket, browser_id):
                                        self.tickets_secured += 1
                                        self.stats.secured_ticket()
                                        self.log(f"TICKET SECURED! ({self.tickets_secured}/{self.settings.get('max_tickets')})", 'alert')
                                        
                                        if self.tickets_secured >= self.settings.get('max_tickets'):
                                            self.log("ALL TICKETS SECURED! Shutting down...", 'alert')
                                            self.shutdown_event.set()
                                            return
                    
                    except Exception:
                        continue
                
                # Wait before next check
                wait_time = random.uniform(
                    self.settings.get('min_wait'),
                    self.settings.get('max_wait')
                )
                time.sleep(wait_time)
                
                # Periodic refresh
                refresh_interval = self.settings.get('refresh_interval')
                if time.time() - last_refresh > refresh_interval + random.randint(-3, 3):
                    self.log(f"Refreshing page", 'info', browser_id)
                    driver.refresh()
                    time.sleep(1)
                    self.dismiss_popups(driver)
                    last_refresh = time.time()
                
            except WebDriverException as e:
                if "invalid session" in str(e).lower():
                    self.log(f"Session died", 'error', browser_id)
                    break
                else:
                    self.log(f"WebDriver error", 'error', browser_id)
                    time.sleep(2)
                    
            except Exception as e:
                self.log(f"Unexpected error - {str(e)[:50]}", 'error', browser_id)
                time.sleep(2)
    
    def run_bot(self):
        """Run the bot with current settings"""
        # Get target URL
        if not self.target_url:
            self.target_url = input(f"\n{Fore.GREEN}Enter FanSale event URL: {Fore.WHITE}").strip()
            if not self.target_url:
                self.log("No URL provided", 'error')
                return
        
        print(f"\n{Fore.GREEN}🚀 Starting bot with saved settings...{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}Target: {Fore.WHITE}{self.target_url[:50]}...")
        print(f"{Fore.CYAN}Browsers: {Fore.WHITE}{self.settings.get('num_browsers')}")
        print(f"{Fore.CYAN}Max tickets: {Fore.WHITE}{self.settings.get('max_tickets')}")
        print(f"{Fore.CYAN}Hunting: {Fore.WHITE}{', '.join(self.settings.get('ticket_types'))}\n")
        
        # Start live stats display thread
        stats_thread = threading.Thread(target=self.display_live_stats, daemon=True)
        stats_thread.start()
        
        # Create browsers and start hunting threads
        TerminalUI.live_stats_header()
        
        with ThreadPoolExecutor(max_workers=self.settings.get('num_browsers')) as executor:
            futures = []
            
            for i in range(self.settings.get('num_browsers')):
                try:
                    driver = self.create_browser(i)
                    self.browsers.append(driver)
                    self.stats.stats['active_browsers'] += 1
                    
                    future = executor.submit(self.hunt_tickets, i, driver)
                    futures.append(future)
                    
                    self.log(f"Browser {i} launched", 'success')
                    time.sleep(1)
                    
                except Exception as e:
                    self.log(f"Failed to create browser {i}: {e}", 'error')
            
            # Wait for completion
            try:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.log(f"Thread error: {e}", 'error')
                        
            except KeyboardInterrupt:
                self.log("\nShutdown requested...", 'warning')
                self.shutdown_event.set()
        
        # Cleanup
        self.log("Closing browsers...", 'info')
        for driver in self.browsers:
            try:
                driver.quit()
            except:
                pass
        
        # Final summary
        stats = self.stats.get_stats()
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}📊 Final Summary:")
        print(f"{Fore.GREEN}  • Runtime: {self.stats.get_runtime()}")
        print(f"{Fore.GREEN}  • Total checks: {stats['total_checks']:,}")
        print(f"{Fore.GREEN}  • Unique tickets seen: {stats['unique_tickets_seen']}")
        print(f"{Fore.GREEN}  • Tickets secured: {stats['tickets_secured']}")
        
        if stats['tickets_found']:
            print(f"\n{Fore.YELLOW}  Tickets by type:")
            for category, count in stats['tickets_found'].items():
                print(f"{Fore.GREEN}    • {category.upper()}: {count}")
        
        print(f"{Fore.CYAN}{'='*60}\n")
        
        if stats['tickets_secured'] > 0:
            self.log("Check your screenshots folder for proof of purchase!", 'alert')
        
        input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Fore.WHITE}")
    
    def view_statistics(self):
        """View historical statistics"""
        TerminalUI.print_header()
        
        # Load stats file if exists
        stats_file = Path("bot_statistics.json")
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    historical = json.load(f)
                
                print(f"{Fore.CYAN}📊 Historical Statistics\n")
                print(f"{Fore.WHITE}Total runs: {Fore.YELLOW}{historical.get('total_runs', 0)}")
                print(f"{Fore.WHITE}Total runtime: {Fore.YELLOW}{historical.get('total_runtime', 'N/A')}")
                print(f"{Fore.WHITE}Total checks: {Fore.YELLOW}{historical.get('total_checks', 0):,}")
                print(f"{Fore.WHITE}Total tickets secured: {Fore.GREEN}{historical.get('total_secured', 0)}")
                
                if historical.get('tickets_by_type'):
                    print(f"\n{Fore.WHITE}Tickets by type:")
                    for category, count in historical.get('tickets_by_type', {}).items():
                        print(f"  • {category.upper()}: {count}")
                
            except:
                print(f"{Fore.YELLOW}No historical statistics available yet.")
        else:
            print(f"{Fore.YELLOW}No historical statistics available yet.")
            print(f"{Fore.WHITE}Run the bot to start collecting statistics.")
        
        input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Fore.WHITE}")
    
    def show_help(self):
        """Display help information"""
        TerminalUI.print_header()
        print(f"{Fore.CYAN}📖 Help & Guide\n")
        
        print(f"{Fore.YELLOW}Quick Start:")
        print(f"{Fore.WHITE}1. Press [2] to configure settings")
        print(f"{Fore.WHITE}2. Set number of browsers (2-4 recommended)")
        print(f"{Fore.WHITE}3. Choose ticket types to hunt")
        print(f"{Fore.WHITE}4. Press [1] to run the bot")
        
        print(f"\n{Fore.YELLOW}Tips:")
        print(f"{Fore.WHITE}• Use 2-4 browsers for optimal performance")
        print(f"{Fore.WHITE}• Set specific ticket types to reduce noise")
        print(f"{Fore.WHITE}• Enable sound alerts for important events")
        print(f"{Fore.WHITE}• Screenshots are saved automatically on purchase")
        
        print(f"\n{Fore.YELLOW}Keyboard Shortcuts:")
        print(f"{Fore.WHITE}• Ctrl+C: Stop the bot gracefully")
        
        print(f"\n{Fore.YELLOW}Performance:")
        print(f"{Fore.WHITE}• Expected: 60-300 checks/minute per browser")
        print(f"{Fore.WHITE}• Lower wait times = faster checking")
        print(f"{Fore.WHITE}• More browsers = better coverage")
        
        input(f"\n{Fore.YELLOW}Press Enter to return to menu...{Fore.WHITE}")
    
    def main(self):
        """Main application loop"""
        while True:
            choice = TerminalUI.main_menu()
            
            if choice == '1':
                self.run_bot()
                # Reset for next run
                self.shutdown_event.clear()
                self.tickets_secured = 0
                self.seen_tickets.clear()
                self.browsers.clear()
                self.stats = StatsTracker()
                
            elif choice == '2':
                self.configure_settings()
                
            elif choice == '3':
                self.view_statistics()
                
            elif choice == '4':
                self.show_help()
                
            elif choice == '5':
                print(f"\n{Fore.YELLOW}👋 Thanks for using FanSale Ultimate Bot!")
                break
            
            else:
                self.log("Invalid choice", 'error')
                time.sleep(1)


if __name__ == "__main__":
    try:
        bot = FanSaleUltimate()
        bot.main()
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)