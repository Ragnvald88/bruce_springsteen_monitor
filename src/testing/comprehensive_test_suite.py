#!/usr/bin/env python3
"""
StealthMaster AI Comprehensive Test Suite v2.0
Identifies performance issues, bugs, and optimization opportunities
"""

import asyncio
import time
import psutil
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result tracking"""
    test_name: str
    category: str
    passed: bool
    duration: float
    memory_delta: float
    error: Optional[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class PerformanceMetrics:
    """Performance tracking"""
    browser_launch_time: float = 0.0
    context_creation_time: float = 0.0
    page_setup_time: float = 0.0
    navigation_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    concurrent_performance: Dict[str, float] = None
    
    def __post_init__(self):
        if self.concurrent_performance is None:
            self.concurrent_performance = {}


class ComprehensiveTestSuite:
    """Comprehensive testing framework"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.performance_metrics = PerformanceMetrics()
        self.start_time = time.time()
        self.process = psutil.Process()
        
    def log_test_start(self, test_name: str):
        """Log test start with formatting"""
        logger.info(f"\n{Fore.CYAN}{'='*60}")
        logger.info(f"{Fore.CYAN}🧪 TEST: {test_name}")
        logger.info(f"{Fore.CYAN}{'='*60}")
        
    def log_success(self, message: str):
        """Log success message"""
        logger.info(f"{Fore.GREEN}✅ {message}")
        
    def log_warning(self, message: str):
        """Log warning message"""
        logger.warning(f"{Fore.YELLOW}⚠️  {message}")
        
    def log_error(self, message: str):
        """Log error message"""
        logger.error(f"{Fore.RED}❌ {message}")
        
    def log_info(self, message: str):
        """Log info message"""
        logger.info(f"{Fore.BLUE}ℹ️  {message}")
        
    async def run_all_tests(self):
        """Run all tests"""
        self.log_test_start("COMPREHENSIVE TEST SUITE")
        
        # Performance baseline
        await self.test_performance_baseline()
        
        # Core functionality tests
        await self.test_core_imports()
        await self.test_browser_operations()
        await self.test_stealth_effectiveness()
        await self.test_concurrent_performance()
        await self.test_memory_leaks()
        await self.test_error_recovery()
        await self.test_platform_access()
        
        # Generate report
        self.generate_report()
        
    async def test_core_imports(self):
        """Test core module imports"""
        self.log_test_start("Core Module Imports")
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        test_imports = [
            ("stealth.stealth_engine", "StealthMasterEngine"),
            ("profiles.manager", "ProfileManager"),
            ("core.orchestrator", "UltimateOrchestrator"),
            ("platforms.unified_handler", "UnifiedTicketingHandler"),
            ("core.proxy_manager", "StealthProxyManager"),
        ]
        
        passed = True
        errors = []
        
        for module_path, class_name in test_imports:
            try:
                module = __import__(f"src.{module_path}", fromlist=[class_name])
                if hasattr(module, class_name):
                    self.log_success(f"Imported {class_name} from {module_path}")
                else:
                    self.log_error(f"Class {class_name} not found in {module_path}")
                    passed = False
                    errors.append(f"{class_name} not found")
            except Exception as e:
                self.log_error(f"Failed to import {module_path}: {str(e)}")
                passed = False
                errors.append(str(e))
        
        duration = time.time() - start_time
        memory_delta = self.process.memory_info().rss / 1024 / 1024 - memory_start
        
        self.results.append(TestResult(
            test_name="Core Imports",
            category="functionality",
            passed=passed,
            duration=duration,
            memory_delta=memory_delta,
            error="; ".join(errors) if errors else None
        ))
        
    async def test_performance_baseline(self):
        """Establish performance baseline"""
        self.log_test_start("Performance Baseline")
        
        # Memory baseline
        memory_info = self.process.memory_info()
        self.performance_metrics.memory_usage_mb = memory_info.rss / 1024 / 1024
        
        # CPU baseline
        self.performance_metrics.cpu_percent = self.process.cpu_percent(interval=1)
        
        self.log_info(f"Baseline Memory: {self.performance_metrics.memory_usage_mb:.1f} MB")
        self.log_info(f"Baseline CPU: {self.performance_metrics.cpu_percent:.1f}%")
        
    async def test_browser_operations(self):
        """Test browser launch and operations"""
        self.log_test_start("Browser Operations")
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        passed = True
        error = None
        
        try:
            async with async_playwright() as p:
                # Test browser launch
                launch_start = time.time()
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                self.performance_metrics.browser_launch_time = time.time() - launch_start
                self.log_success(f"Browser launched in {self.performance_metrics.browser_launch_time:.2f}s")
                
                # Test context creation
                context_start = time.time()
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                self.performance_metrics.context_creation_time = time.time() - context_start
                self.log_success(f"Context created in {self.performance_metrics.context_creation_time:.2f}s")
                
                # Test page operations
                page_start = time.time()
                page = await context.new_page()
                
                # Test CDP session
                try:
                    client = await context.new_cdp_session(page)
                    await client.send('Page.addScriptToEvaluateOnNewDocument', {
                        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
                    })
                    self.log_success("CDP session created successfully")
                except Exception as e:
                    self.log_warning(f"CDP session creation issue: {e}")
                
                self.performance_metrics.page_setup_time = time.time() - page_start
                self.log_success(f"Page setup completed in {self.performance_metrics.page_setup_time:.2f}s")
                
                # Test navigation
                nav_start = time.time()
                response = await page.goto('https://httpbin.org/headers', wait_until='networkidle')
                self.performance_metrics.navigation_time = time.time() - nav_start
                
                if response and response.ok:
                    self.log_success(f"Navigation successful in {self.performance_metrics.navigation_time:.2f}s")
                else:
                    self.log_warning(f"Navigation response: {response.status if response else 'None'}")
                
                await browser.close()
                
        except Exception as e:
            passed = False
            error = str(e)
            self.log_error(f"Browser operation failed: {error}")
            traceback.print_exc()
        
        duration = time.time() - start_time
        memory_delta = self.process.memory_info().rss / 1024 / 1024 - memory_start
        
        self.results.append(TestResult(
            test_name="Browser Operations",
            category="performance",
            passed=passed,
            duration=duration,
            memory_delta=memory_delta,
            error=error,
            metrics={
                "browser_launch": self.performance_metrics.browser_launch_time,
                "context_creation": self.performance_metrics.context_creation_time,
                "page_setup": self.performance_metrics.page_setup_time,
                "navigation": self.performance_metrics.navigation_time
            }
        ))
        
    async def test_stealth_effectiveness(self):
        """Test stealth measures effectiveness"""
        self.log_test_start("Stealth Effectiveness")
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        passed = True
        stealth_results = {}
        
        try:
            # Import stealth engine
            from src.stealth.stealth_engine import StealthMasterEngine
            stealth_engine = StealthMasterEngine()
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Apply stealth
                await stealth_engine.apply_stealth(page, context)
                
                # Test stealth effectiveness
                await page.goto('https://bot.sannysoft.com', wait_until='networkidle')
                
                # Check various indicators
                checks = {
                    'webdriver': await page.evaluate('() => navigator.webdriver'),
                    'chrome': await page.evaluate('() => !!window.chrome'),
                    'permissions': await page.evaluate('() => navigator.permissions !== undefined'),
                    'plugins_length': await page.evaluate('() => navigator.plugins.length'),
                    'languages': await page.evaluate('() => navigator.languages.length > 0'),
                }
                
                for check, result in checks.items():
                    if check == 'webdriver' and result is None:
                        self.log_success(f"{check}: Hidden (undefined)")
                        stealth_results[check] = True
                    elif check == 'chrome' and result:
                        self.log_success(f"{check}: Present")
                        stealth_results[check] = True
                    elif check == 'plugins_length' and result > 0:
                        self.log_success(f"{check}: {result} plugins")
                        stealth_results[check] = True
                    elif check == 'languages' and result:
                        self.log_success(f"{check}: Configured")
                        stealth_results[check] = True
                    else:
                        self.log_warning(f"{check}: {result}")
                        stealth_results[check] = False
                
                await browser.close()
                
        except Exception as e:
            passed = False
            self.log_error(f"Stealth test failed: {e}")
            traceback.print_exc()
        
        duration = time.time() - start_time
        memory_delta = self.process.memory_info().rss / 1024 / 1024 - memory_start
        
        self.results.append(TestResult(
            test_name="Stealth Effectiveness",
            category="security",
            passed=passed and all(stealth_results.values()),
            duration=duration,
            memory_delta=memory_delta,
            metrics=stealth_results
        ))
        
    async def test_concurrent_performance(self):
        """Test concurrent browser operations"""
        self.log_test_start("Concurrent Performance")
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        concurrent_counts = [1, 3, 5]
        results = {}
        
        async def launch_and_navigate(index: int):
            """Launch browser and navigate"""
            start = time.time()
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto('https://httpbin.org/delay/1')
                await browser.close()
            return time.time() - start
        
        for count in concurrent_counts:
            self.log_info(f"Testing {count} concurrent browsers...")
            tasks = [launch_and_navigate(i) for i in range(count)]
            concurrent_start = time.time()
            durations = await asyncio.gather(*tasks)
            total_duration = time.time() - concurrent_start
            
            avg_duration = sum(durations) / len(durations)
            results[f"{count}_browsers"] = {
                "total_time": total_duration,
                "avg_time": avg_duration,
                "efficiency": avg_duration / total_duration
            }
            
            self.log_success(f"{count} browsers: {total_duration:.2f}s total, {avg_duration:.2f}s average")
        
        duration = time.time() - start_time
        memory_delta = self.process.memory_info().rss / 1024 / 1024 - memory_start
        
        self.results.append(TestResult(
            test_name="Concurrent Performance",
            category="performance",
            passed=True,
            duration=duration,
            memory_delta=memory_delta,
            metrics=results
        ))
        
    async def test_memory_leaks(self):
        """Test for memory leaks"""
        self.log_test_start("Memory Leak Detection")
        start_time = time.time()
        memory_readings = []
        
        # Perform repeated operations
        iterations = 5
        for i in range(iterations):
            memory_before = self.process.memory_info().rss / 1024 / 1024
            
            # Launch and close browser
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto('https://httpbin.org/html')
                await browser.close()
            
            # Force garbage collection
            import gc
            gc.collect()
            await asyncio.sleep(1)
            
            memory_after = self.process.memory_info().rss / 1024 / 1024
            memory_delta = memory_after - memory_before
            memory_readings.append(memory_delta)
            
            self.log_info(f"Iteration {i+1}: Memory delta = {memory_delta:.2f} MB")
        
        # Analyze trend
        avg_delta = sum(memory_readings) / len(memory_readings)
        max_delta = max(memory_readings)
        
        leak_detected = avg_delta > 5.0  # 5MB average increase suggests leak
        
        if leak_detected:
            self.log_warning(f"Potential memory leak detected: {avg_delta:.2f} MB average increase")
        else:
            self.log_success(f"No significant memory leak: {avg_delta:.2f} MB average delta")
        
        duration = time.time() - start_time
        
        self.results.append(TestResult(
            test_name="Memory Leak Detection",
            category="stability",
            passed=not leak_detected,
            duration=duration,
            memory_delta=avg_delta,
            metrics={
                "iterations": iterations,
                "avg_delta": avg_delta,
                "max_delta": max_delta,
                "readings": memory_readings
            }
        ))
        
    async def test_error_recovery(self):
        """Test error handling and recovery"""
        self.log_test_start("Error Recovery")
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        recovery_results = {}
        
        # Test 1: Invalid URL recovery
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    await page.goto('https://invalid-domain-that-does-not-exist.com', timeout=5000)
                except Exception:
                    recovery_results['invalid_url'] = True
                    self.log_success("Recovered from invalid URL")
                
                # Test navigation after error
                response = await page.goto('https://httpbin.org/status/200')
                if response.ok:
                    recovery_results['post_error_navigation'] = True
                    self.log_success("Navigation works after error")
                
                await browser.close()
                
        except Exception as e:
            self.log_error(f"Recovery test failed: {e}")
        
        # Test 2: Timeout recovery
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    await page.goto('https://httpbin.org/delay/10', timeout=2000)
                except Exception:
                    recovery_results['timeout'] = True
                    self.log_success("Recovered from timeout")
                
                await browser.close()
                
        except Exception as e:
            self.log_error(f"Timeout recovery failed: {e}")
        
        duration = time.time() - start_time
        memory_delta = self.process.memory_info().rss / 1024 / 1024 - memory_start
        
        self.results.append(TestResult(
            test_name="Error Recovery",
            category="stability",
            passed=len(recovery_results) >= 2,
            duration=duration,
            memory_delta=memory_delta,
            metrics=recovery_results
        ))
        
    async def test_platform_access(self):
        """Test access to ticketing platforms"""
        self.log_test_start("Platform Access")
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024
        
        platforms = {
            "Fansale": "https://www.fansale.it",
            "Ticketmaster": "https://www.ticketmaster.it",
            "Vivaticket": "https://www.vivaticket.com"
        }
        
        access_results = {}
        
        try:
            from src.stealth.stealth_engine import StealthMasterEngine
            stealth_engine = StealthMasterEngine()
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                for platform, url in platforms.items():
                    self.log_info(f"Testing {platform}...")
                    
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    # Apply stealth
                    await stealth_engine.apply_stealth(page, context)
                    
                    try:
                        response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        
                        # Check for blocks
                        content = await page.content()
                        blocked = any(indicator in content.lower() for indicator in [
                            'blocked', 'captcha', 'unusual activity', 'access denied'
                        ])
                        
                        if response and response.ok and not blocked:
                            access_results[platform] = "accessible"
                            self.log_success(f"{platform}: Accessible")
                        else:
                            access_results[platform] = "blocked"
                            self.log_warning(f"{platform}: May be blocked")
                            
                    except Exception as e:
                        access_results[platform] = f"error: {str(e)[:50]}"
                        self.log_error(f"{platform}: {str(e)[:50]}")
                    
                    await context.close()
                
                await browser.close()
                
        except Exception as e:
            self.log_error(f"Platform access test failed: {e}")
        
        duration = time.time() - start_time
        memory_delta = self.process.memory_info().rss / 1024 / 1024 - memory_start
        
        accessible_count = sum(1 for v in access_results.values() if v == "accessible")
        
        self.results.append(TestResult(
            test_name="Platform Access",
            category="functionality",
            passed=accessible_count >= 2,  # At least 2 platforms accessible
            duration=duration,
            memory_delta=memory_delta,
            metrics=access_results
        ))
        
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log_test_start("TEST REPORT")
        
        # Calculate summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        total_duration = sum(r.duration for r in self.results)
        total_memory = sum(r.memory_delta for r in self.results)
        
        # Group by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Print summary
        logger.info(f"\n{Fore.CYAN}{'='*60}")
        logger.info(f"{Fore.CYAN}SUMMARY")
        logger.info(f"{Fore.CYAN}{'='*60}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {Fore.GREEN}{passed_tests}{Style.RESET_ALL}")
        logger.info(f"Failed: {Fore.RED}{total_tests - passed_tests}{Style.RESET_ALL}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info(f"Total Memory Delta: {total_memory:.2f} MB")
        
        # Category breakdown
        logger.info(f"\n{Fore.CYAN}CATEGORY BREAKDOWN")
        for category, results in categories.items():
            passed = sum(1 for r in results if r.passed)
            logger.info(f"\n{category.upper()}: {passed}/{len(results)} passed")
            for result in results:
                status = f"{Fore.GREEN}✅ PASS" if result.passed else f"{Fore.RED}❌ FAIL"
                logger.info(f"  {result.test_name}: {status}{Style.RESET_ALL} ({result.duration:.2f}s)")
                if result.error:
                    logger.info(f"    Error: {result.error}")
        
        # Performance metrics
        logger.info(f"\n{Fore.CYAN}PERFORMANCE METRICS")
        logger.info(f"Browser Launch: {self.performance_metrics.browser_launch_time:.2f}s")
        logger.info(f"Context Creation: {self.performance_metrics.context_creation_time:.2f}s")
        logger.info(f"Page Setup: {self.performance_metrics.page_setup_time:.2f}s")
        logger.info(f"Navigation: {self.performance_metrics.navigation_time:.2f}s")
        
        # Issues found
        logger.info(f"\n{Fore.CYAN}ISSUES IDENTIFIED")
        issues = []
        
        # Check for performance issues
        if self.performance_metrics.browser_launch_time > 2.0:
            issues.append("⚠️  Slow browser launch time (>2s)")
        
        # Check for memory issues
        memory_leak_test = next((r for r in self.results if r.test_name == "Memory Leak Detection"), None)
        if memory_leak_test and not memory_leak_test.passed:
            issues.append("⚠️  Potential memory leak detected")
        
        # Check for platform access issues
        platform_test = next((r for r in self.results if r.test_name == "Platform Access"), None)
        if platform_test and platform_test.metrics:
            for platform, status in platform_test.metrics.items():
                if status != "accessible":
                    issues.append(f"⚠️  {platform} access issues: {status}")
        
        if issues:
            for issue in issues:
                logger.warning(issue)
        else:
            logger.info(f"{Fore.GREEN}No critical issues found!")
        
        # Save detailed report
        report_path = Path("test_results_detailed.json")
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "duration": total_duration,
                "memory_delta": total_memory
            },
            "performance_metrics": asdict(self.performance_metrics),
            "results": [asdict(r) for r in self.results],
            "issues": issues
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n{Fore.GREEN}Detailed report saved to: {report_path}")


async def main():
    """Run comprehensive test suite"""
    suite = ComprehensiveTestSuite()
    try:
        await suite.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n👋 Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test suite error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())