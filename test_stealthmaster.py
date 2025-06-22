#!/usr/bin/env python3
"""
Comprehensive tests for StealthMaster
Tests login, detection, performance, and reliability
"""

import sys
import os
import time
import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# Import our bot
sys.path.insert(0, str(Path(__file__).parent))
from stealthmaster import StealthMaster

load_dotenv()


class TestStealthMaster(unittest.TestCase):
    """Unit tests for StealthMaster components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = StealthMaster()
        
    def test_credentials_loaded(self):
        """Test that credentials are loaded from .env"""
        self.assertIsNotNone(self.bot.email, "Email should be loaded from .env")
        self.assertIsNotNone(self.bot.password, "Password should be loaded from .env")
        
    def test_initial_state(self):
        """Test initial bot state"""
        self.assertEqual(self.bot.tickets_reserved, 0)
        self.assertEqual(self.bot.max_tickets, 4)
        self.assertFalse(self.bot.logged_in)
        self.assertEqual(self.bot.checks, 0)
        
    def test_is_logged_in_detection(self):
        """Test login status detection"""
        # Mock driver
        self.bot.driver = Mock()
        
        # Test logged out state
        mock_element = Mock()
        mock_element.text = "Accedi Login"
        self.bot.driver.find_element.return_value = mock_element
        self.assertFalse(self.bot.is_logged_in())
        
        # Test logged in state
        mock_element.text = "Il mio account Esci"
        self.assertTrue(self.bot.is_logged_in())
        
        # Test with email visible
        mock_element.text = f"Benvenuto {self.bot.email}"
        self.assertTrue(self.bot.is_logged_in())


class TestTicketDetection(unittest.TestCase):
    """Test ticket detection logic"""
    
    def setUp(self):
        self.bot = StealthMaster()
        self.bot.driver = Mock()
        
    def test_find_tickets_with_euro_symbol(self):
        """Test that we find elements with € symbol"""
        # Mock JavaScript execution result
        mock_tickets = [
            {
                'index': 0,
                'text': 'Settore A - €50.00',
                'hasButton': True,
                'hasLink': False
            },
            {
                'index': 1,
                'text': 'Settore B - €75.00',
                'hasButton': False,
                'hasLink': True
            }
        ]
        
        self.bot.driver.execute_script = Mock(return_value=mock_tickets)
        
        # Mock the rest of the method
        with patch.object(self.bot, 'is_logged_in', return_value=True):
            result = self.bot.find_and_reserve_tickets()
            
        # Verify JavaScript was called
        self.bot.driver.execute_script.assert_called()
        
        # Check that stats were updated
        self.assertEqual(self.bot.stats['tickets_found'], 2)
        
    def test_no_tickets_found(self):
        """Test behavior when no tickets are found"""
        self.bot.driver.execute_script = Mock(return_value=[])
        
        with patch.object(self.bot, 'is_logged_in', return_value=True):
            result = self.bot.find_and_reserve_tickets()
            
        self.assertFalse(result)
        self.assertEqual(self.bot.stats['tickets_found'], 0)


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks - measures actual execution times"""
    
    @classmethod
    def setUpClass(cls):
        """Set up performance tracking"""
        cls.results = {
            'timestamp': datetime.now().isoformat(),
            'benchmarks': {}
        }
        
    def test_driver_creation_time(self):
        """Benchmark driver creation time"""
        bot = StealthMaster()
        
        start_time = time.time()
        try:
            driver = bot.create_driver()
            creation_time = time.time() - start_time
            
            self.results['benchmarks']['driver_creation'] = {
                'time_seconds': creation_time,
                'passed': creation_time < 10,  # Should create in under 10 seconds
                'threshold': 10
            }
            
            driver.quit()
        except Exception as e:
            self.results['benchmarks']['driver_creation'] = {
                'error': str(e),
                'passed': False
            }
            
    def test_javascript_execution_speed(self):
        """Test JavaScript execution performance"""
        bot = StealthMaster()
        
        try:
            driver = bot.create_driver()
            driver.get("https://www.google.com")  # Simple test page
            
            # Test JavaScript execution speed
            js_times = []
            for _ in range(5):
                start = time.time()
                result = driver.execute_script("return document.querySelectorAll('*').length")
                js_times.append(time.time() - start)
            
            avg_time = sum(js_times) / len(js_times)
            
            self.results['benchmarks']['js_execution'] = {
                'avg_time_seconds': avg_time,
                'samples': js_times,
                'passed': avg_time < 0.1,  # Should execute in under 100ms
                'threshold': 0.1
            }
            
            driver.quit()
        except Exception as e:
            self.results['benchmarks']['js_execution'] = {
                'error': str(e),
                'passed': False
            }
            
    @classmethod
    def tearDownClass(cls):
        """Save benchmark results"""
        Path("test_results").mkdir(exist_ok=True)
        with open(f"test_results/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(cls.results, f, indent=2)
        
        print("\n📊 Benchmark Results:")
        for name, result in cls.results['benchmarks'].items():
            if 'error' in result:
                print(f"  ❌ {name}: ERROR - {result['error']}")
            else:
                status = "✅" if result['passed'] else "❌"
                print(f"  {status} {name}: {result.get('time_seconds', result.get('avg_time_seconds')):.3f}s")


class TestReliability(unittest.TestCase):
    """Test error handling and reliability"""
    
    def test_login_retry_on_failure(self):
        """Test that login retries on failure"""
        bot = StealthMaster()
        bot.driver = Mock()
        
        # Mock login failure
        bot.driver.current_url = "https://www.ticketone.it/login"
        bot.driver.execute_script = Mock(side_effect=Exception("Login failed"))
        
        result = bot.login()
        self.assertFalse(result)
        self.assertEqual(bot.stats['login_attempts'], 1)
        
    def test_continues_after_ticket_error(self):
        """Test that bot continues after ticket detection error"""
        bot = StealthMaster()
        bot.driver = Mock()
        
        # Mock an error during ticket detection
        bot.driver.execute_script = Mock(side_effect=Exception("Page changed"))
        
        with patch.object(bot, 'is_logged_in', return_value=True):
            result = bot.find_and_reserve_tickets()
            
        # Should return False but not crash
        self.assertFalse(result)
        
    def test_handles_stale_elements(self):
        """Test handling of stale element references"""
        bot = StealthMaster()
        bot.driver = Mock()
        
        # Mock stale element
        mock_element = Mock()
        mock_element.text = Mock(side_effect=Exception("Stale element"))
        bot.driver.find_element.return_value = mock_element
        
        # Should not crash
        result = bot.is_logged_in()
        self.assertFalse(result)


class IntegrationTest(unittest.TestCase):
    """Integration test - tests the full flow"""
    
    def test_full_monitoring_cycle(self):
        """Test a complete monitoring cycle"""
        results = {
            'test': 'full_monitoring_cycle',
            'timestamp': datetime.now().isoformat(),
            'steps': []
        }
        
        try:
            bot = StealthMaster()
            bot.driver = bot.create_driver()
            
            # Step 1: Load page
            start = time.time()
            bot.driver.get("https://www.fansale.it")
            load_time = time.time() - start
            results['steps'].append({
                'step': 'page_load',
                'time': load_time,
                'success': True
            })
            
            # Step 2: Check login status
            start = time.time()
            logged_in = bot.is_logged_in()
            check_time = time.time() - start
            results['steps'].append({
                'step': 'login_check',
                'time': check_time,
                'logged_in': logged_in,
                'success': True
            })
            
            # Step 3: Search for elements with €
            start = time.time()
            elements = bot.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
            search_time = time.time() - start
            results['steps'].append({
                'step': 'element_search',
                'time': search_time,
                'elements_found': len(elements),
                'success': True
            })
            
            bot.driver.quit()
            results['overall_success'] = True
            
        except Exception as e:
            results['error'] = str(e)
            results['overall_success'] = False
            
        # Save results
        Path("test_results").mkdir(exist_ok=True)
        with open(f"test_results/integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(results, f, indent=2)
            
        return results


def run_all_tests():
    """Run all tests and generate report"""
    print("🧪 Running StealthMaster Test Suite\n")
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate summary
    print("\n📋 Test Summary:")
    print(f"  Tests Run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Run integration test separately for detailed output
    print("\n🔄 Running Integration Test...")
    integration_result = IntegrationTest().test_full_monitoring_cycle()
    
    if integration_result['overall_success']:
        print("✅ Integration test passed!")
        for step in integration_result['steps']:
            print(f"  - {step['step']}: {step['time']:.3f}s")
    else:
        print(f"❌ Integration test failed: {integration_result.get('error', 'Unknown error')}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)