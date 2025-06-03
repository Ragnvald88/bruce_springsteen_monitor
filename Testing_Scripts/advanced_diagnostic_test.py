# src/utils/advanced_diagnostic_test.py
import asyncio
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml
import random
import hashlib

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from src.core.browser_manager import StealthBrowserManager
from src.core.browser_profiles import BrowserProfile

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedStealthTester:
    """Comprehensive testing suite for browser stealth and anti-detection"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'profiles': {},
            'detection_tests': {},
            'target_sites': {},
            'performance_metrics': {}
        }
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("ADVANCED BROWSER STEALTH TESTING SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now()}")
        print()
        
        async with async_playwright() as playwright:
            # Initialize browser manager
            manager = StealthBrowserManager(self.config, playwright)
            await manager.start_manager()
            
            try:
                # Test 1: Profile Loading and Validation
                await self._test_profile_loading(manager)
                
                # Test 2: Basic Stealth Detection
                await self._test_basic_detection(manager)
                
                # Test 3: Advanced Fingerprinting Tests
                await self._test_advanced_fingerprinting(manager)
                
                # Test 4: Target Site Access
                await self._test_target_sites(manager)
                
                # Test 5: Performance and Timing
                await self._test_performance_metrics(manager)
                
                # Test 6: Persistent Context Testing
                await self._test_persistent_contexts(manager)
                
                # Test 7: Multi-Profile Rotation
                await self._test_profile_rotation(manager)
                
                # Generate report
                self._generate_report()
                
            finally:
                await manager.stop_manager()
    
    async def _test_profile_loading(self, manager: StealthBrowserManager):
        """Test profile loading and validation"""
        print("\n🔍 TEST 1: Profile Loading and Validation")
        print("-" * 60)
        
        for profile in manager.profiles:
            print(f"\n📋 Testing profile: {profile.name}")
            
            # Check critical fields
            critical_fields = {
                'user_agent': profile.user_agent,
                'viewport': f"{profile.viewport_width}x{profile.viewport_height}",
                'screen': f"{profile.screen_width}x{profile.screen_height}",
                'timezone': profile.timezone,
                'locale': profile.locale,
                'webgl_vendor': profile.webgl_vendor,
                'webgl_renderer': profile.webgl_renderer
            }
            
            missing_fields = []
            for field, value in critical_fields.items():
                if not value or value == "None":
                    missing_fields.append(field)
                else:
                    print(f"  ✓ {field}: {value}")
            
            if missing_fields:
                print(f"  ❌ Missing fields: {', '.join(missing_fields)}")
            
            # Test extra_js_props
            extra_props = profile.extra_js_props
            print(f"  📊 Extra JS props: {len(extra_props)} properties defined")
            
            # Check WebGL extensions
            webgl_extensions = extra_props.get('webgl_extensions', [])
            print(f"  🎨 WebGL extensions: {len(webgl_extensions)} extensions")
            
            # Check fonts
            fonts = extra_props.get('system_fonts', [])
            print(f"  🔤 System fonts: {len(fonts)} fonts")
            
            self.test_results['profiles'][profile.name] = {
                'critical_fields': critical_fields,
                'missing_fields': missing_fields,
                'extra_props_count': len(extra_props),
                'webgl_extensions_count': len(webgl_extensions),
                'fonts_count': len(fonts)
            }
    
    async def _test_basic_detection(self, manager: StealthBrowserManager):
        """Test against basic bot detection"""
        print("\n🤖 TEST 2: Basic Bot Detection")
        print("-" * 60)
        
        detection_sites = [
            {
                'name': 'Bot.sannysoft.com',
                'url': 'https://bot.sannysoft.com/',
                'check_selectors': {
                    'passed': '.passed',
                    'failed': '.failed',
                    'warning': '.warn'
                }
            },
            {
                'name': 'AmIUnique',
                'url': 'https://amiunique.org/fingerprint',
                'wait_time': 10000
            }
        ]
        
        for site in detection_sites:
            print(f"\n🌐 Testing on {site['name']}...")
            
            try:
                async with manager.get_context() as (context, profile):
                    page = await context.new_page()
                    
                    # Navigate to detection site
                    await page.goto(site['url'], wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(site.get('wait_time', 5000))
                    
                    # Take screenshot
                    screenshot_path = f"test_results/{site['name'].replace('.', '_')}_{profile.name}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"  📸 Screenshot saved: {screenshot_path}")
                    
                    # Check for detection indicators
                    if 'check_selectors' in site:
                        results = {}
                        for check_type, selector in site['check_selectors'].items():
                            count = await page.locator(selector).count()
                            results[check_type] = count
                            
                        print(f"  ✅ Passed: {results.get('passed', 0)}")
                        print(f"  ❌ Failed: {results.get('failed', 0)}")
                        print(f"  ⚠️  Warning: {results.get('warning', 0)}")
                        
                        self.test_results['detection_tests'][f"{site['name']}_{profile.name}"] = results
                    
                    # Extract detection details
                    detection_data = await page.evaluate("""
                        () => {
                            return {
                                webdriver: navigator.webdriver,
                                chrome: !!window.chrome,
                                chrome_runtime: !!(window.chrome && window.chrome.runtime),
                                permissions_query: typeof navigator.permissions?.query,
                                languages: navigator.languages,
                                plugins_length: navigator.plugins.length,
                                user_agent: navigator.userAgent,
                                platform: navigator.platform,
                                vendor: navigator.vendor,
                                webgl_vendor: (() => {
                                    try {
                                        const canvas = document.createElement('canvas');
                                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                                        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                                        return debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A';
                                    } catch (e) {
                                        return 'Error';
                                    }
                                })(),
                                webgl_renderer: (() => {
                                    try {
                                        const canvas = document.createElement('canvas');
                                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                                        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                                        return debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A';
                                    } catch (e) {
                                        return 'Error';
                                    }
                                })()
                            };
                        }
                    """)
                    
                    print(f"  🔍 Detection data:")
                    for key, value in detection_data.items():
                        print(f"    {key}: {value}")
                    
                    await page.close()
                    
            except Exception as e:
                print(f"  ❌ Error testing {site['name']}: {e}")
                logger.error(f"Detection test failed: {e}", exc_info=True)
    
    async def _test_advanced_fingerprinting(self, manager: StealthBrowserManager):
        """Test advanced fingerprinting detection"""
        print("\n🔬 TEST 3: Advanced Fingerprinting Tests")
        print("-" * 60)
        
        tests = [
            {
                'name': 'CreepJS',
                'url': 'https://abrahamjuliot.github.io/creepjs/',
                'wait_selector': '.visitor-rating',
                'wait_time': 15000
            },
            {
                'name': 'FingerprintJS',
                'url': 'https://fingerprintjs.github.io/fingerprintjs/',
                'wait_time': 5000
            },
            {
                'name': 'BotD',
                'url': 'https://fingerprintjs.github.io/BotD/',
                'wait_time': 5000
            }
        ]
        
        for test in tests:
            print(f"\n🧪 Testing {test['name']}...")
            
            try:
                async with manager.get_context() as (context, profile):
                    page = await context.new_page()
                    
                    await page.goto(test['url'], wait_until='networkidle', timeout=60000)
                    
                    if 'wait_selector' in test:
                        await page.wait_for_selector(test['wait_selector'], timeout=test['wait_time'])
                    else:
                        await page.wait_for_timeout(test['wait_time'])
                    
                    # CreepJS specific checks
                    if test['name'] == 'CreepJS':
                        try:
                            trust_score = await page.text_content('.visitor-rating')
                            lies_element = await page.query_selector('.lies-total')
                            lies = await lies_element.inner_text() if lies_element else 'N/A'
                            
                            print(f"  🎯 Trust Score: {trust_score}")
                            print(f"  🚨 Lies Detected: {lies}")
                            
                            # Get detailed lie information
                            lie_details = await page.evaluate("""
                                () => {
                                    const lies = [];
                                    document.querySelectorAll('.lietext').forEach(el => {
                                        lies.push(el.textContent);
                                    });
                                    return lies;
                                }
                            """)
                            
                            if lie_details:
                                print("  📋 Lie details:")
                                for lie in lie_details[:5]:  # Show first 5
                                    print(f"    - {lie}")
                                    
                        except Exception as e:
                            print(f"  ⚠️  Could not extract CreepJS scores: {e}")
                    
                    # BotD specific checks
                    elif test['name'] == 'BotD':
                        try:
                            bot_result = await page.evaluate("""
                                () => {
                                    // Look for bot probability in the page
                                    const elements = document.querySelectorAll('*');
                                    for (let el of elements) {
                                        if (el.textContent.includes('bot probability')) {
                                            return el.textContent;
                                        }
                                    }
                                    return 'Not found';
                                }
                            """)
                            print(f"  🤖 Bot Detection Result: {bot_result}")
                        except Exception as e:
                            print(f"  ⚠️  Could not extract BotD result: {e}")
                    
                    # Take screenshot
                    screenshot_path = f"test_results/{test['name']}_{profile.name}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"  📸 Screenshot saved: {screenshot_path}")
                    
                    await page.close()
                    
            except Exception as e:
                print(f"  ❌ Error testing {test['name']}: {e}")
                logger.error(f"Fingerprinting test failed: {e}", exc_info=True)
    
    async def _test_target_sites(self, manager: StealthBrowserManager):
        """Test access to target sites"""
        print("\n🎯 TEST 4: Target Site Access")
        print("-" * 60)
        
        target_sites = [
            {
                'name': 'Ticketmaster.nl',
                'url': 'https://www.ticketmaster.nl',
                'check_for': ['Access Denied', 'Pardon Our Interruption', 'queue'],
                'search_test': True,
                'search_term': 'Bruce Springsteen'
            },
            {
                'name': 'FanSale.nl',
                'url': 'https://www.fansale.nl',
                'check_for': ['Access Denied', 'blocked'],
                'search_test': False
            }
        ]
        
        for site in target_sites:
            print(f"\n🌍 Testing {site['name']}...")
            
            try:
                async with manager.get_context() as (context, profile):
                    page = await context.new_page()
                    
                    # Navigate to site
                    start_time = time.time()
                    response = await page.goto(site['url'], wait_until='domcontentloaded', timeout=30000)
                    load_time = time.time() - start_time
                    
                    print(f"  📊 Status: {response.status}")
                    print(f"  ⏱️  Load time: {load_time:.2f}s")
                    
                    await page.wait_for_timeout(5000)
                    
                    # Check for blocks
                    page_content = await page.content()
                    blocks_found = []
                    for block_text in site['check_for']:
                        if block_text.lower() in page_content.lower():
                            blocks_found.append(block_text)
                    
                    if blocks_found:
                        print(f"  ❌ BLOCKED! Found: {', '.join(blocks_found)}")
                    else:
                        print(f"  ✅ Access granted!")
                    
                    # Check page title
                    title = await page.title()
                    print(f"  📄 Page title: {title[:50]}...")
                    
                    # Check for Akamai
                    cookies = await context.cookies()
                    akamai_cookies = [c for c in cookies if '_abck' in c['name'] or 'bm_' in c['name']]
                    
                    if akamai_cookies:
                        print(f"  🛡️  Akamai detected: {len(akamai_cookies)} cookies")
                        for cookie in akamai_cookies[:2]:
                            print(f"    - {cookie['name']}: {cookie['value'][:20]}...")
                    else:
                        print(f"  ℹ️  No Akamai cookies detected")
                    
                    # Search test
                    if site['search_test'] and not blocks_found:
                        print(f"  🔍 Attempting search for '{site['search_term']}'...")
                        
                        search_selectors = [
                            'input[type="search"]',
                            'input[placeholder*="Search"]',
                            'input[placeholder*="Zoek"]',
                            'input[name="search"]',
                            'input[name="q"]',
                            '#search-input',
                            '.search-input'
                        ]
                        
                        search_found = False
                        for selector in search_selectors:
                            try:
                                search_box = await page.wait_for_selector(selector, timeout=3000)
                                if search_box:
                                    await search_box.click()
                                    await search_box.type(site['search_term'], delay=100)
                                    await page.keyboard.press('Enter')
                                    await page.wait_for_timeout(3000)
                                    
                                    # Check if results loaded
                                    new_url = page.url
                                    if new_url != site['url']:
                                        print(f"    ✅ Search successful! New URL: {new_url[:50]}...")
                                        search_found = True
                                    break
                            except:
                                continue
                        
                        if not search_found:
                            print(f"    ⚠️  Could not find search box")
                    
                    # Take screenshot
                    screenshot_path = f"test_results/{site['name'].replace('.', '_')}_{profile.name}.png"
                    await page.screenshot(path=screenshot_path, full_page=False)
                    print(f"  📸 Screenshot saved: {screenshot_path}")
                    
                    # Store results
                    self.test_results['target_sites'][f"{site['name']}_{profile.name}"] = {
                        'status': response.status,
                        'load_time': load_time,
                        'blocked': len(blocks_found) > 0,
                        'blocks_found': blocks_found,
                        'title': title,
                        'akamai_cookies': len(akamai_cookies)
                    }
                    
                    await page.close()
                    
            except PlaywrightError as e:
                print(f"  ❌ Playwright error: {e}")
                self.test_results['target_sites'][f"{site['name']}_{profile.name}"] = {
                    'error': str(e),
                    'blocked': True
                }
            except Exception as e:
                print(f"  ❌ Error testing {site['name']}: {e}")
                logger.error(f"Target site test failed: {e}", exc_info=True)
    
    async def _test_performance_metrics(self, manager: StealthBrowserManager):
        """Test performance and resource usage"""
        print("\n⚡ TEST 5: Performance Metrics")
        print("-" * 60)
        
        # Get manager metrics
        metrics = manager.get_performance_metrics()
        
        print(f"\n📊 Browser Pool Metrics:")
        print(f"  Pool size: {metrics['pool_size']}/{metrics['target_pool_size']}")
        print(f"  Total contexts opened: {metrics['overall']['total_contexts']}")
        print(f"  Total errors: {metrics['overall']['total_errors']}")
        print(f"  Total detections: {metrics['overall']['total_detections']}")
        print(f"  Average health score: {metrics['overall']['avg_health_score']:.1f}")
        print(f"  Average response time: {metrics['overall']['avg_response_time_ms']:.0f}ms")
        
        print(f"\n🖥️  Instance Details:")
        for instance in metrics['instances']:
            print(f"  Instance {instance['id'][:8]}...:")
            print(f"    Profile: {instance['profile']}")
            print(f"    Health: {instance['health_score']:.1f}")
            print(f"    Age: {instance['age_seconds']:.0f}s")
            print(f"    Errors: {instance['errors']}")
            print(f"    Detections: {instance['detections']}")
        
        self.test_results['performance_metrics'] = metrics
    
    async def _test_persistent_contexts(self, manager: StealthBrowserManager):
        """Test persistent browser contexts"""
        print("\n💾 TEST 6: Persistent Context Testing")
        print("-" * 60)
        
        # Only test if persistent contexts are configured
        if not manager.config.get('browser_launch_options', {}).get('use_persistent_user_data_dir_if_available'):
            print("  ℹ️  Persistent contexts not configured, skipping test")
            return
        
        print("  🔧 Testing persistent context creation...")
        
        try:
            profile = manager.profiles[0]  # Use first profile
            context = await manager.get_persistent_context_for_profile(profile)
            
            print(f"  ✅ Created persistent context for profile: {profile.name}")
            
            # Test navigation
            page = await context.new_page()
            await page.goto('https://www.google.com', wait_until='domcontentloaded')
            
            # Set a cookie to test persistence
            await context.add_cookies([{
                'name': 'test_persistence',
                'value': f'test_{int(time.time())}',
                'domain': '.google.com',
                'path': '/'
            }])
            
            print("  🍪 Set test cookie")
            
            await page.close()
            
            # Get the same context again
            context2 = await manager.get_persistent_context_for_profile(profile)
            
            # Check if cookie persists
            cookies = await context2.cookies()
            test_cookie = next((c for c in cookies if c['name'] == 'test_persistence'), None)
            
            if test_cookie:
                print(f"  ✅ Cookie persisted: {test_cookie['value']}")
            else:
                print("  ❌ Cookie did not persist")
                
        except Exception as e:
            print(f"  ❌ Persistent context test failed: {e}")
            logger.error(f"Persistent context test error: {e}", exc_info=True)
    
    async def _test_profile_rotation(self, manager: StealthBrowserManager):
        """Test multiple profile rotation"""
        print("\n🔄 TEST 7: Multi-Profile Rotation")
        print("-" * 60)
        
        if len(manager.profiles) < 2:
            print("  ℹ️  Less than 2 profiles available, skipping rotation test")
            return
        
        print(f"  Testing rotation across {len(manager.profiles)} profiles...")
        
        rotation_results = []
        
        # Test each profile
        for i in range(min(5, len(manager.profiles) * 2)):  # Test up to 5 rotations
            try:
                async with manager.get_context() as (context, profile):
                    page = await context.new_page()
                    
                    # Quick test
                    await page.goto('https://httpbin.org/headers', wait_until='networkidle')
                    
                    # Get headers
                    headers_text = await page.text_content('pre')
                    headers = json.loads(headers_text)
                    
                    user_agent = headers['headers'].get('User-Agent', 'N/A')
                    
                    rotation_results.append({
                        'iteration': i + 1,
                        'profile': profile.name,
                        'user_agent_match': user_agent == profile.user_agent
                    })
                    
                    print(f"    Iteration {i + 1}: Profile '{profile.name}' - UA match: {user_agent == profile.user_agent}")
                    
                    await page.close()
                    
            except Exception as e:
                print(f"    ❌ Rotation {i + 1} failed: {e}")
        
        # Check rotation diversity
        profiles_used = set(r['profile'] for r in rotation_results)
        print(f"\n  📊 Rotation Summary:")
        print(f"    Total rotations: {len(rotation_results)}")
        print(f"    Unique profiles used: {len(profiles_used)}")
        print(f"    Profiles: {', '.join(profiles_used)}")
    
    def _generate_report(self):
        """Generate and save test report"""
        print("\n📄 GENERATING TEST REPORT")
        print("=" * 80)
        
        # Create test_results directory if it doesn't exist
        os.makedirs('test_results', exist_ok=True)
        
        # Save detailed JSON report
        report_path = f"test_results/stealth_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📁 Detailed report saved to: {report_path}")
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("-" * 60)
        
        # Profile summary
        print(f"\n🔍 Profiles tested: {len(self.test_results['profiles'])}")
        for profile_name, data in self.test_results['profiles'].items():
            missing = len(data['missing_fields'])
            status = "✅" if missing == 0 else "⚠️"
            print(f"  {status} {profile_name}: {missing} missing fields")
        
        # Detection summary
        if self.test_results['detection_tests']:
            print(f"\n🤖 Detection tests performed: {len(self.test_results['detection_tests'])}")
            for test_name, results in self.test_results['detection_tests'].items():
                if isinstance(results, dict) and 'failed' in results:
                    status = "✅" if results.get('failed', 0) == 0 else "❌"
                    print(f"  {status} {test_name}: {results.get('failed', 0)} failures")
        
        # Target sites summary
        if self.test_results['target_sites']:
            print(f"\n🎯 Target sites tested: {len(self.test_results['target_sites'])}")
            for site_test, data in self.test_results['target_sites'].items():
                if isinstance(data, dict):
                    if data.get('blocked'):
                        print(f"  ❌ {site_test}: BLOCKED")
                    elif 'error' in data:
                        print(f"  ❌ {site_test}: ERROR - {data['error'][:50]}...")
                    else:
                        print(f"  ✅ {site_test}: SUCCESS (Status: {data.get('status', 'N/A')})")
        
        print("\n" + "=" * 80)
        print("Testing completed!")


async def main():
    """Main test runner"""
    # Check if custom config path is provided
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    
    # Create test results directory
    os.makedirs('test_results', exist_ok=True)
    
    # Run tests
    tester = AdvancedStealthTester(config_path)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())