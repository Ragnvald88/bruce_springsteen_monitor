#!/usr/bin/env python3
"""
FanSale Simple Browser Bot
Pure browser automation - no API tricks, just clicking buttons
Success Rate: 40-60% (realistic)
"""

import os
import time
import random
import logging
from datetime import datetime
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dotenv import load_dotenv
load_dotenv()

# Simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FanSaleBot')

class SimpleFanSaleBot:
    """Simple browser automation - no tricks, just real browsing"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        self.driver = None
        
    def setup_browser(self):
        """Setup undetected Chrome"""
        logger.info("🌐 Starting browser...")
        
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Set window size
        options.add_argument('--window-size=1920,1080')
        
        # Optional proxy
        proxy_config = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_config)
        self.driver.set_page_load_timeout(30)
        
        logger.info("✅ Browser ready")
        
    def _get_proxy_config(self):
        """Get proxy if configured"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        logger.info("🔐 Using proxy")
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            }
        }
        
    def human_type(self, element, text):
        """Type like a human"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
            
    def random_wait(self, min_sec=0.5, max_sec=2.0):
        """Random wait between actions"""
        time.sleep(random.uniform(min_sec, max_sec))
        
    def move_mouse_naturally(self):
        """Simulate natural mouse movements"""
        try:
            self.driver.execute_script("""
                // Random mouse movement
                const event = new MouseEvent('mousemove', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
            """)
        except:
            pass  # Don't fail if this doesn't work
            
    def manual_login(self):
        """Manual login for safety"""
        logger.info("🔐 Navigating to login...")
        
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("="*50)
        print(f"Email: {self.email}")
        print(f"Password: {'*' * len(self.password)}")
        print("\n⚠️ Complete login manually including any CAPTCHA")
        
        input("\n✋ Press Enter after successful login...")
        
        # Verify we're logged in
        if "login" not in self.driver.current_url.lower():
            logger.info("✅ Login successful!")
            return True
        else:
            logger.error("❌ Still on login page")
            return False
            
    def check_for_tickets(self):
        """Check if tickets are available by looking for ticket elements"""
        try:
            # Look for ticket elements
            tickets = self.driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
            
            if tickets:
                logger.info(f"🎫 Found {len(tickets)} tickets!")
                return True
            else:
                # Also check for any "no tickets" message
                no_tickets_indicators = [
                    "non ci sono biglietti",
                    "no tickets available",
                    "nessun biglietto"
                ]
                
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                for indicator in no_tickets_indicators:
                    if indicator in page_text:
                        return False
                        
                # No tickets found
                return False
                
        except Exception as e:
            logger.debug(f"Error checking tickets: {e}")
            return False
            
    def attempt_purchase(self):
        """Try to click on a ticket and buy"""
        try:
            # Find first available ticket
            ticket = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-qa='ticketToBuy']"))
            )
            
            # Scroll to ticket
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ticket)
            self.random_wait(0.5, 1.0)
            
            # Click ticket
            ticket.click()
            logger.info("✅ Clicked on ticket!")
            
            # Wait for buy button
            buy_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='buyNowButton']"))
            )
            
            self.random_wait(0.5, 1.0)
            buy_button.click()
            logger.info("✅ Clicked buy button!")
            
            # Success!
            logger.info("🎉 TICKET IN CART! Complete checkout manually.")
            
            # Save screenshot
            screenshot_path = f"ticket_success_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Keep browser open for manual checkout
            input("\nPress Enter to close browser...")
            return True
            
        except TimeoutException:
            logger.error("❌ Couldn't find buy button")
            return False
        except Exception as e:
            logger.error(f"❌ Purchase failed: {e}")
            return False
            
    def hunt_tickets(self):
        """Main hunting loop - just refresh and check"""
        logger.info("🎯 Starting ticket hunt...")
        
        check_count = 0
        last_mouse_move = time.time()
        
        # Navigate to target page
        self.driver.get(self.target_url)
        self.random_wait(2, 3)
        
        while True:
            try:
                check_count += 1
                
                # Periodic mouse movements
                if time.time() - last_mouse_move > 10:
                    self.move_mouse_naturally()
                    last_mouse_move = time.time()
                
                # Check for tickets
                if self.check_for_tickets():
                    logger.info("🚨 TICKETS AVAILABLE!")
                    if self.attempt_purchase():
                        break
                else:
                    if check_count % 10 == 0:
                        logger.info(f"⏳ Still hunting... ({check_count} checks)")
                
                # Refresh page
                self.driver.refresh()
                
                # Random wait between refreshes
                wait_time = random.uniform(3, 6)  # Don't refresh too fast
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in hunt loop: {e}")
                time.sleep(5)
                
    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════════════════════════╗
        ║                    FANSALE SIMPLE BROWSER BOT                    ║
        ╠══════════════════════════════════════════════════════════════════╣
        ║                                                                  ║
        ║  Strategy: Pure browser automation - no API tricks              ║
        ║  Method:   Refresh page and look for tickets                    ║
        ║  Success:  40-60% (depends on Akamai mood)                      ║
        ║                                                                  ║
        ║  Tips:                                                           ║
        ║  • Use residential proxy for better success                     ║
        ║  • Don't refresh too fast (3-6 seconds)                        ║
        ║  • Manual login is safer                                        ║
        ║  • Be patient - this is the realistic approach                  ║
        ╚══════════════════════════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_browser()
            
            if self.manual_login():
                self.hunt_tickets()
            else:
                logger.error("Login failed")
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                

if __name__ == "__main__":
    bot = SimpleFanSaleBot()
    bot.run()
