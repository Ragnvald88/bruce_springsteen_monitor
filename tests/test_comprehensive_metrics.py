#!/usr/bin/env python3
"""Comprehensive metrics test suite for StealthMaster with detailed data usage analysis."""

import asyncio
import time
import psutil
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config import load_settings
from stealth.core import StealthCore
from stealth.fingerprint import FingerprintGenerator
from browser.launcher import BrowserLauncher
from playwright.async_api import async_playwright, Page, Route, Request, Response


class ComprehensiveMetricsTest:
    """Comprehensive test suite with detailed metrics."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "data_analysis": {},
            "recommendations": []
        }
        self.settings = load_settings(Path("config.yaml"))
        
    async def run_all_tests(self):
        """Run comprehensive test suite."""
        print("🚀 Starting Comprehensive Metrics Test Suite...\n")
        
        # Test 1: Data Usage Analysis
        print("📊 Test 1: Data Usage Analysis")
        data_results = await self.test_data_usage_detailed()
        self.results["tests"]["data_usage"] = data_results
        
        # Test 2: Page Load Performance
        print("\n📊 Test 2: Page Load Performance")
        load_results = await self.test_page_load_performance()
        self.results["tests"]["page_load"] = load_results
        
        # Test 3: Resource Analysis
        print("\n📊 Test 3: Resource Type Analysis")
        resource_results = await self.test_resource_analysis()
        self.results["tests"]["resource_analysis"] = resource_results
        
        # Test 4: Network Latency
        print("\n📊 Test 4: Network Latency Impact")
        latency_results = await self.test_network_latency()
        self.results["tests"]["network_latency"] = latency_results
        
        # Test 5: Bot Detection Deep Dive
        print("\n📊 Test 5: Bot Detection Deep Analysis")
        detection_results = await self.test_bot_detection_detailed()
        self.results["tests"]["bot_detection_detailed"] = detection_results
        
        # Test 6: Optimization Impact
        print("\n📊 Test 6: Optimization Impact Analysis")
        optimization_results = await self.test_optimization_impact()
        self.results["tests"]["optimization_impact"] = optimization_results
        
        # Analyze and save results
        self._analyze_results()
        self._save_results()
        
        return self.results
    
    async def test_data_usage_detailed(self) -> Dict[str, Any]:
        """Detailed data usage analysis across different sites."""
        results = {
            "sites": {},
            "total_data_mb": 0,
            "average_per_site_mb": 0,
            "resource_breakdown": {}
        }
        
        test_sites = [
            ("Fansale", "https://www.fansale.it"),
            ("Ticketmaster", "https://www.ticketmaster.it"),
            ("Vivaticket", "https://www.vivaticket.com"),
            ("Example (baseline)", "https://www.example.com")
        ]
        
        playwright = await async_playwright().start()
        
        for site_name, url in test_sites:
            print(f"  Testing {site_name}...", end="\r")
            
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Track all network activity
            resources = {
                "document": {"count": 0, "size": 0},
                "stylesheet": {"count": 0, "size": 0},
                "image": {"count": 0, "size": 0},
                "media": {"count": 0, "size": 0},
                "font": {"count": 0, "size": 0},
                "script": {"count": 0, "size": 0},
                "xhr": {"count": 0, "size": 0},
                "fetch": {"count": 0, "size": 0},
                "other": {"count": 0, "size": 0}
            }
            
            total_size = 0
            request_count = 0
            
            async def on_response(response: Response):
                nonlocal total_size, request_count
                request_count += 1
                
                try:
                    # Get response size
                    body = await response.body()
                    size = len(body)
                    total_size += size
                    
                    # Categorize by resource type
                    resource_type = response.request.resource_type
                    if resource_type in resources:
                        resources[resource_type]["count"] += 1
                        resources[resource_type]["size"] += size
                    else:
                        resources["other"]["count"] += 1
                        resources["other"]["size"] += size
                except:
                    pass
            
            page.on("response", on_response)
            
            # Navigate and measure
            start_time = time.perf_counter()
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                load_time = time.perf_counter() - start_time
            except Exception as e:
                load_time = -1
                print(f"  ❌ {site_name} failed: {str(e)[:50]}")
            
            await asyncio.sleep(2)  # Let any lazy-loaded content load
            
            # Calculate totals
            total_mb = total_size / (1024 * 1024)
            
            results["sites"][site_name] = {
                "url": url,
                "total_size_mb": round(total_mb, 2),
                "request_count": request_count,
                "load_time_s": round(load_time, 2),
                "resources": {k: {"count": v["count"], "size_mb": round(v["size"]/(1024*1024), 2)} 
                            for k, v in resources.items() if v["count"] > 0}
            }
            
            results["total_data_mb"] += total_mb
            
            # Update resource breakdown
            for rtype, data in resources.items():
                if rtype not in results["resource_breakdown"]:
                    results["resource_breakdown"][rtype] = {"count": 0, "size_mb": 0}
                results["resource_breakdown"][rtype]["count"] += data["count"]
                results["resource_breakdown"][rtype]["size_mb"] += data["size"] / (1024 * 1024)
            
            await browser.close()
            
            print(f"  ✅ {site_name}: {total_mb:.1f}MB in {request_count} requests")
        
        await playwright.stop()
        
        # Calculate averages
        results["average_per_site_mb"] = round(results["total_data_mb"] / len(test_sites), 2)
        results["total_data_mb"] = round(results["total_data_mb"], 2)
        
        # Round resource breakdown
        for rtype in results["resource_breakdown"]:
            results["resource_breakdown"][rtype]["size_mb"] = round(
                results["resource_breakdown"][rtype]["size_mb"], 2
            )
        
        return results
    
    async def test_page_load_performance(self) -> Dict[str, Any]:
        """Test page load performance metrics."""
        results = {
            "metrics": [],
            "average_metrics": {}
        }
        
        playwright = await async_playwright().start()
        
        for i in range(3):
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Apply stealth
            stealth = StealthCore()
            await stealth.apply_page_stealth(page)
            
            # Measure performance metrics
            await page.goto("https://www.ticketmaster.it", wait_until="domcontentloaded")
            
            metrics = await page.evaluate("""
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    return {
                        dns_lookup_ms: perf.domainLookupEnd - perf.domainLookupStart,
                        tcp_connect_ms: perf.connectEnd - perf.connectStart,
                        request_ms: perf.responseStart - perf.requestStart,
                        response_ms: perf.responseEnd - perf.responseStart,
                        dom_processing_ms: perf.domComplete - perf.domInteractive,
                        dom_content_loaded_ms: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                        total_load_ms: perf.loadEventEnd - perf.fetchStart,
                        first_paint_ms: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        first_contentful_paint_ms: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                    };
                }
            """)
            
            results["metrics"].append(metrics)
            await browser.close()
        
        await playwright.stop()
        
        # Calculate averages
        if results["metrics"]:
            avg_metrics = {}
            for key in results["metrics"][0].keys():
                values = [m[key] for m in results["metrics"]]
                avg_metrics[key] = round(statistics.mean(values), 2)
            results["average_metrics"] = avg_metrics
        
        return results
    
    async def test_resource_analysis(self) -> Dict[str, Any]:
        """Analyze resource types and their impact."""
        results = {
            "blocking_impact": {},
            "resource_timing": {}
        }
        
        playwright = await async_playwright().start()
        
        # Test with different resource blocking strategies
        blocking_strategies = [
            ("none", []),
            ("images", ["image"]),
            ("css_fonts", ["stylesheet", "font"]),
            ("media", ["image", "media", "font"]),
            ("aggressive", ["image", "media", "font", "stylesheet"])
        ]
        
        for strategy_name, blocked_types in blocking_strategies:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            
            if blocked_types:
                await context.route("**/*", lambda route: 
                    route.abort() if route.request.resource_type in blocked_types
                    else route.continue_()
                )
            
            page = await context.new_page()
            
            # Measure load time and data
            start = time.perf_counter()
            data_size = 0
            request_count = 0
            
            async def on_response(response: Response):
                nonlocal data_size, request_count
                request_count += 1
                try:
                    body = await response.body()
                    data_size += len(body)
                except:
                    pass
            
            page.on("response", on_response)
            
            try:
                await page.goto("https://www.ticketmaster.it", wait_until="networkidle", timeout=30000)
                load_time = time.perf_counter() - start
                
                # Check if page is functional
                has_content = await page.evaluate("() => document.body.innerText.length > 100")
                
                results["blocking_impact"][strategy_name] = {
                    "blocked_types": blocked_types,
                    "load_time_s": round(load_time, 2),
                    "data_mb": round(data_size / (1024 * 1024), 2),
                    "requests": request_count,
                    "functional": has_content
                }
            except Exception as e:
                results["blocking_impact"][strategy_name] = {
                    "error": str(e)[:100],
                    "blocked_types": blocked_types
                }
            
            await browser.close()
        
        await playwright.stop()
        
        return results
    
    async def test_network_latency(self) -> Dict[str, Any]:
        """Test impact of network latency on performance."""
        results = {}
        
        playwright = await async_playwright().start()
        
        # Different latency scenarios (in ms)
        latencies = [0, 100, 300, 500]
        
        for latency in latencies:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Add artificial latency
            if latency > 0:
                await context.route("**/*", lambda route: 
                    asyncio.create_task(self._delayed_continue(route, latency))
                )
            
            page = await context.new_page()
            
            start = time.perf_counter()
            try:
                await page.goto("https://www.example.com", wait_until="networkidle", timeout=30000)
                load_time = time.perf_counter() - start
                
                results[f"{latency}ms"] = {
                    "load_time_s": round(load_time, 2),
                    "latency_impact_s": round(load_time - results.get("0ms", {}).get("load_time_s", 0), 2) if latency > 0 else 0
                }
            except Exception as e:
                results[f"{latency}ms"] = {"error": str(e)[:50]}
            
            await browser.close()
        
        await playwright.stop()
        
        return results
    
    async def _delayed_continue(self, route: Route, delay_ms: int):
        """Helper to add delay to requests."""
        await asyncio.sleep(delay_ms / 1000)
        await route.continue_()
    
    async def test_bot_detection_detailed(self) -> Dict[str, Any]:
        """Detailed bot detection analysis."""
        results = {
            "detection_vectors": {},
            "evasion_effectiveness": {}
        }
        
        playwright = await async_playwright().start()
        
        # Test different configurations
        configs = [
            ("baseline", {"headless": True}, False),
            ("with_stealth", {"headless": True}, True),
            ("headed", {"headless": False}, True),
            ("custom_args", {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ]
            }, True)
        ]
        
        for config_name, launch_options, apply_stealth in configs:
            print(f"  Testing {config_name} configuration...", end="\r")
            
            browser = await playwright.chromium.launch(**launch_options)
            page = await browser.new_page()
            
            if apply_stealth:
                stealth = StealthCore()
                await stealth.apply_page_stealth(page)
            
            # Navigate to detection test
            await page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=30000)
            
            # Run comprehensive checks
            detection_results = await page.evaluate("""
                () => {
                    const results = {
                        webdriver: navigator.webdriver,
                        webdriver_in_window: 'webdriver' in window,
                        chrome_runtime: !!window.chrome && !!window.chrome.runtime,
                        permissions_query: typeof navigator.permissions?.query === 'function',
                        plugins_length: navigator.plugins.length,
                        plugins_type: Object.prototype.toString.call(navigator.plugins),
                        languages: navigator.languages.join(','),
                        user_agent: navigator.userAgent,
                        headless_chrome: /HeadlessChrome/.test(navigator.userAgent),
                        automation_controlled: /Chrome.*Headless/.test(navigator.userAgent),
                        cdc_props: Object.keys(window).filter(k => k.includes('cdc_')).length,
                        selenium_props: Object.keys(window).filter(k => k.includes('selenium')).length,
                        webgl_vendor: (() => {
                            try {
                                const canvas = document.createElement('canvas');
                                const gl = canvas.getContext('webgl');
                                return gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_VENDOR_WEBGL);
                            } catch { return 'error'; }
                        })(),
                        canvas_test: (() => {
                            try {
                                const canvas = document.createElement('canvas');
                                const ctx = canvas.getContext('2d');
                                ctx.font = '14px Arial';
                                ctx.fillText('test', 2, 15);
                                return canvas.toDataURL().length > 0;
                            } catch { return false; }
                        })()
                    };
                    
                    // Count detections
                    results.detection_count = 0;
                    if (results.webdriver !== undefined) results.detection_count++;
                    if (results.plugins_length === 0) results.detection_count++;
                    if (results.headless_chrome) results.detection_count++;
                    if (results.cdc_props > 0) results.detection_count++;
                    if (results.selenium_props > 0) results.detection_count++;
                    
                    return results;
                }
            """)
            
            results["detection_vectors"][config_name] = detection_results
            
            # Take screenshot for analysis
            await page.screenshot(path=f"tests/bot_detection_{config_name}.png")
            
            await browser.close()
            
            print(f"  ✅ {config_name}: {detection_results['detection_count']} detections")
        
        await playwright.stop()
        
        return results
    
    async def test_optimization_impact(self) -> Dict[str, Any]:
        """Test impact of various optimizations."""
        results = {
            "optimizations": {}
        }
        
        playwright = await async_playwright().start()
        
        # Different optimization configurations
        optimizations = [
            ("baseline", {}),
            ("block_images", {"block": ["image"]}),
            ("block_media", {"block": ["image", "media", "font"]}),
            ("aggressive", {"block": ["image", "media", "font", "stylesheet"]}),
            ("cache_enabled", {"cache": True}),
            ("combined", {"block": ["image", "media"], "cache": True})
        ]
        
        for opt_name, config in optimizations:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Apply blocking if configured
            if "block" in config:
                await context.route("**/*", lambda route: 
                    route.abort() if route.request.resource_type in config["block"]
                    else route.continue_()
                )
            
            page = await context.new_page()
            
            # Measure metrics
            start = time.perf_counter()
            data_size = 0
            cache_hits = 0
            
            async def on_response(response: Response):
                nonlocal data_size, cache_hits
                try:
                    if response.from_service_worker:
                        cache_hits += 1
                    body = await response.body()
                    data_size += len(body)
                except:
                    pass
            
            page.on("response", on_response)
            
            # Test on multiple pages to see cache effect
            pages_to_test = [
                "https://www.ticketmaster.it",
                "https://www.ticketmaster.it/browse/concerti-catid-10001/musica-tickets-it/category",
                "https://www.ticketmaster.it"  # Revisit to test cache
            ]
            
            total_load_time = 0
            for url in pages_to_test:
                page_start = time.perf_counter()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    total_load_time += time.perf_counter() - page_start
                except:
                    pass
            
            results["optimizations"][opt_name] = {
                "config": config,
                "total_load_time_s": round(total_load_time, 2),
                "data_mb": round(data_size / (1024 * 1024), 2),
                "cache_hits": cache_hits,
                "avg_page_load_s": round(total_load_time / len(pages_to_test), 2)
            }
            
            await browser.close()
        
        await playwright.stop()
        
        return results
    
    def _analyze_results(self):
        """Analyze results and generate recommendations."""
        analysis = self.results["data_analysis"]
        
        # Data usage analysis
        data_usage = self.results["tests"]["data_usage"]
        analysis["total_data_consumption"] = {
            "average_site_mb": data_usage["average_per_site_mb"],
            "heaviest_resources": sorted(
                data_usage["resource_breakdown"].items(),
                key=lambda x: x[1]["size_mb"],
                reverse=True
            )[:3]
        }
        
        # Optimization effectiveness
        if "optimization_impact" in self.results["tests"]:
            opt_impact = self.results["tests"]["optimization_impact"]["optimizations"]
            baseline = opt_impact.get("baseline", {})
            
            analysis["optimization_savings"] = {}
            for opt_name, data in opt_impact.items():
                if opt_name != "baseline" and baseline:
                    savings_mb = baseline.get("data_mb", 0) - data.get("data_mb", 0)
                    savings_pct = (savings_mb / baseline.get("data_mb", 1)) * 100 if baseline.get("data_mb", 0) > 0 else 0
                    
                    analysis["optimization_savings"][opt_name] = {
                        "data_saved_mb": round(savings_mb, 2),
                        "data_saved_percent": round(savings_pct, 1),
                        "speed_impact_s": round(data.get("avg_page_load_s", 0) - baseline.get("avg_page_load_s", 0), 2)
                    }
        
        # Bot detection analysis
        if "bot_detection_detailed" in self.results["tests"]:
            detection_data = self.results["tests"]["bot_detection_detailed"]["detection_vectors"]
            
            analysis["bot_detection_summary"] = {}
            for config, results in detection_data.items():
                analysis["bot_detection_summary"][config] = {
                    "detections": results.get("detection_count", 0),
                    "webdriver_hidden": results.get("webdriver") is None or results.get("webdriver") is False,
                    "plugins_present": results.get("plugins_length", 0) > 0,
                    "headless_hidden": not results.get("headless_chrome", False)
                }
        
        # Generate recommendations
        recommendations = []
        
        # Data optimization recommendations
        if data_usage["average_per_site_mb"] > 5:
            recommendations.append({
                "priority": "HIGH",
                "category": "Data Usage",
                "issue": f"High data consumption: {data_usage['average_per_site_mb']}MB average per site",
                "recommendation": "Implement aggressive resource blocking for images, media, and fonts",
                "potential_savings": "60-80% data reduction"
            })
        
        # Bot detection recommendations
        if analysis.get("bot_detection_summary", {}).get("with_stealth", {}).get("detections", 0) > 2:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Bot Detection",
                "issue": "Multiple bot detection vectors still active",
                "recommendation": "Enhance stealth measures with better plugin emulation and WebGL spoofing",
                "impact": "Reduced risk of blocking"
            })
        
        # Performance recommendations
        if self.results["tests"].get("page_load", {}).get("average_metrics", {}).get("total_load_ms", 0) > 5000:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Performance",
                "issue": "Slow page load times",
                "recommendation": "Enable caching and connection pooling",
                "potential_improvement": "30-50% faster loads"
            })
        
        self.results["recommendations"] = recommendations
    
    def _save_results(self):
        """Save detailed results."""
        results_file = Path("tests/comprehensive_metrics_results.json")
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: {results_file}")
        
        # Generate summary report
        self._generate_summary_report()
    
    def _generate_summary_report(self):
        """Generate human-readable summary report."""
        report = []
        report.append("=" * 60)
        report.append("COMPREHENSIVE METRICS TEST SUMMARY")
        report.append("=" * 60)
        
        # Data Usage Summary
        data_usage = self.results["tests"]["data_usage"]
        report.append("\n📊 DATA USAGE ANALYSIS:")
        report.append(f"  Average per site: {data_usage['average_per_site_mb']}MB")
        report.append("  Resource breakdown:")
        for rtype, data in sorted(data_usage["resource_breakdown"].items(), 
                                 key=lambda x: x[1]["size_mb"], reverse=True)[:5]:
            report.append(f"    - {rtype}: {data['size_mb']}MB ({data['count']} requests)")
        
        # Optimization Impact
        if "optimization_savings" in self.results["data_analysis"]:
            report.append("\n💡 OPTIMIZATION EFFECTIVENESS:")
            for opt, savings in self.results["data_analysis"]["optimization_savings"].items():
                report.append(f"  {opt}: {savings['data_saved_percent']:.1f}% data saved")
        
        # Bot Detection
        if "bot_detection_summary" in self.results["data_analysis"]:
            report.append("\n🤖 BOT DETECTION STATUS:")
            for config, status in self.results["data_analysis"]["bot_detection_summary"].items():
                report.append(f"  {config}: {status['detections']} detections")
        
        # Recommendations
        report.append("\n📋 TOP RECOMMENDATIONS:")
        for rec in self.results["recommendations"][:3]:
            report.append(f"  [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        
        report.append("\n" + "=" * 60)
        
        # Print and save
        report_text = "\n".join(report)
        print(report_text)
        
        with open("tests/comprehensive_metrics_summary.txt", "w") as f:
            f.write(report_text)


async def main():
    """Run comprehensive metrics tests."""
    tester = ComprehensiveMetricsTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())