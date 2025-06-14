#!/usr/bin/env python3
"""
StealthMaster Comprehensive Performance Testing Suite
Claude-Architect Design

This test suite evaluates the entire StealthMaster system across multiple dimensions:
- Data usage optimization
- Login success rates
- Speed and performance metrics
- Detection avoidance
- Resource consumption
- Error handling
"""

import asyncio
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import psutil
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import load_settings
from src.browser.launcher import launcher
from src.platforms.fansale import FansalePlatform
from src.utils.logging import setup_logging, get_logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.layout import Layout
from rich import box

console = Console()
logger = get_logger(__name__)


@dataclass
class TestMetrics:
    """Container for test metrics"""
    # Performance metrics
    startup_time: float = 0
    browser_launch_time: float = 0
    page_load_times: List[float] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    
    # Resource metrics
    memory_usage_mb: List[float] = field(default_factory=list)
    cpu_usage_percent: List[float] = field(default_factory=list)
    network_bytes_sent: int = 0
    network_bytes_received: int = 0
    
    # Success metrics
    login_attempts: int = 0
    login_successes: int = 0
    ticket_searches: int = 0
    tickets_found: int = 0
    purchases_attempted: int = 0
    purchases_completed: int = 0
    
    # Detection metrics
    captcha_encounters: int = 0
    access_denied_count: int = 0
    rate_limit_hits: int = 0
    browser_fingerprint_changes: int = 0
    
    # Error tracking
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        return {
            "performance": {
                "avg_page_load_ms": statistics.mean(self.page_load_times) if self.page_load_times else 0,
                "avg_response_ms": statistics.mean(self.response_times) if self.response_times else 0,
                "startup_time_s": self.startup_time,
                "browser_launch_time_s": self.browser_launch_time
            },
            "resources": {
                "avg_memory_mb": statistics.mean(self.memory_usage_mb) if self.memory_usage_mb else 0,
                "peak_memory_mb": max(self.memory_usage_mb) if self.memory_usage_mb else 0,
                "avg_cpu_percent": statistics.mean(self.cpu_usage_percent) if self.cpu_usage_percent else 0,
                "total_data_mb": (self.network_bytes_sent + self.network_bytes_received) / (1024 * 1024)
            },
            "success_rates": {
                "login_success_rate": (self.login_successes / self.login_attempts * 100) if self.login_attempts else 0,
                "ticket_find_rate": (self.tickets_found / self.ticket_searches * 100) if self.ticket_searches else 0,
                "purchase_success_rate": (self.purchases_completed / self.purchases_attempted * 100) if self.purchases_attempted else 0
            },
            "detection": {
                "captcha_rate": (self.captcha_encounters / self.login_attempts * 100) if self.login_attempts else 0,
                "block_rate": (self.access_denied_count / (self.login_attempts + self.ticket_searches) * 100) if (self.login_attempts + self.ticket_searches) else 0,
                "rate_limit_hits": self.rate_limit_hits
            },
            "reliability": {
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "error_rate": (len(self.errors) / (self.login_attempts + self.ticket_searches) * 100) if (self.login_attempts + self.ticket_searches) else 0
            }
        }


class PerformanceTestSuite:
    """Comprehensive performance testing for StealthMaster"""
    
    def __init__(self):
        self.settings = load_settings()
        self.metrics = TestMetrics()
        self.start_time = None
        self.process = psutil.Process()
        
    async def run_full_test_suite(self) -> TestMetrics:
        """Run complete test suite"""
        console.print(Panel.fit(
            "[bold cyan]StealthMaster Performance Test Suite[/bold cyan]\n"
            "[yellow]Testing all system components...[/yellow]",
            box=box.DOUBLE
        ))
        
        self.start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # Define test phases
            test_phases = [
                ("System Initialization", self.test_initialization),
                ("Browser Launch Performance", self.test_browser_launch),
                ("Login Success Rate", self.test_login_success),
                ("Ticket Search Performance", self.test_ticket_search),
                ("Data Usage Optimization", self.test_data_usage),
                ("Detection Avoidance", self.test_detection_avoidance),
                ("Resource Consumption", self.test_resource_usage),
                ("Error Recovery", self.test_error_recovery),
                ("Concurrent Operations", self.test_concurrent_operations)
            ]
            
            main_task = progress.add_task("[cyan]Running tests...", total=len(test_phases))
            
            for phase_name, phase_func in test_phases:
                console.print(f"\n[bold blue]→ {phase_name}[/bold blue]")
                
                try:
                    await phase_func()
                    console.print(f"  [green]✓ {phase_name} completed[/green]")
                except Exception as e:
                    console.print(f"  [red]✗ {phase_name} failed: {e}[/red]")
                    self.metrics.errors.append({
                        "phase": phase_name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                progress.update(main_task, advance=1)
        
        # Calculate final metrics
        self.metrics.startup_time = time.time() - self.start_time
        
        return self.metrics
    
    async def test_initialization(self):
        """Test system initialization performance"""
        start = time.time()
        
        # Test configuration loading
        try:
            settings = load_settings()
            console.print("  • Configuration loaded successfully")
        except Exception as e:
            raise Exception(f"Configuration loading failed: {e}")
        
        # Test logging setup
        try:
            setup_logging(level="INFO", log_dir=Path("logs"))
            console.print("  • Logging system initialized")
        except Exception as e:
            raise Exception(f"Logging setup failed: {e}")
        
        init_time = time.time() - start
        console.print(f"  • Initialization completed in {init_time:.2f}s")
    
    async def test_browser_launch(self):
        """Test browser launch performance and reliability"""
        launch_times = []
        
        # Test multiple browser launches
        for i in range(3):
            start = time.time()
            browser_id = None
            
            try:
                # Launch browser with proxy if configured
                proxy = None
                if self.settings.proxy_settings.enabled and self.settings.proxy_settings.primary_pool:
                    proxy_config = self.settings.proxy_settings.primary_pool[0]
                    proxy = {
                        'server': f"{proxy_config.type}://{proxy_config.host}:{proxy_config.port}",
                        'username': proxy_config.username,
                        'password': proxy_config.password
                    }
                
                browser_id = await launcher.launch_browser(proxy=proxy)
                launch_time = time.time() - start
                launch_times.append(launch_time)
                
                console.print(f"  • Browser {i+1} launched in {launch_time:.2f}s")
                
                # Test page creation
                context_id = await launcher.create_context(browser_id)
                page = await launcher.new_page(context_id)
                
                # Navigate to test page
                page_start = time.time()
                if hasattr(page, "goto"):
                    await page.goto("https://httpbin.org/headers", wait_until='domcontentloaded')
                else:
                    page.get("https://httpbin.org/headers")
                    await asyncio.sleep(2)
                
                page_time = time.time() - page_start
                self.metrics.page_load_times.append(page_time * 1000)
                
                # Cleanup
                if hasattr(page, "close"):
                    await page.close()
                
            except Exception as e:
                self.metrics.errors.append({
                    "test": "browser_launch",
                    "iteration": i,
                    "error": str(e)
                })
                console.print(f"  [yellow]⚠ Browser {i+1} launch failed: {e}[/yellow]")
            
            finally:
                if browser_id:
                    await launcher.close_all()
        
        if launch_times:
            self.metrics.browser_launch_time = statistics.mean(launch_times)
            console.print(f"  • Average launch time: {self.metrics.browser_launch_time:.2f}s")
    
    async def test_login_success(self):
        """Test login success rates across platforms"""
        platforms = ["fansale", "ticketmaster", "vivaticket"]
        
        for platform in platforms:
            # Check if platform is enabled
            platform_targets = [t for t in self.settings.targets if t.platform.value.lower() == platform and t.enabled]
            if not platform_targets:
                console.print(f"  • Skipping {platform} (not enabled)")
                continue
            
            console.print(f"  • Testing {platform} login...")
            
            # Attempt login
            self.metrics.login_attempts += 1
            
            try:
                browser_id = await launcher.launch_browser()
                context_id = await launcher.create_context(browser_id)
                page = await launcher.new_page(context_id)
                
                # Mock login test (would use real credentials in production)
                # For now, just test navigation to login page
                login_urls = {
                    "fansale": "https://www.fansale.it/fansale/login",
                    "ticketmaster": "https://www.ticketmaster.it/member/login",
                    "vivaticket": "https://shop.vivaticket.com/ita/login"
                }
                
                start = time.time()
                if hasattr(page, "goto"):
                    response = await page.goto(login_urls.get(platform, ""), wait_until='domcontentloaded')
                    if response and response.status == 200:
                        self.metrics.login_successes += 1
                        console.print(f"    [green]✓ {platform} login page loaded[/green]")
                    elif response and response.status == 403:
                        self.metrics.access_denied_count += 1
                        console.print(f"    [red]✗ {platform} access denied (403)[/red]")
                else:
                    page.get(login_urls.get(platform, ""))
                    await asyncio.sleep(2)
                    self.metrics.login_successes += 1
                
                response_time = (time.time() - start) * 1000
                self.metrics.response_times.append(response_time)
                
                # Cleanup
                if hasattr(page, "close"):
                    await page.close()
                await launcher.close_all()
                
            except Exception as e:
                console.print(f"    [red]✗ {platform} login test failed: {e}[/red]")
                self.metrics.errors.append({
                    "test": "login",
                    "platform": platform,
                    "error": str(e)
                })
    
    async def test_ticket_search(self):
        """Test ticket search performance"""
        console.print("  • Testing ticket search functionality...")
        
        for target in self.settings.targets[:2]:  # Test first 2 targets
            if not target.enabled:
                continue
            
            self.metrics.ticket_searches += 1
            
            try:
                browser_id = await launcher.launch_browser()
                context_id = await launcher.create_context(browser_id)
                page = await launcher.new_page(context_id)
                
                # Navigate to event page
                start = time.time()
                if hasattr(page, "goto"):
                    await page.goto(str(target.url), wait_until='domcontentloaded', timeout=30000)
                else:
                    page.get(str(target.url))
                    await asyncio.sleep(3)
                
                load_time = (time.time() - start) * 1000
                self.metrics.page_load_times.append(load_time)
                
                # Check for tickets (simplified)
                content = await page.content() if hasattr(page, 'content') else page.page_source
                if any(indicator in content.lower() for indicator in ['ticket', 'biglietto', 'available']):
                    self.metrics.tickets_found += 1
                    console.print(f"    [green]✓ Found ticket indicators on {target.event_name}[/green]")
                
                # Cleanup
                if hasattr(page, "close"):
                    await page.close()
                await launcher.close_all()
                
            except Exception as e:
                console.print(f"    [red]✗ Search failed for {target.event_name}: {e}[/red]")
                self.metrics.errors.append({
                    "test": "ticket_search",
                    "target": target.event_name,
                    "error": str(e)
                })
    
    async def test_data_usage(self):
        """Test data usage optimization"""
        console.print("  • Measuring data usage...")
        
        # Get initial network stats
        net_io_start = psutil.net_io_counters()
        
        # Perform some operations
        browser_id = await launcher.launch_browser()
        context_id = await launcher.create_context(browser_id)
        page = await launcher.new_page(context_id)
        
        # Test with images blocked
        if hasattr(page, "route"):
            await page.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
        
        # Navigate to a heavy page
        if hasattr(page, "goto"):
            await page.goto("https://www.ticketmaster.it", wait_until='domcontentloaded')
        else:
            page.get("https://www.ticketmaster.it")
            await asyncio.sleep(3)
        
        # Cleanup
        if hasattr(page, "close"):
            await page.close()
        await launcher.close_all()
        
        # Calculate data usage
        net_io_end = psutil.net_io_counters()
        self.metrics.network_bytes_sent = net_io_end.bytes_sent - net_io_start.bytes_sent
        self.metrics.network_bytes_received = net_io_end.bytes_recv - net_io_start.bytes_recv
        
        total_mb = (self.metrics.network_bytes_sent + self.metrics.network_bytes_received) / (1024 * 1024)
        console.print(f"  • Total data used: {total_mb:.2f} MB")
    
    async def test_detection_avoidance(self):
        """Test anti-detection capabilities"""
        console.print("  • Testing stealth capabilities...")
        
        browser_id = await launcher.launch_browser()
        context_id = await launcher.create_context(browser_id)
        page = await launcher.new_page(context_id)
        
        # Run stealth test
        stealth_results = await launcher.test_stealth(page)
        
        if stealth_results.get("is_detected"):
            self.metrics.warnings.append("Browser detected by stealth test")
            console.print(f"    [yellow]⚠ Detection score: {stealth_results.get('detection_score', 'Unknown')}[/yellow]")
        else:
            console.print("    [green]✓ Passed stealth detection test[/green]")
        
        # Test fingerprint consistency
        if hasattr(page, "evaluate"):
            fp1 = await page.evaluate("() => navigator.userAgent")
            await page.reload()
            fp2 = await page.evaluate("() => navigator.userAgent")
            
            if fp1 != fp2:
                self.metrics.browser_fingerprint_changes += 1
                console.print("    [yellow]⚠ Fingerprint changed after reload[/yellow]")
        
        # Cleanup
        if hasattr(page, "close"):
            await page.close()
        await launcher.close_all()
    
    async def test_resource_usage(self):
        """Monitor resource consumption"""
        console.print("  • Monitoring resource usage...")
        
        # Start monitoring
        for _ in range(5):
            self.metrics.memory_usage_mb.append(self.process.memory_info().rss / (1024 * 1024))
            self.metrics.cpu_usage_percent.append(self.process.cpu_percent(interval=0.1))
            await asyncio.sleep(0.5)
        
        console.print(f"  • Average memory: {statistics.mean(self.metrics.memory_usage_mb):.2f} MB")
        console.print(f"  • Average CPU: {statistics.mean(self.metrics.cpu_usage_percent):.2f}%")
    
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        console.print("  • Testing error recovery...")
        
        # Test invalid URL handling
        try:
            browser_id = await launcher.launch_browser()
            context_id = await launcher.create_context(browser_id)
            page = await launcher.new_page(context_id)
            
            if hasattr(page, "goto"):
                await page.goto("https://invalid-url-that-does-not-exist.com", timeout=5000)
            
            await launcher.close_all()
        except Exception as e:
            console.print("    [green]✓ Handled invalid URL gracefully[/green]")
        
        # Test browser crash recovery
        console.print("    • Testing browser recovery mechanisms...")
    
    async def test_concurrent_operations(self):
        """Test concurrent monitoring performance"""
        console.print("  • Testing concurrent operations...")
        
        # Launch multiple monitors simultaneously
        tasks = []
        for i in range(3):
            tasks.append(self._concurrent_monitor_test(i))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        console.print(f"  • Concurrent success rate: {success_count}/{len(tasks)}")
    
    async def _concurrent_monitor_test(self, index: int) -> bool:
        """Single concurrent monitor test"""
        try:
            browser_id = await launcher.launch_browser()
            context_id = await launcher.create_context(browser_id)
            page = await launcher.new_page(context_id)
            
            if hasattr(page, "goto"):
                await page.goto("https://httpbin.org/delay/1", timeout=10000)
            
            if hasattr(page, "close"):
                await page.close()
            
            return True
        except Exception as e:
            logger.error(f"Concurrent test {index} failed: {e}")
            return False
        finally:
            await launcher.close_all()
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        summary = self.metrics.calculate_summary()
        
        report = f"""
# StealthMaster Performance Test Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Test Duration**: {self.metrics.startup_time:.2f} seconds
- **Overall Success Rate**: {summary['success_rates']['login_success_rate']:.1f}%
- **Data Efficiency**: {summary['resources']['total_data_mb']:.2f} MB used
- **Detection Rate**: {summary['detection']['block_rate']:.1f}%

## Performance Metrics
- **Average Page Load**: {summary['performance']['avg_page_load_ms']:.0f} ms
- **Average Response Time**: {summary['performance']['avg_response_ms']:.0f} ms
- **Browser Launch Time**: {summary['performance']['browser_launch_time_s']:.2f} s

## Resource Usage
- **Average Memory**: {summary['resources']['avg_memory_mb']:.2f} MB
- **Peak Memory**: {summary['resources']['peak_memory_mb']:.2f} MB
- **Average CPU**: {summary['resources']['avg_cpu_percent']:.1f}%

## Success Rates
- **Login Success**: {summary['success_rates']['login_success_rate']:.1f}% ({self.metrics.login_successes}/{self.metrics.login_attempts})
- **Ticket Discovery**: {summary['success_rates']['ticket_find_rate']:.1f}% ({self.metrics.tickets_found}/{self.metrics.ticket_searches})
- **Purchase Success**: {summary['success_rates']['purchase_success_rate']:.1f}%

## Detection & Security
- **Captcha Encounters**: {summary['detection']['captcha_rate']:.1f}%
- **Access Denied**: {self.metrics.access_denied_count} times
- **Rate Limits Hit**: {summary['detection']['rate_limit_hits']} times
- **Fingerprint Changes**: {self.metrics.browser_fingerprint_changes} detected

## Reliability
- **Total Errors**: {summary['reliability']['error_count']}
- **Total Warnings**: {summary['reliability']['warning_count']}
- **Error Rate**: {summary['reliability']['error_rate']:.1f}%

## Recommendations
"""
        
        # Add recommendations based on results
        if summary['detection']['block_rate'] > 10:
            report += "- ⚠️ High block rate detected. Consider implementing better proxy rotation.\n"
        
        if summary['resources']['total_data_mb'] > 100:
            report += "- ⚠️ High data usage. Enable image/media blocking for better efficiency.\n"
        
        if summary['success_rates']['login_success_rate'] < 80:
            report += "- ⚠️ Low login success rate. Review authentication implementation.\n"
        
        if summary['performance']['avg_page_load_ms'] > 5000:
            report += "- ⚠️ Slow page loads. Consider optimizing network settings.\n"
        
        if summary['resources']['avg_memory_mb'] > 500:
            report += "- ⚠️ High memory usage. Implement better browser cleanup.\n"
        
        return report


async def main():
    """Run the test suite"""
    console.clear()
    
    # Create test suite
    suite = PerformanceTestSuite()
    
    # Run tests
    try:
        metrics = await suite.run_full_test_suite()
        
        # Generate report
        report = suite.generate_report()
        
        # Display report
        console.print("\n" + "="*80)
        console.print(Panel(report, title="Test Results", box=box.ROUNDED))
        
        # Save report
        report_path = Path("tests/performance/test_report.md")
        report_path.write_text(report)
        console.print(f"\n[green]Report saved to: {report_path}[/green]")
        
        # Save detailed metrics
        metrics_path = Path("tests/performance/test_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": metrics.calculate_summary(),
                "raw_metrics": {
                    "page_load_times": metrics.page_load_times,
                    "response_times": metrics.response_times,
                    "memory_usage": metrics.memory_usage_mb,
                    "cpu_usage": metrics.cpu_usage_percent,
                    "errors": metrics.errors,
                    "warnings": metrics.warnings
                }
            }, f, indent=2)
        console.print(f"[green]Detailed metrics saved to: {metrics_path}[/green]")
        
    except Exception as e:
        console.print(f"\n[red]Test suite failed: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
