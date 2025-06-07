# src/utils/verify_fixes.py
import asyncio
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment setup"""
    print("🔍 Checking Environment")
    print("-" * 60)
    
    # Check proxy environment variables
    proxy_user = os.getenv('PROXY_USER')
    proxy_pass = os.getenv('PROXY_PASS')
    
    if proxy_user and proxy_pass:
        print(f"  ✅ PROXY_USER is set: {proxy_user[:3]}***")
        print(f"  ✅ PROXY_PASS is set: ***")
    else:
        print("  ❌ Proxy credentials not found in environment")
        print("  To set them:")
        print("    export PROXY_USER=your_username")
        print("    export PROXY_PASS=your_password")
    
    # Check config file
    if os.path.exists('config/config.yaml'):
        print("  ✅ Config file found")
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            proxy_enabled = config.get('proxy', {}).get('enabled', False)
            print(f"  ℹ️  Proxy enabled in config: {proxy_enabled}")
    else:
        print("  ❌ Config file not found")
    
    return proxy_user and proxy_pass

async def test_without_proxy():
    """Test browser without proxy first"""
    print("\n🌐 Testing Without Proxy")
    print("-" * 60)
    
    # Load config and disable proxy
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['proxy']['enabled'] = False
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            # Test basic connectivity
            async with manager.get_context() as (context, profile):
                print(f"  Profile: {profile.name}")
                
                page = await context.new_page()
                
                # Test simple page
                try:
                    await page.goto('https://httpbin.org/ip', timeout=10000)
                    ip_data = await page.text_content('body')
                    print(f"  ✅ Connected without proxy")
                    print(f"  Your IP: {ip_data[:50]}...")
                except Exception as e:
                    print(f"  ❌ Failed to connect: {e}")
                
                await page.close()
                
        finally:
            await manager.stop_manager()

async def test_profile_diversity():
    """Test that profiles are rotating properly"""
    print("\n🔄 Testing Profile Diversity")
    print("-" * 60)
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Disable proxy for this test
    config['proxy']['enabled'] = False
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            profile_usage = {}
            
            # Create 10 contexts to test rotation
            for i in range(10):
                async with manager.get_context() as (context, profile):
                    profile_name = profile.name
                    profile_usage[profile_name] = profile_usage.get(profile_name, 0) + 1
                    print(f"  Context {i+1}: {profile_name}")
                    
                    # Quick delay to simulate usage
                    await asyncio.sleep(0.5)
            
            print(f"\n  Profile usage summary:")
            for profile_name, count in profile_usage.items():
                print(f"    {profile_name}: {count} times")
            
            if len(profile_usage) > 1:
                print("  ✅ Profile rotation is working!")
            else:
                print("  ❌ Only one profile was used")
                
        finally:
            await manager.stop_manager()

async def test_stealth_injection():
    """Test that stealth data is properly injected"""
    print("\n🛡️  Testing Stealth Injection")
    print("-" * 60)
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['proxy']['enabled'] = False
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            async with manager.get_context() as (context, profile):
                print(f"  Testing profile: {profile.name}")
                
                page = await context.new_page()
                
                # Navigate to a blank page
                await page.goto('data:text/html,<html><body>Test Page</body></html>')
                
                # Check injected data
                injected_data = await page.evaluate("""
                    () => {
                        return {
                            has_profile: typeof window.__fingerprint_profile__ !== 'undefined',
                            profile_name: window.__fingerprint_profile__ ? window.__fingerprint_profile__.name : null,
                            stealth_level: window.__STEALTH_LEVEL__,
                            webdriver: navigator.webdriver,
                            user_agent: navigator.userAgent,
                            platform: navigator.platform,
                            languages: navigator.languages
                        };
                    }
                """)
                
                print("\n  Injection results:")
                print(f"    Profile injected: {injected_data['has_profile']}")
                print(f"    Profile name: {injected_data['profile_name']}")
                print(f"    Stealth level: {injected_data['stealth_level']}")
                print(f"    Webdriver: {injected_data['webdriver']}")
                print(f"    User agent matches: {injected_data['user_agent'] == profile.user_agent}")
                print(f"    Platform matches: {injected_data['platform'] == profile.js_platform}")
                
                if injected_data['has_profile'] and injected_data['profile_name'] == profile.name:
                    print("\n  ✅ Stealth injection is working!")
                else:
                    print("\n  ❌ Stealth injection failed")
                
                await page.close()
                
        finally:
            await manager.stop_manager()

async def test_ticketmaster_quick():
    """Quick Ticketmaster test"""
    print("\n🎫 Quick Ticketmaster Test")
    print("-" * 60)
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Test without proxy first
    config['proxy']['enabled'] = False
    
    async with async_playwright() as p:
        from src.core.browser_manager import StealthBrowserManager
        
        manager = StealthBrowserManager(config, p)
        await manager.start_manager()
        
        try:
            async with manager.get_context() as (context, profile):
                print(f"  Profile: {profile.name}")
                print(f"  User Agent: {profile.user_agent[:50]}...")
                
                page = await context.new_page()
                
                print("  Navigating to Ticketmaster...")
                try:
                    # Use domcontentloaded instead of networkidle
                    response = await page.goto(
                        'https://www.ticketmaster.nl',
                        wait_until='domcontentloaded',
                        timeout=20000
                    )
                    
                    print(f"  Initial response: {response.status}")
                    
                    # Wait a bit
                    await page.wait_for_timeout(3000)
                    
                    # Check URL
                    current_url = page.url
                    print(f"  Current URL: {current_url[:80]}...")
                    
                    if 'queue' in current_url:
                        print("  ❌ Sent to queue (bot detected)")
                    else:
                        print("  ✅ Not immediately queued")
                        
                        # Check for Akamai
                        cookies = await context.cookies()
                        akamai_cookies = [c for c in cookies if '_abck' in c['name'] or 'bm_' in c['name']]
                        if akamai_cookies:
                            print(f"  ⚠️  Akamai cookies found: {len(akamai_cookies)}")
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                
                await page.close()
                
        finally:
            await manager.stop_manager()

async def main():
    """Run all verification tests"""
    print("=" * 80)
    print("BROWSER MANAGER FIX VERIFICATION")
    print("=" * 80)
    print(f"Started at: {datetime.now()}\n")
    
    # Check environment
    has_proxy_creds = check_environment()
    
    # Test without proxy first
    await test_without_proxy()
    
    # Test profile diversity
    await test_profile_diversity()
    
    # Test stealth injection
    await test_stealth_injection()
    
    # Quick Ticketmaster test
    print("\nTest Ticketmaster? (y/n): ", end='')
    if input().lower() == 'y':
        await test_ticketmaster_quick()
    
    print("\n" + "=" * 80)
    print("Verification completed!")
    
    if not has_proxy_creds:
        print("\n⚠️  Remember to set proxy credentials if you need proxy support:")
        print("  export PROXY_USER=your_username")
        print("  export PROXY_PASS=your_password")

if __name__ == "__main__":
    asyncio.run(main())