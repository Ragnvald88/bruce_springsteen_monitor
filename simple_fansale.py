#!/usr/bin/env python3
"""
Minimal Working Fansale Monitor
Focuses only on what's needed to avoid blocks
"""

import sys
import time
import random
import logging
from pathlib import Path

# Python 3.12+ compatibility fix
if sys.version_info >= (3, 12):
    import importlib.util
    import types
    
    # Create a dummy distutils module
    distutils = types.ModuleType('distutils')
    distutils.version = types.ModuleType('distutils.version')
    
    class LooseVersion:
        def __init__(self, version):
            self.version = str(version)
        
        def __str__(self):
            return self.version
        
        def __lt__(self, other):
            return self.version < str(other)
        
        def __le__(self, other):
            return self.version <= str(other)
        
        def __gt__(self, other):
            return self.version > str(other)
        
        def __ge__(self, other):
            return self.version >= str(other)
        
        def __eq__(self, other):
            return self.version == str(other)
        
        def __ne__(self, other):
            return self.version != str(other)
    
    distutils.version.LooseVersion = LooseVersion
    sys.modules['distutils'] = distutils
    sys.modules['distutils.version'] = distutils.version

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_driver(proxy_config=None):
    """Create a properly configured undetected Chrome driver"""
    options = uc.ChromeOptions()
    
    # Minimal options that work
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Random window size
    width = random.randint(1366, 1920)
    height = random.randint(768, 1080)
    options.add_argument(f'--window-size={width},{height}')
    
    # User agent
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # Proxy
    if proxy_config:
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from utils.proxy_auth_extension import create_proxy_auth_extension
        
        ext_path = create_proxy_auth_extension(
            proxy_config['username'],
            proxy_config['password'],
            proxy_config['host'],
            proxy_config['port']
        )
        options.add_extension(ext_path)
        logger.info(f"Using proxy: {proxy_config['host']}:{proxy_config['port']}")
    
    # Create driver
    driver = uc.Chrome(options=options, version_main=None)
    
    # Basic stealth
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return driver


def monitor_fansale(url, proxy_config=None, interval=30):
    """Monitor Fansale for tickets"""
    driver = None
    consecutive_errors = 0
    max_errors = 3
    
    while consecutive_errors < max_errors:
        try:
            if not driver:
                logger.info("Creating new browser instance...")
                driver = create_driver(proxy_config)
                time.sleep(random.uniform(2, 4))
            
            logger.info(f"Navigating to: {url}")
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # Handle cookies
            try:
                cookie_button = driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
                if cookie_button.is_displayed():
                    cookie_button.click()
                    logger.info("Accepted cookies")
                    time.sleep(random.uniform(1, 2))
            except:
                pass
            
            # Check if blocked
            page_source = driver.page_source.lower()
            if 'access denied' in page_source or 'blocked' in page_source:
                logger.warning("Detected block! Waiting longer...")
                time.sleep(random.uniform(60, 120))
                driver.quit()
                driver = None
                continue
            
            # Reset error counter on success
            consecutive_errors = 0
            
            # Monitor loop
            while True:
                try:
                    # Look for tickets
                    tickets = driver.find_elements(By.CSS_SELECTOR, ".offer-item, .listing-item")
                    
                    if tickets:
                        logger.info(f"🎫 Found {len(tickets)} tickets!")
                        # Burst mode - check more frequently
                        time.sleep(random.uniform(5, 10))
                    else:
                        logger.info("No tickets found")
                        time.sleep(random.uniform(interval-5, interval+5))
                    
                    # Refresh page
                    driver.refresh()
                    time.sleep(random.uniform(2, 4))
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Error in monitor loop: {e}")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Stopping...")
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error: {e} (attempt {consecutive_errors}/{max_errors})")
            
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            
            if consecutive_errors < max_errors:
                wait_time = min(300, 60 * consecutive_errors)
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
    
    if driver:
        driver.quit()


if __name__ == "__main__":
    # Configuration
    FANSALE_URL = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
    
    PROXY = {
        'host': 'geo.iproyal.com',
        'port': '12321',
        'username': 'Doqe2Sm9Yjl1MrZd',
        'password': 'dNbFYaRftANFAJqH'
    }
    
    # Run the monitor
    monitor_fansale(FANSALE_URL, proxy_config=PROXY)
