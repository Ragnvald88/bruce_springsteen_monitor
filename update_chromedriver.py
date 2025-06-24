#!/usr/bin/env python3
"""
ChromeDriver Update Helper
Fixes version mismatch between Chrome browser and ChromeDriver
"""

import subprocess
import sys
import os

def update_chromedriver():
    """Update ChromeDriver to match installed Chrome version"""
    print("🔧 ChromeDriver Update Helper")
    print("=" * 50)
    
    # Check Chrome version
    try:
        if sys.platform == "darwin":  # macOS
            result = subprocess.run(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                capture_output=True, text=True
            )
        elif sys.platform == "win32":  # Windows
            result = subprocess.run(
                ["chrome", "--version"],
                capture_output=True, text=True
            )
        else:  # Linux
            result = subprocess.run(
                ["google-chrome", "--version"],
                capture_output=True, text=True
            )
        
        if result.returncode == 0:
            chrome_version = result.stdout.strip()
            print(f"✅ Found Chrome: {chrome_version}")
            
            # Extract major version
            major_version = chrome_version.split()[2].split('.')[0]
            print(f"📌 Chrome major version: {major_version}")
        else:
            print("❌ Could not detect Chrome version")
            return False
            
    except Exception as e:
        print(f"❌ Error detecting Chrome: {e}")
        return False
    
    # Update undetected-chromedriver
    print("\n🔄 Updating undetected-chromedriver...")
    try:
        # Uninstall current version
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "undetected-chromedriver"], 
                      capture_output=True)
        
        # Install latest version
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "undetected-chromedriver"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ Successfully updated undetected-chromedriver")
            
            # Clear any cached drivers
            cache_dir = os.path.expanduser("~/.cache/selenium")
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir)
                print("🧹 Cleared ChromeDriver cache")
            
            return True
        else:
            print(f"❌ Failed to update: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Update error: {e}")
        return False

def main():
    """Main function"""
    success = update_chromedriver()
    
    if success:
        print("\n✅ ChromeDriver update complete!")
        print("🎯 You can now run: python fansale_no_login.py")
    else:
        print("\n❌ Update failed. Please try manually:")
        print("1. pip uninstall undetected-chromedriver")
        print("2. pip install --upgrade undetected-chromedriver")
        print("3. Clear cache: rm -rf ~/.cache/selenium")

if __name__ == "__main__":
    main()