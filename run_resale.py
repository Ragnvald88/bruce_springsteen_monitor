#!/usr/bin/env python3
"""
Quick launcher for StealthMaster - FanSale & VivaTicket only
Uses existing project structure with optimizations
"""

import asyncio
import os
import sys
from pathlib import Path

# Apply distutils patch for Python 3.12+ compatibility
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Starting StealthMaster with FanSale/VivaTicket focus...")

# Modify config temporarily
import yaml

config_path = project_root / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Disable Ticketmaster, enable only FanSale and VivaTicket
for target in config['targets']:
    if target['platform'] == 'ticketmaster':
        target['enabled'] = False
    elif target['platform'] in ['fansale', 'vivaticket']:
        target['enabled'] = True
        # Optimize intervals
        target['interval_s'] = 10  # Reasonable checking interval
        if 'burst_mode' in target:
            target['burst_mode']['enabled'] = True
            target['burst_mode']['min_interval_s'] = 3

# Use stealth mode for better success
config['app_settings']['mode'] = 'stealth'

# Save temporary config
temp_config_path = project_root / "config_resale_temp.yaml"
with open(temp_config_path, 'w') as f:
    yaml.dump(config, f)

# Set environment variable to use temp config
os.environ['STEALTHMASTER_CONFIG'] = str(temp_config_path)

# Run the main stealthmaster
from stealthmaster import main as original_main

try:
    asyncio.run(original_main())
finally:
    # Cleanup temp config
    if temp_config_path.exists():
        temp_config_path.unlink()