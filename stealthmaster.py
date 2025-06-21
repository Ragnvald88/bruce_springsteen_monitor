#!/usr/bin/env python3
"""
StealthMaster - Final Optimized Version
Auto-reserves tickets with auto-relogin
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

load_dotenv()

# Logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/stealthmaster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StealthMaster:
    """Optimized ticket bot with auto-reserve and auto-relogin"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.driver = None
        self.tickets_reserved = 0
        self.max_tickets = 4
        self.checks = 0
        self.logged_in = False
        
        # Stats
        self.stats = {
            'start_time': datetime.now(),
            'checks': 0,
            'tickets_found': 0,
            'tickets_reserved': 0,
            'login_attempts': 0
        }
    
    def create_driver(self):
        """Create optimized driver"""
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Optimize for speed
        options.page_load_strategy = 'eager'
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(20)
        
        # Anti-detection
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return driver
    
    def is_logged_in(self):
        """Check if we're logged in"""
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            return any(x in page_text for x in ['Il mio account', 'Esci', 'Logout', self.email])
        except:
            return False
    
    def login(self):
        """Auto-login when needed"""
        try:
            self.stats['login_attempts'] += 1
            logger.info(f"Login attempt #{self.stats['login_attempts']}")
            
            # Click Accedi link
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
            
            # Fill TicketOne form
            if "ticketone.it" in self.driver.current_url:
                username = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                username.clear()
                username.send_keys(self.email)
                
                password = self.driver.find_element(By.ID, "password")
                password.clear()
                password.send_keys(self.password)
                
                login_btn = self.driver.find_element(By.ID, "loginCustomerButton")
                login_btn.click()
                
                time.sleep(10)
                
                if "fansale.it" in self.driver.current_url:
                    self.logged_in = True
                    logger.info("✅ Login successful!")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def find_and_reserve_tickets(self):
        """Find tickets and auto-reserve them"""
        try:
            # Check login status first
            if not self.is_logged_in():
                logger.info("Not logged in, attempting auto-login...")
                if not self.login():
                    return False
            
            # Find all elements with prices
            ticket_elements = self.driver.execute_script("""
                const tickets = [];
                const elements = document.querySelectorAll('*');
                
                for (let i = 0; i < elements.length; i++) {
                    const elem = elements[i];
                    if (elem.textContent && elem.textContent.includes('€') && 
                        elem.textContent.length > 10 && elem.textContent.length < 500) {
                        tickets.push({
                            index: i,
                            text: elem.textContent.substring(0, 200),
                            hasButton: !!elem.querySelector('button'),
                            hasLink: !!elem.querySelector('a')
                        });
                    }
                }
                return tickets.slice(0, 20);
            """)
            
            if ticket_elements:
                self.stats['tickets_found'] += len(ticket_elements)
                logger.info(f"🎫 Found {len(ticket_elements)} potential tickets")
                
                for ticket in ticket_elements:
                    if self.tickets_reserved >= self.max_tickets:
                        logger.info(f"✅ Reserved {self.max_tickets} tickets - mission complete!")
                        return True
                    
                    # Try to reserve this ticket
                    logger.info(f"Attempting to reserve: {ticket['text'][:80]}...")
                    
                    # Click on the ticket element
                    clicked = self.driver.execute_script(f"""
                        const elements = document.querySelectorAll('*');
                        const elem = elements[{ticket['index']}];
                        if (elem) {{
                            // Try to find clickable element
                            const clickable = elem.querySelector('button, a') || elem;
                            clickable.click();
                            return true;
                        }}
                        return false;
                    """)
                    
                    if clicked:
                        time.sleep(3)
                        
                        # Look for add to cart button
                        added = self.driver.execute_script("""
                            const buttons = document.querySelectorAll('button, input[type="submit"], a');
                            for (const btn of buttons) {
                                const text = (btn.textContent || '').toLowerCase();
                                if (text.includes('aggiungi') || text.includes('carrello') || 
                                    text.includes('add') || text.includes('cart') ||
                                    text.includes('prenota') || text.includes('riserva')) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        
                        if added:
                            time.sleep(2)
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                            if any(word in page_text for word in ['carrello', 'cart', 'aggiunto', 'added']):
                                self.tickets_reserved += 1
                                self.stats['tickets_reserved'] += 1
                                logger.info(f"✅ Ticket #{self.tickets_reserved} reserved!")
                            
                        # Go back if needed
                        if "ticket" not in self.driver.current_url:
                            self.driver.back()
                            time.sleep(2)
            else:
                logger.info("No tickets found on this check")
            
            return False
            
        except Exception as e:
            logger.error(f"Error in ticket check: {e}")
            return False
    
    def print_status(self):
        """Print current status"""
        runtime = str(datetime.now() - self.stats['start_time']).split('.')[0]
        print(f"\r⏱️  Runtime: {runtime} | 🔍 Checks: {self.stats['checks']} | 🎫 Found: {self.stats['tickets_found']} | ✅ Reserved: {self.tickets_reserved}/{self.max_tickets}", end='', flush=True)
    
    def run(self):
        """Main run loop"""
        ticket_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        logger.info("🚀 StealthMaster Starting...")
        logger.info(f"📧 Account: {self.email}")
        logger.info(f"🎯 Target: {self.max_tickets} tickets at ANY price")
        logger.info("🔄 Auto-relogin enabled\n")
        
        try:
            self.driver = self.create_driver()
            self.driver.get(ticket_url)
            time.sleep(5)
            
            # Main loop
            while self.tickets_reserved < self.max_tickets:
                self.stats['checks'] += 1
                self.checks += 1
                
                # Print status
                self.print_status()
                
                # Check and reserve tickets
                if self.find_and_reserve_tickets():
                    break
                
                # Refresh page
                self.driver.refresh()
                time.sleep(5)  # 5 seconds between checks
                
        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopped by user")
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
        finally:
            # Save session data
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "duration": str(datetime.now() - self.stats['start_time']),
                "stats": self.stats,
                "tickets_reserved": self.tickets_reserved
            }
            
            with open(f"logs/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"\n\n📊 Session Summary:")
            logger.info(f"   Duration: {session_data['duration']}")
            logger.info(f"   Checks: {self.stats['checks']}")
            logger.info(f"   Tickets Found: {self.stats['tickets_found']}")
            logger.info(f"   Tickets Reserved: {self.tickets_reserved}")
            logger.info(f"   Login Attempts: {self.stats['login_attempts']}")
            
            if self.driver:
                self.driver.quit()


def main():
    """Main entry point"""
    # Check credentials
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        logger.error("❌ Missing FANSALE_EMAIL or FANSALE_PASSWORD in .env file!")
        return
    
    # Create and run bot
    bot = StealthMaster()
    bot.run()


if __name__ == "__main__":
    main()
