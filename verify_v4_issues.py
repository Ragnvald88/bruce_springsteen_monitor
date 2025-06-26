#!/usr/bin/env python3
"""
Test script to verify V4 issues:
1. Image loading
2. CAPTCHA detection
3. Popup detection
4. 2captcha integration
"""

import sys
import time
sys.path.insert(0, '.')
from fansale_v4 import FanSaleBot, BotConfig
from pathlib import Path
import json

# Create test bot
config = BotConfig()
config.browsers_count = 1
bot = FanSaleBot(config)

print("🔍 Testing FanSale V4 Issues...")
print("=" * 60)

# Test 1: Check if images are loading
print("\n1. Testing image loading...")
browser = bot.create_browser(1)

if browser:
    try:
        # Navigate to a page with images
        browser.get("https://www.google.com/search?q=test+images&tbm=isch")
        time.sleep(3)
        
        # Check if images are loading
        result = browser.execute_script("""
            var images = document.querySelectorAll('img');
            var loadedImages = 0;
            var blockedImages = 0;
            
            for (var i = 0; i < images.length; i++) {
                if (images[i].naturalWidth > 0 && images[i].naturalHeight > 0) {
                    loadedImages++;
                } else if (images[i].complete && images[i].naturalWidth === 0) {
                    blockedImages++;
                }
            }
            
            // Also check Chrome preferences
            var prefs = null;
            try {
                // This won't work in content script but worth trying
                if (window.chrome && window.chrome.prefs) {
                    prefs = 'Chrome prefs accessible';
                }
            } catch(e) {}
            
            return {
                totalImages: images.length,
                loadedImages: loadedImages,
                blockedImages: blockedImages,
                imagesEnabled: loadedImages > 0,
                chromePrefs: prefs
            };
        """)
        
        print(f"   Total images found: {result['totalImages']}")
        print(f"   Images loaded: {result['loadedImages']}")
        print(f"   Images blocked: {result['blockedImages']}")
        print(f"   ✅ Images enabled: {result['imagesEnabled']}" if result['imagesEnabled'] else "   ❌ IMAGES ARE BLOCKED!")
        
        # Test 2: Navigate to FanSale and check for popups/CAPTCHA
        print("\n2. Testing FanSale page...")
        browser.get(bot.target_url)
        time.sleep(5)
        
        # Check page source for popup indicators
        page_source = browser.page_source
        popup_indicators = [
            'modal', 'popup', 'overlay', 'cookie', 'gdpr', 'privacy',
            'accetta', 'chiudi', 'dismiss', 'close'
        ]
        
        found_indicators = []
        for indicator in popup_indicators:
            if indicator.lower() in page_source.lower():
                found_indicators.append(indicator)
        
        print(f"   Popup indicators found: {found_indicators}")
        
        # Test popup dismissal
        print("\n3. Testing popup dismissal...")
        dismissed = bot.dismiss_popups(browser, 1)
        print(f"   Popups dismissed: {dismissed}")
        
        # Test CAPTCHA detection
        print("\n4. Testing CAPTCHA detection...")
        captcha_detected, sitekey, pageurl = bot.detect_captcha(browser)
        print(f"   CAPTCHA detected: {captcha_detected}")
        if captcha_detected:
            print(f"   Sitekey: {sitekey}")
            print(f"   Page URL: {pageurl}")
        
        # Check for actual CAPTCHA elements
        captcha_elements = browser.execute_script("""
            var results = {
                recaptchaDiv: document.querySelectorAll('div.g-recaptcha').length,
                recaptchaIframe: document.querySelectorAll('iframe[src*="recaptcha"]').length,
                captchaText: document.body.innerHTML.toLowerCase().includes('captcha'),
                verificaText: document.body.innerHTML.toLowerCase().includes('verifica')
            };
            return results;
        """)
        
        print(f"\n   Actual CAPTCHA elements found:")
        print(f"   - g-recaptcha divs: {captcha_elements['recaptchaDiv']}")
        print(f"   - recaptcha iframes: {captcha_elements['recaptchaIframe']}")
        print(f"   - 'captcha' text: {captcha_elements['captchaText']}")
        print(f"   - 'verifica' text: {captcha_elements['verificaText']}")
        
        # Test 5: Check 2captcha configuration
        print("\n5. Testing 2captcha configuration...")
        print(f"   API key configured: {'Yes' if bot.captcha_solver and bot.captcha_solver.api_key else 'No'}")
        print(f"   Auto-solve enabled: {bot.auto_solve}")
        
        # Dump browser info
        print("\n6. Browser configuration info:")
        browser_info = browser.execute_script("""
            return {
                userAgent: navigator.userAgent,
                plugins: navigator.plugins.length,
                webdriver: navigator.webdriver,
                languages: navigator.languages,
                platform: navigator.platform,
                vendor: navigator.vendor
            };
        """)
        
        print(f"   User Agent: {browser_info['userAgent'][:80]}...")
        print(f"   Plugins: {browser_info['plugins']}")
        print(f"   Webdriver: {browser_info['webdriver']}")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.quit()
else:
    print("❌ Failed to create browser")

print("\n" + "=" * 60)
print("Test complete.")
