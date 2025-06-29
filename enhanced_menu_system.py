#!/usr/bin/env python3
"""
Enhanced Menu System for FanSale Ultimate Bot
Improved visuals, better navigation, and enhanced logging
"""

from colorama import init, Fore, Back, Style
import time
import os

# Initialize colorama
init(autoreset=True)

class EnhancedTerminalUI:
    """Enhanced terminal UI with improved visuals and navigation"""
    
    THEMES = {
        "neon": {
            "primary": Fore.CYAN + Style.BRIGHT,
            "secondary": Fore.MAGENTA,
            "success": Fore.GREEN + Style.BRIGHT,
            "warning": Fore.YELLOW + Style.BRIGHT,
            "error": Fore.RED + Style.BRIGHT,
            "accent": Fore.BLUE + Style.BRIGHT,
            "dim": Fore.WHITE + Style.DIM,
            "header_bg": Back.BLUE,
            "menu_bg": Back.BLACK
        },
        "matrix": {
            "primary": Fore.GREEN,
            "secondary": Fore.GREEN + Style.DIM,
            "success": Fore.GREEN + Style.BRIGHT,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Fore.GREEN + Style.BRIGHT,
            "dim": Fore.GREEN + Style.DIM,
            "header_bg": Back.BLACK,
            "menu_bg": Back.BLACK
        },
        "ocean": {
            "primary": Fore.BLUE + Style.BRIGHT,
            "secondary": Fore.CYAN,
            "success": Fore.GREEN + Style.BRIGHT,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Fore.CYAN + Style.BRIGHT,
            "dim": Fore.BLUE + Style.DIM,
            "header_bg": Back.BLUE,
            "menu_bg": Back.BLACK
        },
        "sunset": {
            "primary": Fore.RED + Style.BRIGHT,
            "secondary": Fore.YELLOW,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW + Style.BRIGHT,
            "error": Fore.RED + Style.BRIGHT,
            "accent": Fore.MAGENTA + Style.BRIGHT,
            "dim": Fore.RED + Style.DIM,
            "header_bg": Back.RED,
            "menu_bg": Back.BLACK
        }
    }
    
    # Enhanced icons
    ICONS = {
        'hunt': '🎯',
        'settings': '⚙️',
        'stats': '📊',
        'theme': '🎨',
        'help': '📖',
        'exit': '🚪',
        'success': '✨',
        'error': '💥',
        'warning': '⚡',
        'info': '💡',
        'ticket': '🎫',
        'browser': '🌐',
        'speed': '🚀',
        'money': '💰',
        'time': '⏱️',
        'profile': '👤',
        'auto': '🤖',
        'notification': '🔔',
        'arrow': '➤',
        'check': '✓',
        'cross': '✗',
        'star': '⭐',
        'heart': '❤️',
        'fire': '🔥',
        'trophy': '🏆',
        'shield': '🛡️',
        'key': '🔑',
        'lock': '🔒',
        'unlock': '🔓'
    }
    
    @staticmethod
    def clear():
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_enhanced_header(theme="neon"):
        """Print enhanced header with gradient effect"""
        EnhancedTerminalUI.clear()
        colors = EnhancedTerminalUI.THEMES[theme]
        
        # Top border
        print(colors["primary"] + "╔" + "═" * 78 + "╗")
        
        # ASCII Art with gradient effect
        ascii_lines = [
            "███████╗ █████╗ ███╗   ██╗███████╗ █████╗ ██╗     ███████╗",
            "██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗██║     ██╔════╝",
            "█████╗  ███████║██╔██╗ ██║███████╗███████║██║     █████╗  ",
            "██╔══╝  ██╔══██║██║╚██╗██║╚════██║██╔══██║██║     ██╔══╝  ",
            "██║     ██║  ██║██║ ╚████║███████║██║  ██║███████╗███████╗",
            "╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝"
        ]
        
        for i, line in enumerate(ascii_lines):
            if i < 3:
                print(f"║ {colors['accent']}{line:^76} ║")
            else:
                print(f"║ {colors['primary']}{line:^76} ║")
        
        # Subtitle
        print("║" + " " * 78 + "║")
        subtitle = f"{EnhancedTerminalUI.ICONS['ticket']} ULTIMATE TICKET HUNTER - ENHANCED EDITION {EnhancedTerminalUI.ICONS['ticket']}"
        print(f"║ {colors['secondary']}{subtitle:^76} ║")
        
        # Bottom border
        print(colors["primary"] + "╚" + "═" * 78 + "╝" + Style.RESET_ALL)
        print()
    
    @staticmethod
    def enhanced_main_menu(settings):
        """Enhanced main menu with better visuals"""
        theme = settings.get("theme", "neon")
        colors = EnhancedTerminalUI.THEMES[theme]
        EnhancedTerminalUI.print_enhanced_header(theme)
        
        # Current status bar
        print(colors["accent"] + "┌─ CURRENT STATUS " + "─" * 60 + "┐")
        
        # Event info
        url = settings.get("target_url", "")
        if "bruce-springsteen" in url:
            event_name = f"{EnhancedTerminalUI.ICONS['star']} Bruce Springsteen Concert"
        else:
            event_name = f"{EnhancedTerminalUI.ICONS['ticket']} Custom Event"
        
        # Status indicators
        browsers = settings.get('num_browsers', 2)
        ticket_types = settings.get('ticket_types', ['all'])
        auto_buy = settings.get('auto_buy', False)
        
        print(f"│ Event: {colors['success']}{event_name:<67} │")
        print(f"│ Config: {colors['secondary']}{browsers} browsers, hunting {', '.join(ticket_types):<52} │")
        print(f"│ Auto-buy: {colors['success'] if auto_buy else colors['error']}{'ENABLED' if auto_buy else 'DISABLED':<64} │")
        print(colors["accent"] + "└" + "─" * 77 + "┘\n")
        
        # Menu sections with enhanced visuals
        menu_items = [
            ("QUICK ACTIONS", "primary", [
                ("1", "Start Hunting", "hunt", "Begin the ticket hunt with current settings"),
                ("2", "Quick Settings", "speed", "Fast configuration for immediate hunting")
            ]),
            ("CONFIGURATION", "secondary", [
                ("3", "Advanced Settings", "settings", "Detailed bot configuration"),
                ("4", "Profile Manager", "profile", "Save and load hunting profiles"),
                ("5", "Auto-Buy Rules", "auto", "Configure automatic purchase rules")
            ]),
            ("ANALYTICS", "accent", [
                ("6", "Live Dashboard", "stats", "Real-time hunting statistics"),
                ("7", "Statistics & History", "trophy", "View historical performance"),
                ("8", "Performance Report", "fire", "Detailed analytics and insights")
            ]),
            ("CUSTOMIZATION", "primary", [
                ("9", "Change Theme", "theme", "Customize visual appearance"),
                ("0", "Notification Settings", "notification", "Configure alerts and sounds")
            ]),
            ("HELP & MORE", "dim", [
                ("H", "Help & Guide", "help", "Learn how to use the bot effectively"),
                ("A", "About", "info", "Information about the bot"),
                ("X", "Exit", "exit", "Close the application")
            ])
        ]
        
        for section_name, color_key, items in menu_items:
            # Section header
            print(f"{colors[color_key]}╭─ {section_name} {'─' * (75 - len(section_name))}╮")
            
            for key, name, icon_key, description in items:
                icon = EnhancedTerminalUI.ICONS.get(icon_key, '•')
                key_display = f"[{key}]"
                
                # Enhanced item display with description
                print(f"│ {colors['accent']}{key_display:<4} {icon} {Fore.WHITE}{name:<25} "
                      f"{colors['dim']}{description:<41} │")
            
            print(f"{colors[color_key]}╰{'─' * 77}╯")
            print()
        
        # Input prompt with animation
        prompt = f"{colors['accent']}{EnhancedTerminalUI.ICONS['arrow']} Select option: {Fore.WHITE}"
        return input(prompt).strip().upper()
    
    @staticmethod
    def enhanced_log(message, level='info', browser_id=None, theme="neon"):
        """Enhanced logging with better visuals"""
        colors = EnhancedTerminalUI.THEMES[theme]
        timestamp = time.strftime('%H:%M:%S')
        
        # Enhanced level indicators
        level_config = {
            'info': (EnhancedTerminalUI.ICONS['info'], colors['primary']),
            'success': (EnhancedTerminalUI.ICONS['success'], colors['success']),
            'warning': (EnhancedTerminalUI.ICONS['warning'], colors['warning']),
            'error': (EnhancedTerminalUI.ICONS['error'], colors['error']),
            'alert': (EnhancedTerminalUI.ICONS['fire'], colors['accent']),
            'ticket': (EnhancedTerminalUI.ICONS['ticket'], colors['success']),
            'browser': (EnhancedTerminalUI.ICONS['browser'], colors['secondary']),
            'speed': (EnhancedTerminalUI.ICONS['speed'], colors['accent']),
            'money': (EnhancedTerminalUI.ICONS['money'], colors['success'])
        }
        
        icon, color = level_config.get(level, ('•', colors['dim']))
        
        # Browser indicator
        browser_str = f"[B{browser_id}]" if browser_id is not None else "    "
        
        # Enhanced log format with better spacing
        log_line = (
            f"\r{colors['dim']}[{timestamp}] "
            f"{colors['secondary']}{browser_str} "
            f"{icon} "
            f"{color}{message:<80}"
            f"{Style.RESET_ALL}"
        )
        
        # Clear line and print
        print(f"\r{' ' * 120}\r{log_line}", flush=True)
    
    @staticmethod
    def enhanced_live_stats(stats, theme="neon"):
        """Enhanced live statistics display"""
        colors = EnhancedTerminalUI.THEMES[theme]
        
        # Clear previous stats area
        print(f"\033[s", end='')  # Save cursor
        print(f"\033[15;0H", end='')  # Move to stats area
        
        # Stats header
        print(f"\n{colors['primary']}╔══ LIVE HUNTING STATISTICS {'═' * 48}══╗")
        
        # Runtime and performance
        runtime = stats.get('runtime', '00:00:00')
        cpm = stats.get('checks_per_minute', 0)
        best_cpm = stats.get('best_cpm', 0)
        
        print(f"║ {EnhancedTerminalUI.ICONS['time']} Runtime: {colors['accent']}{runtime:<12} "
              f"{EnhancedTerminalUI.ICONS['speed']} CPM: {colors['success']}{cpm:<6} "
              f"{EnhancedTerminalUI.ICONS['trophy']} Best: {colors['success']}{best_cpm:<6} ║")
        
        # Ticket statistics
        checks = stats.get('total_checks', 0)
        found = stats.get('unique_tickets_seen', 0)
        secured = stats.get('tickets_secured', 0)
        errors = stats.get('errors_encountered', 0)
        
        print(f"║ {EnhancedTerminalUI.ICONS['check']} Checks: {colors['secondary']}{checks:<10} "
              f"{EnhancedTerminalUI.ICONS['ticket']} Found: {colors['warning']}{found:<6} "
              f"{EnhancedTerminalUI.ICONS['success']} Secured: {colors['success']}{secured:<4} ║")
        
        # Browser status with visual indicators
        browsers = stats.get('browser_status', {})
        if browsers:
            print(f"║{'─' * 76}║")
            print(f"║ BROWSER STATUS:                                                            ║")
            
            for bid, status in browsers.items():
                status_icon = EnhancedTerminalUI.ICONS['check'] if status['active'] else EnhancedTerminalUI.ICONS['cross']
                status_color = colors['success'] if status['active'] else colors['error']
                cpm_val = status.get('cpm', 0)
                
                # Progress bar for CPM
                max_cpm = 300
                bar_width = 20
                filled = int((cpm_val / max_cpm) * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                
                print(f"║   {status_color}{status_icon} Browser {bid}: "
                      f"{colors['accent']}[{bar}] "
                      f"{colors['secondary']}{cpm_val:>3} CPM "
                      f"{colors['dim']}({status.get('last_check', 'Never')})          ║")
        
        # Ticket breakdown
        tickets_found = stats.get('tickets_found', {})
        if tickets_found:
            print(f"║{'─' * 76}║")
            print(f"║ TICKETS BY TYPE:                                                           ║")
            
            for category, count in tickets_found.items():
                bar_width = 30
                max_count = max(tickets_found.values()) if tickets_found else 1
                filled = int((count / max_count) * bar_width)
                bar = "▓" * filled + "░" * (bar_width - filled)
                
                cat_display = category.upper()[:10].ljust(10)
                print(f"║   {colors['accent']}{cat_display} "
                      f"{colors['secondary']}[{bar}] "
                      f"{colors['success']}{count:>3}                  ║")
        
        print(f"{colors['primary']}╚{'═' * 76}╝")
        print(f"\033[u", end='', flush=True)  # Restore cursor
    
    @staticmethod
    def show_notification(message, notification_type="info", theme="neon"):
        """Display enhanced notification banners"""
        colors = EnhancedTerminalUI.THEMES[theme]
        
        type_config = {
            'success': (EnhancedTerminalUI.ICONS['success'], colors['success'], "SUCCESS"),
            'error': (EnhancedTerminalUI.ICONS['error'], colors['error'], "ERROR"),
            'alert': (EnhancedTerminalUI.ICONS['fire'], colors['accent'], "ALERT"),
            'ticket': (EnhancedTerminalUI.ICONS['ticket'], colors['success'], "TICKET FOUND")
        }
        
        icon, color, label = type_config.get(notification_type, ('•', colors['primary'], "INFO"))
        
        # Create notification box
        width = 60
        print(f"\n{color}╔{'═' * width}╗")
        print(f"║ {icon} {label:^{width-4}} {icon} ║")
        print(f"║{' ' * width}║")
        
        # Word wrap message
        words = message.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= width - 4:
                line += word + " "
            else:
                print(f"║  {line:<{width-4}}  ║")
                line = word + " "
        if line:
            print(f"║  {line:<{width-4}}  ║")
        
        print(f"║{' ' * width}║")
        print(f"╚{'═' * width}╝{Style.RESET_ALL}\n")

# Example usage
if __name__ == "__main__":
    # Demo the enhanced menu
    settings = {
        "theme": "neon",
        "target_url": "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388",
        "num_browsers": 2,
        "ticket_types": ["prato_a", "prato_b"],
        "auto_buy": True
    }
    
    # Show main menu
    choice = EnhancedTerminalUI.enhanced_main_menu(settings)
    print(f"\nYou selected: {choice}")
    
    # Demo some logs
    time.sleep(1)
    EnhancedTerminalUI.enhanced_log("Bot initialized successfully", "success")
    time.sleep(0.5)
    EnhancedTerminalUI.enhanced_log("Starting browser 0...", "browser", 0)
    time.sleep(0.5)
    EnhancedTerminalUI.enhanced_log("Found 3 tickets!", "ticket", 0)
    time.sleep(0.5)
    EnhancedTerminalUI.enhanced_log("Connection error - retrying...", "warning", 1)
    
    # Demo notification
    time.sleep(1)
    EnhancedTerminalUI.show_notification(
        "New ticket found: PRATO A - €150 - Sector 5, Row 12",
        "ticket"
    )
    
    # Demo live stats
    stats = {
        'runtime': '00:15:32',
        'checks_per_minute': 145,
        'best_cpm': 230,
        'total_checks': 2340,
        'unique_tickets_seen': 12,
        'tickets_secured': 2,
        'errors_encountered': 3,
        'browser_status': {
            0: {'active': True, 'cpm': 165, 'last_check': '2s ago'},
            1: {'active': True, 'cpm': 80, 'last_check': '1s ago'}
        },
        'tickets_found': {
            'prato_a': 4,
            'prato_b': 3,
            'settore': 5
        }
    }
    
    EnhancedTerminalUI.enhanced_live_stats(stats)