"""
Notification system for StealthMaster
Supports multiple notification channels including Telegram, Pushover, etc.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger('StealthMaster.Notifications')


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    def send(self, message: str, **kwargs) -> bool:
        """Send a notification message"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the channel is properly configured"""
        pass


class TelegramNotifier(NotificationChannel):
    """Telegram notification channel"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)
    
    def send(self, message: str, parse_mode: str = 'HTML', **kwargs) -> bool:
        """
        Send a message via Telegram
        
        Args:
            message: The message to send
            parse_mode: Telegram parse mode (HTML or Markdown)
            **kwargs: Additional parameters for the Telegram API
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.debug("Telegram not configured")
            return False
        
        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            data.update(kwargs)
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False


class PushoverNotifier(NotificationChannel):
    """Pushover notification channel"""
    
    def __init__(self):
        self.user_key = os.getenv('PUSHOVER_USER_KEY')
        self.api_token = os.getenv('PUSHOVER_API_TOKEN')
        self.api_url = "https://api.pushover.net/1/messages.json"
    
    def is_configured(self) -> bool:
        """Check if Pushover is properly configured"""
        return bool(self.user_key and self.api_token)
    
    def send(self, message: str, title: str = "StealthMaster", priority: int = 0, **kwargs) -> bool:
        """
        Send a message via Pushover
        
        Args:
            message: The message to send
            title: Message title
            priority: Message priority (-2 to 2)
            **kwargs: Additional Pushover parameters
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.debug("Pushover not configured")
            return False
        
        try:
            data = {
                'token': self.api_token,
                'user': self.user_key,
                'message': message,
                'title': title,
                'priority': priority,
                'timestamp': int(datetime.now().timestamp())
            }
            data.update(kwargs)
            
            response = requests.post(
                self.api_url,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Pushover message sent successfully")
                return True
            else:
                logger.error(f"Pushover API error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Pushover message: {e}")
            return False


class Notifier:
    """Main notification manager that handles multiple channels"""
    
    def __init__(self):
        """Initialize all available notification channels"""
        self.channels = []
        
        # Initialize Telegram if configured
        telegram = TelegramNotifier()
        if telegram.is_configured():
            self.channels.append(telegram)
            logger.info("Telegram notifications enabled")
        
        # Initialize Pushover if configured
        pushover = PushoverNotifier()
        if pushover.is_configured():
            self.channels.append(pushover)
            logger.info("Pushover notifications enabled")
        
        if not self.channels:
            logger.warning("No notification channels configured")
    
    def send_ticket_reserved(self, ticket_info: Dict[str, Any]):
        """Send notification for successful ticket reservation"""
        message = self._format_ticket_message(ticket_info)
        
        for channel in self.channels:
            try:
                channel.send(message)
            except Exception as e:
                logger.error(f"Failed to send via {channel.__class__.__name__}: {e}")
    
    def send_error(self, error_message: str, critical: bool = False):
        """Send error notification"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if critical:
            message = f"🚨 <b>CRITICAL ERROR</b> at {timestamp}\n\n{error_message}"
        else:
            message = f"⚠️ <b>Error</b> at {timestamp}\n\n{error_message}"
        
        for channel in self.channels:
            try:
                if isinstance(channel, PushoverNotifier) and critical:
                    # High priority for critical errors
                    channel.send(message, priority=1)
                else:
                    channel.send(message)
            except Exception as e:
                logger.error(f"Failed to send via {channel.__class__.__name__}: {e}")
    
    def send_status(self, status_message: str):
        """Send general status update"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"ℹ️ <b>Status Update</b> at {timestamp}\n\n{status_message}"
        
        for channel in self.channels:
            try:
                channel.send(message)
            except Exception as e:
                logger.error(f"Failed to send via {channel.__class__.__name__}: {e}")
    
    def _format_ticket_message(self, ticket_info: Dict[str, Any]) -> str:
        """Format ticket reservation message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""🎫 <b>TICKET RESERVED!</b>

<b>Time:</b> {timestamp}
<b>Event:</b> {ticket_info.get('event', 'Unknown')}
<b>Price:</b> {ticket_info.get('price', 'Unknown')}
<b>Section:</b> {ticket_info.get('section', 'Unknown')}
<b>Quantity:</b> {ticket_info.get('quantity', 1)}

<b>Status:</b> ✅ Added to cart successfully

<i>Check your cart and complete the purchase!</i>"""
        
        return message
    
    def test_notifications(self):
        """Send a test notification to all configured channels"""
        test_message = """🧪 <b>Test Notification</b>

This is a test message from StealthMaster.
If you received this, notifications are working correctly!

Configured channels: {}""".format(
            ', '.join([ch.__class__.__name__ for ch in self.channels])
        )
        
        success_count = 0
        for channel in self.channels:
            try:
                if channel.send(test_message):
                    success_count += 1
                    logger.info(f"Test notification sent via {channel.__class__.__name__}")
            except Exception as e:
                logger.error(f"Test notification failed for {channel.__class__.__name__}: {e}")
        
        return success_count == len(self.channels)


# Example usage
if __name__ == "__main__":
    # Test the notification system
    logging.basicConfig(level=logging.DEBUG)
    
    notifier = Notifier()
    
    # Test notification
    if notifier.test_notifications():
        print("✅ All notifications sent successfully!")
    else:
        print("❌ Some notifications failed")
    
    # Test ticket notification
    ticket_info = {
        'event': 'Bruce Springsteen - Milano',
        'price': '€85.00',
        'section': 'Prato Gold',
        'quantity': 2
    }
    notifier.send_ticket_reserved(ticket_info)