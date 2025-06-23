#!/usr/bin/env python3
"""
FanSale Bot - Enhanced Hunter-Buyer Edition
Combines speed of hunter-buyer pattern with advanced stealth and optimizations
Each browser independently hunts and buys for maximum speed
"""

import os
import sys
import time
import random
import logging
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from utilities.stealth_improvements import StealthEnhancements
from utilities.speed_optimizations import SpeedOptimizer, FastTicketChecker

from dotenv import load_dotenv
load_dotenv()

# Configure logging with enhanced format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(threadName)-12s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FanSaleHunterBuyer')


class FanSaleHunterBuyerBot:
    """Enhanced hunter-buyer bot with stealth and speed optimizations"""
    
    def __init__(self):
        # Credentials
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
                                    "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554")
        
        # Configuration
        self.num_browsers = 3  # Default
        self.use_proxy = False
        self.use_lite_mode = True  # Default to lite for speed
        self.use_stealth = True
        self.manual_login = True  # As requested
        
        # Browser management
        self.browsers = []
        self.browser_threads = []
        self.purchase_lock = threading.Lock()
        self.ticket_secured = threading.Event()
        self.shutdown_event = threading.Event()
        
        # Optimization helpers
        self.stealth = StealthEnhancements()
        self.optimizer = SpeedOptimizer()
        
        # Statistics
        self.start_time = None
        self.check_counts = {}
        self.total_checks = 0
        
    def calculate_smart_refresh_timing(self) -> Tuple[float, float]:
        """Calculate aggressive refresh timing with smart distribution"""
        # Target: 20-30+ checks per minute TOTAL across all browsers
        # Strategy: Vary timing to avoid pattern detection
        
        if self.num_browsers == 1:
            # Single browser: 15-20 checks/minute (3-4 seconds between)
            min_wait = 3.0
            max_wait = 4.0
        elif self.num_browsers == 2:
            # 2 browsers: 25-30 checks/minute total (4-5 seconds each)
            min_wait = 4.0
            max_wait = 5.0
        elif self.num_browsers == 3:
            # 3 browsers: 30-36 checks/minute total (5-6 seconds each)
            min_wait = 5.0
            max_wait = 6.0
        elif self.num_browsers <= 5:
            # 4-5 browsers: 40-50 checks/minute total (6-7.5 seconds each)
            min_wait = 6.0
            max_wait = 7.5
        else:
            # 6+ browsers: 50-60 checks/minute total (7-10 seconds each)
            min_wait = 7.0
            max_wait = 10.0
        
        # Add randomization factor to avoid detection
        # Each browser will have slightly different timing
        browser_offset = random.uniform(-0.5, 0.5)
        
        return (min_wait + browser_offset, max_wait + browser_offset)
    
    def get_proxy_config(self) -> Optional[Dict]:
        """Get proxy configuration if enabled"""
        if not self.use_proxy:
            return None
        
        required_vars = ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'IPROYAL_HOSTNAME', 'IPROYAL_PORT']
        if not all(os.getenv(k) for k in required_vars):
            logger.warning("⚠️  Proxy credentials incomplete. Running without proxy.")
            return None
        
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        logger.info("🔐 Proxy configured for Italy")
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            }
        }
    
    def create_hunter_buyer_browser(self, browser_id: int) -> uc.Chrome:
        """Create a stealth-optimized hunter-buyer browser"""
        logger.info(f"🚀 Creating Hunter-Buyer Browser {browser_id}...")
        
        options = uc.ChromeOptions()
        
        # Unique persistent profile
        profile_dir = Path("browser_profiles") / f"hunter_buyer_{browser_id}"
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir.absolute()}')
        
        # Apply stealth options
        if self.use_stealth:
            for arg in self.stealth.get_enhanced_chrome_options():
                options.add_argument(arg)
        
        # Apply speed optimizations
        for arg in self.optimizer.get_performance_chrome_options():
            options.add_argument(arg)
        
        # Window positioning (optimized grid layout)
        positions = [
            (0, 0), (400, 0), (800, 0), (1200, 0),      # Row 1
            (0, 350), (400, 350), (800, 350), (1200, 350),  # Row 2
            (0, 700), (400, 700)                         # Row 3
        ]
        
        if browser_id <= len(positions):
            x, y = positions[browser_id - 1]
        else:
            x = ((browser_id - 1) % 4) * 400
            y = ((browser_id - 1) // 4) * 350
        
        options.add_argument(f'--window-position={x},{y}')
        options.add_argument('--window-size=380,320')
        
        # Lite mode for maximum speed
        if self.use_lite_mode:
            prefs = {
                "profile.default_content_setting_values": {
                    "images": 2,  # Block images
                    "plugins": 2,  # Block plugins
                    "popups": 2,  # Block popups
                    "geolocation": 2,  # Block location
                    "notifications": 2,  # Block notifications
                    "media_stream": 2,  # Block media
                },
                "profile.managed_default_content_settings": {
                    "images": 2,
                    "stylesheets": 2,  # Block CSS for ultra-speed
                }
            }
            options.add_experimental_option("prefs", prefs)
            logger.info(f"  💨 Browser {browser_id}: Ultra-lite mode enabled")
        
        # Create browser with proxy if configured
        proxy_config = self.get_proxy_config()
        
        try:
            driver = uc.Chrome(options=options, seleniumwire_options=proxy_config)
            driver.set_page_load_timeout(20)
            
            # Inject stealth JavaScript
            if self.use_stealth:
                driver.execute_script(self.stealth.get_stealth_javascript())
            
            # Apply speed optimizations
            driver.execute_script(self.optimizer.get_fast_page_load_script())
            self.optimizer.optimize_dom_queries(driver)
            
            logger.info(f"✅ Browser {browser_id} created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create browser {browser_id}: {e}")
            raise
    
    def apply_anti_detection_measures(self, driver: uc.Chrome, browser_id: int):
        """Apply additional anti-detection measures"""
        try:
            # Randomize viewport size slightly
            width = 380 + random.randint(-20, 20)
            height = 320 + random.randint(-20, 20)
            driver.set_window_size(width, height)
            
            # Set random zoom level (95-105%)
            zoom = random.uniform(0.95, 1.05)
            driver.execute_script(f"document.body.style.zoom = '{zoom}'")
            
            # Add random browser storage data to appear more human
            driver.execute_script("""
                // Add some localStorage data
                try {
                    localStorage.setItem('lastVisit', Date.now());
                    localStorage.setItem('visits', Math.floor(Math.random() * 10) + 1);
                    sessionStorage.setItem('session_id', Math.random().toString(36));
                } catch(e) {}
                
                // Add some cookies
                document.cookie = "returning_user=true; path=/";
                document.cookie = `browser_id=${Math.random().toString(36)}; path=/`;
            """)
            
            logger.debug(f"Browser {browser_id}: Anti-detection measures applied")
        except Exception as e:
            logger.warning(f"Failed to apply some anti-detection measures: {e}")
    
    def manual_login_browser(self, browser_id: int, driver: uc.Chrome) -> bool:
        """Handle manual login for a browser"""
        logger.info(f"🔐 Manual login required for Browser {browser_id}")
        
        try:
            # Navigate to login page
            driver.get("https://www.fansale.it/fansale/login.htm")
            time.sleep(2)  # Let page load
            
            # Display login instructions
            print(f"\n{'='*60}")
            print(f"🔐 LOGIN REQUIRED - BROWSER #{browser_id}")
            print(f"{'='*60}")
            print(f"Email: {self.email}")
            print(f"Password: {'*' * len(self.password)}")
            print(f"\n⚠️  Please login manually in Browser #{browser_id}")
            print(f"{'='*60}\n")
            
            input(f"✋ Press Enter after Browser #{browser_id} is successfully logged in...")
            
            # Navigate to target page after login
            logger.info(f"Navigating Browser {browser_id} to target page...")
            driver.get(self.target_url)
            time.sleep(3)  # Let page fully load
            
            # Apply anti-detection measures after login
            self.apply_anti_detection_measures(driver, browser_id)
            
            # Quick verification
            if "fansale" in driver.current_url.lower():
                logger.info(f"✅ Browser {browser_id} logged in and ready!")
                return True
            else:
                logger.warning(f"⚠️  Browser {browser_id} might not be properly logged in")
                return True  # Continue anyway
                
        except Exception as e:
            logger.error(f"❌ Login process failed for Browser {browser_id}: {e}")
            return False
    
    def hunt_and_buy(self, browser_id: int, driver: uc.Chrome):
        """Core hunter-buyer loop with aggressive checking and smart evasion"""
        thread_name = f"Hunter-{browser_id}"
        threading.current_thread().name = thread_name
        
        # Initialize fast checker for this browser
        fast_checker = FastTicketChecker(driver)
        refresh_min, refresh_max = self.calculate_smart_refresh_timing()
        
        # Pattern variation to avoid detection
        patterns = ['normal', 'burst', 'slow', 'random']
        current_pattern = random.choice(patterns)
        pattern_switch_time = time.time() + random.uniform(30, 60)  # Switch pattern every 30-60s
        
        logger.info(f"🎯 Hunter {browser_id} active! Base timing: {refresh_min:.1f}-{refresh_max:.1f}s")
        
        check_count = 0
        last_refresh = time.time()
        burst_mode = False
        slow_period = False
        
        while not self.ticket_secured.is_set() and not self.shutdown_event.is_set():
            try:
                check_count += 1
                self.check_counts[browser_id] = check_count
                self.total_checks += 1
                
                # Switch patterns periodically to avoid detection
                if time.time() > pattern_switch_time:
                    current_pattern = random.choice(patterns)
                    pattern_switch_time = time.time() + random.uniform(30, 60)
                    logger.debug(f"Hunter {browser_id}: Switching to {current_pattern} pattern")
                
                # Fast ticket check
                has_tickets, ticket_count = fast_checker.fast_ticket_check()
                
                if has_tickets and ticket_count > 0:
                    logger.info(f"🎫 HUNTER {browser_id}: {ticket_count} TICKETS DETECTED!")
                    
                    # Try to acquire purchase lock
                    if self.purchase_lock.acquire(blocking=False):
                        try:
                            if not self.ticket_secured.is_set():
                                logger.info(f"🔥 HUNTER {browser_id}: INITIATING PURCHASE!")
                                if self.execute_lightning_purchase(driver, browser_id):
                                    self.ticket_secured.set()
                                    logger.info(f"✅ HUNTER {browser_id}: TICKET SECURED!")
                                else:
                                    logger.warning(f"❌ Hunter {browser_id}: Purchase failed")
                        finally:
                            self.purchase_lock.release()
                    else:
                        logger.info(f"Hunter {browser_id}: Another hunter is purchasing...")
                
                # Dynamic refresh logic based on pattern
                if current_pattern == 'burst':
                    # Burst mode: very fast for short period
                    wait_time = random.uniform(2.0, 3.0)
                elif current_pattern == 'slow':
                    # Slow mode: longer waits to balance out bursts
                    wait_time = random.uniform(refresh_max, refresh_max + 2)
                elif current_pattern == 'random':
                    # Random mode: highly variable timing
                    wait_time = random.uniform(2.0, refresh_max + 3)
                else:
                    # Normal mode: standard timing
                    wait_time = random.uniform(refresh_min, refresh_max)
                
                # Add micro-variations to prevent exact patterns
                wait_time += random.uniform(-0.5, 0.5)
                
                # Ensure minimum wait to avoid hammering
                wait_time = max(2.0, wait_time)
                
                # Refresh logic
                time_since_refresh = time.time() - last_refresh
                if time_since_refresh >= wait_time:
                    # Add human-like behavior randomly
                    if random.random() < 0.15:  # 15% chance
                        # Quick mouse movement
                        if random.random() < 0.5:
                            self.stealth.random_mouse_movement(driver, 0.3)
                        # Or small scroll
                        else:
                            self.stealth.random_scrolling(driver, 0.2)
                    
                    # Vary refresh method occasionally
                    if random.random() < 0.9:  # 90% normal refresh
                        driver.refresh()
                    else:  # 10% alternative refresh
                        driver.execute_script("location.reload()")
                    
                    last_refresh = time.time()
                    
                    # Wait with calculated time
                    time.sleep(wait_time)
                else:
                    # Small wait between checks
                    time.sleep(0.3)
                
                # Progress update with rate calculation
                if check_count % 10 == 0:
                    elapsed = time.time() - self.start_time if self.start_time else 1
                    rate = (check_count * 60) / elapsed
                    logger.info(f"   Hunter {browser_id}: {check_count} checks | {rate:.1f}/min")
                    
            except TimeoutException:
                logger.debug(f"Hunter {browser_id}: Page timeout, refreshing...")
                driver.refresh()
                time.sleep(2)
                
            except WebDriverException as e:
                if "target window already closed" in str(e):
                    logger.warning(f"Hunter {browser_id}: Browser closed")
                    break
                logger.error(f"Hunter {browser_id}: WebDriver error: {e}")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Hunter {browser_id}: Unexpected error: {e}")
                traceback.print_exc()
                time.sleep(5)
        
        logger.info(f"Hunter {browser_id}: Shutting down")
    
    def execute_lightning_purchase(self, driver: uc.Chrome, browser_id: int) -> bool:
        """Execute ultra-fast purchase sequence"""
        try:
            logger.info(f"⚡ Hunter {browser_id}: Lightning purchase sequence initiated!")
            
            # Bring window to front
            driver.switch_to.window(driver.current_window_handle)
            
            # Try multiple ticket selectors for robustness
            ticket_selectors = [
                "[data-qa='ticketToBuy']",
                "div.ticket-item",
                "//div[contains(@class, 'ticket')]",
                "button[class*='ticket']"
            ]
            
            ticket_clicked = False
            for selector in ticket_selectors:
                try:
                    if selector.startswith('//'):
                        # XPath
                        ticket = driver.find_element(By.XPATH, selector)
                    else:
                        # CSS
                        ticket = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Click with JavaScript for maximum speed
                    driver.execute_script("arguments[0].click();", ticket)
                    ticket_clicked = True
                    logger.info(f"✓ Ticket clicked using selector: {selector}")
                    break
                except:
                    continue
            
            if not ticket_clicked:
                logger.error("Failed to click any ticket element")
                return False
            
            # Wait for and click buy button
            buy_selectors = [
                "[data-qa='buyNowButton']",
                "button[class*='buy']",
                "//button[contains(text(), 'Compra')]",
                "//button[contains(text(), 'Buy')]"
            ]
            
            for selector in buy_selectors:
                try:
                    buy_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((
                            By.XPATH if selector.startswith('//') else By.CSS_SELECTOR,
                            selector
                        ))
                    )
                    driver.execute_script("arguments[0].click();", buy_button)
                    logger.info(f"✓ Buy button clicked!")
                    
                    # Take screenshot
                    screenshot_path = f"ticket_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"📸 Screenshot saved: {screenshot_path}")
                    
                    logger.info("✅✅✅ PURCHASE COMPLETED! Check browser to finish checkout.")
                    return True
                    
                except TimeoutException:
                    continue
            
            logger.error("Failed to find buy button")
            return False
            
        except Exception as e:
            logger.error(f"Purchase execution failed: {e}")
            traceback.print_exc()
            return False
    
    def display_statistics(self):
        """Display running statistics in a separate thread"""
        while not self.shutdown_event.is_set():
            try:
                time.sleep(30)  # Update every 30 seconds
                
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    
                    # Calculate rates
                    check_rate = self.total_checks / (elapsed / 60) if elapsed > 0 else 0
                    
                    # Per-browser stats
                    browser_stats = []
                    for bid, count in self.check_counts.items():
                        browser_stats.append(f"B{bid}:{count}")
                    
                    logger.info(f"📊 STATS | Time: {minutes}m {seconds}s | " +
                              f"Total Checks: {self.total_checks} | " +
                              f"Rate: {check_rate:.1f}/min | " +
                              f"Browsers: {' '.join(browser_stats)}")
                    
            except Exception as e:
                logger.error(f"Stats display error: {e}")
    
    def run(self):
        """Main execution flow"""
        print("\n" + "="*70)
        print("🎯 FANSALE BOT - ENHANCED HUNTER-BUYER EDITION")
        print("="*70)
        print("Each browser hunts AND buys independently for MAXIMUM SPEED!")
        print("First to find = First to buy. No delays.")
        print("="*70 + "\n")
        
        # Get configuration from user
        while True:
            try:
                num = input("🌐 How many hunter-buyer browsers? (1-5, recommended 2-3): ").strip()
                self.num_browsers = int(num)
                if 1 <= self.num_browsers <= 5:
                    break
                print("❌ Please enter a number between 1 and 5")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Proxy configuration
        proxy_choice = input("\n🔐 Use proxy for all browsers? (y/n, default: n): ").strip().lower()
        self.use_proxy = proxy_choice == 'y'
        
        # Lite mode configuration
        lite_choice = input("\n💨 Use ultra-lite mode for speed? (y/n, default: y): ").strip().lower()
        self.use_lite_mode = lite_choice != 'n'
        
        # Stealth configuration
        stealth_choice = input("\n🥷 Enable stealth enhancements? (y/n, default: y): ").strip().lower()
        self.use_stealth = stealth_choice != 'n'
        
        # Calculate and display configuration
        refresh_timing = self.calculate_smart_refresh_timing()
        
        # Calculate expected checks per minute
        avg_wait = (refresh_timing[0] + refresh_timing[1]) / 2
        checks_per_browser = 60 / avg_wait
        total_checks_per_min = self.num_browsers * checks_per_browser
        
        print(f"\n📋 CONFIGURATION SUMMARY:")
        print(f"   • Browsers: {self.num_browsers} hunter-buyers")
        print(f"   • Timing per browser: {refresh_timing[0]:.1f}-{refresh_timing[1]:.1f}s")
        print(f"   • Expected rate: ~{checks_per_browser:.1f} checks/min per browser")
        print(f"   • TOTAL RATE: ~{total_checks_per_min:.1f} checks/minute 🚀")
        print(f"   • Proxy: {'✅ Enabled' if self.use_proxy else '❌ Disabled'}")
        print(f"   • Lite mode: {'✅ Ultra-fast' if self.use_lite_mode else '❌ Normal'}")
        print(f"   • Stealth: {'✅ Enhanced' if self.use_stealth else '❌ Basic'}")
        print(f"   • Pattern variation: ✅ Enabled (burst/normal/slow/random)")
        print(f"   • Target: {self.target_url}")
        
        try:
            # Create and login all browsers
            print(f"\n🚀 Setting up {self.num_browsers} hunter-buyer browsers...\n")
            
            for i in range(1, self.num_browsers + 1):
                driver = self.create_hunter_buyer_browser(i)
                
                # Manual login
                if not self.manual_login_browser(i, driver):
                    logger.error(f"Failed to login browser {i}")
                    driver.quit()
                    continue
                
                self.browsers.append(driver)
                
                # Test stealth if enabled
                if self.use_stealth and i == 1:  # Only test first browser
                    logger.info("🔍 Testing stealth measures...")
                    test_results = self.stealth.test_detection(driver)
                    analysis = self.stealth.analyze_detection_results(test_results)
                    logger.info(f"🛡️ Stealth Score: {analysis['score']}/100 ({analysis['status']})")
            
            if not self.browsers:
                logger.error("❌ No browsers were successfully created. Exiting.")
                return
            
            logger.info(f"\n✅ All {len(self.browsers)} browsers are logged in and ready!")
            input("\n✋ Press Enter to START THE HUNT across all browsers...")
            
            # Start hunting
            self.start_time = time.time()
            logger.info("\n🎯 HUNT IS LIVE! All browsers are actively hunting for tickets.\n")
            
            # Start hunter threads
            for i, driver in enumerate(self.browsers):
                thread = threading.Thread(
                    target=self.hunt_and_buy,
                    args=(i + 1, driver),
                    daemon=True
                )
                thread.start()
                self.browser_threads.append(thread)
                time.sleep(0.5)  # Stagger thread starts
            
            # Start statistics thread
            stats_thread = threading.Thread(target=self.display_statistics, daemon=True)
            stats_thread.start()
            
            # Wait for ticket to be secured or user interrupt
            print("\n⚡ Hunting in progress... Press Ctrl+C to stop.\n")
            
            while not self.ticket_secured.is_set():
                time.sleep(1)
            
            logger.info("\n🎉 TICKET SECURED! The winning browser will remain open.")
            logger.info("Complete your purchase in the browser window.")
            input("\nPress Enter to close other browsers and exit...")
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested by user...")
            
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            traceback.print_exc()
            
        finally:
            # Cleanup
            logger.info("🧹 Cleaning up...")
            self.shutdown_event.set()
            
            # Close browsers (except the one with the ticket if secured)
            for i, driver in enumerate(self.browsers):
                try:
                    if not self.ticket_secured.is_set() or i != 0:  # Keep first browser open if ticket secured
                        driver.quit()
                except:
                    pass
            
            logger.info("✅ Shutdown complete.")


def main():
    """Entry point"""
    # Check dependencies
    try:
        import undetected_chromedriver
        from dotenv import load_dotenv
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check credentials
    load_dotenv()
    if not os.getenv('FANSALE_EMAIL') or not os.getenv('FANSALE_PASSWORD'):
        print("❌ Missing credentials in .env file")
        print("Please ensure FANSALE_EMAIL and FANSALE_PASSWORD are set")
        sys.exit(1)
    
    # Run bot
    bot = FanSaleHunterBuyerBot()
    bot.run()


if __name__ == "__main__":
    main()
