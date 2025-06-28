#!/usr/bin/env python3
"""
Debug script for FanSale Bot V6
Checks environment and configuration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

print("🔍 FanSale Bot V6 - Debug Check")
print("=" * 50)

# Check Python version
print(f"\n📌 Python Version: {sys.version}")

# Check current directory
print(f"\n📁 Current Directory: {os.getcwd()}")

# Check for .env file
env_path = Path(".env")
print(f"\n🔍 Checking for .env file at: {env_path.absolute()}")
if env_path.exists():
    print("✅ .env file found!")
    
    # Load and check environment
    load_dotenv()
    fansale_url = os.getenv('FANSALE_URL')
    twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY')
    
    print(f"\n📋 Environment Variables:")
    print(f"   FANSALE_URL: {'✅ Set' if fansale_url else '❌ Not set'}")
    if fansale_url:
        print(f"   URL: {fansale_url[:50]}...")
    print(f"   TWOCAPTCHA_API_KEY: {'✅ Set' if twocaptcha_key else '⚠️ Not set (optional)'}")
    
    # Check .env content
    print(f"\n📄 .env file content:")
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key = line.split('=')[0]
                    print(f"   {key}=***")
else:
    print("❌ .env file NOT found!")
    print("\n💡 Create .env file with:")
    print("   FANSALE_URL=https://www.fansale.it/fansale/tickets/...")
    print("   TWOCAPTCHA_API_KEY=your_api_key_here (optional)")

# Check for config file
config_path = Path("bot_config_v6.json")
print(f"\n🔍 Checking for config file at: {config_path.absolute()}")
if config_path.exists():
    print("✅ Config file found!")
else:
    print("❌ Config file NOT found!")

# Check dependencies
print("\n📦 Checking dependencies:")
try:
    import selenium
    print(f"✅ selenium: {selenium.__version__}")
except ImportError:
    print("❌ selenium not installed")

try:
    import undetected_chromedriver
    print(f"✅ undetected-chromedriver: installed")
except ImportError:
    print("❌ undetected-chromedriver not installed")

try:
    from twocaptcha import TwoCaptcha
    print(f"✅ 2captcha-python: installed")
except ImportError:
    print("⚠️ 2captcha-python not installed (optional)")

try:
    import numpy
    print(f"✅ numpy: {numpy.__version__}")
except ImportError:
    print("⚠️ numpy not installed (optional, for mouse simulation)")

# Check Chrome/Chromium
print("\n🌐 Checking browser:")
chrome_paths = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
]

chrome_found = False
for path in chrome_paths:
    if Path(path).exists():
        print(f"✅ Chrome/Chromium found at: {path}")
        chrome_found = True
        break

if not chrome_found:
    print("⚠️ Chrome/Chromium not found in standard locations")
    print("   undetected-chromedriver will try to auto-download")

print("\n" + "=" * 50)
print("✨ Debug check complete!")
