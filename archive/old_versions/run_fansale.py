#!/usr/bin/env python3
"""Simple FanSale bot runner"""

import os
import sys
import time

# Kill any existing Chrome processes
os.system("pkill -f 'Google Chrome' 2>/dev/null")
os.system("pkill -f 'chromedriver' 2>/dev/null")
time.sleep(1)

# Set environment
os.environ['FANSALE_TARGET_URL'] = 'https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388'
os.environ['TWOCAPTCHA_API_KEY'] = 'c58050aca5076a2a26ba2eff1c429d4d'

print("🎫 FANSALE BOT V7 - FIXED VERSION")
print("="*60)
print("Starting with 2 browsers, hunting all ticket types...")
print("="*60)

# Create input file
with open('bot_input.txt', 'w') as f:
    f.write('2\n')  # 2 browsers
    f.write('2\n')  # 2 max tickets  
    f.write('6\n')  # All ticket types
    f.write('\n')   # Press Enter to start

# Run bot
os.system("python3 fansale_check.py < bot_input.txt")

# Cleanup
try:
    os.remove('bot_input.txt')
except:
    pass