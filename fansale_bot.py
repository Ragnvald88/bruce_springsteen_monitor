#!/usr/bin/env python3
"""
FanSale Bot - Main Entry Point
Simple browser automation approach
"""

import os
import sys
from pathlib import Path

def print_banner():
    """Display realistic assessment banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    FANSALE BOT - REALISTIC APPROACH              ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  🔍 Reality Check Complete                                       ║
    ║                                                                  ║
    ║  API Bypass Success Rate: ~0% (not realistic)                   ║
    ║  Browser Automation: 40-60% (depends on many factors)           ║
    ║                                                                  ║
    ║  The Truth:                                                      ║
    ║  • Akamai's sensor data is impossibly complex                   ║
    ║  • Direct API access will always trigger 403                    ║
    ║  • Browser automation is the only realistic path                 ║
    ║  • Even then, success depends on luck and timing                ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

def main():
    """Main entry point"""
    print_banner()
    
    print("\n📋 Available Options:")
    print("1. Simple Browser Bot (RECOMMENDED - 40-60% success)")
    print("2. Advanced Bot (complex but similar success rate)")
    print("3. Test Cookie Pattern (for learning)")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting Simple Browser Bot...")
        print("This just refreshes the page and looks for tickets.")
        print("No API tricks, just pure browser automation.\n")
        os.system("python3 fansale_simple_browser.py")
    elif choice == "2":
        print("\n🚀 Starting Advanced Bot...")
        print("More complex but similar success rate.\n")
        os.system("python3 fansale_advanced.py")
    elif choice == "3":
        print("\n🧪 Running Cookie Pattern Test...")
        os.system("python3 test_akamai_pattern.py")
    elif choice == "4":
        print("\n👋 Good luck!")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice!")

if __name__ == "__main__":
    main()
