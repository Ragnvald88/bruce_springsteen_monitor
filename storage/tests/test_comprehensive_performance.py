#!/usr/bin/env python3
"""
Comprehensive Performance and Stealth Test Suite
Tests profiles, stealth effectiveness, performance metrics, and efficiency
"""

import asyncio
import os
import sys
import time
import psutil
import json
import random
from datetime import datetime
from typing import Dict, List, Any, Tuple
import statistics

# Add src to path
sys.path.insert(0, 'src')

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from stealth.cdp_stealth import CDPStealthEngine
from profiles.manager import ProfileManager
from core.proxy_manager import StealthProxyManager

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('PerformanceTest')


class PerformanceMetrics:
    """Track performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'browser_launch_times': [],
            'page_load_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'network_latency': [],
            'stealth_detection_results': {},
            'profile_fingerprints': {},
            'proxy_performance': {},
            'resource_efficiency': {}
        }
        self.process = psutil.Process()
        
    def record_metric(self, category: str, value: float, label: str = None):
        """Record a performance metric"""
        if category not in self.metrics:
            self.metrics[category] = []
        
        if label:
            if not isinstance(self.metrics[category], dict):
                self.metrics[category] = {}
            self.metrics[category][label] = value
        else:
            self.metrics[category].append(value)
            
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        return {
            'memory_mb': self.process.memory_info().rss / 1024 / 1024,
            'cpu_percent': self.process.cpu_percent(interval=0.1),
            'num_threads': self.process.num_threads(),
            'open_files': len(self.process.open_files())
        }
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        report = {}
        
        for category, data in self.metrics.items():
            if isinstance(data, list) and data:
                report[category] = {
                    'mean': statistics.mean(data),
                    'median': statistics.median(data),
                    'min': min(data),
                    'max': max(data),
                    'std_dev': statistics.stdev(data) if len(data) > 1 else 0
                }
            else:
                report[category] = data
                
        return report


async def test_stealth_effectiveness(page: Page, profile_name: str) -> Dict[str, Any]:
    """Test stealth effectiveness on multiple detection services"""
    logger.info(f"🔍 Testing stealth effectiveness for {profile_name}")
    
    results = {
        'profile': profile_name,
        'tests': {},
        'score': 0
    }
    
    # Test 1: Bot.sannysoft.com
    try:
        logger.info("  Testing bot.sannysoft.com...")
        await page.goto('https://bot.sannysoft.com/', timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Extract test results
        test_results = await page.evaluate("""
            () => {
                const results = {};
                const rows = document.querySelectorAll('table tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                        const test = cells[0]?.textContent?.trim();
                        const result = cells[1]?.textContent?.trim();
                        if (test && test !== 'Test') {
                            results[test] = result;
                        }
                    }
                });
                return results;
            }
        """)
        
        # Analyze results
        passed_tests = 0
        total_tests = len(test_results)
        
        for test, result in test_results.items():
            is_passed = 'passed' in result.lower() or 'missing' not in result.lower()
            if is_passed:
                passed_tests += 1
            results['tests'][f'sannysoft_{test}'] = is_passed
            
        results['sannysoft_score'] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
    except Exception as e:
        logger.error(f"  Sannysoft test failed: {e}")
        results['tests']['sannysoft'] = False
        
    # Test 2: Fingerprint detection
    try:
        logger.info("  Testing fingerprint uniqueness...")
        fingerprint = await page.evaluate("""
            () => {
                return {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    platform: navigator.platform,
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    screenResolution: `${screen.width}x${screen.height}`,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    webdriver: navigator.webdriver,
                    plugins: navigator.plugins.length,
                    canvas: (() => {
                        try {
                            const canvas = document.createElement('canvas');
                            const ctx = canvas.getContext('2d');
                            ctx.textBaseline = 'top';
                            ctx.font = '14px Arial';
                            ctx.fillText('fingerprint', 2, 2);
                            return canvas.toDataURL().slice(-50);
                        } catch (e) {
                            return 'error';
                        }
                    })()
                };
            }
        """)
        
        results['fingerprint'] = fingerprint
        results['tests']['webdriver_hidden'] = fingerprint['webdriver'] is None or fingerprint['webdriver'] == 'undefined'
        results['tests']['plugins_present'] = fingerprint['plugins'] > 0
        
    except Exception as e:
        logger.error(f"  Fingerprint test failed: {e}")
        
    # Test 3: Platform-specific detection
    platforms = {
        'fansale': 'https://www.fansale.it',
        'ticketmaster': 'https://www.ticketmaster.it',
        'vivaticket': 'https://www.vivaticket.com/it'
    }
    
    for platform, url in platforms.items():
        try:
            logger.info(f"  Testing {platform} detection...")
            response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            is_blocked = any(word in content.lower() for word in ['blocked', 'forbidden', 'captcha', 'challenge'])
            
            results['tests'][f'{platform}_accessible'] = not is_blocked
            results[f'{platform}_status'] = response.status if response else 0
            
        except Exception as e:
            logger.error(f"  {platform} test failed: {e}")
            results['tests'][f'{platform}_accessible'] = False
            
    # Calculate overall score
    total_passed = sum(1 for passed in results['tests'].values() if passed)
    total_tests = len(results['tests'])
    results['score'] = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    return results


async def test_profile_performance(profile_manager: ProfileManager, metrics: PerformanceMetrics):
    """Test performance across different profiles"""
    logger.info("\n📊 TESTING PROFILE PERFORMANCE...")
    
    # Get all profiles
    all_profile_ids = list(profile_manager.profiles.keys())
    profiles = []
    for profile_id in all_profile_ids[:5]:  # Test first 5 profiles
        profile = profile_manager.get_profile(profile_id)
        if profile:
            profiles.append(profile)
    
    async with async_playwright() as p:
        for profile in profiles:
            logger.info(f"\nTesting profile: {profile.id}")
            
            # Measure browser launch time
            start_time = time.time()
            browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
            launch_time = time.time() - start_time
            metrics.record_metric('browser_launch_times', launch_time)
            logger.info(f"  Browser launch: {launch_time:.2f}s")
            
            # Get proxy config
            proxy_config = None
            if profile.proxy_config:
                proxy_config = {
                    'server': profile.proxy_config.get('server') if isinstance(profile.proxy_config, dict) else profile.proxy_config.server
                }
                
            # Create context
            context_start = time.time()
            context = await CDPStealthEngine.create_stealth_context(browser, proxy_config)
            context_time = time.time() - context_start
            logger.info(f"  Context creation: {context_time:.2f}s")
            
            # Create page and test
            page = await context.new_page()
            await CDPStealthEngine.apply_page_stealth(page)
            
            # Record system metrics
            sys_metrics = metrics.get_system_metrics()
            metrics.record_metric('memory_usage', sys_metrics['memory_mb'])
            metrics.record_metric('cpu_usage', sys_metrics['cpu_percent'])
            
            # Test stealth effectiveness
            stealth_results = await test_stealth_effectiveness(page, profile.id)
            metrics.record_metric('stealth_detection_results', stealth_results, profile.id)
            
            logger.info(f"  Stealth score: {stealth_results['score']:.1f}%")
            logger.info(f"  Memory usage: {sys_metrics['memory_mb']:.1f} MB")
            logger.info(f"  CPU usage: {sys_metrics['cpu_percent']:.1f}%")
            
            await browser.close()
            
            # Cool down between profiles
            await asyncio.sleep(2)


async def test_concurrent_performance(metrics: PerformanceMetrics):
    """Test performance with concurrent browsers"""
    logger.info("\n🚀 TESTING CONCURRENT PERFORMANCE...")
    
    async def run_browser_instance(index: int):
        """Run a single browser instance"""
        async with async_playwright() as p:
            browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
            context = await CDPStealthEngine.create_stealth_context(browser, None)
            page = await context.new_page()
            
            # Simulate monitoring activity
            urls = [
                'https://www.fansale.it/fansale/',
                'https://www.vivaticket.com/it',
                'https://www.ticketmaster.it'
            ]
            
            for url in urls:
                try:
                    start = time.time()
                    await page.goto(url, timeout=30000)
                    load_time = time.time() - start
                    metrics.record_metric('page_load_times', load_time)
                except:
                    pass
                    
            await browser.close()
            
    # Test with different concurrency levels
    for concurrent_count in [1, 3, 5]:
        logger.info(f"\nTesting with {concurrent_count} concurrent browsers...")
        
        start_time = time.time()
        start_metrics = metrics.get_system_metrics()
        
        # Run concurrent browsers
        tasks = [run_browser_instance(i) for i in range(concurrent_count)]
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        end_metrics = metrics.get_system_metrics()
        
        # Record efficiency metrics
        metrics.record_metric('resource_efficiency', {
            'concurrent_count': concurrent_count,
            'total_time': total_time,
            'memory_increase': end_metrics['memory_mb'] - start_metrics['memory_mb'],
            'avg_cpu': end_metrics['cpu_percent']
        }, f'concurrent_{concurrent_count}')
        
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Memory increase: {end_metrics['memory_mb'] - start_metrics['memory_mb']:.1f} MB")


async def test_proxy_performance(proxy_manager: StealthProxyManager, metrics: PerformanceMetrics):
    """Test proxy performance and reliability"""
    logger.info("\n🌐 TESTING PROXY PERFORMANCE...")
    
    proxies = await proxy_manager.get_all_proxies()
    
    for proxy in proxies[:3]:  # Test first 3 proxies
        logger.info(f"\nTesting proxy: {proxy.get('server', 'Unknown')}")
        
        # Test latency
        start = time.time()
        is_valid = await proxy_manager.validate_proxy(proxy)
        latency = time.time() - start
        
        metrics.record_metric('network_latency', latency)
        metrics.record_metric('proxy_performance', {
            'valid': is_valid,
            'latency': latency,
            'location': proxy.get('location', 'Unknown')
        }, proxy.get('server', 'unknown'))
        
        logger.info(f"  Valid: {is_valid}")
        logger.info(f"  Latency: {latency:.2f}s")


async def test_detection_patterns():
    """Test various detection patterns and evasion techniques"""
    logger.info("\n🕵️ TESTING DETECTION PATTERNS...")
    
    detection_tests = {
        'mouse_movement': {
            'description': 'Human-like mouse movement',
            'test': lambda page: CDPStealthEngine.simulate_human_mouse(page)
        },
        'typing_pattern': {
            'description': 'Human-like typing speed',
            'test': lambda page: CDPStealthEngine.type_like_human(page, 'input', 'test')
        },
        'scroll_behavior': {
            'description': 'Natural scrolling',
            'test': lambda page: page.evaluate("""
                () => {
                    window.scrollTo({
                        top: 500,
                        behavior: 'smooth'
                    });
                }
            """)
        }
    }
    
    results = {}
    
    async with async_playwright() as p:
        browser = await CDPStealthEngine.create_undetectable_browser(p.chromium)
        context = await CDPStealthEngine.create_stealth_context(browser, None)
        page = await context.new_page()
        
        for test_name, test_info in detection_tests.items():
            try:
                logger.info(f"  Testing {test_info['description']}...")
                await test_info['test'](page)
                results[test_name] = 'passed'
            except Exception as e:
                logger.error(f"    Failed: {e}")
                results[test_name] = 'failed'
                
        await browser.close()
        
    return results


async def generate_improvement_plan(metrics: PerformanceMetrics):
    """Generate improvement plan based on test results"""
    logger.info("\n📋 GENERATING IMPROVEMENT PLAN...")
    
    report = metrics.generate_report()
    
    improvements = []
    
    # Analyze browser launch times
    if report.get('browser_launch_times', {}).get('mean', 0) > 2.0:
        improvements.append({
            'category': 'Performance',
            'issue': 'Slow browser launch times',
            'recommendation': 'Implement browser pooling to reuse instances',
            'priority': 'High'
        })
        
    # Analyze memory usage
    if report.get('memory_usage', {}).get('mean', 0) > 500:
        improvements.append({
            'category': 'Resource Usage',
            'issue': 'High memory consumption',
            'recommendation': 'Implement periodic browser restarts and better cleanup',
            'priority': 'Medium'
        })
        
    # Analyze stealth effectiveness
    stealth_scores = []
    for profile_id, results in report.get('stealth_detection_results', {}).items():
        if isinstance(results, dict) and 'score' in results:
            stealth_scores.append(results['score'])
            
    if stealth_scores and statistics.mean(stealth_scores) < 80:
        improvements.append({
            'category': 'Stealth',
            'issue': 'Low stealth effectiveness scores',
            'recommendation': 'Enhance CDP stealth with additional evasion techniques',
            'priority': 'High'
        })
        
    # Analyze proxy performance
    slow_proxies = []
    for proxy, perf in report.get('proxy_performance', {}).items():
        if isinstance(perf, dict) and perf.get('latency', 0) > 5:
            slow_proxies.append(proxy)
            
    if slow_proxies:
        improvements.append({
            'category': 'Network',
            'issue': f'Slow proxy performance: {len(slow_proxies)} proxies',
            'recommendation': 'Implement proxy benchmarking and automatic rotation',
            'priority': 'Medium'
        })
        
    return improvements, report


async def main():
    """Run comprehensive performance tests"""
    logger.info("="*80)
    logger.info("🔬 COMPREHENSIVE PERFORMANCE AND STEALTH TEST")
    logger.info("="*80)
    
    metrics = PerformanceMetrics()
    
    # Initialize managers
    profile_manager = ProfileManager()
    proxy_manager = StealthProxyManager({
        'proxy_providers': [{
            'name': 'iproyal',
            'type': 'residential',
            'endpoints': []
        }]
    })
    
    # Run tests
    await test_profile_performance(profile_manager, metrics)
    await test_concurrent_performance(metrics)
    await test_proxy_performance(proxy_manager, metrics)
    detection_results = await test_detection_patterns()
    
    # Generate improvement plan
    improvements, report = await generate_improvement_plan(metrics)
    
    # Save detailed report
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'metrics': report,
        'detection_patterns': detection_results,
        'improvements': improvements
    }
    
    with open('performance_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
        
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("📊 PERFORMANCE TEST SUMMARY")
    logger.info("="*80)
    
    logger.info("\n🎯 Key Metrics:")
    if 'browser_launch_times' in report:
        logger.info(f"  Avg browser launch: {report['browser_launch_times']['mean']:.2f}s")
    if 'page_load_times' in report:
        logger.info(f"  Avg page load: {report['page_load_times']['mean']:.2f}s")
    if 'memory_usage' in report:
        logger.info(f"  Avg memory usage: {report['memory_usage']['mean']:.1f} MB")
    if 'cpu_usage' in report:
        logger.info(f"  Avg CPU usage: {report['cpu_usage']['mean']:.1f}%")
        
    logger.info("\n🛡️ Stealth Effectiveness:")
    for profile_id, results in report.get('stealth_detection_results', {}).items():
        if isinstance(results, dict):
            logger.info(f"  {profile_id}: {results.get('score', 0):.1f}% detection evasion")
            
    logger.info("\n📈 Improvement Plan:")
    for imp in improvements:
        logger.info(f"\n  [{imp['priority']}] {imp['category']}")
        logger.info(f"  Issue: {imp['issue']}")
        logger.info(f"  Fix: {imp['recommendation']}")
        
    logger.info("\n✅ Full report saved to: performance_report.json")


if __name__ == "__main__":
    asyncio.run(main())