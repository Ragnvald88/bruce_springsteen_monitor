#!/usr/bin/env python3
"""
FanSale Bot - Enhanced No Login Edition
Features:
- No login required
- Ticket type categorization (Prato A, Prato B, Settore)
- Duplicate detection to avoid re-logging same tickets
- Persistent statistics across restarts
- Beautiful terminal logging with ticket details
"""

import os
import sys
import time
import random
import logging
import threading
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

# Suppress verbose logs
os.environ['WDM_LOG_LEVEL'] = '0'
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement

from dotenv import load_dotenv
load_dotenv()

# ANSI color codes for beautiful terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Configure logging with custom formatter
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelname == 'INFO':
            if 'PRATO A' in record.msg:
                record.msg = f"{Colors.GREEN}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'PRATO B' in record.msg:
                record.msg = f"{Colors.BLUE}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'SETTORE' in record.msg:
                record.msg = f"{Colors.YELLOW}{Colors.BOLD}{record.msg}{Colors.END}"
            elif 'NEW TICKET' in record.msg:
                record.msg = f"{Colors.CYAN}{Colors.BOLD}{record.msg}{Colors.END}"
            elif '🎫' in record.msg:
                record.msg = f"{Colors.BOLD}{record.msg}{Colors.END}"
        return super().format(record)

# Configure logging
logger = logging.getLogger('FanSaleBot')
logger.setLevel(logging.INFO)
logger.handlers.clear()

# Console handler with colors
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('fansale_bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(file_handler)

class FanSaleBot:
    """Enhanced FanSale bot with ticket type tracking - No login required"""
    
    def __init__(self):
        # Get target URL from env or use default
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554")
        
        # Configuration
        self.num_browsers = 1
        self.max_tickets = 4
        self.ticket_filters = []  # Will be set to track specific types
        
        # State management
        self.browsers = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        
        # Ticket tracking - to avoid duplicate logging
        self.seen_tickets = set()  # Store hashes of seen tickets
        self.ticket_details_cache = {}  # Store full details of tickets
        
        # Load persistent statistics
        self.stats_file = Path("fansale_stats.json")
        self.load_stats()
        
        # Performance monitoring
        self.session_start_time = time.time()

    def load_stats(self):
        """Load persistent statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    # Merge with default stats structure
                    self.stats = {
                        'total_checks': saved_stats.get('total_checks', 0),
                        'total_tickets_found': saved_stats.get('total_tickets_found', 0),
                        'unique_tickets_found': saved_stats.get('unique_tickets_found', 0),
                        'tickets_by_type': {
                            'prato_a': saved_stats.get('tickets_by_type', {}).get('prato_a', 0),
                            'prato_b': saved_stats.get('tickets_by_type', {}).get('prato_b', 0),
                            'settore': saved_stats.get('tickets_by_type', {}).get('settore', 0),
                            'other': saved_stats.get('tickets_by_type', {}).get('other', 0)
                        },
                        'purchases': saved_stats.get('purchases', 0),
                        'blocks_encountered': saved_stats.get('blocks_encountered', 0),
                        'all_time_runtime': saved_stats.get('all_time_runtime', 0)
                    }
                logger.info(f"📊 Loaded stats: {self.stats['unique_tickets_found']} unique tickets tracked historically")
            except Exception as e:
                logger.warning(f"Could not load stats: {e}, starting fresh")
                self.init_fresh_stats()
        else:
            self.init_fresh_stats()
    
    def init_fresh_stats(self):
        """Initialize fresh statistics structure"""
        self.stats = {
            'total_checks': 0,
            'total_tickets_found': 0,
            'unique_tickets_found': 0,
            'tickets_by_type': {
                'prato_a': 0,
                'prato_b': 0,
                'settore': 0,
                'other': 0
            },
            'purchases': 0,
            'blocks_encountered': 0,
            'all_time_runtime': 0
        }
    
    def save_stats(self):
        """Save statistics to file"""
        try:
            # Update runtime
            session_time = time.time() - self.session_start_time
            self.stats['all_time_runtime'] += session_time
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
    
    def categorize_ticket(self, ticket_text: str) -> str:
        """Categorize ticket based on text content"""
        ticket_lower = ticket_text.lower()
        
        # Check for Prato A
        if 'prato a' in ticket_lower or 'prato gold a' in ticket_lower:
            return 'prato_a'
        # Check for Prato B
        elif 'prato b' in ticket_lower or 'prato gold b' in ticket_lower:
            return 'prato_b'
        # Check for Settore
        elif 'settore' in ticket_lower or 'settore numerato' in ticket_lower:
            return 'settore'
        else:
            return 'other'
    
    def generate_ticket_hash(self, ticket_text: str) -> str:
        """Generate unique hash for ticket to detect duplicates"""
        # Extract key identifying information
        # Remove dynamic elements like timestamps
        clean_text = re.sub(r'\d{1,2}:\d{2}:\d{2}', '', ticket_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return hashlib.md5(clean_text.encode()).hexdigest()