import os
import sys
import time
import json
import random
import base64
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from collections import deque
from urllib.parse import urlparse

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException

# Setup
from dotenv import load_dotenv
load_dotenv()

# Logging
logger = logging.getLogger('FanSaleSensorBot')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S'))
logger.addHandler(handler)
class FanSaleSensorBot:
    """
    Advanced bot implementing sensor data generation for Akamai bypass
    Based on detective investigation findings
    """
    
    def __init__(self):
        # Core config
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        
        # URLs
        self.base_url = "https://www.fansale.it"
        self.api_endpoint = f"{self.base_url}/json/offers/17844388"
        self.target_url = f"{self.base_url}/fansale/tickets/all/bruce-springsteen/458554/17844388"
        
        # Cookie tracking
        self.abck_cookie = None
        self.bm_sz_cookie = None
        self.ak_bmsc_cookie = None
        self.sensor_data_endpoint = None  # Will find dynamically
        
        # Sensor data components
        self.start_ts = int(time.time() * 1000)
        self.sensor_history = []
        self.mouse_events = []
        self.key_events = []
        self.device_data = self._generate_device_data()
        
        self.driver = None
    def _generate_device_data(self):
        """Generate realistic device fingerprint data"""
        return {
            "screen": {
                "width": 1920,
                "height": 1080,
                "availWidth": 1920,
                "availHeight": 1040,
                "colorDepth": 24,
                "pixelDepth": 24
            },
            "navigator": {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "platform": "Win32",
                "language": "it-IT",
                "languages": ["it-IT", "it", "en-US", "en"],
                "hardwareConcurrency": 8,
                "deviceMemory": 8
            },
            "webgl": {
                "vendor": "Google Inc. (NVIDIA)",
                "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Direct3D11)"
            },
            "canvas": self._generate_canvas_fingerprint(),
            "timezone": -60,  # Italy timezone
            "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"]
        }