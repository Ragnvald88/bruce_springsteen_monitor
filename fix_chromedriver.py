#!/usr/bin/env python3
"""
ChromeDriver Version Fixer
Ensures ChromeDriver matches installed Chrome version
"""

import subprocess
import sys
import os
import shutil
import platform
from pathlib import Path

def get_chrome_version():
    """Get installed Chrome version"""
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
            version = result.stdout.strip()
            major_version = int(version.split()[2].split('.')[0])
            return major_version
    except:
        pass
    return None

def fix_chromedriver_version():
    """Fix ChromeDriver version to match Chrome"""
    print("🔧 ChromeDriver Version Fixer")
    print("=" * 50)
    
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("❌ Could not detect Chrome version")
        return False
    
    print(f"✅ Detected Chrome version: {chrome_version}")
    
    # Clear all caches
    print("\n🧹 Clearing driver caches...")
    cache_dirs = [
        os.path.expanduser("~/.cache/selenium"),
        os.path.expanduser("~/.cache/undetected_chromedriver"),
        os.path.expanduser("~/.wdm"),
        os.path.expanduser("~/Library/Caches/undetected_chromedriver"),
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✓ Cleared {cache_dir}")
            except:
                pass
    
    # Install specific undetected-chromedriver version for Chrome 137
    if chrome_version == 137:
        print("\n📦 Installing undetected-chromedriver for Chrome 137...")
        # First uninstall current version
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "undetected-chromedriver"], 
                      capture_output=True)
        
        # Install version that supports Chrome 137
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "undetected-chromedriver==3.5.3"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ Installed compatible undetected-chromedriver version")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            
            # Try alternative approach
            print("\n🔄 Trying alternative fix...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--force-reinstall", "undetected-chromedriver"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ Reinstalled undetected-chromedriver")
                return True
    
    return False

def main():
    """Main function"""
    if fix_chromedriver_version():
        print("\n✅ ChromeDriver fix complete!")
        print("🎯 You can now run: python3 fansale_no_login.py")
    else:
        print("\n❌ Fix failed. Manual steps:")
        print("1. Update Chrome to latest version")
        print("2. pip uninstall undetected-chromedriver")
        print("3. pip install undetected-chromedriver==3.5.3")

if __name__ == "__main__":
    main()
