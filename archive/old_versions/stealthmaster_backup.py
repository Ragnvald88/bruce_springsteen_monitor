#!/usr/bin/env python3
"""
StealthMaster - Clean and Simple
Just reserves tickets, no bullshit
"""

import sys
import os
import time
import json
import random
import logging
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
from dotenv import load_dotenv

load_dotenv()

# Logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/stealthmaster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StealthMaster:
    """Simple ticket bot that just works"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.driver = None
        self.tickets_reserved = 0
        self.max_tickets = 4
        self.checks = 0
        self.consecutive_failures = 0
        self.delay = 5  # seconds between checks
        self.target_url = None  # Store the URL we want to monitor
        self.logged_in = False  # Track login state to avoid redundant checks
        self.clicked_tickets = set()  # Track clicked tickets to avoid duplicates
    
    def create_driver(self):
        """Create stealth driver"""
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.page_load_strategy = 'eager'
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(20)
        
        # Enhanced stealth - hide webdriver and add fake plugins
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fake plugins array
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override chrome detection
            window.chrome = {
                runtime: {}
            };
            
            // Remove automation indicators
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
            });
        """)
        
        return driver
    
    def accept_cookies(self):
        """Accept cookie popups if they appear"""
        try:
            # Wait a bit for cookie popup to appear
            time.sleep(2)
            
            # OneTrust specific (most common)
            try:
                cookie_btn = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
                if cookie_btn.is_displayed():
                    cookie_btn.click()
                    logger.info("✅ Accepted OneTrust cookies")
                    time.sleep(1)
                    return True
            except:
                pass
            
            # CybotCookiebot (common on Italian sites)
            try:
                cookie_btn = self.driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
                if cookie_btn.is_displayed():
                    cookie_btn.click()
                    logger.info("✅ Accepted Cookiebot cookies")
                    time.sleep(1)
                    return True
            except:
                pass
            
            # Try other common selectors
            cookie_selectors = [
                "button.optanon-allow-all",
                "button#accept-all",
                "button.accept-all",
                ".cookie-consent-accept",
                "button[aria-label*='accetta']",
                "button[aria-label*='accept']",
                ".cc-btn.cc-allow",
                "button.cc-btn.cc-allow-all"
            ]
            
            for selector in cookie_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            elem.click()
                            logger.info(f"✅ Accepted cookies with: {selector}")
                            time.sleep(1)
                            return True
                except:
                    pass
            
            # JavaScript approach - look for visible buttons with cookie-related text
            clicked = self.driver.execute_script("""
                const buttons = document.querySelectorAll('button, a');
                for (const btn of buttons) {
                    const text = (btn.textContent || '').toLowerCase();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    
                    // Check if button is visible
                    const rect = btn.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    
                    // Check for cookie-related text
                    if (text.includes('accetta tutti') || text.includes('accept all') ||
                        text.includes('accetta') || text.includes('accept') ||
                        text.includes('ok') || text.includes('chiudi') ||
                        ariaLabel.includes('accetta') || ariaLabel.includes('accept')) {
                        
                        // Check if it's actually about cookies
                        const parent = btn.closest('[class*="cookie"], [class*="consent"], [id*="cookie"], [id*="consent"], [class*="gdpr"], [id*="gdpr"]');
                        if (parent || text.includes('cookie') || ariaLabel.includes('cookie')) {
                            console.log('Clicking cookie button:', btn);
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            """)
            
            if clicked:
                logger.info("✅ Accepted cookies via JavaScript")
                time.sleep(1)
                return True
                
        except Exception as e:
            logger.debug(f"Cookie handling error: {e}")
        
        return False
    
    def is_logged_in(self):
        """Check if logged in"""
        try:
            # First check URL - if on login page, definitely not logged in
            if "login.htm" in self.driver.current_url:
                return False
            
            # Check for logout/user menu elements that only appear when logged in
            logged_in_found = False
            
            # Look for logout link/button
            try:
                logout_elements = self.driver.find_elements(By.XPATH, 
                    "//a[contains(@href, 'logout')] | //a[contains(text(), 'Esci')] | //a[contains(text(), 'Logout')]")
                if logout_elements and any(elem.is_displayed() for elem in logout_elements):
                    logged_in_found = True
            except:
                pass
            
            # Look for user account menu
            if not logged_in_found:
                try:
                    account_elements = self.driver.find_elements(By.XPATH,
                        "//*[contains(@class, 'user-menu')] | //*[contains(@class, 'account-menu')] | //a[contains(text(), 'Il mio account')]")
                    if account_elements and any(elem.is_displayed() for elem in account_elements):
                        logged_in_found = True
                except:
                    pass
            
            # If we found logged-in indicators, we're logged in
            if logged_in_found:
                return True
            
            # As last check, see if there are NO visible login buttons
            # This is less reliable so only use if we haven't found positive indicators
            try:
                login_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Accedi')]")
                visible_login_buttons = [btn for btn in login_buttons if btn.is_displayed()]
                
                # If no visible login buttons AND we're not on login page, might be logged in
                if not visible_login_buttons and "login.htm" not in self.driver.current_url:
                    # Double-check with page text
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if self.email in page_text or "Il mio account" in page_text:
                        return True
            except:
                pass
                
            return False
        except Exception as e:
            logger.debug(f"Login check error: {e}")
            return False
    
    def login(self):
        """Login to Fansale"""
        try:
            logger.info("Logging in...")
            
            # Check if we're on the login page with iframe
            if "login.htm" in self.driver.current_url:
                logger.info("Already on login page")
                
                # Accept cookies if present
                self.accept_cookies()
                
                # Wait for iframe to load
                time.sleep(3)
                
                # Try to find iframe
                try:
                    iframe = self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='ticketone.it']")
                    logger.info("Found TicketOne iframe, switching to it")
                    self.driver.switch_to.frame(iframe)
                except:
                    logger.info("No iframe found, assuming direct form")
            
            else:
                # Click Accedi to get to login page
                logger.info("Looking for Accedi button...")
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
                
                # Accept cookies if they appeared after navigation
                self.accept_cookies()
                
                # Check if we're now on login page with iframe
                if "login.htm" in self.driver.current_url:
                    try:
                        iframe = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='ticketone.it']"))
                        )
                        logger.info("Switching to TicketOne iframe")
                        self.driver.switch_to.frame(iframe)
                    except:
                        logger.info("No iframe, trying direct form")
            
            # Now fill the form
            logger.info("Looking for username field...")
            username = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username.clear()
            username.send_keys(self.email)
            logger.info("Filled username")
            
            password = self.driver.find_element(By.ID, "password")
            password.clear()
            password.send_keys(self.password)
            logger.info("Filled password")
            
            # Click login button
            login_btn = self.driver.find_element(By.ID, "loginCustomerButton")
            login_btn.click()
            logger.info("Clicked login button")
            
            # Switch back to main content
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            # Wait for login to complete
            time.sleep(10)
            
            # Check if we're logged in
            if "fansale.it" in self.driver.current_url and "login" not in self.driver.current_url:
                logger.info("✅ Login successful!")
                
                # Navigate back to the target URL if we're not on a ticket page
                current_url = self.driver.current_url
                if self.target_url and not ("bruce-springsteen" in current_url and "/tickets/" in current_url):
                    logger.info(f"Navigating to target URL: {self.target_url}")
                    self.driver.get(self.target_url)
                    time.sleep(3)
                
                return True
            else:
                logger.error(f"Login failed, current URL: {self.driver.current_url}")
                return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            # Make sure we're back in default content
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False
    
    def check_if_blocked(self):
        """Check for blocking"""
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            if any(word in body_text for word in ['access denied', 'forbidden', 'captcha', 'rate limit']):
                logger.warning("🚫 Blocked!")
                self.consecutive_failures += 1
                # Increase delay if blocked
                self.delay = min(self.delay * 1.5, 60)
                return True
            return False
        except:
            return False
    
    def find_and_reserve_tickets(self):
        """Find tickets and reserve them"""
        try:
            # Check if blocked
            if self.check_if_blocked():
                return False
                
            # Check login
            current_url = self.driver.current_url
            logged_in = self.is_logged_in()
            
            logger.debug(f"Current URL: {current_url}")
            logger.debug(f"Logged in status: {logged_in}")
            
            if not logged_in:
                logger.info("Not logged in, attempting login...")
                if not self.login():
                    return False
            
            # Wait for page to load tickets
            time.sleep(2)
            
            # Find tickets using multiple strategies
            logger.info("Searching for tickets...")
            
            # Strategy 1: Look for common ticket selectors
            ticket_elements = []
            ticket_selectors = [
                ".offer-item",
                ".ticket-item", 
                "[class*='offer']",
                "[class*='ticket']",
                "[class*='listing']",
                "[data-testid*='ticket']",
                ".listing-item"
            ]
            
            for selector in ticket_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        ticket_elements.extend(elements)
                        break
                except:
                    pass
            
            # Strategy 2: Find elements with prices
            if not ticket_elements:
                ticket_elements = self.driver.execute_script("""
                    const tickets = [];
                    const priceRegex = /€\\s*(\\d+(?:[.,]\\d+)?)/;
                    
                    // Look for elements containing prices
                    const allElements = document.querySelectorAll('div, article, section, li, a');
                    
                    for (const elem of allElements) {
                        const text = elem.textContent || '';
                        
                        // Skip if too long or too short
                        if (text.length < 10 || text.length > 500) continue;
                        
                        // Must contain a price
                        if (!text.includes('€')) continue;
                        
                        // Skip if it's just a price element (likely child of ticket)
                        const children = elem.querySelectorAll('*');
                        if (children.length < 2) continue;
                        
                        // Check if it looks like a ticket listing
                        const hasPrice = priceRegex.test(text);
                        const hasTicketKeywords = /settore|fila|posto|sector|row|seat|block|tribune/i.test(text);
                        
                        if (hasPrice || hasTicketKeywords) {
                            // Check if not sold out
                            if (!elem.classList.contains('sold-out') && !text.toLowerCase().includes('esaurit')) {
                                tickets.push(elem);
                            }
                        }
                    }
                    
                    console.log('Found ' + tickets.length + ' potential ticket elements');
                    return tickets.slice(0, 20);  // Return max 20 tickets
                """)
            
            if ticket_elements:
                logger.info(f"🎫 Found {len(ticket_elements)} potential tickets")
                
                for i, ticket_elem in enumerate(ticket_elements):
                    if self.tickets_reserved >= self.max_tickets:
                        logger.info(f"✅ Reserved {self.max_tickets} tickets - done!")
                        return True
                    
                    try:
                        # Get ticket info
                        ticket_text = ticket_elem.text if hasattr(ticket_elem, 'text') else self.driver.execute_script("return arguments[0].textContent", ticket_elem)
                        logger.info(f"\nChecking ticket {i+1}: {ticket_text[:100]}...")
                        
                        # Try to find clickable element (the ticket itself or a button within)
                        clickable = None
                        
                        # First try to find a button/link within the ticket
                        try:
                            clickable_selectors = [
                                "button",
                                "a[href*='cart']",
                                "a[href*='add']",
                                "[class*='add-to-cart']",
                                "[onclick]"
                            ]
                            
                            for sel in clickable_selectors:
                                try:
                                    btn = ticket_elem.find_element(By.CSS_SELECTOR, sel) if hasattr(ticket_elem, 'find_element') else None
                                    if btn and btn.is_displayed():
                                        clickable = btn
                                        break
                                except:
                                    pass
                        except:
                            pass
                        
                        # If no button found, click the ticket element itself
                        if not clickable:
                            clickable = ticket_elem
                        
                        # Scroll to element
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable)
                        time.sleep(1)
                        
                        # Click the element
                        try:
                            clickable.click()
                        except:
                            # Try JavaScript click
                            self.driver.execute_script("arguments[0].click();", clickable)
                        
                        logger.info("Clicked ticket, waiting for response...")
                        time.sleep(3)
                        
                        # Check if we're on a detail page or if add to cart appeared
                        current_url_after = self.driver.current_url
                        
                        # Look for add to cart button
                        cart_added = False
                        add_selectors = [
                            "button[class*='add-to-cart']",
                            "button[class*='cart']",
                            "button[class*='aggiungi']",
                            "a[class*='add-to-cart']",
                            "//button[contains(text(), 'Aggiungi')]",
                            "//button[contains(text(), 'carrello')]",
                            "//a[contains(text(), 'Aggiungi')]",
                            "//button[contains(text(), 'Add')]",
                            "//button[contains(text(), 'Cart')]"
                        ]
                        
                        for selector in add_selectors:
                            try:
                                if selector.startswith("//"):
                                    # XPath
                                    add_btn = self.driver.find_element(By.XPATH, selector)
                                else:
                                    # CSS
                                    add_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                                
                                if add_btn.is_displayed() and add_btn.is_enabled():
                                    add_btn.click()
                                    cart_added = True
                                    logger.info("Clicked add to cart button")
                                    time.sleep(2)
                                    break
                            except:
                                pass
                        
                        # Check if ticket was added
                        if cart_added:
                            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                            success_keywords = ['carrello', 'cart', 'aggiunto', 'added', 'successo', 'success']
                            
                            if any(keyword in page_text for keyword in success_keywords):
                                self.tickets_reserved += 1
                                logger.info(f"✅ Ticket #{self.tickets_reserved} reserved successfully!")
                                self.consecutive_failures = 0
                                self.delay = max(self.delay * 0.8, 3)
                            else:
                                logger.info("Add to cart clicked but success not confirmed")
                        
                        # Navigate back if we went to a detail page
                        if current_url != current_url_after:
                            self.driver.back()
                            time.sleep(2)
                        
                    except Exception as e:
                        logger.debug(f"Error processing ticket {i+1}: {e}")
                        continue
                        
            else:
                logger.info("No tickets found on this page")
                self.consecutive_failures += 1
            
            return False
            
        except Exception as e:
            logger.error(f"Error finding tickets: {e}")
            return False
    
    def run(self):
        """Main loop"""
        ticket_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        self.target_url = ticket_url  # Store the target URL
        
        logger.info("🚀 StealthMaster Starting (Clean Version)")
        logger.info(f"📧 Account: {self.email}")
        logger.info(f"🎯 Target: {self.max_tickets} tickets at ANY price\n")
        
        try:
            self.driver = self.create_driver()
            self.driver.get(ticket_url)
            time.sleep(3)
            
            # Accept cookies on first load
            self.accept_cookies()
            
            # Main loop
            while self.tickets_reserved < self.max_tickets:
                self.checks += 1
                
                # Status
                print(f"\r🔍 Check #{self.checks} | 🎫 Reserved: {self.tickets_reserved}/{self.max_tickets} | ⏱️ Delay: {self.delay:.0f}s", end='', flush=True)
                
                # Try to reserve
                if self.find_and_reserve_tickets():
                    break
                
                # Wait
                wait_time = self.delay + random.uniform(-1, 1)
                logger.debug(f"Waiting {wait_time:.1f}s before next check...")
                time.sleep(wait_time)
                
                # Only refresh if we're still on the right page
                current_url = self.driver.current_url
                # Check if we're on the correct page (URL might have slight variations)
                if "bruce-springsteen" in current_url and "/tickets/" in current_url:
                    self.driver.refresh()
                else:
                    logger.warning(f"Not on target page! Current: {current_url}")
                    logger.info(f"Navigating back to: {self.target_url}")
                    self.driver.get(self.target_url)
                    time.sleep(3)
                    self.accept_cookies()
                
        except KeyboardInterrupt:
            logger.info("\n⏹️ Stopped")
        finally:
            logger.info(f"\n\n📊 Summary:")
            logger.info(f"   Checks: {self.checks}")
            logger.info(f"   Tickets Reserved: {self.tickets_reserved}")
            
            if self.driver:
                self.driver.quit()


def main():
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        logger.error("❌ Missing credentials in .env!")
        return
    
    bot = StealthMaster()
    bot.run()


if __name__ == "__main__":
    main()