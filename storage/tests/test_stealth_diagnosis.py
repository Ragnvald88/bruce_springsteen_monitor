#!/usr/bin/env python3
"""
StealthMaster AI Quick Diagnostic Tool
Tests proxy, stealth measures, and platform access
"""

import asyncio
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from playwright.async_api import async_playwright
import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('StealthMaster')


class StealthDiagnostic:
    """Quick diagnostic for StealthMaster AI"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'proxy_tests': {},
            'stealth_tests': {},
            'platform_tests': {},
            'recommendations': []
        }
        
    async def run_diagnostics(self):
        """Run all diagnostic tests"""
        logger.info("="*80)
        logger.info("🛡️  STEALTHMASTER AI DIAGNOSTIC v2.0")
        logger.info("="*80)
        
        # Test 1: Proxy
        await self.test_proxy()
        
        # Test 2: Stealth detection
        await self.test_stealth_measures()
        
        # Test 3: Platform access
        await self.test_platforms()
        
        # Generate recommendations
        self.analyze_results()
        
        # Save report
        self.save_report()
        
    async def test_proxy(self):
        """Test proxy connectivity"""
        logger.info("\n🔍 TESTING PROXY CONNECTIVITY...")
        
        # Get proxy from environment
        proxy_host = os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')
        proxy_port = os.getenv('IPROYAL_PORT', '12321')
        proxy_user = os.getenv('IPROYAL_USERNAME', '')
        proxy_pass = os.getenv('IPROYAL_PASSWORD', '')
        
        if not proxy_user or not proxy_pass:
            logger.error("❌ No proxy credentials found in environment!")
            self.results['proxy_tests']['configured'] = False
            return
            
        proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        logger.info(f"Testing proxy: {proxy_host}:{proxy_port}")
        
        # Test with httpx
        try:
            start = time.time()
            async with httpx.AsyncClient(
                proxies={
                    "http://": proxy_url,
                    "https://": proxy_url
                },
                timeout=20.0
            ) as client:
                # Try multiple services
                for service in ['http://ip-api.com/json', 'https://api.ipify.org?format=json']:
                    try:
                        response = await client.get(service)
                        if response.status_code == 200:
                            data = response.json()
                            detected_ip = data.get('query') or data.get('ip')
                            response_time = (time.time() - start) * 1000
                            
                            logger.info(f"✅ Proxy working!")
                            logger.info(f"   Detected IP: {detected_ip}")
                            logger.info(f"   Response time: {response_time:.0f}ms")
                            
                            self.results['proxy_tests']['httpx'] = {
                                'working': True,
                                'detected_ip': detected_ip,
                                'response_time': response_time
                            }
                            break
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Proxy test failed: {e}")
            self.results['proxy_tests']['httpx'] = {
                'working': False,
                'error': str(e)
            }
            
        # Test with Playwright
        logger.info("\nTesting proxy with browser...")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    proxy={
                        'server': proxy_url
                    },
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-http2',
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Test navigation
                try:
                    await page.goto('https://httpbin.org/ip', timeout=20000)
                    content = await page.content()
                    
                    logger.info("✅ Browser proxy test passed!")
                    self.results['proxy_tests']['playwright'] = {
                        'working': True,
                        'page_loaded': True
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Browser navigation failed: {e}")
                    self.results['proxy_tests']['playwright'] = {
                        'working': False,
                        'error': str(e)
                    }
                    
                await browser.close()
                
            except Exception as e:
                logger.error(f"❌ Browser launch failed: {e}")
                self.results['proxy_tests']['playwright'] = {
                    'working': False,
                    'launch_error': str(e)
                }
                
    async def test_stealth_measures(self):
        """Test browser stealth detection"""
        logger.info("\n🔍 TESTING STEALTH MEASURES...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Use headful for better stealth
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-http2',
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            page = await context.new_page()
            
            # Apply stealth JavaScript
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Fix chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            """)
            
            # Test on bot detection site
            try:
                logger.info("Testing on bot.sannysoft.com...")
                await page.goto('https://bot.sannysoft.com/', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Check detection status
                failed_tests = await page.evaluate("""
                    () => {
                        const tests = [];
                        const rows = document.querySelectorAll('table tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 2) {
                                const testName = cells[0]?.textContent?.trim();
                                const result = cells[1]?.textContent?.trim();
                                if (result && (result.includes('missing') || result.includes('failed'))) {
                                    tests.push(testName);
                                }
                            }
                        });
                        return tests;
                    }
                """)
                
                if failed_tests:
                    logger.warning(f"⚠️ Failed stealth tests: {', '.join(failed_tests)}")
                else:
                    logger.info("✅ All stealth tests passed!")
                    
                self.results['stealth_tests']['bot_sannysoft'] = {
                    'passed': len(failed_tests) == 0,
                    'failed_tests': failed_tests
                }
                
                # Take screenshot
                await page.screenshot(path='stealth_test.png')
                logger.info("📸 Screenshot saved: stealth_test.png")
                
            except Exception as e:
                logger.error(f"Stealth test error: {e}")
                self.results['stealth_tests']['bot_sannysoft'] = {
                    'error': str(e)
                }
                
            await browser.close()
            
    async def test_platforms(self):
        """Test access to ticketing platforms"""
        logger.info("\n🔍 TESTING PLATFORM ACCESS...")
        
        platforms = [
            {
                'name': 'Fansale',
                'urls': [
                    'https://www.fansale.it',
                    'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554/17844388'
                ]
            },
            {
                'name': 'Ticketmaster',
                'urls': [
                    'https://www.ticketmaster.it',
                    'https://shop.ticketmaster.it/biglietti/bruce-springsteen-2025-milano'
                ]
            },
            {
                'name': 'Vivaticket',
                'urls': [
                    'https://www.vivaticket.com/it',
                    'https://www.vivaticket.com/it/search?q=bruce+springsteen'
                ]
            }
        ]
        
        # Get proxy settings
        proxy_config = None
        proxy_user = os.getenv('IPROYAL_USERNAME', '')
        if proxy_user:
            proxy_host = os.getenv('IPROYAL_HOSTNAME', 'geo.iproyal.com')
            proxy_port = os.getenv('IPROYAL_PORT', '12321')
            proxy_pass = os.getenv('IPROYAL_PASSWORD', '')
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            proxy_config = {'server': proxy_url}
            
        async with async_playwright() as p:
            for platform in platforms:
                logger.info(f"\nTesting {platform['name']}...")
                
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy_config,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-http2',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='it-IT',  # Italian locale for Italian sites
                    timezone_id='Europe/Rome'
                )
                
                page = await context.new_page()
                
                platform_results = {
                    'accessible': False,
                    'urls_tested': {},
                    'blocks_detected': [],
                    'errors': []
                }
                
                for url in platform['urls']:
                    try:
                        logger.info(f"  Testing: {url}")
                        response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                        
                        status = response.status if response else 0
                        logger.info(f"    Status: {status}")
                        
                        # Check for blocks
                        content = await page.content()
                        title = await page.title()
                        
                        blocked = False
                        block_reasons = []
                        
                        if status == 403:
                            blocked = True
                            block_reasons.append('403 Forbidden')
                        
                        if 'blocked' in content.lower() or 'forbidden' in content.lower():
                            blocked = True
                            block_reasons.append('Blocked message detected')
                            
                        if 'captcha' in content.lower() or 'challenge' in content.lower():
                            blocked = True
                            block_reasons.append('Captcha detected')
                            
                        if 'cloudflare' in content.lower():
                            blocked = True
                            block_reasons.append('Cloudflare protection')
                            
                        platform_results['urls_tested'][url] = {
                            'status': status,
                            'title': title,
                            'blocked': blocked,
                            'reasons': block_reasons
                        }
                        
                        if not blocked and status == 200:
                            platform_results['accessible'] = True
                            logger.info(f"    ✅ Accessible!")
                        else:
                            logger.warning(f"    ❌ Blocked: {', '.join(block_reasons)}")
                            platform_results['blocks_detected'].extend(block_reasons)
                            
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"    ❌ Error: {error_msg}")
                        platform_results['errors'].append(error_msg)
                        platform_results['urls_tested'][url] = {
                            'error': error_msg
                        }
                        
                await browser.close()
                
                self.results['platform_tests'][platform['name'].lower()] = platform_results
                
    def analyze_results(self):
        """Analyze results and generate recommendations"""
        logger.info("\n📊 ANALYZING RESULTS...")
        
        recommendations = []
        
        # Check proxy
        proxy_working = False
        if 'httpx' in self.results['proxy_tests']:
            proxy_working = self.results['proxy_tests']['httpx'].get('working', False)
            
        if not proxy_working:
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Proxy not working',
                'solution': [
                    'Verify proxy credentials in .env file',
                    'Check if proxy service is active',
                    'Try alternative proxy endpoints',
                    'Consider using residential proxies'
                ]
            })
            
        # Check stealth
        stealth_ok = False
        if 'bot_sannysoft' in self.results['stealth_tests']:
            stealth_ok = self.results['stealth_tests']['bot_sannysoft'].get('passed', False)
            
        if not stealth_ok:
            failed = self.results['stealth_tests']['bot_sannysoft'].get('failed_tests', [])
            recommendations.append({
                'priority': 'HIGH',
                'issue': f'Stealth detection failing: {", ".join(failed)}',
                'solution': [
                    'Use undetected-chromedriver instead of regular Playwright',
                    'Implement more sophisticated fingerprint spoofing',
                    'Add browser profile rotation',
                    'Use headless=False for critical operations'
                ]
            })
            
        # Check platform access
        for platform, results in self.results['platform_tests'].items():
            if not results.get('accessible', False):
                blocks = list(set(results.get('blocks_detected', [])))
                recommendations.append({
                    'priority': 'HIGH',
                    'issue': f'{platform.title()} blocking access: {", ".join(blocks)}',
                    'solution': [
                        'Use residential proxies from Italy',
                        'Implement request rate limiting',
                        'Add more human-like behavior patterns',
                        'Consider using Playwright stealth plugin',
                        'Rotate user agents and browser profiles'
                    ]
                })
                
        self.results['recommendations'] = recommendations
        
    def save_report(self):
        """Save diagnostic report"""
        report_file = 'stealthmaster_diagnostic_report.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"\n📄 Detailed report saved to: {report_file}")
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("📊 DIAGNOSTIC SUMMARY")
        logger.info("="*80)
        
        # Proxy status
        proxy_ok = self.results['proxy_tests'].get('httpx', {}).get('working', False)
        logger.info(f"🌐 Proxy Status: {'✅ WORKING' if proxy_ok else '❌ FAILED'}")
        
        # Stealth status
        stealth_ok = self.results['stealth_tests'].get('bot_sannysoft', {}).get('passed', False)
        logger.info(f"🛡️ Stealth Status: {'✅ UNDETECTED' if stealth_ok else '❌ DETECTED'}")
        
        # Platform status
        logger.info("\n🎯 Platform Access:")
        for platform, results in self.results['platform_tests'].items():
            accessible = results.get('accessible', False)
            status = '✅ ACCESSIBLE' if accessible else '❌ BLOCKED'
            logger.info(f"  {platform.title()}: {status}")
            
        # Recommendations
        if self.results['recommendations']:
            logger.info("\n💡 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(self.results['recommendations'][:3], 1):
                logger.info(f"\n  {i}. [{rec['priority']}] {rec['issue']}")
                for solution in rec['solution'][:2]:
                    logger.info(f"     → {solution}")
                    
        logger.info("\n" + "="*80)
        logger.info("🏁 DIAGNOSTIC COMPLETE")
        logger.info("="*80)


async def main():
    """Run StealthMaster diagnostic"""
    diagnostic = StealthDiagnostic()
    await diagnostic.run_diagnostics()


if __name__ == "__main__":
    asyncio.run(main())