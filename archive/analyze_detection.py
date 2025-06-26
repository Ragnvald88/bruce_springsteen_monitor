#!/usr/bin/env python3
"""
Analyze why the bot is being detected immediately
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json

def analyze_detection():
    """Test what's causing immediate detection"""
    print("🔍 Analyzing bot detection vectors...\n")
    
    # Create minimal browser
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    driver = uc.Chrome(options=options)
    
    # First test on a detection site
    print("1. Testing on bot detection site...")
    driver.get("https://bot.sannysoft.com/")
    time.sleep(3)
    
    # Comprehensive detection checks
    detection_results = {}
    
    # WebDriver detection
    detection_results['webdriver'] = driver.execute_script("return navigator.webdriver")
    
    # Chrome properties
    detection_results['chrome'] = driver.execute_script("""
        return {
            exists: typeof window.chrome !== 'undefined',
            runtime: typeof window.chrome?.runtime !== 'undefined',
            loadTimes: typeof window.chrome?.loadTimes === 'function'
        }
    """)
    
    # Plugins
    detection_results['plugins'] = driver.execute_script("""
        return {
            length: navigator.plugins.length,
            names: Array.from(navigator.plugins).map(p => p.name)
        }
    """)
    
    # Permissions
    detection_results['permissions'] = driver.execute_script("""
        return navigator.permissions ? 'exists' : 'missing'
    """)
    
    # CDP detection
    detection_results['cdp'] = driver.execute_script("""
        return {
            cdc_props: Object.keys(window).filter(k => k.includes('cdc')),
            document_props: Object.keys(document).filter(k => k.includes('selenium') || k.includes('webdriver'))
        }
    """)
    
    # User agent
    detection_results['userAgent'] = driver.execute_script("return navigator.userAgent")
    
    # Languages
    detection_results['languages'] = driver.execute_script("return navigator.languages")
    
    # Screen properties
    detection_results['screen'] = driver.execute_script("""
        return {
            width: screen.width,
            height: screen.height,
            availWidth: screen.availWidth,
            availHeight: screen.availHeight,
            colorDepth: screen.colorDepth,
            pixelDepth: screen.pixelDepth
        }
    """)
    
    # WebGL
    detection_results['webgl'] = driver.execute_script("""
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl');
            return {
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER)
            };
        } catch(e) {
            return 'error';
        }
    """)
    
    print("\n📊 Detection Results:")
    print(json.dumps(detection_results, indent=2))
    
    # Now test on FanSale
    print("\n2. Testing on FanSale...")
    driver.get("https://www.fansale.it")
    time.sleep(3)
    
    # Check for blocking indicators
    page_source = driver.page_source.lower()
    current_url = driver.current_url
    page_title = driver.title
    
    print(f"\nCurrent URL: {current_url}")
    print(f"Page Title: {page_title}")
    
    # Check for common block patterns
    block_indicators = [
        'access denied',
        'blocked',
        'cloudflare',
        'checking your browser',
        'please verify',
        'unusual traffic',
        'bot detection'
    ]
    
    detected_blocks = [indicator for indicator in block_indicators if indicator in page_source]
    
    if detected_blocks:
        print(f"\n⚠️ Block indicators found: {detected_blocks}")
    
    # Check console logs
    logs = driver.get_log('browser')
    if logs:
        print("\n📝 Console logs:")
        for log in logs[-10:]:  # Last 10 logs
            print(f"  {log['level']}: {log['message']}")
    
    input("\nPress Enter to close browser...")
    driver.quit()
    
    return detection_results

if __name__ == "__main__":
    results = analyze_detection()
    
    print("\n🎯 Key Issues Found:")
    
    if results['webdriver']:
        print("❌ navigator.webdriver is TRUE (dead giveaway!)")
    
    if results['plugins']['length'] == 0:
        print("❌ No browser plugins (suspicious)")
    
    if not results['chrome']['runtime']:
        print("❌ Missing chrome.runtime (automation detected)")
    
    if 'HeadlessChrome' in results['userAgent']:
        print("❌ Headless Chrome detected in user agent")
    
    if results['cdp']['cdc_props']:
        print(f"❌ CDP properties found: {results['cdp']['cdc_props']}")
    
    print("\n💡 The bot is being detected through multiple vectors!")
