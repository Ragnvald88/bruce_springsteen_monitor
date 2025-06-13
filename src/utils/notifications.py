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
        url: Optional[str] = None
    ):
        """Send notification when tickets are found."""
        self.notification_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Console notification with sound
        print(f"\n🎯 TICKET ALERT at {timestamp}!")
        print(f"Platform: {platform}")
        print(f"Event: {event_name}")
        print(f"Tickets found: {ticket_count}")
        if url:
            print(f"URL: {url}")
        print("\a")  # System beep
        
        # macOS notification
        if os.system == 'Darwin':  # macOS
            title = f"🎫 Tickets Found on {platform}!"
            message = f"{ticket_count} tickets for {event_name}"
            os.system(f'''
                osascript -e 'display notification "{message}" with title "{title}" sound name "Glass"'
            ''')
        
        # Log to file
        logger.info(f"TICKET ALERT: {platform} - {event_name} - {ticket_count} tickets")
        
        # Future: Add email, SMS, Discord, Telegram notifications
        
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