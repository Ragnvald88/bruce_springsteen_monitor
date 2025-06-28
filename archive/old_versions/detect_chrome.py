#!/usr/bin/env python3
"""
Detect Chrome version and clear caches
"""

import subprocess
import os
import shutil
import sys

def get_chrome_version():
    """Get installed Chrome version"""
    try:
        # macOS
        result = subprocess.run(
            ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            version_str = result.stdout.strip()
            print(f"Chrome version string: {version_str}")
            # Extract version number
            version = version_str.split()[-1]
            major_version = int(version.split('.')[0])
            return major_version
    except Exception as e:
        print(f"Error detecting Chrome: {e}")
    
    return None

def clear_chromedriver_cache():
    """Clear all ChromeDriver caches"""
    cache_dirs = [
        os.path.expanduser("~/.wdm"),
        os.path.expanduser("~/Library/Caches/undetected_chromedriver"),
        os.path.expanduser("~/Library/Application Support/undetected_chromedriver"),
        os.path.expanduser("~/.cache/selenium"),
        os.path.expanduser("~/.cache/undetected_chromedriver"),
    ]
    
    print("\n🧹 Clearing ChromeDriver caches...")
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared: {cache_dir}")
            except Exception as e:
                print(f"❌ Failed to clear {cache_dir}: {e}")
        else:
            print(f"⏭️  Not found: {cache_dir}")

def main():
    print("🔍 Chrome Version Detector & Cache Cleaner")
    print("="*50)
    
    # Detect Chrome version
    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"\n✅ Chrome major version: {chrome_version}")
        print(f"\n📝 Add this version to fansale_v7_ultimate.py:")
        print(f"   In the 'attempts' list, add: ({chrome_version}, 'Chrome {chrome_version}')")
    else:
        print("\n❌ Could not detect Chrome version")
    
    # Ask to clear caches
    response = input("\n🧹 Clear ChromeDriver caches? (y/n): ")
    if response.lower() == 'y':
        clear_chromedriver_cache()
        print("\n✅ Caches cleared!")
        print("\n🔧 Now run these commands:")
        print("   pip uninstall undetected-chromedriver")
        print("   pip install undetected-chromedriver")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()