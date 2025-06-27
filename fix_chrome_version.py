#!/usr/bin/env python3
"""
Fix Chrome version mismatch for FanSale Bot
"""

import subprocess
import sys
import os

def get_chrome_version():
    """Get installed Chrome version"""
    try:
        # macOS
        result = subprocess.run(
            ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            version = result.stdout.strip().split()[-1]
            return version
    except:
        pass
    
    try:
        # Try alternative method
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip().split()[-1]
            return version
    except:
        pass
    
    return None

def main():
    print("🔧 Chrome Version Fix Tool")
    print("="*50)
    
    # 1. Check Chrome version
    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"✅ Chrome version detected: {chrome_version}")
        major_version = chrome_version.split('.')[0]
        print(f"   Major version: {major_version}")
    else:
        print("❌ Could not detect Chrome version")
        print("   Make sure Google Chrome is installed")
        return
    
    # 2. Fix options
    print("\n📋 Fix Options:")
    print("1. Update undetected-chromedriver (recommended)")
    print("2. Modify bot to use auto-detect version")
    print("3. Force specific Chrome version")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        print("\n🔄 Updating undetected-chromedriver...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "undetected-chromedriver"])
        print("✅ Updated! Try running the bot again.")
        
    elif choice == "2":
        print("\n📝 The bot already uses version_main=None for auto-detection.")
        print("   This error suggests ChromeDriver needs updating.")
        print("\n🔧 Quick fix - run these commands:")
        print("   pip uninstall undetected-chromedriver")
        print("   pip install undetected-chromedriver")
        
    elif choice == "3":
        print(f"\n📝 To force Chrome version {major_version}, modify fansale_v7_ultimate.py:")
        print(f"   Change: version_main=None")
        print(f"   To:     version_main={major_version}")
        print("\n⚠️  Note: Auto-detection (None) is usually better")
    
    # 3. Additional fixes
    print("\n🔧 Additional Troubleshooting:")
    print("1. Clear ChromeDriver cache:")
    print("   rm -rf ~/.wdm")
    print("   rm -rf ~/Library/Caches/undetected_chromedriver")
    print("\n2. Install specific ChromeDriver version:")
    print(f"   pip install undetected-chromedriver")
    print("\n3. Use Selenium Manager (fallback):")
    print("   pip install selenium --upgrade")

if __name__ == "__main__":
    main()