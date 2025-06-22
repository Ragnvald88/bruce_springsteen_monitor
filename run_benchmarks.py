#!/usr/bin/env python3
"""
Real benchmark runner for StealthMaster
Measures actual performance metrics without faking results
"""

import sys
import os
import time
import json
import psutil
import traceback
from pathlib import Path
from datetime import datetime
from statistics import mean, stdev

# Python 3.12+ fix
if sys.version_info >= (3, 12):
    sys.path.insert(0, str(Path(__file__).parent))
    from src.utils.uc_patch import patch_distutils
    patch_distutils()

from selenium.webdriver.common.by import By
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from stealthmaster import StealthMaster

load_dotenv()


class BenchmarkRunner:
    """Runs real performance benchmarks"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'python_version': sys.version
            },
            'benchmarks': {},
            'passed': True
        }
        
    def measure_driver_creation(self, iterations=3):
        """Measure driver creation time"""
        print("📊 Measuring driver creation time...")
        times = []
        
        for i in range(iterations):
            bot = StealthMaster()
            start = time.time()
            
            try:
                driver = bot.create_driver()
                creation_time = time.time() - start
                times.append(creation_time)
                print(f"  Iteration {i+1}: {creation_time:.2f}s")
                driver.quit()
                time.sleep(2)  # Pause between iterations
            except Exception as e:
                print(f"  Iteration {i+1}: FAILED - {e}")
                self.results['benchmarks']['driver_creation'] = {
                    'error': str(e),
                    'passed': False
                }
                return
        
        avg_time = mean(times)
        std_dev = stdev(times) if len(times) > 1 else 0
        
        self.results['benchmarks']['driver_creation'] = {
            'iterations': iterations,
            'times': times,
            'average': avg_time,
            'std_dev': std_dev,
            'passed': avg_time < 10,
            'requirement': '< 10 seconds'
        }
        
        print(f"  Average: {avg_time:.2f}s (Requirement: < 10s)")
        
    def measure_page_load(self, iterations=3):
        """Measure page load times"""
        print("\n📊 Measuring page load time...")
        times = []
        
        try:
            bot = StealthMaster()
            driver = bot.create_driver()
            
            for i in range(iterations):
                start = time.time()
                driver.get("https://www.fansale.it")
                load_time = time.time() - start
                times.append(load_time)
                print(f"  Iteration {i+1}: {load_time:.2f}s")
                time.sleep(2)
                
            driver.quit()
            
            avg_time = mean(times)
            self.results['benchmarks']['page_load'] = {
                'iterations': iterations,
                'times': times,
                'average': avg_time,
                'passed': avg_time < 5,
                'requirement': '< 5 seconds'
            }
            
            print(f"  Average: {avg_time:.2f}s (Requirement: < 5s)")
            
        except Exception as e:
            print(f"  FAILED: {e}")
            self.results['benchmarks']['page_load'] = {
                'error': str(e),
                'passed': False
            }
            
    def measure_javascript_performance(self):
        """Measure JavaScript execution speed"""
        print("\n📊 Measuring JavaScript performance...")
        
        try:
            bot = StealthMaster()
            driver = bot.create_driver()
            driver.get("https://www.fansale.it")
            time.sleep(3)
            
            # Test 1: Simple query
            times_simple = []
            for i in range(5):
                start = time.time()
                result = driver.execute_script("return document.querySelectorAll('*').length")
                times_simple.append(time.time() - start)
                
            # Test 2: Complex query (finding € elements)
            times_complex = []
            for i in range(5):
                start = time.time()
                result = driver.execute_script("""
                    const elements = document.querySelectorAll('*');
                    let count = 0;
                    for (const elem of elements) {
                        if (elem.textContent && elem.textContent.includes('€')) {
                            count++;
                        }
                    }
                    return count;
                """)
                times_complex.append(time.time() - start)
                
            driver.quit()
            
            avg_simple = mean(times_simple)
            avg_complex = mean(times_complex)
            
            self.results['benchmarks']['javascript_performance'] = {
                'simple_query_avg': avg_simple,
                'complex_query_avg': avg_complex,
                'simple_times': times_simple,
                'complex_times': times_complex,
                'passed': avg_complex < 0.5,
                'requirement': '< 500ms for complex queries'
            }
            
            print(f"  Simple query average: {avg_simple*1000:.1f}ms")
            print(f"  Complex query average: {avg_complex*1000:.1f}ms (Requirement: < 500ms)")
            
        except Exception as e:
            print(f"  FAILED: {e}")
            self.results['benchmarks']['javascript_performance'] = {
                'error': str(e),
                'passed': False
            }
            
    def measure_memory_usage(self, duration=60):
        """Measure memory usage over time"""
        print(f"\n📊 Measuring memory usage over {duration} seconds...")
        
        try:
            bot = StealthMaster()
            driver = bot.create_driver()
            driver.get("https://www.fansale.it")
            
            # Get process
            process = psutil.Process()
            memory_samples = []
            
            start_time = time.time()
            while time.time() - start_time < duration:
                memory_mb = process.memory_info().rss / (1024 * 1024)
                memory_samples.append(memory_mb)
                print(f"\r  Current memory: {memory_mb:.1f}MB", end='', flush=True)
                time.sleep(5)
                
                # Simulate some activity
                driver.refresh()
                
            driver.quit()
            
            avg_memory = mean(memory_samples)
            max_memory = max(memory_samples)
            
            self.results['benchmarks']['memory_usage'] = {
                'duration_seconds': duration,
                'samples': len(memory_samples),
                'average_mb': avg_memory,
                'max_mb': max_memory,
                'passed': max_memory < 500,
                'requirement': '< 500MB'
            }
            
            print(f"\n  Average: {avg_memory:.1f}MB, Max: {max_memory:.1f}MB (Requirement: < 500MB)")
            
        except Exception as e:
            print(f"\n  FAILED: {e}")
            self.results['benchmarks']['memory_usage'] = {
                'error': str(e),
                'passed': False
            }
            
    def measure_stealth_features(self):
        """Check stealth/anti-detection features"""
        print("\n📊 Checking stealth features...")
        
        try:
            bot = StealthMaster()
            driver = bot.create_driver()
            driver.get("https://www.fansale.it")
            
            # Check navigator.webdriver
            webdriver_check = driver.execute_script("return navigator.webdriver")
            
            # Check user agent
            user_agent = driver.execute_script("return navigator.userAgent")
            
            # Check plugins
            plugins_length = driver.execute_script("return navigator.plugins.length")
            
            # Check permissions
            permissions_check = driver.execute_script("""
                return Notification.permission !== 'default' || 
                       navigator.permissions === undefined
            """)
            
            driver.quit()
            
            stealth_score = 0
            if webdriver_check is None or webdriver_check is False:
                stealth_score += 25
            if "Chrome" in user_agent and "HeadlessChrome" not in user_agent:
                stealth_score += 25
            if plugins_length > 0:
                stealth_score += 25
            if not permissions_check:
                stealth_score += 25
                
            self.results['benchmarks']['stealth_features'] = {
                'webdriver_hidden': webdriver_check is None or webdriver_check is False,
                'user_agent_ok': "Chrome" in user_agent and "HeadlessChrome" not in user_agent,
                'plugins_present': plugins_length > 0,
                'permissions_ok': not permissions_check,
                'stealth_score': stealth_score,
                'passed': stealth_score >= 75,
                'requirement': 'Score >= 75/100'
            }
            
            print(f"  Stealth Score: {stealth_score}/100 (Requirement: >= 75)")
            print(f"    - navigator.webdriver hidden: {'✅' if webdriver_check is None or webdriver_check is False else '❌'}")
            print(f"    - User agent OK: {'✅' if 'Chrome' in user_agent and 'HeadlessChrome' not in user_agent else '❌'}")
            print(f"    - Plugins present: {'✅' if plugins_length > 0 else '❌'}")
            
        except Exception as e:
            print(f"  FAILED: {e}")
            self.results['benchmarks']['stealth_features'] = {
                'error': str(e),
                'passed': False
            }
            
    def run_all_benchmarks(self):
        """Run all benchmarks"""
        print("🚀 Starting StealthMaster Benchmarks\n")
        
        try:
            self.measure_driver_creation()
            self.measure_page_load()
            self.measure_javascript_performance()
            self.measure_memory_usage(duration=30)  # Shorter duration for testing
            self.measure_stealth_features()
            
            # Calculate overall pass/fail
            for benchmark in self.results['benchmarks'].values():
                if not benchmark.get('passed', False):
                    self.results['passed'] = False
                    break
                    
        except Exception as e:
            print(f"\n❌ Benchmark suite failed: {e}")
            traceback.print_exc()
            self.results['error'] = str(e)
            self.results['passed'] = False
            
        # Save results
        Path("test_results").mkdir(exist_ok=True)
        filename = f"test_results/benchmarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Print summary
        print("\n" + "="*50)
        print("📋 BENCHMARK SUMMARY")
        print("="*50)
        
        for name, result in self.results['benchmarks'].items():
            if 'error' in result:
                print(f"❌ {name}: FAILED - {result['error']}")
            else:
                status = "✅" if result['passed'] else "❌"
                print(f"{status} {name}: {result.get('requirement', 'N/A')}")
                
        print("\n" + "="*50)
        if self.results['passed']:
            print("✅ ALL BENCHMARKS PASSED!")
        else:
            print("❌ SOME BENCHMARKS FAILED!")
        print("="*50)
        
        print(f"\nResults saved to: {filename}")
        
        return self.results['passed']


if __name__ == "__main__":
    runner = BenchmarkRunner()
    success = runner.run_all_benchmarks()
    sys.exit(0 if success else 1)