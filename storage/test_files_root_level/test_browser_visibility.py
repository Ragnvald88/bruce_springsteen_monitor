#!/usr/bin/env python3
"""Test browser visibility settings"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import load_and_merge_configs, DEFAULT_CONFIG_FILE

def test_browser_visibility():
    """Check browser visibility configuration"""
    print("=== Testing Browser Visibility Configuration ===\n")
    
    # Load config
    config = load_and_merge_configs(DEFAULT_CONFIG_FILE)
    
    # Check browser options
    browser_options = config.get('browser_options', {})
    headless = browser_options.get('headless', True)
    
    print(f"1. Browser headless setting: {headless}")
    print(f"   {'⚠️  Browsers will be HIDDEN' if headless else '✓ Browsers will be VISIBLE'}")
    
    # Check other browser settings
    print(f"\n2. Other browser settings:")
    print(f"   - viewport width: {browser_options.get('viewport', {}).get('width', 'default')}")
    print(f"   - viewport height: {browser_options.get('viewport', {}).get('height', 'default')}")
    print(f"   - user agent: {'custom' if browser_options.get('user_agent') else 'default'}")
    
    # Check authentication
    auth_config = config.get('authentication', {})
    auth_enabled = auth_config.get('enabled', False)
    
    print(f"\n3. Authentication configuration:")
    print(f"   - enabled: {auth_enabled}")
    
    if auth_enabled:
        platforms = auth_config.get('platforms', {})
        for platform, creds in platforms.items():
            has_creds = bool(creds.get('email') or creds.get('password'))
            print(f"   - {platform}: {'configured' if has_creds else 'missing'}")
    
    # Check if test mode
    dry_run = config.get('app_settings', {}).get('dry_run', False)
    print(f"\n4. Dry run mode: {dry_run}")
    print(f"   {'⚠️  No actual purchases will be made' if dry_run else '✓ Real purchases enabled'}")
    
    return not headless  # Return True if browsers will be visible

if __name__ == "__main__":
    visible = test_browser_visibility()
    print(f"\n{'✓ Browsers will be VISIBLE during operation' if visible else '⚠️  Browsers will be HIDDEN - change headless to false in config.yaml to see them'}")