#!/usr/bin/env python3
"""
Simplified Fansale Bot - Focus on what works
"""

import asyncio
import time
import random
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleFansaleBot:
    def __init__(self, proxy_config=None):
        self.proxy_config = proxy_config
        self.driver = None
        self.blocked_count = 0
        
    def setup_driver(self):
        """Create a simple undetected Chrome driver"""
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-site-isolation-trials')
        
        # Random window size
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Proxy support
        if self.proxy_config:
            from ..utils.proxy_auth_extension import create_proxy_auth_extension
            ext_path = create_proxy_auth_extension(
                self.proxy_config['username'],
                self.proxy_config['password'],
                self.proxy_config['host'],
                self.proxy_config['port']
            )
            options.add_extension(ext_path)
            logger.info(f"Using proxy: {self.proxy_config['host']}:{self.proxy_config['port']}")
        
        # Create driver
        self.driver = uc.Chrome(options=options, version_main=None)
        
        # Apply basic stealth patches
        self.driver.execute_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fix chrome object
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: () => ({})
                };
            }
            
            // Remove CDP traces
            for (const key in window) {
                if (key.includes('cdc_') || key.includes('_cdc')) {
                    delete window[key];
                }
            }
        """)
        
        return self.driver
    
    def wait_random(self, min_sec=1, max_sec=3):
        """Human-like random wait"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def check_for_block(self):
        """Check if we're blocked"""
        try:
            page_source = self.driver.page_source.lower()
            if any(blocked in page_source for blocked in ['access denied', 'blocked', '_abck', 'akamai']):
                self.blocked_count += 1
                logger.warning(f"Blocked detected! Count: {self.blocked_count}")
                return True
        except:
            pass
        return False
    
    def handle_cookies(self):
        """Accept cookies if present"""
        try:
            # Common cookie selectors for Fansale
            cookie_selectors = [
                "button[class*='accept']",
                "button[class*='cookie']",
                "button[id*='accept']",
                "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if cookie_btn.is_displayed():
                        cookie_btn.click()
                        logger.info("Accepted cookies")
                        self.wait_random(1, 2)
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"No cookie banner found: {e}")
    
    def monitor_tickets(self, url, interval=30):
        """Simple ticket monitoring"""
        logger.info(f"Starting monitoring: {url}")
        
        first_visit = True
        
        while True:
            try:
                if first_visit:
                    # First visit - full page load
                    self.driver.get(url)
                    self.wait_random(3, 5)
                    
                    # Handle cookies
                    self.handle_cookies()
                    
                    # Check for block
                    if self.check_for_block():
                        logger.error("Blocked on first visit!")
                        self.wait_random(30, 60)
                        continue
                    
                    first_visit = False
                else:
                    # Subsequent visits - just refresh
                    self.driver.refresh()
                    self.wait_random(2, 4)
                
                # Check for tickets
                ticket_selectors = [
                    ".offer-item",
                    "[class*='ticket']",
                    "[class*='offer']",
                    ".listing-item"
                ]
                
                tickets_found = False
                for selector in ticket_selectors:
                    try:
                        tickets = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if tickets:
                            logger.info(f"Found {len(tickets)} potential tickets!")
                            tickets_found = True
                            break
                    except:
                        continue
                
                if tickets_found:
                    # Burst mode - check more frequently
                    self.wait_random(5, 10)
                else:
                    logger.info("No tickets found, waiting...")
                    self.wait_random(interval - 5, interval + 5)
                    
            except WebDriverException as e:
                logger.error(f"Browser error: {e}")
                # Try to recover
                try:
                    self.driver.quit()
                except:
                    pass
                self.setup_driver()
                first_visit = True
                self.wait_random(5, 10)
                
            except KeyboardInterrupt:
                logger.info("Stopping...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                self.wait_random(10, 20)
    
    def run(self, url):
        """Run the bot"""
        try:
            self.setup_driver()
            self.monitor_tickets(url)
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    # Test configuration
    proxy = {
        'host': 'geo.iproyal.com',
        'port': '12321',
        'username': 'Doqe2Sm9Yjl1MrZd',
        'password': 'dNbFYaRftANFAJqH'
    }
    
    bot = SimpleFansaleBot(proxy_config=proxy)
    bot.run("https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388")
