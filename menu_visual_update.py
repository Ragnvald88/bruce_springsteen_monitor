#!/usr/bin/env python3
"""
Visual Menu and Logging Updates for FanSale Ultimate Bot
This file contains the enhanced implementations to replace existing methods
"""

# Enhanced main_menu method to replace the existing one
def enhanced_main_menu(settings):
    """Enhanced main menu with better visuals and navigation"""
    theme = settings.get("theme", "cyberpunk")
    colors = TerminalUI.THEMES[theme]
    TerminalUI.print_header(theme)
    
    # Status bar with current configuration
    print(colors["accent"] + "┌─ CURRENT CONFIGURATION " + "─" * 54 + "┐")
    
    # Event info
    url = settings.get("target_url", DEFAULT_TARGET_URL)
    if "bruce-springsteen" in url:
        event_name = "🎸 Bruce Springsteen Concert"
    else:
        event_name = "🎫 Custom Event"
    
    # Configuration summary
    browsers = settings.get('num_browsers', 2)
    ticket_types = settings.get('ticket_types', ['all'])
    auto_buy = settings.get('auto_buy', False)
    max_tickets = settings.get('max_tickets', 2)
    
    print(f"│ Event: {colors['success']}{event_name:<65} │")
    print(f"│ Setup: {colors['secondary']}{browsers} browsers • {max_tickets} max tickets • "
          f"{'Auto-buy ON' if auto_buy else 'Manual mode':<28} │")
    print(f"│ Types: {colors['accent']}{', '.join(ticket_types):<65} │")
    print(colors["accent"] + "└" + "─" * 77 + "┘\n")
    
    # Menu sections with better organization
    print(colors["primary"] + "╔══ QUICK START " + "═" * 62 + "╗")
    print(f"║ {colors['accent']}[1] {Fore.WHITE}🎯 START HUNTING      "
          f"{colors['secondary']}Begin ticket hunt with current settings{' '*18} ║")
    print(f"║ {colors['accent']}[2] {Fore.WHITE}⚡ QUICK SETTINGS     "
          f"{colors['secondary']}Fast configuration (browsers, speed, auto-buy){' '*11} ║")
    print(colors["primary"] + "╠══ CONFIGURATION " + "═" * 60 + "╣")
    print(f"║ {colors['accent']}[3] {Fore.WHITE}⚙️  ADVANCED SETTINGS  "
          f"{colors['secondary']}Detailed bot configuration and preferences{' '*15} ║")
    print(f"║ {colors['accent']}[4] {Fore.WHITE}👤 PROFILE MANAGER    "
          f"{colors['secondary']}Save and load hunting profiles{' '*27} ║")
    print(f"║ {colors['accent']}[5] {Fore.WHITE}🤖 AUTO-BUY RULES     "
          f"{colors['secondary']}Configure automatic purchase rules{' '*23} ║")
    print(colors["primary"] + "╠══ ANALYTICS " + "═" * 64 + "╣")
    print(f"║ {colors['accent']}[6] {Fore.WHITE}📊 LIVE DASHBOARD     "
          f"{colors['secondary']}Real-time hunting statistics (demo){' '*22} ║")
    print(f"║ {colors['accent']}[7] {Fore.WHITE}📈 STATISTICS         "
          f"{colors['secondary']}View historical performance data{' '*25} ║")
    print(f"║ {colors['accent']}[8] {Fore.WHITE}🏆 PERFORMANCE        "
          f"{colors['secondary']}Detailed analytics and insights{' '*26} ║")
    print(colors["primary"] + "╠══ CUSTOMIZATION " + "═" * 60 + "╣")
    print(f"║ {colors['accent']}[9] {Fore.WHITE}🎨 CHANGE THEME       "
          f"{colors['secondary']}Customize visual appearance{' '*30} ║")
    print(f"║ {colors['accent']}[0] {Fore.WHITE}🔔 NOTIFICATIONS      "
          f"{colors['secondary']}Configure alerts and sounds{' '*30} ║")
    print(colors["primary"] + "╠══ HELP & MORE " + "═" * 62 + "╣")
    print(f"║ {colors['accent']}[H] {Fore.WHITE}📖 HELP & GUIDE       "
          f"{colors['secondary']}Learn how to use the bot effectively{' '*21} ║")
    print(f"║ {colors['accent']}[A] {Fore.WHITE}💎 ABOUT              "
          f"{colors['secondary']}Information about FanSale Ultimate{' '*23} ║")
    print(f"║ {colors['accent']}[X] {Fore.WHITE}🚪 EXIT               "
          f"{colors['secondary']}Close the application{' '*36} ║")
    print(colors["primary"] + "╚" + "═" * 77 + "╝\n")
    
    return input(colors["accent"] + "➤ Select option: " + Fore.WHITE).strip().upper()

# Enhanced log method with better visuals
def enhanced_log(self, message, level='info', browser_id=None):
    """Enhanced logging with improved visuals and emojis"""
    with self.display_lock:
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        # Enhanced level indicators with better emojis
        level_config = {
            'info': ('💡', colors['primary'], 'INFO'),
            'success': ('✨', colors['success'], 'SUCCESS'),
            'warning': ('⚡', colors['warning'], 'WARNING'),
            'error': ('💥', colors['error'], 'ERROR'),
            'alert': ('🔥', colors['accent'] + Style.BRIGHT, 'ALERT'),
            'ticket': ('🎫', colors['success'] + Style.BRIGHT, 'TICKET'),
            'check': ('🔍', colors['secondary'], 'CHECK'),
            'browser': ('🌐', colors['primary'], 'BROWSER'),
            'stealth': ('🥷', colors['secondary'] + Style.DIM, 'STEALTH'),
            'speed': ('🚀', colors['accent'], 'SPEED'),
            'money': ('💰', colors['success'], 'PURCHASE'),
            'captcha': ('🔐', colors['warning'], 'CAPTCHA'),
            'profile': ('👤', colors['secondary'], 'PROFILE'),
            'stats': ('📊', colors['primary'], 'STATS')
        }
        
        icon, color, label = level_config.get(level, ('•', colors['secondary'], 'LOG'))
        
        # Browser indicator with color
        if browser_id is not None:
            browser_str = f"{colors['cyan']}[B{browser_id}]{Style.RESET_ALL}"
        else:
            browser_str = "    "
        
        # Format message with proper padding
        max_msg_length = 70
        if len(message) > max_msg_length:
            message = message[:max_msg_length-3] + "..."
        
        # Build log line with consistent formatting
        log_parts = [
            f"{colors['secondary'] + Style.DIM}[{timestamp}]{Style.RESET_ALL}",
            browser_str,
            f"{icon}",
            f"{color}[{label:>7}]{Style.RESET_ALL}",
            f"{color}{message}{Style.RESET_ALL}"
        ]
        
        log_line = " ".join(log_parts)
        
        # Clear line and print
        print(f"\r{' ' * 120}\r{log_line}", flush=True)
        
        # Add to notification queue if important
        if level in ['alert', 'ticket', 'error', 'success']:
            if hasattr(self, 'notifications'):
                self.notifications.notify(message, level, browser_id)

# Enhanced live stats display
def enhanced_display_live_stats(self):
    """Display enhanced live statistics with better visuals"""
    theme = self.settings.get("theme", "cyberpunk")
    colors = TerminalUI.THEMES[theme]
    
    while not self.shutdown_event.is_set():
        try:
            stats = self.stats.get_stats()
            runtime = self.stats.get_runtime()
            
            with self.display_lock:
                # Position cursor
                print(f"\033[s", end='')
                print(f"\033[15;0H", end='')
                
                # Enhanced stats box
                print(f"\n{colors['primary']}╔{'═'*78}╗")
                print(f"║{colors['accent'] + Style.BRIGHT} {'📊 LIVE HUNTING STATISTICS'.center(76)} {colors['primary']}║")
                print(f"╠{'═'*38}╦{'═'*39}╣")
                
                # Performance metrics
                print(f"║ {colors['secondary']}⏱️  Runtime: {colors['accent']}{runtime:<10} "
                      f"{colors['secondary']}🌐 Browsers: {colors['accent']}{stats['active_browsers']:<3} "
                      f"║ {colors['secondary']}🚀 CPM: {colors['success']}{stats['checks_per_minute']:<5} "
                      f"{colors['secondary']}🏆 Best: {colors['success']}{stats['best_cpm']:<5} ║")
                
                # Ticket metrics
                print(f"║ {colors['secondary']}🔍 Checks: {colors['primary']}{stats['total_checks']:<8} "
                      f"{colors['secondary']}👀 Found: {colors['warning']}{stats['unique_tickets_seen']:<5} "
                      f"║ {colors['secondary']}✅ Secured: {colors['success'] + Style.BRIGHT}{stats['tickets_secured']:<3} "
                      f"{colors['secondary']}❌ Errors: {colors['error']}{stats['errors_encountered']:<5} ║")
                
                print(f"╠{'═'*38}╩{'═'*39}╣")
                
                # Ticket breakdown with progress bars
                if stats['tickets_found']:
                    total_found = sum(stats['tickets_found'].values())
                    print(f"║ {colors['accent']}TICKETS BY CATEGORY ({total_found} total):{' '*46} ║")
                    
                    for category, count in sorted(stats['tickets_found'].items(), 
                                                key=lambda x: x[1], reverse=True):
                        # Create progress bar
                        bar_width = 25
                        max_count = max(stats['tickets_found'].values())
                        filled = int((count / max_count) * bar_width) if max_count > 0 else 0
                        bar = "█" * filled + "░" * (bar_width - filled)
                        
                        cat_display = category.upper()[:10].ljust(10)
                        count_str = f"{count:>3}"
                        
                        print(f"║   {colors['accent']}{cat_display} "
                              f"{colors['secondary']}[{bar}] "
                              f"{colors['success']}{count_str} "
                              f"{colors['secondary']}({count/total_found*100:>4.1f}%){' '*15} ║")
                
                # Recent activity
                recent_tickets = self.stats.get_ticket_history()[-3:]
                if recent_tickets:
                    print(f"╠{'═'*78}╣")
                    print(f"║ {colors['accent']}RECENT ACTIVITY:{' '*61} ║")
                    for ticket in recent_tickets:
                        time_str = ticket['time']
                        cat_str = ticket['category'].upper()[:8]
                        price_str = f"€{ticket['info'].get('price', '?')}" if ticket['info'].get('price') else "€?"
                        info_line = f"[{time_str}] {cat_str} - {price_str}"
                        print(f"║   {colors['success']}🎫 {info_line:<71} ║")
                
                # Browser status indicators
                print(f"╠{'═'*78}╣")
                print(f"║ {colors['accent']}BROWSER STATUS:{' '*62} ║")
                
                for i in range(self.settings.get('num_browsers')):
                    if i < len(self.browsers):
                        status = "🟢 Active"
                        color = colors['success']
                    else:
                        status = "🔴 Offline"
                        color = colors['error']
                    
                    print(f"║   {color}Browser {i}: {status:<65} ║")
                
                print(f"╚{'═'*78}╝")
                print(f"\033[u", end='', flush=True)
            
            time.sleep(1)
        except:
            time.sleep(1)

# Enhanced quick settings menu
def enhanced_quick_settings_menu(settings):
    """Enhanced quick settings with visual feedback"""
    theme = settings.get("theme", "cyberpunk")
    colors = TerminalUI.THEMES[theme]
    TerminalUI.print_header(theme)
    
    print(colors["accent"] + "⚡ QUICK SETTINGS - INTERACTIVE CONFIGURATION\n")
    
    # Visual representation of current settings
    browsers = settings.get('num_browsers')
    max_tickets = settings.get('max_tickets')
    auto_buy = settings.get('auto_buy')
    sound = settings.get('sound_alerts')
    min_wait = settings.get('min_wait')
    max_wait = settings.get('max_wait')
    
    # Browser count with visual indicator
    browser_bar = "█" * browsers + "░" * (8 - browsers)
    print(f"{colors['primary']}🌐 Browsers: {colors['accent']}[{browser_bar}] {browsers}/8")
    print(f"   {colors['secondary']}[+] Increase  [-] Decrease")
    
    # Max tickets with visual
    ticket_bar = "█" * min(max_tickets, 10) + "░" * (10 - min(max_tickets, 10))
    print(f"\n{colors['primary']}🎫 Max Tickets: {colors['accent']}[{ticket_bar}] {max_tickets}")
    print(f"   {colors['secondary']}[SHIFT +/-] Adjust")
    
    # Speed settings with visual range
    print(f"\n{colors['primary']}🚀 Check Speed: {colors['accent']}{min_wait}s - {max_wait}s")
    print(f"   {colors['secondary']}[S] Configure speed")
    
    # Toggle switches with visual indicators
    auto_indicator = "🟢 ON " if auto_buy else "🔴 OFF"
    sound_indicator = "🔊 ON " if sound else "🔇 OFF"
    
    print(f"\n{colors['primary']}🤖 Auto-Buy: {colors['accent']}{auto_indicator}")
    print(f"   {colors['secondary']}[A] Toggle")
    
    print(f"\n{colors['primary']}🔔 Sound Alerts: {colors['accent']}{sound_indicator}")
    print(f"   {colors['secondary']}[M] Toggle")
    
    print(f"\n{colors['success']}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"{colors['accent']}[Enter] 🎯 Start Hunting with these settings")
    print(f"{colors['secondary']}[ESC]   ← Back to Main Menu\n")
    
    return input(colors["accent"] + "➤ Action: " + Fore.WHITE).strip()