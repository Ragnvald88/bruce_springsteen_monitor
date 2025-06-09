#!/usr/bin/env python3
"""Comprehensive performance and optimization test suite for StealthMaster."""

import asyncio
import time
import psutil
import tracemalloc
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import aiohttp
from playwright.async_api import async_playwright, Page, Browser
import numpy as np

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import load_settings
from profiles.manager import ProfileManager
from stealth.core import StealthCore
from stealth.fingerprint import FingerprintGenerator
from stealth.behaviors import HumanBehavior
from browser.launcher import BrowserLauncher
from config import Platform


class PerformanceTestSuite:
    """Comprehensive test suite for StealthMaster performance analysis."""
    
    def __init__(self):
        """Initialize test suite."""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "tests": {}
        }
        self.settings = load_settings(Path("config.yaml"))
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for context."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": sys.version.split()[0]
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests."""
        print("🚀 Starting comprehensive performance test suite...\n")
        
        # Test 1: Startup Performance
        print("📊 Test 1: Startup Performance")
        startup_results = await self.test_startup_performance()
        self.results["tests"]["startup_performance"] = startup_results
        
        # Test 2: Memory Usage
        print("\n📊 Test 2: Memory Usage Analysis")
        memory_results = await self.test_memory_usage()
        self.results["tests"]["memory_usage"] = memory_results
        
        # Test 3: Network Performance
        print("\n📊 Test 3: Network Performance")
        network_results = await self.test_network_performance()
        self.results["tests"]["network_performance"] = network_results
        
        # Test 4: Bot Detection Evasion
        print("\n📊 Test 4: Bot Detection Evasion")
        detection_results = await self.test_bot_detection()
        self.results["tests"]["bot_detection"] = detection_results
        
        # Test 5: Fingerprint Uniqueness
        print("\n📊 Test 5: Fingerprint Uniqueness")
        fingerprint_results = await self.test_fingerprint_uniqueness()
        self.results["tests"]["fingerprint_uniqueness"] = fingerprint_results
        
        # Test 6: Concurrent Operations
        print("\n📊 Test 6: Concurrent Operations")
        concurrent_results = await self.test_concurrent_operations()
        self.results["tests"]["concurrent_operations"] = concurrent_results
        
        # Test 7: Data Usage
        print("\n📊 Test 7: Data Usage Analysis")
        data_results = await self.test_data_usage()
        self.results["tests"]["data_usage"] = data_results
        
        # Save results
        self._save_results()
        
        return self.results
    
    async def test_startup_performance(self) -> Dict[str, Any]:
        """Test application startup performance."""
        results = {
            "profile_manager_init": [],
            "browser_launch": [],
            "stealth_init": [],
            "total_startup": []
        }
        
        # Run multiple iterations
        for i in range(5):
            print(f"  Iteration {i+1}/5", end="\r")
            
            # Test ProfileManager initialization
            start = time.perf_counter()
            pm = ProfileManager(self.settings)
            await pm.load_all_profiles()
            results["profile_manager_init"].append(time.perf_counter() - start)
            
            # Test browser launch
            start = time.perf_counter()
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            results["browser_launch"].append(time.perf_counter() - start)
            
            # Test stealth initialization
            start = time.perf_counter()
            stealth = StealthCore()
            await stealth.apply_page_stealth(page)
            results["stealth_init"].append(time.perf_counter() - start)
            
            # Total startup time
            total = (results["profile_manager_init"][-1] + 
                    results["browser_launch"][-1] + 
                    results["stealth_init"][-1])
            results["total_startup"].append(total)
            
            # Cleanup
            await browser.close()
            await playwright.stop()
        
        # Calculate statistics
        return {
            "profile_manager_init_ms": {
                "mean": round(statistics.mean(results["profile_manager_init"]) * 1000, 2),
                "std": round(statistics.stdev(results["profile_manager_init"]) * 1000, 2),
                "min": round(min(results["profile_manager_init"]) * 1000, 2),
                "max": round(max(results["profile_manager_init"]) * 1000, 2)
            },
            "browser_launch_ms": {
                "mean": round(statistics.mean(results["browser_launch"]) * 1000, 2),
                "std": round(statistics.stdev(results["browser_launch"]) * 1000, 2),
                "min": round(min(results["browser_launch"]) * 1000, 2),
                "max": round(max(results["browser_launch"]) * 1000, 2)
            },
            "stealth_init_ms": {
                "mean": round(statistics.mean(results["stealth_init"]) * 1000, 2),
                "std": round(statistics.stdev(results["stealth_init"]) * 1000, 2),
                "min": round(min(results["stealth_init"]) * 1000, 2),
                "max": round(max(results["stealth_init"]) * 1000, 2)
            },
            "total_startup_ms": {
                "mean": round(statistics.mean(results["total_startup"]) * 1000, 2),
                "std": round(statistics.stdev(results["total_startup"]) * 1000, 2),
                "min": round(min(results["total_startup"]) * 1000, 2),
                "max": round(max(results["total_startup"]) * 1000, 2)
            }
        }
    
    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage patterns."""
        tracemalloc.start()
        process = psutil.Process()
        
        results = {
            "baseline_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "after_profile_load_mb": 0,
            "after_browser_launch_mb": 0,
            "after_navigation_mb": 0,
            "peak_memory_mb": 0,
            "memory_leaks": []
        }
        
        # Load profiles
        pm = ProfileManager(self.settings)
        await pm.load_all_profiles()
        results["after_profile_load_mb"] = round(process.memory_info().rss / 1024 / 1024, 2)
        
        # Launch browsers
        browsers = []
        playwright = await async_playwright().start()
        
        for i in range(3):
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            stealth = StealthCore()
            await stealth.apply_page_stealth(page)
            browsers.append((browser, page))
        
        results["after_browser_launch_mb"] = round(process.memory_info().rss / 1024 / 1024, 2)
        
        # Navigate to pages
        test_urls = [
            "https://www.fansale.it",
            "https://www.ticketmaster.it",
            "https://www.vivaticket.com"
        ]
        
        for i, (browser, page) in enumerate(browsers):
            if i < len(test_urls):
                try:
                    await page.goto(test_urls[i], wait_until="domcontentloaded", timeout=30000)
                except:
                    pass
        
        results["after_navigation_mb"] = round(process.memory_info().rss / 1024 / 1024, 2)
        results["peak_memory_mb"] = results["after_navigation_mb"]
        
        # Check for memory leaks by creating and destroying objects
        initial_mem = process.memory_info().rss
        for i in range(10):
            fp = FingerprintGenerator()
            _ = fp.generate()
            del fp
        
        await asyncio.sleep(1)  # Allow garbage collection
        final_mem = process.memory_info().rss
        
        leak_mb = round((final_mem - initial_mem) / 1024 / 1024, 2)
        if leak_mb > 5:  # More than 5MB growth suggests a leak
            results["memory_leaks"].append({
                "component": "FingerprintGenerator",
                "leak_mb": leak_mb
            })
        
        # Cleanup
        for browser, _ in browsers:
            await browser.close()
        await playwright.stop()
        
        # Get memory allocation stats
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')[:10]
        
        results["top_memory_consumers"] = [
            {
                "file": stat.traceback.format()[0].split('/')[-1],
                "size_mb": round(stat.size / 1024 / 1024, 2)
            }
            for stat in top_stats[:5]
        ]
        
        tracemalloc.stop()
        return results
    
    async def test_network_performance(self) -> Dict[str, Any]:
        """Test network performance and optimization."""
        results = {
            "request_times": [],
            "data_transferred_kb": [],
            "concurrent_request_performance": {},
            "proxy_performance": {}
        }
        
        playwright = await async_playwright().start()
        
        # Test with and without optimization
        for optimization in [False, True]:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            
            if optimization:
                # Enable request interception for optimization
                await context.route("**/*", lambda route: route.abort() 
                    if route.request.resource_type in ["image", "media", "font", "stylesheet"]
                    else route.continue_())
            
            page = await context.new_page()
            
            # Track network activity
            requests = []
            data_transferred = 0
            
            def on_request(request):
                requests.append({
                    "url": request.url,
                    "method": request.method,
                    "start_time": time.time()
                })
            
            def on_response(response):
                nonlocal data_transferred
                if response.body_size:
                    data_transferred += response.body_size
            
            page.on("request", on_request)
            page.on("response", on_response)
            
            # Navigate to test site
            start = time.perf_counter()
            try:
                await page.goto("https://www.ticketmaster.it", wait_until="networkidle", timeout=30000)
                load_time = time.perf_counter() - start
                
                key = "optimized" if optimization else "standard"
                results[f"{key}_load_time_s"] = round(load_time, 2)
                results[f"{key}_requests"] = len(requests)
                results[f"{key}_data_kb"] = round(data_transferred / 1024, 2)
            except Exception as e:
                results[f"{'optimized' if optimization else 'standard'}_error"] = str(e)
            
            await browser.close()
        
        # Test concurrent requests
        async def make_concurrent_requests(num_requests: int):
            async with aiohttp.ClientSession() as session:
                start = time.perf_counter()
                tasks = []
                
                for _ in range(num_requests):
                    task = session.get("https://httpbin.org/delay/1")
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                return time.perf_counter() - start
        
        for num in [1, 5, 10]:
            duration = await make_concurrent_requests(num)
            results["concurrent_request_performance"][f"{num}_requests_s"] = round(duration, 2)
        
        await playwright.stop()
        return results
    
    async def test_bot_detection(self) -> Dict[str, Any]:
        """Test bot detection evasion capabilities."""
        results = {
            "detection_tests": {},
            "fingerprint_consistency": {},
            "behavioral_tests": {}
        }
        
        playwright = await async_playwright().start()
        
        # Test multiple detection vectors
        detection_urls = {
            "basic_js": "https://bot.sannysoft.com/",
            "fingerprint": "https://fingerprintjs.github.io/fingerprintjs/",
            "canvas": "https://browserleaks.com/canvas",
            "webrtc": "https://browserleaks.com/webrtc"
        }
        
        for test_name, url in detection_urls.items():
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Apply stealth
            stealth = StealthCore()
            await stealth.apply_page_stealth(page)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Check for common bot detection indicators
                detection_checks = await page.evaluate("""
                    () => {
                        return {
                            webdriver: navigator.webdriver,
                            headless: /HeadlessChrome/.test(navigator.userAgent),
                            plugins_length: navigator.plugins.length,
                            languages: navigator.languages.length,
                            permissions: typeof Notification !== 'undefined' && Notification.permission,
                            chrome_runtime: window.chrome && window.chrome.runtime,
                            console_firebug: window.console && window.console.firebug,
                            phantom: window._phantom || window.phantom,
                            nightmare: window.__nightmare,
                            selenium: window._selenium || window.__webdriver_evaluate || window.__selenium_evaluate
                        };
                    }
                """)
                
                results["detection_tests"][test_name] = {
                    "passed": not any([
                        detection_checks.get("webdriver"),
                        detection_checks.get("headless"),
                        detection_checks.get("plugins_length", 0) == 0,
                        detection_checks.get("phantom"),
                        detection_checks.get("nightmare"),
                        detection_checks.get("selenium")
                    ]),
                    "details": detection_checks
                }
                
            except Exception as e:
                results["detection_tests"][test_name] = {
                    "passed": False,
                    "error": str(e)
                }
            
            await browser.close()
        
        # Test behavioral patterns
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        stealth = StealthCore()
        await stealth.apply_stealth(page)
        behavior = HumanBehavior()
        
        # Test mouse movement
        start = time.perf_counter()
        await behavior.move_mouse_naturally(page, (100, 100), (500, 500))
        mouse_time = time.perf_counter() - start
        
        # Test typing
        await page.goto("https://www.google.com", wait_until="domcontentloaded")
        search_box = await page.query_selector('input[name="q"]')
        if search_box:
            start = time.perf_counter()
            await behavior.human_type(page, "test query", search_box)
            typing_time = time.perf_counter() - start
            
            results["behavioral_tests"] = {
                "mouse_movement_natural": mouse_time > 0.2,  # Should take time
                "typing_natural": typing_time > 1.0,  # Should take time for realistic typing
                "mouse_movement_time_s": round(mouse_time, 3),
                "typing_time_s": round(typing_time, 3)
            }
        
        await browser.close()
        await playwright.stop()
        
        return results
    
    async def test_fingerprint_uniqueness(self) -> Dict[str, Any]:
        """Test fingerprint generation uniqueness and consistency."""
        results = {
            "uniqueness_test": {},
            "consistency_test": {},
            "entropy_analysis": {}
        }
        
        fg = FingerprintGenerator()
        
        # Generate multiple fingerprints
        fingerprints = []
        for _ in range(100):
            fp = fg.generate()
            fingerprints.append(fp)
        
        # Test uniqueness
        unique_fingerprints = len(set(fp.get("fingerprint_id") for fp in fingerprints))
        results["uniqueness_test"] = {
            "total_generated": 100,
            "unique_count": unique_fingerprints,
            "uniqueness_ratio": unique_fingerprints / 100
        }
        
        # Test consistency of key fields
        user_agents = [fp.get("user_agent") for fp in fingerprints]
        unique_user_agents = len(set(user_agents))
        
        canvas_hashes = [fp.get("canvas", {}).get("hash") for fp in fingerprints]
        unique_canvas = len(set(canvas_hashes))
        
        results["consistency_test"] = {
            "unique_user_agents": unique_user_agents,
            "unique_canvas_fingerprints": unique_canvas,
            "user_agent_diversity": unique_user_agents / 100,
            "canvas_diversity": unique_canvas / 100
        }
        
        # Calculate entropy
        def calculate_entropy(values):
            """Calculate Shannon entropy."""
            counts = {}
            for v in values:
                counts[v] = counts.get(v, 0) + 1
            
            total = len(values)
            entropy = 0
            for count in counts.values():
                if count > 0:
                    p = count / total
                    entropy -= p * np.log2(p)
            
            return entropy
        
        results["entropy_analysis"] = {
            "user_agent_entropy": round(calculate_entropy(user_agents), 3),
            "canvas_entropy": round(calculate_entropy(canvas_hashes), 3),
            "max_possible_entropy": round(np.log2(100), 3)  # Maximum entropy for 100 samples
        }
        
        return results
    
    async def test_concurrent_operations(self) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        results = {
            "concurrent_browsers": {},
            "resource_usage": {},
            "response_times": []
        }
        
        playwright = await async_playwright().start()
        process = psutil.Process()
        
        # Test different concurrency levels
        for concurrency in [1, 3, 5]:
            start_mem = process.memory_info().rss / 1024 / 1024
            start_cpu = process.cpu_percent()
            
            browsers = []
            pages = []
            
            # Launch browsers concurrently
            start = time.perf_counter()
            
            for _ in range(concurrency):
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                stealth = StealthCore()
                await stealth.apply_page_stealth(page)
                browsers.append(browser)
                pages.append(page)
            
            launch_time = time.perf_counter() - start
            
            # Navigate all pages concurrently
            navigation_tasks = []
            for page in pages:
                task = page.goto("https://www.ticketmaster.it", wait_until="domcontentloaded", timeout=30000)
                navigation_tasks.append(task)
            
            start = time.perf_counter()
            try:
                await asyncio.gather(*navigation_tasks, return_exceptions=True)
                navigation_time = time.perf_counter() - start
            except:
                navigation_time = -1
            
            # Measure resource usage
            await asyncio.sleep(1)  # Let things settle
            end_mem = process.memory_info().rss / 1024 / 1024
            end_cpu = process.cpu_percent()
            
            results["concurrent_browsers"][f"{concurrency}_browsers"] = {
                "launch_time_s": round(launch_time, 2),
                "navigation_time_s": round(navigation_time, 2),
                "memory_increase_mb": round(end_mem - start_mem, 2),
                "cpu_usage_percent": round(end_cpu - start_cpu, 2),
                "avg_time_per_browser_s": round((launch_time + navigation_time) / concurrency, 2)
            }
            
            # Cleanup
            for browser in browsers:
                await browser.close()
        
        await playwright.stop()
        return results
    
    async def test_data_usage(self) -> Dict[str, Any]:
        """Test data usage optimization."""
        results = {
            "standard_browsing": {},
            "optimized_browsing": {},
            "savings": {}
        }
        
        playwright = await async_playwright().start()
        
        # Test pages
        test_pages = [
            "https://www.fansale.it",
            "https://www.ticketmaster.it",
            "https://www.vivaticket.com"
        ]
        
        for mode in ["standard", "optimized"]:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            
            total_data = 0
            total_requests = 0
            blocked_resources = 0
            
            def on_request(request):
                nonlocal total_requests, blocked_resources
                total_requests += 1
                
                if mode == "optimized":
                    resource_type = request.resource_type
                    if resource_type in ["image", "media", "font", "stylesheet"]:
                        blocked_resources += 1
            
            def on_response(response):
                nonlocal total_data
                if response.body_size:
                    total_data += response.body_size
            
            await context.route("**/*", lambda route: 
                route.abort() if mode == "optimized" and 
                route.request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            )
            
            # Navigate to test pages
            page = await context.new_page()
            page.on("request", on_request)
            page.on("response", on_response)
            
            for url in test_pages:
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                except:
                    pass
            
            results[f"{mode}_browsing"] = {
                "total_data_mb": round(total_data / 1024 / 1024, 2),
                "total_requests": total_requests,
                "blocked_resources": blocked_resources,
                "avg_data_per_page_mb": round((total_data / 1024 / 1024) / len(test_pages), 2)
            }
            
            await browser.close()
        
        # Calculate savings
        if results["standard_browsing"]["total_data_mb"] > 0:
            savings_mb = results["standard_browsing"]["total_data_mb"] - results["optimized_browsing"]["total_data_mb"]
            savings_percent = (savings_mb / results["standard_browsing"]["total_data_mb"]) * 100
            
            results["savings"] = {
                "data_saved_mb": round(savings_mb, 2),
                "data_saved_percent": round(savings_percent, 2),
                "requests_blocked": results["optimized_browsing"]["blocked_resources"],
                "requests_blocked_percent": round(
                    (results["optimized_browsing"]["blocked_resources"] / 
                     results["standard_browsing"]["total_requests"]) * 100, 2
                )
            }
        
        await playwright.stop()
        return results
    
    def _save_results(self):
        """Save test results to file."""
        results_file = Path("tests/performance_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Results saved to: {results_file}")
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and provide recommendations."""
        analysis = {
            "performance_issues": [],
            "optimization_opportunities": [],
            "security_concerns": [],
            "recommendations": []
        }
        
        # Analyze startup performance
        startup = self.results["tests"].get("startup_performance", {})
        if startup.get("total_startup_ms", {}).get("mean", 0) > 5000:
            analysis["performance_issues"].append({
                "issue": "Slow startup time",
                "current": f"{startup['total_startup_ms']['mean']}ms",
                "target": "< 5000ms",
                "impact": "high"
            })
        
        # Analyze memory usage
        memory = self.results["tests"].get("memory_usage", {})
        if memory.get("peak_memory_mb", 0) > 500:
            analysis["performance_issues"].append({
                "issue": "High memory usage",
                "current": f"{memory['peak_memory_mb']}MB",
                "target": "< 500MB",
                "impact": "medium"
            })
        
        if memory.get("memory_leaks"):
            analysis["performance_issues"].append({
                "issue": "Potential memory leaks detected",
                "components": [leak["component"] for leak in memory["memory_leaks"]],
                "impact": "high"
            })
        
        # Analyze network performance
        network = self.results["tests"].get("network_performance", {})
        if network.get("standard_load_time_s", 0) > 10:
            analysis["optimization_opportunities"].append({
                "area": "Network optimization",
                "current_load_time": f"{network.get('standard_load_time_s')}s",
                "optimized_load_time": f"{network.get('optimized_load_time_s')}s",
                "potential_improvement": "Enable request filtering"
            })
        
        # Analyze bot detection
        detection = self.results["tests"].get("bot_detection", {})
        failed_tests = []
        for test_name, result in detection.get("detection_tests", {}).items():
            if not result.get("passed", True):
                failed_tests.append(test_name)
        
        if failed_tests:
            analysis["security_concerns"].append({
                "issue": "Failed bot detection tests",
                "failed_tests": failed_tests,
                "risk": "high"
            })
        
        # Analyze fingerprint uniqueness
        fingerprint = self.results["tests"].get("fingerprint_uniqueness", {})
        if fingerprint.get("uniqueness_test", {}).get("uniqueness_ratio", 0) < 0.95:
            analysis["security_concerns"].append({
                "issue": "Low fingerprint uniqueness",
                "uniqueness_ratio": fingerprint["uniqueness_test"]["uniqueness_ratio"],
                "target": "> 0.95",
                "risk": "medium"
            })
        
        # Generate recommendations
        if analysis["performance_issues"]:
            analysis["recommendations"].append({
                "priority": "high",
                "action": "Optimize startup performance",
                "details": "Consider lazy loading and async initialization"
            })
        
        if analysis["optimization_opportunities"]:
            analysis["recommendations"].append({
                "priority": "medium",
                "action": "Implement resource blocking",
                "details": "Block unnecessary resources (images, fonts, etc.) to reduce data usage"
            })
        
        if analysis["security_concerns"]:
            analysis["recommendations"].append({
                "priority": "critical",
                "action": "Enhance stealth measures",
                "details": "Review and update bot detection evasion techniques"
            })
        
        return analysis


async def main():
    """Run performance tests."""
    test_suite = PerformanceTestSuite()
    
    # Run all tests
    results = await test_suite.run_all_tests()
    
    # Analyze results
    print("\n" + "="*60)
    print("📊 PERFORMANCE TEST ANALYSIS")
    print("="*60)
    
    analysis = test_suite.analyze_results()
    
    # Print summary
    print("\n🔍 Performance Issues Found:")
    if analysis["performance_issues"]:
        for issue in analysis["performance_issues"]:
            print(f"  ⚠️  {issue['issue']} - Current: {issue.get('current', 'N/A')} (Impact: {issue['impact']})")
    else:
        print("  ✅ No significant performance issues detected")
    
    print("\n💡 Optimization Opportunities:")
    if analysis["optimization_opportunities"]:
        for opp in analysis["optimization_opportunities"]:
            print(f"  📈 {opp['area']} - {opp.get('potential_improvement', 'Available')}")
    else:
        print("  ✅ System is well optimized")
    
    print("\n🔒 Security Concerns:")
    if analysis["security_concerns"]:
        for concern in analysis["security_concerns"]:
            print(f"  🚨 {concern['issue']} (Risk: {concern['risk']})")
    else:
        print("  ✅ No security concerns detected")
    
    print("\n📋 Recommendations:")
    for rec in analysis["recommendations"]:
        print(f"  [{rec['priority'].upper()}] {rec['action']}")
        print(f"         {rec['details']}")
    
    print("\n" + "="*60)
    print(f"Full results saved to: tests/performance_test_results.json")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())