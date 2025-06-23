#!/usr/bin/env python3
"""
FanSale Bot - Main Entry Point
Choose your approach based on your needs
"""

import os
import sys
from pathlib import Path

def print_banner():
    """Display options banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    FANSALE BOT - CHOOSE YOUR APPROACH            ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  Reality Check:                                                  ║
    ║  • API Bypass: ~0% success (impossible)                          ║
    ║  • Browser Automation: 30-60% success                           ║
    ║  • Multiple browsers = better coverage!                          ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

def show_comparison():
    """Show bot comparison"""
    print("""
    📊 Bot Comparison:
    
    1. Parallel Multi-Browser (NEW!):
       • 4 browsers hunting simultaneously
       • Best coverage - no gaps!
       • ~4 refreshes/min total
       • Requires 5 logins
       
    2. Simple Browser Bot:
       • Single browser, fast refresh
       • 1.2-3.6 GB/hour data usage
       • Simple to use
       
    3. Lite Browser Bot:
       • Low data usage (200-400 MB/hour)
       • For proxy users
       • Manual purchase required
    """)

def main():
    """Main entry point"""
    print_banner()
    
    print("\n📋 Available Bots:")
    print("1. 🚀 Parallel Multi-Browser Bot (BEST COVERAGE - NEW!)")
    print("2. 📱 Simple Browser Bot (single browser)")
    print("3. 💾 Lite Browser Bot (low data for proxy)")
    print("4. 📊 Compare bot features")
    print("5. 🚪 Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting Parallel Multi-Browser Bot...")
        print("⚠️  You'll need to login to 5 browsers")
        print("✅ Best coverage - 4 hunters + 1 purchase browser")
        print("✅ If one gets blocked, others continue!\n")
        os.system("python3 fansale_parallel_bot.py")
        
    elif choice == "2":
        print("\n🚀 Starting Simple Browser Bot...")
        print("📊 Single browser, fast refresh")
        print("✅ Simple and effective\n")
        os.system("python3 fansale_simple_browser.py")
        
    elif choice == "3":
        print("\n🚀 Starting Lite Browser Bot...")
        print("📊 Uses 80-90% LESS data than normal bot")
        print("⚠️  Page will look broken (no images/CSS)")
        print("⚠️  Manual purchase required when tickets found\n")
        os.system("python3 fansale_lite_browser.py")
        
    elif choice == "4":
        show_comparison()
        input("\nPress Enter to return to menu...")
        main()
        
    elif choice == "5":
        print("\n👋 Good luck with your tickets!")
        sys.exit(0)
        
    else:
        print("\n❌ Invalid choice!")
        main()

if __name__ == "__main__":
    main()