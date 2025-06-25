#!/usr/bin/env python3
"""
Fix 1: Menu System - Stop asking for browser config when selecting option 1
"""

import json
from pathlib import Path

def fix_menu_system():
    """Fix the menu system to not ask for config when starting"""
    
    print("🔧 Fixing menu system...")
    
    file_path = Path("fansale_no_login.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Update __init__ to load saved configuration
    old_init = """        # Configuration
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_filters = []  # Will be set to track specific types
        self.ticket_types_to_hunt = {'prato_a', 'prato_b'}  # Default to Prato types"""
    
    new_init = """        # Load saved configuration from bot_config.json
        self._load_saved_config()
        
        # Configuration from loaded settings
        self.num_browsers = self.config.browsers_count
        self.max_tickets = self.config.max_tickets
        self.ticket_filters = getattr(self, 'ticket_filters', [])
        self.ticket_types_to_hunt = getattr(self, 'ticket_types_to_hunt', {'prato_a', 'prato_b'})"""
    
    content = content.replace(old_init, new_init)
    
    # Fix 2: Add method to load saved configuration
    load_config_method = '''
    def _load_saved_config(self):
        """Load saved configuration including ticket types"""
        config_path = Path("bot_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    
                # Load ticket hunting preferences
                if 'ticket_types_to_hunt' in saved_config:
                    self.ticket_types_to_hunt = set(saved_config['ticket_types_to_hunt'])
                if 'ticket_filters' in saved_config:
                    self.ticket_filters = saved_config['ticket_filters']
                    
                logger.info(f"✅ Loaded saved configuration")
            except Exception as e:
                logger.warning(f"Could not load saved config: {e}")
'''
    
    # Insert after __init__ method
    init_end = content.find("        self.notification_manager = NotificationManager(enabled=True)")
    if init_end > 0:
        insert_pos = content.find('\n', init_end) + 1
        content = content[:insert_pos] + load_config_method + content[insert_pos:]
    
    # Fix 3: Update run() to not call configure automatically
    old_run = """            # Show menu
            if not self.show_menu():
                print(f"{Colors.YELLOW}👋 Goodbye!{Colors.END}")
                return
            
            # Configure if first run
            if not hasattr(self, '_configured'):
                self.configure()
                self._configured = True"""
    
    new_run = """            # Show menu
            if not self.show_menu():
                print(f"{Colors.YELLOW}👋 Goodbye!{Colors.END}")
                return
            
            # Configuration is now loaded from saved settings
            # Only configure() when explicitly selected from menu"""
    
    content = content.replace(old_run, new_run)
    
    # Fix 4: Update configure_settings to save ticket types
    old_save = """        # Save configuration
        self.config.browsers_count = self.num_browsers
        self.config.max_tickets = self.max_tickets
        self.config.save(Path("bot_config.json"))"""
    
    new_save = """        # Save configuration including ticket types
        self.config.browsers_count = self.num_browsers
        self.config.max_tickets = self.max_tickets
        
        # Save additional settings
        config_data = self.config.__dict__.copy()
        config_data['ticket_types_to_hunt'] = list(self.ticket_types_to_hunt)
        config_data['ticket_filters'] = self.ticket_filters
        
        with open(Path("bot_config.json"), 'w') as f:
            json.dump(config_data, f, indent=2)"""
    
    content = content.replace(old_save, new_save)
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Menu system fixed!")
    print("\nChanges made:")
    print("1. ✅ Bot now loads saved configuration on startup")
    print("2. ✅ Option 1 starts hunting immediately without asking for config")
    print("3. ✅ Ticket type preferences are saved and loaded")
    print("4. ✅ Configuration only shown when option 2 is selected")
    
    # Update default bot_config.json with sensible defaults
    config_path = Path("bot_config.json")
    if not config_path.exists():
        default_config = {
            "browsers_count": 2,
            "max_tickets": 2,
            "refresh_interval": 30,
            "session_timeout": 900,
            "min_wait": 2.0,
            "max_wait": 4.0,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "ticket_types_to_hunt": ["prato_a", "prato_b"],
            "ticket_filters": []
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print("\n✅ Created default configuration file")

if __name__ == "__main__":
    fix_menu_system()
