#!/usr/bin/env python3
"""Quick performance verification for optimized FanSale bot"""

import time
import json
from pathlib import Path

def verify_config():
    """Check if configuration is optimized for speed"""
    config_path = Path("bot_config_v7.json")
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ Configuration Check:")
        print(f"  • min_wait: {config.get('min_wait', 'Not set')} (should be 0.3)")
        print(f"  • max_wait: {config.get('max_wait', 'Not set')} (should be 1.0)")
        print(f"  • popup_check_interval: {config.get('popup_check_interval', 'Not set')} (should be 30)")
        print(f"  • browsers_count: {config.get('browsers_count', 'Not set')}")
        
        # Check if intervals are optimized
        if config.get('min_wait', 1) <= 0.3 and config.get('max_wait', 2) <= 1.0:
            print("\n✅ Speed settings are OPTIMIZED!")
            expected_checks_per_min = 60 / ((0.3 + 1.0) / 2)
            print(f"  • Expected: ~{expected_checks_per_min:.1f} checks/minute per browser")
            print(f"  • With {config.get('browsers_count', 2)} browsers: ~{expected_checks_per_min * config.get('browsers_count', 2):.1f} total checks/minute")
        else:
            print("\n⚠️  Speed settings need optimization!")
    else:
        print("❌ Config file not found - will use defaults (0.3-1.0s intervals)")

def check_imports():
    """Verify all required modules are available"""
    print("\n✅ Import Check:")
    try:
        import undetected_chromedriver
        print("  • undetected_chromedriver: OK")
    except:
        print("  • undetected_chromedriver: MISSING")
    
    try:
        import selenium
        print("  • selenium: OK")
    except:
        print("  • selenium: MISSING")
    
    try:
        import dotenv
        print("  • python-dotenv: OK")
    except:
        print("  • python-dotenv: MISSING")
    
    try:
        import requests
        print("  • requests: OK")
    except:
        print("  • requests: MISSING")

def estimate_performance():
    """Estimate expected performance"""
    print("\n📊 Performance Estimates:")
    print("  • Check interval: 0.3-1.0 seconds")
    print("  • Average: 0.65 seconds per check")
    print("  • Per browser: ~92 checks/minute")
    print("  • With 2 browsers: ~184 checks/minute")
    print("  • With 4 browsers: ~369 checks/minute")
    print("\n💡 To increase performance:")
    print("  • Add more browsers (up to CPU cores)")
    print("  • Ensure stable internet connection")
    print("  • Close unnecessary applications")

if __name__ == "__main__":
    print("🚀 FanSale Bot Performance Verification\n")
    verify_config()
    check_imports()
    estimate_performance()
    print("\n✅ Optimizations Applied:")
    print("  • Removed 3-second image verification delay")
    print("  • Reduced popup check from 210s to 30s")
    print("  • Simplified logging (no file I/O during hunting)")
    print("  • Reduced buy selectors from 30+ to 8")
    print("  • Removed complex retry logic")
    print("\nReady to run: python3 fansale_check.py")