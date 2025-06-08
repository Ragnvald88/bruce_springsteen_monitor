#!/usr/bin/env python3
"""Test script to find runtime bugs in main.py"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_minimal_run():
    """Test minimal functionality"""
    print("\n=== Testing Minimal Run ===")
    
    try:
        # Test config loading
        from src.main import load_and_merge_configs, DEFAULT_CONFIG_FILE
        print("1. Testing config loading...")
        config = load_and_merge_configs(DEFAULT_CONFIG_FILE)
        print(f"   ✓ Config loaded: {len(config)} sections")
        
        # Test logging setup
        from src.main import setup_logging
        print("2. Testing logging setup...")
        setup_logging(config)
        print("   ✓ Logging initialized")
        
        # Test orchestrator creation
        print("3. Testing orchestrator import...")
        from src.core.enhanced_orchestrator_v3 import UnifiedOrchestrator
        print("   ✓ Orchestrator imported")
        
        # Test playwright
        print("4. Testing playwright...")
        from playwright.async_api import async_playwright
        async with async_playwright() as playwright:
            print("   ✓ Playwright initialized")
            
            # Test orchestrator creation
            print("5. Creating orchestrator instance...")
            orchestrator = UnifiedOrchestrator(
                config, 
                playwright, 
                DEFAULT_CONFIG_FILE
            )
            print("   ✓ Orchestrator created")
            
            # Test initialization
            print("6. Initializing subsystems...")
            result = await orchestrator.initialize_subsystems()
            print(f"   {'✓' if result else '✗'} Subsystems initialized: {result}")
            
            if not result:
                print("   ! Initialization failed - checking details...")
                return
            
            # Test pre-warm
            print("7. Testing pre-warm connections...")
            try:
                await asyncio.wait_for(orchestrator.pre_warm_connections(), timeout=5.0)
                print("   ✓ Pre-warm completed")
            except asyncio.TimeoutError:
                print("   ! Pre-warm timed out after 5 seconds")
            except Exception as e:
                print(f"   ✗ Pre-warm error: {e}")
            
            # Test run with immediate stop
            print("8. Testing run method...")
            stop_event = asyncio.Event()
            
            async def stop_after_delay():
                await asyncio.sleep(2)
                stop_event.set()
                print("   - Stop event set")
            
            stop_task = asyncio.create_task(stop_after_delay())
            
            try:
                await orchestrator.run(stop_event)
                print("   ✓ Run completed")
            except Exception as e:
                print(f"   ✗ Run error: {e}")
            finally:
                await stop_task
                
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def test_import_time():
    """Test import performance"""
    print("\n=== Testing Import Times ===")
    import time
    
    modules = [
        'src.core.orchestrator',
        'src.platforms.fansale',
        'src.profiles.manager',
        'src.core.stealth.stealth_engine',
        'src.utils.live_status_logger'
    ]
    
    for module in modules:
        start = time.time()
        try:
            __import__(module)
            elapsed = time.time() - start
            print(f"✓ {module}: {elapsed:.3f}s")
        except Exception as e:
            print(f"✗ {module}: {e}")

async def test_authentication():
    """Test authentication configuration"""
    print("\n=== Testing Authentication ===")
    
    try:
        from src.main import load_and_merge_configs, DEFAULT_CONFIG_FILE
        config = load_and_merge_configs(DEFAULT_CONFIG_FILE)
        
        auth_config = config.get('authentication', {})
        print(f"1. Auth enabled: {auth_config.get('enabled', False)}")
        
        if auth_config.get('enabled'):
            platforms = auth_config.get('platforms', {})
            for platform, creds in platforms.items():
                has_email = bool(creds.get('email'))
                has_password = bool(creds.get('password'))
                print(f"2. {platform}: email={'✓' if has_email else '✗'}, password={'✓' if has_password else '✗'}")
        
        # Check environment variables
        import os
        env_vars = ['FANSALE_EMAIL', 'FANSALE_PASSWORD']
        print("\n3. Environment variables:")
        for var in env_vars:
            value = os.getenv(var)
            print(f"   {var}: {'✓ Set' if value else '✗ Not set'}")
            
    except Exception as e:
        print(f"✗ Auth test error: {e}")

async def main():
    """Run all tests"""
    print("Starting runtime bug tests...\n")
    
    await test_import_time()
    await test_authentication()
    await test_minimal_run()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())