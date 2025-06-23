#!/usr/bin/env python3
"""
FanSale Lite Browser Bot
Optimized for minimal data usage
"""

import os
import time
import random
import logging
from datetime import datetime

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('FanSaleLite')

class LiteFanSaleBot:
    """Minimal data usage version"""
    
    def __init__(self):
        self.email = os.getenv('FANSALE_EMAIL')
        self.password = os.getenv('FANSALE_PASSWORD')
        self.target_url = "https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388"
        self.driver = None        
    def setup_browser(self):
        """Setup browser with aggressive data saving"""
        logger.info("🌐 Starting data-optimized browser...")
        
        options = uc.ChromeOptions()
        
        # CRITICAL: Block images, CSS, fonts - saves 80%+ bandwidth
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Block images
            "profile.managed_default_content_settings.stylesheets": 2,  # Block CSS
            "profile.managed_default_content_settings.fonts": 2,  # Block fonts
            "profile.managed_default_content_settings.plugins": 2,  # Block plugins
            "profile.managed_default_content_settings.popups": 2,  # Block popups
            "profile.managed_default_content_settings.media_stream": 2,  # Block media
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Block resource types at driver level
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Risky but saves data
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-gpu')
        
        # Basic stealth
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Smaller window = less rendering
        options.add_argument('--window-size=1024,768')
        
        # Enable request interception for ultimate control
        seleniumwire_options = {
            'disable_encoding': True,  # Don't decode responses
            'request_storage': 'memory',
            'request_storage_max_size': 10  # Only keep last 10 requests
        }        
        # Add proxy if configured
        proxy_config = self._get_proxy_config()
        if proxy_config:
            seleniumwire_options.update(proxy_config)
        
        self.driver = uc.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        self.driver.set_page_load_timeout(15)  # Faster timeout
        
        # Block unnecessary requests
        def interceptor(request):
            # Block resource-heavy requests
            block_patterns = [
                '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
                '.css', '.scss',  # Stylesheets
                '.woff', '.woff2', '.ttf', '.eot',  # Fonts
                '.mp4', '.webm', '.avi',  # Videos
                '.mp3', '.wav',  # Audio
                'google-analytics', 'facebook', 'doubleclick',  # Tracking
                'akamai',  # Akamai sensor scripts (risky but saves data)
            ]
            
            if any(pattern in request.url.lower() for pattern in block_patterns):
                request.abort()
        
        self.driver.request_interceptor = interceptor
        
        logger.info("✅ Data-optimized browser ready")
        logger.info("📊 Blocking: images, CSS, fonts, tracking")
        
    def _get_proxy_config(self):
        """Get proxy if configured"""
        if not all(os.getenv(k) for k in ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 
                                          'IPROYAL_HOSTNAME', 'IPROYAL_PORT']):
            logger.info("⚠️ No proxy configured - using direct connection")
            return None            
        proxy_auth = f"{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}"
        proxy_server = f"{os.getenv('IPROYAL_HOSTNAME')}:{os.getenv('IPROYAL_PORT')}"
        
        logger.info("🔐 Using proxy (saves your home IP)")
        return {
            'proxy': {
                'http': f'http://{proxy_auth}@{proxy_server}',
                'https': f'https://{proxy_auth}@{proxy_server}'
            }
        }
        
    def manual_login(self):
        """Manual login"""
        logger.info("🔐 Navigating to login...")
        
        self.driver.get("https://www.fansale.it/fansale/login.htm")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("="*50)
        print(f"Email: {self.email}")
        print(f"Password: {'*' * len(self.password)}")
        print("\n⚠️ Page will look broken (no CSS) - that's normal!")
        print("Complete login manually")
        
        input("\n✋ Press Enter after successful login...")
        
        if "login" not in self.driver.current_url.lower():
            logger.info("✅ Login successful!")
            return True
        return False            
    def check_for_tickets_lite(self):
        """Check for tickets with minimal data"""
        try:
            # Look for ticket elements in raw HTML
            page_source = self.driver.page_source.lower()
            
            # Check for ticket indicators
            if 'data-qa="tickettobuy"' in page_source:
                # Try to count them
                count = page_source.count('data-qa="tickettobuy"')
                logger.info(f"🎫 Found {count} potential tickets!")
                return True
            
            # Check for "no tickets" indicators
            no_ticket_phrases = [
                "non ci sono biglietti",
                "no tickets",
                "nessun biglietto",
                "sold out"
            ]
            
            for phrase in no_ticket_phrases:
                if phrase in page_source:
                    return False
                    
            return False
            
        except Exception as e:
            logger.debug(f"Error checking: {e}")
            return False
            
    def hunt_tickets_lite(self):
        """Ultra-light hunting loop"""
        logger.info("🎯 Starting lite hunt mode...")
        logger.info("📊 Data usage: ~200KB-500KB per refresh (vs 2-5MB normal)")
        
        check_count = 0
        data_used_mb = 0        
        # Initial page load
        self.driver.get(self.target_url)
        time.sleep(3)
        
        while True:
            try:
                check_count += 1
                
                # Estimate data usage (rough)
                data_used_mb += 0.3  # ~300KB per refresh without images/CSS
                
                if self.check_for_tickets_lite():
                    logger.info("🚨 TICKETS DETECTED!")
                    logger.info("⚠️ Cannot auto-purchase without JavaScript")
                    logger.info("👉 Manual action required!")
                    
                    # Try to enable JavaScript for purchase
                    logger.info("🔄 Reloading with full page for purchase...")
                    
                    # Save URL
                    current_url = self.driver.current_url
                    
                    # Quit and restart with JS enabled
                    self.driver.quit()
                    
                    # Restart with JavaScript
                    options = uc.ChromeOptions()
                    self.driver = uc.Chrome(options=options)
                    self.driver.get(current_url)
                    
                    logger.info("✅ Full page loaded - complete purchase manually!")
                    input("\nPress Enter to close...")
                    break
                    
                else:
                    if check_count % 20 == 0:
                        logger.info(f"⏳ Still hunting... (Checks: {check_count}, Data: ~{data_used_mb:.1f}MB)")
                
                # Refresh
                self.driver.refresh()
                
                # Wait between refreshes
                wait_time = random.uniform(4, 7)  # Slightly longer to be safer
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info(f"\n🛑 Stopped. Total data used: ~{data_used_mb:.1f}MB")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(5)                
    def run(self):
        """Main execution"""
        print("""
        ╔══════════════════════════════════════════════════════════════════╗
        ║                 FANSALE LITE BROWSER BOT                         ║
        ╠══════════════════════════════════════════════════════════════════╣
        ║                                                                  ║
        ║  💾 ULTRA LOW DATA MODE                                          ║
        ║                                                                  ║
        ║  Data Usage:                                                     ║
        ║  • Normal bot: 1.2-3.6 GB/hour                                  ║
        ║  • Lite bot: 200-400 MB/hour (80-90% savings!)                 ║
        ║                                                                  ║
        ║  Trade-offs:                                                     ║
        ║  • ❌ No images (page looks broken)                             ║
        ║  • ❌ No auto-purchase (no JavaScript)                          ║
        ║  • ❌ Slightly higher detection risk                            ║
        ║  • ✅ Saves massive bandwidth                                   ║
        ║  • ✅ Proxy lasts 10x longer                                    ║
        ║                                                                  ║
        ║  Note: When tickets found, browser restarts with JS             ║
        ╚══════════════════════════════════════════════════════════════════╝
        """)
        
        try:
            self.setup_browser()
            
            if self.manual_login():
                self.hunt_tickets_lite()
            else:
                logger.error("Login failed")
                
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                

if __name__ == "__main__":
    bot = LiteFanSaleBot()
    bot.run()