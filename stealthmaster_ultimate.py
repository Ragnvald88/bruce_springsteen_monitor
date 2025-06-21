#!/usr/bin/env python3
"""
StealthMaster Ultimate - The Best of Everything with Proxy Optimization
Combines all optimizations with minimal data usage for proxy efficiency
"""

import sys
import os
import time
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

# Setup
console = Console()
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/stealthmaster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StealthMasterUltimate:
    """
    Ultimate StealthMaster - Best performance with proxy optimization
    
    Features:
    - Single browser instance (saves proxy bandwidth)
    - Aggressive resource blocking
    - Smart caching to minimize requests
    - Page hash comparison to skip unchanged content
    - Compressed data storage
    - Bandwidth monitoring
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.url = config.get('url')
        self.check_interval = config.get('check_interval', 5)
        self.auto_reserve = config.get('auto_reserve', True)
        self.max_price = config.get('max_price', 999999)
        self.quantity = config.get('quantity', 1)
        
        # Proxy optimization settings
        self.use_proxy = config.get('proxy', None)
        self.minimize_bandwidth = config.get('minimize_bandwidth', True)
        self.cache_responses = config.get('cache_responses', True)
        
        # Login credentials - prioritize .env over config
        self.email = os.getenv('FANSALE_EMAIL') or config.get('email', None)
        self.password = os.getenv('FANSALE_PASSWORD') or config.get('password', None)
        self.logged_in = False
        
        # Build proxy URL from .env if not in config
        if not self.use_proxy and os.getenv('IPROYAL_USERNAME'):
            proxy_user = os.getenv('IPROYAL_USERNAME')
            proxy_pass = os.getenv('IPROYAL_PASSWORD')
            proxy_host = os.getenv('IPROYAL_HOSTNAME')
            proxy_port = os.getenv('IPROYAL_PORT')
            if all([proxy_user, proxy_pass, proxy_host, proxy_port]):
                self.use_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
                logger.info("Using IPRoyal proxy from .env")
        
        # Browser instance
        self.driver = None
        
        # Performance tracking
        self.stats = {
            'start_time': datetime.now(),
            'checks': 0,
            'tickets_found': 0,
            'tickets_reserved': 0,
            'reservation_attempts': 0,
            'errors': 0,
            'blocks': 0,
            'bandwidth_saved': 0,
            'total_bandwidth': 0,
            'cache_hits': 0,
            'avg_check_time': 0,
            'fastest_check': float('inf'),
            'status': 'initializing',
            'session_reservations': []  # Track all reservations this session
        }
        
        # Intelligent caching
        self.page_cache = {}
        self.ticket_cache = {}
        self.seen_tickets = set()
        self.reserved_tickets = set()
        self.last_page_hash = None
        self.last_full_check = 0
        
        # Session ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def verify_proxy(self, driver) -> bool:
        """Verify proxy is working correctly"""
        try:
            # Check IP through proxy
            driver.get('https://api.ipify.org?format=json')
            ip_data = driver.execute_script("return document.body.innerText;")
            
            if ip_data:
                logger.info(f"✓ Proxy verified - Current IP: {ip_data}")
                with open(f'logs/proxy_usage_{self.session_id}.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - Proxy verified: {ip_data}\n")
                return True
            return False
        except Exception as e:
            logger.error(f"Proxy verification failed: {e}")
            return False
    
    def create_ultimate_driver(self) -> Optional[uc.Chrome]:
        """Create the most optimized driver with proxy support"""
        try:
            options = uc.ChromeOptions()
            
            # Core stealth options
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Headless for maximum speed and lowest bandwidth
            if self.config.get('headless', True):
                options.add_argument('--headless=new')
            
            # Proxy configuration
            if self.use_proxy:
                options.add_argument(f'--proxy-server={self.use_proxy}')
                logger.info(f"🌐 Proxy configured: {self.use_proxy}")
                
                # Log proxy to file
                with open(f'logs/proxy_usage_{self.session_id}.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - Proxy configured: {self.use_proxy}\n")
            
            # Maximum bandwidth optimization
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript-harmony-shipping')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-hang-monitor')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-prompt-on-repost')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-web-resources')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--no-first-run')
            options.add_argument('--safebrowsing-disable-auto-update')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Network optimization
            options.add_argument('--aggressive-cache-discard')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # Data saver preferences
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,
                    'plugins': 2,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2,
                    'media_stream': 2,
                    'media_stream_mic': 2,
                    'media_stream_camera': 2,
                    'protocol_handlers': 2,
                    'ppapi_broker': 2,
                    'automatic_downloads': 2,
                    'midi_sysex': 2,
                    'push_messaging': 2,
                    'ssl_cert_decisions': 2,
                    'metro_switch_to_desktop': 2,
                    'protected_media_identifier': 2,
                    'app_banner': 2,
                    'site_engagement': 2,
                    'durable_storage': 2
                },
                'profile.managed_default_content_settings': {
                    'images': 2,
                    'javascript': 1,  # Keep JS enabled for functionality
                    'cookies': 1,
                    'plugins': 2,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2,
                    'media_stream': 2
                }
            }
            options.add_experimental_option('prefs', prefs)
            
            # Page load strategy - don't wait for all resources
            options.page_load_strategy = 'eager'
            
            # Window size
            options.add_argument('--window-size=1920,1080')
            
            # Create driver
            service = Service()
            driver = uc.Chrome(options=options, service=service, version_main=None)
            
            # Configure timeouts
            driver.set_page_load_timeout(15)
            driver.implicitly_wait(0)
            
            # Advanced resource blocking via CDP
            if self.minimize_bandwidth:
                driver.execute_cdp_cmd('Network.enable', {})
                driver.execute_cdp_cmd('Network.setBlockedURLs', {
                    'urls': [
                        '*analytics*', '*google*', '*facebook*', '*doubleclick*',
                        '*cloudflare*', '*amazon-adsystem*', '*googlesyndication*',
                        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.svg', '*.ico',
                        '*.woff*', '*.ttf', '*.otf', '*.css', '*.mp4', '*.webm'
                    ]
                })
                
                # Enable cache
                driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': False})
                
                # Set custom headers for compression
                driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                    'headers': {
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Cache-Control': 'max-age=3600',
                        'Connection': 'keep-alive'
                    }
                })
            
            # Minimal anti-detection
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)
            
            logger.info("✓ Ultimate driver created with maximum optimizations")
            
            # Verify proxy is working
            if self.use_proxy:
                self.verify_proxy(driver)
            
            return driver
            
        except Exception as e:
            logger.error(f"Driver creation error: {e}")
            return None
    
    def calculate_page_hash(self) -> str:
        """Calculate hash of page content for change detection"""
        try:
            # Get only the ticket container HTML to minimize data
            ticket_container = self.driver.execute_script("""
                const containers = document.querySelectorAll('.offer-list, .ticket-list, [class*="ticket-container"], main');
                return containers.length > 0 ? containers[0].innerHTML : document.body.innerHTML;
            """)
            return hashlib.md5(ticket_container.encode()).hexdigest()
        except:
            return ""
    
    def update_lifetime_stats(self):
        """Update lifetime reservation statistics"""
        try:
            lifetime_file = Path('logs/lifetime_reservations.json')
            
            # Load existing stats
            if lifetime_file.exists():
                with open(lifetime_file, 'r') as f:
                    lifetime_stats = json.load(f)
            else:
                lifetime_stats = {'total': 0, 'by_date': {}, 'by_price': {}}
            
            # Update stats
            lifetime_stats['total'] += 1
            today = datetime.now().strftime('%Y-%m-%d')
            lifetime_stats['by_date'][today] = lifetime_stats['by_date'].get(today, 0) + 1
            
            # Save updated stats
            with open(lifetime_file, 'w') as f:
                json.dump(lifetime_stats, f, indent=2)
                
            logger.info(f"Lifetime total reservations: {lifetime_stats['total']}")
            
        except Exception as e:
            logger.error(f"Failed to update lifetime stats: {e}")
    
    def handle_cookies_fast(self):
        """Handle cookies with minimal overhead"""
        try:
            # Use JavaScript for instant cookie acceptance
            self.driver.execute_script("""
                const buttons = document.querySelectorAll('button[id*="accept"], button[class*="accept"], button[class*="consent"]');
                buttons.forEach(btn => btn.click());
            """)
            time.sleep(0.5)
        except:
            pass
    
    def extract_tickets_ultimate(self) -> Tuple[List[Dict], int]:
        """Extract tickets with bandwidth optimization"""
        try:
            # Get tickets via optimized JavaScript
            tickets_data = self.driver.execute_script("""
                const tickets = [];
                const selectors = ['.offer-item', '[class*="offer"]', '[class*="ticket"]', '.listing-item'];
                let totalElements = 0;
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    totalElements += elements.length;
                    
                    elements.forEach((el, index) => {
                        if (el.offsetHeight > 0) {
                            const text = el.innerText || el.textContent || '';
                            if (text.trim()) {
                                const priceMatch = text.match(/€\\s*(\\d+(?:[.,]\\d+)?)/);
                                tickets.push({
                                    text: text.trim().substring(0, 200),
                                    price: priceMatch ? parseFloat(priceMatch[1].replace(',', '.')) : null,
                                    selector: selector,
                                    index: index,
                                    id: el.getAttribute('data-id') || index
                                });
                            }
                        }
                    });
                }
                
                return {tickets: tickets, elementCount: totalElements};
            """)
            
            # Process tickets
            new_tickets = []
            data_size = len(json.dumps(tickets_data))
            
            for data in tickets_data.get('tickets', []):
                ticket_id = hash(data['text'])
                
                if ticket_id not in self.seen_tickets:
                    self.seen_tickets.add(ticket_id)
                    
                    # Apply filters
                    if data['price'] is None or data['price'] <= self.max_price:
                        new_tickets.append({
                            'id': ticket_id,
                            'text': data['text'],
                            'price': data['price'],
                            'selector': data['selector'],
                            'index': data['index'],
                            'timestamp': time.time()
                        })
                        
                        # Cache the ticket
                        self.ticket_cache[ticket_id] = data
            
            return new_tickets, data_size
            
        except Exception as e:
            logger.debug(f"Extraction error: {e}")
            return [], 0
    
    async def smart_reserve_ticket(self, ticket: Dict) -> bool:
        """Reserve ticket with minimal requests"""
        try:
            start_time = time.time()
            self.stats['reservation_attempts'] += 1
            
            # Use JavaScript for faster interaction
            result = self.driver.execute_script("""
                const selector = arguments[0];
                const index = arguments[1];
                
                // Find and click the ticket
                const elements = document.querySelectorAll(selector);
                if (!elements[index]) return {success: false, error: 'Element not found'};
                
                elements[index].scrollIntoView({behavior: 'instant', block: 'center'});
                elements[index].click();
                
                // Wait and look for action buttons
                return new Promise((resolve) => {
                    setTimeout(() => {
                        const actionButtons = document.querySelectorAll(
                            'button[class*="cart"], button[class*="add"], button[class*="buy"], ' +
                            'button[class*="reserve"], input[type="submit"][value*="cart"], ' +
                            'a[href*="cart"][class*="button"]'
                        );
                        
                        if (actionButtons.length > 0) {
                            actionButtons[0].click();
                            
                            // Check cart status after brief wait
                            setTimeout(() => {
                                const cartIndicators = document.querySelectorAll(
                                    '.cart-count, .basket-count, [class*="cart-count"], ' +
                                    '[class*="basket"] [class*="count"]'
                                );
                                
                                let hasItems = false;
                                cartIndicators.forEach(ind => {
                                    const text = ind.textContent || ind.innerText || '';
                                    if (text && text.trim() !== '0') {
                                        hasItems = true;
                                    }
                                });
                                
                                resolve({success: hasItems, clicked: true});
                            }, 1000);
                        } else {
                            resolve({success: false, error: 'No action button found'});
                        }
                    }, 1500);
                });
            """, ticket['selector'], ticket['index'])
            
            elapsed = time.time() - start_time
            
            if result.get('success'):
                self.stats['tickets_reserved'] += 1
                self.reserved_tickets.add(ticket['id'])
                
                # Log successful reservation
                reservation_data = {
                    'timestamp': datetime.now().isoformat(),
                    'ticket': ticket['text'],
                    'price': ticket.get('price', 'unknown'),
                    'time_taken': f"{elapsed:.2f}s"
                }
                
                with open(f'logs/reservations_{self.session_id}.json', 'a') as f:
                    json.dump(reservation_data, f)
                    f.write('\n')
                
                # Update session total
                self.stats['session_reservations'].append(reservation_data)
                
                # Update lifetime total
                self.update_lifetime_stats()
                
                logger.info(f"🎉 Ticket reserved in {elapsed:.2f}s!")
                console.print(f"\n[bold green]🎉 TICKET RESERVED![/bold green]")
                console.print(f"Price: €{ticket.get('price', 'unknown')}")
                console.print(f"[yellow]Total reserved this session: {len(self.stats['session_reservations'])}[/yellow]")
                print('\a' * 3)  # Alert sound
                
                return True
            else:
                logger.debug(f"Reservation failed: {result.get('error', 'Unknown')}")
                return False
                
        except Exception as e:
            logger.error(f"Reservation error: {e}")
            return False
    
    def check_if_blocked(self) -> bool:
        """Quick block detection"""
        try:
            # Fast check using JavaScript
            blocked = self.driver.execute_script("""
                const text = document.body.innerText.toLowerCase();
                const indicators = ['access denied', 'rate limit', 'captcha', 'forbidden', 'blocked'];
                return indicators.some(ind => text.includes(ind));
            """)
            
            if blocked:
                self.stats['blocks'] += 1
                logger.warning("⚠️ Blocked detected")
                
            return blocked
            
        except:
            return False
    
    def perform_login(self) -> bool:
        """Perform login to Fansale"""
        try:
            logger.info("🔐 Attempting login to Fansale...")
            
            # Navigate to login page
            login_url = "https://www.fansale.it/fansale/login"
            self.driver.get(login_url)
            time.sleep(2)
            
            # Find and fill email field
            email_field = self.driver.execute_script("""
                const selectors = ['input[name="email"]', 'input[type="email"]', '#email', '[id*="email"]'];
                for (const sel of selectors) {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        elem.value = arguments[0];
                        elem.dispatchEvent(new Event('input', {bubbles: true}));
                        return true;
                    }
                }
                return false;
            """, self.email)
            
            if not email_field:
                logger.error("Could not find email field")
                return False
            
            time.sleep(1)
            
            # Find and fill password field
            password_field = self.driver.execute_script("""
                const selectors = ['input[name="password"]', 'input[type="password"]', '#password', '[id*="password"]'];
                for (const sel of selectors) {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        elem.value = arguments[0];
                        elem.dispatchEvent(new Event('input', {bubbles: true}));
                        return true;
                    }
                }
                return false;
            """, self.password)
            
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            time.sleep(1)
            
            # Submit login form
            submit_result = self.driver.execute_script("""
                const selectors = ['button[type="submit"]', 'input[type="submit"]', '.login-button', '[class*="login"][class*="submit"]'];
                for (const sel of selectors) {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        elem.click();
                        return true;
                    }
                }
                // Try form submit
                const forms = document.querySelectorAll('form');
                for (const form of forms) {
                    if (form.innerHTML.includes('password')) {
                        form.submit();
                        return true;
                    }
                }
                return false;
            """)
            
            if not submit_result:
                logger.error("Could not submit login form")
                return False
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login successful
            login_success = self.driver.execute_script("""
                // Check for login indicators
                const loggedInIndicators = [
                    '.user-menu', '.logout', '[href*="logout"]', 
                    '.my-account', '[class*="user-account"]'
                ];
                
                for (const sel of loggedInIndicators) {
                    if (document.querySelector(sel)) return true;
                }
                
                // Check if we're on login page (failed)
                if (window.location.href.includes('login')) return false;
                
                // Check for error messages
                const errorIndicators = ['error', 'invalid', 'incorrect'];
                const bodyText = document.body.innerText.toLowerCase();
                for (const error of errorIndicators) {
                    if (bodyText.includes(error)) return false;
                }
                
                return true;
            """)
            
            if login_success:
                logger.info("✅ Successfully logged in to Fansale!")
                self.logged_in = True
                
                # Save session cookies
                self.save_session_cookies()
                
                return True
            else:
                logger.error("❌ Login failed - check credentials")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def save_session_cookies(self):
        """Save session cookies for faster future logins"""
        try:
            cookies = self.driver.get_cookies()
            with open(f'logs/session_cookies_{self.session_id}.pkl', 'wb') as f:
                pickle.dump(cookies, f)
            logger.info("Session cookies saved")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
    
    def load_session_cookies(self) -> bool:
        """Try to load previous session cookies"""
        try:
            cookie_files = list(Path('logs').glob('session_cookies_*.pkl'))
            if cookie_files:
                # Use most recent cookie file
                latest_cookie_file = max(cookie_files, key=lambda p: p.stat().st_mtime)
                
                with open(latest_cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                # Add cookies to driver
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                
                logger.info("Previous session cookies loaded")
                return True
        except Exception as e:
            logger.debug(f"Could not load cookies: {e}")
        return False
    
    async def intelligent_check_loop(self):
        """Smart checking with bandwidth optimization"""
        consecutive_errors = 0
        last_full_refresh = time.time()
        
        while True:
            try:
                check_start = time.time()
                self.stats['checks'] += 1
                
                # Smart refresh strategy
                current_time = time.time()
                time_since_refresh = current_time - last_full_refresh
                
                # Determine check type
                if time_since_refresh > 300:  # Full refresh every 5 minutes
                    logger.debug("Performing full page refresh")
                    self.driver.refresh()
                    last_full_refresh = current_time
                    await asyncio.sleep(1)
                else:
                    # Quick hash check first
                    current_hash = self.calculate_page_hash()
                    
                    if current_hash == self.last_page_hash:
                        # Page unchanged, skip extraction
                        self.stats['cache_hits'] += 1
                        self.stats['bandwidth_saved'] += 1000  # Estimate 1KB saved
                        check_time = time.time() - check_start
                        await asyncio.sleep(self.check_interval)
                        continue
                    
                    self.last_page_hash = current_hash
                
                # Check if blocked
                if self.check_if_blocked():
                    self.stats['status'] = 'blocked'
                    await self.recovery_procedure()
                    continue
                
                # Extract tickets
                new_tickets, data_size = self.extract_tickets_ultimate()
                self.stats['total_bandwidth'] += data_size
                
                # Update status
                self.stats['status'] = 'running'
                consecutive_errors = 0
                
                # Handle new tickets
                if new_tickets:
                    self.stats['tickets_found'] += len(new_tickets)
                    
                    console.print(f"\n[green]🎫 {len(new_tickets)} NEW TICKETS FOUND![/green]")
                    
                    # Show ticket details
                    for i, ticket in enumerate(new_tickets[:5]):
                        console.print(f"  [{i+1}] {ticket['text'][:80]}...")
                        if ticket.get('price'):
                            console.print(f"      💰 €{ticket['price']}")
                    
                    # Auto-reserve - THIS IS WHERE THE MAGIC HAPPENS!
                    if self.auto_reserve:
                        logger.info("🎯 AUTO-RESERVE TRIGGERED! Found new tickets, attempting reservation...")
                        self.stats['status'] = 'reserving'
                        
                        # Sort by price (cheapest first)
                        sorted_tickets = sorted(
                            [t for t in new_tickets if t.get('price')],
                            key=lambda x: x['price']
                        )
                        
                        # Reserve tickets up to quantity
                        for ticket in sorted_tickets[:self.quantity]:
                            if ticket['id'] not in self.reserved_tickets:
                                logger.info(f"🎫 Attempting to reserve ticket at €{ticket.get('price', 'unknown')}...")
                                if await self.smart_reserve_ticket(ticket):
                                    logger.info("✅ TICKET SUCCESSFULLY RESERVED!")
                                    break  # Stop after successful reservation
                                else:
                                    logger.warning("❌ Failed to reserve this ticket, trying next...")
                                await asyncio.sleep(1)
                        
                        self.stats['status'] = 'running'
                    else:
                        logger.warning("⚠️ Auto-reserve is OFF! Enable it in config.yaml to automatically reserve tickets!")
                    
                    # Alert
                    print('\a')
                
                # Update timing stats
                check_time = time.time() - check_start
                self.stats['avg_check_time'] = (
                    (self.stats['avg_check_time'] * (self.stats['checks'] - 1) + check_time) 
                    / self.stats['checks']
                )
                self.stats['fastest_check'] = min(self.stats['fastest_check'], check_time)
                
                # Dynamic interval
                if new_tickets:
                    interval = 2  # Fast when tickets available
                else:
                    interval = self.check_interval
                    # Slower at night (Italian time)
                    hour = datetime.now().hour
                    if 0 <= hour <= 6:
                        interval *= 1.5
                
                await asyncio.sleep(interval)
                
            except WebDriverException as e:
                logger.error(f"WebDriver error: {e}")
                self.stats['errors'] += 1
                consecutive_errors += 1
                
                if consecutive_errors >= 3:
                    await self.recovery_procedure()
                else:
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"Check loop error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    async def recovery_procedure(self) -> bool:
        """Recover from blocks or errors"""
        try:
            logger.info("🔄 Attempting recovery...")
            
            # Close and recreate driver
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            # Exponential backoff
            wait_time = min(300, 30 * (2 ** min(self.stats['blocks'], 4)))
            logger.info(f"⏳ Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)
            
            # Create new driver
            self.driver = self.create_ultimate_driver()
            if not self.driver:
                return False
            
            # Navigate to page
            self.driver.get(self.url)
            await asyncio.sleep(3)
            
            # Handle cookies
            self.handle_cookies_fast()
            
            # Reset caches
            self.last_page_hash = None
            
            # Check success
            if not self.check_if_blocked():
                logger.info("✅ Recovery successful!")
                self.stats['status'] = 'running'
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Recovery error: {e}")
            return False
    
    def save_session_report(self):
        """Save detailed session report"""
        try:
            report = {
                'session_id': self.session_id,
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': str(datetime.now() - self.stats['start_time']),
                'url': self.url,
                'proxy_used': self.use_proxy,
                'stats': self.stats,
                'reservations': self.stats['session_reservations']
            }
            
            report_file = f'logs/session_report_{self.session_id}.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Session report saved to {report_file}")
            
            # Also append to master log
            with open('logs/all_sessions.jsonl', 'a') as f:
                json.dump({
                    'session_id': self.session_id,
                    'date': datetime.now().isoformat(),
                    'tickets_reserved': len(self.stats['session_reservations']),
                    'total_value': sum(r.get('price', 0) for r in self.stats['session_reservations'] if isinstance(r.get('price'), (int, float)))
                }, f)
                f.write('\n')
                
        except Exception as e:
            logger.error(f"Failed to save session report: {e}")
    
    def create_dashboard(self) -> Panel:
        """Comprehensive dashboard with bandwidth stats"""
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green")
        
        runtime = str(datetime.now() - self.stats['start_time']).split('.')[0]
        
        # Performance metrics
        table.add_row("⏱️  Runtime", runtime)
        table.add_row("🔍 Checks", str(self.stats['checks']))
        table.add_row("🎫 Tickets Found", str(self.stats['tickets_found']))
        table.add_row("🎯 Reserved", f"{self.stats['tickets_reserved']} / {self.stats['reservation_attempts']}")
        table.add_row("⚡ Avg Check", f"{self.stats['avg_check_time']:.2f}s")
        table.add_row("🏃 Fastest", f"{self.stats['fastest_check']:.2f}s" 
                     if self.stats['fastest_check'] < float('inf') else "N/A")
        
        # Bandwidth metrics
        table.add_row("", "")
        bandwidth_mb = self.stats['total_bandwidth'] / 1024 / 1024
        saved_mb = self.stats['bandwidth_saved'] / 1024 / 1024
        table.add_row("📊 Data Used", f"{bandwidth_mb:.2f} MB")
        table.add_row("💾 Data Saved", f"{saved_mb:.2f} MB")
        table.add_row("🎯 Cache Hits", str(self.stats['cache_hits']))
        
        # Session reservations
        if self.stats['session_reservations']:
            table.add_row("", "")
            total_value = sum(r.get('price', 0) for r in self.stats['session_reservations'] if isinstance(r.get('price'), (int, float)))
            table.add_row("🎟️  Session Total", f"{len(self.stats['session_reservations'])} tickets")
            table.add_row("💶 Total Value", f"€{total_value:.2f}")
        
        # Status
        table.add_row("", "")
        status_color = {
            'running': 'green',
            'blocked': 'red',
            'error': 'yellow',
            'initializing': 'cyan',
            'reserving': 'magenta'
        }.get(self.stats['status'], 'white')
        
        table.add_row("📊 Status", f"[{status_color}]{self.stats['status'].upper()}[/{status_color}]")
        table.add_row("⚠️  Errors/Blocks", f"{self.stats['errors']} / {self.stats['blocks']}")
        
        # Configuration
        table.add_row("", "")
        table.add_row("⚙️  Auto-Reserve", "ON" if self.auto_reserve else "OFF")
        table.add_row("💰 Max Price", f"€{self.max_price}")
        if self.use_proxy:
            table.add_row("🌐 Proxy", "Active")
        
        return Panel(table, title=f"StealthMaster Ultimate [{self.session_id}]", border_style="cyan")
    
    async def run(self):
        """Main run method"""
        logger.info("🚀 Starting StealthMaster Ultimate")
        logger.info(f"Target: {self.url}")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info(f"Auto-reserve: {self.auto_reserve}")
        logger.info(f"Bandwidth optimization: {self.minimize_bandwidth}")
        
        try:
            # Create optimized driver
            self.driver = self.create_ultimate_driver()
            if not self.driver:
                raise Exception("Failed to create driver")
            
            # Check for login credentials
            if not self.email or not self.password:
                console.print("[red]❌ No login credentials provided![/red]")
                console.print("[yellow]Fansale requires login to view and reserve tickets.[/yellow]")
                raise Exception("Login credentials required")
            
            # Try to load previous session
            console.print("[cyan]Checking for previous session...[/cyan]")
            self.driver.get(self.url)
            await asyncio.sleep(2)
            
            if self.load_session_cookies():
                self.driver.refresh()
                await asyncio.sleep(2)
            
            # Check if already logged in
            is_logged_in = self.driver.execute_script("""
                const indicators = ['.user-menu', '.logout', '[href*="logout"]', '.my-account'];
                return indicators.some(sel => document.querySelector(sel) !== null);
            """)
            
            if not is_logged_in:
                console.print("[yellow]Not logged in, performing login...[/yellow]")
                if not self.perform_login():
                    raise Exception("Login failed")
                
                # Navigate back to tickets page
                self.driver.get(self.url)
                await asyncio.sleep(3)
            else:
                console.print("[green]✅ Already logged in from previous session![/green]")
                self.logged_in = True
            
            # Handle cookies
            self.handle_cookies_fast()
            
            # Initial check
            if self.check_if_blocked():
                console.print("[red]❌ Blocked on first visit![/red]")
                console.print("[yellow]Attempting recovery...[/yellow]")
                if not await self.recovery_procedure():
                    raise Exception("Unable to bypass initial block")
            else:
                console.print("[green]✅ Successfully connected![/green]")
            
            # Start monitoring with dashboard
            with Live(self.create_dashboard(), refresh_per_second=1) as live:
                monitor_task = asyncio.create_task(self.intelligent_check_loop())
                
                while True:
                    live.update(self.create_dashboard())
                    await asyncio.sleep(1)
                    
                    # Check if monitor task failed
                    if monitor_task.done():
                        monitor_task.result()  # Re-raise any exception
                        
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping...[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Fatal error: {e}[/red]")
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            # Final summary
            runtime = datetime.now() - self.stats['start_time']
            console.print(f"\n[cyan]Session Summary:[/cyan]")
            console.print(f"  Runtime: {runtime}")
            console.print(f"  Total checks: {self.stats['checks']}")
            console.print(f"  Tickets found: {self.stats['tickets_found']}")
            console.print(f"  Tickets reserved: {self.stats['tickets_reserved']}")
            console.print(f"  Success rate: {self.stats['tickets_reserved']}/{self.stats['reservation_attempts']}")
            console.print(f"  Data used: {self.stats['total_bandwidth']/1024/1024:.2f} MB")
            console.print(f"  Data saved: {self.stats['bandwidth_saved']/1024/1024:.2f} MB")
            console.print(f"  Cache efficiency: {self.stats['cache_hits']} hits")
            
            # Save final session report
            self.save_session_report()


def load_config() -> Dict:
    """Load configuration with defaults"""
    # Try to load from config file
    config_path = Path("config.yaml")
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                data = yaml.safe_load(f)
                
            # Extract Fansale configuration
            for target in data.get('targets', []):
                if target.get('enabled') and target.get('platform') == 'fansale':
                    config = {
                        'url': target['url'],
                        'check_interval': target.get('check_interval', 5),
                        'auto_reserve': target.get('auto_reserve', True),
                        'max_price': target.get('max_price', 999999),
                        'quantity': target.get('quantity', 1),
                        'headless': target.get('headless', True),
                        'minimize_bandwidth': target.get('minimize_bandwidth', True),
                        'cache_responses': target.get('cache_responses', True),
                        'proxy': target.get('proxy', None),
                        'email': target.get('email', None),
                        'password': target.get('password', None)
                    }
                    return config
                    
        except ImportError:
            logger.warning("PyYAML not installed, using defaults")
        except Exception as e:
            logger.error(f"Config error: {e}")
    
    # Default configuration
    return {
        'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
        'check_interval': 5,
        'auto_reserve': True,
        'max_price': 999999,
        'quantity': 1,
        'headless': True,
        'minimize_bandwidth': True,
        'cache_responses': True,
        'proxy': None,
        'email': None,
        'password': None
    }


async def main():
    """Main entry point"""
    config = load_config()
    
    # Check if we have credentials from .env
    if os.getenv('FANSALE_EMAIL') and os.getenv('FANSALE_PASSWORD'):
        logger.info("Using Fansale credentials from .env file")
    elif not config.get('email') or not config.get('password'):
        console.print("[red]❌ No Fansale credentials found![/red]")
        console.print("Please set FANSALE_EMAIL and FANSALE_PASSWORD in .env file")
        console.print("Or add them to config.yaml")
        return
    # No interactive prompts - use config values as-is
    # Everything is already configured in config.yaml or .env
    
    # Show configuration
    console.print("\n[cyan]Configuration:[/cyan]")
    console.print(f"  URL: {config['url']}")
    console.print(f"  Auto-reserve: [bold green]{'ON' if config['auto_reserve'] else 'OFF'}[/bold green]")
    console.print(f"  Max price: €{config['max_price']}")
    console.print(f"  Tickets to reserve: {config.get('quantity', 1)}")
    console.print(f"  Check interval: {config['check_interval']}s")
    console.print(f"  Proxy: {'IPRoyal (.env)' if 'iproyal' in str(config.get('proxy', '')).lower() else config.get('proxy', 'None')}")
    console.print(f"  Bandwidth optimization: ON")
    console.print(f"  Credentials: {'From .env' if os.getenv('FANSALE_EMAIL') else 'From config.yaml'}")
    console.print("")
    console.print("[bold yellow]🎯 AUTO-RESERVE IS ACTIVE - Tickets will be reserved automatically![/bold yellow]")
    console.print("")
    
    # Run bot
    bot = StealthMasterUltimate(config)
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")