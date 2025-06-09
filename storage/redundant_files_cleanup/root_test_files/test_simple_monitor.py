#!/usr/bin/env python3
"""
Simple test to check if monitoring works
"""

import asyncio
import logging
from src.core.enhanced_orchestrator_v3 import EnhancedOrchestrator

logging.basicConfig(level=logging.INFO)

async def main():
    config = {
        'app_settings': {
            'mode': 'stealth',
            'open_browser_mode': 'both'
        },
        'targets': [
            {
                'platform': 'fansale',
                'event_name': 'Test Event',
                'url': 'https://www.fansale.it',
                'enabled': True,
                'priority': 'NORMAL'
            }
        ]
    }
    
    orchestrator = EnhancedOrchestrator(config)
    
    try:
        await orchestrator.start()
        await asyncio.sleep(5)
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())