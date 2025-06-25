#!/usr/bin/env python3
"""
FanSale Bot - Enhanced Edition with Options Menu
Optimized for speed, stability, and session management
"""

import os
import sys
import time
import random
import logging
import threading
import traceback
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Suppress verbose WebDriver logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('seleniumwire').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from dotenv import load_dotenv
load_dotenv()

# Import enhanced utilities if available
try:
    from utilities.stealth_enhancements import StealthEnhancements
    from utilities.speed_optimizer import SpeedOptimizer, FastTicketChecker
    from utilities.session_manager import SessionManager
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False


@dataclass
class BotConfiguration:
    """Bot configuration with defaults"""
    num_browsers: int = 2
    use_proxy: bool = False
    use_auto_login: bool = True
    max_tickets: int = 4
    ticket_filters: List[str] = field(default_factory=list)
    filter_mode: str = 'any'  # 'any' or 'all'
    clear_profiles_on_start: bool = False
    session_refresh_interval: int = 900  # 15 minutes
    check_interval_base: float = 3.0  # Base wait time between checks
    
    def save(self, path: Path = Path("bot_config.json")):
        """Save configuration to file"""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, path: Path = Path("bot_config.json")):
        """Load configuration from file"""
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                return cls(**data)
            except:
                pass
        return cls()


# Configure cleaner logging
class CleanFormatter(logging.Formatter):
    """Custom formatter to suppress WebDriver stack traces"""
    def format(self, record):
        msg = str(record.msg)
        if "Stacktrace:" in msg:
            msg = msg.split('\n')[0]
            record.msg = msg
        return super().format(record)


# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(CleanFormatter('%(asctime)s | %(threadName)-10s | %(message)s', datefmt='%H:%M:%S'))
logger.handlers = [console_handler]

file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(CleanFormatter('%(asctime)s | %(threadName)-10s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(file_handler)


class FanSaleBot:
    """Enhanced FanSale ticket bot with better configuration management"""
    
    def __init__(self):
        # Load saved configuration
        self.config = BotConfiguration.load()
        
        # Credentials from env
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
        
        # Apply configuration
        self.num_browsers = self.config.num_browsers
        self.use_proxy = self.config.use_proxy
        self.use_auto_login = self.config.use_auto_login
        self.max_tickets = self.config.max_tickets
        self.ticket_filters = self.config.ticket_filters
        self.filter_mode = self.config.filter_mode
        self.session_refresh_interval = self.config.session_refresh_interval
        
        # Browser management
        self.browsers = []
        self.browser_threads = []
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        self.shutdown_event = threading.Event()
        
        # Statistics with enhanced tracking
        self.stats = {
            'total_checks': 0,
            'no_ticket_found': 0,
            'tickets_found': 0,
            'successful_checkouts': 0,
            'already_reserved': 0,
            'start_time': None,
            'ticket_categories': {
                'prato_a': 0,
                'prato_b': 0,
                'settore': 0,
                'tribuna': 0,
                'other': 0
            }
        }
        
        # Session management
        self.last_login_check = {}
        self.login_check_interval = 300  # 5 minutes
        self.last_session_refresh = {}
        
        # Enhanced features
        if ENHANCED_MODE:
            self.stealth = StealthEnhancements()
            self.optimizer = SpeedOptimizer()
            self.session_manager = SessionManager()
    
    def show_options_menu(self):
        """Display enhanced options menu"""
        while True:
            print("\n" + "="*60)
            print("⚙️  BOT OPTIONS & CONFIGURATION")
            print("="*60)
            print(f"\n📋 Current Configuration:")
            print(f"   • Browsers: {self.config.num_browsers}")
            print(f"   • Use Proxy: {'Yes' if self.config.use_proxy else 'No'}")
            print(f"   • Auto-login: {'Yes' if self.config.use_auto_login else 'No'}")
            print(f"   • Max Tickets: {self.config.max_tickets}")
            print(f"   • Clear Profiles on Start: {'Yes' if self.config.clear_profiles_on_start else 'No'}")
            print(f"   • Session Refresh: {self.config.session_refresh_interval // 60} minutes")
            
            if self.config.ticket_filters:
                print(f"   • Filters: {', '.join(self.config.ticket_filters)} ({self.config.filter_mode} mode)")
            else:
                print(f"   • Filters: None (accepting ALL tickets)")
            
            print("\n1. Change Number of Browsers")
            print("2. Toggle Proxy Usage")
            print("3. Toggle Auto-login")
            print("4. Configure Ticket Filters")
            print("5. Set Max Tickets to Purchase")
            print("6. Toggle Clear Profiles on Start")
            print("7. Set Session Refresh Interval")
            print("8. Save and Return to Main Menu")
            print("9. Cancel (Don't Save Changes)")
            
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                self.configure_browsers()
            elif choice == '2':
                self.config.use_proxy = not self.config.use_proxy
                print(f"\n✅ Proxy {'enabled' if self.config.use_proxy else 'disabled'}")
            elif choice == '3':
                if ENHANCED_MODE:
                    self.config.use_auto_login = not self.config.use_auto_login
                    print(f"\n✅ Auto-login {'enabled' if self.config.use_auto_login else 'disabled'}")
                else:
                    print("\n⚠️  Auto-login requires enhanced utilities")
            elif choice == '4':
                self.configure_filters_menu()
            elif choice == '5':
                self.configure_max_tickets()
            elif choice == '6':
                self.config.clear_profiles_on_start = not self.config.clear_profiles_on_start
                print(f"\n✅ Clear profiles on start {'enabled' if self.config.clear_profiles_on_start else 'disabled'}")
            elif choice == '7':
                self.configure_refresh_interval()
            elif choice == '8':
                # Save and apply configuration
                self.config.save()
                self.apply_configuration()
                print("\n✅ Configuration saved!")
                break
            elif choice == '9':
                # Reload original configuration
                self.config = BotConfiguration.load()
                self.apply_configuration()
                print("\n↩️  Changes discarded")
                break
    
    def configure_browsers(self):
        """Configure number of browsers"""
        while True:
            try:
                num = input("\n🌐 Number of browsers (1-5, recommended 2-3): ").strip()
                num = int(num)
                if 1 <= num <= 5:
                    self.config.num_browsers = num
                    print(f"\n✅ Set to {num} browsers")
                    break
                else:
                    print("❌ Please enter 1-5")
            except ValueError:
                print("❌ Invalid number")
    
    def configure_max_tickets(self):
        """Configure maximum tickets to purchase"""
        while True:
            try:
                num = input("\n🎫 Maximum tickets to purchase (1-10): ").strip()
                num = int(num)
                if 1 <= num <= 10:
                    self.config.max_tickets = num
                    print(f"\n✅ Will purchase up to {num} tickets")
                    break
                else:
                    print("❌ Please enter 1-10")
            except ValueError:
                print("❌ Invalid number")
    
    def configure_refresh_interval(self):
        """Configure session refresh interval"""
        while True:
            try:
                minutes = input("\n⏱️  Session refresh interval in minutes (10-60, default 15): ").strip()
                if not minutes:
                    minutes = 15
                else:
                    minutes = int(minutes)
                
                if 10 <= minutes <= 60:
                    self.config.session_refresh_interval = minutes * 60
                    print(f"\n✅ Session will refresh every {minutes} minutes")
                    break
                else:
                    print("❌ Please enter 10-60 minutes")
            except ValueError:
                print("❌ Invalid number")
    
    def configure_filters_menu(self):
        """Enhanced filter configuration"""
        print("\n🎫 TICKET FILTER CONFIGURATION")
        print("="*50)
        print("\n📍 Common sections:")
        print("   • Prato A, Prato B - Field/lawn sections")
        print("   • Parterre - Standing area")
        print("   • Tribuna - Tribune/grandstand seats") 
        print("   • Settore - Sector seating")
        print("\n💡 Examples:")
        print("   • 'Prato A' - Only Prato A tickets")
        print("   • 'Prato' - Any Prato section")
        print("   • 'Tribuna,Settore' - Tribune OR Sector")
        print("\n⚠️  Leave empty to accept ALL tickets")
        
        filter_input = input("\nEnter keywords (comma-separated): ").strip()
        
        if filter_input:
            self.config.ticket_filters = [f.strip() for f in filter_input.split(',') if f.strip()]
            
            if len(self.config.ticket_filters) > 1:
                mode = input("\nMatch ANY keyword or ALL keywords? (any/all, default: any): ").strip().lower()
                self.config.filter_mode = 'all' if mode == 'all' else 'any'
            else:
                self.config.filter_mode = 'any'
            
            print(f"\n✅ Filters configured:")
            print(f"   Keywords: {self.config.ticket_filters}")
            print(f"   Mode: {self.config.filter_mode}")
        else:
            self.config.ticket_filters = []
            print("\n✅ No filters - will accept ALL tickets")
    
    def apply_configuration(self):
        """Apply configuration to bot instance"""
        self.num_browsers = self.config.num_browsers
        self.use_proxy = self.config.use_proxy
        self.use_auto_login = self.config.use_auto_login
        self.max_tickets = self.config.max_tickets
        self.ticket_filters = self.config.ticket_filters
        self.filter_mode = self.config.filter_mode
        self.session_refresh_interval = self.config.session_refresh_interval
    
    def categorize_ticket(self, ticket_text: str):
        """Categorize ticket for statistics"""
        ticket_lower = ticket_text.lower()
        
        if 'prato a' in ticket_lower:
            self.stats['ticket_categories']['prato_a'] += 1
        elif 'prato b' in ticket_lower:
            self.stats['ticket_categories']['prato_b'] += 1
        elif 'settore' in ticket_lower:
            self.stats['ticket_categories']['settore'] += 1
        elif 'tribuna' in ticket_lower:
            self.stats['ticket_categories']['tribuna'] += 1
        else:
            self.stats['ticket_categories']['other'] += 1
    
    def log_stats_dashboard(self):
        """Log statistics in dashboard format like the paste"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        
        total_unique_tickets = sum(self.stats['ticket_categories'].values())
        rate = self.stats['total_checks'] / (elapsed / 60) if elapsed > 60 else 0
        
        dashboard = f"""
════════════════════════════════════════════════════════════
📊 FANSALE BOT STATISTICS DASHBOARD
════════════════════════════════════════════════════════════

⏱️  Total Runtime: {hours}h {minutes}m
🔍 Total Checks: {self.stats['total_checks']:,}
🎫 Unique Tickets Found: {total_unique_tickets}

📈 Ticket Breakdown:
   ● Prato A: {self.stats['ticket_categories']['prato_a']}
   ● Prato B: {self.stats['ticket_categories']['prato_b']}
   ● Settore: {self.stats['ticket_categories']['settore']}
   ● Tribuna: {self.stats['ticket_categories']['tribuna']}
   ○ Other: {self.stats['ticket_categories']['other']}

🛍️  Purchases: {self.stats['successful_checkouts']}
🚫 Already Reserved: {self.stats['already_reserved']}

⚡ Average Rate: {rate:.1f} checks/min

════════════════════════════════════════════════════════════
"""
        logger.info(dashboard)
        
        # Also save to file
        with open('fansale_stats.json', 'w') as f:
            json.dump({
                'runtime_seconds': elapsed,
                'stats': self.stats,
                'config': asdict(self.config),
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
    
    # [Previous methods remain the same - play_alarm, save_stats, get_proxy_config, create_browser, etc.]
    # I'll include the key changes to the existing methods:
    
    def matches_filters(self, driver: uc.Chrome, ticket_element) -> bool:
        """Enhanced filter matching with statistics tracking"""
        if not self.ticket_filters:
            return True
        
        ticket_text = self.get_ticket_text(driver, ticket_element)
        
        if not ticket_text:
            logger.warning("Could not extract text from ticket, skipping...")
            return False
        
        # Track ticket category for statistics
        self.categorize_ticket(ticket_text)
        
        # Log the ticket text for debugging
        logger.debug(f"Ticket text: {ticket_text}")
        
        # Check filters
        if self.filter_mode == 'any':
            for keyword in self.ticket_filters:
                if keyword.lower() in ticket_text:
                    logger.info(f"✓ Ticket matches filter: '{keyword}'")
                    return True
            logger.debug(f"✗ Ticket doesn't match any filter: {self.ticket_filters}")
            return False
        else:
            for keyword in self.ticket_filters:
                if keyword.lower() not in ticket_text:
                    logger.debug(f"✗ Ticket missing required keyword: '{keyword}'")
                    return False
            logger.info(f"✓ Ticket matches all filters: {self.ticket_filters}")
            return True
    
    def run_bot(self):
        """Enhanced bot execution with pre-configured options"""
        # Check if we should clear profiles
        if self.config.clear_profiles_on_start:
            print("\n🧹 Clearing browser profiles as configured...")
            self.clear_browser_profiles()
        
        print(f"\n📋 STARTING WITH CONFIGURATION:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Proxy: {'✅ Yes' if self.use_proxy else '❌ No'}")
        print(f"   • Auto-login: {'✅ Yes' if self.use_auto_login else '❌ No'}")
        print(f"   • Max tickets: {self.max_tickets}")
        
        if self.ticket_filters:
            print(f"   • Filters: {', '.join(self.ticket_filters)} ({self.filter_mode} match)")
        else:
            print(f"   • Filters: None (accepting ALL tickets)")
        
        print(f"   • Target: {self.target_url}")
        print(f"   • Session refresh: Every {self.session_refresh_interval // 60} minutes")
        
        try:
            # Create browsers
            print(f"\n🚀 Starting {self.num_browsers} browsers...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if not driver:
                    logger.error(f"Failed to create browser {i}")
                    continue
                
                if not self.manual_login(i, driver):
                    logger.error(f"Failed to login browser {i}")
                    driver.quit()
                    continue
                
                self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created successfully")
                return
            
            logger.info(f"✅ {len(self.browsers)} browsers ready!")
            input("\n✋ Press Enter to START HUNTING...")
            
            # Start statistics
            self.stats['start_time'] = time.time()
            
            # Start hunter threads
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_and_buy,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                self.browser_threads.append(thread)
            
            # Enhanced stats display thread
            def periodic_stats():
                while not self.shutdown_event.is_set():
                    time.sleep(60)  # Every minute
                    self.log_stats_dashboard()
            
            stats_thread = threading.Thread(target=periodic_stats, daemon=True)
            stats_thread.start()
            
            logger.info("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            # Wait for completion or interrupt
            while self.tickets_secured < self.max_tickets and not self.shutdown_event.is_set():
                time.sleep(1)
            
            if self.tickets_secured >= self.max_tickets:
                logger.info(f"\n🎉 SUCCESS! All {self.max_tickets} tickets secured!")
                self.play_alarm()
                input("\nPress Enter to close browsers and exit...")
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            traceback.print_exc()
        finally:
            # Final stats
            self.log_stats_dashboard()
            
            # Cleanup
            self.shutdown_event.set()
            logger.info("🧹 Cleaning up...")
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
            
            logger.info("✅ Shutdown complete")
    
    def show_main_menu(self):
        """Enhanced main menu"""
        print("\n" + "="*60)
        print("🎫 FANSALE BOT - ENHANCED EDITION")
        print("="*60)
        print("\n1. 🚀 Quick Start (Use Saved Configuration)")
        print("2. ⚙️  Options & Configuration")
        print("3. 🧹 Clear Browser Profiles")
        print("4. 📊 Show Statistics")
        print("5. 🔍 Test Filters (Debug Mode)")
        print("6. 🚪 Exit")
        print("\nEnter your choice (1-6): ", end='')
    
    def run(self):
        """Enhanced main entry point"""
        while True:
            self.show_main_menu()
            
            choice = input().strip()
            
            if choice == '1':
                # Quick start with saved configuration
                self.run_bot()
            elif choice == '2':
                # Options menu
                self.show_options_menu()
            elif choice == '3':
                self.clear_browser_profiles()
            elif choice == '4':
                self.handle_statistics()
            elif choice == '5':
                self.test_filters()
            elif choice == '6':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please try again.")
    
    # Include all the other methods from the original file here
    # (play_alarm, get_ticket_text, hunt_and_buy, execute_purchase, etc.)
    # They remain the same as in the original fansale.py


def main():
    """Entry point"""
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install undetected-chromedriver selenium-wire python-dotenv")
        sys.exit(1)
    
    # Check credentials
    load_dotenv()
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        print("❌ Missing credentials!")
        print("\nCreate a .env file with:")
        print("FANSALE_EMAIL=your@email.com")
        print("FANSALE_PASSWORD=yourpassword")
        print("FANSALE_TARGET_URL=https://www.fansale.it/...")
        sys.exit(1)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()
