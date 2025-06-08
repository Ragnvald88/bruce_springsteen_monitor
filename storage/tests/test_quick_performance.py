#!/usr/bin/env python3
"""
Quick Performance and Stealth Test
Focused test for immediate insights
"""

import asyncio
import os
import sys
import time
import psutil
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright
from stealth.cdp_stealth import CDPStealthEngine

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('QuickPerfTest')


async def test_stealth_and_performance():
    """Quick test of stealth effectiveness and performance"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'performance': {},
        'recommendations': []
    }
    
    process = psutil.Process()
    start_memory = process.memory_info().rss / 1024 / 1024
    
    async with async_playwright() as p:
        # Test 1: Browser Launch Performance
        logger.info("🚀 Testing browser launch performance...")
        launch_start = time.time()
        browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
        launch_time = time.time() - launch_start
        results['performance']['browser_launch_time'] = launch_time
        logger.info(f"  Launch time: {launch_time:.2f}s")
        
        # Test 2: Context Creation with Proxy
        logger.info("\n🌐 Testing context creation...")
        proxy_config = None
        if os.getenv('IPROYAL_USERNAME'):
            proxy_config = {
                'server': f"http://{os.getenv('IPROYAL_USERNAME')}:{os.getenv('IPROYAL_PASSWORD')}@geo.iproyal.com:12321"
            }
            
        context_start = time.time()
        context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
        context_time = time.time() - context_start
        results['performance']['context_creation_time'] = context_time
        logger.info(f"  Context creation: {context_time:.2f}s")
        
        # Test 3: Page Creation and Stealth Application
        page_start = time.time()
        page = await context.new_page()
        await CDPStealthEngine.apply_page_stealth(page)
        page_time = time.time() - page_start
        results['performance']['page_setup_time'] = page_time
        logger.info(f"  Page setup: {page_time:.2f}s")
        
        # Test 4: Stealth Detection
        logger.info("\n🕵️ Testing stealth effectiveness...")
        
        # Check WebDriver
        await page.goto('https://bot.sannysoft.com/', timeout=30000)
        await page.wait_for_timeout(2000)
        
        webdriver_check = await page.evaluate("() => navigator.webdriver")
        results['tests']['webdriver_hidden'] = webdriver_check is None or webdriver_check == False
        logger.info(f"  WebDriver hidden: {results['tests']['webdriver_hidden']}")
        
        # Check Chrome
        chrome_check = await page.evaluate("() => !!window.chrome")
        results['tests']['chrome_present'] = chrome_check
        logger.info(f"  Chrome object present: {chrome_check}")
        
        # Check Plugins
        plugins_count = await page.evaluate("() => navigator.plugins.length")
        results['tests']['plugins_count'] = plugins_count
        logger.info(f"  Plugin count: {plugins_count}")
        
        # Test 5: Platform Access Performance
        logger.info("\n🎫 Testing platform access...")
        platforms = [
            ('Fansale', 'https://www.fansale.it'),
            ('Vivaticket', 'https://www.vivaticket.com/it'),
            ('Ticketmaster', 'https://www.ticketmaster.it')
        ]
        
        for name, url in platforms:
            try:
                start = time.time()
                response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                load_time = time.time() - start
                
                content = await page.content()
                is_blocked = any(word in content.lower() for word in ['blocked', 'forbidden', 'captcha'])
                
                results['tests'][f'{name.lower()}_accessible'] = not is_blocked
                results['performance'][f'{name.lower()}_load_time'] = load_time
                
                logger.info(f"  {name}: {'✅ Accessible' if not is_blocked else '❌ Blocked'} ({load_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"  {name}: Error - {str(e)[:50]}")
                results['tests'][f'{name.lower()}_accessible'] = False
                
        # Test 6: Resource Usage
        end_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = end_memory - start_memory
        cpu_percent = process.cpu_percent(interval=0.1)
        
        results['performance']['memory_increase_mb'] = memory_increase
        results['performance']['cpu_percent'] = cpu_percent
        results['performance']['threads'] = process.num_threads()
        
        logger.info(f"\n📊 Resource Usage:")
        logger.info(f"  Memory increase: {memory_increase:.1f} MB")
        logger.info(f"  CPU usage: {cpu_percent:.1f}%")
        logger.info(f"  Threads: {process.num_threads()}")
        
        await browser.close()
        
    # Generate Recommendations
    logger.info("\n💡 Generating recommendations...")
    
    if launch_time > 2.0:
        results['recommendations'].append({
            'issue': 'Slow browser launch',
            'impact': 'High',
            'solution': 'Implement browser pooling to reuse instances'
        })
        
    if memory_increase > 200:
        results['recommendations'].append({
            'issue': 'High memory usage',
            'impact': 'Medium',
            'solution': 'Implement periodic browser restarts'
        })
        
    if not results['tests'].get('webdriver_hidden', False):
        results['recommendations'].append({
            'issue': 'WebDriver detection failing',
            'impact': 'Critical',
            'solution': 'Review CDP stealth implementation'
        })
        
    blocked_platforms = [p for p in ['fansale', 'ticketmaster', 'vivaticket'] 
                        if not results['tests'].get(f'{p}_accessible', False)]
    if blocked_platforms:
        results['recommendations'].append({
            'issue': f'Platforms blocked: {", ".join(blocked_platforms)}',
            'impact': 'High',
            'solution': 'Use platform-specific stealth configurations'
        })
        
    return results


async def test_concurrent_load():
    """Test concurrent browser performance"""
    logger.info("\n🔄 Testing concurrent load...")
    
    async def browser_task(index):
        async with async_playwright() as p:
            browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
            context = await CDPStealthEngine.create_stealth_context(browser, None)
            page = await context.new_page()
            await page.goto('https://www.fansale.it', timeout=30000)
            await browser.close()
            return index
            
    # Test with 3 concurrent browsers
    start = time.time()
    tasks = [browser_task(i) for i in range(3)]
    await asyncio.gather(*tasks)
    total_time = time.time() - start
    
    logger.info(f"  3 concurrent browsers completed in {total_time:.2f}s")
    logger.info(f"  Average per browser: {total_time/3:.2f}s")
    
    return total_time


async def main():
    """Run quick performance tests"""
    logger.info("="*60)
    logger.info("⚡ QUICK PERFORMANCE & STEALTH TEST")
    logger.info("="*60)
    
    # Run main tests
    results = await test_stealth_and_performance()
    
    # Run concurrent test
    concurrent_time = await test_concurrent_load()
    results['performance']['concurrent_3_browsers'] = concurrent_time
    
    # Save results
    with open('quick_performance_report.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    # Print Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    logger.info("\n✅ Stealth Tests:")
    for test, result in results['tests'].items():
        if isinstance(result, bool):
            logger.info(f"  {test}: {'PASS' if result else 'FAIL'}")
        else:
            logger.info(f"  {test}: {result}")
            
    logger.info("\n⚡ Performance Metrics:")
    for metric, value in results['performance'].items():
        if isinstance(value, float):
            logger.info(f"  {metric}: {value:.2f}")
            
    logger.info("\n💡 Recommendations:")
    for rec in results['recommendations']:
        logger.info(f"\n  [{rec['impact']}] {rec['issue']}")
        logger.info(f"  → {rec['solution']}")
        
    logger.info("\n✅ Report saved to: quick_performance_report.json")


if __name__ == "__main__":
    asyncio.run(main())