#!/usr/bin/env python3
"""
Simplified FanSale Bot - Removes overengineering while keeping core functionality
"""

import os
import time
import threading
import random
from pathlib import Path
from datetime import datetime

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from dotenv import load_dotenv

load_dotenv()

class SimpleFanSaleBot:
    """Simplified bot focusing on speed and reliability"""
    
    def __init__(self):
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
            "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
        
        # Simple configuration
        self.num_browsers = 2
        self.max_tickets = 2
        self.ticket_types_to_hunt = set()  # Will be set by user
        
        # State
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.tickets_secured = 0
        self.seen_tickets = set()
        
        # Simple stats
        self.total_checks = 0
        self.tickets_found = 0
        self.start_time = time.time()
        
    def create_browser(self, browser_id):
        """Simple browser creation - let undetected-chromedriver handle the magic"""
        print(f"🚀 Creating Browser {browser_id}...")
        
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Simple window positioning
        x = (browser_id - 1) * 460
        options.add_argument(f'--window-position={x},0')
        options.add_argument('--window-size=450,800')
        
        try:
            # Just use auto-detect - it works 99% of the time
            driver = uc.Chrome(options=options, use_subprocess=True)
            print(f"✅ Browser {browser_id} created")
            return driver
        except Exception as e:
            print(f"❌ Failed to create browser: {e}")
            return None
    
    def dismiss_popup_if_exists(self, driver):
        """Simple popup dismissal - just click common buttons"""
        try:
            # Look for common popup buttons
            buttons = driver.find_elements(By.CSS_SELECTOR, 
                "button.js-BotProtectionModalButton1, button[aria-label*='close'], button[aria-label*='chiudi']")
            
            for btn in buttons:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    return True
                    
            # Special case: "Carica Offerte" button
            carica = driver.find_elements(By.XPATH, "//button[contains(text(), 'Carica Offerte')]")
            if carica and carica[0].is_displayed():
                driver.execute_script("arguments[0].click();", carica[0])
                return True
                
        except:
            pass
        return False
    
    def categorize_ticket(self, text):
        """Simple ticket categorization"""
        text_lower = text.lower()
        if 'prato a' in text_lower:
            return 'prato_a'
        elif 'prato b' in text_lower:
            return 'prato_b'
        elif any(word in text_lower for word in ['settore', 'fila', 'posto']):
            return 'settore'
        return 'other'
    
    def hunt_tickets(self, browser_id, driver):
        """Main hunting loop - simplified for speed"""
        print(f"🎯 Hunter {browser_id} starting...")
        
        # Navigate to page
        driver.get(self.target_url)
        time.sleep(1)
        
        # Dismiss initial popups
        self.dismiss_popup_if_exists(driver)
        
        while not self.shutdown_event.is_set() and self.tickets_secured < self.max_tickets:
            try:
                self.total_checks += 1
                
                # Find tickets
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                for ticket in tickets:
                    ticket_text = ticket.text
                    ticket_hash = hash(ticket_text)  # Simple hash
                    
                    if ticket_hash not in self.seen_tickets:
                        self.seen_tickets.add(ticket_hash)
                        self.tickets_found += 1
                        
                        category = self.categorize_ticket(ticket_text)
                        print(f"🎫 NEW {category.upper()} ticket found!")
                        
                        # If it's a ticket we want, try to buy it
                        if category in self.ticket_types_to_hunt:
                            if self.try_purchase(driver, ticket, browser_id):
                                self.tickets_secured += 1
                                if self.tickets_secured >= self.max_tickets:
                                    return
                
                # Quick refresh every 15 seconds
                if self.total_checks % 15 == 0:
                    driver.refresh()
                    time.sleep(0.5)
                    self.dismiss_popup_if_exists(driver)
                
                # Status update every 30 checks
                if self.total_checks % 30 == 0:
                    elapsed = time.time() - self.start_time
                    rate = self.total_checks / elapsed * 60
                    print(f"📊 Hunter {browser_id}: {self.total_checks} checks @ {rate:.1f}/min")
                
                # Fast checking
                time.sleep(random.uniform(0.3, 0.7))
                
            except WebDriverException:
                print(f"Browser {browser_id} error, refreshing...")
                driver.refresh()
                time.sleep(2)
            except Exception as e:
                print(f"Hunter {browser_id} error: {e}")
                time.sleep(2)
    
    def try_purchase(self, driver, ticket_element, browser_id):
        """Simple purchase attempt"""
        try:
            print(f"⚡ Hunter {browser_id}: Attempting purchase...")
            
            # Click the ticket
            driver.execute_script("arguments[0].click();", ticket_element)
            time.sleep(1)
            
            # Look for buy button
            buy_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='buyNowButton']"))
            )
            
            driver.execute_script("arguments[0].click();", buy_btn)
            print(f"✅ Hunter {browser_id}: Buy button clicked!")
            
            # Check if we navigated to checkout
            time.sleep(2)
            if 'cart' in driver.current_url or 'checkout' in driver.current_url:
                print(f"🎉 Hunter {browser_id}: Reached checkout!")
                print('\a' * 3)  # Alert sound
                return True
            
            # Check for CAPTCHA
            if driver.find_elements(By.CSS_SELECTOR, "div.g-recaptcha, iframe[src*='recaptcha']"):
                print(f"🤖 CAPTCHA detected! Please solve manually.")
                print('\a' * 5)  # Alert sound
                # Wait for manual solve
                time.sleep(30)
                
        except TimeoutException:
            print(f"No buy button found")
        except Exception as e:
            print(f"Purchase failed: {e}")
        
        return False
    
    def configure(self):
        """Simple configuration"""
        print("\n🎫 FANSALE BOT - SIMPLIFIED VERSION")
        print("=" * 40)
        
        # Number of browsers
        num = input("\n🌐 Number of browsers (1-4, default 2): ").strip()
        self.num_browsers = int(num) if num and num.isdigit() else 2
        
        # Max tickets
        max_t = input("🎫 Max tickets (1-4, default 2): ").strip()
        self.max_tickets = int(max_t) if max_t and max_t.isdigit() else 2
        
        # Ticket types
        print("\n🎯 SELECT TICKET TYPES TO HUNT:")
        print("1. Prato A")
        print("2. Prato B")
        print("3. Settore (Seated)")
        print("4. All types")
        
        selection = input("\nEnter choices (e.g., '1,2'): ").strip()
        
        if '4' in selection:
            self.ticket_types_to_hunt = {'prato_a', 'prato_b', 'settore', 'other'}
        else:
            type_map = {'1': 'prato_a', '2': 'prato_b', '3': 'settore'}
            self.ticket_types_to_hunt = {type_map[c] for c in selection.split(',') if c in type_map}
        
        print(f"\n✅ Hunting for: {', '.join(self.ticket_types_to_hunt)}")
        print(f"✅ Browsers: {self.num_browsers}")
        print(f"✅ Max tickets: {self.max_tickets}")
    
    def show_stats(self):
        """Simple stats display"""
        elapsed = time.time() - self.start_time
        runtime = f"{int(elapsed//60)}m {int(elapsed%60)}s"
        rate = self.total_checks / elapsed * 60 if elapsed > 0 else 0
        
        print(f"\n{'='*40}")
        print(f"📊 STATISTICS - Runtime: {runtime}")
        print(f"🔍 Total Checks: {self.total_checks}")
        print(f"⚡ Check Rate: {rate:.1f}/min")
        print(f"🎫 Unique Tickets Found: {self.tickets_found}")
        print(f"🛒 Tickets Secured: {self.tickets_secured}")
        print(f"{'='*40}\n")
    
    def run(self):
        """Run the bot"""
        self.configure()
        
        # Create browsers
        print(f"\n🚀 Starting {self.num_browsers} browser(s)...")
        for i in range(1, self.num_browsers + 1):
            driver = self.create_browser(i)
            if driver:
                self.browsers.append(driver)
        
        if not self.browsers:
            print("❌ No browsers created")
            return
        
        input("\n✋ Press Enter to START HUNTING...")
        
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
        
        try:
            # Show stats every 30 seconds
            while self.tickets_secured < self.max_tickets:
                time.sleep(30)
                self.show_stats()
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
        
        # Cleanup
        self.shutdown_event.set()
        for driver in self.browsers:
            try:
                driver.quit()
            except:
                pass
        
        self.show_stats()
        print("✅ Done!")

if __name__ == "__main__":
    bot = SimpleFanSaleBot()
    bot.run()