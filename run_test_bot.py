#!/usr/bin/env python3
"""
Run FanSale Bot V7 with test configuration
"""

import os
import sys
import time
import threading
import multiprocessing

# Python 3.13 fix
if __name__ == "__main__":
    multiprocessing.freeze_support()

# Set test environment
os.environ['FANSALE_TARGET_URL'] = 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554'

from fansale_v7_ultimate import FanSaleBotV7, BotConfig

def run_test_bot():
    """Run bot with test configuration"""
    print("\n" + "="*60)
    print("🤖 FANSALE BOT V7 - TEST RUN")
    print("="*60)
    
    # Create test config
    config = BotConfig()
    config.browsers_count = 1  # Just one browser
    config.max_tickets = 1     # Stop after one ticket
    
    # Create bot
    bot = FanSaleBotV7(config)
    print(f"\n✅ Bot created with target URL: {bot.target_url[:50]}...")
    
    # Select ticket types (simulate user selection)
    bot.ticket_types_to_hunt = ["prato_a", "prato_b", "settore"]
    print(f"✅ Hunting for ticket types: {', '.join(bot.ticket_types_to_hunt)}")
    
    # Run for 30 seconds then stop
    print("\n🏃 Running bot for 30 seconds...")
    print("Press Ctrl+C to stop early\n")
    
    try:
        # Start bot
        bot.run()
        
        # Let it run for 30 seconds
        time.sleep(30)
        
        # Stop bot
        print("\n⏹️ Stopping bot...")
        bot.shutdown_event.set()
        
        # Wait for threads to finish
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
        bot.shutdown_event.set()
    
    print("\n✅ Test completed!")
    print(f"Total tickets found: {bot.stats.total_tickets_found}")
    print(f"Unique tickets: {bot.stats.unique_tickets_found}")

if __name__ == "__main__":
    run_test_bot()