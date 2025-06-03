# src/utils/improved_profile_test.py
import asyncio
import sys
import os
import json
from datetime import datetime

# Corrected sys.path.append
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_profile_rotation():
    """Test that profiles are actually rotating"""
    print("🔄 Testing Profile Rotation")
    print("-" * 60)
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            profiles_used = []
            
            # Test 5 context creations
            for i in range(5):
                async with manager.get_context() as (context, profile):
                    profiles_used.append(profile.name)
                    print(f"  Context {i+1}: {profile.name}")
                    
                    # Quick test
                    page = await context.new_page()
                    
                    # Use a simple test page
                    try:
                        await page.goto('https://www.example.com', timeout=10000)
                        print(f"    ✅ Page loaded successfully")
                    except Exception as e:
                        print(f"    ❌ Error: {e}")
                    
                    await page.close()
            
            # Check diversity
            unique_profiles = set(profiles_used)
            print(f"\n  Summary:")
            print(f"  Total contexts: {len(profiles_used)}")
            print(f"  Unique profiles: {len(unique_profiles)}")
            print(f"  Profiles: {', '.join(unique_profiles)}")
            
            if len(unique_profiles) == 1:
                print("  ⚠️  WARNING: Only one profile is being used!")
                
        finally:
            await manager.stop_manager()

async def test_stealth_injection():
    """Test if stealth scripts are being injected properly"""
    print("\n🛡️  Testing Stealth Injection")
    print("-" * 60)
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            async with manager.get_context() as (context, profile):
                print(f"  Profile: {profile.name}")
                
                page = await context.new_page()
                
                # Navigate to a simple page
                await page.goto('data:text/html,<html><body>Test</body></html>')
                
                # Check stealth properties
                stealth_checks = await page.evaluate("""
                    () => {
                        return {
                            webdriver: navigator.webdriver,
                            chrome: !!window.chrome,
                            chrome_runtime: !!(window.chrome && window.chrome.runtime),
                            fingerprint_profile: !!window.__fingerprint_profile__,
                            stealth_level: window.__STEALTH_LEVEL__,
                            user_agent: navigator.userAgent,
                            languages: navigator.languages,
                            platform: navigator.platform,
                            vendor: navigator.vendor,
                            plugins_length: navigator.plugins.length,
                            permissions_query: typeof navigator.permissions?.query
                        };
                    }
                """)
                
                print("\n  Stealth check results:")
                for key, value in stealth_checks.items():
                    status = "✅" if key in ['chrome', 'fingerprint_profile'] or (key == 'webdriver' and value == False) else "ℹ️"
                    print(f"    {status} {key}: {value}")
                
                # Check if profile was injected
                if stealth_checks.get('fingerprint_profile'):
                    print("    ✅ Profile data injected successfully")
                else:
                    print("    ❌ Profile data NOT injected!")
                
                await page.close()
                
        finally:
            await manager.stop_manager()

async def test_simple_ticketmaster():
    """Simple Ticketmaster test with minimal wait"""
    print("\n🎫 Simple Ticketmaster Test")
    print("-" * 60)
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Try with headful mode to see what's happening
    config['browser_launch_options']['headless'] = False
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            async with manager.get_context() as (context, profile):
                print(f"  Profile: {profile.name}")
                
                page = await context.new_page()
                
                # Listen for responses
                queue_detected = False
                def check_response(response):
                    nonlocal queue_detected
                    if 'queue' in response.url:
                        queue_detected = True
                        print(f"  ⚠️  Queue redirect detected: {response.url[:80]}...")
                
                page.on('response', check_response)
                
                print("  Navigating to Ticketmaster...")
                try:
                    response = await page.goto(
                        'https://www.ticketmaster.nl',
                        wait_until='commit',  # Don't wait for full load
                        timeout=15000
                    )
                    
                    print(f"  Initial response: {response.status}")
                    
                    # Quick wait
                    await page.wait_for_timeout(2000)
                    
                    current_url = page.url
                    print(f"  Current URL: {current_url[:80]}...")
                    
                    if 'queue' in current_url or queue_detected:
                        print("  ❌ BLOCKED: Sent to queue")
                    else:
                        print("  ✅ Not immediately blocked")
                        
                        # Try to find search box quickly
                        try:
                            search = await page.wait_for_selector('input[type="search"], input[name="search"]', timeout=3000)
                            if search:
                                print("  ✅ Found search box - site appears accessible")
                        except:
                            print("  ⚠️  Could not find search box")
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                
                print("\n  Press Enter to close browser...")
                input()
                
                await page.close()
                
        finally:
            await manager.stop_manager()

async def main():
    """Run all tests"""
    print("=" * 80)
    print("IMPROVED PROFILE AND STEALTH TESTING")
    print("=" * 80)
    print(f"Started at: {datetime.now()}\n")
    
    # Test 1: Profile rotation
    await test_profile_rotation()
    
    # Test 2: Stealth injection
    await test_stealth_injection()
    
    # Test 3: Simple Ticketmaster test
    print("\nRun Ticketmaster test? (y/n): ", end='')
    if input().lower() == 'y':
        await test_simple_ticketmaster()
    
    print("\n" + "=" * 80)
    print("Testing completed!")

if __name__ == "__main__":
    asyncio.run(main())