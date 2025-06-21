#!/usr/bin/env python3
"""
StealthMaster Working Version - Based on actual Fansale structure
"""

import sys
import os
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import pickle

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
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/stealthmaster_working.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WorkingStealthMaster:
    def __init__(self):
        # Credentials from .env
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        # Proxy from .env
        self.proxy_url = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_user = os.getenv('IPROYAL_USERNAME')
            proxy_pass = os.getenv('IPROYAL_PASSWORD')
            proxy_host = os.getenv('IPROYAL_HOSTNAME')
            proxy_port = os.getenv('IPROYAL_PORT')
            if all([proxy_user, proxy_pass, proxy_host, proxy_port]):
                encoded_pass = quote(proxy_pass, safe='')
                self.proxy_url = f"http://{proxy_user}:{encoded_pass}@{proxy_host}:{proxy_port}"
        
        self.driver = None
        self.logged_in = False
        self.tickets_reserved = 0
        self.max_tickets = 4
        
    def create_driver(self):
        """Create optimized driver"""
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Don't use proxy for now - it might be causing issues
        # if self.proxy_url:
        #     options.add_argument(f'--proxy-server={self.proxy_url}')
        #     logger.info(f"Using proxy: {self.proxy_url[:30]}...")
        
        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Page load strategy
        options.page_load_strategy = 'normal'  # Wait for full page load
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # Basic anti-detection
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        logger.info("Driver created successfully")
        return driver
    
    def wait_and_click(self, selector, timeout=10):
        """Wait for element and click it"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except TimeoutException:
            return False
    
    def wait_and_type(self, selector, text, timeout=10):
        """Wait for element and type text"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(text)
            return True
        except TimeoutException:
            return False
    
    def perform_login(self):
        """Perform login to Fansale"""
        try:
            logger.info("Starting login process...")
            
            # Go to Fansale homepage
            logger.info("Step 1: Going to Fansale homepage")
            self.driver.get("https://www.fansale.it")
            time.sleep(3)
            
            # Handle cookies if present
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[class*='cookie']",
                ".cookie-accept",
                "[class*='consent'] button"
            ]
            
            for selector in cookie_selectors:
                if self.wait_and_click(selector, timeout=3):
                    logger.info("Accepted cookies")
                    time.sleep(1)
                    break
            
            # Look for login button - try multiple approaches
            logger.info("Step 2: Looking for login button")
            
            # Method 1: Try clicking by link text
            try:
                login_link = self.driver.find_element(By.LINK_TEXT, "Accedi")
                login_link.click()
                logger.info("Clicked Accedi link")
                time.sleep(5)
            except:
                # Method 2: Try by partial link text
                try:
                    login_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "Accedi")
                    login_link.click()
                    logger.info("Clicked Accedi link (partial)")
                    time.sleep(5)
                except:
                    # Method 3: Try JavaScript
                    clicked = self.driver.execute_script("""
                        const links = document.querySelectorAll('a');
                        for (const link of links) {
                            if (link.textContent.includes('Accedi') || 
                                link.textContent.includes('Login')) {
                                link.click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    
                    if not clicked:
                        logger.error("Could not find login button")
                        return False
                    
                    time.sleep(5)
            
            # Now we should be on TicketOne login page
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Fill username
            logger.info("Step 3: Filling username")
            if not self.wait_and_type("#username", self.email):
                logger.error("Could not find username field")
                return False
            
            # Fill password
            logger.info("Step 4: Filling password")
            if not self.wait_and_type("#password", self.password):
                logger.error("Could not find password field")
                return False
            
            time.sleep(1)
            
            # Click login button
            logger.info("Step 5: Clicking login button")
            if not self.wait_and_click("#loginCustomerButton"):
                # Try alternative selectors
                if not self.wait_and_click("input[value='Accedi']"):
                    logger.error("Could not find login button")
                    return False
            
            # Wait for login to complete
            logger.info("Step 6: Waiting for login to complete...")
            time.sleep(10)  # Give plenty of time for redirect
            
            # Check if logged in
            current_url = self.driver.current_url
            logger.info(f"After login URL: {current_url}")
            
            # Save cookies for future use
            if "fansale.it" in current_url:
                cookies = self.driver.get_cookies()
                with open('logs/fansale_cookies.pkl', 'wb') as f:
                    pickle.dump(cookies, f)
                logger.info("Saved session cookies")
                
                self.logged_in = True
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login failed - not redirected to Fansale")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_for_tickets(self):
        """Check for available tickets"""
        try:
            # Look for ticket elements - we need to discover the actual selectors
            ticket_selectors = [
                ".offer-list-item",
                ".ticket-offer",
                "[class*='offer-item']",
                "[class*='ticket-item']",
                "article",
                ".card",
                "tr[class*='offer']",
                "[data-id]"
            ]
            
            tickets_found = []
            
            for selector in ticket_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        try:
                            text = element.text
                            if text and len(text) > 10:  # Has meaningful content
                                # Look for price
                                price = None
                                if "€" in text:
                                    import re
                                    price_match = re.search(r'€\s*(\d+(?:[.,]\d+)?)', text)
                                    if price_match:
                                        price = float(price_match.group(1).replace(',', '.'))
                                
                                tickets_found.append({
                                    'element': element,
                                    'text': text[:200],
                                    'price': price,
                                    'selector': selector
                                })
                        except:
                            pass
            
            return tickets_found
            
        except Exception as e:
            logger.error(f"Error checking tickets: {e}")
            return []
    
    def reserve_ticket(self, ticket):
        """Attempt to reserve a ticket"""
        try:
            logger.info(f"Attempting to reserve ticket: {ticket['text'][:50]}...")
            
            # Click on the ticket
            ticket['element'].click()
            time.sleep(2)
            
            # Look for add to cart / reserve button
            reserve_selectors = [
                "button[class*='cart']",
                "button[class*='add']",
                "button[class*='reserve']",
                "button[class*='buy']",
                "a[class*='cart']",
                "input[type='submit']",
                "[class*='add-to-cart']"
            ]
            
            for selector in reserve_selectors:
                if self.wait_and_click(selector, timeout=5):
                    logger.info(f"Clicked reserve button: {selector}")
                    time.sleep(3)
                    
                    # Check if added to cart
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if any(word in page_text.lower() for word in ['carrello', 'cart', 'aggiunto', 'added']):
                        self.tickets_reserved += 1
                        logger.info(f"✅ Ticket {self.tickets_reserved} reserved successfully!")
                        return True
                    
            logger.warning("Could not find reserve button")
            return False
            
        except Exception as e:
            logger.error(f"Reserve error: {e}")
            return False
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        check_count = 0
        
        while True:
            try:
                check_count += 1
                logger.info(f"\n--- Check #{check_count} ---")
                
                # Check for tickets
                tickets = self.check_for_tickets()
                
                if tickets:
                    logger.info(f"🎫 Found {len(tickets)} tickets!")
                    
                    # Try to reserve tickets
                    for ticket in tickets:
                        if self.tickets_reserved >= self.max_tickets:
                            logger.info(f"Already reserved {self.max_tickets} tickets, stopping")
                            return
                        
                        if ticket['price']:
                            logger.info(f"Ticket available at €{ticket['price']}")
                        
                        if self.reserve_ticket(ticket):
                            # Go back to ticket list
                            self.driver.back()
                            time.sleep(2)
                        else:
                            # Try to go back anyway
                            try:
                                self.driver.back()
                                time.sleep(2)
                            except:
                                pass
                else:
                    logger.info("No tickets found")
                
                # Refresh page
                self.driver.refresh()
                
                # Wait before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(10)
    
    async def run(self):
        """Main run method"""
        console.print("[bold cyan]StealthMaster Working Version[/bold cyan]\n")
        
        if not self.email or not self.password:
            console.print("[red]No credentials found in .env![/red]")
            return
        
        try:
            # Create driver
            self.driver = self.create_driver()
            
            # Try to load previous session
            cookie_file = Path('logs/fansale_cookies.pkl')
            if cookie_file.exists():
                logger.info("Found previous session cookies")
                self.driver.get("https://www.fansale.it")
                time.sleep(2)
                
                with open(cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except:
                            pass
                
                self.driver.refresh()
                time.sleep(3)
                
                # Check if logged in
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if any(word in page_text for word in ['Il mio account', 'My account', 'Esci', 'Logout']):
                    logger.info("Previous session still valid!")
                    self.logged_in = True
            
            # Login if needed
            if not self.logged_in:
                if not self.perform_login():
                    console.print("[red]Login failed![/red]")
                    return
            
            # Go to ticket page
            ticket_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
            logger.info(f"Navigating to ticket page: {ticket_url}")
            self.driver.get(ticket_url)
            time.sleep(3)
            
            # Start monitoring
            console.print("[green]Starting ticket monitoring...[/green]")
            console.print("[yellow]Will auto-reserve up to 4 tickets at ANY price[/yellow]\n")
            
            await self.monitor_loop()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping...[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
            
            console.print(f"\n[cyan]Summary:[/cyan]")
            console.print(f"  Tickets reserved: {self.tickets_reserved}")


async def main():
    bot = WorkingStealthMaster()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())