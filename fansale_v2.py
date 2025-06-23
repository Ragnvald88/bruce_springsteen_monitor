#!/usr/bin/env python3
"""
FanSale Bot - Enhanced Hunter Edition v2.0
Fixed JavaScript errors, cleaner logging, automatic login support
"""

import os
import sys
import time
import random
import logging
import threading
import traceback
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Suppress verbose WebDriver logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('seleniumwire').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

# Import utilities (with fallback if not available)
try:
    from utilities.stealth_enhancements import StealthEnhancements
    from utilities.speed_optimizer import SpeedOptimizer, FastTicketChecker
    from utilities.session_manager import SessionManager
    UTILITIES_AVAILABLE = True
except ImportError:
    UTILITIES_AVAILABLE = False
    print("⚠️  Enhanced utilities not found, using basic mode")

from dotenv import load_dotenv
load_dotenv()

# Configure cleaner logging
class CleanFormatter(logging.Formatter):
    """Custom formatter to suppress WebDriver stack traces"""
    def format(self, record):
        # Skip WebDriver stack traces
        msg = str(record.msg)
        if "Stacktrace:" in msg:
            # Extract just the error message
            msg = msg.split('\n')[0]
            record.msg = msg
        return super().format(record)

# Set up logging with clean formatter
handler = logging.StreamHandler()
handler.setFormatter(CleanFormatter('%(asctime)s | %(threadName)-10s | %(message)s', datefmt='%H:%M:%S'))

logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(handler)

# File handler
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(CleanFormatter('%(asctime)s | %(threadName)-10s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(file_handler)


class FanSaleBot:
    """Enhanced FanSale bot with automatic login and cleaner logging"""
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388")
