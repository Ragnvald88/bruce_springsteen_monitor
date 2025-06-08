#!/usr/bin/env python3
"""
Realistic Performance Test for StealthMaster AI
Test with actual ticketing platform scenarios
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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


class RealisticPerformanceTest:
    """Test performance with realistic ticketing scenarios"""
    
    def __init__(self):
        self.test_urls = [
            "https://www.fansale.it",
            "https://www.ticketmaster.it",
            "https://www.vivaticket.com",
            "https://httpbin.org/delay/2",  # Simulate slow page
            "https://httpbin.org/html",
        ]
        
    async def run_test(self):
        """Run realistic performance test"""
        logger.info(f"{Fore.CYAN}{'='*60}")
        logger.info(f"{Fore.CYAN}🎯 REALISTIC PERFORMANCE TEST - BROWSER POOL")
        logger.info(f"{Fore.CYAN}{'='*60}")
        
        # Test the actual system with browser pool
        await self.test_unified_handler_with_pool()
        
    async def test_unified_handler_with_pool(self):
        """Test UnifiedTicketingHandler with browser pool"""
        from src.core.browser_pool import get_browser_pool
        from src.stealth.stealth_engine import StealthMasterEngine
        
        # Initialize components
        pool_config = {
            'headless': False,  # Use headful for realistic test
            'channel': 'chrome',
            'min_size': 3,
            'max_size': 5,
            'max_age_seconds': 3600
        }
        
        browser_pool = await get_browser_pool(pool_config)
        stealth_engine = StealthMasterEngine()
        
        logger.info("\n📊 Testing with Browser Pool")
        logger.info("  - Pool size: 3-5 browsers")
        logger.info("  - Stealth engine: Enabled")
        logger.info("  - Test URLs: 5 different sites")
        
        metrics = {
            'scan_times': [],
            'acquisition_times': [],
            'navigation_times': [],
            'stealth_application_times': []
        }
        
        # Simulate 15 scans across different URLs
        for i in range(15):
            url = self.test_urls[i % len(self.test_urls)]
            scan_start = time.time()
            
            try:
                # Acquire browser from pool
                acq_start = time.time()
                async with browser_pool.acquire_browser() as (browser, context, page):
                    acquisition_time = time.time() - acq_start
                    metrics['acquisition_times'].append(acquisition_time)
                    
                    # Apply stealth
                    stealth_start = time.time()
                    await stealth_engine.apply_ultimate_stealth(
                        browser, context, page, "generic"
                    )
                    stealth_time = time.time() - stealth_start
                    metrics['stealth_application_times'].append(stealth_time)
                    
                    # Navigate
                    nav_start = time.time()
                    try:
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    except Exception as e:
                        logger.warning(f"Navigation error for {url}: {str(e)[:50]}")
                    nav_time = time.time() - nav_start
                    metrics['navigation_times'].append(nav_time)
                    
                    # Simulate ticket checking
                    await asyncio.sleep(0.5)
                    
                    # Try to find some elements (simulate real work)
                    try:
                        await page.evaluate("""() => {
                            return document.querySelectorAll('a').length;
                        }""")
                    except:
                        pass
                    
                scan_time = time.time() - scan_start
                metrics['scan_times'].append(scan_time)
                
                logger.info(
                    f"  Scan {i+1}/15 [{url.split('/')[2]}]: "
                    f"{scan_time:.2f}s total "
                    f"(acq: {acquisition_time:.3f}s, nav: {nav_time:.2f}s)"
                )
                
            except Exception as e:
                logger.error(f"  Scan {i+1} failed: {str(e)[:100]}")
        
        # Get pool statistics
        pool_stats = browser_pool.get_stats()
        
        # Shutdown pool
        await browser_pool.shutdown_pool()
        
        # Report results
        logger.info(f"\n{Fore.GREEN}📈 RESULTS:")
        logger.info(f"  Total scans: {len(metrics['scan_times'])}")
        logger.info(f"  Avg scan time: {sum(metrics['scan_times'])/len(metrics['scan_times']):.2f}s")
        logger.info(f"  Avg acquisition: {sum(metrics['acquisition_times'])/len(metrics['acquisition_times']):.3f}s")
        logger.info(f"  Avg navigation: {sum(metrics['navigation_times'])/len(metrics['navigation_times']):.2f}s")
        logger.info(f"  Pool hit rate: {pool_stats['hit_rate']:.1f}%")
        logger.info(f"  Browsers created: {pool_stats['browsers_created']}")
        logger.info(f"  Browsers recycled: {pool_stats['browsers_recycled']}")
        
        # Performance insights
        logger.info(f"\n{Fore.CYAN}💡 PERFORMANCE INSIGHTS:")
        
        # Check acquisition efficiency
        avg_acq = sum(metrics['acquisition_times'])/len(metrics['acquisition_times'])
        if avg_acq < 0.5:
            logger.info(f"  {Fore.GREEN}✓ Excellent browser acquisition time (<0.5s)")
        elif avg_acq < 1.0:
            logger.info(f"  {Fore.YELLOW}⚠ Good browser acquisition time (<1s)")
        else:
            logger.info(f"  {Fore.RED}✗ Slow browser acquisition (>1s)")
        
        # Check pool efficiency
        if pool_stats['hit_rate'] > 80:
            logger.info(f"  {Fore.GREEN}✓ Excellent pool utilization (>80% hit rate)")
        elif pool_stats['hit_rate'] > 50:
            logger.info(f"  {Fore.YELLOW}⚠ Good pool utilization (>50% hit rate)")
        else:
            logger.info(f"  {Fore.RED}✗ Poor pool utilization (<50% hit rate)")
        
        # Estimate time saved
        browser_launch_time = 0.5  # Conservative estimate
        time_saved = (pool_stats['pool_hits'] * browser_launch_time)
        logger.info(f"  {Fore.GREEN}⏱️  Estimated time saved: {time_saved:.1f}s")
        
        # Memory efficiency
        browsers_reused = pool_stats['pool_hits']
        memory_saved_mb = browsers_reused * 50  # ~50MB per browser instance
        logger.info(f"  {Fore.GREEN}💾 Estimated memory saved: {memory_saved_mb} MB")
        
        # Save detailed metrics
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'pool_stats': pool_stats,
            'summary': {
                'total_scans': len(metrics['scan_times']),
                'avg_scan_time': sum(metrics['scan_times'])/len(metrics['scan_times']),
                'pool_efficiency': pool_stats['hit_rate'],
                'time_saved_estimate': time_saved,
                'memory_saved_estimate_mb': memory_saved_mb
            }
        }
        
        with open('realistic_performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n{Fore.GREEN}📄 Report saved to: realistic_performance_report.json")


async def main():
    """Run realistic performance test"""
    test = RealisticPerformanceTest()
    try:
        await test.run_test()
    except KeyboardInterrupt:
        logger.info("\n👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())