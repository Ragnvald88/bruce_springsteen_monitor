#!/usr/bin/env python3
"""Test script to verify StealthMaster enhancements"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.telemetry.data_tracker import DataUsageTracker
from src.detection.ticket_detector import TicketDetector


async def test_data_tracker():
    """Test the data tracker functionality"""
    print("Testing Data Tracker...")
    
    tracker = DataUsageTracker()
    await tracker.start_monitoring()
    
    # Simulate some requests
    await tracker.track_request(
        platform="fansale",
        url="https://example.com/event1",
        response_size=1024 * 512,  # 512KB
        blocked_resources={'images': 5, 'scripts': 3}
    )
    
    await tracker.track_request(
        platform="ticketmaster",
        url="https://example.com/event2",
        response_size=1024 * 256,  # 256KB
        blocked_resources={'images': 10, 'scripts': 2}
    )
    
    # Get summary
    summary = tracker.get_summary()
    print(f"Total data used: {summary['total_data_mb']} MB")
    print(f"Platforms: {summary['platforms']}")
    print(f"Recommendations: {summary['recommendations']}")
    
    # Generate report
    report = await tracker.generate_report()
    print("\nReport:")
    print(report)
    
    await tracker.stop_monitoring()
    print("✅ Data Tracker test passed!")


async def test_ticket_detector():
    """Test the ticket detector functionality"""
    print("\nTesting Ticket Detector...")
    
    detector = TicketDetector()
    
    # Mock page object
    class MockPage:
        async def query_selector_all(self, selector):
            # Simulate finding ticket elements
            if selector in ['.ticket-listing-item', '.offer-row']:
                return ['element1', 'element2']  # Found 2 elements
            elif selector in ['.ticket-price', '.offer-price']:
                return ['price1']  # Found price
            elif selector in ['.available-tickets', 'button[class*="buy"]']:
                return ['buy_button']  # Found buy button
            return []
        
        async def content(self):
            return """
            <div class="ticket-listing-item">
                <span class="ticket-price">€50</span>
                <button class="buy-now">Acquista ora</button>
                <span>Disponibile</span>
                <span>Seleziona biglietti</span>
            </div>
            """
    
    # Test Fansale detection
    mock_page = MockPage()
    result = await detector.detect_tickets(mock_page, 'fansale')
    
    print(f"Tickets found: {result['tickets_found']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Ticket count: {result['ticket_count']}")
    print(f"Recommendation: {result['recommendation']}")
    
    assert result['tickets_found'] == True, "Should have found tickets"
    assert result['confidence'] >= 0.7, "Confidence should be high"
    
    print("✅ Ticket Detector test passed!")


async def main():
    """Run all tests"""
    print("🧪 Running StealthMaster Enhancement Tests\n")
    
    try:
        await test_data_tracker()
        await test_ticket_detector()
        
        print("\n✅ All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
