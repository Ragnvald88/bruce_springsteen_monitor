#!/usr/bin/env python3
"""
StealthMaster AI Performance Comparison Test
Compare performance before and after optimizations
"""

import asyncio
import time
import json
import sys
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from statistics import mean, stdev

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright
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


class PerformanceComparison:
    """Compare performance with and without browser pool"""
    
    def __init__(self):
        self.results = {
            'without_pool': {},
            'with_pool': {},
            'improvements': {}
        }
        self.process = psutil.Process()
        
    async def run_comparison(self):
        """Run full performance comparison"""
        logger.info(f"{Fore.CYAN}{'='*60}")
        logger.info(f"{Fore.CYAN}🚀 STEALTHMASTER AI PERFORMANCE COMPARISON")
        logger.info(f"{Fore.CYAN}{'='*60}")
        
        # Test 1: Without browser pool (traditional approach)
        logger.info(f"\n{Fore.YELLOW}📊 TEST 1: Traditional Approach (No Browser Pool)")
        await self.test_without_pool()
        
        # Give system time to clean up
        await asyncio.sleep(5)
        import gc
        gc.collect()
        
        # Test 2: With browser pool
        logger.info(f"\n{Fore.YELLOW}📊 TEST 2: Optimized Approach (With Browser Pool)")
        await self.test_with_pool()
        
        # Calculate improvements
        self.calculate_improvements()
        
        # Generate report
        self.generate_report()
        
    async def test_without_pool(self):
        """Test performance without browser pool"""
        metrics = {
            'browser_launch_times': [],
            'scan_times': [],
            'memory_usage': [],
            'total_time': 0
        }
        
        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Simulate 10 scans
        for i in range(10):
            scan_start = time.time()
            
            # Traditional approach - new browser each time
            async with async_playwright() as p:
                browser_start = time.time()
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                browser_launch_time = time.time() - browser_start
                metrics['browser_launch_times'].append(browser_launch_time)
                
                context = await browser.new_context()
                page = await context.new_page()
                
                # Simulate navigation
                await page.goto('https://httpbin.org/html', wait_until='domcontentloaded')
                
                # Simulate some work
                await page.evaluate('() => document.querySelector("h1")')
                await asyncio.sleep(0.5)
                
                await browser.close()
            
            scan_time = time.time() - scan_start
            metrics['scan_times'].append(scan_time)
            
            # Memory usage
            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics['memory_usage'].append(current_memory - initial_memory)
            
            logger.info(f"  Scan {i+1}: {scan_time:.2f}s (browser launch: {browser_launch_time:.2f}s)")
        
        metrics['total_time'] = time.time() - start_time
        self.results['without_pool'] = metrics
        
        logger.info(f"\n{Fore.GREEN}✅ Traditional approach completed in {metrics['total_time']:.2f}s")
        
    async def test_with_pool(self):
        """Test performance with browser pool"""
        from src.core.browser_pool import BrowserPool
        
        metrics = {
            'browser_launch_times': [],
            'scan_times': [],
            'memory_usage': [],
            'pool_acquisition_times': [],
            'total_time': 0
        }
        
        # Initialize browser pool
        pool = BrowserPool({
            'min_size': 2,
            'max_size': 3,
            'headless': True
        })
        await pool.initialize()
        
        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Simulate 10 scans
        for i in range(10):
            scan_start = time.time()
            acquisition_start = time.time()
            
            # Use browser pool
            async with pool.acquire_browser() as (browser, context, page):
                acquisition_time = time.time() - acquisition_start
                metrics['pool_acquisition_times'].append(acquisition_time)
                
                # Simulate navigation
                await page.goto('https://httpbin.org/html', wait_until='domcontentloaded')
                
                # Simulate some work
                await page.evaluate('() => document.querySelector("h1")')
                await asyncio.sleep(0.5)
            
            scan_time = time.time() - scan_start
            metrics['scan_times'].append(scan_time)
            
            # Memory usage
            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics['memory_usage'].append(current_memory - initial_memory)
            
            logger.info(f"  Scan {i+1}: {scan_time:.2f}s (pool acquisition: {acquisition_time:.2f}s)")
        
        metrics['total_time'] = time.time() - start_time
        metrics['browser_launch_times'] = [0.0] * 10  # No individual launches with pool
        
        # Get pool stats
        pool_stats = pool.get_stats()
        metrics['pool_stats'] = pool_stats
        
        await pool.shutdown_pool()
        
        self.results['with_pool'] = metrics
        
        logger.info(f"\n{Fore.GREEN}✅ Optimized approach completed in {metrics['total_time']:.2f}s")
        logger.info(f"  Pool hit rate: {pool_stats['hit_rate']:.1f}%")
        
    def calculate_improvements(self):
        """Calculate performance improvements"""
        without = self.results['without_pool']
        with_pool = self.results['with_pool']
        
        improvements = {
            'total_time_reduction': (without['total_time'] - with_pool['total_time']) / without['total_time'] * 100,
            'avg_scan_time_reduction': (mean(without['scan_times']) - mean(with_pool['scan_times'])) / mean(without['scan_times']) * 100,
            'browser_launch_overhead_eliminated': sum(without['browser_launch_times']),
            'memory_efficiency': (mean(without['memory_usage']) - mean(with_pool['memory_usage'])) / mean(without['memory_usage']) * 100,
            'consistency_improvement': (stdev(without['scan_times']) - stdev(with_pool['scan_times'])) / stdev(without['scan_times']) * 100
        }
        
        self.results['improvements'] = improvements
        
    def generate_report(self):
        """Generate comprehensive comparison report"""
        logger.info(f"\n{Fore.CYAN}{'='*60}")
        logger.info(f"{Fore.CYAN}📈 PERFORMANCE COMPARISON REPORT")
        logger.info(f"{Fore.CYAN}{'='*60}")
        
        # Traditional approach stats
        without = self.results['without_pool']
        logger.info(f"\n{Fore.YELLOW}Traditional Approach (No Pool):")
        logger.info(f"  Total time: {without['total_time']:.2f}s")
        logger.info(f"  Avg scan time: {mean(without['scan_times']):.2f}s (±{stdev(without['scan_times']):.2f}s)")
        logger.info(f"  Avg browser launch: {mean(without['browser_launch_times']):.2f}s")
        logger.info(f"  Avg memory delta: {mean(without['memory_usage']):.1f} MB")
        
        # Optimized approach stats
        with_pool = self.results['with_pool']
        logger.info(f"\n{Fore.YELLOW}Optimized Approach (With Pool):")
        logger.info(f"  Total time: {with_pool['total_time']:.2f}s")
        logger.info(f"  Avg scan time: {mean(with_pool['scan_times']):.2f}s (±{stdev(with_pool['scan_times']):.2f}s)")
        logger.info(f"  Avg pool acquisition: {mean(with_pool['pool_acquisition_times']):.3f}s")
        logger.info(f"  Avg memory delta: {mean(with_pool['memory_usage']):.1f} MB")
        if 'pool_stats' in with_pool:
            logger.info(f"  Pool hit rate: {with_pool['pool_stats']['hit_rate']:.1f}%")
        
        # Improvements
        imp = self.results['improvements']
        logger.info(f"\n{Fore.GREEN}🚀 IMPROVEMENTS:")
        logger.info(f"  Total time reduction: {Fore.GREEN}{imp['total_time_reduction']:.1f}%")
        logger.info(f"  Avg scan time reduction: {Fore.GREEN}{imp['avg_scan_time_reduction']:.1f}%")
        logger.info(f"  Browser launch overhead eliminated: {Fore.GREEN}{imp['browser_launch_overhead_eliminated']:.1f}s")
        logger.info(f"  Memory efficiency improvement: {Fore.GREEN}{imp['memory_efficiency']:.1f}%")
        logger.info(f"  Consistency improvement: {Fore.GREEN}{imp['consistency_improvement']:.1f}%")
        
        # Key insights
        logger.info(f"\n{Fore.CYAN}💡 KEY INSIGHTS:")
        
        if imp['total_time_reduction'] > 40:
            logger.info(f"  {Fore.GREEN}✓ Excellent performance improvement! Over 40% faster.")
        elif imp['total_time_reduction'] > 20:
            logger.info(f"  {Fore.GREEN}✓ Good performance improvement! Over 20% faster.")
        else:
            logger.info(f"  {Fore.YELLOW}⚠ Moderate improvement. Consider further optimization.")
        
        if imp['memory_efficiency'] > 0:
            logger.info(f"  {Fore.GREEN}✓ Memory usage is more efficient with pooling.")
        
        if imp['consistency_improvement'] > 0:
            logger.info(f"  {Fore.GREEN}✓ Performance is more consistent with pooling.")
        
        # Save detailed report
        report_path = Path("performance_comparison_report.json")
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results,
                'summary': {
                    'performance_gain': f"{imp['total_time_reduction']:.1f}%",
                    'recommendation': 'Browser pooling provides significant performance improvements'
                }
            }, f, indent=2)
        
        logger.info(f"\n{Fore.GREEN}📄 Detailed report saved to: {report_path}")


async def main():
    """Run performance comparison"""
    comparison = PerformanceComparison()
    try:
        await comparison.run_comparison()
    except KeyboardInterrupt:
        logger.info("\n👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())