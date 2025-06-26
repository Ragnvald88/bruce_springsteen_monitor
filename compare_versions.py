#!/usr/bin/env python3
"""
Compare script to test fansale.py (v1) and fansale_v2.py performance
"""

import time
import subprocess
import json
import os
import signal
import sys
from pathlib import Path
from datetime import datetime

class ComparisonRunner:
    def __init__(self):
        self.results = {
            'v1': {},
            'v2': {},
            'test_start': datetime.now().isoformat()
        }
        
    def backup_stats(self):
        """Backup existing stats file"""
        stats_file = Path('fansale_stats.json')
        if stats_file.exists():
            backup_name = f'fansale_stats_backup_{int(time.time())}.json'
            stats_file.rename(backup_name)
            print(f"✅ Backed up stats to {backup_name}")
            
    def clear_stats(self):
        """Clear stats for fresh test"""
        stats_file = Path('fansale_stats.json')
        if stats_file.exists():
            stats_file.unlink()
            
    def get_stats(self):
        """Read current stats"""
        stats_file = Path('fansale_stats.json')
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                return json.load(f)
        return None
        
    def test_browser_creation(self, script_name):
        """Test browser creation speed"""
        print(f"\n🧪 Testing browser creation for {script_name}...")
        
        # Create test script that just creates browsers and exits
        test_code = f"""
import sys
sys.path.insert(0, '.')
from {script_name.replace('.py', '')} import FanSaleBot
import time

bot = FanSaleBot()
bot.num_browsers = 2

start_time = time.time()
browsers = []
for i in range(1, 3):
    try:
        browser = bot.create_browser(i)
        if browser:
            browsers.append(browser)
    except Exception as e:
        print(f"Failed to create browser: {{e}}")
        
creation_time = time.time() - start_time
print(f"BROWSER_CREATION_TIME: {{creation_time}}")

# Cleanup
for browser in browsers:
    try:
        browser.quit()
    except:
        pass
"""
        
        # Write test script
        test_file = Path(f'browser_test_{script_name}')
        with open(test_file, 'w') as f:
            f.write(test_code)
            
        try:
            # Run test
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse results
            for line in result.stdout.split('\n'):
                if 'BROWSER_CREATION_TIME:' in line:
                    creation_time = float(line.split(':')[1].strip())
                    return creation_time
                    
            if result.returncode != 0:
                print(f"❌ Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Browser creation timed out")
            return None
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
                
    def test_page_load_speed(self, script_name):
        """Test page load speed with/without images"""
        print(f"\n🧪 Testing page load speed for {script_name}...")
        
        # This would require running the actual bot briefly
        # For now, we'll note this as a metric to observe during live testing
        return "Requires live testing"
        
    def test_memory_usage(self, script_name):
        """Test memory usage"""
        print(f"\n🧪 Testing memory usage for {script_name}...")
        
        # Create test that runs briefly and reports memory
        test_code = f"""
import sys
sys.path.insert(0, '.')
from {script_name.replace('.py', '')} import FanSaleBot
import time
import resource

bot = FanSaleBot()
bot.num_browsers = 1

# Create browser
browsers = []
try:
    browser = bot.create_browser(1)
    if browser:
        browsers.append(browser)
        
    # Navigate to a page
    browser.get("https://www.fansale.it")
    time.sleep(3)
    
    # Get memory usage
    usage = resource.getrusage(resource.RUSAGE_SELF)
    memory_mb = usage.ru_maxrss / 1024 / 1024
    print(f"MEMORY_USAGE_MB: {{memory_mb}}")
    
except Exception as e:
    print(f"Error: {{e}}")
finally:
    for browser in browsers:
        try:
            browser.quit()
        except:
            pass
"""
        
        test_file = Path(f'memory_test_{script_name}')
        with open(test_file, 'w') as f:
            f.write(test_code)
            
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            for line in result.stdout.split('\n'):
                if 'MEMORY_USAGE_MB:' in line:
                    memory_mb = float(line.split(':')[1].strip())
                    return memory_mb
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        finally:
            if test_file.exists():
                test_file.unlink()
                
    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting FanSale Bot Comparison Tests")
        print("=" * 60)
        
        # Backup existing stats
        self.backup_stats()
        
        # Test both versions
        for version, script in [('v1', 'fansale.py'), ('v2', 'fansale_v2.py')]:
            print(f"\n\n📋 Testing {script} ({version})")
            print("-" * 40)
            
            # Clear stats for fresh test
            self.clear_stats()
            
            # Test browser creation time
            creation_time = self.test_browser_creation(script)
            if creation_time:
                self.results[version]['browser_creation_time'] = creation_time
                print(f"✅ Browser creation time: {creation_time:.2f}s")
            
            # Test memory usage
            memory_mb = self.test_memory_usage(script)
            if memory_mb:
                self.results[version]['memory_usage_mb'] = memory_mb
                print(f"✅ Memory usage: {memory_mb:.2f} MB")
                
            # Note about other metrics
            self.results[version]['notes'] = {
                'page_load_speed': 'V2 should be faster due to image blocking',
                'refresh_pattern': 'V2 has staggered refresh (25-35s) vs V1 fixed (30s)',
                'human_behavior': 'V2 has 5% chance of 8-15s pauses',
                'browser_startup': 'V2 has 3-7s delays between browsers'
            }
            
        # Summary
        self.print_summary()
        
        # Save results
        with open('comparison_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Full results saved to comparison_results.json")
        
    def print_summary(self):
        """Print comparison summary"""
        print("\n\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        # Browser creation comparison
        v1_creation = self.results['v1'].get('browser_creation_time', 'N/A')
        v2_creation = self.results['v2'].get('browser_creation_time', 'N/A')
        
        if isinstance(v1_creation, float) and isinstance(v2_creation, float):
            diff = v2_creation - v1_creation
            pct = (diff / v1_creation) * 100 if v1_creation > 0 else 0
            
            print(f"\n🌐 Browser Creation Time:")
            print(f"   V1: {v1_creation:.2f}s")
            print(f"   V2: {v2_creation:.2f}s")
            if diff > 0:
                print(f"   ⚠️  V2 is {diff:.2f}s slower ({pct:.1f}%) due to startup delays")
            else:
                print(f"   ✅ V2 is {abs(diff):.2f}s faster ({abs(pct):.1f}%)")
                
        # Memory comparison
        v1_memory = self.results['v1'].get('memory_usage_mb', 'N/A')
        v2_memory = self.results['v2'].get('memory_usage_mb', 'N/A')
        
        if isinstance(v1_memory, float) and isinstance(v2_memory, float):
            diff = v2_memory - v1_memory
            pct = (diff / v1_memory) * 100 if v1_memory > 0 else 0
            
            print(f"\n💾 Memory Usage:")
            print(f"   V1: {v1_memory:.2f} MB")
            print(f"   V2: {v2_memory:.2f} MB")
            if diff > 0:
                print(f"   ⚠️  V2 uses {diff:.2f} MB more ({pct:.1f}%)")
            else:
                print(f"   ✅ V2 uses {abs(diff):.2f} MB less ({abs(pct):.1f}%)")
                
        # Feature comparison
        print(f"\n✨ V2 Enhancements:")
        print("   ✅ Images disabled for faster page loads")
        print("   ✅ Staggered refresh cycles (anti-detection)")
        print("   ✅ Human-like pause patterns (5% chance)")
        print("   ✅ Delayed browser startup (anti-detection)")
        
        print(f"\n⚡ Performance Impact:")
        print("   • Page loads: V2 should be 20-30% faster (no images)")
        print("   • Detection risk: V2 significantly lower")
        print("   • Check rate: V2 slightly lower (human pauses)")
        print("   • Overall: V2 trades minor speed for better stealth")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    runner = ComparisonRunner()
    runner.run_tests()
