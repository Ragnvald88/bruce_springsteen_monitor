"""Notification system for ticket alerts."""

import asyncio
import logging
from typing import Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages notifications when tickets are found."""
    
    def __init__(self):
        self.enabled = True
        self.notification_count = 0
        
    async def send_ticket_alert(
        self, 
        platform: str, 
        event_name: str, 
        ticket_count: int,
        url: Optional[str] = None,
        confidence: float = 1.0
    ):
        """Send notification when tickets are found."""
        self.notification_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Console notification with sound
        print(f"\n🎯 TICKET ALERT at {timestamp}!")
        print(f"Platform: {platform}")
        print(f"Event: {event_name}")
        print(f"Tickets found: {ticket_count}")
        print(f"Confidence: {confidence:.0%}")
        if url:
            print(f"URL: {url}")
        print("\a")  # System beep
        
        # macOS notification
        if os.system == 'Darwin':  # macOS
            title = f"🎫 Tickets Found on {platform}!"
            message = f"{ticket_count} tickets for {event_name} ({confidence:.0%} confidence)"
            os.system(f'''
                osascript -e 'display notification "{message}" with title "{title}" sound name "Glass"'
            ''')
        
        # Log to file
        logger.info(f"TICKET ALERT: {platform} - {event_name} - {ticket_count} tickets - {confidence:.0%} confidence")
        
        # Future: Add email, SMS, Discord, Telegram notifications
    
    async def send_purchase_success(
        self,
        platform: str,
        order_id: Optional[str] = None,
        tickets: int = 0,
        price: float = 0.0
    ):
        """Send notification for successful purchase."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Console notification
        print(f"\n🎉 PURCHASE SUCCESS at {timestamp}!")
        print(f"Platform: {platform}")
        if order_id:
            print(f"Order ID: {order_id}")
        print(f"Tickets: {tickets}")
        if price > 0:
            print(f"Total Price: €{price:.2f}")
        print("\a\a")  # Double beep for success
        
        # macOS notification
        if os.system == 'Darwin':  # macOS
            title = f"🎉 Purchase Complete on {platform}!"
            message = f"Order {order_id}: {tickets} tickets purchased"
            os.system(f'''
                osascript -e 'display notification "{message}" with title "{title}" sound name "Hero"'
            ''')
        
        # Log to file
        logger.info(f"PURCHASE SUCCESS: {platform} - Order {order_id} - {tickets} tickets - €{price:.2f}")
        
    async def test_notification(self):
        """Test notification system."""
        await self.send_ticket_alert(
            platform="Test Platform",
            event_name="Test Event",
            ticket_count=2,
            url="https://example.com"
        )


# Global instance
notification_manager = NotificationManager()