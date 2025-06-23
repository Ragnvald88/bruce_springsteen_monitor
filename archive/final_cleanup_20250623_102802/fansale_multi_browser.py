#!/usr/bin/env python3
"""
FanSale Multi-Browser Bot
Rotates between multiple browser profiles to avoid rate limiting
Transfers found tickets to a dedicated purchase browser
"""

import os
import time
import random
import logging
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | [%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)

class BrowserInstance:
    """Single browser instance with its own profile"""
    
    def __init__(self, instance_id, profile_name):
        self.id = instance_id
        self.profile_name = profile_name
        self.driver = None
        self.logger = logging.getLogger(f'Browser-{instance_id}')
        self.start_time = None
        self.check_count = 0
        self.is_active = False
        self.is_blocked = False
        
    def setup(self):
        """Setup browser with unique profile"""
        self.logger.info(f"🌐 Starting browser with profile: {self.profile_name}")
        
        options = uc.ChromeOptions()
        
        # Each browser gets its own profile
        profile_dir = Path("browser_profiles") / self.profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Standard options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1200,800')
        
        # Position windows differently
        x_pos = (self.id - 1) * 400
        y_pos = (self.id - 1) * 100
        options.add_argument(f'--window-position={x_pos},{y_pos}')
        
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(20)
        self.start_time = time.time()
        self.is_active = True
        
    def cleanup(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.is_active = False