#!/usr/bin/env python3
"""
FanSale Bot - Ultimate Stealth Edition
Uses advanced techniques to bypass immediate detection
"""

import os
import sys
import json
import time
import random
import logging
import tempfile
import threading
from datetime import datetime
from typing import Optional, Dict, List

# Try multiple driver options
try:
    import undetected_chromedriver as uc
except ImportError:
    print("Installing undetected-chromedriver...")
    os.system("pip install undetected-chromedriver")
    import undetected_chromedriver as uc

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class UltimateStealthBot:
    """Ultimate stealth bot with maximum anti-detection"""
    
    def __init__(self):
        self.target_url = os.getenv('FANSALE_TARGET_URL', 
            'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388')
        self.max_tickets = 4
        self.ticket_types = ['prato_b', 'prato_a']
        self.tickets_secured = 0
        self.shutdown_event = threading.Event()
        
        # Stealth settings
        self.use_stealth_mode = True
        self.human_mode = True
        self.check_rate = 20  # Very slow for maximum stealth
        
    def create_ultimate_stealth_browser(self):
        """Create browser with maximum stealth techniques"""
        logger.info("🥷 Creating ultimate stealth browser...")
        
        try:
            # Method 1: Try with patched undetected-chromedriver
            return self._create_patched_browser()
        except Exception as e:
            logger.warning(f"Patched browser failed: {e}")
            
            # Method 2: Try manual Chrome with debugging
            try:
                return self._create_manual_browser()
            except Exception as e2:
                logger.error(f"Manual browser failed: {e2}")
                
                # Method 3: Last resort - basic stealth
                return self._create_basic_stealth_browser()
    
    def _create_patched_browser(self):
        """Create browser with patched undetected-chromedriver"""
        logger.info("Attempting patched undetected-chromedriver...")
        
        # Create options
        options = uc.ChromeOptions()
        
        # Critical: Use subprocess to avoid detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Stealth arguments
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=AutomationControlled')
        
        # Window settings
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Preferences
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_setting_values.notifications': 2,
            'excludeSwitches': ['enable-automation'],
            'useAutomationExtension': False,
            'profile.default_content_setting_values.plugins': 1,
            'profile.content_settings.plugin_whitelist.adobe-flash-player': 1,
            'profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player': 1,
            'PluginsAllowedForUrls': 'https://fansale.it'
        }
        options.add_experimental_option('prefs', prefs)
        
        # Use specific Chrome binary if available
        chrome_binary = self._find_chrome_binary()
        if chrome_binary:
            options.binary_location = chrome_binary
            logger.info(f"Using Chrome binary: {chrome_binary}")
        
        # Create driver with patches
        driver = uc.Chrome(
            options=options,
            driver_executable_path=None,  # Let it auto-download
            version_main=None,  # Auto-detect version
            patcher_force_close=True,  # Force close patcher
            suppress_welcome=True,
            use_subprocess=True,  # Critical for stealth!
            driver_patcher=True
        )
        
        # Apply maximum stealth patches
        self._apply_stealth_patches(driver)
        
        return driver
    
    def _create_manual_browser(self):
        """Create browser using manual Chrome instance"""
        logger.info("Attempting manual Chrome with remote debugging...")
        
        import subprocess
        
        # Start Chrome with debugging port
        chrome_path = self._find_chrome_binary()
        if not chrome_path:
            raise Exception("Chrome not found")
        
        # Use random debugging port
        debug_port = random.randint(9222, 9999)
        
        # Start Chrome manually
        subprocess.Popen([
            chrome_path,
            f'--remote-debugging-port={debug_port}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-blink-features=AutomationControlled',
            '--user-data-dir=' + tempfile.mkdtemp()
        ])
        
        time.sleep(3)  # Let Chrome start
        
        # Connect to existing Chrome
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        
        # Use standard ChromeDriver
        driver = webdriver.Chrome(options=options)
        
        # Apply stealth patches
        self._apply_stealth_patches(driver)
        
        return driver
    
    def _create_basic_stealth_browser(self):
        """Create basic stealth browser as fallback"""
        logger.info("Using basic stealth browser...")
        
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = uc.Chrome(options=options, use_subprocess=False)
        self._apply_stealth_patches(driver)
        
        return driver
    
    def _find_chrome_binary(self):
        """Find Chrome binary location"""
        locations = [
            # macOS
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            # Windows
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            # Linux
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser'
        ]
        
        for loc in locations:
            if os.path.exists(loc):
                return loc
        
        return None
    
    def _apply_stealth_patches(self, driver):
        """Apply all stealth patches to driver"""
        
        # Patch 1: Override navigator.webdriver before any page loads
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                // Remove webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Remove chrome driver
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            '''
        })
        
        # Patch 2: Add missing Chrome properties
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                window.chrome = {
                    app: {
                        isInstalled: false,
                        InstallState: {
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        },
                        RunningState: {
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        }
                    },
                    runtime: {
                        OnInstalledReason: {
                            CHROME_UPDATE: 'chrome_update',
                            INSTALL: 'install',
                            SHARED_MODULE_UPDATE: 'shared_module_update',
                            UPDATE: 'update'
                        },
                        OnRestartRequiredReason: {
                            APP_UPDATE: 'app_update',
                            OS_UPDATE: 'os_update',
                            PERIODIC: 'periodic'
                        },
                        PlatformArch: {
                            ARM: 'arm',
                            ARM64: 'arm64',
                            MIPS: 'mips',
                            MIPS64: 'mips64',
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        },
                        PlatformNaclArch: {
                            ARM: 'arm',
                            MIPS: 'mips',
                            MIPS64: 'mips64',
                            X86_32: 'x86-32',
                            X86_64: 'x86-64'
                        },
                        PlatformOs: {
                            ANDROID: 'android',
                            CROS: 'cros',
                            LINUX: 'linux',
                            MAC: 'mac',
                            OPENBSD: 'openbsd',
                            WIN: 'win'
                        },
                        RequestUpdateCheckStatus: {
                            NO_UPDATE: 'no_update',
                            THROTTLED: 'throttled',
                            UPDATE_AVAILABLE: 'update_available'
                        },
                        connect: function() {},
                        sendMessage: function() {}
                    }
                };
                
                // Add plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: ""},
                            description: "",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        },
                        {
                            0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                            1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                            description: "",
                            filename: "internal-nacl-plugin",
                            length: 2,
                            name: "Native Client"
                        }
                    ]
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Fix WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, [parameter]);
                };
                
                // Fix screen
                Object.defineProperty(screen, 'availTop', {get: () => 0});
                Object.defineProperty(screen, 'availLeft', {get: () => 0});
                
                // Remove automation properties
                ['webdriver', '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate',
                 '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped',
                 '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder',
                 '_selenium', 'calledSelenium', 'ChromeDriverw', 'driver-evaluate',
                 'webdriver-evaluate', 'selenium-evaluate', 'webdriverCommand',
                 'webdriver-evaluate-response', '__webdriverFunc', '__webdriver_script_fn',
                 '__$webdriverAsyncExecutor', '__lastWatirAlert', '__lastWatirConfirm',
                 '__lastWatirPrompt', '_WEBDRIVER_ELEM_CACHE', '$chrome_asyncScriptInfo',
                 '$cdc_asdjflasutopfhvcZLmcfl_'].forEach(prop => {
                    delete window[prop];
                    delete document[prop];
                });
            '''
        })
        
        # Patch 3: Fix navigator properties
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                // Languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'it-IT', 'it']
                });
                
                // Platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'MacIntel'
                });
                
                // Hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                
                // Device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // Connection
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 100,
                        downlink: 10.0,
                        saveData: false
                    })
                });
            '''
        })
        
        # Set user agent via CDP to ensure it's set before page load
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Set timezone
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': 'Europe/Rome'
        })
        
        # Set geolocation
        driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
            'latitude': 41.9028,
            'longitude': 12.4964,
            'accuracy': 100
        })
        
        logger.info("✅ Applied all stealth patches")

    
    def simulate_human_entry(self, driver):
        """Navigate to FanSale like a human would"""
        logger.info("🚶 Simulating human entry pattern...")
        
        try:
            # Step 1: Go to Google first (like a human)
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # Step 2: Search for FanSale
            search_box = driver.find_element(By.NAME, "q")
            
            # Type like a human
            search_term = "fansale tickets"
            for char in search_term:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            time.sleep(random.uniform(0.5, 1))
            search_box.submit()
            time.sleep(random.uniform(2, 3))
            
            # Step 3: Click on FanSale link
            try:
                fansale_link = driver.find_element(By.PARTIAL_LINK_TEXT, "FanSale")
                fansale_link.click()
                time.sleep(random.uniform(3, 5))
            except:
                # Fallback: go directly
                driver.get("https://www.fansale.it")
                time.sleep(random.uniform(3, 5))
            
            # Step 4: Browse around a bit
            self._random_browsing(driver)
            
            # Step 5: Finally go to target
            logger.info("🎯 Navigating to target page...")
            driver.get(self.target_url)
            time.sleep(random.uniform(2, 4))
            
            return True
            
        except Exception as e:
            logger.error(f"Human entry simulation failed: {e}")
            return False
    
    def _random_browsing(self, driver):
        """Browse random pages like a human"""
        try:
            # Find some links
            links = driver.find_elements(By.TAG_NAME, "a")[:10]
            
            if links:
                # Click a random link
                random_link = random.choice(links)
                driver.execute_script("arguments[0].scrollIntoView();", random_link)
                time.sleep(random.uniform(0.5, 1))
                
                try:
                    random_link.click()
                    time.sleep(random.uniform(2, 4))
                    driver.back()
                    time.sleep(random.uniform(1, 2))
                except:
                    pass
                    
        except:
            pass
    
    def human_like_mouse_movement(self, driver):
        """Simulate human mouse movements"""
        if not self.human_mode:
            return
            
        try:
            action = ActionChains(driver)
            
            # Random movements
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                
                # Move in small steps (more human-like)
                steps = random.randint(3, 6)
                for i in range(steps):
                    intermediate_x = int(x * (i+1) / steps)
                    intermediate_y = int(y * (i+1) / steps)
                    action.move_by_offset(intermediate_x, intermediate_y)
                    action.pause(random.uniform(0.01, 0.05))
                
                # Reset to avoid going off screen
                action.move_by_offset(-x, -y)
            
            action.perform()
            
        except Exception as e:
            logger.debug(f"Mouse movement error: {e}")
    
    def check_if_blocked(self, driver):
        """Check if we're blocked"""
        try:
            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()
            
            # Check URL
            if any(word in current_url for word in ['blocked', 'denied', 'captcha', 'challenge']):
                return True
            
            # Check page content
            block_phrases = [
                'access denied',
                'you have been blocked',
                'suspicious activity',
                'please verify you are human',
                'checking your browser',
                'ddos protection',
                'unusual traffic'
            ]
            
            for phrase in block_phrases:
                if phrase in page_source:
                    logger.warning(f"Block phrase detected: {phrase}")
                    return True
            
            # Check for Cloudflare
            if 'cloudflare' in page_source and ('checking' in page_source or 'challenge' in page_source):
                logger.warning("Cloudflare challenge detected")
                return True
            
            return False
            
        except:
            return False
    
    def hunt_tickets_stealth(self, driver):
        """Hunt tickets with maximum stealth"""
        logger.info("🎯 Starting stealth hunt...")
        
        check_count = 0
        last_mouse_move = time.time()
        last_human_action = time.time()
        tickets_found_count = 0
        
        while not self.shutdown_event.is_set():
            try:
                check_count += 1
                
                # Random mouse movements
                if time.time() - last_mouse_move > random.uniform(10, 20):
                    self.human_like_mouse_movement(driver)
                    last_mouse_move = time.time()
                
                # Random human actions
                if time.time() - last_human_action > random.uniform(60, 120):
                    self._perform_human_action(driver)
                    last_human_action = time.time()
                
                # Check for blocks periodically
                if check_count % 10 == 0:
                    if self.check_if_blocked(driver):
                        logger.error("🚫 BLOCKED! Stopping hunt...")
                        return
                
                # Look for tickets
                tickets = driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
                
                if tickets:
                    logger.info(f"👀 Found {len(tickets)} tickets!")
                    tickets_found_count += len(tickets)
                    
                    for ticket in tickets:
                        try:
                            # Extract info
                            ticket_text = ticket.text.lower()
                            
                            # Check if it's our target type
                            is_target = any(ticket_type in ticket_text for ticket_type in self.ticket_types)
                            
                            if is_target:
                                logger.info("🎯 TARGET TICKET FOUND!")
                                
                                # Human-like hover
                                action = ActionChains(driver)
                                action.move_to_element(ticket)
                                action.pause(random.uniform(0.5, 1.0))
                                action.perform()
                                
                                # Click with human delay
                                time.sleep(random.uniform(0.3, 0.8))
                                ticket.click()
                                
                                # Wait for purchase button
                                try:
                                    purchase_btn = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, 
                                            "[data-qa='purchaseButton'], button[class*='purchase'], button[class*='buy']"))
                                    )
                                    
                                    # Human pause
                                    time.sleep(random.uniform(0.5, 1.5))
                                    purchase_btn.click()
                                    
                                    logger.info("🎉 PURCHASE CLICKED!")
                                    
                                    # Screenshot
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    driver.save_screenshot(f"screenshots/purchase_{timestamp}.png")
                                    
                                    self.tickets_secured += 1
                                    
                                    if self.tickets_secured >= self.max_tickets:
                                        logger.info("✅ Max tickets secured!")
                                        return
                                        
                                except TimeoutException:
                                    logger.warning("Purchase button not found")
                                except Exception as e:
                                    logger.error(f"Purchase error: {e}")
                                    
                        except Exception as e:
                            logger.debug(f"Ticket processing error: {e}")
                
                # Status update
                if check_count % 20 == 0:
                    logger.info(f"Status: {check_count} checks | Found {tickets_found_count} tickets total")
                
                # Variable human-like wait
                wait_time = self._calculate_human_wait()
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Hunt error: {e}")
                time.sleep(random.uniform(2, 5))
    
    def _perform_human_action(self, driver):
        """Perform random human-like actions"""
        actions = [
            lambda: driver.execute_script("window.scrollBy(0, %d)" % random.randint(100, 300)),
            lambda: driver.execute_script("window.scrollBy(0, %d)" % random.randint(-300, -100)),
            lambda: self.human_like_mouse_movement(driver),
            lambda: None  # Sometimes do nothing
        ]
        
        action = random.choice(actions)
        try:
            action()
        except:
            pass
    
    def _calculate_human_wait(self):
        """Calculate human-like wait time"""
        base_wait = 60.0 / self.check_rate
        
        # Add human variability
        if random.random() < 0.05:  # 5% chance of long pause
            return random.uniform(5.0, 10.0)
        elif random.random() < 0.15:  # 15% chance of medium pause
            return random.uniform(2.0, 4.0)
        else:
            # Normal variation
            return base_wait + random.uniform(-0.5, 1.5)
    
    def run(self):
        """Main run method"""
        logger.info("🥷 ULTIMATE STEALTH BOT STARTING...")
        logger.info("This version uses maximum anti-detection techniques")
        
        os.makedirs("screenshots", exist_ok=True)
        
        # Create stealth browser
        driver = self.create_ultimate_stealth_browser()
        
        if not driver:
            logger.error("❌ Failed to create stealth browser!")
            return
        
        try:
            # Test if we're detected
            logger.info("🔍 Testing detection status...")
            driver.get("https://bot.sannysoft.com/")
            time.sleep(3)
            
            webdriver_status = driver.execute_script("return navigator.webdriver")
            logger.info(f"navigator.webdriver: {webdriver_status}")
            
            if webdriver_status:
                logger.warning("⚠️ Browser may be detectable! Proceeding with caution...")
            else:
                logger.info("✅ Browser appears undetectable!")
            
            # Navigate like a human
            if self.use_stealth_mode:
                success = self.simulate_human_entry(driver)
                if not success:
                    logger.warning("Human entry failed, going direct...")
                    driver.get(self.target_url)
                    time.sleep(random.uniform(3, 5))
            else:
                driver.get(self.target_url)
                time.sleep(random.uniform(2, 4))
            
            # Check if blocked immediately
            if self.check_if_blocked(driver):
                logger.error("🚫 BLOCKED ON ENTRY! Site has detected automation.")
                logger.info("\nTry these solutions:")
                logger.info("1. Use a VPN or proxy")
                logger.info("2. Clear all cookies and cache")
                logger.info("3. Try from a different IP")
                logger.info("4. Use the manual browser method")
                return
            
            # Start hunting
            self.hunt_tickets_stealth(driver)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                driver.quit()
            except:
                pass
            
            logger.info(f"\n✅ Session complete. Tickets secured: {self.tickets_secured}")


def main():
    print("""
    🥷 ULTIMATE STEALTH BOT 🥷
    ========================
    
    This version uses:
    - Advanced WebDriver hiding
    - Human-like navigation patterns
    - Complete browser spoofing
    - Anti-fingerprinting techniques
    
    If you're still getting blocked, the site may be using
    advanced bot detection that requires manual intervention.
    
    Starting in 5 seconds...
    """)
    
    time.sleep(5)
    
    bot = UltimateStealthBot()
    bot.run()


if __name__ == "__main__":
    main()
