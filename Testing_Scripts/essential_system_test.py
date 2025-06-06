#!/usr/bin/env python3
"""
Essential System Test Suite - StealthMaster AI Optimized
Consolidated testing replacing 7 redundant test files
Combines: advanced_diagnostic_test.py + quick_network_diagnostic.py + verify_fixes.py + import.py
Result: Single comprehensive test suite
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class EssentialSystemTester:
    """Comprehensive system testing with optimized coverage"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {
            'imports': {'passed': 0, 'failed': 0, 'details': []},
            'network': {'passed': 0, 'failed': 0, 'details': []},
            'profiles': {'passed': 0, 'failed': 0, 'details': []},
            'stealth': {'passed': 0, 'failed': 0, 'details': []},
            'platforms': {'passed': 0, 'failed': 0, 'details': []},
        }
        self.start_time = time.time()
    
    async def run_comprehensive_test(self) -> bool:
        """Run all essential tests"""
        print("🛡️ StealthMaster AI - Essential System Test Suite")
        print("=" * 60)
        
        success = True
        
        # 1. Import and dependency validation
        print("\n1️⃣ Testing imports and dependencies...")
        success &= await self._test_imports()
        
        # 2. Network connectivity and proxy testing
        print("\n2️⃣ Testing network connectivity...")
        success &= await self._test_network()
        
        # 3. Profile system validation
        print("\n3️⃣ Testing profile system...")
        success &= await self._test_profiles()
        
        # 4. Stealth system validation
        print("\n4️⃣ Testing stealth capabilities...")
        success &= await self._test_stealth()
        
        # 5. Platform integration testing
        print("\n5️⃣ Testing platform integration...")
        success &= await self._test_platforms()
        
        # Generate comprehensive report
        await self._generate_report()
        
        return success
    
    async def _test_imports(self) -> bool:
        """Test essential imports and dependencies"""
        essential_imports = [
            ('asyncio', 'Core async support'),
            ('playwright.async_api', 'Browser automation'),
            ('httpx', 'HTTP client'),
            ('core.ultra_stealth', 'Ultra-stealth system'),
            ('profiles.consolidated_models', 'Profile models'),
            ('core.orchestrator', 'Main orchestrator'),
            ('core.managers', 'Connection managers'),
        ]
        
        all_passed = True
        
        for module_name, description in essential_imports:
            try:
                __import__(module_name)
                self._record_success('imports', f"✅ {module_name}: {description}")
            except ImportError as e:
                self._record_failure('imports', f"❌ {module_name}: {str(e)}")
                all_passed = False
            except Exception as e:
                self._record_failure('imports', f"❌ {module_name}: Unexpected error - {str(e)}")
                all_passed = False
        
        return all_passed
    
    async def _test_network(self) -> bool:
        """Test network connectivity and HTTP capabilities"""
        try:
            import httpx
            
            # Test basic connectivity
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("https://httpbin.org/get", timeout=10.0)
                    if response.status_code == 200:
                        self._record_success('network', "✅ Basic HTTP connectivity working")
                    else:
                        self._record_failure('network', f"❌ HTTP connectivity failed: {response.status_code}")
                        return False
                except Exception as e:
                    self._record_failure('network', f"❌ Network connectivity failed: {str(e)}")
                    return False
            
            # Test User-Agent and headers
            async with httpx.AsyncClient() as client:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36'
                    }
                    response = await client.get("https://httpbin.org/headers", headers=headers, timeout=10.0)
                    if response.status_code == 200:
                        self._record_success('network', "✅ Custom headers working")
                    else:
                        self._record_failure('network', f"❌ Header testing failed: {response.status_code}")
                except Exception as e:
                    self._record_failure('network', f"❌ Header testing failed: {str(e)}")
            
            return True
            
        except ImportError:
            self._record_failure('network', "❌ httpx not available")
            return False
    
    async def _test_profiles(self) -> bool:
        """Test profile system functionality"""
        try:
            from profiles.consolidated_models import (
                BrowserProfile, Platform, ProfileQuality, 
                create_optimized_profile, create_profiles_batch
            )
            
            # Test basic profile creation
            profile = BrowserProfile()
            if profile.profile_id and profile.browser and profile.user_agent:
                self._record_success('profiles', "✅ Basic profile creation working")
            else:
                self._record_failure('profiles', "❌ Basic profile creation failed")
                return False
            
            # Test platform-optimized profile creation
            fansale_profile = create_optimized_profile(Platform.FANSALE)
            if fansale_profile.locale == "it-IT" and fansale_profile.timezone == "Europe/Rome":
                self._record_success('profiles', "✅ Platform-optimized profile creation working")
            else:
                self._record_failure('profiles', "❌ Platform optimization failed")
            
            # Test batch profile creation
            profiles = create_profiles_batch(Platform.TICKETMASTER, count=3)
            if len(profiles) == 3 and all(p.profile_id for p in profiles):
                self._record_success('profiles', "✅ Batch profile creation working")
            else:
                self._record_failure('profiles', "❌ Batch profile creation failed")
            
            # Test profile serialization
            profile_dict = profile.to_dict()
            restored_profile = BrowserProfile.from_dict(profile_dict)
            if restored_profile.profile_id == profile.profile_id:
                self._record_success('profiles', "✅ Profile serialization working")
            else:
                self._record_failure('profiles', "❌ Profile serialization failed")
            
            return True
            
        except Exception as e:
            self._record_failure('profiles', f"❌ Profile system failed: {str(e)}")
            return False
    
    async def _test_stealth(self) -> bool:
        """Test ultra-stealth system functionality"""
        try:
            from core.ultra_stealth import (
                CoreStealthEngine, UnifiedProfile, ProfileGenerator,
                get_ultra_stealth_integration
            )
            
            # Test profile generation
            profile = ProfileGenerator.generate_for_platform('fansale')
            if profile.browser and profile.platform == 'fansale':
                self._record_success('stealth', "✅ Stealth profile generation working")
            else:
                self._record_failure('stealth', "❌ Stealth profile generation failed")
                return False
            
            # Test stealth engine creation
            engine = CoreStealthEngine()
            if hasattr(engine, 'create_stealth_context'):
                self._record_success('stealth', "✅ Stealth engine creation working")
            else:
                self._record_failure('stealth', "❌ Stealth engine creation failed")
            
            # Test integration layer
            integration = get_ultra_stealth_integration()
            if hasattr(integration, 'create_stealth_browser_context'):
                self._record_success('stealth', "✅ Stealth integration working")
            else:
                self._record_failure('stealth', "❌ Stealth integration failed")
            
            # Test script generation
            script = engine._generate_stealth_script(profile)
            if "Ultra-Stealth v2.0" in script and len(script) > 100:
                self._record_success('stealth', "✅ Stealth script generation working")
            else:
                self._record_failure('stealth', "❌ Stealth script generation failed")
            
            return True
            
        except Exception as e:
            self._record_failure('stealth', f"❌ Stealth system failed: {str(e)}")
            return False
    
    async def _test_platforms(self) -> bool:
        """Test platform integration"""
        try:
            # Test orchestrator import and initialization
            from core.orchestrator import UnifiedOrchestrator
            
            # Basic config for testing
            test_config = {
                'app_settings': {'mode': 'adaptive'},
                'targets': [],
                'profile_manager_settings': {},
                'cache_settings': {'max_size_mb': 50},
                'data_limits': {}
            }
            
            # Test orchestrator creation (without playwright instance)
            orchestrator = UnifiedOrchestrator(
                config=test_config,
                playwright_instance=None,  # Skip for unit test
                config_file_path="test",
                gui_queue=None
            )
            
            if hasattr(orchestrator, 'initialize_subsystems'):
                self._record_success('platforms', "✅ Orchestrator creation working")
            else:
                self._record_failure('platforms', "❌ Orchestrator creation failed")
                return False
            
            # Test platform enums
            from profiles.consolidated_models import Platform
            
            platforms = [Platform.FANSALE, Platform.TICKETMASTER, Platform.VIVATICKET]
            if all(p.requires_stealth is not None for p in platforms):
                self._record_success('platforms', "✅ Platform configuration working")
            else:
                self._record_failure('platforms', "❌ Platform configuration failed")
            
            return True
            
        except Exception as e:
            self._record_failure('platforms', f"❌ Platform integration failed: {str(e)}")
            return False
    
    def _record_success(self, category: str, message: str):
        """Record a successful test"""
        self.results[category]['passed'] += 1
        self.results[category]['details'].append(message)
        print(f"  {message}")
    
    def _record_failure(self, category: str, message: str):
        """Record a failed test"""
        self.results[category]['failed'] += 1
        self.results[category]['details'].append(message)
        print(f"  {message}")
    
    async def _generate_report(self):
        """Generate comprehensive test report"""
        duration = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("🛡️ STEALTHMASTER AI - SYSTEM TEST REPORT")
        print("=" * 60)
        
        total_passed = sum(cat['passed'] for cat in self.results.values())
        total_failed = sum(cat['failed'] for cat in self.results.values())
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {total_failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 40)
        
        for category, data in self.results.items():
            total = data['passed'] + data['failed']
            rate = (data['passed'] / total * 100) if total > 0 else 0
            status = "✅" if data['failed'] == 0 else "⚠️" if rate >= 75 else "❌"
            
            print(f"{status} {category.upper()}: {data['passed']}/{total} ({rate:.1f}%)")
        
        if total_failed == 0:
            print("\n🎉 ALL TESTS PASSED! System is ready for operation.")
        elif success_rate >= 80:
            print(f"\n⚠️  MOSTLY WORKING: {success_rate:.1f}% success rate. Check failed tests.")
        else:
            print(f"\n❌ SYSTEM ISSUES: Only {success_rate:.1f}% success rate. Review failed tests.")
        
        print("\n💡 StealthMaster AI Ultra-Optimized Testing Complete!")

async def main():
    """Run the essential system test suite"""
    try:
        tester = EssentialSystemTester()
        success = await tester.run_comprehensive_test()
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())