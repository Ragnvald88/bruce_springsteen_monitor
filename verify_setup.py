#!/usr/bin/env python3
"""
🎸 Bruce Springsteen Ticket Hunter - Setup Verification
StealthMaster AI Diagnostic Tool

Run this script to verify your system setup before starting the main bot.
"""

import os
import sys
import yaml
from pathlib import Path
import asyncio
from dotenv import load_dotenv

def print_header():
    print("="*80)
    print("🎸 BRUCE SPRINGSTEEN TICKET HUNTER - SETUP VERIFICATION 🎸")
    print("="*80)

def check_env_file():
    """Check .env file and credentials"""
    print("\n🔐 CHECKING CREDENTIALS...")
    
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    if not env_path.exists():
        print("❌ .env file not found!")
        if env_example_path.exists():
            print("💡 Copy .env.example to .env and fill in your credentials")
        else:
            print("💡 Create a .env file with your FanSale credentials")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check FanSale credentials
    email = os.getenv('FANSALE_EMAIL')
    password = os.getenv('FANSALE_PASSWORD')
    
    if not email:
        print("❌ FANSALE_EMAIL not set in .env")
        return False
    elif '@' not in email:
        print("⚠️  FANSALE_EMAIL format looks invalid")
        return False
    else:
        print(f"✅ FANSALE_EMAIL: {email[:3]}***@{email.split('@')[1] if '@' in email else '???'}")
    
    if not password:
        print("❌ FANSALE_PASSWORD not set in .env")
        return False
    elif len(password) < 6:
        print("⚠️  FANSALE_PASSWORD seems too short")
        return False
    else:
        print(f"✅ FANSALE_PASSWORD: {'*' * len(password)} ({len(password)} chars)")
    
    # Check proxy settings (optional)
    proxy_host = os.getenv('IPROYAL_HOSTNAME')
    if proxy_host:
        print(f"✅ PROXY CONFIGURED: {proxy_host}")
    else:
        print("⚠️  No proxy configured (optional)")
    
    return True

def check_config_file():
    """Check config.yaml settings"""
    print("\n⚙️  CHECKING CONFIGURATION...")
    
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        print("❌ config/config.yaml not found!")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check browser settings
        browser_opts = config.get('browser_options', {})
        headless = browser_opts.get('headless', True)
        
        if headless:
            print("⚠️  BROWSERS WILL BE HIDDEN (headless: true)")
            print("   💡 Change to 'headless: false' to see browsers")
        else:
            print("✅ BROWSERS WILL BE VISIBLE (headless: false)")
        
        # Check authentication
        auth = config.get('authentication', {})
        auth_enabled = auth.get('enabled', False)
        
        if auth_enabled:
            print("✅ AUTHENTICATION ENABLED")
            fansale_auth = auth.get('platforms', {}).get('fansale')
            if fansale_auth:
                print("✅ FanSale authentication configured")
            else:
                print("❌ FanSale authentication not configured")
        else:
            print("❌ AUTHENTICATION DISABLED")
            print("   💡 Change 'enabled: true' in authentication section")
        
        # Check targets
        targets = config.get('targets', [])
        enabled_targets = [t for t in targets if t.get('enabled')]
        
        if enabled_targets:
            print(f"✅ {len(enabled_targets)} ACTIVE TARGETS:")
            for target in enabled_targets:
                platform = target.get('platform', 'unknown')
                event = target.get('event_name', 'Unknown Event')
                print(f"   🎯 {platform}: {event}")
        else:
            print("❌ NO ACTIVE TARGETS")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def check_dependencies():
    """Check required Python packages"""
    print("\n📦 CHECKING DEPENDENCIES...")
    
    required_packages = [
        'asyncio', 'yaml', 'playwright', 'httpx', 'dotenv', 
        'logging', 'numpy', 'scipy', 'aiofiles'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'yaml':
                import yaml
            elif package == 'dotenv':
                from dotenv import load_dotenv
            elif package == 'httpx':
                import httpx
            elif package == 'numpy':
                import numpy
            elif package == 'scipy':
                import scipy
            elif package == 'aiofiles':
                import aiofiles
            elif package == 'playwright':
                import playwright
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n💡 Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

async def test_browser_launch():
    """Test browser launching"""
    print("\n🌐 TESTING BROWSER LAUNCH...")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            print("   🚀 Launching test browser...")
            browser = await p.chromium.launch(
                headless=False,  # Force visible for test
                args=["--start-maximized"]
            )
            
            print("   📄 Creating test page...")
            page = await browser.new_page()
            
            print("   🌍 Testing navigation...")
            await page.goto("https://www.google.com")
            await page.wait_for_load_state('networkidle')
            
            title = await page.title()
            print(f"   ✅ Page loaded: {title}")
            
            print("   🔄 Closing test browser...")
            await browser.close()
            
            print("✅ BROWSER TEST SUCCESSFUL!")
            return True
            
    except Exception as e:
        print(f"❌ BROWSER TEST FAILED: {e}")
        print("💡 Try: playwright install chromium")
        return False

def print_summary(env_ok, config_ok, deps_ok, browser_ok):
    """Print final summary"""
    print("\n" + "="*80)
    print("📊 SETUP VERIFICATION SUMMARY")
    print("="*80)
    
    all_ok = all([env_ok, config_ok, deps_ok, browser_ok])
    
    status_icon = "✅" if all_ok else "❌"
    print(f"{status_icon} CREDENTIALS:    {'OK' if env_ok else 'ISSUES'}")
    print(f"{status_icon} CONFIGURATION: {'OK' if config_ok else 'ISSUES'}")
    print(f"{status_icon} DEPENDENCIES:  {'OK' if deps_ok else 'ISSUES'}")
    print(f"{status_icon} BROWSER TEST:  {'OK' if browser_ok else 'ISSUES'}")
    
    print("="*80)
    
    if all_ok:
        print("🎉 SYSTEM READY FOR BRUCE SPRINGSTEEN TICKET HUNTING!")
        print("🚀 Run: python src/main.py")
    else:
        print("⚠️  PLEASE FIX THE ISSUES ABOVE BEFORE STARTING")
        print("💡 Run this script again after making changes")
    
    print("="*80)

async def main():
    """Main verification function"""
    print_header()
    
    env_ok = check_env_file()
    config_ok = check_config_file()
    deps_ok = check_dependencies()
    browser_ok = await test_browser_launch()
    
    print_summary(env_ok, config_ok, deps_ok, browser_ok)

if __name__ == "__main__":
    asyncio.run(main())