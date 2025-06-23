#!/usr/bin/env python3
"""
FanSale Bot - Ultimate Hunter-Buyer Edition
Each browser is an independent hunter AND buyer for maximum speed.
First to find = First to buy. No delays, no transfers.
"""

import os
import sys
import time
import random
import logging
import threading
from datetime import datetime
from pathlib import Path
import traceback

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(threadName)-10s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FanSaleBot')


class FanSaleUltimateBot:
    """Each browser is a self-contained hunter-buyer for maximum speed."""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Configuration
        self.num_browsers = 3  # Default, user can change
        self.use_proxy = False
        self.use_lite_mode = False
        
        # Thread synchronization
        self.browsers = []
        self.threads = []
        self.purchase_lock = threading.Lock()
        self.ticket_secured = False
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.start_time = None
        self.check_counts = {}  # Per browser check counts
        self.total_checks = 0

    def calculate_refresh_timing(self):
        """Smart refresh timing to avoid rate limits while maximizing coverage."""
        # Total target: 3-4 refreshes/minute across all browsers
        if self.num_browsers == 1:
            return (10, 15)  # Single browser can be more aggressive
        elif self.num_browsers == 2:
            return (15, 25)  # 2 browsers
        elif self.num_browsers <= 4:
            return (20, 35)  # 3-4 browsers
        elif self.num_browsers <= 6:
            return (30, 45)  # 5-6 browsers
        else:
            return (40, 60)  # 7+ browsers - very conservative
    
    def get_proxy_config(self):
        """Get proxy configuration if enabled."""
        if not self.use_proxy:
            return None
            
        required_vars = ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'IPROYAL_HOSTNAME', 'IPROYAL_PORT']
        if not all(os.getenv(k) for k in required_vars):
            logger.warning("⚠️  Proxy credentials incomplete. Running without proxy.")
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        logger.info("🔐 Proxy configured")
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            }
        }
    def create_browser(self, browser_id):
        """Create a hunter-buyer browser with optimal settings."""
        logger.info(f"🚀 Creating Browser {browser_id}...")
        
        options = uc.ChromeOptions()
        
        # Unique persistent profile for each browser
        profile_dir = Path("browser_profiles") / f"hunter_buyer_{browser_id}"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Window positioning (grid layout)
        positions = [
            (0, 0), (400, 0), (800, 0), (1200, 0),      # Row 1
            (0, 400), (400, 400), (800, 400), (1200, 400),  # Row 2
            (0, 800), (400, 800)                         # Row 3
        ]
        
        if browser_id <= len(positions):
            x, y = positions[browser_id - 1]
        else:
            x, y = (0, 0)
            
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=380,350')
        
        # Lite mode settings if enabled
        if self.use_lite_mode:
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
            }
            options.add_experimental_option("prefs", prefs)
            logger.info(f"  💾 Browser {browser_id}: Lite mode enabled")
        
        # Create browser
        proxy_config = self.get_proxy_config()
        driver = uc.Chrome(options=options, seleniumwire_options=proxy_config)
        driver.set_page_load_timeout(20)
        
        return driver
    
    def login_browser(self, browser_id, driver):
        """Handle manual login for a browser."""
        logger.info(f"🔐 Login required for Browser {browser_id}")
        
        # Navigate to login
        driver.get("https://www.fansale.it/fansale/login.htm")
        
        print(f"\n{'='*60}")
        print(f"LOGIN TO BROWSER #{browser_id}")
        print(f"{'='*60}")
        print(f"Email: {self.email}")
        print(f"Password: {'*' * len(self.password)}")
        
        input(f"\n✋ Press Enter after Browser #{browser_id} is logged in...")
        
        # Verify login by checking for user menu
        try:
            # Auto-navigate to target page after login
            driver.get(self.target_url)
            time.sleep(2)
            
            # Quick check if we can see the page properly
            if "bruce" in driver.title.lower() or "springsteen" in driver.title.lower():
                logger.info(f"✅ Browser {browser_id} logged in and on listing page!")
                return True
            else:
                logger.warning(f"⚠️  Browser {browser_id} might not be on the correct page")
                return True  # Continue anyway
                
        except Exception as e:
            logger.error(f"❌ Browser {browser_id} login verification failed: {e}")
            return False