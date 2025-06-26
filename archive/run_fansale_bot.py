#!/usr/bin/env python3
"""
FanSale Bot Master Menu
Choose your bot version based on your needs
"""

import os
import sys
import subprocess

def print_header():
    """Print the header"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  🎫 FANSALE BOT MASTER 🎫                    ║
║                                                              ║
║              Choose Your Weapon Wisely! ⚔️                    ║
╚══════════════════════════════════════════════════════════════╝
    """)

def print_bot_options():
    """Print available bot options"""
    print("\n🤖 AVAILABLE BOTS:\n")
    
    print("1️⃣  Simple Chrome Bot (NEW! 🆕)")
    print("   • Fast & minimal - no fancy stealth")
    print("   • Regular Chrome without UC")
    print("   • Auto-reserves selected ticket types")
    print("   • ⭐ Less is more approach!")
    print()
    
    print("2️⃣  Real Browser Profile (95% Success)")
    print("   • Uses your actual Chrome profile")
    print("   • Most reliable but requires Chrome closed")
    print("   • Perfect for avoiding all detection")
    print()
    
    print("3️⃣  Ultimate Stealth Bot (70-80% Success)")
    print("   • Undetected ChromeDriver with max stealth")
    print("   • Multiple fallback methods")
    print("   • Good balance of speed and stealth")
    print()
    
    print("4️⃣  Fixed Original Bot (50% Success)")
    print("   • Original bot with improvements")
    print("   • Fast but may be detected")
    print("   • Good if not IP blocked")
    print()
    
    print("5️⃣  Analyze Detection 🔍")
    print("   • Diagnose why you're being blocked")
    print("   • Compare detection methods")
    print("   • Helpful for troubleshooting")
    print()
    
    print("6️⃣  Test UC vs Regular Chrome")
    print("   • Compare detection between methods")
    print("   • See what FanSale detects")
    print()
    
    print("7️⃣  Fix ChromeDriver")
    print("   • Fix Chrome/ChromeDriver version mismatch")
    print()
    
    print("8️⃣  Clean Chrome Processes")
    print("   • Kill stuck Chrome processes")
    print()
    
    print("0️⃣  Exit")
    print()

def run_bot(script_name):
    """Run a bot script"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    if not os.path.exists(script_path):
        print(f"\n❌ Error: {script_name} not found!")
        return
        
    print(f"\n🚀 Starting {script_name}...\n")
    
    # Use the venv python if it exists
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = sys.executable
        
    try:
        subprocess.run([python_cmd, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Bot exited with error: {e}")
    except KeyboardInterrupt:
        print("\n\n⏹️  Bot stopped by user")

def main():
    """Main menu loop"""
    while True:
        print_header()
        print_bot_options()
        
        choice = input("Select option (0-8): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye! Happy ticket hunting!")
            break
        elif choice == '1':
            run_bot('fansale_simple_chrome.py')
        elif choice == '2':
            run_bot('fansale_real_browser.py')
        elif choice == '3':
            run_bot('fansale_ultimate_stealth.py')
        elif choice == '4':
            run_bot('fansale_no_login_fixed.py')
        elif choice == '5':
            run_bot('analyze_detection.py')
        elif choice == '6':
            run_bot('test_uc_detection.py')
        elif choice == '7':
            run_bot('fix_chromedriver.py')
        elif choice == '8':
            run_bot('cleanup_chrome.py')
        else:
            print("\n❌ Invalid choice! Please try again.")
            
        if choice in ['1', '2', '3', '4', '5', '6']:
            input("\n\nPress Enter to return to menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")