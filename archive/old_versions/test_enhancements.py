#!/usr/bin/env python3
"""
Test script to verify StealthMaster enhancements
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.telemetry.data_tracker import DataUsageTracker
from src.telemetry.history_tracker import history_tracker

async def test_enhancements():
    print("Testing StealthMaster Enhancements...\n")
    
    # Test 1: Data tracker caching
    print("1. Testing data tracker smart caching:")
    tracker = DataUsageTracker()
    
    # Simulate a page object
    class MockPage:
        async def evaluate(self, script):
            return {
                'tickets': [
                    {'text': 'PRATO A - €150', 'available': True},
                    {'text': 'PRATO B - €120', 'available': True}
                ],
                'hasTickets': True
            }
    
    page = MockPage()
    
    # First call should fetch
    result1 = await tracker.smart_check(page, 'https://test.com', 'fansale')
    print(f"   First call result: {result1['hasTickets']}")
    
    # Second call should use cache
    result2 = await tracker.smart_check(page, 'https://test.com', 'fansale')
    print(f"   Second call (cached): {result2['hasTickets']}")
    print(f"   Cache working: {'✓' if 'fansale:https://test.com' in tracker.request_cache else '✗'}\n")
    
    # Test 2: History tracking with 3 categories
    print("2. Testing simplified ticket categories:")
    history_tracker.set_session_id("test_session")
    
    # Test different ticket types
    test_contents = [
        ("PRATO A disponibile", "prato_a"),
        ("PRATO B tickets", "prato_b"),
        ("TRIBUNA NUMERATA", "seating"),
        ("Random content", "general")
    ]
    
    for content, expected in test_contents:
        category = history_tracker._categorize_ticket(content)
        print(f"   '{content}' -> {category} {'✓' if category == expected else '✗'}")
    
    print("\n3. Cookie directory check:")
    cookie_dir = Path("data/cookies")
    print(f"   Cookie directory exists: {'✓' if cookie_dir.exists() else '✗'}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(test_enhancements())
