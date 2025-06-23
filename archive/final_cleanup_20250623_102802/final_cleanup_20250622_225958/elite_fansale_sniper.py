import os
import sys
import time
import json
import random
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Setup ---
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# --- Elite Logger ---
logger = logging.getLogger('EliteSniper')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
logger.addHandler(handler)

class BotState(Enum):
    INIT = "init"
    LOGIN = "login"
    HUNT = "hunt"
    SNIPE = "snipe"
    WIN = "win"

class EliteFanSaleSniper:
    """Elite-level ticket sniper - Simple, Fast, Undetectable"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Elite timing strategy
        self.check_patterns = [
            # Pattern: (min_wait, max_wait, burst_count)
            (0.3, 0.8, 3),    # Fast burst
            (1.5, 3.0, 1),    # Normal check
            (0.5, 1.0, 2),    # Medium burst
            (2.0, 4.0, 1),    # Slow check
        ]
        self.pattern_index = 0
        
        # Smart detection
        self.last_content_hash = None
        self.unchanged_count = 0
        
        self.state = BotState.INIT
        self.driver = None

    def setup_driver(self):
        """Ultra-optimized driver setup"""
        options = uc.ChromeOptions()
        
        # Data-saving preferences
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values": {
                "cookies": 1,
                "media_stream": 2,
                "notifications": 2,
                "geolocation": 2,
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        # Elite performance flags
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        
        # Profile for session persistence
        profile_dir = Path("browser_profiles") / "elite_fansale"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # IPRoyal proxy setup
        proxy_options = None
        if all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                      'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
            proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
            
            # Request interception to save bandwidth
            proxy_options = {
                'proxy': {
                    'http': f'http://{proxy_auth}@{proxy_server}',
                    'https': f'https://{proxy_auth}@{proxy_server}'
                },
                'exclude_hosts': ['fonts.googleapis.com', 'googletagmanager.com'],
                'suppress_connection_errors': True
            }
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(10)
        
        # Block unnecessary requests to save proxy data
        self.driver.request_interceptor = self.intercept_request
        
        logger.info("💀 Elite driver initialized")

    def intercept_request(self, request):
        """Block unnecessary requests to save proxy bandwidth"""
        block_patterns = [
            'google-analytics', 'googletagmanager', 'doubleclick',
            'facebook', 'hotjar', 'clarity', '.png', '.jpg', '.gif',
            'font', '.css', 'analytics', 'tracking'
        ]
        
        for pattern in block_patterns:
            if pattern in request.url:
                request.abort()
