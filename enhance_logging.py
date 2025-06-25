#!/usr/bin/env python3
"""
Add clearer ticket detection logging
"""

from pathlib import Path

def enhance_ticket_logging():
    """Add clearer logging when tickets are detected"""
    
    file_path = Path("fansale_no_login.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the log_new_ticket method and enhance it
    old_log = '''        # Build detailed ticket description
        details = []
        if ticket_info['section']:
            details.append(f"Section: {ticket_info['section']}")'''
    
    new_log = '''        # Build detailed ticket description
        details = []
        
        # Add clear indication of what we're looking for vs what we found
        raw_text_preview = ticket_info['raw_text'][:100].replace('\\n', ' ')
        logger.debug(f"🔍 Ticket text preview: {raw_text_preview}")
        logger.debug(f"🎯 Categorized as: {category}")
        
        if ticket_info['section']:
            details.append(f"Section: {ticket_info['section']}")'''
    
    content = content.replace(old_log, new_log)
    
    # Also enhance the categorize_ticket to log what it's matching
    old_categorize = '''    def categorize_ticket(self, ticket_text: str) -> str:
        """Categorize ticket based on text content"""
        ticket_lower = ticket_text.lower()'''
    
    new_categorize = '''    def categorize_ticket(self, ticket_text: str) -> str:
        """Categorize ticket based on text content"""
        ticket_lower = ticket_text.lower()
        
        # Debug logging to verify detection
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Checking ticket text: {ticket_lower[:50]}...")'''
    
    content = content.replace(old_categorize, new_categorize)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Enhanced ticket detection logging!")
    print("\nNow when you run the bot:")
    print("- It will show what text it's analyzing")
    print("- It will confirm how each ticket is categorized")
    print("\n💡 Run with debug logging to see details:")
    print("   Set logging level to DEBUG in the bot")

if __name__ == "__main__":
    enhance_ticket_logging()
