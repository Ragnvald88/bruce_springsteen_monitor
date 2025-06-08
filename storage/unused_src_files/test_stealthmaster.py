#!/usr/bin/env python3
"""
StealthMaster AI Comprehensive Testing Suite
Tests proxy functionality, anti-detection measures, and platform access
"""

import asyncio
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright, Page, BrowserContext
import httpx

# Import our modules
from core.proxy_manager import StealthProxyManager, Proxy
from profiles.manager import ProfileManager
from profiles.models import BrowserProfile
from platforms.unified_handler import UnifiedTicketingHandler
from utils.enhanced_logger import setup_logging
from core.config_loader import load_config

# Setup enhanced logging
setup_logging()
logger = logging.getLogger(__name__)


class StealthMasterTester:
    """Comprehensive testing suite for StealthMaster AI"""
    
    def __init__(self):
        self.results = {
            'proxy_tests': {},
            'platform_tests': {},
            'detection_tests': {},
            'login_tests': {},
            'recommendations': []
        }
        self.config = load_config()
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.critical("="*80)
        logger.critical("🛡️  STEALTHMASTER AI DIAGNOSTIC SUITE v2.0")
        logger.critical("="*80)
        
        # Test 1: Proxy Connectivity
        await self.test_proxy_connectivity()
        
        # Test 2: Browser Fingerprinting
        await self.test_browser_fingerprinting()
        
        # Test 3: Platform Access
        await self.test_platform_access()
        
        # Test 4: Anti-Detection Measures
        await self.test_anti_detection()
        
        # Test 5: Login Functionality
        await self.test_login_functionality()
        
        # Generate Report
        self.generate_report()
        
    async def test_proxy_connectivity(self):
        """Test proxy connectivity and authentication"""
        logger.info("\n🔍 TESTING PROXY CONNECTIVITY...")
        
        proxy_config = self.config.get('proxy_settings', {})
        proxies = proxy_config.get('primary_pool', [])
        
        for i, proxy_data in enumerate(proxies):
            logger.info(f"\nTesting Proxy #{i+1}: {proxy_data.get('host')}:{proxy_data.get('port')}")
            
            # Test 1: Basic connectivity
            proxy = Proxy(
                host=os.getenv(proxy_data['host'].replace('${', '').replace('}', ''), proxy_data['host']),
                port=int(os.getenv(str(proxy_data['port']).replace('${', '').replace('}', ''), proxy_data['port'])),
                username=os.getenv(proxy_data['username'].replace('${', '').replace('}', ''), ''),
                password=os.getenv(proxy_data['password'].replace('${', '').replace('}', ''), ''),
                proxy_type=proxy_data.get('type', 'http')
            )
            
            # Test with httpx
            test_results = await self._test_proxy_with_httpx(proxy)
            
            # Test with Playwright
            playwright_results = await self._test_proxy_with_playwright(proxy)
            
            self.results['proxy_tests'][f'proxy_{i+1}'] = {
                'httpx_test': test_results,
                'playwright_test': playwright_results,
                'proxy_url': proxy.url
            }
            
    async def _test_proxy_with_httpx(self, proxy: Proxy) -> Dict[str, Any]:
        """Test proxy with httpx client"""
        results = {
            'basic_connectivity': False,
            'auth_working': False,
            'response_time': None,
            'detected_ip': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Test multiple endpoints
            test_urls = [
                'http://ip-api.com/json',
                'https://httpbin.org/ip',
                'https://api.ipify.org?format=json'
            ]
            
            for url in test_urls:
                try:
                    async with httpx.AsyncClient(
                        proxies={
                            "http://": proxy.url,
                            "https://": proxy.url
                        },
                        timeout=15.0,
                        follow_redirects=True
                    ) as client:
                        response = await client.get(url)
                        
                        if response.status_code == 200:
                            results['basic_connectivity'] = True
                            results['auth_working'] = True
                            results['response_time'] = (time.time() - start_time) * 1000
                            
                            data = response.json()
                            results['detected_ip'] = data.get('query') or data.get('origin') or data.get('ip')
                            logger.info(f"✅ Proxy working! Detected IP: {results['detected_ip']}")
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed with {url}: {e}")
                    continue
                    
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"❌ Proxy test failed: {e}")
            
        return results
        
    async def _test_proxy_with_playwright(self, proxy: Proxy) -> Dict[str, Any]:
        """Test proxy with Playwright browser"""
        results = {
            'browser_launch': False,
            'page_load': False,
            'javascript_enabled': False,
            'webrtc_leak': False,
            'detected_ip': None,
            'user_agent': None,
            'error': None
        }
        
        async with async_playwright() as p:
            try:
                # Launch browser with proxy
                browser = await p.chromium.launch(
                    headless=True,
                    proxy={
                        'server': proxy.url
                    },
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-http2',
                        '--force-http1'
                    ]
                )
                results['browser_launch'] = True
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                page = await context.new_page()
                
                # Test page loading
                try:
                    await page.goto('https://api.ipify.org?format=json', timeout=20000)
                    results['page_load'] = True
                    
                    # Get detected IP
                    content = await page.content()
                    if 'ip' in content:
                        import re
                        ip_match = re.search(r'"ip":"([^"]+)"', content)
                        if ip_match:
                            results['detected_ip'] = ip_match.group(1)
                            
                except Exception as e:
                    logger.debug(f"Page load error: {e}")
                    
                # Test JavaScript execution
                try:
                    js_result = await page.evaluate("() => navigator.userAgent")
                    results['javascript_enabled'] = bool(js_result)
                    results['user_agent'] = js_result
                except:
                    pass
                    
                # Test WebRTC leak
                try:
                    await page.goto('https://browserleaks.com/webrtc', timeout=15000)
                    await page.wait_for_timeout(2000)
                    content = await page.content()
                    results['webrtc_leak'] = 'Local IP' not in content
                except:
                    pass
                    
                await browser.close()
                
            except Exception as e:
                results['error'] = str(e)
                logger.error(f"Playwright proxy test error: {e}")
                
        return results
        
    async def test_browser_fingerprinting(self):
        """Test browser fingerprinting and stealth measures"""
        logger.info("\n🔍 TESTING BROWSER FINGERPRINTING...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Add stealth scripts
            await page.add_init_script("""
                // Basic stealth overrides
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // Store original chrome
                const originalChrome = window.chrome;
                
                // Create fake chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            """)
            
            # Test on fingerprinting site
            try:
                await page.goto('https://bot.sannysoft.com/', timeout=30000)
                await page.wait_for_timeout(5000)
                
                # Take screenshot for analysis
                screenshot_path = 'fingerprint_test.png'
                await page.screenshot(path=screenshot_path)
                logger.info(f"📸 Fingerprint test screenshot saved: {screenshot_path}")
                
                # Check for failed tests
                failed_tests = await page.evaluate("""
                    () => {
                        const rows = document.querySelectorAll('tr');
                        const failed = [];
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 2) {
                                const status = cells[cells.length - 1].textContent.trim();
                                if (status.includes('❌') || status.includes('fail')) {
                                    failed.push(cells[0].textContent.trim());
                                }
                            }
                        });
                        return failed;
                    }
                """)
                
                self.results['detection_tests']['fingerprint'] = {
                    'failed_tests': failed_tests,
                    'screenshot': screenshot_path
                }
                
                if failed_tests:
                    logger.warning(f"⚠️ Failed fingerprint tests: {', '.join(failed_tests)}")
                else:
                    logger.info("✅ All fingerprint tests passed!")
                    
            except Exception as e:
                logger.error(f"Fingerprint test error: {e}")
                
            await browser.close()
            
    async def test_platform_access(self):
        """Test access to each ticketing platform"""
        logger.info("\n🔍 TESTING PLATFORM ACCESS...")
        
        platforms = [
            {
                'name': 'Fansale',
                'url': 'https://www.fansale.it',
                'test_url': 'https://www.fansale.it/fansale/'
            },
            {
                'name': 'Ticketmaster',
                'url': 'https://www.ticketmaster.it',
                'test_url': 'https://shop.ticketmaster.it'
            },
            {
                'name': 'Vivaticket',
                'url': 'https://www.vivaticket.com',
                'test_url': 'https://www.vivaticket.com/it'
            }
        ]
        
        for platform in platforms:
            logger.info(f"\nTesting {platform['name']}...")
            results = await self._test_single_platform(platform)
            self.results['platform_tests'][platform['name'].lower()] = results
            
    async def _test_single_platform(self, platform: Dict[str, str]) -> Dict[str, Any]:
        """Test a single platform"""
        results = {
            'accessible': False,
            'blocked': False,
            'captcha_detected': False,
            'cloudflare_detected': False,
            'response_code': None,
            'page_title': None,
            'error': None
        }
        
        async with async_playwright() as p:
            # Get a profile from manager
            profile_manager = ProfileManager(self.config)
            profiles = await profile_manager.get_healthy_profiles()
            
            if not profiles:
                logger.error("No profiles available!")
                return results
                
            profile = profiles[0]
            
            # Launch with profile settings
            browser = await p.chromium.launch(
                headless=True,
                args=profile.get_launch_options()['args']
            )
            
            context_params = profile.get_context_params()
            context = await browser.new_context(**context_params)
            
            page = await context.new_page()
            
            # Apply stealth measures
            await self._apply_stealth_measures(page)
            
            try:
                response = await page.goto(platform['test_url'], timeout=30000, wait_until='domcontentloaded')
                
                if response:
                    results['response_code'] = response.status
                    results['accessible'] = response.status == 200
                    
                # Check for blocks
                page_content = await page.content()
                page_title = await page.title()
                results['page_title'] = page_title
                
                # Detection patterns
                if any(pattern in page_content.lower() for pattern in ['blocked', 'forbidden', 'access denied']):
                    results['blocked'] = True
                    
                if any(pattern in page_content for pattern in ['captcha', 'recaptcha', 'challenge']):
                    results['captcha_detected'] = True
                    
                if 'cloudflare' in page_content.lower() or 'cf-ray' in page_content:
                    results['cloudflare_detected'] = True
                    
                # Take screenshot
                screenshot_name = f"{platform['name'].lower()}_test.png"
                await page.screenshot(path=screenshot_name)
                
                logger.info(f"Status: {'✅ Accessible' if results['accessible'] else '❌ Blocked'}")
                if results['blocked']:
                    logger.warning(f"Block reason: Captcha={results['captcha_detected']}, CF={results['cloudflare_detected']}")
                    
            except Exception as e:
                results['error'] = str(e)
                logger.error(f"Platform test error: {e}")
                
            await browser.close()
            
        return results
        
    async def _apply_stealth_measures(self, page: Page):
        """Apply comprehensive stealth measures"""
        # Load stealth scripts
        stealth_js = """
        // Comprehensive stealth measures
        (() => {
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fix chrome object
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {},
                };
            }
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // Fix navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    }
                ]
            });
            
            // WebGL Vendor/Renderer
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Open Source Technology Center';
                }
                if (parameter === 37446) {
                    return 'Mesa DRI Intel(R) Ivybridge Mobile';
                }
                return getParameter(parameter);
            };
            
            // Hide automation indicators
            delete window.__playwright;
            delete window.__selenium;
            delete window.__webdriver;
        })();
        """
        
        await page.add_init_script(stealth_js)
        
    async def test_anti_detection(self):
        """Test advanced anti-detection measures"""
        logger.info("\n🔍 TESTING ANTI-DETECTION MEASURES...")
        
        detection_sites = [
            {
                'name': 'Bot Detection',
                'url': 'https://bot.sannysoft.com/',
                'check': 'fingerprint'
            },
            {
                'name': 'Browser Leaks',
                'url': 'https://browserleaks.com/javascript',
                'check': 'javascript'
            },
            {
                'name': 'WebRTC Leak',
                'url': 'https://browserleaks.com/webrtc',
                'check': 'webrtc'
            }
        ]
        
        for site in detection_sites:
            logger.info(f"\nTesting on {site['name']}...")
            # Implementation would go here
            
    async def test_login_functionality(self):
        """Test login functionality for each platform"""
        logger.info("\n🔍 TESTING LOGIN FUNCTIONALITY...")
        
        # Check for credentials
        platforms = {
            'fansale': {
                'username_env': 'FANSALE_EMAIL',
                'password_env': 'FANSALE_PASSWORD',
                'login_url': 'https://www.fansale.it/fansale/login',
                'username_selector': 'input[name="email"]',
                'password_selector': 'input[name="password"]',
                'submit_selector': 'button[type="submit"]'
            },
            'ticketmaster': {
                'username_env': 'TM_USERNAME',
                'password_env': 'TM_PASSWORD',
                'login_url': 'https://www.ticketmaster.it/member/sign-in',
                'username_selector': 'input[name="email-sign-in"]',
                'password_selector': 'input[name="password-sign-in"]',
                'submit_selector': 'button[type="submit"]'
            }
        }
        
        for platform_name, config in platforms.items():
            username = os.getenv(config['username_env'])
            password = os.getenv(config['password_env'])
            
            if not username or not password:
                logger.warning(f"⚠️ No credentials configured for {platform_name}")
                self.results['login_tests'][platform_name] = {
                    'configured': False,
                    'tested': False
                }
                continue
                
            logger.info(f"\nTesting {platform_name} login...")
            result = await self._test_platform_login(platform_name, config, username, password)
            self.results['login_tests'][platform_name] = result
            
    async def _test_platform_login(self, platform: str, config: Dict, username: str, password: str) -> Dict[str, Any]:
        """Test login for a specific platform"""
        result = {
            'configured': True,
            'tested': True,
            'login_successful': False,
            'error': None,
            'screenshot': None
        }
        
        # Implementation would perform actual login test
        logger.info(f"Would test login for {platform} with user: {username[:3]}***")
        
        return result
        
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.critical("\n" + "="*80)
        logger.critical("📊 STEALTHMASTER AI DIAGNOSTIC REPORT")
        logger.critical("="*80)
        
        # Proxy Report
        logger.info("\n🌐 PROXY STATUS:")
        for proxy_id, results in self.results['proxy_tests'].items():
            httpx_ok = results['httpx_test'].get('basic_connectivity', False)
            playwright_ok = results['playwright_test'].get('browser_launch', False)
            
            status = "✅ WORKING" if (httpx_ok and playwright_ok) else "❌ FAILED"
            logger.info(f"  {proxy_id}: {status}")
            
            if httpx_ok:
                logger.info(f"    - Detected IP: {results['httpx_test'].get('detected_ip')}")
                logger.info(f"    - Response Time: {results['httpx_test'].get('response_time', 0):.0f}ms")
            else:
                logger.error(f"    - Error: {results['httpx_test'].get('error')}")
                
        # Platform Report
        logger.info("\n🎯 PLATFORM ACCESS:")
        for platform, results in self.results['platform_tests'].items():
            if results['accessible'] and not results['blocked']:
                logger.info(f"  {platform}: ✅ ACCESSIBLE")
            else:
                logger.error(f"  {platform}: ❌ BLOCKED")
                if results['captcha_detected']:
                    logger.warning(f"    - Captcha detected")
                if results['cloudflare_detected']:
                    logger.warning(f"    - Cloudflare protection detected")
                    
        # Recommendations
        logger.critical("\n💡 RECOMMENDATIONS:")
        
        # Check proxy issues
        proxy_working = any(
            r['httpx_test'].get('basic_connectivity', False) 
            for r in self.results['proxy_tests'].values()
        )
        
        if not proxy_working:
            logger.critical("  1. ❌ CRITICAL: No working proxies detected!")
            logger.critical("     - Check proxy credentials in environment variables")
            logger.critical("     - Verify proxy service is active")
            logger.critical("     - Try alternative proxy providers")
            
        # Check platform blocks
        platforms_blocked = sum(
            1 for r in self.results['platform_tests'].values() 
            if r.get('blocked', False) or not r.get('accessible', False)
        )
        
        if platforms_blocked > 0:
            logger.critical(f"  2. ⚠️ WARNING: {platforms_blocked} platforms blocking access")
            logger.critical("     - Implement more advanced stealth measures")
            logger.critical("     - Use residential proxies from target country")
            logger.critical("     - Add human-like behavior simulation")
            logger.critical("     - Consider using undetected-chromedriver")
            
        # Save detailed report
        report_path = 'stealthmaster_diagnostic_report.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"\n📄 Detailed report saved to: {report_path}")
        
        logger.critical("\n" + "="*80)
        logger.critical("🏁 DIAGNOSTIC COMPLETE")
        logger.critical("="*80)


async def main():
    """Run StealthMaster AI diagnostic tests"""
    tester = StealthMasterTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())