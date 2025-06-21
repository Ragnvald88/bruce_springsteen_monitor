#!/usr/bin/env python3
"""
StealthMaster Simple - Focus on what works
Auto-relogin when logged out
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()

class SimpleStealthMaster:
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.driver = None
        self.logged_in = False
        self.tickets_reserved = 0
        self.max_tickets = 4
        self.checks = 0
        
    def create_driver(self):
        """Create a simple driver without proxy complications"""
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.page_load_strategy = 'eager'  # Don't wait for all resources
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(20)
        return driver
    
    def is_logged_in(self):
        """Check if we're logged in"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            # Look for signs we're logged in
            logged_in_indicators = ['Il mio account', 'My account', 'Esci', 'Logout', self.email]
            return any(indicator in page_text for indicator in logged_in_indicators)
        except:
            return False
    
    def login(self):
        """Simple login process"""
        try:
            print("\n🔐 Logging in...")
            
            # Step 1: Click Accedi link
            links = self.driver.find_elements(By.TAG_NAME, "a")
            clicked = False
            for link in links:
                if "Accedi" in link.text:
                    link.click()
                    clicked = True
                    break
            
            if not clicked:
                # Try JavaScript click
                self.driver.execute_script("""
                    const links = document.querySelectorAll('a');
                    for (const link of links) {
                        if (link.textContent.includes('Accedi')) {
                            link.click();
                            return true;
                        }
                    }
                """)
            
            time.sleep(5)
            
            # Step 2: Fill login form if on TicketOne
            if "ticketone.it" in self.driver.current_url:
                # Username
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                username_field.clear()
                username_field.send_keys(self.email)
                
                # Password
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                password_field.send_keys(self.password)
                
                # Submit
                login_button = self.driver.find_element(By.ID, "loginCustomerButton")
                login_button.click()
                
                # Wait for redirect
                time.sleep(10)
                
                if "fansale.it" in self.driver.current_url:
                    self.logged_in = True
                    print("✅ Login successful!")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def find_and_reserve_tickets(self):
        """Find tickets and try to reserve them"""
        try:
            # First check if we need to login
            if not self.is_logged_in():
                print("📋 Not logged in, attempting login...")
                if not self.login():
                    return
            
            self.checks += 1
            print(f"\n🔍 Check #{self.checks} at {datetime.now().strftime('%H:%M:%S')}")
            
            # Look for tickets - try multiple approaches
            tickets_found = False
            
            # Method 1: Look for price elements (most reliable indicator)
            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
            
            for elem in price_elements:
                try:
                    # Get parent element that might be the ticket container
                    parent = elem.find_element(By.XPATH, "./..")
                    grandparent = parent.find_element(By.XPATH, "./..")
                    
                    # Check if this looks like a ticket listing
                    text = grandparent.text
                    if len(text) > 20 and "€" in text:
                        tickets_found = True
                        print(f"🎫 Found ticket: {text[:100]}...")
                        
                        # Try to click on it or find a button
                        clickable = None
                        
                        # Look for buttons within this element
                        buttons = grandparent.find_elements(By.TAG_NAME, "button")
                        if buttons:
                            clickable = buttons[0]
                        else:
                            # Look for links
                            links = grandparent.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                if link.get_attribute("href") and "ticket" in link.get_attribute("href"):
                                    clickable = link
                                    break
                        
                        if clickable:
                            print("🖱️ Clicking on ticket/button...")
                            clickable.click()
                            time.sleep(3)
                            
                            # Check if we're on a detail page or if something happened
                            current_url = self.driver.current_url
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                            
                            if "carrello" in page_text or "cart" in page_text or "aggiunto" in page_text:
                                self.tickets_reserved += 1
                                print(f"✅ Ticket #{self.tickets_reserved} reserved!")
                                
                                if self.tickets_reserved >= self.max_tickets:
                                    print(f"🎉 Reserved {self.max_tickets} tickets - mission complete!")
                                    return True
                            
                            # Go back if we navigated away
                            if current_url != self.driver.current_url:
                                self.driver.back()
                                time.sleep(2)
                        
                except Exception as e:
                    pass
            
            if not tickets_found:
                print("❌ No tickets found on this check")
            
            return False
            
        except Exception as e:
            print(f"❌ Error during ticket check: {e}")
            return False
    
    def run(self):
        """Main run loop"""
        print("🚀 StealthMaster Simple Starting...")
        print(f"📧 Email: {self.email}")
        print(f"🎯 Will reserve up to {self.max_tickets} tickets at ANY price")
        
        try:
            self.driver = self.create_driver()
            
            # Go to ticket page
            ticket_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
            print(f"\n📍 Going to: {ticket_url}")
            self.driver.get(ticket_url)
            time.sleep(5)
            
            # Main loop
            while self.tickets_reserved < self.max_tickets:
                if self.find_and_reserve_tickets():
                    break
                
                # Refresh page
                print("🔄 Refreshing page...")
                self.driver.refresh()
                time.sleep(5)  # Wait 5 seconds between checks
            
        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
        finally:
            print(f"\n📊 Summary:")
            print(f"   Checks performed: {self.checks}")
            print(f"   Tickets reserved: {self.tickets_reserved}")
            
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    bot = SimpleStealthMaster()
    bot.run()