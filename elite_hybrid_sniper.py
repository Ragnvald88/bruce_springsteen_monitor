import os
import sys
import time
import json
import random
import hashlib
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
from selenium.webdriver.chrome.service import Service

# --- Setup ---
load_dotenv()
Path("logs").mkdir(exist_ok=True)
Path("browser_profiles").mkdir(exist_ok=True)

# --- Logging ---
logger = logging.getLogger('EliteSniper')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)

class EliteFanSaleBot:
    """
    Elite FanSale Bot - Hybrid Approach
    Combines browser automation with smart detection patterns
    """
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Smart timing patterns (mimics human behavior)
        self.check_patterns = [
            # (min_seconds, max_seconds, checks_in_burst)
            (0.8, 1.5, 2),    # Quick double-check
            (3.0, 5.0, 1),    # Pause
            (1.0, 2.0, 3),    # Moderate burst
            (4.0, 7.0, 1),    # Longer pause
            (0.5, 1.2, 2),    # Fast burst
            (2.5, 4.5, 1),    # Medium pause
        ]
        self.current_pattern = 0
        
        # Detection avoidance
        self.last_mouse_move = 0
        self.page_hash = None
        self.no_change_count = 0
        
        self.driver = None

    def setup_driver(self):
        """Setup browser with maximum stealth and minimum data usage"""
        logger.info("🚀 Initializing elite browser...")
        
        options = uc.ChromeOptions()
        
        # Critical data-saving preferences
        prefs = {
            # Block images completely
            "profile.managed_default_content_settings.images": 2,
            # Block other resource-heavy content
            "profile.default_content_setting_values": {
                "media_stream": 2,
                "media_stream_mic": 2,
                "media_stream_camera": 2,
                "notifications": 2,
                "automatic_downloads": 2,
            },
            # Aggressive cache settings
            "disk-cache-size": 4096,
            "media-cache-size": 4096,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Performance flags
        flags = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-gpu',
            '--disable-logging',
            '--disable-plugins',
            '--disable-images',
            '--disable-javascript-harmony-shipping',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-features=TranslateUI',
            '--disable-features=OptimizationGuideModelDownloading',
            '--aggressive-cache-discard',
            '--memory-pressure-off',
        ]
        
        for flag in flags:
            options.add_argument(flag)
        
        # Persistent profile
        profile_dir = Path("browser_profiles") / "elite_fansale"
        options.add_argument(f'--user-data-dir={os.path.abspath(profile_dir)}')
        
        # IPRoyal proxy
        proxy_options = self._get_proxy_config()
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=proxy_options)
        self.driver.set_page_load_timeout(8)
        
        # Inject monitoring scripts
        self._inject_monitor_script()
        
        logger.info("✅ Elite browser ready")

    def _get_proxy_config(self):
        """Configure IPRoyal proxy with request filtering"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            return None
            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        def request_interceptor(request):
            # Block unnecessary resources to save proxy data
            block_patterns = [
                '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
                'font', '.css', 'analytics', 'google', 'facebook',
                'tracking', 'advertisement', '.mp4', '.webm'
            ]
            
            for pattern in block_patterns:
                if pattern in request.url.lower():
                    request.abort()
                    
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            },
            'request_interceptor': request_interceptor,
            'suppress_connection_errors': True
        }

    def _inject_monitor_script(self):
        """Inject JavaScript for ultra-fast ticket detection"""
        monitor_script = """
        window.ticketMonitor = {
            lastCheck: null,
            found: false,
            
            check: function() {
                const ticket = document.querySelector('div[data-qa="ticketToBuy"]');
                if (ticket && !this.found) {
                    this.found = true;
                    // Create a visible flag for Selenium
                    document.body.setAttribute('data-ticket-found', 'true');
                    return true;
                }
                return false;
            },
            
            getPageHash: function() {
                // Quick hash of ticket area content
                const area = document.querySelector('.ticket-listings, .event-tickets, main');
                return area ? area.textContent.length : 0;
            }
        };
        
        // Run check every 200ms (client-side, no network usage)
        setInterval(() => window.ticketMonitor.check(), 200);
        """
        
        try:
            self.driver.execute_script(monitor_script)
        except:
            pass
