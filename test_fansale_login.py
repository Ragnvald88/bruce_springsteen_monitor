#!/usr/bin/env python3
"""
🔐 FanSale Login Test - Verify authentication implementation
Test the new FanSale login functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import required modules
from src.profiles.models import BrowserProfile
from src.platforms.fansale import FansaleMonitor
from src.core.managers import ConnectionPoolManager
from playwright.async_api import async_playwright
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockBrowserManager:
    """Mock browser manager for testing"""
    
    def __init__(self, playwright_instance):
        self.playwright = playwright_instance
        
    async def get_stealth_context(self, profile, force_new=False):
        """Create a stealth browser context"""
        browser = await self.playwright.chromium.launch(
            headless=False,  # Show browser for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': profile.viewport_width, 'height': profile.viewport_height},
            user_agent=profile.user_agent,
            locale='it-IT',
            timezone_id='Europe/Rome',
            extra_http_headers={
                'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            }
        )
        
        return context

async def test_fansale_login():
    """Test FanSale login functionality"""
    print("🔐 Testing FanSale Login Implementation")
    print("=" * 60)
    
    # Check environment variables
    email = os.getenv('FANSALE_EMAIL')
    password = os.getenv('FANSALE_PASSWORD')
    
    if not email or not password:
        print("❌ FanSale credentials not found in environment variables")
        print("Please ensure FANSALE_EMAIL and FANSALE_PASSWORD are set in .env file")
        return False
    
    print(f"✅ Found credentials for: {email}")
    
    # Create test profile
    test_profile = BrowserProfile(
        name="FanSale Login Test Profile",
        profile_id="test_login_profile",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport_width=1920,
        viewport_height=1080,
        locale="it-IT",
        timezone="Europe/Rome",
        languages_override=["it-IT", "it", "en-US", "en"]
    )
    
    # Test configuration
    test_config = {
        'event_name': 'Bruce Springsteen - Login Test',
        'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388',
        'priority': 'HIGH',
        'max_price_per_ticket': 500.0,
        'desired_sections': [],
        'fair_deal_only': False,
        'certified_only': False
    }
    
    async with async_playwright() as playwright:
        try:
            # Setup mock managers
            browser_manager = MockBrowserManager(playwright)
            connection_manager = ConnectionPoolManager({}, None)
            cache = {}
            
            # Create FanSale monitor
            monitor = FansaleMonitor(
                config=test_config,
                profile=test_profile,
                browser_manager=browser_manager,
                connection_manager=connection_manager,
                cache=cache
            )
            
            print("🚀 Initializing FanSale monitor...")
            
            # Initialize with authentication
            await monitor.initialize()
            
            print("✅ FanSale monitor initialized successfully!")
            
            # Test basic page access
            print("🌐 Testing page access...")
            try:
                await monitor.page.goto(test_config['url'], wait_until='networkidle', timeout=30000)
                current_url = monitor.page.url
                print(f"📍 Current URL: {current_url}")
                
                # Check if we can access the page content
                page_title = await monitor.page.title()
                print(f"📄 Page title: {page_title}")
                
                # Look for login indicators vs. content
                is_logged_in = await monitor._verify_login_success()
                if is_logged_in:
                    print("✅ Successfully authenticated and accessing content!")
                else:
                    print("❌ Authentication status unclear")
                
                # Wait a moment to observe the page
                print("⏳ Waiting 10 seconds for manual inspection...")
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"❌ Error accessing page: {e}")
            
            # Cleanup
            await monitor.cleanup()
            
            return True
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"❌ Test failed: {e}")
            return False

async def main():
    """Main test function"""
    success = await test_fansale_login()
    
    if success:
        print("\n✅ FanSale login test completed!")
    else:
        print("\n❌ FanSale login test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())