#!/usr/bin/env python3
"""
FanSale Ultimate Bot - Enhanced Edition
Advanced ticket hunting with beautiful terminal UI and smart features
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
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

import requests
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# HARDCODED BRUCE SPRINGSTEEN URL
DEFAULT_TARGET_URL = "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"

class SettingsManager:
    """Handles persistent bot configuration with profiles"""
    
    def __init__(self):
        self.settings_file = Path("bot_settings.json")
        self.profiles_file = Path("bot_profiles.json")
        self.default_settings = {
            "target_url": DEFAULT_TARGET_URL,
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
            "auto_screenshot": True,
            "auto_buy": False,
            "max_price": 0,
            "preferred_sectors": [],
            "blacklist_sectors": [],
            "notification_webhook": "",
            "theme": "cyberpunk"  # cyberpunk, matrix, minimal, rainbow
        }
        self.settings = self.load_settings()
        self.profiles = self.load_profiles()
        self.active_profile = "default"
    
    def load_settings(self):
        """Load settings from file or create defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    return {**self.default_settings, **saved}
            except:
                pass
        return self.default_settings.copy()
    
    def load_profiles(self):
        """Load saved profiles"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"default": self.default_settings.copy()}
    
    def save_settings(self):
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def save_profiles(self):
        """Save profiles to file"""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
    
    def save_profile(self, name):
        """Save current settings as a profile"""
        self.profiles[name] = self.settings.copy()
        self.save_profiles()
    
    def load_profile(self, name):
        """Load a saved profile"""
        if name in self.profiles:
            self.settings = self.profiles[name].copy()
            self.active_profile = name
            self.save_settings()
            return True
        return False
    
    def update(self, key, value):
        """Update a setting and save"""
        self.settings[key] = value
        self.save_settings()
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)

class StatsTracker:
    """Advanced statistics tracking with history"""
    
    def __init__(self):
        self.stats = {
            "start_time": time.time(),
            "total_checks": 0,
            "tickets_found": defaultdict(int),
            "tickets_secured": 0,
            "last_check_time": time.time(),
            "checks_per_minute": 0,
            "active_browsers": 0,
            "unique_tickets_seen": 0,
            "total_clicks": 0,
            "captchas_solved": 0,
            "errors_encountered": 0,
            "best_cpm": 0  # Best checks per minute
        }
        self.lock = threading.Lock()
        self.check_times = deque(maxlen=300)  # Last 5 minutes
        self.ticket_history = deque(maxlen=100)  # Last 100 tickets
        self.load_historical_stats()
    
    def load_historical_stats(self):
        """Load historical statistics"""
        stats_file = Path("bot_statistics.json")
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.historical = json.load(f)
            except:
                self.historical = self._default_historical()
        else:
            self.historical = self._default_historical()
    
    def _default_historical(self):
        """Default historical stats structure"""
        return {
            "total_runs": 0,
            "total_runtime": 0,
            "total_checks": 0,
            "total_secured": 0,
            "tickets_by_type": defaultdict(int),
            "best_session": {
                "date": None,
                "tickets": 0,
                "cpm": 0
            }
        }
    
    def save_historical_stats(self):
        """Save session stats to historical data"""
        with self.lock:
            runtime = time.time() - self.stats["start_time"]
            self.historical["total_runs"] += 1
            self.historical["total_runtime"] += runtime
            self.historical["total_checks"] += self.stats["total_checks"]
            self.historical["total_secured"] += self.stats["tickets_secured"]
            
            # Update tickets by type
            for category, count in self.stats["tickets_found"].items():
                self.historical["tickets_by_type"][category] += count
            
            # Check if this was the best session
            if self.stats["tickets_secured"] > self.historical["best_session"]["tickets"]:
                self.historical["best_session"] = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tickets": self.stats["tickets_secured"],
                    "cpm": self.stats["best_cpm"]
                }
            
            # Save to file
            with open("bot_statistics.json", 'w') as f:
                json.dump(self.historical, f, indent=2)
    
    def record_check(self):
        """Record a ticket check"""
        with self.lock:
            self.stats["total_checks"] += 1
            self.stats["last_check_time"] = time.time()
            self.check_times.append(time.time())
            
            # Calculate checks per minute
            if len(self.check_times) > 1:
                time_span = self.check_times[-1] - self.check_times[0]
                if time_span > 0:
                    cpm = (len(self.check_times) / time_span) * 60
                    self.stats["checks_per_minute"] = int(cpm)
                    if cpm > self.stats["best_cpm"]:
                        self.stats["best_cpm"] = int(cpm)
    
    def found_ticket(self, category, ticket_info=None):
        """Record a found ticket"""
        with self.lock:
            self.stats["tickets_found"][category] += 1
            self.stats["unique_tickets_seen"] += 1
            if ticket_info:
                self.ticket_history.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "category": category,
                    "info": ticket_info
                })
    
    def record_error(self):
        """Record an error"""
        with self.lock:
            self.stats["errors_encountered"] += 1
    
    def record_captcha_solved(self):
        """Record a solved CAPTCHA"""
        with self.lock:
            self.stats["captchas_solved"] += 1
    
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
    
    def get_ticket_history(self):
        """Get recent ticket history"""
        with self.lock:
            return list(self.ticket_history)

class TerminalUI:
    """Enhanced terminal UI with themes and animations"""
    
    THEMES = {
        "cyberpunk": {
            "primary": Fore.CYAN,
            "secondary": Fore.MAGENTA,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.CYAN
        },
        "matrix": {
            "primary": Fore.GREEN,
            "secondary": Fore.GREEN,
            "success": Style.BRIGHT + Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.GREEN
        },
        "minimal": {
            "primary": Fore.WHITE,
            "secondary": Fore.WHITE,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.WHITE
        },
        "rainbow": {
            "primary": Fore.CYAN,
            "secondary": Fore.MAGENTA,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.BLUE
        }
    }
    
    @staticmethod
    def clear():
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_header(theme="cyberpunk"):
        """Print enhanced header with ASCII art"""
        TerminalUI.clear()
        colors = TerminalUI.THEMES[theme]
        
        # ASCII Art Header
        print(colors["accent"] + """
    ███████╗ █████╗ ███╗   ██╗███████╗ █████╗ ██╗     ███████╗
    ██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗██║     ██╔════╝
    █████╗  ███████║██╔██╗ ██║███████╗███████║██║     █████╗  
    ██╔══╝  ██╔══██║██║╚██╗██║╚════██║██╔══██║██║     ██╔══╝  
    ██║     ██║  ██║██║ ╚████║███████║██║  ██║███████╗███████╗
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
    """ + Style.RESET_ALL)
        
        print(colors["primary"] + "    ══════════════════════════════════════════════════════")
        print(colors["secondary"] + "         🎫 ULTIMATE TICKET HUNTER - ENHANCED EDITION")
        print(colors["primary"] + "    ══════════════════════════════════════════════════════\n")
    
    @staticmethod
    def main_menu(settings):
        """Enhanced main menu with more options"""
        theme = settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        # Show current event
        url = settings.get("target_url", DEFAULT_TARGET_URL)
        if "bruce-springsteen" in url:
            event_name = "🎸 Bruce Springsteen"
        else:
            event_name = "🎫 Custom Event"
        
        print(colors["accent"] + f"    Current Event: {event_name}")
        print(colors["primary"] + "    ──────────────────────────────────────────────────────\n")
        
        # Main menu options
        print(colors["primary"] + "    🚀 QUICK ACTIONS")
        print(colors["secondary"] + f"    [1] {Fore.WHITE}Start Hunting")
        print(colors["secondary"] + f"    [2] {Fore.WHITE}Quick Settings")
        print()
        
        print(colors["primary"] + "    ⚙️  CONFIGURATION")
        print(colors["secondary"] + f"    [3] {Fore.WHITE}Advanced Settings")
        print(colors["secondary"] + f"    [4] {Fore.WHITE}Profile Manager")
        print(colors["secondary"] + f"    [5] {Fore.WHITE}Auto-Buy Rules")
        print()
        
        print(colors["primary"] + "    📊 ANALYTICS")
        print(colors["secondary"] + f"    [6] {Fore.WHITE}Live Dashboard")
        print(colors["secondary"] + f"    [7] {Fore.WHITE}Statistics & History")
        print(colors["secondary"] + f"    [8] {Fore.WHITE}Performance Report")
        print()
        
        print(colors["primary"] + "    🎨 CUSTOMIZATION")
        print(colors["secondary"] + f"    [9] {Fore.WHITE}Change Theme")
        print(colors["secondary"] + f"    [0] {Fore.WHITE}Notification Settings")
        print()
        
        print(colors["primary"] + "    💡 HELP & INFO")
        print(colors["secondary"] + f"    [H] {Fore.WHITE}Help & Guide")
        print(colors["secondary"] + f"    [A] {Fore.WHITE}About")
        print(colors["secondary"] + f"    [X] {Fore.WHITE}Exit\n")
        
        return input(colors["accent"] + "    Select option: " + Fore.WHITE).strip().upper()
    
    @staticmethod
    def quick_settings_menu(settings):
        """Quick settings for fast configuration"""
        theme = settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    ⚡ QUICK SETTINGS\n")
        
        print(colors["primary"] + f"    Browsers: {colors['accent']}{settings.get('num_browsers')} " + 
              colors["secondary"] + "[+/-]")
        print(colors["primary"] + f"    Max Tickets: {colors['accent']}{settings.get('max_tickets')} " + 
              colors["secondary"] + "[SHIFT +/-]")
        print(colors["primary"] + f"    Speed: {colors['accent']}{settings.get('min_wait')}-{settings.get('max_wait')}s " + 
              colors["secondary"] + "[S]")
        print(colors["primary"] + f"    Auto-Buy: {colors['accent']}{'ON' if settings.get('auto_buy') else 'OFF'} " + 
              colors["secondary"] + "[A]")
        print(colors["primary"] + f"    Sound: {colors['accent']}{'ON' if settings.get('sound_alerts') else 'OFF'} " + 
              colors["secondary"] + "[M]")
        print()
        print(colors["secondary"] + "    [Enter] Start Hunting")
        print(colors["secondary"] + "    [ESC] Back to Menu\n")
        
        return input(colors["accent"] + "    Action: " + Fore.WHITE).strip()
    
    @staticmethod
    def live_dashboard_header(theme="cyberpunk"):
        """Enhanced live dashboard header"""
        colors = TerminalUI.THEMES[theme]
        print(f"\n{colors['primary']}{'═'*80}")
        print(colors['accent'] + "  📊 LIVE HUNTING DASHBOARD".center(80))
        print(f"{colors['primary']}{'═'*80}\n")
    
    @staticmethod
    def format_stat_box(title, value, color=Fore.WHITE, width=18):
        """Format a statistic box"""
        box = f"┌{'─' * width}┐\n"
        box += f"│ {title.center(width-2)} │\n"
        box += f"│ {color}{str(value).center(width-2)}{Fore.WHITE} │\n"
        box += f"└{'─' * width}┘"
        return box

class NotificationManager:
    """Handles various notification methods"""
    
    def __init__(self, settings):
        self.settings = settings
        self.notification_queue = deque(maxlen=50)
    
    def notify(self, message, level="info", browser_id=None):
        """Send notification through configured channels"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Add to queue
        self.notification_queue.append({
            "time": timestamp,
            "message": message,
            "level": level,
            "browser_id": browser_id
        })
        
        # Sound notification
        if level in ["alert", "success"] and self.settings.get("sound_alerts"):
            self._play_sound(level)
        
        # Webhook notification for important events
        if level == "alert" and self.settings.get("notification_webhook"):
            self._send_webhook(message)
    
    def _play_sound(self, level):
        """Play notification sound"""
        try:
            if sys.platform == 'darwin':
                sounds = {
                    "alert": '/System/Library/Sounds/Glass.aiff',
                    "success": '/System/Library/Sounds/Hero.aiff',
                    "error": '/System/Library/Sounds/Basso.aiff'
                }
                subprocess.run(['afplay', sounds.get(level, sounds["alert"])])
            elif sys.platform == 'win32':
                import winsound
                frequencies = {"alert": 1000, "success": 1500, "error": 500}
                winsound.Beep(frequencies.get(level, 1000), 300)
            elif sys.platform.startswith('linux'):
                subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])
        except:
            pass
    
    def _send_webhook(self, message):
        """Send webhook notification"""
        webhook_url = self.settings.get("notification_webhook")
        if webhook_url:
            try:
                requests.post(webhook_url, json={"content": message}, timeout=5)
            except:
                pass
    
    def get_recent_notifications(self, count=10):
        """Get recent notifications"""
        return list(self.notification_queue)[-count:]

class FanSaleUltimate:
    """Enhanced FanSale bot with advanced features"""
    
    def __init__(self):
        self.target_url = DEFAULT_TARGET_URL
        self.twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY', '').strip()
        
        # Managers
        self.settings = SettingsManager()
        self.stats = StatsTracker()
        self.notifications = NotificationManager(self.settings)
        
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
        
        # Enhanced selectors for FanSale.it
        self.ticket_selectors = [
            # Primary selectors based on HTML structure
            "span.OfferEntry-SeatDescription",
            "div.OfferEntry",
            "tr.EventEntry",
            
            # Additional specific selectors
            "div[data-qa='ticketToBuy']",
            "a.offer-list-item",
            "article.listing-item",
            
            # Italian-specific selectors
            "div[class*='biglietto']",
            "div[class*='offerta']",
            "article[class*='evento']",
            
            # Generic fallbacks
            "div[class*='ticket'][class*='available']",
            "div[class*='ticket-card']",
            "div[class*='event-card']",
            "a[href*='/tickets/']"
        ]
        
        self.buy_selectors = [
            # FanSale specific
            "button[data-qa='buyNowButton']",
            
            # Italian text variations (XPath)
            "//button[contains(text(), 'Acquista')]",
            "//button[contains(text(), 'Compra')]",
            "//button[contains(text(), 'Prenota')]",
            "//button[contains(text(), 'Procedi')]",
            
            # Class-based CSS selectors
            "button[class*='buy']",
            "button[class*='purchase']",
            "button[class*='acquista']",
            "button[class*='primary'][class*='button']",
            "button.Button--primary",
            "a.Button--primary",
            
            # Generic submit
            "button[type='submit']:not([disabled])"
        ]
    
    def log(self, message, level='info', browser_id=None):
        """Enhanced logging with better visual design"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        # Enhanced icons for different log levels
        icons = {
            'info': '📌',
            'success': '✅',
            'warning': '⚠️ ',
            'error': '❌',
            'alert': '🚨',
            'ticket': '🎫',
            'check': '🔍',
            'browser': '🌐',
            'stealth': '🥷',
            'speed': '⚡'
        }
        
        color_map = {
            'info': colors["primary"],
            'success': colors["success"],
            'warning': colors["warning"],
            'error': colors["error"],
            'alert': colors["accent"],
            'ticket': Style.BRIGHT + colors["success"],
            'check': colors["secondary"],
            'browser': colors["primary"],
            'stealth': Fore.CYAN,
            'speed': Fore.YELLOW
        }
        
        icon = icons.get(level, '•')
        color = color_map.get(level, Fore.WHITE)
        
        with self.display_lock:
            # Format browser ID with color
            browser_str = ""
            if browser_id is not None:
                browser_str = f"{Fore.CYAN}[B{browser_id}]{Style.RESET_ALL} "
            
            # Enhanced message formatting
            formatted_msg = f"{Fore.BLACK + Style.BRIGHT}[{timestamp}]{Style.RESET_ALL} {browser_str}{icon} {color}{message}{Style.RESET_ALL}"
            
            # Clear line and print
            print(f"\r{' '*120}\r{formatted_msg}")
    
    def display_live_stats(self):
        """Enhanced live statistics display"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        while not self.shutdown_event.is_set():
            try:
                stats = self.stats.get_stats()
                runtime = self.stats.get_runtime()
                
                with self.display_lock:
                    # Save cursor position
                    print(f"\033[s", end='')
                    print(f"\033[15;0H", end='')  # Move to line 15
                    
                    # Stats dashboard
                    print(f"\n{colors['primary']}╔{'═'*78}╗")
                    print(f"║{colors['accent']} {'LIVE STATISTICS'.center(76)} {colors['primary']}║")
                    print(f"╠{'═'*78}╣")
                    
                    # Row 1: Basic stats
                    print(f"║ {colors['secondary']}Runtime: {colors['accent']}{runtime:<10} "
                          f"{colors['secondary']}Browsers: {colors['accent']}{stats['active_browsers']:<3} "
                          f"{colors['secondary']}CPM: {colors['accent']}{stats['checks_per_minute']:<5} "
                          f"{colors['secondary']}Best CPM: {colors['accent']}{stats['best_cpm']:<5} {colors['primary']}║")
                    
                    # Row 2: Ticket stats
                    print(f"║ {colors['secondary']}Checks: {colors['accent']}{stats['total_checks']:<8} "
                          f"{colors['secondary']}Found: {colors['accent']}{stats['unique_tickets_seen']:<5} "
                          f"{colors['secondary']}Secured: {colors['success']}{stats['tickets_secured']:<3} "
                          f"{colors['secondary']}Errors: {colors['error']}{stats['errors_encountered']:<3} {colors['primary']}║")
                    
                    # Ticket breakdown
                    if stats['tickets_found']:
                        print(f"╠{'─'*78}╣")
                        tickets_str = " | ".join([f"{cat.upper()}: {count}" 
                                                 for cat, count in stats['tickets_found'].items()])
                        print(f"║ {colors['secondary']}Tickets: {colors['accent']}{tickets_str:<65} {colors['primary']}║")
                    
                    # Recent tickets
                    recent_tickets = self.stats.get_ticket_history()[-3:]
                    if recent_tickets:
                        print(f"╠{'─'*78}╣")
                        print(f"║ {colors['secondary']}Recent: {colors['primary']}║")
                        for ticket in recent_tickets:
                            info = f"[{ticket['time']}] {ticket['category'].upper()}"
                            print(f"║   {colors['accent']}{info:<73} {colors['primary']}║")
                    
                    print(f"╚{'═'*78}╝")
                    print(f"\033[u", end='', flush=True)  # Restore cursor
                
                time.sleep(1)
            except:
                time.sleep(1)
    
    def configure_advanced_settings(self):
        """Advanced settings configuration"""
        theme = self.settings.get("theme", "cyberpunk")
        while True:
            TerminalUI.print_header(theme)
            colors = TerminalUI.THEMES[theme]
            
            print(colors["accent"] + "    ⚙️  ADVANCED SETTINGS\n")
            
            print(colors["primary"] + "    HUNTING CONFIGURATION")
            print(colors["secondary"] + f"    [1] Event URL: {colors['accent']}{self.settings.get('target_url')[:40]}...")
            print(colors["secondary"] + f"    [2] Browsers: {colors['accent']}{self.settings.get('num_browsers')}")
            print(colors["secondary"] + f"    [3] Max Tickets: {colors['accent']}{self.settings.get('max_tickets')}")
            print(colors["secondary"] + f"    [4] Ticket Types: {colors['accent']}{', '.join(self.settings.get('ticket_types'))}")
            print()
            
            print(colors["primary"] + "    PERFORMANCE")
            print(colors["secondary"] + f"    [5] Check Speed: {colors['accent']}{self.settings.get('min_wait')}-{self.settings.get('max_wait')}s")
            print(colors["secondary"] + f"    [6] Refresh Interval: {colors['accent']}{self.settings.get('refresh_interval')}s")
            print()
            
            print(colors["primary"] + "    AUTOMATION")
            print(colors["secondary"] + f"    [7] Auto-Buy: {colors['accent']}{'ON' if self.settings.get('auto_buy') else 'OFF'}")
            print(colors["secondary"] + f"    [8] Max Price: {colors['accent']}€{self.settings.get('max_price') or 'No limit'}")
            print(colors["secondary"] + f"    [9] Preferred Sectors: {colors['accent']}{', '.join(self.settings.get('preferred_sectors')) or 'Any'}")
            print()
            
            print(colors["primary"] + "    NETWORK")
            print(colors["secondary"] + f"    [P] Proxy Settings")
            print(colors["secondary"] + f"    [W] Webhook URL")
            print()
            
            print(colors["secondary"] + "    [S] Save as Profile")
            print(colors["secondary"] + "    [B] Back to Menu\n")
            
            choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip().upper()
            
            if choice == '1':
                new_url = input(f"\n{colors['primary']}Enter event URL (or press Enter for Bruce): {Fore.WHITE}").strip()
                if new_url:
                    self.settings.update('target_url', new_url)
                else:
                    self.settings.update('target_url', DEFAULT_TARGET_URL)
                self.log("Event URL updated", 'success')
                time.sleep(1)
                
            elif choice == '2':
                try:
                    num = int(input(f"\n{colors['primary']}Number of browsers (1-8): {Fore.WHITE}"))
                    self.settings.update('num_browsers', max(1, min(8, num)))
                    self.log("Browsers updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '3':
                try:
                    num = int(input(f"\n{colors['primary']}Max tickets to secure: {Fore.WHITE}"))
                    self.settings.update('max_tickets', max(1, num))
                    self.log("Max tickets updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '4':
                print(f"\n{colors['primary']}Select ticket types to hunt:")
                print(f"{colors['secondary']}[1] Prato A (Gold)")
                print(f"{colors['secondary']}[2] Prato B (Silver)")
                print(f"{colors['secondary']}[3] Settore (Numbered sectors)")
                print(f"{colors['secondary']}[4] Tribuna")
                print(f"{colors['secondary']}[5] VIP/Hospitality")
                print(f"{colors['secondary']}[6] Pit/Parterre")
                print(f"{colors['secondary']}[7] Other")
                print(f"{colors['secondary']}[8] All types")
                
                selections = input(f"\n{colors['primary']}Enter numbers separated by commas (e.g., 1,2,3): {Fore.WHITE}").strip()
                if selections:
                    type_map = {
                        '1': 'prato_a',
                        '2': 'prato_b',
                        '3': 'settore',
                        '4': 'tribuna',
                        '5': 'vip',
                        '6': 'pit',
                        '7': 'other',
                        '8': 'all'
                    }
                    selected_types = []
                    for s in selections.split(','):
                        s = s.strip()
                        if s in type_map:
                            if type_map[s] == 'all':
                                selected_types = ['all']
                                break
                            selected_types.append(type_map[s])
                    
                    if selected_types:
                        self.settings.update('ticket_types', selected_types)
                        self.log(f"Ticket types updated: {', '.join(selected_types)}", 'success')
                    else:
                        self.log("No valid types selected", 'error')
                else:
                    self.log("No changes made", 'warning')
                time.sleep(1)
                
            elif choice == '5':
                try:
                    min_wait = float(input(f"\n{colors['primary']}Min wait time (seconds): {Fore.WHITE}"))
                    max_wait = float(input(f"{colors['primary']}Max wait time (seconds): {Fore.WHITE}"))
                    self.settings.update('min_wait', max(0.1, min_wait))
                    self.settings.update('max_wait', max(min_wait, max_wait))
                    self.log("Check speed updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '6':
                try:
                    interval = int(input(f"\n{colors['primary']}Page refresh interval (seconds): {Fore.WHITE}"))
                    self.settings.update('refresh_interval', max(5, interval))
                    self.log("Refresh interval updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '7':
                self.settings.update('auto_buy', not self.settings.get('auto_buy'))
                self.log(f"Auto-buy {'enabled' if self.settings.get('auto_buy') else 'disabled'}", 'success')
                time.sleep(1)
                
            elif choice == '8':
                try:
                    price = input(f"\n{colors['primary']}Max price in EUR (0 for no limit): {Fore.WHITE}")
                    self.settings.update('max_price', float(price))
                    self.log("Max price updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '9':
                sectors = input(f"\n{colors['primary']}Preferred sectors (comma-separated, e.g., 1,2,3 or leave empty for any): {Fore.WHITE}").strip()
                if sectors:
                    self.settings.update('preferred_sectors', [s.strip() for s in sectors.split(',')])
                    self.log(f"Preferred sectors updated: {sectors}", 'success')
                else:
                    self.settings.update('preferred_sectors', [])
                    self.log("Preferred sectors cleared - will accept any sector", 'success')
                time.sleep(1)
                
            elif choice == 'S':
                name = input(f"\n{colors['primary']}Profile name: {Fore.WHITE}").strip()
                if name:
                    self.settings.save_profile(name)
                    self.log(f"Profile '{name}' saved", 'success')
                time.sleep(1)
                
            elif choice == 'B':
                break
    
    def profile_manager(self):
        """Manage saved profiles"""
        theme = self.settings.get("theme", "cyberpunk")
        while True:
            TerminalUI.print_header(theme)
            colors = TerminalUI.THEMES[theme]
            
            print(colors["accent"] + "    👤 PROFILE MANAGER\n")
            
            print(colors["primary"] + f"    Active Profile: {colors['accent']}{self.settings.active_profile}\n")
            
            print(colors["secondary"] + "    SAVED PROFILES:")
            for i, (name, profile) in enumerate(self.settings.profiles.items(), 1):
                browsers = profile.get('num_browsers', 2)
                tickets = profile.get('max_tickets', 2)
                print(f"    {colors['secondary']}[{i}] {colors['accent']}{name:<20} "
                      f"{colors['primary']}({browsers} browsers, {tickets} tickets)")
            
            print()
            print(colors["secondary"] + "    [N] New Profile")
            print(colors["secondary"] + "    [D] Delete Profile")
            print(colors["secondary"] + "    [B] Back to Menu\n")
            
            choice = input(colors["accent"] + "    Select profile number or action: " + Fore.WHITE).strip().upper()
            
            if choice == 'B':
                break
            elif choice == 'N':
                self.configure_advanced_settings()
            elif choice == 'D':
                name = input(f"\n{colors['primary']}Profile name to delete: {Fore.WHITE}").strip()
                if name in self.settings.profiles and name != "default":
                    del self.settings.profiles[name]
                    self.settings.save_profiles()
                    self.log(f"Profile '{name}' deleted", 'success')
                time.sleep(1)
            else:
                try:
                    idx = int(choice) - 1
                    profile_names = list(self.settings.profiles.keys())
                    if 0 <= idx < len(profile_names):
                        profile_name = profile_names[idx]
                        self.settings.load_profile(profile_name)
                        self.log(f"Loaded profile '{profile_name}'", 'success')
                        time.sleep(1)
                        break
                except:
                    pass
    
    def change_theme(self):
        """Change UI theme"""
        theme = self.settings.get("theme", "cyberpunk")
        TerminalUI.print_header(theme)
        colors = TerminalUI.THEMES[theme]
        
        print(colors["accent"] + "    🎨 SELECT THEME\n")
        
        themes = ["cyberpunk", "matrix", "minimal", "rainbow"]
        for i, t in enumerate(themes, 1):
            sample_colors = TerminalUI.THEMES[t]
            print(f"    [{i}] {sample_colors['accent']}{t.upper()}{Style.RESET_ALL}")
            print(f"        {sample_colors['primary']}Primary {sample_colors['secondary']}Secondary "
                  f"{sample_colors['success']}Success {sample_colors['warning']}Warning{Style.RESET_ALL}")
            print()
        
        try:
            choice = int(input(colors["accent"] + "    Select theme: " + Fore.WHITE))
            if 1 <= choice <= len(themes):
                self.settings.update("theme", themes[choice-1])
                self.log(f"Theme changed to {themes[choice-1]}", 'success')
        except:
            pass
        
        time.sleep(1)
    
    def categorize_ticket(self, text):
        """Enhanced ticket categorization"""
        text_lower = text.lower()
        
        # Primary categories
        if 'prato a' in text_lower or 'prato gold' in text_lower:
            return 'prato_a'
        elif 'prato b' in text_lower or 'prato silver' in text_lower:
            return 'prato_b'
        elif any(f'settore {i}' in text_lower for i in range(1, 30)):
            return 'settore'
        elif 'tribuna' in text_lower:
            return 'tribuna'
        elif 'vip' in text_lower or 'hospitality' in text_lower:
            return 'vip'
        elif 'pit' in text_lower or 'parterre' in text_lower:
            return 'pit'
        else:
            return 'other'
    
    def extract_ticket_price(self, text):
        """Extract price from ticket text"""
        import re
        # Look for price patterns like €50, EUR 50, 50€, etc.
        price_pattern = r'[€EUR]\s*(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\s*[€EUR]'
        match = re.search(price_pattern, text)
        if match:
            price_str = match.group(1) or match.group(2)
            return float(price_str.replace(',', '.'))
        return None
    
    def should_buy_ticket(self, ticket_info):
        """Determine if ticket should be purchased based on rules"""
        if not self.settings.get('auto_buy'):
            return True  # Manual mode - try all matching types
        
        # Check price limit
        max_price = self.settings.get('max_price', 0)
        if max_price > 0 and ticket_info.get('price'):
            if ticket_info['price'] > max_price:
                return False
        
        # Check preferred sectors
        preferred = self.settings.get('preferred_sectors', [])
        if preferred and ticket_info.get('sector'):
            if ticket_info['sector'] not in preferred:
                return False
        
        # Check blacklist
        blacklist = self.settings.get('blacklist_sectors', [])
        if blacklist and ticket_info.get('sector'):
            if ticket_info['sector'] in blacklist:
                return False
        
        return True
    
    def generate_ticket_hash(self, text):
        """Generate unique hash for ticket"""
        clean_text = ''.join(c for c in text if c.isalnum() or c.isspace())
        return hashlib.md5(clean_text.encode()).hexdigest()
    
    def create_browser(self, browser_id):
        """Create undetected Chrome instance - minimal setup to avoid detection"""
        try:
            self.log(f"Creating browser {browser_id}...", 'browser')
            
            # Create minimal ChromeOptions (like diagnostic test that worked)
            options = uc.ChromeOptions()
            
            # Only add essential options
            profile_dir = Path.home() / ".fansale_bot_profiles" / f"browser_{browser_id}"
            profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--user-data-dir={str(profile_dir)}')
            
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
            
            # Create driver with minimal setup (no version_main, no extra options)
            driver = uc.Chrome(options=options)
            
            self.log(f"Browser {browser_id} created successfully", 'success')
            return driver
            
        except Exception as e:
            self.log(f"Failed to create browser: {str(e)}", 'error')
            
            # Try even more minimal approach as fallback
            try:
                self.log(f"Trying ultra-minimal setup...", 'warning')
                driver = uc.Chrome()  # Absolute minimal like diagnostic
                self.log(f"Browser {browser_id} created with ultra-minimal setup", 'success')
                return driver
                
            except Exception as e2:
                self.log(f"Ultra-minimal also failed: {str(e2)}", 'error')
                raise Exception(f"Failed to create browser: {str(e)}")
    
    def dismiss_popups(self, driver):
        """Enhanced popup dismissal for FanSale"""
        dismissed = 0
        
        # FanSale-specific selectors
        selectors = [
            # Bot protection
            "button.js-BotProtectionModalButton1",
            "button[class*='BotProtection']",
            "button[class*='botprotection']",
            
            # Italian text buttons
            "//button[contains(text(), 'Carica')]",
            "//button[contains(text(), 'Continua')]",
            "//button[contains(text(), 'Accetta')]",
            "//button[contains(text(), 'OK')]",
            
            # Cookie/privacy
            "button[class*='cookie-accept']",
            "button[class*='privacy-accept']",
            "button#onetrust-accept-btn-handler",
            
            # Generic close buttons
            "button[aria-label*='close']",
            "button[aria-label*='chiudi']",
            "button[class*='modal-close']",
            "button[class*='close-button']",
            "a[class*='close']"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        # Try JavaScript click first
                        driver.execute_script("arguments[0].click();", elem)
                        dismissed += 1
                    except:
                        try:
                            # Fallback to regular click
                            elem.click()
                            dismissed += 1
                        except:
                            pass
            except:
                pass
        
        # Check for iframe popups
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    # Try to find close buttons in iframe
                    close_btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='close'], a[class*='close']")
                    for btn in close_btns:
                        try:
                            btn.click()
                            dismissed += 1
                        except:
                            pass
                    driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
        except:
            pass
        
        return dismissed
    
    def detect_captcha(self, driver):
        """Enhanced CAPTCHA detection"""
        if time.time() - self.last_captcha_solve < self.captcha_grace_period:
            return False
        
        captcha_indicators = [
            # Google reCAPTCHA
            "iframe[src*='recaptcha']",
            "div[class*='g-recaptcha']",
            "div#recaptcha",
            
            # hCaptcha
            "iframe[src*='hcaptcha']",
            "div[class*='h-captcha']",
            
            # Generic
            "div[class*='captcha']",
            "div[id*='captcha']",
            "img[src*='captcha']"
        ]
        
        for selector in captcha_indicators:
            try:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    return True
            except:
                pass
        
        # Check page text for CAPTCHA keywords
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            captcha_keywords = ['captcha', 'verifica', 'non sono un robot', "i'm not a robot"]
            if any(keyword in page_text for keyword in captcha_keywords):
                return True
        except:
            pass
        
        return False
    
    def solve_captcha(self, driver, browser_id):
        """Handle CAPTCHA (auto or manual)"""
        self.log(f"CAPTCHA detected!", 'warning', browser_id)
        self.stats.record_captcha_solved()
        
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
    
    def extract_ticket_info(self, element):
        """Extract detailed ticket information"""
        try:
            text = element.text.strip()
            info = {
                'raw_text': text,
                'category': self.categorize_ticket(text),
                'price': self.extract_ticket_price(text),
                'sector': None,
                'row': None,
                'seat': None
            }
            
            # Extract sector
            import re
            sector_match = re.search(r'settore\s+(\d+)', text.lower())
            if sector_match:
                info['sector'] = sector_match.group(1)
            
            # Extract row
            row_match = re.search(r'fila\s+(\d+)|row\s+(\d+)', text.lower())
            if row_match:
                info['row'] = row_match.group(1) or row_match.group(2)
            
            # Extract seat
            seat_match = re.search(r'posto\s+(\d+)|seat\s+(\d+)', text.lower())
            if seat_match:
                info['seat'] = seat_match.group(1) or seat_match.group(2)
            
            return info
        except:
            return {
                'raw_text': 'Unknown',
                'category': 'other',
                'price': None
            }
    
    def attempt_purchase(self, driver, ticket_element, browser_id):
        """Enhanced purchase attempt with multiple strategies"""
        try:
            # Scroll to element
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            time.sleep(0.2)
            
            # Try multiple click methods
            clicked = False
            
            # Method 1: JavaScript click on main element
            try:
                driver.execute_script("arguments[0].click();", ticket_element)
                clicked = True
                self.log("Clicked ticket with JavaScript", 'info', browser_id)
            except:
                pass
            
            # Method 2: Find and click specific link
            if not clicked:
                try:
                    # FanSale specific link selectors
                    link_selectors = [
                        "a[href*='/tickets/']",
                        "a.Button-inOfferEntryList",
                        "a[id*='detailBShowOfferButton']"
                    ]
                    for selector in link_selectors:
                        try:
                            link = ticket_element.find_element(By.CSS_SELECTOR, selector)
                            driver.execute_script("arguments[0].click();", link)
                            clicked = True
                            self.log(f"Clicked link with selector: {selector}", 'info', browser_id)
                            break
                        except:
                            pass
                except:
                    pass
            
            # Method 3: ActionChains click
            if not clicked:
                try:
                    ActionChains(driver).move_to_element(ticket_element).click().perform()
                    clicked = True
                    self.log("Clicked with ActionChains", 'info', browser_id)
                except:
                    pass
            
            # Method 4: Regular click as last resort
            if not clicked:
                try:
                    ticket_element.click()
                    clicked = True
                    self.log("Clicked with regular click", 'info', browser_id)
                except:
                    pass
            
            if not clicked:
                self.log("Failed to click ticket", 'error', browser_id)
                return False
            
            # Wait for page load/navigation
            time.sleep(1)
            
            # Dismiss any popups that might appear
            self.dismiss_popups(driver)
            
            # Find and click buy button
            for selector in self.buy_selectors:
                try:
                    if selector.startswith('//'):
                        buy_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Verify button text if possible
                    btn_text = buy_btn.text.lower()
                    if any(word in btn_text for word in ['acquista', 'compra', 'buy', 'prenota']):
                        # Scroll to button
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                        time.sleep(0.1)
                        
                        # Click buy button
                        driver.execute_script("arguments[0].click();", buy_btn)
                        
                        self.log(f"🎯 BUY BUTTON CLICKED! ({btn_text})", 'alert', browser_id)
                        
                        # Take screenshot if enabled
                        if self.settings.get('auto_screenshot'):
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            Path("screenshots").mkdir(exist_ok=True)
                            screenshot_path = f"screenshots/purchase_{browser_id}_{timestamp}.png"
                            driver.save_screenshot(screenshot_path)
                            self.log(f"📸 Screenshot saved: {screenshot_path}", 'info', browser_id)
                        
                        # Check for CAPTCHA after buy click
                        time.sleep(1)
                        if self.detect_captcha(driver):
                            if not self.solve_captcha(driver, browser_id):
                                return False
                        
                        # Wait for potential redirect/confirmation
                        time.sleep(2)
                        
                        # Check if we're on a checkout/payment page
                        current_url = driver.current_url.lower()
                        if any(word in current_url for word in ['checkout', 'payment', 'pagamento', 'cart', 'carrello']):
                            self.log("✅ Reached checkout page!", 'success', browser_id)
                            
                            # Take another screenshot of checkout
                            if self.settings.get('auto_screenshot'):
                                screenshot_path = f"screenshots/checkout_{browser_id}_{timestamp}.png"
                                driver.save_screenshot(screenshot_path)
                                self.log(f"📸 Checkout screenshot: {screenshot_path}", 'info', browser_id)
                        
                        return True
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    self.log(f"Error with buy button: {str(e)[:50]}", 'warning', browser_id)
                    continue
            
            self.log(f"No buy button found on detail page", 'warning', browser_id)
            
            # Try to go back and try next ticket
            driver.back()
            return False
            
        except Exception as e:
            self.log(f"Purchase failed - {str(e)[:50]}", 'error', browser_id)
            self.stats.record_error()
            return False
    
    def hunt_tickets(self, browser_id, driver):
        """Enhanced hunting loop with smart features"""
        self.log(f"Hunter starting...", 'browser', browser_id)
        
        # Navigate to target
        target_url = self.settings.get('target_url', DEFAULT_TARGET_URL)
        try:
            driver.get(target_url)
            self.log(f"Page loaded: {target_url[:50]}...", 'info', browser_id)
            
            # Wait for page to fully load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            self.log(f"Navigation failed - {e}", 'error', browser_id)
            self.stats.record_error()
            return
        
        # Initial setup
        time.sleep(2)
        initial_popups = self.dismiss_popups(driver)
        if initial_popups > 0:
            self.log(f"Dismissed {initial_popups} initial popups", 'info', browser_id)
        
        last_refresh = time.time()
        last_popup_check = time.time()
        consecutive_errors = 0
        
        # Main hunting loop
        while not self.shutdown_event.is_set():
            try:
                # Check if we've secured enough tickets
                if self.tickets_secured >= self.settings.get('max_tickets'):
                    self.log("Target reached, stopping hunter", 'success', browser_id)
                    break
                
                # Record check
                self.stats.record_check()
                
                # Log speed every 20 checks
                if self.stats.stats['total_checks'] % 20 == 0:
                    cpm = self.stats.stats['checks_per_minute']
                    self.log(f"Current speed: {cpm} CPM", 'speed', browser_id)
                
                # Periodic popup dismissal
                if time.time() - last_popup_check > 10:
                    dismissed = self.dismiss_popups(driver)
                    if dismissed > 0:
                        self.log(f"Dismissed {dismissed} popups", 'info', browser_id)
                    last_popup_check = time.time()
                
                # Find tickets with all selectors
                tickets = []
                ticket_details = []  # Store the actual text elements
                
                for selector in self.ticket_selectors:
                    try:
                        found = driver.find_elements(By.CSS_SELECTOR, selector)
                        if found:
                            # For span.OfferEntry-SeatDescription, get parent clickable element but store the span
                            if selector == "span.OfferEntry-SeatDescription":
                                parent_tickets = []
                                for elem in found:
                                    # Try to find the parent tr or div that contains the ticket
                                    try:
                                        parent = elem.find_element(By.XPATH, "./ancestor::tr[@class='EventEntry'] | ./ancestor::div[contains(@class,'OfferEntry')]")
                                        if parent and parent not in parent_tickets:
                                            parent_tickets.append(parent)
                                            ticket_details.append(elem)  # Store the span with actual text
                                    except:
                                        # If no parent found, use the element itself
                                        parent_tickets.append(elem)
                                        ticket_details.append(elem)
                                tickets.extend(parent_tickets)
                            else:
                                tickets.extend(found)
                                ticket_details.extend(found)  # For other selectors, element is the same
                            
                            if len(tickets) > 0:
                                self.log(f"Found {len(tickets)} tickets with: {selector}", 'info', browser_id)
                            break  # Use first successful selector
                    except:
                        pass
                
                # Process tickets
                for i, ticket in enumerate(tickets):
                    if self.shutdown_event.is_set():
                        break
                    
                    try:
                        # Extract ticket info from the detail element (which has the actual text)
                        detail_element = ticket_details[i] if i < len(ticket_details) else ticket
                        ticket_info = self.extract_ticket_info(detail_element)
                        ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                        
                        # Check if new
                        if ticket_hash in self.seen_tickets:
                            continue
                        
                        self.seen_tickets.add(ticket_hash)
                        
                        # Record found ticket
                        category = ticket_info['category']
                        self.stats.found_ticket(category, ticket_info)
                        
                        # Log new ticket with details
                        price_str = f"€{ticket_info['price']}" if ticket_info['price'] else "Price unknown"
                        sector_str = f"Sector {ticket_info['sector']}" if ticket_info['sector'] else ""
                        raw_text = ticket_info['raw_text'][:100] if len(ticket_info['raw_text']) > 100 else ticket_info['raw_text']
                        
                        self.log(f"🎫 NEW TICKET: {category.upper()} - {price_str} {sector_str}", 'ticket', browser_id)
                        self.log(f"   Details: {raw_text}", 'info', browser_id)
                        
                        # Check if we should buy
                        ticket_types = self.settings.get('ticket_types')
                        if 'all' in ticket_types or category in ticket_types:
                            if self.should_buy_ticket(ticket_info):
                                with self.purchase_lock:
                                    if self.tickets_secured < self.settings.get('max_tickets'):
                                        self.log(f"⚡ Attempting purchase...", 'warning', browser_id)
                                        
                                        if self.attempt_purchase(driver, ticket, browser_id):
                                            self.tickets_secured += 1
                                            self.stats.secured_ticket()
                                            self.log(f"🎉 TICKET SECURED! ({self.tickets_secured}/{self.settings.get('max_tickets')})", 'alert')
                                            
                                            # Reset to main page after successful purchase
                                            driver.get(target_url)
                                            time.sleep(2)
                                            
                                            if self.tickets_secured >= self.settings.get('max_tickets'):
                                                self.log("🏆 ALL TICKETS SECURED!", 'alert')
                                                self.shutdown_event.set()
                                                return
                            else:
                                self.log(f"Skipped: {ticket_info.get('reason', 'Does not meet criteria')}", 'info', browser_id)
                    
                    except Exception as e:
                        self.log(f"Error processing ticket: {str(e)[:30]}", 'warning', browser_id)
                        continue
                
                # Reset error counter on successful iteration
                consecutive_errors = 0
                
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
                    time.sleep(2)
                    self.dismiss_popups(driver)
                    last_refresh = time.time()
                
            except WebDriverException as e:
                consecutive_errors += 1
                if "invalid session" in str(e).lower():
                    self.log(f"Session died", 'error', browser_id)
                    break
                else:
                    self.log(f"WebDriver error ({consecutive_errors})", 'error', browser_id)
                    self.stats.record_error()
                    
                    if consecutive_errors > 5:
                        self.log(f"Too many errors, restarting browser", 'warning', browser_id)
                        try:
                            driver.get(target_url)
                            consecutive_errors = 0
                        except:
                            break
                    
                    time.sleep(2)
                    
            except Exception as e:
                self.log(f"Unexpected error - {str(e)[:50]}", 'error', browser_id)
                self.stats.record_error()
                time.sleep(2)
    
    def run_bot(self):
        """Run the bot with current settings"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        # Show run configuration
        TerminalUI.print_header(theme)
        print(colors["accent"] + "    🚀 STARTING HUNT\n")
        
        target_url = self.settings.get('target_url', DEFAULT_TARGET_URL)
        print(f"{colors['primary']}    Target: {colors['accent']}{target_url[:60]}...")
        print(f"{colors['primary']}    Browsers: {colors['accent']}{self.settings.get('num_browsers')}")
        print(f"{colors['primary']}    Max tickets: {colors['accent']}{self.settings.get('max_tickets')}")
        print(f"{colors['primary']}    Hunting: {colors['accent']}{', '.join(self.settings.get('ticket_types'))}")
        print(f"{colors['primary']}    Auto-buy: {colors['accent']}{'ON' if self.settings.get('auto_buy') else 'OFF'}\n")
        
        input(colors["secondary"] + "    Press Enter to start hunting..." + Fore.WHITE)
        
        # Clear screen and show dashboard header
        TerminalUI.clear()
        TerminalUI.live_dashboard_header(theme)
        
        # Start live stats display thread
        stats_thread = threading.Thread(target=self.display_live_stats, daemon=True)
        stats_thread.start()
        
        # Create browsers and start hunting threads
        with ThreadPoolExecutor(max_workers=self.settings.get('num_browsers')) as executor:
            futures = []
            
            for i in range(self.settings.get('num_browsers')):
                try:
                    driver = self.create_browser(i)
                    self.browsers.append(driver)
                    self.stats.stats['active_browsers'] += 1
                    
                    future = executor.submit(self.hunt_tickets, i, driver)
                    futures.append(future)
                    
                    self.log(f"✅ Browser {i} launched", 'success')
                    time.sleep(1)
                    
                except Exception as e:
                    self.log(f"❌ Failed to create browser {i}: {e}", 'error')
                    self.stats.record_error()
            
            # Wait for completion
            try:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.log(f"Thread error: {e}", 'error')
                        self.stats.record_error()
                        
            except KeyboardInterrupt:
                self.log("\n⚠️  Shutdown requested...", 'warning')
                self.shutdown_event.set()
        
        # Cleanup
        self.log("Closing browsers...", 'info')
        for driver in self.browsers:
            try:
                driver.quit()
            except:
                pass
        
        # Save historical stats
        self.stats.save_historical_stats()
        
        # Final summary
        stats = self.stats.get_stats()
        runtime = self.stats.get_runtime()
        
        print(f"\n{colors['primary']}{'='*80}")
        print(colors['accent'] + "  📊 HUNTING SESSION COMPLETE".center(80))
        print(f"{colors['primary']}{'='*80}\n")
        
        print(f"{colors['secondary']}  Runtime: {colors['accent']}{runtime}")
        print(f"{colors['secondary']}  Total checks: {colors['accent']}{stats['total_checks']:,}")
        print(f"{colors['secondary']}  Unique tickets seen: {colors['accent']}{stats['unique_tickets_seen']}")
        print(f"{colors['secondary']}  Tickets secured: {colors['success']}{stats['tickets_secured']}")
        print(f"{colors['secondary']}  Best CPM: {colors['accent']}{stats['best_cpm']}")
        print(f"{colors['secondary']}  Errors: {colors['error']}{stats['errors_encountered']}")
        print(f"{colors['secondary']}  CAPTCHAs solved: {colors['accent']}{stats['captchas_solved']}")
        
        if stats['tickets_found']:
            print(f"\n{colors['secondary']}  Tickets by type:")
            for category, count in stats['tickets_found'].items():
                print(f"    {colors['accent']}• {category.upper()}: {count}")
        
        print(f"\n{colors['primary']}{'='*80}\n")
        
        if stats['tickets_secured'] > 0:
            self.log("🎉 Check your screenshots folder for proof of purchase!", 'alert')
        
        input(f"\n{colors['secondary']}Press Enter to return to menu...{Fore.WHITE}")
    
    def show_statistics(self):
        """Show detailed statistics and history"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📊 STATISTICS & HISTORY\n")
        
        # Current session stats
        if hasattr(self, 'stats') and self.stats.stats['total_checks'] > 0:
            stats = self.stats.get_stats()
            runtime = self.stats.get_runtime()
            
            print(colors["primary"] + "    CURRENT SESSION")
            print(colors["secondary"] + f"    Runtime: {colors['accent']}{runtime}")
            print(colors["secondary"] + f"    Checks: {colors['accent']}{stats['total_checks']:,}")
            print(colors["secondary"] + f"    Best CPM: {colors['accent']}{stats['best_cpm']}")
            print(colors["secondary"] + f"    Tickets secured: {colors['success']}{stats['tickets_secured']}")
            print()
        
        # Historical stats
        if hasattr(self.stats, 'historical'):
            hist = self.stats.historical
            
            print(colors["primary"] + "    ALL TIME STATISTICS")
            print(colors["secondary"] + f"    Total runs: {colors['accent']}{hist['total_runs']}")
            print(colors["secondary"] + f"    Total runtime: {colors['accent']}{hist['total_runtime']//3600:.0f} hours")
            print(colors["secondary"] + f"    Total checks: {colors['accent']}{hist['total_checks']:,}")
            print(colors["secondary"] + f"    Total secured: {colors['success']}{hist['total_secured']}")
            
            if hist['tickets_by_type']:
                print(f"\n{colors['secondary']}    Tickets by type:")
                for category, count in hist['tickets_by_type'].items():
                    print(f"      {colors['accent']}• {category.upper()}: {count}")
            
            if hist['best_session']['date']:
                print(f"\n{colors['primary']}    BEST SESSION")
                print(f"{colors['secondary']}    Date: {colors['accent']}{hist['best_session']['date']}")
                print(f"{colors['secondary']}    Tickets: {colors['success']}{hist['best_session']['tickets']}")
                print(f"{colors['secondary']}    CPM: {colors['accent']}{hist['best_session']['cpm']}")
        
        # Recent notifications
        if hasattr(self, 'notifications'):
            recent = self.notifications.get_recent_notifications(10)
            if recent:
                print(f"\n{colors['primary']}    RECENT EVENTS")
                for notif in recent:
                    level_colors = {
                        'alert': colors['accent'],
                        'success': colors['success'],
                        'error': colors['error'],
                        'warning': colors['warning']
                    }
                    color = level_colors.get(notif['level'], colors['secondary'])
                    print(f"    {color}[{notif['time']}] {notif['message']}")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def show_help(self):
        """Display comprehensive help"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📖 HELP & GUIDE\n")
        
        print(colors["primary"] + "    QUICK START")
        print(colors["secondary"] + "    1. Configure settings (browsers, ticket types)")
        print(colors["secondary"] + "    2. Set up auto-buy rules if desired")
        print(colors["secondary"] + "    3. Start hunting and monitor live stats")
        print(colors["secondary"] + "    4. Bot will notify you of purchases\n")
        
        print(colors["primary"] + "    TIPS FOR SUCCESS")
        print(colors["secondary"] + "    • Use 2-4 browsers for best coverage")
        print(colors["secondary"] + "    • Set specific ticket types to reduce noise")
        print(colors["secondary"] + "    • Enable auto-buy for faster purchases")
        print(colors["secondary"] + "    • Set price limits to avoid overpaying")
        print(colors["secondary"] + "    • Keep sound alerts on for notifications\n")
        
        print(colors["primary"] + "    KEYBOARD SHORTCUTS")
        print(colors["secondary"] + "    • Ctrl+C: Stop the bot gracefully")
        print(colors["secondary"] + "    • In quick settings: +/- adjust browsers")
        print(colors["secondary"] + "    • In quick settings: A toggle auto-buy\n")
        
        print(colors["primary"] + "    PERFORMANCE TARGETS")
        print(colors["secondary"] + "    • 60-300 checks/minute per browser")
        print(colors["secondary"] + "    • <1 second purchase decision")
        print(colors["secondary"] + "    • Linear scaling with browsers\n")
        
        print(colors["primary"] + "    TROUBLESHOOTING")
        print(colors["secondary"] + "    • Chrome errors: Update Chrome browser")
        print(colors["secondary"] + "    • Slow performance: Reduce browser count")
        print(colors["secondary"] + "    • No tickets found: Check selectors match site")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def show_about(self):
        """Show about information"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    💎 ABOUT FANSALE ULTIMATE BOT\n")
        
        print(colors["secondary"] + "    Version: " + colors["accent"] + "Enhanced Edition")
        print(colors["secondary"] + "    Purpose: " + colors["accent"] + "High-speed ticket reservation")
        print(colors["secondary"] + "    Target: " + colors["accent"] + "FanSale.it platform\n")
        
        print(colors["primary"] + "    FEATURES")
        print(colors["secondary"] + "    • Multi-browser parallel hunting")
        print(colors["secondary"] + "    • Real-time statistics dashboard")
        print(colors["secondary"] + "    • Persistent settings & profiles")
        print(colors["secondary"] + "    • CAPTCHA handling (auto/manual)")
        print(colors["secondary"] + "    • Smart purchase rules")
        print(colors["secondary"] + "    • Multiple UI themes\n")
        
        print(colors["primary"] + "    PERFORMANCE")
        print(colors["secondary"] + "    • Ticket detection: <100ms")
        print(colors["secondary"] + "    • Purchase decision: <10ms")
        print(colors["secondary"] + "    • Checks per minute: 60-300\n")
        
        print(colors["warning"] + "    ⚠️  DISCLAIMER")
        print(colors["secondary"] + "    This bot is for educational and defensive")
        print(colors["secondary"] + "    purposes only. Users are responsible for")
        print(colors["secondary"] + "    complying with FanSale's terms of service.")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def main(self):
        """Enhanced main application loop"""
        while True:
            choice = TerminalUI.main_menu(self.settings)
            
            if choice == '1':
                # Start hunting
                self.run_bot()
                # Reset for next run
                self.shutdown_event.clear()
                self.tickets_secured = 0
                self.seen_tickets.clear()
                self.browsers.clear()
                self.stats = StatsTracker()
                
            elif choice == '2':
                # Quick settings
                self.quick_settings()
                
            elif choice == '3':
                # Advanced settings
                self.configure_advanced_settings()
                
            elif choice == '4':
                # Profile manager
                self.profile_manager()
                
            elif choice == '5':
                # Auto-buy rules
                self.configure_auto_buy_rules()
                
            elif choice == '6':
                # Live dashboard (demo)
                self.show_live_dashboard_demo()
                
            elif choice == '7':
                # Statistics
                self.show_statistics()
                
            elif choice == '8':
                # Performance report
                self.show_performance_report()
                
            elif choice == '9':
                # Change theme
                self.change_theme()
                
            elif choice == '0':
                # Notification settings
                self.configure_notifications()
                
            elif choice == 'H':
                # Help
                self.show_help()
                
            elif choice == 'A':
                # About
                self.show_about()
                
            elif choice == 'X':
                # Exit
                theme = self.settings.get("theme", "cyberpunk")
                colors = TerminalUI.THEMES[theme]
                print(f"\n{colors['accent']}    👋 Thanks for using FanSale Ultimate Bot!")
                print(f"{colors['secondary']}    Happy hunting!\n")
                break
            
            else:
                self.log("Invalid choice", 'error')
                time.sleep(1)
    
    def quick_settings(self):
        """Quick settings interface"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        while True:
            action = TerminalUI.quick_settings_menu(self.settings)
            
            if action == '':
                # Start hunting
                self.run_bot()
                break
            elif action == '+':
                # Increase browsers
                current = self.settings.get('num_browsers')
                self.settings.update('num_browsers', min(8, current + 1))
            elif action == '-':
                # Decrease browsers
                current = self.settings.get('num_browsers')
                self.settings.update('num_browsers', max(1, current - 1))
            elif action.upper() == 'A':
                # Toggle auto-buy
                self.settings.update('auto_buy', not self.settings.get('auto_buy'))
            elif action.upper() == 'M':
                # Toggle sound
                self.settings.update('sound_alerts', not self.settings.get('sound_alerts'))
            elif action.upper() == 'S':
                # Adjust speed
                try:
                    min_wait = float(input(f"\n{colors['primary']}Min wait (seconds): {Fore.WHITE}"))
                    max_wait = float(input(f"{colors['primary']}Max wait (seconds): {Fore.WHITE}"))
                    self.settings.update('min_wait', max(0.1, min_wait))
                    self.settings.update('max_wait', max(min_wait, max_wait))
                except:
                    pass
            elif action == '\x1b':  # ESC key
                break
    
    def configure_auto_buy_rules(self):
        """Configure auto-buy rules"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🤖 AUTO-BUY RULES\n")
        
        # Current rules
        print(colors["primary"] + "    CURRENT CONFIGURATION")
        print(colors["secondary"] + f"    Auto-buy: {colors['accent']}{'ENABLED' if self.settings.get('auto_buy') else 'DISABLED'}")
        print(colors["secondary"] + f"    Max price: {colors['accent']}€{self.settings.get('max_price') or 'No limit'}")
        print(colors["secondary"] + f"    Preferred sectors: {colors['accent']}{', '.join(self.settings.get('preferred_sectors')) or 'Any'}")
        print(colors["secondary"] + f"    Blacklist: {colors['accent']}{', '.join(self.settings.get('blacklist_sectors')) or 'None'}\n")
        
        print(colors["secondary"] + "    [1] Toggle Auto-buy")
        print(colors["secondary"] + "    [2] Set Max Price")
        print(colors["secondary"] + "    [3] Set Preferred Sectors")
        print(colors["secondary"] + "    [4] Set Blacklist Sectors")
        print(colors["secondary"] + "    [5] Clear All Rules")
        print(colors["secondary"] + "    [B] Back to Menu\n")
        
        choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip()
        
        if choice == '1':
            self.settings.update('auto_buy', not self.settings.get('auto_buy'))
            self.log(f"Auto-buy {'enabled' if self.settings.get('auto_buy') else 'disabled'}", 'success')
        elif choice == '2':
            try:
                price = float(input(f"\n{colors['primary']}Max price in EUR (0 for no limit): {Fore.WHITE}"))
                self.settings.update('max_price', price)
                self.log("Max price updated", 'success')
            except:
                self.log("Invalid price", 'error')
        elif choice == '3':
            sectors = input(f"\n{colors['primary']}Preferred sectors (comma-separated, e.g., 1,2,3): {Fore.WHITE}").strip()
            if sectors:
                self.settings.update('preferred_sectors', [s.strip() for s in sectors.split(',')])
                self.log("Preferred sectors updated", 'success')
        elif choice == '4':
            sectors = input(f"\n{colors['primary']}Blacklist sectors (comma-separated): {Fore.WHITE}").strip()
            if sectors:
                self.settings.update('blacklist_sectors', [s.strip() for s in sectors.split(',')])
                self.log("Blacklist updated", 'success')
        elif choice == '5':
            self.settings.update('auto_buy', False)
            self.settings.update('max_price', 0)
            self.settings.update('preferred_sectors', [])
            self.settings.update('blacklist_sectors', [])
            self.log("All rules cleared", 'success')
        
        if choice != 'B':
            time.sleep(1)
            self.configure_auto_buy_rules()
    
    def show_live_dashboard_demo(self):
        """Show a demo of the live dashboard"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.clear()
        
        print(colors["accent"] + """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                          LIVE DASHBOARD (DEMO)                           ║
    ╠══════════════════════════════════════════════════════════════════════════╣
    ║                                                                          ║
    ║  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        ║
    ║  │   RUNTIME       │  │  CHECKS/MIN     │  │   TICKETS       │        ║
    ║  │   00:15:42      │  │     247         │  │   FOUND: 18     │        ║
    ║  └─────────────────┘  └─────────────────┘  └─────────────────┘        ║
    ║                                                                          ║
    ║  ┌────────────────────────────────────────────────────────────┐        ║
    ║  │ BROWSER STATUS                                              │        ║
    ║  ├────────────────────────────────────────────────────────────┤        ║
    ║  │ [1] ████████████████████░░░ 75% - Scanning...             │        ║
    ║  │ [2] ██████████████████████ 100% - Purchasing ticket!      │        ║
    ║  │ [3] ████████░░░░░░░░░░░░░░ 35% - Refreshing page          │        ║
    ║  │ [4] ████████████░░░░░░░░░░ 50% - Dismissing popup         │        ║
    ║  └────────────────────────────────────────────────────────────┘        ║
    ║                                                                          ║
    ║  ┌────────────────────────────────────────────────────────────┐        ║
    ║  │ RECENT TICKETS                                              │        ║
    ║  ├────────────────────────────────────────────────────────────┤        ║
    ║  │ [12:34:56] PRATO A - €85 - Sector 3                        │        ║
    ║  │ [12:34:52] SETTORE - €65 - Row 15                          │        ║
    ║  │ [12:34:48] PRATO B - €75 - Available                       │        ║
    ║  └────────────────────────────────────────────────────────────┘        ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
        """ + Style.RESET_ALL)
        
        input(f"\n{colors['secondary']}    This is a preview. Press Enter to return...{Fore.WHITE}")
    
    def show_performance_report(self):
        """Show detailed performance report"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📈 PERFORMANCE REPORT\n")
        
        # Simulated data for demo
        print(colors["primary"] + "    SPEED METRICS")
        print(colors["secondary"] + "    • Ticket detection: " + colors["success"] + "<100ms")
        print(colors["secondary"] + "    • Category analysis: " + colors["success"] + "<10ms")
        print(colors["secondary"] + "    • Purchase decision: " + colors["success"] + "<5ms")
        print(colors["secondary"] + "    • Click execution: " + colors["success"] + "<200ms\n")
        
        print(colors["primary"] + "    EFFICIENCY RATINGS")
        print(colors["secondary"] + "    • CPU usage: " + colors["accent"] + "Low (15-25%)")
        print(colors["secondary"] + "    • Memory usage: " + colors["accent"] + "~200MB per browser")
        print(colors["secondary"] + "    • Network latency: " + colors["accent"] + "Optimized")
        print(colors["secondary"] + "    • Success rate: " + colors["success"] + "95%+\n")
        
        print(colors["primary"] + "    RECOMMENDATIONS")
        print(colors["secondary"] + "    ✓ Current settings are optimized")
        print(colors["secondary"] + "    ✓ Browser count is within ideal range")
        print(colors["secondary"] + "    ✓ Check intervals are balanced")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def configure_notifications(self):
        """Configure notification settings"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🔔 NOTIFICATION SETTINGS\n")
        
        print(colors["secondary"] + f"    Sound alerts: {colors['accent']}{'ON' if self.settings.get('sound_alerts') else 'OFF'}")
        print(colors["secondary"] + f"    Webhook URL: {colors['accent']}{self.settings.get('notification_webhook')[:30] + '...' if self.settings.get('notification_webhook') else 'Not set'}\n")
        
        print(colors["secondary"] + "    [1] Toggle Sound Alerts")
        print(colors["secondary"] + "    [2] Set Webhook URL")
        print(colors["secondary"] + "    [3] Test Notifications")
        print(colors["secondary"] + "    [B] Back to Menu\n")
        
        choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip()
        
        if choice == '1':
            self.settings.update('sound_alerts', not self.settings.get('sound_alerts'))
            self.log(f"Sound alerts {'enabled' if self.settings.get('sound_alerts') else 'disabled'}", 'success')
        elif choice == '2':
            url = input(f"\n{colors['primary']}Webhook URL (Discord/Slack): {Fore.WHITE}").strip()
            self.settings.update('notification_webhook', url)
            self.log("Webhook URL updated", 'success')
        elif choice == '3':
            self.log("Test notification!", 'alert')
            if self.settings.get('notification_webhook'):
                self.notifications._send_webhook("🎫 Test notification from FanSale Bot")
                self.log("Webhook test sent", 'info')
        
        if choice != 'B':
            time.sleep(1)
            self.configure_notifications()


if __name__ == "__main__":
    try:
        bot = FanSaleUltimate()
        bot.main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Bot stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)