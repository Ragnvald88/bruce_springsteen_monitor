#!/usr/bin/env python3
"""
FanSale Bot - No Login Required Edition
Based on user discovery that tickets can be reserved without authentication
"""

import os
import sys
import time
import random
import logging
import threading
import json
from datetime import datetime
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
logger.handlers.clear()

# Console handler
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(handler)

# File handler
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(file_handler)


class FanSaleBot:
    """Streamlined FanSale bot - No login required"""
    
    def __init__(self):
        # Get target URL from env or use default
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554")
        
        # Configuration
        self.num_browsers = 1
        self.ticket_filters = []
        self.filter_mode = 'any'  # 'any' or 'all'
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.found_tickets = set()  # Track unique tickets to avoid duplicates
        self.in_checkout = {}  # Track checkout state per browser {browser_id: bool}
        self.stats = {
            'checks': 0,
            'tickets_found': 0,
            'tickets_matching_filter': 0,
            'purchase_attempts': 0,
            'successful_purchases': 0,
            'start_time': None,
            'blocks_encountered': 0
        }

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
        
        # Window positioning
        positions = [(0, 0), (450, 0), (900, 0)]
        x, y = positions[browser_id - 1] if browser_id <= 3 else (0, 0)
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=450,700')
        
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
            """)
            
            logger.info(f"✅ Browser {browser_id} ready")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser: {e}")
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
            """)
            
            # Navigate to blank page
            driver.get("about:blank")
            time.sleep(1)
            
            logger.info(f"✅ Browser {browser_id} data cleared")
            self.stats['blocks_encountered'] += 1
            
        except Exception as e:
            logger.error(f"Failed to clear browser data: {e}")

    def get_ticket_info(self, ticket_element) -> str:
        """Extract ticket information for filtering"""
        try:
            ticket_text = ticket_element.text.lower()
            
            # Try to get more detailed info if available
            details = ticket_element.find_elements(By.CSS_SELECTOR, "span, div, p")
            for detail in details:
                text = detail.text.strip()
                if text:
                    ticket_text += " " + text.lower()
                    
            return ticket_text
        except:
            return ""
    
    def get_ticket_id(self, ticket_element) -> str:
        """Generate unique ID for a ticket based on its content and attributes"""
        try:
            # Collect unique identifiers
            id_parts = []
            
            # Try to get data attributes
            for attr in ['data-id', 'data-ticket-id', 'id']:
                attr_value = ticket_element.get_attribute(attr)
                if attr_value:
                    id_parts.append(attr_value)
            
            # Get text content (section, row, price, etc.)
            ticket_text = ticket_element.text.replace('\n', ' ').strip()
            if ticket_text:
                # Extract key info like section, row, seat, price
                id_parts.append(ticket_text)
            
            # If no unique identifiers found, use element location
            if not id_parts:
                location = ticket_element.location
                id_parts.append(f"{location.get('x', 0)}_{location.get('y', 0)}")
            
            # Create hash of all parts
            ticket_id = "_".join(str(part) for part in id_parts)
            return ticket_id
        except:
            # Fallback to random ID
            return f"ticket_{time.time()}_{random.randint(1000, 9999)}"

    def matches_filter(self, ticket_text: str) -> bool:
        """Check if ticket matches our filters"""
        if not self.ticket_filters:
            return True  # No filters = accept all
            
        ticket_text = ticket_text.lower()
        
        if self.filter_mode == 'any':
            # Match if ANY keyword is found
            for keyword in self.ticket_filters:
                if keyword.lower() in ticket_text:
                    return True
            return False
        else:
            # Match if ALL keywords are found
            for keyword in self.ticket_filters:
                if keyword.lower() not in ticket_text:
                    return False
            return True
    
    def is_in_checkout(self, driver: uc.Chrome) -> bool:
        """Check if we're in the checkout process"""
        try:
            # Check URL for checkout indicators
            current_url = driver.current_url.lower()
            checkout_indicators = ['checkout', 'payment', 'review', 'confirm', 'acquisto', 'pagamento']
            
            for indicator in checkout_indicators:
                if indicator in current_url:
                    return True
            
            # Check page content for checkout elements
            checkout_selectors = [
                "div[class*='checkout']",
                "div[class*='payment']",
                "form[class*='payment']",
                "div[class*='review-order']",
                "button[class*='confirm']",
                "h1:contains('Checkout')",
                "h1:contains('Pagamento')",
                "h2:contains('Riepilogo ordine')"
            ]
            
            for selector in checkout_selectors:
                try:
                    if driver.find_elements(By.CSS_SELECTOR, selector):
                        return True
                except:
                    pass
            
            # Check if ticket is reserved/in cart
            reserved_indicators = [
                "div[class*='reserved']",
                "div[class*='cart']",
                "span:contains('riservato')",
                "span:contains('reserved')"
            ]
            
            for selector in reserved_indicators:
                try:
                    if driver.find_elements(By.CSS_SELECTOR, selector):
                        return True
                except:
                    pass
                    
            return False
        except:
            return False
    def hunt_tickets(self, browser_id: int, driver: uc.Chrome):
        """Main hunting loop - NO LOGIN REQUIRED"""
        logger.info(f"🎯 Hunter {browser_id} starting...")
        
        # Initialize checkout state for this browser
        self.in_checkout[browser_id] = False
        
        # Navigate directly to event page
        logger.info(f"📍 Navigating to: {self.target_url}")
        driver.get(self.target_url)
        time.sleep(3)
        
        check_count = 0
        last_refresh = time.time()
        last_session_refresh = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                check_count += 1
                self.stats['checks'] += 1
                
                # Check and update checkout state
                if self.is_in_checkout(driver):
                    if not self.in_checkout.get(browser_id, False):
                        logger.info(f"🛒 Hunter {browser_id}: Entered checkout! Pausing refreshes...")
                        self.in_checkout[browser_id] = True
                    time.sleep(5)
                    continue
                else:
                    if self.in_checkout.get(browser_id, False):
                        logger.info(f"📍 Hunter {browser_id}: Left checkout, resuming normal operation...")
                        self.in_checkout[browser_id] = False
                
                # Check for 404 blocks
                if self.is_blocked(driver):
                    logger.warning(f"⚠️ Hunter {browser_id}: 404 block detected!")
                    self.clear_browser_data(driver, browser_id)
                    driver.get(self.target_url)
                    time.sleep(3)
                    continue
                
                # Session refresh every 15 minutes to prevent blocks
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
                    # Track new unique tickets
                    new_tickets_found = False
                    unique_tickets_this_check = []
                    
                    for ticket in tickets:
                        ticket_id = self.get_ticket_id(ticket)
                        if ticket_id not in self.found_tickets:
                            self.found_tickets.add(ticket_id)
                            unique_tickets_this_check.append(ticket)
                            new_tickets_found = True
                            self.stats['tickets_found'] += 1
                    
                    if new_tickets_found:
                        logger.info(f"🎫 HUNTER {browser_id}: {len(unique_tickets_this_check)} NEW tickets found!")
                        
                        # Filter tickets if filters are set
                        matching_tickets = []
                        for ticket in unique_tickets_this_check:
                            ticket_info = self.get_ticket_info(ticket)
                            if self.matches_filter(ticket_info):
                                matching_tickets.append(ticket)
                                logger.info(f"✅ NEW ticket matches filter: {ticket_info[:50]}...")
                                self.stats['tickets_matching_filter'] += 1
                            else:
                                logger.debug(f"❌ NEW ticket doesn't match: {ticket_info[:50]}...")
                        
                        if matching_tickets:
                            logger.info(f"🎯 {len(matching_tickets)} NEW tickets match your filters!")
                            
                            # Try to select up to 4 tickets at once
                            tickets_to_select = matching_tickets[:4]
                            logger.info(f"🎟️ Attempting to select {len(tickets_to_select)} ticket(s)...")
                            
                            with self.purchase_lock:
                                if self.attempt_multi_ticket_purchase(driver, tickets_to_select, browser_id):
                                    self.stats['successful_purchases'] += 1
                                    logger.info(f"🎉 Successfully initiated purchase for {len(tickets_to_select)} ticket(s)!")
                                else:
                                    logger.warning(f"❌ Failed to purchase tickets, will keep hunting...")
                        else:
                            logger.info(f"⚠️ Found {len(unique_tickets_this_check)} NEW tickets but none match filters")
                    else:
                        logger.debug(f"Hunter {browser_id}: {len(tickets)} tickets visible (all previously seen)")
                        
                # Smart refresh
                refresh_time = random.uniform(2.5, 3.5)
                
                # Full page refresh every 30 seconds
                if time.time() - last_refresh > 30:
                    driver.refresh()
                    last_refresh = time.time()
                else:
                    time.sleep(refresh_time)
                
                # Progress update
                if check_count % 50 == 0:
                    elapsed = time.time() - self.stats['start_time']
                    rate = (check_count * 60) / elapsed if elapsed > 0 else 0
                    logger.info(f"📊 Hunter {browser_id}: {check_count} checks @ {rate:.1f}/min")
                    
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

    def attempt_multi_ticket_purchase(self, driver: uc.Chrome, tickets: list, browser_id: int) -> bool:
        """Attempt to select and purchase multiple tickets (up to 4)"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Attempting to select {len(tickets)} ticket(s)...")
            self.stats['purchase_attempts'] += 1
            
            # Click all tickets to select them
            for i, ticket in enumerate(tickets):
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket)
                    driver.execute_script("arguments[0].click();", ticket)
                    logger.info(f"✓ Selected ticket {i+1}/{len(tickets)}")
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Failed to select ticket {i+1}: {e}")
            
            # Wait a moment for selection to register
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
                        buy_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    driver.execute_script("arguments[0].click();", buy_btn)
                    logger.info(f"✅ Hunter {browser_id}: Buy button clicked for {len(tickets)} ticket(s)!")
                    
                    # Mark browser as in checkout
                    self.in_checkout[browser_id] = True
                    
                    # Play alarm sound
                    print('\a' * 3)  # System beep
                    
                    # Take screenshot
                    screenshot_path = f"screenshots/purchase_{int(time.time())}.png"
                    Path("screenshots").mkdir(exist_ok=True)
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                    
                    return True
                    
                except:
                    continue
                    
            logger.warning(f"Hunter {browser_id}: Couldn't find buy button after selecting tickets")
            return False
            
        except Exception as e:
            logger.error(f"Multi-ticket purchase failed: {e}")
            return False

    def configure_filters(self):
        """Configure ticket filtering"""
        print("\n🎫 TICKET FILTERING (Optional)")
        print("="*50)
        print("\nCommon Italian venue sections:")
        print("  • Prato - Lawn/standing area (e.g., 'Prato A', 'Prato B')")
        print("  • Tribuna - Tribune/stands")
        print("  • Parterre - Floor/pit area")
        print("  • Settore - Sector (e.g., 'Settore 1', 'Settore 2')")
        print("  • Numerato - Numbered seats")
        print("\nExamples:")
        print("  - Enter 'Prato A' to only get Prato A tickets")
        print("  - Enter 'Tribuna, Gold' to get Tribuna OR Gold tickets")
        print("  - Leave empty to accept ALL tickets")
        
        filter_input = input("\n🔍 Enter keywords (comma-separated) or press Enter for ALL: ").strip()
        
        if filter_input:
            self.ticket_filters = [f.strip() for f in filter_input.split(',') if f.strip()]
            
            if len(self.ticket_filters) > 1:
                print("\n🤔 Multiple keywords detected!")
                print("  1. ANY - Accept tickets with ANY of these keywords (default)")
                print("  2. ALL - Only accept tickets with ALL keywords")
                mode_choice = input("\nChoose mode (1 or 2, default 1): ").strip()
                self.filter_mode = 'all' if mode_choice == '2' else 'any'
            
            print(f"\n✅ Filters configured:")
            print(f"   • Keywords: {', '.join(self.ticket_filters)}")
            print(f"   • Mode: {self.filter_mode.upper()}")
            print(f"   • Will {'accept tickets with ANY' if self.filter_mode == 'any' else 'ONLY accept tickets with ALL'} keyword(s)")
        else:
            print("\n✅ No filters - will accept ALL available tickets")

    def configure(self):
        """Configure bot settings"""
        print("\n🤖 FANSALE BOT CONFIGURATION (No Login Required!)")
        print("="*50)
        
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
        
        # Configure filters
        self.configure_filters()
        
        # Summary
        print(f"\n📋 Configuration Summary:")
        print(f"   • Browsers: {self.num_browsers}")
        print(f"   • Ticket selection: Up to 4 tickets per attempt")
        print(f"   • Filters: {', '.join(self.ticket_filters) if self.ticket_filters else 'None (accept all)'}")
        print(f"   • Target URL: {self.target_url[:50]}...")
        print(f"\n⚡ NO LOGIN REQUIRED - Going directly to event page!")
        print(f"⚠️  Bot will run continuously until you stop it with Ctrl+C")
    
    def run(self):
        """Main execution - NO LOGIN REQUIRED"""
        try:
            # Configure
            self.configure()
            
            # Create browsers
            print(f"\n🚀 Starting {self.num_browsers} browser(s)...")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_browser(i)
                if driver:
                    self.browsers.append(driver)
            
            if not self.browsers:
                logger.error("❌ No browsers created")
                return

            logger.info(f"✅ {len(self.browsers)} browser(s) ready!")
            input("\n✋ Press Enter to START HUNTING (no login required)...")
            
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
            
            # Monitor progress
            print("\n🎯 HUNTING ACTIVE! Press Ctrl+C to stop.\n")
            
            try:
                last_update = time.time()
                while True:  # Run forever until Ctrl+C
                    time.sleep(1)
                    
                    # Status update every 30 seconds
                    if time.time() - last_update > 30:
                        elapsed = time.time() - self.stats['start_time']
                        rate = self.stats['checks'] / (elapsed / 60) if elapsed > 0 else 0
                        
                        print(f"\n📊 Status Update:")
                        print(f"   • Total checks: {self.stats['checks']}")
                        print(f"   • Check rate: {rate:.1f}/min")
                        print(f"   • Tickets found: {self.stats['tickets_found']}")
                        print(f"   • Matching filters: {self.stats['tickets_matching_filter']}")
                        print(f"   • Purchase attempts: {self.stats['purchase_attempts']}")
                        print(f"   • Successful purchases: {self.stats['successful_purchases']}")
                        print(f"   • 404 blocks cleared: {self.stats['blocks_encountered']}")
                        print(f"   • Active browsers: {len([t for t in threads if t.is_alive()])}")
                        last_update = time.time()
                    
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
                    
            # Show final stats
            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                print(f"\n📊 Final Statistics:")
                print(f"   • Total checks: {self.stats['checks']}")
                print(f"   • Tickets found: {self.stats['tickets_found']}")
                print(f"   • Matching filters: {self.stats['tickets_matching_filter']}")
                print(f"   • Purchase attempts: {self.stats['purchase_attempts']}")
                print(f"   • Successful purchases: {self.stats['successful_purchases']}")
                print(f"   • 404 blocks cleared: {self.stats['blocks_encountered']}")
                print(f"   • Runtime: {elapsed/60:.1f} minutes")
                print(f"   • Check rate: {self.stats['checks']/(elapsed/60):.1f}/min")


def main():
    """Entry point"""
    print("="*60)
    print("🎫 FANSALE BOT - NO LOGIN REQUIRED EDITION")
    print("="*60)
    print("\n✨ Based on discovery that tickets can be reserved without login!")
    
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("Run: pip install undetected-chromedriver python-dotenv selenium")
        sys.exit(1)
    
    # Load environment
    load_dotenv()
    
    # Check for target URL
    if not os.getenv('FANSALE_TARGET_URL'):
        print("\n⚠️  No target URL in .env file")
        print("Using default Bruce Springsteen URL")
        print("To change, add to .env file:")
        print("FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/...")
        time.sleep(2)
    
    # Run bot
    bot = FanSaleBot()
    bot.run()


if __name__ == "__main__":
    main()