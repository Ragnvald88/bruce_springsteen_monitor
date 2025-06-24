#!/usr/bin/env python3
"""
FanSale Bot - Stealth Edition v3.0
Optimized for speed, stealth, and reliability
Fixed all syntax errors and improved detection avoidance
"""

import os
import sys
import time
import random
import logging
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Suppress verbose logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)
logger.handlers.clear()  # Clear any existing handlers

# Add debug handler for more details
debug_handler = logging.FileHandler('debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(debug_handler)

# Console handler
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(handler)


class FanSaleBot:
    """Streamlined FanSale bot with focus on speed and stealth"""
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
        
        # Configuration
        self.num_browsers = 1
        self.use_proxy = False
        self.max_tickets = 4
        self.ticket_filters = []  # Keywords to filter tickets
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()  # Thread safety for purchases
        self.tickets_secured = 0
        
        # Enhanced statistics with ticket type tracking
        self.stats = {
            'checks': 0,
            'tickets_found': 0,
            'tickets_by_type': {
                'prato_a': 0,
                'prato_b': 0,
                'seating': 0,
                'tribuna': 0,
                'parterre': 0,
                'unknown': 0
            },
            'rejected_tickets': [],  # Tickets that didn't meet criteria
            'purchases': 0,
            'start_time': None,
            'last_save': None
        }
        
        # Load existing stats if available
        self.load_stats()

    def load_stats(self):
        """Load statistics from file if exists"""
        stats_file = Path('ticket_stats.json')
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    # Merge with current stats
                    for key in ['tickets_found', 'purchases']:
                        if key in saved_stats:
                            self.stats[key] = saved_stats[key]
                    if 'tickets_by_type' in saved_stats:
                        self.stats['tickets_by_type'].update(saved_stats['tickets_by_type'])
                    logger.info(f"📊 Loaded stats: {self.stats['tickets_found']} tickets found previously")
            except Exception as e:
                logger.debug(f"Failed to load stats: {e}")
    
    def save_stats(self):
        """Save statistics to file"""
        try:
            stats_to_save = {
                'tickets_found': self.stats['tickets_found'],
                'tickets_by_type': self.stats['tickets_by_type'],
                'purchases': self.stats['purchases'],
                'last_save': datetime.now().isoformat(),
                'rejected_tickets': self.stats['rejected_tickets'][-50:]  # Keep last 50 rejected
            }
            with open('ticket_stats.json', 'w') as f:
                json.dump(stats_to_save, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def detect_ticket_type(self, ticket_text: str) -> str:
        """Detect ticket type from text"""
        text_lower = ticket_text.lower()
        
        # Check for specific ticket types
        if 'prato a' in text_lower:
            return 'prato_a'
        elif 'prato b' in text_lower:
            return 'prato_b'
        elif any(word in text_lower for word in ['tribuna', 'tribune']):
            return 'tribuna'
        elif 'parterre' in text_lower:
            return 'parterre'
        elif any(word in text_lower for word in ['settore', 'sector', 'posto', 'seat', 'fila', 'row']):
            return 'seating'
        else:
            return 'unknown'
    
    def get_ticket_info(self, driver: uc.Chrome, ticket_element) -> dict:
        """Extract detailed ticket information"""
        try:
            ticket_text = ""
            price = "N/A"
            
            # Try to get text from ticket element
            try:
                ticket_text = ticket_element.text
            except:
                ticket_text = driver.execute_script("return arguments[0].innerText || arguments[0].textContent || ''", ticket_element)
            
            # Try to find price
            try:
                price_elem = ticket_element.find_element(By.CSS_SELECTOR, "[class*='price'], [class*='prezzo'], [class*='euro']")
                price = price_elem.text
            except:
                pass
            
            # Detect type
            ticket_type = self.detect_ticket_type(ticket_text)
            
            return {
                'text': ticket_text[:100],  # First 100 chars
                'type': ticket_type,
                'price': price,
                'time': datetime.now().strftime('%H:%M:%S')
            }
            
        except Exception as e:
            logger.debug(f"Error extracting ticket info: {e}")
            return {'text': 'Unknown', 'type': 'unknown', 'price': 'N/A', 'time': datetime.now().strftime('%H:%M:%S')}
    
    def matches_filters(self, ticket_info: dict) -> bool:
        """Check if ticket matches configured filters"""
        if not self.ticket_filters:
            return True
            
        ticket_text = ticket_info['text'].lower()
        return any(filter_keyword.lower() in ticket_text for filter_keyword in self.ticket_filters)

    def create_browser(self, browser_id: int) -> Optional[uc.Chrome]:
        """Create stealth browser instance"""
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
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Window size and position
        positions = [(0, 0), (450, 0), (900, 0)]
        x, y = positions[browser_id - 1] if browser_id <= 3 else (0, 0)
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=450,700')
        
        # Profile persistence
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
                console.log('Stealth mode active');
            """)
            
            logger.info(f"✅ Browser {browser_id} ready")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser: {e}")
            return None

    def verify_login(self, driver: uc.Chrome) -> bool:
        """Check if browser is logged in - PROPERLY FIXED"""
        try:
            page_source = driver.page_source.lower()
            
            # First check if we're on a login page
            if 'login' in driver.current_url or '/login.htm' in driver.current_url:
                return False
            
            # Look for login button/link that indicates NOT logged in
            not_logged_indicators = [
                'accedi per acquistare',  # Login to purchase
                'effettua il login',      # Please login
                'registrati/accedi',       # Register/Login
                '>login<',                 # Login button
                '>accedi<'                 # Login button in Italian
            ]
            
            # If we find these, we're NOT logged in
            if any(indicator in page_source for indicator in not_logged_indicators):
                return False
            
            # Positive indicators of being logged in
            logged_in_indicators = [
                'il mio fansale',
                'my fansale', 
                'mio account',
                'logout',
                'esci',
                'ciao,'  # Hello, username
            ]
            
            # If we find these, we ARE logged in
            if any(indicator in page_source for indicator in logged_in_indicators):
                return True
                
            # Default to not logged in to be safe
            return False
            
        except Exception as e:
            logger.debug(f"Login check error: {e}")
            return False
    
    def manual_login(self, browser_id: int, driver: uc.Chrome) -> bool:
        """Handle manual login process"""
        logger.info(f"🔐 Checking login status for Browser {browser_id}...")
        
        try:
            # Navigate to target page first
            driver.get(self.target_url)
            time.sleep(3)
            
            # Debug: Show what we see on the page
            page_title = driver.title
            logger.info(f"Page title: {page_title}")
            
            # Check if already logged in
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} already logged in!")
                return True
            
            # Check if we see any login prompts
            page_source = driver.page_source.lower()
            if 'accedi per' in page_source or 'effettua il login' in page_source:
                logger.info(f"⚠️ Browser {browser_id}: Login required - found login prompt")
            
            # Need to login
            logger.info(f"📝 Login required for Browser {browser_id}")
            driver.get("https://www.fansale.it/fansale/login.htm")
            
            print(f"\n{'='*60}")
            print(f"🔐 MANUAL LOGIN REQUIRED - Browser #{browser_id}")
            print(f"{'='*60}")
            print(f"Please log in manually in the browser window")
            print(f"Email: {self.email}")
            print(f"{'='*60}\n")
            
            input(f"✋ Press Enter after you've logged in...")
            
            # Navigate back and verify
            driver.get(self.target_url)
            time.sleep(3)
            
            if self.verify_login(driver):
                logger.info(f"✅ Browser {browser_id} logged in successfully!")
                return True
            else:
                logger.error(f"❌ Browser {browser_id} login failed - still seeing login prompts")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop - optimized for speed with enhanced logging"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        check_count = 0
        last_refresh = time.time()
        last_stats_save = time.time()
        no_ticket_count = 0
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                check_count += 1
                self.stats['checks'] += 1
                
                # Periodic login check every 5 minutes
                if check_count % 100 == 0:
                    if not self.verify_login(driver):
                        logger.warning(f"⚠️ Hunter {browser_id}: Re-login needed")
                        if not self.manual_login(browser_id, driver):
                            break
                
                # Quick ticket check
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🎫 HUNTER {browser_id}: {len(tickets)} TICKETS SPOTTED!")
                    
                    tickets_to_buy = []
                    
                    for i, ticket in enumerate(tickets):
                        ticket_info = self.get_ticket_info(driver, ticket)
                        ticket_type = ticket_info['type']
                        
                        # Update statistics
                        self.stats['tickets_found'] += 1
                        self.stats['tickets_by_type'][ticket_type] += 1
                        
                        # Log ticket details
                        type_emoji = {
                            'prato_a': '🌱A',
                            'prato_b': '🌱B', 
                            'seating': '💺',
                            'tribuna': '🏛️',
                            'parterre': '🎭',
                            'unknown': '❓'
                        }.get(ticket_type, '❓')
                        
                        logger.info(f"  #{i+1} {type_emoji} {ticket_type.upper()}: {ticket_info['text'][:50]}... | {ticket_info['price']}")
                        
                        # Check if matches filters
                        if self.matches_filters(ticket_info):
                            tickets_to_buy.append((ticket, ticket_info))
                            logger.info(f"     ✅ Matches criteria!")
                        else:
                            logger.info(f"     ❌ Doesn't match criteria")
                            self.stats['rejected_tickets'].append(ticket_info)
                    
                    logger.info(f"{'='*60}\n")
                    
                    # Try to buy matching tickets
                    for ticket, ticket_info in tickets_to_buy[:self.max_tickets - self.tickets_secured]:
                        with self.purchase_lock:  # Thread safety
                            if self.tickets_secured >= self.max_tickets:
                                break
                            if self.purchase_ticket(driver, ticket, browser_id):
                                self.tickets_secured += 1
                                self.stats['purchases'] += 1
                                logger.info(f"🎉 PURCHASED: {ticket_info['type']} ticket!")
                                
                                if self.tickets_secured >= self.max_tickets:
                                    logger.info(f"🎉 Max tickets secured!")
                                    return
                else:
                    no_ticket_count += 1
                    # Log every 10 checks when no tickets
                    if no_ticket_count % 10 == 0:
                        logger.info(f"Hunter {browser_id}: No tickets (checked {check_count} times)")
                
                # Save stats every 30 seconds
                if time.time() - last_stats_save > 30:
                    self.save_stats()
                    last_stats_save = time.time()
                
                # Smart refresh with jitter
                refresh_time = random.uniform(2.5, 3.5)
                
                # Full page refresh every 30 seconds to avoid stale elements
                if time.time() - last_refresh > 30:
                    logger.debug(f"Hunter {browser_id}: Refreshing page...")
                    driver.refresh()
                    last_refresh = time.time()
                else:
                    # Just wait and re-check
                    time.sleep(refresh_time)
                
                # Log progress with ticket type breakdown
                if check_count % 50 == 0:
                    rate = (check_count * 60) / (time.time() - self.stats['start_time'])
                    logger.info(f"\n📊 Hunter {browser_id} Progress:")
                    logger.info(f"   Checks: {check_count} @ {rate:.1f}/min")
                    logger.info(f"   Total tickets seen: {self.stats['tickets_found']}")
                    logger.info(f"   By type: " + ", ".join([f"{k}: {v}" for k, v in self.stats['tickets_by_type'].items() if v > 0]))
                    logger.info("")
                    
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
            
            # Click ticket
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
                    
                    # Play alarm
                    print('\a' * 3)  # System beep
                    
                    # Take screenshot
                    driver.save_screenshot(f"ticket_{int(time.time())}.png")
                    
                    return True
                    
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.debug(f"Purchase failed: {e}")
            return False

    def configure(self):
        """Configure bot settings"""
        print("\n🔧 BOT CONFIGURATION")
        print("="*40)
        
        # Number of browsers
        while True:
            try:
                num = input("\n🌐 Number of browsers (1-3, default 1): ").strip()
                if not num:
                    self.num_browsers = 1
                    break
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 3:
                    break
                print("❌ Please enter 1-3")
            except ValueError:
                print("❌ Invalid number")
        
        # Proxy
        proxy = input("\n🔐 Use proxy? (y/n, default n): ").strip().lower()
        self.use_proxy = proxy == 'y'
        
        # Max tickets
        try:
            max_t = input("\n🎫 Max tickets to buy (1-4, default 4): ").strip()
            if max_t:
                self.max_tickets = min(4, max(1, int(max_t)))
        except:
            pass
        
        # Ticket filters
        print("\n🎯 TICKET FILTERING (optional)")
        print("Common types: prato a, prato b, tribuna, parterre, settore")
        filter_input = input("Enter keywords to filter (comma-separated, or press Enter for all): ").strip()
        if filter_input:
            self.ticket_filters = [f.strip() for f in filter_input.split(',') if f.strip()]
            print(f"✅ Will only buy tickets matching: {self.ticket_filters}")
        else:
            print("✅ Will consider all ticket types")
        
        print(f"\n📋 Configuration:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Proxy: {'Yes' if self.use_proxy else 'No'}")
        print(f"   • Max tickets: {self.max_tickets}")
        print(f"   • Filters: {self.ticket_filters if self.ticket_filters else 'None (all types)'}")
        print(f"   • Target: {self.target_url}")
    
    def run(self):
        """Main execution"""
        try:
            # Configure
            self.configure()
            
            # Create browsers
            print(f"\n🚀 Starting {self.num_browsers} browsers...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if not driver:
                    continue
                    
                if not self.manual_login(i, driver):
                    driver.quit()
                    continue
                    
                self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created")
                return

            logger.info(f"✅ {len(self.browsers)} browsers ready!")
            input("\n✋ Press Enter to START HUNTING...")
            
            # Start hunting
            self.stats['start_time'] = time.time()
            threads = []
            
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_tickets,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
            
            # Monitor progress with periodic updates
            print("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            try:
                last_update = time.time()
                while self.tickets_secured < self.max_tickets:
                    time.sleep(1)
                    
                    # Show status every 30 seconds
                    if time.time() - last_update > 30:
                        self.save_stats()  # Save current stats
                        elapsed = time.time() - self.stats['start_time']
                        rate = self.stats['checks'] / (elapsed / 60) if elapsed > 0 else 0
                        
                        print(f"
📊 Status Update at {datetime.now().strftime('%H:%M:%S')}:")
                        print(f"   • Total checks: {self.stats['checks']}")
                        print(f"   • Check rate: {rate:.1f}/min")
                        print(f"   • Total tickets spotted: {self.stats['tickets_found']}")
                        
                        # Show ticket type breakdown
                        type_breakdown = []
                        for t_type, count in self.stats['tickets_by_type'].items():
                            if count > 0:
                                type_breakdown.append(f"{t_type}: {count}")
                        if type_breakdown:
                            print(f"   • By type: {', '.join(type_breakdown)}")
                        
                        print(f"   • Rejected (no match): {len(self.stats['rejected_tickets'])}")
                        print(f"   • Active browsers: {len([t for t in threads if t.is_alive()])}")
                        last_update = time.time()
                    
                logger.info(f"\n🎉 SUCCESS! {self.tickets_secured} tickets secured!")
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping...")
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            
        finally:
            # Cleanup
            self.shutdown_event.set()
            
            for driver in self.browsers:
                try:
                    driver.quit()
                except:
                    pass
                    
            # Save and show final stats
            self.save_stats()
            
            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                print(f"
{'='*60}")
                print(f"📊 FINAL STATISTICS")
                print(f"{'='*60}")
                print(f"   • Runtime: {elapsed/60:.1f} minutes")
                print(f"   • Total checks: {self.stats['checks']}")
                print(f"   • Check rate: {self.stats['checks']/(elapsed/60):.1f}/min")
                print(f"   • Tickets found: {self.stats['tickets_found']}")
                print(f"   • Purchases: {self.stats['purchases']}")
                
                print(f"
📈 Ticket Type Breakdown:")
                for t_type, count in sorted(self.stats['tickets_by_type'].items()):
                    if count > 0:
                        percentage = (count / self.stats['tickets_found'] * 100) if self.stats['tickets_found'] > 0 else 0
                        print(f"   • {t_type.upper()}: {count} ({percentage:.1f}%)")
                
                if self.stats['rejected_tickets']:
                    print(f"
❌ Rejected {len(self.stats['rejected_tickets'])} tickets that didn't match criteria")
                
                print(f"
💾 Stats saved to ticket_stats.json")
                print(f"{'='*60}")


def main():
    """Entry point"""
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium")
        sys.exit(1)
    
    # Check credentials
    load_dotenv()
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        print("❌ Missing credentials in .env file!")
        sys.exit(1)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()
