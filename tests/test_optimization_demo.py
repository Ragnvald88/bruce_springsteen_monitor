#!/usr/bin/env python3
"""Demonstration of data optimization effectiveness."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright

# Create the DataOptimizer class inline to avoid import issues
class DataOptimizer:
    """Optimizes data usage by blocking unnecessary resources."""
    
    OPTIMIZATION_LEVELS = {
        "minimal": {
            "block": {"font", "media"},
            "allow_domains": set(),
            "block_domains": set()
        },
        "moderate": {
            "block": {"font", "media", "image"},
            "allow_domains": set(),
            "block_domains": {"googletagmanager.com", "google-analytics.com", "doubleclick.net", "facebook.com"}
        },
        "aggressive": {
            "block": {"font", "media", "image", "stylesheet"},
            "allow_domains": set(),
            "block_domains": {"googletagmanager.com", "google-analytics.com", "doubleclick.net", 
                            "facebook.com", "twitter.com", "pinterest.com", "linkedin.com",
                            "cloudflare.com", "cookielaw.org", "cookiebot.com"}
        },
        "extreme": {
            "block": {"font", "media", "image", "stylesheet", "websocket", "manifest", "other"},
            "allow_domains": {"ticketmaster.it", "fansale.it", "vivaticket.com"},
            "block_domains": set(),
            "block_third_party_scripts": True
        }
    }
    
    def __init__(self, level: str = "moderate"):
        self.level = level
        self.config = self.OPTIMIZATION_LEVELS.get(level, self.OPTIMIZATION_LEVELS["moderate"])
        self.stats = {
            "requests_blocked": 0,
            "requests_allowed": 0,
            "data_saved_bytes": 0,
            "blocked_by_type": {}
        }
        
    async def setup_context(self, context):
        await context.route("**/*", self._handle_route)
    
    async def _handle_route(self, route):
        request = route.request
        
        if self._should_block(request):
            self.stats["requests_blocked"] += 1
            resource_type = request.resource_type
            self.stats["blocked_by_type"][resource_type] = self.stats["blocked_by_type"].get(resource_type, 0) + 1
            
            estimated_sizes = {
                "image": 50 * 1024,
                "stylesheet": 30 * 1024,
                "font": 40 * 1024,
                "media": 500 * 1024,
                "script": 50 * 1024,
                "other": 10 * 1024
            }
            self.stats["data_saved_bytes"] += estimated_sizes.get(resource_type, 10 * 1024)
            
            await route.abort()
        else:
            self.stats["requests_allowed"] += 1
            await route.continue_()
    
    def _should_block(self, request):
        url = request.url
        resource_type = request.resource_type
        
        if resource_type == "document":
            return False
        
        if resource_type in self.config["block"]:
            return True
        
        domain = self._extract_domain(url)
        
        if self.config["allow_domains"]:
            if not any(allowed in domain for allowed in self.config["allow_domains"]):
                return True
        
        if any(blocked in domain for blocked in self.config["block_domains"]):
            return True
        
        if self.config.get("block_third_party_scripts") and resource_type == "script":
            if not any(allowed in domain for allowed in self.config.get("allow_domains", [])):
                return True
        
        tracking_patterns = [
            "analytics", "tracking", "metrics", "telemetry", "beacon",
            "pixel", "tag", "gtm", "_ga", "matomo", "piwik", "hotjar",
            "segment", "mixpanel", "amplitude", "heap", "fullstory"
        ]
        if any(pattern in url.lower() for pattern in tracking_patterns):
            return True
        
        ad_patterns = [
            "doubleclick", "adsystem", "adserver", "adtech", "adzerk",
            "advertising", "amazon-adsystem", "googlesyndication", "adnxs",
            "adsafeprotected", "teads", "smartadserver"
        ]
        if any(pattern in url.lower() for pattern in ad_patterns):
            return True
        
        return False
    
    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def get_stats(self):
        total_requests = self.stats["requests_blocked"] + self.stats["requests_allowed"]
        block_rate = (self.stats["requests_blocked"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "level": self.level,
            "requests_blocked": self.stats["requests_blocked"],
            "requests_allowed": self.stats["requests_allowed"],
            "block_rate_percent": round(block_rate, 1),
            "data_saved_mb": round(self.stats["data_saved_bytes"] / (1024 * 1024), 2),
            "blocked_by_type": self.stats["blocked_by_type"]
        }

# Create StealthCore inline
class StealthCore:
    async def apply_context_stealth(self, context):
        # Add stealth scripts before page creation
        await context.add_init_script("""
            // Hide webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Add minimal plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const arr = [];
                    arr.length = 0;
                    Object.setPrototypeOf(arr, PluginArray.prototype);
                    return arr;
                },
                configurable: true
            });
        """)
    
    async def apply_page_stealth(self, page):
        # Basic page-level stealth
        pass


async def test_data_optimization():
    """Test and demonstrate data optimization."""
    print("🚀 Data Optimization Demonstration\n")
    
    playwright = await async_playwright().start()
    
    # Test sites
    test_urls = [
        "https://www.ticketmaster.it",
        "https://www.vivaticket.com"
    ]
    
    # Test different optimization levels
    optimization_levels = ["none", "minimal", "moderate", "aggressive", "extreme"]
    
    results = {}
    
    for level in optimization_levels:
        print(f"\n📊 Testing {level} optimization...")
        
        # Create browser with optimization
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
        )
        
        context = await browser.new_context()
        
        # Apply optimization if not "none"
        optimizer = None
        if level != "none":
            optimizer = DataOptimizer(level)
            await optimizer.setup_context(context)
        
        # Apply stealth
        stealth = StealthCore()
        await stealth.apply_context_stealth(context)
        
        page = await context.new_page()
        
        # Track data usage
        total_data = 0
        request_count = 0
        
        async def on_response(response):
            nonlocal total_data, request_count
            request_count += 1
            try:
                body = await response.body()
                total_data += len(body)
            except:
                pass
        
        if level == "none":
            page.on("response", on_response)
        
        # Visit sites
        for url in test_urls:
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)  # Let lazy content load
            except Exception as e:
                print(f"  ❌ Error loading {url}: {str(e)[:50]}")
        
        # Get stats
        if optimizer:
            stats = optimizer.get_stats()
            results[level] = {
                "data_saved_mb": stats["data_saved_mb"],
                "requests_blocked": stats["requests_blocked"],
                "requests_allowed": stats["requests_allowed"],
                "block_rate": stats["block_rate_percent"]
            }
            print(f"  ✅ Blocked {stats['requests_blocked']} requests ({stats['block_rate_percent']}%)")
            print(f"  💾 Estimated data saved: {stats['data_saved_mb']}MB")
        else:
            results[level] = {
                "total_data_mb": round(total_data / (1024 * 1024), 2),
                "total_requests": request_count
            }
            print(f"  📊 Total data: {results[level]['total_data_mb']}MB in {request_count} requests")
        
        await browser.close()
    
    await playwright.stop()
    
    # Print comparison
    print("\n" + "="*60)
    print("DATA OPTIMIZATION COMPARISON")
    print("="*60)
    
    baseline = results.get("none", {})
    baseline_data = baseline.get("total_data_mb", 0)
    baseline_requests = baseline.get("total_requests", 0)
    
    print(f"\nBaseline (no optimization):")
    print(f"  Data: {baseline_data}MB")
    print(f"  Requests: {baseline_requests}")
    
    for level in ["minimal", "moderate", "aggressive", "extreme"]:
        if level in results:
            stats = results[level]
            print(f"\n{level.capitalize()} optimization:")
            print(f"  Requests blocked: {stats['requests_blocked']} ({stats['block_rate']}%)")
            print(f"  Data saved: {stats['data_saved_mb']}MB")
            
            # Calculate savings vs baseline
            if baseline_data > 0:
                est_remaining = baseline_data - stats['data_saved_mb']
                savings_pct = (stats['data_saved_mb'] / baseline_data) * 100
                print(f"  Estimated savings: {savings_pct:.1f}%")
    
    print("\n" + "="*60)


async def test_bot_detection_improvements():
    """Test bot detection improvements."""
    print("\n🤖 Bot Detection Improvements Test\n")
    
    playwright = await async_playwright().start()
    
    # Test configurations
    configs = [
        ("Old headless", {"headless": True}, False),
        ("Improved headless", {"headless": True}, True),
    ]
    
    for name, launch_opts, use_improved in configs:
        print(f"\nTesting {name}...")
        
        if use_improved:
            # Use improved launcher
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                ]
            )
        else:
            browser = await playwright.chromium.launch(**launch_opts)
        
        context = await browser.new_context()
        
        # Apply stealth
        stealth = StealthCore()
        await stealth.apply_context_stealth(context)
        
        page = await context.new_page()
        await stealth.apply_page_stealth(page)
        
        # Test detection
        await page.goto("https://bot.sannysoft.com/", wait_until="networkidle")
        
        # Check key indicators
        checks = await page.evaluate("""
            () => ({
                webdriver: navigator.webdriver,
                userAgent: navigator.userAgent,
                headlessInUA: /HeadlessChrome/.test(navigator.userAgent),
                plugins: navigator.plugins.length,
                chrome: !!window.chrome
            })
        """)
        
        print(f"  Webdriver: {checks['webdriver']}")
        print(f"  Headless in UA: {checks['headlessInUA']}")
        print(f"  Plugins: {checks['plugins']}")
        print(f"  Chrome object: {checks['chrome']}")
        print(f"  User Agent: {checks['userAgent'][:50]}...")
        
        await browser.close()
    
    await playwright.stop()


async def test_real_world_scenario():
    """Test real-world ticketing scenario with optimizations."""
    print("\n🎟️ Real-World Ticketing Scenario Test\n")
    
    playwright = await async_playwright().start()
    
    # Create optimized browser
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "--window-size=1920,1080"
        ]
    )
    
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="it-IT",
        timezone_id="Europe/Rome"
    )
    
    # Apply aggressive optimization
    optimizer = DataOptimizer("aggressive")
    await optimizer.setup_context(context)
    
    # Apply stealth
    stealth = StealthCore()
    await stealth.apply_context_stealth(context)
    
    page = await context.new_page()
    await stealth.apply_page_stealth(page)
    
    print("Testing Ticketmaster Italy with optimizations...")
    
    # Measure performance
    start = time.perf_counter()
    
    try:
        # Navigate to main page
        await page.goto("https://www.ticketmaster.it", wait_until="domcontentloaded")
        print(f"  ✅ Main page loaded in {time.perf_counter() - start:.2f}s")
        
        # Search for concerts
        search_start = time.perf_counter()
        await page.goto("https://www.ticketmaster.it/browse/concerti-catid-10001/musica-tickets-it/category", 
                       wait_until="domcontentloaded")
        print(f"  ✅ Concert list loaded in {time.perf_counter() - search_start:.2f}s")
        
        # Get optimization stats
        stats = optimizer.get_stats()
        print(f"\n📊 Optimization Results:")
        print(f"  Requests blocked: {stats['requests_blocked']}")
        print(f"  Data saved: {stats['data_saved_mb']}MB")
        print(f"  Block rate: {stats['block_rate_percent']}%")
        
        # Check if page is functional
        has_events = await page.evaluate("() => document.querySelectorAll('[data-event-id]').length > 0")
        print(f"  Page functional: {'✅ Yes' if has_events else '❌ No'}")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    await browser.close()
    await playwright.stop()


async def main():
    """Run all optimization tests."""
    
    # Test 1: Data optimization levels
    await test_data_optimization()
    
    # Test 2: Bot detection improvements
    await test_bot_detection_improvements()
    
    # Test 3: Real-world scenario
    await test_real_world_scenario()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())