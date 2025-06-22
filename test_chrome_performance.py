#!/usr/bin/env python3
"""
Chrome Performance Tester
Tests different Chrome flag combinations to find the fastest setup
"""

import time
import statistics
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# Test configurations
TEST_CONFIGS = {
    "baseline": {
        "name": "Baseline (minimal flags)",
        "flags": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled"
        ]
    },
    "balanced": {
        "name": "Balanced (recommended)",
        "flags": [
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--disable-blink-features=AutomationControlled",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",
            "--disable-logging"
        ]
    },
    "aggressive": {
        "name": "Aggressive (maximum speed)",
        "flags": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",
            "--disable-javascript-harmony-shipping",
            "--disable-webgl",
            "--disable-3d-apis",
            "--aggressive-cache-discard",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-features=TranslateUI",
            "--memory-pressure-off",
            "--disable-logging",
            "--disable-default-apps",
            "--disable-hang-monitor",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--no-first-run"
        ]
    }
}

def test_configuration(config_name, flags):
    """Test a Chrome configuration and measure performance"""
    print(f"\n🧪 Testing: {config_name}")
    
    options = uc.ChromeOptions()
    options.add_experimental_option("prefs", {
        "profile.managed_default_content_settings.images": 2
    })
    
    for flag in flags:
        options.add_argument(flag)
    
    try:
        # Start timer
        start_time = time.time()
        
        # Create driver
        driver = uc.Chrome(options=options)
        driver_creation_time = time.time() - start_time
        
        # Test page load
        load_start = time.time()
        driver.get("https://www.fansale.it/fansale/")
        page_load_time = time.time() - load_start
        
        # Test element detection
        detect_start = time.time()
        try:
            driver.find_element(By.CSS_SELECTOR, "body")
            element_detect_time = time.time() - detect_start
        except:
            element_detect_time = -1
        
        # Test JavaScript execution
        js_start = time.time()
        result = driver.execute_script("return document.readyState")
        js_exec_time = time.time() - js_start
        
        driver.quit()
        
        return {
            "driver_creation": driver_creation_time,
            "page_load": page_load_time,
            "element_detect": element_detect_time,
            "js_execution": js_exec_time,
            "total": driver_creation_time + page_load_time
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    print("🏁 Chrome Performance Test Suite")
    print("This will test different Chrome configurations to find the fastest")
    print("-" * 60)
    
    results = {}
    
    for config_key, config in TEST_CONFIGS.items():
        result = test_configuration(config["name"], config["flags"])
        if result:
            results[config_key] = result
            print(f"  ✅ Driver creation: {result['driver_creation']:.2f}s")
            print(f"  ✅ Page load: {result['page_load']:.2f}s")
            print(f"  ✅ Element detection: {result['element_detect']:.3f}s")
            print(f"  ✅ JS execution: {result['js_execution']:.3f}s")
            print(f"  📊 Total time: {result['total']:.2f}s")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if results:
        fastest = min(results.items(), key=lambda x: x[1]['total'])
        print(f"\n🏆 Fastest configuration: {TEST_CONFIGS[fastest[0]]['name']}")
        print(f"   Total time: {fastest[1]['total']:.2f}s")
        
        print("\n📈 Configuration Comparison:")
        for config_key, result in sorted(results.items(), key=lambda x: x[1]['total']):
            print(f"   {TEST_CONFIGS[config_key]['name']}: {result['total']:.2f}s")
        
        # Save best config
        with open("best_chrome_flags.txt", "w") as f:
            f.write(f"# Best Chrome flags for your system\n")
            f.write(f"# Configuration: {TEST_CONFIGS[fastest[0]]['name']}\n")
            f.write(f"# Total time: {fastest[1]['total']:.2f}s\n\n")
            for flag in TEST_CONFIGS[fastest[0]]['flags']:
                f.write(f"{flag}\n")
        
        print(f"\n💾 Best configuration saved to: best_chrome_flags.txt")

if __name__ == "__main__":
    main()
