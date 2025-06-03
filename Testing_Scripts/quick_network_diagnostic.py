# src/utils/quick_network_diagnostic.py
import asyncio
import aiohttp
import time
import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from src.core.browser_manager import StealthBrowserManager
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickDiagnostic:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'network_tests': {},
            'stealth_tests': {},
            'recommendations': []
        }
    
    async def run_diagnostics(self):
        """Run quick diagnostics"""
        print("=" * 80)
        print("QUICK NETWORK AND STEALTH DIAGNOSTIC")
        print("=" * 80)
        print(f"Started at: {datetime.now()}\n")
        
        # Test 1: Basic network connectivity
        await self.test_network_connectivity()
        
        # Test 2: Proxy connectivity (if configured)
        await self.test_proxy_connectivity()
        
        # Test 3: Quick browser test
        await self.test_browser_basics()
        
        # Test 4: Ticketmaster specific test
        await self.test_ticketmaster_detection()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Save results
        self.save_results()
    
    async def test_network_connectivity(self):
        """Test basic network connectivity"""
        print("🌐 TEST 1: Network Connectivity")
        print("-" * 60)
        
        test_urls = [
            ('Google', 'https://www.google.com'),
            ('Cloudflare DNS', 'https://1.1.1.1'),
            ('Bot.sannysoft', 'https://bot.sannysoft.com'),
            ('Ticketmaster NL', 'https://www.ticketmaster.nl'),
            ('httpbin.org', 'https://httpbin.org/headers')
        ]
        
        async with aiohttp.ClientSession() as session:
            for name, url in test_urls:
                try:
                    start = time.time()
                    async with session.get(url, timeout=10) as response:
                        elapsed = time.time() - start
                        print(f"  ✅ {name}: {response.status} ({elapsed:.2f}s)")
                        self.results['network_tests'][name] = {
                            'status': response.status,
                            'time': elapsed,
                            'success': True
                        }
                except asyncio.TimeoutError:
                    print(f"  ❌ {name}: TIMEOUT")
                    self.results['network_tests'][name] = {'success': False, 'error': 'timeout'}
                except Exception as e:
                    print(f"  ❌ {name}: {type(e).__name__}")
                    self.results['network_tests'][name] = {'success': False, 'error': str(e)}
    
    async def test_proxy_connectivity(self):
        """Test proxy if configured"""
        print("\n🔌 TEST 2: Proxy Connectivity")
        print("-" * 60)
        
        # Load config
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        proxy_config = config.get('proxy', {})
        if not proxy_config.get('enabled'):
            print("  ℹ️  Proxy not enabled in config")
            return
        
        # Check env vars
        username = os.getenv(proxy_config.get('username_env', 'PROXY_USER'))
        password = os.getenv(proxy_config.get('password_env', 'PROXY_PASS'))
        
        if not username or not password:
            print("  ❌ Proxy credentials not found in environment variables")
            print(f"     Expected: {proxy_config.get('username_env', 'PROXY_USER')} and {proxy_config.get('password_env', 'PROXY_PASS')}")
            self.results['recommendations'].append("Set proxy credentials in environment variables")
            return
        
        print("  ✅ Proxy credentials found")
        
        # Test proxy connection
        ports = proxy_config.get('rotating_ports', [])
        if ports:
            port = ports[0]
            template = proxy_config.get('server_template', '')
            try:
                proxy_url = template.format(port=port, user=username, proxy_pass=password)
                print(f"  🔍 Testing proxy on port {port}...")
                
                # Quick test with proxy
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    try:
                        async with session.get(
                            'http://httpbin.org/ip',
                            proxy=proxy_url,
                            timeout=10
                        ) as response:
                            data = await response.json()
                            print(f"  ✅ Proxy working! IP: {data.get('origin', 'Unknown')}")
                    except Exception as e:
                        print(f"  ❌ Proxy test failed: {e}")
                        self.results['recommendations'].append("Check proxy configuration and credentials")
            except Exception as e:
                print(f"  ❌ Failed to format proxy URL: {e}")
    
    async def test_browser_basics(self):
        """Test basic browser functionality"""
        print("\n🌍 TEST 3: Browser Basics")
        print("-" * 60)
        
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        async with async_playwright() as p:
            try:
                # Test without stealth first
                print("  Testing standard browser...")
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Simple navigation test
                await page.goto('https://httpbin.org/headers', timeout=10000)
                headers = await page.text_content('pre')
                print(f"  ✅ Basic browser working")
                
                # Check user agent
                data = json.loads(headers)
                ua = data['headers'].get('User-Agent', '')
                if 'HeadlessChrome' in ua:
                    print(f"  ⚠️  Headless detected in UA: {ua[:50]}...")
                
                await browser.close()
                
            except Exception as e:
                print(f"  ❌ Basic browser test failed: {e}")
                self.results['recommendations'].append("Check Playwright installation")
    
    async def test_ticketmaster_detection(self):
        """Specific Ticketmaster detection test"""
        print("\n🎫 TEST 4: Ticketmaster Detection")
        print("-" * 60)
        
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        async with async_playwright() as p:
            manager = StealthBrowserManager(config, p)
            await manager.start_manager()
            
            try:
                # Test with stealth
                print("  Testing with stealth browser...")
                
                async with manager.get_context() as (context, profile):
                    print(f"  Using profile: {profile.name}")
                    
                    page = await context.new_page()
                    
                    # Add response listener
                    responses = []
                    page.on('response', lambda r: responses.append(r))
                    
                    try:
                        # Navigate with shorter timeout
                        response = await page.goto(
                            'https://www.ticketmaster.nl',
                            wait_until='domcontentloaded',
                            timeout=20000
                        )
                        
                        print(f"  📊 Initial response: {response.status}")
                        
                        # Wait a bit for any redirects
                        await page.wait_for_timeout(3000)
                        
                        # Check current URL
                        current_url = page.url
                        print(f"  📍 Current URL: {current_url}")
                        
                        # Check for queue
                        if 'queue' in current_url:
                            print("  ❌ DETECTED: Sent to queue")
                            self.results['stealth_tests']['ticketmaster_queue'] = True
                        
                        # Check page content
                        try:
                            title = await page.title()
                            print(f"  📄 Page title: {title[:50]}...")
                        except:
                            pass
                        
                        # Check for blocking text
                        blocking_texts = ['Access Denied', 'Pardon Our Interruption', 'queue-it']
                        for text in blocking_texts:
                            try:
                                found = await page.locator(f'text=/{text}/i').count()
                                if found > 0:
                                    print(f"  ❌ Found blocking text: {text}")
                                    self.results['stealth_tests'][f'blocking_text_{text}'] = True
                            except:
                                pass
                        
                        # Analyze responses
                        print(f"\n  📡 Response analysis:")
                        queue_responses = [r for r in responses if 'queue' in r.url]
                        if queue_responses:
                            print(f"  ❌ Queue responses: {len(queue_responses)}")
                            for r in queue_responses[:3]:
                                print(f"     - {r.url[:80]}...")
                        
                        # Check cookies
                        cookies = await context.cookies()
                        akamai_cookies = [c for c in cookies if '_abck' in c['name'] or 'bm_' in c['name']]
                        queue_cookies = [c for c in cookies if 'queue' in c['name'].lower()]
                        
                        print(f"\n  🍪 Cookie analysis:")
                        print(f"     Total cookies: {len(cookies)}")
                        print(f"     Akamai cookies: {len(akamai_cookies)}")
                        print(f"     Queue cookies: {len(queue_cookies)}")
                        
                        if akamai_cookies:
                            print("  ⚠️  Akamai bot protection detected")
                            for cookie in akamai_cookies[:2]:
                                print(f"     - {cookie['name']}: {cookie['value'][:20]}...")
                        
                        # Take screenshot
                        await page.screenshot(path='test_results/ticketmaster_diagnostic.png')
                        print("  📸 Screenshot saved: test_results/ticketmaster_diagnostic.png")
                        
                    except PlaywrightTimeoutError:
                        print("  ❌ Page load timeout")
                        self.results['stealth_tests']['timeout'] = True
                    except Exception as e:
                        print(f"  ❌ Error: {e}")
                        self.results['stealth_tests']['error'] = str(e)
                    
                    await page.close()
                    
            finally:
                await manager.stop_manager()
    
    def generate_recommendations(self):
        """Generate recommendations based on results"""
        print("\n💡 RECOMMENDATIONS")
        print("-" * 60)
        
        # Check network issues
        network_failures = sum(1 for r in self.results['network_tests'].values() if not r.get('success', False))
        if network_failures > 2:
            self.results['recommendations'].append("Network connectivity issues detected - check firewall/VPN")
            print("  ⚠️  Network connectivity issues detected")
        
        # Check if detected by Ticketmaster
        if self.results['stealth_tests'].get('ticketmaster_queue'):
            print("  ❌ Ticketmaster is detecting the bot")
            self.results['recommendations'].extend([
                "Current stealth measures insufficient for Ticketmaster",
                "Consider using residential proxies",
                "Implement more sophisticated browser fingerprinting",
                "Add human-like behavior patterns",
                "Test with different browser profiles"
            ])
        
        # Print all recommendations
        if self.results['recommendations']:
            print("\n  Recommended actions:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✅ No critical issues found")
    
    def save_results(self):
        """Save diagnostic results"""
        os.makedirs('test_results', exist_ok=True)
        
        filename = f"test_results/diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📁 Results saved to: {filename}")

async def main():
    diagnostic = QuickDiagnostic()
    await diagnostic.run_diagnostics()

if __name__ == "__main__":
    asyncio.run(main())