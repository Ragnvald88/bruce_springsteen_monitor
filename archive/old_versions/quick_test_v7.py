#!/usr/bin/env python3
"""
Quick operational test for FanSale Bot V7
Tests the bot in action with a single browser
"""

import os
import sys
import time
from pathlib import Path

def quick_test():
    """Run a quick operational test of the bot"""
    print("\n" + "="*60)
    print("🧪 FANSALE BOT V7 - QUICK OPERATIONAL TEST")
    print("="*60)
    
    # 1. Check environment
    print("\n1️⃣ Checking environment...")
    
    if not Path(".env").exists():
        print("❌ No .env file found!")
        print("Creating test .env file...")
        with open(".env", "w") as f:
            f.write("# FanSale Bot Configuration\n")
            f.write("FANSALE_TARGET_URL=https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554\n")
            f.write("# TWOCAPTCHA_API_KEY=your_key_here\n")
        print("✅ Created .env file with default URL")
    else:
        print("✅ .env file exists")
    
    # 2. Check dependencies
    print("\n2️⃣ Checking dependencies...")
    try:
        import undetected_chromedriver
        print("✅ undetected-chromedriver installed")
    except ImportError:
        print("❌ Missing undetected-chromedriver")
        print("Run: pip install undetected-chromedriver")
        return False
    
    try:
        from selenium import webdriver
        print("✅ selenium installed")
    except ImportError:
        print("❌ Missing selenium")
        print("Run: pip install selenium")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ Missing python-dotenv")
        print("Run: pip install python-dotenv")
        return False
    
    # 3. Load environment
    print("\n3️⃣ Loading environment...")
    load_dotenv()
    target_url = os.getenv('FANSALE_TARGET_URL')
    if target_url:
        print(f"✅ Target URL: {target_url[:50]}...")
    else:
        print("⚠️  No FANSALE_TARGET_URL in .env, will use default")
    
    # 4. Import bot
    print("\n4️⃣ Importing FanSale Bot V7...")
    try:
        from fansale_check import FanSaleBotV7, BotConfig
        print("✅ Bot imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import bot: {e}")
        return False
    
    # 5. Create bot instance
    print("\n5️⃣ Creating bot instance...")
    try:
        config = BotConfig()
        config.browsers_count = 1  # Just one browser for test
        config.max_tickets = 1
        
        bot = FanSaleBotV7(config)
        print("✅ Bot instance created")
        print(f"   Target URL: {bot.target_url[:50]}...")
    except Exception as e:
        print(f"❌ Failed to create bot: {e}")
        return False
    
    # 6. Test browser creation
    print("\n6️⃣ Testing browser creation...")
    try:
        driver = bot.create_browser(1)
        if driver:
            print("✅ Browser created successfully")
            
            # Test navigation
            print("\n7️⃣ Testing navigation...")
            driver.get(bot.target_url)
            time.sleep(3)
            print(f"✅ Navigated to: {driver.current_url[:50]}...")
            
            # Test popup dismissal
            print("\n8️⃣ Testing popup dismissal...")
            popups_dismissed = bot.dismiss_popups(driver, 1)
            print(f"✅ Dismissed {popups_dismissed} popups")
            
            # Test ticket detection
            print("\n9️⃣ Testing ticket detection...")
            tickets = driver.find_elements("css selector", "div[data-qa='ticketToBuy']")
            print(f"✅ Found {len(tickets)} tickets on page")
            
            if tickets:
                # Test categorization
                print("\n🔟 Testing ticket categorization...")
                ticket_info = bot.extract_full_ticket_info(driver, tickets[0])
                print(f"✅ First ticket category: {ticket_info['category']}")
                print(f"   Text preview: {ticket_info['raw_text'][:50]}...")
            
            # Test CAPTCHA detection
            print("\n1️⃣1️⃣ Testing CAPTCHA detection...")
            captcha_detected, sitekey, url = bot.detect_captcha(driver)
            if captcha_detected:
                print(f"⚠️  CAPTCHA detected! Sitekey: {sitekey}")
            else:
                print("✅ No CAPTCHA detected")
            
            # Test image verification
            print("\n1️⃣2️⃣ Testing image loading...")
            images_ok = bot.verify_image_loading(driver, 1)
            if images_ok:
                print("✅ Images are loading correctly")
            else:
                print("⚠️  Image loading issues detected")
            
            # Cleanup
            print("\n🧹 Cleaning up...")
            driver.quit()
            print("✅ Browser closed")
            
        else:
            print("❌ Failed to create browser")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED! Bot is operational.")
    print("="*60)
    
    return True

def main():
    """Run the quick test"""
    print("\nThis will test FanSale Bot V7 functionality.")
    print("A browser window will open briefly.")
    
    response = input("\nProceed with test? (y/n): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    success = quick_test()
    
    if success:
        print("\n🎉 Bot is ready to use!")
        print("\nTo run the full bot:")
        print("  python3 fansale_check.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()