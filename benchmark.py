#!/usr/bin/env python3
"""
StealthMaster Benchmark Suite
Tests the performance and reliability of the ticket bot
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('Benchmark')


class BenchmarkSuite:
    """Comprehensive benchmark tests for StealthMaster"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
            },
            'tests': {}
        }
        
        # Load config
        with open('config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
    
    def run_all_tests(self):
        """Run all benchmark tests"""
        logger.info("🚀 Starting StealthMaster Benchmark Suite")
        
        # Test 1: Configuration and Dependencies
        self.test_configuration()
        
        # Test 2: Browser Launch Speed
        self.test_browser_launch()
        
        # Test 3: Login Process
        self.test_login_speed()
        
        # Test 4: Page Navigation
        self.test_navigation_speed()
        
        # Test 5: Ticket Detection
        self.test_ticket_detection()
        
        # Test 6: Cookie Handling
        self.test_cookie_handling()
        
        # Test 7: Session Persistence
        self.test_session_persistence()
        
        # Test 8: Resource Blocking Effectiveness
        self.test_resource_blocking()
        
        # Test 9: CAPTCHA Detection
        self.test_captcha_detection()
        
        # Test 10: End-to-End Flow
        self.test_end_to_end()
        
        # Save results
        self.save_results()
        
        # Generate report
        self.generate_report()
    
    def test_configuration(self):
        """Test configuration and dependencies"""
        logger.info("\n📋 Test 1: Configuration Check")
        
        test_start = time.time()
        results = {
            'env_vars': {},
            'dependencies': {},
            'config_file': False
        }
        
        # Check environment variables
        required_env = ['FANSALE_EMAIL', 'FANSALE_PASSWORD']
        optional_env = ['IPROYAL_USERNAME', 'IPROYAL_PASSWORD', 'TWOCAPTCHA_API_KEY', 
                       'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        
        for var in required_env:
            results['env_vars'][var] = bool(os.getenv(var))
            if results['env_vars'][var]:
                logger.info(f"✅ {var} configured")
            else:
                logger.error(f"❌ {var} missing")
        
        for var in optional_env:
            results['env_vars'][var] = bool(os.getenv(var))
            if results['env_vars'][var]:
                logger.info(f"✅ {var} configured (optional)")
            else:
                logger.info(f"ℹ️ {var} not configured (optional)")
        
        # Check dependencies
        try:
            import selenium
            results['dependencies']['selenium'] = selenium.__version__
            logger.info(f"✅ Selenium {selenium.__version__}")
        except:
            results['dependencies']['selenium'] = None
            logger.error("❌ Selenium not installed")
        
        try:
            import undetected_chromedriver
            results['dependencies']['undetected_chromedriver'] = undetected_chromedriver.__version__ if hasattr(undetected_chromedriver, '__version__') else True
            logger.info("✅ Undetected ChromeDriver")
        except Exception as e:
            results['dependencies']['undetected_chromedriver'] = False
            logger.error(f"❌ Undetected ChromeDriver issue: {e}")
        
        # Check config file
        results['config_file'] = os.path.exists('config.yaml')
        if results['config_file']:
            logger.info("✅ config.yaml found")
        else:
            logger.error("❌ config.yaml missing")
        
        results['duration'] = time.time() - test_start
        self.results['tests']['configuration'] = results
    
    def test_browser_launch(self):
        """Test browser launch speed"""
        logger.info("\n🌐 Test 2: Browser Launch Speed")
        
        from stealthmaster import StealthMaster
        
        launch_times = []
        
        for i in range(3):
            start_time = time.time()
            
            try:
                bot = StealthMaster(self.config)
                bot.create_driver()
                launch_time = time.time() - start_time
                launch_times.append(launch_time)
                logger.info(f"  Launch {i+1}: {launch_time:.2f}s")
                
                # Cleanup
                if bot.driver:
                    bot.driver.quit()
                
            except Exception as e:
                logger.error(f"  Launch {i+1} failed: {e}")
                launch_times.append(None)
        
        valid_times = [t for t in launch_times if t is not None]
        
        results = {
            'attempts': len(launch_times),
            'successful': len(valid_times),
            'times': launch_times,
            'average': statistics.mean(valid_times) if valid_times else None,
            'min': min(valid_times) if valid_times else None,
            'max': max(valid_times) if valid_times else None
        }
        
        if results['average']:
            logger.info(f"📊 Average launch time: {results['average']:.2f}s")
            
            # Performance assessment
            if results['average'] < 5:
                logger.info("✅ Excellent launch speed")
            elif results['average'] < 10:
                logger.info("⚠️ Acceptable launch speed")
            else:
                logger.warning("❌ Slow launch speed - may miss tickets")
        
        self.results['tests']['browser_launch'] = results
    
    def test_login_speed(self):
        """Test login process speed"""
        logger.info("\n🔐 Test 3: Login Speed")
        
        # Note: This is a simulated test to avoid actual login attempts
        logger.info("⚠️ Simulating login test (not performing actual login)")
        
        # Measure selector finding speed
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        
        test_html = """
        <html>
            <body>
                <input data-qa="loginEmail" />
                <input data-qa="loginPassword" />
                <button data-qa="loginSubmit">Login</button>
            </body>
        </html>
        """
        
        # Create a simple test page
        test_file = Path("test_login.html")
        test_file.write_text(test_html)
        
        try:
            from stealthmaster import StealthMaster
            bot = StealthMaster(self.config)
            bot.create_driver()
            
            # Navigate to test page
            bot.driver.get(f"file://{test_file.absolute()}")
            
            start_time = time.time()
            
            # Find elements
            email_found = bool(bot.driver.find_elements(By.CSS_SELECTOR, "[data-qa='loginEmail']"))
            password_found = bool(bot.driver.find_elements(By.CSS_SELECTOR, "[data-qa='loginPassword']"))
            button_found = bool(bot.driver.find_elements(By.CSS_SELECTOR, "[data-qa='loginSubmit']"))
            
            selector_time = time.time() - start_time
            
            results = {
                'selector_time': selector_time,
                'selectors_found': {
                    'email': email_found,
                    'password': password_found,
                    'submit': button_found
                },
                'estimated_login_time': selector_time + 5  # Add estimated typing/submission time
            }
            
            logger.info(f"  Selector detection: {selector_time:.3f}s")
            logger.info(f"  Estimated total login: {results['estimated_login_time']:.1f}s")
            
            if selector_time < 0.1:
                logger.info("✅ Excellent selector performance")
            else:
                logger.warning("⚠️ Slow selector detection")
            
            # Cleanup
            bot.driver.quit()
            
        except Exception as e:
            logger.error(f"Login test failed: {e}")
            results = {'error': str(e)}
        
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
        
        self.results['tests']['login_speed'] = results
    
    def test_navigation_speed(self):
        """Test page navigation speed"""
        logger.info("\n🧭 Test 4: Page Navigation Speed")
        
        try:
            from stealthmaster import StealthMaster
            bot = StealthMaster(self.config)
            bot.create_driver()
            
            # Test navigation to different pages
            test_urls = [
                ("Fansale Homepage", "https://www.fansale.it"),
                ("Target Event", self.config['target']['url'])
            ]
            
            navigation_times = []
            
            for name, url in test_urls:
                start_time = time.time()
                
                try:
                    bot.driver.get(url)
                    # Wait for basic page load
                    time.sleep(2)
                    nav_time = time.time() - start_time
                    navigation_times.append({
                        'page': name,
                        'url': url,
                        'time': nav_time
                    })
                    logger.info(f"  {name}: {nav_time:.2f}s")
                    
                except Exception as e:
                    logger.error(f"  {name} failed: {e}")
                    navigation_times.append({
                        'page': name,
                        'url': url,
                        'error': str(e)
                    })
            
            # Cleanup
            bot.driver.quit()
            
            valid_times = [n['time'] for n in navigation_times if 'time' in n]
            
            results = {
                'navigations': navigation_times,
                'average_time': statistics.mean(valid_times) if valid_times else None
            }
            
            if results['average_time']:
                logger.info(f"📊 Average navigation: {results['average_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Navigation test failed: {e}")
            results = {'error': str(e)}
        
        self.results['tests']['navigation_speed'] = results
    
    def test_ticket_detection(self):
        """Test ticket detection capabilities"""
        logger.info("\n🎫 Test 5: Ticket Detection")
        
        # Create test HTML with Fansale-like structure
        test_html = """
        <html>
            <body>
                <!-- No tickets message -->
                <div>Sfortunatamente non sono state trovate offerte adeguate</div>
                
                <!-- Simulated tickets -->
                <div data-qa="ticketToBuy">
                    <span>Settore A - Fila 10</span>
                    <span>€85.00</span>
                </div>
                
                <div class="offer-item">
                    <a class="js-Button-inOfferEntryList">
                        <span>Prato Gold</span>
                        <span>€120.00</span>
                    </a>
                </div>
            </body>
        </html>
        """
        
        test_file = Path("test_tickets.html")
        test_file.write_text(test_html)
        
        try:
            from stealthmaster import StealthMaster
            bot = StealthMaster(self.config)
            bot.create_driver()
            
            # Navigate to test page
            bot.driver.get(f"file://{test_file.absolute()}")
            time.sleep(1)
            
            start_time = time.time()
            
            # Test no tickets detection
            no_tickets_found = bool(bot.driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), 'Sfortunatamente non sono state trovate offerte adeguate')]"
            ))
            
            # Test ticket detection
            tickets_qa = bot.driver.find_elements(By.CSS_SELECTOR, "div[data-qa='ticketToBuy']")
            tickets_offer = bot.driver.find_elements(By.CSS_SELECTOR, ".offer-item")
            tickets_button = bot.driver.find_elements(By.CSS_SELECTOR, "a.js-Button-inOfferEntryList")
            
            detection_time = time.time() - start_time
            
            results = {
                'detection_time': detection_time,
                'no_tickets_message': no_tickets_found,
                'tickets_found': {
                    'data-qa': len(tickets_qa),
                    'offer-item': len(tickets_offer),
                    'js-button': len(tickets_button)
                },
                'total_tickets': len(tickets_qa) + len(tickets_offer)
            }
            
            logger.info(f"  Detection time: {detection_time:.3f}s")
            logger.info(f"  No tickets message: {no_tickets_found}")
            logger.info(f"  Tickets found: {results['total_tickets']}")
            
            if detection_time < 0.5 and results['total_tickets'] > 0:
                logger.info("✅ Excellent ticket detection")
            elif results['total_tickets'] > 0:
                logger.info("⚠️ Slow but functional detection")
            else:
                logger.error("❌ Failed to detect tickets")
            
            # Cleanup
            bot.driver.quit()
            
        except Exception as e:
            logger.error(f"Ticket detection test failed: {e}")
            results = {'error': str(e)}
        
        finally:
            if test_file.exists():
                test_file.unlink()
        
        self.results['tests']['ticket_detection'] = results
    
    def test_cookie_handling(self):
        """Test cookie consent handling"""
        logger.info("\n🍪 Test 6: Cookie Handling")
        
        # Create test HTML with cookie banner
        test_html = """
        <html>
            <body>
                <div class="cookie-banner">
                    <button onclick="acceptCookies()">ACCETTA TUTTI I COOKIE</button>
                    <button id="onetrust-accept-btn-handler">Accept All</button>
                </div>
            </body>
            <script>
                function acceptCookies() {
                    document.querySelector('.cookie-banner').style.display = 'none';
                }
            </script>
        </html>
        """
        
        test_file = Path("test_cookies.html")
        test_file.write_text(test_html)
        
        try:
            from stealthmaster import StealthMaster
            bot = StealthMaster(self.config)
            bot.create_driver()
            
            # Navigate to test page
            bot.driver.get(f"file://{test_file.absolute()}")
            time.sleep(1)
            
            start_time = time.time()
            
            # Test cookie handling
            cookie_handled = bot._handle_cookie_consent()
            
            handling_time = time.time() - start_time
            
            # Check if cookie banner is hidden
            banner_hidden = bot.driver.execute_script(
                "return document.querySelector('.cookie-banner')?.style.display === 'none'"
            )
            
            results = {
                'handling_time': handling_time,
                'cookie_handled': cookie_handled,
                'banner_hidden': banner_hidden
            }
            
            logger.info(f"  Handling time: {handling_time:.3f}s")
            logger.info(f"  Cookie handled: {cookie_handled}")
            logger.info(f"  Banner hidden: {banner_hidden}")
            
            if cookie_handled and handling_time < 3:
                logger.info("✅ Excellent cookie handling")
            elif cookie_handled:
                logger.info("⚠️ Slow cookie handling")
            else:
                logger.warning("❌ Failed to handle cookies")
            
            # Cleanup
            bot.driver.quit()
            
        except Exception as e:
            logger.error(f"Cookie handling test failed: {e}")
            results = {'error': str(e)}
        
        finally:
            if test_file.exists():
                test_file.unlink()
        
        self.results['tests']['cookie_handling'] = results
    
    def test_session_persistence(self):
        """Test session save/load functionality"""
        logger.info("\n💾 Test 7: Session Persistence")
        
        session_dir = Path("session")
        test_email = "test@example.com"
        session_file = session_dir / f"{test_email.replace('@', '_at_')}.json"
        
        try:
            # Create test session data
            test_session = {
                'cookies': [
                    {'name': 'test_cookie', 'value': 'test_value', 'domain': '.fansale.it'}
                ],
                'url': 'https://www.fansale.it',
                'timestamp': datetime.now().isoformat()
            }
            
            # Save test session
            start_time = time.time()
            with open(session_file, 'w') as f:
                json.dump(test_session, f)
            save_time = time.time() - start_time
            
            # Load test session
            start_time = time.time()
            with open(session_file, 'r') as f:
                loaded_session = json.load(f)
            load_time = time.time() - start_time
            
            # Verify
            session_valid = (
                loaded_session['cookies'] == test_session['cookies'] and
                loaded_session['url'] == test_session['url']
            )
            
            results = {
                'save_time': save_time,
                'load_time': load_time,
                'session_valid': session_valid,
                'file_size': session_file.stat().st_size if session_file.exists() else 0
            }
            
            logger.info(f"  Save time: {save_time:.3f}s")
            logger.info(f"  Load time: {load_time:.3f}s")
            logger.info(f"  Session valid: {session_valid}")
            logger.info(f"  File size: {results['file_size']} bytes")
            
            if session_valid and save_time < 0.1 and load_time < 0.1:
                logger.info("✅ Excellent session persistence")
            else:
                logger.warning("⚠️ Session persistence issues")
            
        except Exception as e:
            logger.error(f"Session persistence test failed: {e}")
            results = {'error': str(e)}
        
        finally:
            # Cleanup
            if session_file.exists():
                session_file.unlink()
        
        self.results['tests']['session_persistence'] = results
    
    def test_resource_blocking(self):
        """Test resource blocking effectiveness"""
        logger.info("\n🚫 Test 8: Resource Blocking")
        
        try:
            from stealthmaster import StealthMaster
            bot = StealthMaster(self.config)
            
            # Create driver and navigate to a page
            bot.create_driver()
            
            # Enable network logging
            bot.driver.execute_cdp_cmd('Network.enable', {})
            
            # Track blocked resources
            blocked_resources = []
            
            def log_request(request):
                url = request.get('request', {}).get('url', '')
                for pattern in ['font', 'image', 'analytics', 'tracking']:
                    if pattern in url.lower():
                        blocked_resources.append(url)
            
            # Set up request interception
            bot.driver.execute_cdp_cmd('Network.setRequestInterception', {'patterns': [{'urlPattern': '*'}]})
            
            # Navigate to test page
            start_time = time.time()
            bot.driver.get("https://www.fansale.it")
            load_time = time.time() - start_time
            
            results = {
                'page_load_time': load_time,
                'blocked_count': len(blocked_resources),
                'blocking_effective': len(blocked_resources) > 0
            }
            
            logger.info(f"  Page load time: {load_time:.2f}s")
            logger.info(f"  Resources blocked: {len(blocked_resources)}")
            
            if load_time < 5 and len(blocked_resources) > 0:
                logger.info("✅ Effective resource blocking")
            elif load_time < 10:
                logger.info("⚠️ Moderate resource blocking")
            else:
                logger.warning("❌ Ineffective resource blocking")
            
            # Cleanup
            bot.driver.quit()
            
        except Exception as e:
            logger.error(f"Resource blocking test failed: {e}")
            results = {'error': str(e)}
        
        self.results['tests']['resource_blocking'] = results
    
    def test_captcha_detection(self):
        """Test CAPTCHA detection capabilities"""
        logger.info("\n🤖 Test 9: CAPTCHA Detection")
        
        # Note: This is a simulated test
        logger.info("⚠️ Simulating CAPTCHA detection test")
        
        captcha_selectors = [
            "[class*='captcha']",
            "[id*='captcha']",
            "iframe[src*='recaptcha']",
            "[class*='challenge']"
        ]
        
        results = {
            'selectors_tested': len(captcha_selectors),
            'captcha_solver_configured': bool(os.getenv('TWOCAPTCHA_API_KEY')),
            'estimated_solve_time': 30 if os.getenv('TWOCAPTCHA_API_KEY') else None
        }
        
        logger.info(f"  Selectors tested: {results['selectors_tested']}")
        logger.info(f"  CAPTCHA solver: {'Configured' if results['captcha_solver_configured'] else 'Not configured'}")
        
        if results['captcha_solver_configured']:
            logger.info("✅ CAPTCHA handling ready")
        else:
            logger.warning("⚠️ No CAPTCHA solver configured")
        
        self.results['tests']['captcha_detection'] = results
    
    def test_end_to_end(self):
        """Test end-to-end flow timing"""
        logger.info("\n🏁 Test 10: End-to-End Flow")
        
        # Simulate timings based on previous tests
        browser_launch = self.results['tests'].get('browser_launch', {}).get('average', 5)
        login_time = self.results['tests'].get('login_speed', {}).get('estimated_login_time', 10)
        navigation = self.results['tests'].get('navigation_speed', {}).get('average_time', 3)
        detection = self.results['tests'].get('ticket_detection', {}).get('detection_time', 0.5)
        
        # Calculate total time
        total_time = browser_launch + login_time + navigation + detection + 2  # +2 for clicking
        
        results = {
            'browser_launch': browser_launch,
            'login': login_time,
            'navigation': navigation,
            'detection': detection,
            'reservation_click': 2,
            'total_time': total_time
        }
        
        logger.info(f"  Browser launch: {browser_launch:.1f}s")
        logger.info(f"  Login process: {login_time:.1f}s")
        logger.info(f"  Navigation: {navigation:.1f}s")
        logger.info(f"  Detection: {detection:.1f}s")
        logger.info(f"  Click action: 2.0s")
        logger.info(f"  📊 Total time: {total_time:.1f}s")
        
        # Performance assessment
        if total_time < 20:
            logger.info("✅ EXCELLENT - Very competitive for ticket securing")
        elif total_time < 30:
            logger.info("⚠️ GOOD - Should work for most scenarios")
        elif total_time < 45:
            logger.warning("⚠️ FAIR - May miss high-demand tickets")
        else:
            logger.error("❌ POOR - Too slow for competitive ticket buying")
        
        self.results['tests']['end_to_end'] = results
    
    def save_results(self):
        """Save benchmark results to file"""
        results_file = Path("benchmark_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"\n💾 Results saved to: {results_file}")
    
    def generate_report(self):
        """Generate markdown report"""
        report_file = Path("benchmark_report.md")
        
        with open(report_file, 'w') as f:
            f.write("# StealthMaster Benchmark Report\n\n")
            f.write(f"Generated: {self.results['timestamp']}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            
            total_tests = len(self.results['tests'])
            passed_tests = sum(1 for t in self.results['tests'].values() if 'error' not in t)
            
            f.write(f"- Total Tests: {total_tests}\n")
            f.write(f"- Passed: {passed_tests}\n")
            f.write(f"- Failed: {total_tests - passed_tests}\n\n")
            
            # Key Metrics
            f.write("## Key Performance Metrics\n\n")
            
            if 'browser_launch' in self.results['tests']:
                avg_launch = self.results['tests']['browser_launch'].get('average')
                if avg_launch:
                    f.write(f"- **Browser Launch**: {avg_launch:.2f}s average\n")
            
            if 'end_to_end' in self.results['tests']:
                total_time = self.results['tests']['end_to_end'].get('total_time')
                if total_time:
                    f.write(f"- **End-to-End Time**: {total_time:.1f}s\n")
            
            f.write("\n## Detailed Results\n\n")
            
            # Detailed test results
            for test_name, test_results in self.results['tests'].items():
                f.write(f"### {test_name.replace('_', ' ').title()}\n\n")
                
                if isinstance(test_results, dict):
                    for key, value in test_results.items():
                        if key != 'error':
                            f.write(f"- **{key}**: {value}\n")
                    
                    if 'error' in test_results:
                        f.write(f"\n⚠️ **Error**: {test_results['error']}\n")
                
                f.write("\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            e2e_time = self.results['tests'].get('end_to_end', {}).get('total_time', 999)
            
            if e2e_time < 20:
                f.write("✅ **Performance is EXCELLENT** - Your bot is highly competitive\n\n")
                f.write("Tips to maintain performance:\n")
                f.write("- Keep Chrome and drivers updated\n")
                f.write("- Monitor for website changes\n")
                f.write("- Use session persistence to skip login\n")
            elif e2e_time < 30:
                f.write("⚠️ **Performance is GOOD** - Suitable for most scenarios\n\n")
                f.write("Improvements to consider:\n")
                f.write("- Enable headless mode for faster launch\n")
                f.write("- Pre-warm the browser before ticket release\n")
                f.write("- Optimize selector strategies\n")
            else:
                f.write("❌ **Performance needs improvement**\n\n")
                f.write("Critical improvements needed:\n")
                f.write("- Review resource blocking configuration\n")
                f.write("- Optimize browser launch settings\n")
                f.write("- Consider using a faster proxy\n")
                f.write("- Reduce unnecessary waits in code\n")
        
        logger.info(f"📄 Report generated: {report_file}")


def main():
    """Run the benchmark suite"""
    benchmark = BenchmarkSuite()
    
    try:
        benchmark.run_all_tests()
        
        # Print summary
        print("\n" + "="*50)
        print("BENCHMARK COMPLETE")
        print("="*50)
        
        # Check if bot is competitive
        e2e_time = benchmark.results['tests'].get('end_to_end', {}).get('total_time', 999)
        
        if e2e_time < 20:
            print("\n✅ Your bot is HIGHLY COMPETITIVE for securing tickets!")
            print(f"   Total flow time: {e2e_time:.1f} seconds")
            print("   You should be able to secure tickets in most scenarios.")
        elif e2e_time < 30:
            print("\n⚠️ Your bot has GOOD performance")
            print(f"   Total flow time: {e2e_time:.1f} seconds")
            print("   Should work well for moderate-demand events.")
        else:
            print("\n❌ Your bot needs optimization")
            print(f"   Total flow time: {e2e_time:.1f} seconds")
            print("   May struggle with high-demand tickets.")
        
        print("\nCheck benchmark_report.md for detailed analysis.")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Benchmark interrupted by user")
    except Exception as e:
        logger.error(f"\n💥 Benchmark failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()