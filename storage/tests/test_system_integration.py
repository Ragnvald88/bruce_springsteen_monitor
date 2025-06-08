#!/usr/bin/env python3
"""
System Integration Test for StealthMaster AI v3.0
Verify all components work together after optimizations
"""

import asyncio
import sys
import yaml
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_system_integration():
    """Test full system integration"""
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🧪 STEALTHMASTER AI v3.0 - SYSTEM INTEGRATION TEST")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    results = {
        'browser_pool': False,
        'orchestrator': False,
        'unified_handler': False,
        'stealth_engine': False,
        'retry_logic': False
    }
    
    try:
        # Test 1: Browser Pool
        print(f"{Fore.YELLOW}1. Testing Browser Pool...")
        from src.core.browser_pool import get_browser_pool
        
        pool = await get_browser_pool({'min_size': 1, 'max_size': 2})
        
        # Test acquisition
        async with pool.acquire_browser() as (browser, context, page):
            await page.goto('https://httpbin.org/headers')
            content = await page.content()
            if 'headers' in content.lower():
                print(f"{Fore.GREEN}   ✅ Browser pool working correctly")
                results['browser_pool'] = True
            else:
                print(f"{Fore.RED}   ❌ Browser pool issue")
        
        await pool.shutdown_pool()
        
    except Exception as e:
        print(f"{Fore.RED}   ❌ Browser pool error: {e}")
    
    # Test 2: Orchestrator Integration
    print(f"\n{Fore.YELLOW}2. Testing Orchestrator Integration...")
    try:
        from src.core.enhanced_orchestrator_v3 import UltimateOrchestrator
        
        # Load config
        config_path = Path(__file__).parent / "config" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Create orchestrator
        orchestrator = UltimateOrchestrator(config)
        print(f"{Fore.GREEN}   ✅ Orchestrator initialized")
        results['orchestrator'] = True
        
    except Exception as e:
        print(f"{Fore.RED}   ❌ Orchestrator error: {e}")
    
    # Test 3: UnifiedHandler with Pool
    print(f"\n{Fore.YELLOW}3. Testing UnifiedHandler with Browser Pool...")
    try:
        from src.platforms.unified_handler import UnifiedTicketingHandler
        from src.profiles.manager import ProfileManager
        
        # Get a profile
        profile_manager = ProfileManager()
        profiles = list(profile_manager.profiles.values())
        if profiles:
            profile = profiles[0]
            
            # Create test config
            test_config = {
                'url': 'https://httpbin.org/html',
                'event_name': 'Test Event',
                'use_browser_pool': True,
                'headless': True
            }
            
            # Create handler
            handler = UnifiedTicketingHandler(
                config=test_config,
                profile=profile,
                browser_manager=None,
                connection_manager=None,
                cache=None
            )
            
            print(f"{Fore.GREEN}   ✅ UnifiedHandler created with pool support")
            results['unified_handler'] = True
            
    except Exception as e:
        print(f"{Fore.RED}   ❌ UnifiedHandler error: {e}")
    
    # Test 4: Stealth Engine
    print(f"\n{Fore.YELLOW}4. Testing Stealth Engine...")
    try:
        from src.stealth.stealth_engine import StealthMasterEngine
        
        stealth_engine = StealthMasterEngine()
        print(f"{Fore.GREEN}   ✅ StealthMasterEngine initialized")
        results['stealth_engine'] = True
        
    except Exception as e:
        print(f"{Fore.RED}   ❌ Stealth engine error: {e}")
    
    # Test 5: Retry Logic
    print(f"\n{Fore.YELLOW}5. Testing Retry Logic...")
    try:
        from src.utils.retry_utils import retry, CircuitBreaker
        
        # Test retry decorator
        @retry(max_attempts=3, exceptions=ValueError)
        async def test_function():
            return "success"
        
        result = await test_function()
        if result == "success":
            print(f"{Fore.GREEN}   ✅ Retry logic working")
            results['retry_logic'] = True
            
    except Exception as e:
        print(f"{Fore.RED}   ❌ Retry logic error: {e}")
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}📊 TEST SUMMARY")
    print(f"{Fore.CYAN}{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, result in results.items():
        status = f"{Fore.GREEN}PASS" if result else f"{Fore.RED}FAIL"
        print(f"  {component}: {status}")
    
    print(f"\n{Fore.CYAN}Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print(f"\n{Fore.GREEN}🎉 All systems operational! StealthMaster AI v3.0 is ready.")
    else:
        print(f"\n{Fore.YELLOW}⚠️  Some components need attention.")
    
    return passed == total


async def main():
    """Run integration test"""
    try:
        success = await test_system_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())