#!/usr/bin/env python3
"""
Verify proxy configuration for StealthMaster AI
"""

import os
import yaml
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)


def check_proxy_configuration():
    """Check if proxy is properly configured"""
    print(f"{Fore.CYAN}🔍 Checking Proxy Configuration")
    print(f"{Fore.CYAN}{'='*50}")
    
    # Load config
    config_path = Path("config/config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    proxy_settings = config.get('proxy_settings', {})
    
    # Check if proxy is enabled
    enabled = proxy_settings.get('enabled', False)
    print(f"\nProxy Enabled: {Fore.GREEN if enabled else Fore.RED}{enabled}")
    
    if not enabled:
        print(f"{Fore.YELLOW}⚠️  Proxy is disabled. Enable it in config.yaml for better performance.")
        return
    
    # Check proxy pools
    primary_pool = proxy_settings.get('primary_pool', [])
    backup_pool = proxy_settings.get('backup_pool', [])
    
    print(f"\nPrimary Pool: {len(primary_pool)} proxies")
    print(f"Backup Pool: {len(backup_pool)} proxies")
    
    # Check environment variables
    print(f"\n{Fore.YELLOW}Environment Variables Required:")
    
    env_vars = {
        'IPROYAL_HOSTNAME': os.getenv('IPROYAL_HOSTNAME'),
        'IPROYAL_PORT': os.getenv('IPROYAL_PORT'),
        'IPROYAL_USERNAME': os.getenv('IPROYAL_USERNAME'),
        'IPROYAL_PASSWORD': os.getenv('IPROYAL_PASSWORD'),
    }
    
    all_set = True
    for var, value in env_vars.items():
        if value:
            print(f"  {var}: {Fore.GREEN}✓ Set")
        else:
            print(f"  {var}: {Fore.RED}✗ Not Set")
            all_set = False
    
    # Authentication variables
    print(f"\n{Fore.YELLOW}Authentication Variables:")
    auth_vars = {
        'FANSALE_EMAIL': os.getenv('FANSALE_EMAIL'),
        'FANSALE_PASSWORD': os.getenv('FANSALE_PASSWORD'),
    }
    
    for var, value in auth_vars.items():
        if value:
            print(f"  {var}: {Fore.GREEN}✓ Set")
        else:
            print(f"  {var}: {Fore.YELLOW}⚠ Not Set (optional)")
    
    # Configuration details
    print(f"\n{Fore.YELLOW}Proxy Configuration:")
    print(f"  Rotation Strategy: {proxy_settings.get('rotation_strategy', 'unknown')}")
    print(f"  Rotate on Block: {proxy_settings.get('rotation_rules', {}).get('rotate_on_block', False)}")
    print(f"  Max Requests per Proxy: {proxy_settings.get('rotation_rules', {}).get('max_requests_per_proxy', 'N/A')}")
    
    # Platform preferences
    platform_prefs = proxy_settings.get('platform_preferences', {})
    if platform_prefs:
        print(f"\n{Fore.YELLOW}Platform-Specific Settings:")
        for platform, prefs in platform_prefs.items():
            print(f"  {platform}:")
            print(f"    Preferred Countries: {prefs.get('preferred_countries', [])}")
            print(f"    Require Residential: {prefs.get('require_residential', False)}")
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*50}")
    if all_set and enabled:
        print(f"{Fore.GREEN}✅ Proxy configuration looks good!")
        print(f"\nTo test proxy connectivity, run:")
        print(f"  python test_proxy_connectivity.py")
    else:
        print(f"{Fore.YELLOW}⚠️  Proxy configuration needs attention.")
        if not all_set:
            print(f"\n{Fore.YELLOW}To set environment variables:")
            print(f"  export IPROYAL_HOSTNAME='your-proxy-host'")
            print(f"  export IPROYAL_PORT=12345")
            print(f"  export IPROYAL_USERNAME='your-username'")
            print(f"  export IPROYAL_PASSWORD='your-password'")


if __name__ == "__main__":
    check_proxy_configuration()