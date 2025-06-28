#!/usr/bin/env python3
"""Start FanSale bot with error handling"""

import os
import sys
import time
from pathlib import Path

# Clean any stale Chrome processes
print("🧹 Cleaning up any stale Chrome processes...")
os.system("pkill -f 'Google Chrome' 2>/dev/null")
os.system("pkill -f 'chromedriver' 2>/dev/null")
time.sleep(2)

# Clear Chrome crash dumps if they exist
crash_dir = Path.home() / "Library/Application Support/Google/Chrome/Crashpad/pending"
if crash_dir.exists():
    os.system(f"rm -rf '{crash_dir}'/* 2>/dev/null")

# Set up environment
print("\n🔧 Setting up environment...")
os.environ['FANSALE_TARGET_URL'] = 'https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388'
os.environ['TWOCAPTCHA_API_KEY'] = 'c58050aca5076a2a26ba2eff1c429d4d'

# Create input file for automated start
with open('bot_input.txt', 'w') as f:
    f.write('2\n')  # 2 browsers
    f.write('2\n')  # 2 max tickets
    f.write('6\n')  # All ticket types

print("\n🚀 Starting FanSale Bot...")
print("Configuration: 2 browsers, 2 max tickets, all ticket types")
print("-" * 60)

# Run the bot
try:
    os.system("python3 fansale_check.py < bot_input.txt")
except KeyboardInterrupt:
    print("\n\n👋 Bot stopped by user")
except Exception as e:
    print(f"\n\n❌ Error: {e}")
finally:
    # Cleanup
    if Path('bot_input.txt').exists():
        os.remove('bot_input.txt')
    print("\n✅ Cleanup complete")