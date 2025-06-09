#!/usr/bin/env python3
"""Basic performance test suite for StealthMaster."""

import asyncio
import time
import psutil
import json
import statistics
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config import load_settings
from profiles.manager import ProfileManager
from stealth.core import StealthCore
from stealth.fingerprint import FingerprintGenerator
from playwright.async_api import async_playwright


class BasicPerformanceTests:
    """Basic performance tests for StealthMaster."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        self.settings = load_settings(Path("config.yaml"))
    
    async def test_startup_speed(self):
        """Test basic startup performance."""
        print("\n1️⃣ Testing Startup Performance...")
        
        times = []
        
        for i in range(3):
            print(f"   Run {i+1}/3...", end="\r")
            
            start = time.perf_counter()
            
            # Initialize components
            pm = ProfileManager(self.settings)
            await pm.load_all_profiles()
            
            # Launch browser
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Apply stealth
            stealth = StealthCore()
            await stealth.apply_page_stealth(page)
            
            total_time = time.perf_counter() - start
            times.append(total_time)
            
            # Cleanup
            await browser.close()
            await playwright.stop()
        
        self.results["tests"]["startup_performance"] = {
            "average_time_seconds": round(statistics.mean(times), 3),
            "min_time_seconds": round(min(times), 3),
            "max_time_seconds": round(max(times), 3),
            "status": "✅ PASS" if statistics.mean(times) < 5.0 else "❌ FAIL"
        }
        
        print(f"   ✅ Average startup time: {statistics.mean(times):.2f}s")
    
    async def test_memory_usage(self):
        """Test memory consumption."""
        print("\n2️⃣ Testing Memory Usage...")
        
        process = psutil.Process()
        baseline = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple browsers
        playwright = await async_playwright().start()
        browsers = []
        
        for i in range(3):
            print(f"   Launching browser {i+1}/3...", end="\r")
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            stealth = StealthCore()
            await stealth.apply_page_stealth(page)
            browsers.append(browser)
        
        # Measure after launch
        after_launch = process.memory_info().rss / 1024 / 1024
        memory_per_browser = (after_launch - baseline) / 3
        
        # Cleanup
        for browser in browsers:
            await browser.close()
        await playwright.stop()
        
        self.results["tests"]["memory_usage"] = {
            "baseline_mb": round(baseline, 2),
            "after_3_browsers_mb": round(after_launch, 2),
            "memory_per_browser_mb": round(memory_per_browser, 2),
            "status": "✅ PASS" if memory_per_browser < 200 else "❌ FAIL"
        }
        
        print(f"   ✅ Memory per browser: {memory_per_browser:.1f}MB")
    
    async def test_fingerprint_generation(self):
        """Test fingerprint generation performance."""
        print("\n3️⃣ Testing Fingerprint Generation...")
        
        fg = FingerprintGenerator()
        
        # Test generation speed
        start = time.perf_counter()
        fingerprints = []
        for _ in range(100):
            fp = fg.generate()
            fingerprints.append(fp)
        generation_time = time.perf_counter() - start
        
        # Test uniqueness
        unique_ids = len(set(fp.get("id") for fp in fingerprints))
        
        self.results["tests"]["fingerprint_generation"] = {
            "total_generated": 100,
            "unique_fingerprints": unique_ids,
            "generation_time_seconds": round(generation_time, 3),
            "avg_time_per_fingerprint_ms": round((generation_time / 100) * 1000, 2),
            "uniqueness_rate": round(unique_ids / 100, 2),
            "status": "✅ PASS" if unique_ids == 100 else "❌ FAIL"
        }
        
        print(f"   ✅ Generated {unique_ids}/100 unique fingerprints in {generation_time:.2f}s")
    
    async def test_bot_detection_basic(self):
        """Basic bot detection test."""
        print("\n4️⃣ Testing Bot Detection Evasion...")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Apply stealth
        stealth = StealthCore()
        await stealth.apply_page_stealth(page)
        
        # Navigate to bot test page
        try:
            await page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=30000)
            
            # Check basic detection indicators
            detection_checks = await page.evaluate("""
                () => {
                    return {
                        webdriver: navigator.webdriver,
                        headless: /HeadlessChrome/.test(navigator.userAgent),
                        plugins_length: navigator.plugins.length,
                        languages: navigator.languages.length,
                        chrome_runtime: !!window.chrome
                    };
                }
            """)
            
            passed = not detection_checks["webdriver"] and \
                    not detection_checks["headless"] and \
                    detection_checks["plugins_length"] > 0
            
            self.results["tests"]["bot_detection"] = {
                "webdriver_hidden": not detection_checks["webdriver"],
                "headless_hidden": not detection_checks["headless"],
                "has_plugins": detection_checks["plugins_length"] > 0,
                "has_languages": detection_checks["languages"] > 0,
                "status": "✅ PASS" if passed else "❌ FAIL"
            }
            
            print(f"   {'✅' if passed else '❌'} Bot detection test: {'PASSED' if passed else 'FAILED'}")
            
        except Exception as e:
            self.results["tests"]["bot_detection"] = {
                "error": str(e),
                "status": "❌ FAIL"
            }
            print(f"   ❌ Bot detection test failed: {e}")
        
        await browser.close()
        await playwright.stop()
    
    async def test_concurrent_performance(self):
        """Test concurrent browser performance."""
        print("\n5️⃣ Testing Concurrent Operations...")
        
        playwright = await async_playwright().start()
        
        # Test different concurrency levels
        results = {}
        
        for concurrency in [1, 3, 5]:
            start = time.perf_counter()
            
            # Launch browsers concurrently
            tasks = []
            for _ in range(concurrency):
                task = self._launch_and_navigate(playwright)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            total_time = time.perf_counter() - start
            avg_time = total_time / concurrency
            
            results[f"{concurrency}_browsers"] = {
                "total_time_seconds": round(total_time, 2),
                "avg_time_per_browser": round(avg_time, 2)
            }
            
            print(f"   ✅ {concurrency} browsers: {total_time:.2f}s total, {avg_time:.2f}s per browser")
        
        self.results["tests"]["concurrent_performance"] = results
        
        await playwright.stop()
    
    async def _launch_and_navigate(self, playwright):
        """Helper to launch browser and navigate."""
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = StealthCore()
        await stealth.apply_page_stealth(page)
        
        try:
            await page.goto("https://www.example.com", wait_until="domcontentloaded", timeout=30000)
        except:
            pass
        
        await browser.close()
    
    async def test_data_optimization(self):
        """Test data usage optimization."""
        print("\n6️⃣ Testing Data Optimization...")
        
        playwright = await async_playwright().start()
        
        # Test without optimization
        browser1 = await playwright.chromium.launch(headless=True)
        context1 = await browser1.new_context()
        page1 = await context1.new_page()
        
        requests_standard = []
        page1.on("request", lambda req: requests_standard.append(req.resource_type))
        
        try:
            await page1.goto("https://www.example.com", wait_until="networkidle", timeout=30000)
        except:
            pass
        
        await browser1.close()
        
        # Test with optimization (blocking resources)
        browser2 = await playwright.chromium.launch(headless=True)
        context2 = await browser2.new_context()
        
        await context2.route("**/*", lambda route: 
            route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        )
        
        page2 = await context2.new_page()
        requests_optimized = []
        page2.on("request", lambda req: requests_optimized.append(req.resource_type))
        
        try:
            await page2.goto("https://www.example.com", wait_until="networkidle", timeout=30000)
        except:
            pass
        
        await browser2.close()
        await playwright.stop()
        
        blocked = len(requests_standard) - len(requests_optimized)
        savings_percent = (blocked / len(requests_standard) * 100) if requests_standard else 0
        
        self.results["tests"]["data_optimization"] = {
            "requests_standard": len(requests_standard),
            "requests_optimized": len(requests_optimized),
            "requests_blocked": blocked,
            "savings_percent": round(savings_percent, 1),
            "status": "✅ PASS" if savings_percent > 20 else "⚠️ WARN"
        }
        
        print(f"   ✅ Blocked {blocked} requests ({savings_percent:.1f}% savings)")
    
    def save_results(self):
        """Save test results."""
        results_file = Path("tests/basic_performance_results.json")
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Results saved to: {results_file}")
        return results_file
    
    def analyze_results(self):
        """Analyze and print summary."""
        print("\n" + "="*60)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("="*60)
        
        all_passed = True
        issues = []
        
        for test_name, result in self.results["tests"].items():
            status = result.get("status", "❓ UNKNOWN")
            print(f"\n{test_name.replace('_', ' ').title()}: {status}")
            
            if "FAIL" in status:
                all_passed = False
                issues.append(test_name)
            
            # Print key metrics
            if test_name == "startup_performance":
                print(f"  - Average startup time: {result['average_time_seconds']}s")
            elif test_name == "memory_usage":
                print(f"  - Memory per browser: {result['memory_per_browser_mb']}MB")
            elif test_name == "fingerprint_generation":
                print(f"  - Uniqueness rate: {result['uniqueness_rate']*100}%")
            elif test_name == "bot_detection":
                if "webdriver_hidden" in result:
                    print(f"  - Webdriver hidden: {result['webdriver_hidden']}")
                    print(f"  - Headless hidden: {result['headless_hidden']}")
        
        print("\n" + "="*60)
        
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"❌ {len(issues)} TESTS FAILED: {', '.join(issues)}")
        
        print("="*60)
        
        return all_passed, issues


async def main():
    """Run basic performance tests."""
    tests = BasicPerformanceTests()
    
    try:
        # Run all tests
        await tests.test_startup_speed()
        await tests.test_memory_usage()
        await tests.test_fingerprint_generation()
        await tests.test_bot_detection_basic()
        await tests.test_concurrent_performance()
        await tests.test_data_optimization()
        
        # Save and analyze
        tests.save_results()
        all_passed, issues = tests.analyze_results()
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)