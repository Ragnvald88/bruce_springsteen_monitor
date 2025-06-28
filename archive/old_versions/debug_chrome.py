#!/usr/bin/env python3
"""Debug Chrome/ChromeDriver issues"""

import subprocess
import sys
import os
from pathlib import Path

print("🔍 Chrome/ChromeDriver Debugging")
print("="*60)

# 1. Check Chrome installation
print("\n1. Chrome Installation:")
chrome_paths = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

chrome_found = None
for path in chrome_paths:
    if Path(path).exists():
        chrome_found = path
        print(f"✅ Found: {path}")
        
        # Get version
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            version = result.stdout.strip()
            print(f"   Version: {version}")
        except:
            print("   Could not get version")
        break

if not chrome_found:
    print("❌ Chrome not found!")

# 2. Check ChromeDriver
print("\n2. ChromeDriver Check:")
try:
    result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ System ChromeDriver: {result.stdout.strip()}")
        
        # Get version
        try:
            version_result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
            print(f"   Version: {version_result.stdout.strip()}")
        except:
            pass
    else:
        print("ℹ️  No system ChromeDriver (undetected-chromedriver will download)")
except:
    pass

# 3. Check Python packages
print("\n3. Python Packages:")
try:
    import selenium
    print(f"✅ selenium: {selenium.__version__}")
except ImportError:
    print("❌ selenium not installed")

try:
    import undetected_chromedriver as uc
    print(f"✅ undetected-chromedriver: {uc.__version__}")
except ImportError:
    print("❌ undetected-chromedriver not installed")

# 4. Check for Chrome processes
print("\n4. Running Chrome Processes:")
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    chrome_processes = [line for line in result.stdout.split('\n') if 'Chrome' in line and 'grep' not in line]
    if chrome_processes:
        print(f"⚠️  Found {len(chrome_processes)} Chrome processes running")
        print("   Run: pkill -f 'Google Chrome' to clean up")
    else:
        print("✅ No Chrome processes running")
except:
    pass

# 5. Test minimal Chrome startup
print("\n5. Testing Minimal Chrome Startup:")
try:
    import undetected_chromedriver as uc
    
    # Minimal options
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("   Creating driver...")
    driver = uc.Chrome(options=options, version_main=137)
    print("✅ SUCCESS: Driver created")
    
    driver.quit()
    print("✅ Driver closed successfully")
    
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")
    
    # Check error details
    error_str = str(e)
    if "version" in error_str.lower():
        print("\n   Version mismatch detected!")
        print("   Try: pip install --upgrade undetected-chromedriver")
    elif "permission" in error_str.lower():
        print("\n   Permission issue detected!")
        print("   Try: sudo chmod +x on chromedriver")
    elif "cannot find" in error_str.lower():
        print("\n   Chrome not found!")
        print("   Install Chrome from: https://www.google.com/chrome/")

print("\n" + "="*60)
print("Recommendations:")
print("1. Update Chrome to latest stable version")
print("2. pip install --upgrade undetected-chromedriver selenium")
print("3. Clear browser profiles: rm -rf browser_profiles/")
print("4. Kill any stale Chrome: pkill -f 'Google Chrome'")