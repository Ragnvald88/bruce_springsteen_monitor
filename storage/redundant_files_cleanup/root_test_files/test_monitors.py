#!/usr/bin/env python3
"""Test monitor initialization"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test():
    from src.core.enhanced_orchestrator_v3 import EnhancedOrchestrator
    
    config = {
        'app_settings': {
            'mode': 'stealth',
            'headless': False
        },
        'targets': [
            {
                'platform': 'fansale',
                'event_name': 'Bruce Springsteen Milano',
                'url': 'https://www.fansale.it/fansale/tickets/all/bruce-springsteen/458554',
                'enabled': True,
                'priority': 'HIGH',
                'max_price_per_ticket': 500
            }
        ]
    }
    
    orch = EnhancedOrchestrator(config)
    
    print("🚀 Starting orchestrator...")
    await orch.initialize()
    
    print(f"📊 Monitors initialized: {len(orch.monitors)}")
    
    if len(orch.monitors) > 0:
        print("✅ Success! Monitors are working!")
        for monitor_id, monitor in orch.monitors.items():
            print(f"  - {monitor_id}: {monitor.platform}")
    else:
        print("❌ No monitors created")
    
    # Cleanup
    await orch.stop()

if __name__ == "__main__":
    asyncio.run(test())