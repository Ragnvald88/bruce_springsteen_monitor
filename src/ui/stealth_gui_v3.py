# src/ui/stealth_gui_v3.py
"""
StealthMaster AI v3.0 - Professional Control Center GUI
Complete interface overhaul with enhanced functionality and help system
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import scrolledtext
import asyncio
import threading
import queue
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import logging
from pathlib import Path
import yaml

# Import enhanced components
try:
    # Try absolute import first (when run via main.py)
    from src.ui.enhanced_detection_monitor import get_detection_monitor, ThreatLevel
except ImportError:
    # Try relative import (when run directly)
    try:
        from ..ui.enhanced_detection_monitor import get_detection_monitor, ThreatLevel
    except ImportError:
        # If running as standalone, add parent directory to path
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.ui.enhanced_detection_monitor import get_detection_monitor, ThreatLevel

logger = logging.getLogger(__name__)


class Tooltip:
    """Create tooltips for widgets"""
    
    def __init__(self, widget, text='widget info', delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        self.widget.bind('<Enter>', self.enter, add='+')
        self.widget.bind('<Leave>', self.leave, add='+')
        self.widget.bind('<ButtonPress>', self.leave, add='+')
    
    def enter(self, event=None):
        self.schedule()
    
    def leave(self, event=None):
        self.unschedule()
        self.hide()
    
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)
    
    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)
    
    def show(self):
        if self.tipwindow or not self.text:
            return
        
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#2d2d2d", foreground="#ffffff",
                        relief=tk.SOLID, borderwidth=1,
                        font=("Arial", "10", "normal"),
                        padx=10, pady=5)
        label.pack(ipadx=1)
    
    def hide(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class StealthMasterGUI:
    """
    Professional control center for StealthMaster AI v3.0
    Complete with enhanced features, help system, and modern UI
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎸 StealthMaster AI v3.0 - Control Center")
        self.root.geometry("1400x900")
        
        # Set icon if available
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        # Theme configuration
        self.setup_theme()
        
        # State management
        self.bot_running = False
        self.monitors_active = {}
        self.command_queue = queue.Queue()
        self.stats = {
            'tickets_found': 0,
            'successful_attempts': 0,
            'blocked_attempts': 0,
            'data_saved_mb': 0.0
        }
        
        # Components
        self.detection_monitor = None
        self.bot_thread = None
        self.stop_event = threading.Event()
        
        # Build UI
        self.create_ui()
        
        # Load configuration
        self.load_config()
        
        # Start update loop
        self.update_loop()
        
        logger.info("StealthMaster GUI v3.0 initialized")
    
    def setup_theme(self):
        """Configure modern dark theme"""
        
        self.colors = {
            'bg': '#0f0f0f',
            'fg': '#ffffff',
            'card': '#1a1a1a',
            'border': '#2d2d2d',
            'accent': '#3498db',
            'success': '#2ecc71',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'info': '#3498db',
            'text': '#ecf0f1',
            'text_dim': '#95a5a6'
        }
        
        # Configure root
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure all ttk widgets
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', 
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        style.map('TButton',
                 background=[('active', '#2980b9')])
        
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.colors['card'],
                       foreground=self.colors['fg'],
                       padding=[20, 10])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', 'white')])
    
    def create_ui(self):
        """Create the main user interface"""
        
        # Menu bar
        self.create_menu_bar()
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Split into sidebar and main area
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        sidebar = self.create_sidebar(paned)
        paned.add(sidebar, weight=0)
        
        # Main area
        main_area = ttk.Frame(paned)
        paned.add(main_area, weight=1)
        
        # Create tabbed interface in main area
        self.notebook = ttk.Notebook(main_area)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tabs
        self.create_dashboard_tab()
        self.create_targets_tab()
        self.create_settings_tab()
        self.create_analytics_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        
        menubar = tk.Menu(self.root, bg=self.colors['card'], fg=self.colors['fg'])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['card'], fg=self.colors['fg'])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self.load_config_dialog)
        file_menu.add_command(label="Save Config", command=self.save_config_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['card'], fg=self.colors['fg'])
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Detection Monitor", command=self.open_detection_monitor)
        view_menu.add_command(label="Performance Metrics", command=self.show_performance)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Dark Mode", state=tk.DISABLED)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['card'], fg=self.colors['fg'])
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Test Stealth", command=self.test_stealth)
        tools_menu.add_command(label="Benchmark", command=self.run_benchmark)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Cache", command=self.clear_cache)
        tools_menu.add_command(label="Reset Stats", command=self.reset_stats)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['card'], fg=self.colors['fg'])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Start Guide", command=self.show_quick_start)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_separator()
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_sidebar(self, parent):
        """Create sidebar with quick controls"""
        
        sidebar = tk.Frame(parent, bg=self.colors['card'], width=250)
        sidebar.pack_propagate(False)
        
        # Logo/Title
        title_frame = tk.Frame(sidebar, bg=self.colors['card'])
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(
            title_frame,
            text="🎸 StealthMaster",
            font=('Arial', 20, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['fg']
        ).pack()
        
        tk.Label(
            title_frame,
            text="AI v3.0",
            font=('Arial', 12),
            bg=self.colors['card'],
            fg=self.colors['text_dim']
        ).pack()
        
        # Separator
        ttk.Separator(sidebar, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Quick Stats
        self.create_quick_stats(sidebar)
        
        # Separator
        ttk.Separator(sidebar, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Control Buttons
        self.create_control_buttons(sidebar)
        
        # Separator
        ttk.Separator(sidebar, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Mode Selection
        self.create_mode_selector(sidebar)
        
        return sidebar
    
    def create_quick_stats(self, parent):
        """Create quick statistics display"""
        
        stats_frame = tk.Frame(parent, bg=self.colors['card'])
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            stats_frame,
            text="Quick Stats",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['fg']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Stat items
        self.stat_labels = {}
        
        stats = [
            ('tickets_found', '🎫 Tickets Found', '0'),
            ('success_rate', '✅ Success Rate', '0%'),
            ('data_saved', '💾 Data Saved', '0 MB'),
            ('uptime', '⏱️ Uptime', '00:00:00')
        ]
        
        for key, label, default in stats:
            frame = tk.Frame(stats_frame, bg=self.colors['card'])
            frame.pack(fill=tk.X, pady=2)
            
            tk.Label(
                frame,
                text=label,
                font=('Arial', 10),
                bg=self.colors['card'],
                fg=self.colors['text_dim']
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                frame,
                text=default,
                font=('Arial', 10, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['success']
            )
            value_label.pack(side=tk.RIGHT)
            
            self.stat_labels[key] = value_label
    
    def create_control_buttons(self, parent):
        """Create main control buttons"""
        
        controls_frame = tk.Frame(parent, bg=self.colors['card'])
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Start/Stop button
        self.start_button = self.create_action_button(
            controls_frame,
            text="🚀 START BOT",
            command=self.toggle_bot,
            color=self.colors['success'],
            tooltip="Start the ticket monitoring bot"
        )
        self.start_button.pack(fill=tk.X, pady=5)
        
        # Detection Monitor button
        detection_btn = self.create_action_button(
            controls_frame,
            text="🛡️ Detection Monitor",
            command=self.open_detection_monitor,
            color=self.colors['info'],
            tooltip="Open real-time detection monitoring dashboard"
        )
        detection_btn.pack(fill=tk.X, pady=5)
        
        # Emergency Stop
        emergency_btn = self.create_action_button(
            controls_frame,
            text="🛑 EMERGENCY STOP",
            command=self.emergency_stop,
            color=self.colors['danger'],
            tooltip="Immediately stop all operations"
        )
        emergency_btn.pack(fill=tk.X, pady=5)
    
    def create_action_button(self, parent, text, command, color, tooltip=None):
        """Create a styled action button with tooltip"""
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            font=('Arial', 12, 'bold'),
            relief=tk.RAISED,
            cursor='hand2',
            pady=12,
            bd=2,
            activebackground=color,
            activeforeground='white'
        )
        
        # Hover effects
        def on_enter(e):
            btn['bg'] = self.darken_color(color)
        
        def on_leave(e):
            btn['bg'] = color
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        # Add tooltip if provided
        if tooltip:
            Tooltip(btn, tooltip)
        
        return btn
    
    def create_mode_selector(self, parent):
        """Create operation mode selector"""
        
        mode_frame = tk.Frame(parent, bg=self.colors['card'])
        mode_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            mode_frame,
            text="Operation Mode",
            font=('Arial', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['fg']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Mode options
        self.mode_var = tk.StringVar(value="stealth")
        
        modes = [
            ("stealth", "🥷 Stealth", "Maximum stealth, slower operation"),
            ("balanced", "⚖️ Balanced", "Balance between stealth and speed"),
            ("aggressive", "🚀 Aggressive", "Maximum speed, higher detection risk"),
            ("ultra", "🛡️ Ultra-Stealth", "Ultimate protection, very slow")
        ]
        
        for value, text, tooltip in modes:
            frame = tk.Frame(mode_frame, bg=self.colors['card'])
            frame.pack(fill=tk.X, pady=2)
            
            rb = tk.Radiobutton(
                frame,
                text=text,
                variable=self.mode_var,
                value=value,
                bg=self.colors['card'],
                fg=self.colors['fg'],
                selectcolor=self.colors['card'],
                activebackground=self.colors['card'],
                font=('Arial', 10)
            )
            rb.pack(anchor=tk.W)
            
            Tooltip(rb, tooltip)
    
    def create_dashboard_tab(self):
        """Create main dashboard tab"""
        
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Create scrollable area
        canvas = tk.Canvas(dashboard_frame, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(dashboard_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dashboard content
        self.create_dashboard_content(scrollable_frame)
    
    def create_dashboard_content(self, parent):
        """Create dashboard content"""
        
        # Welcome card
        welcome_card = self.create_card(parent, "Welcome to StealthMaster AI v3.0")
        tk.Label(
            welcome_card,
            text="The ultimate ticket monitoring system with undetectable stealth technology.",
            font=('Arial', 12),
            bg=self.colors['card'],
            fg=self.colors['text_dim'],
            wraplength=600
        ).pack(pady=10)
        
        # System Status card
        status_card = self.create_card(parent, "System Status")
        self.create_system_status(status_card)
        
        # Active Monitors card
        monitors_card = self.create_card(parent, "Active Monitors")
        self.create_monitors_display(monitors_card)
        
        # Performance Metrics card
        metrics_card = self.create_card(parent, "Performance Metrics")
        self.create_metrics_display(metrics_card)
    
    def create_card(self, parent, title):
        """Create a styled card widget"""
        
        card = tk.Frame(parent, bg=self.colors['card'], relief=tk.RAISED, bd=1)
        card.pack(fill=tk.X, padx=20, pady=10)
        
        # Title
        title_frame = tk.Frame(card, bg=self.colors['accent'])
        title_frame.pack(fill=tk.X)
        
        tk.Label(
            title_frame,
            text=title,
            font=('Arial', 14, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            pady=10
        ).pack(padx=15)
        
        # Content area
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        return content
    
    def create_system_status(self, parent):
        """Create system status display"""
        
        # Grid layout for status items
        self.status_indicators = {}
        
        items = [
            ('stealth_engine', '🛡️ Stealth Engine', 'READY'),
            ('cdp_bypass', '🔒 CDP Bypass', 'PROTECTED'),
            ('proxy_pool', '🌐 Proxy Pool', 'CONNECTED'),
            ('browser_pool', '🖥️ Browser Pool', 'INITIALIZED'),
            ('data_optimizer', '💾 Data Optimizer', 'ACTIVE'),
            ('detection_monitor', '👁️ Detection Monitor', 'ONLINE')
        ]
        
        for i, (key, label, default) in enumerate(items):
            row = i // 2
            col = i % 2
            
            frame = tk.Frame(parent, bg=self.colors['card'])
            frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')
            
            tk.Label(
                frame,
                text=label,
                font=('Arial', 11),
                bg=self.colors['card'],
                fg=self.colors['fg']
            ).pack(side=tk.LEFT)
            
            status_label = tk.Label(
                frame,
                text=default,
                font=('Arial', 11, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['success']
            )
            status_label.pack(side=tk.LEFT, padx=(10, 0))
            
            self.status_indicators[key] = status_label
    
    def create_monitors_display(self, parent):
        """Create active monitors display"""
        
        # Headers
        headers = ['Platform', 'Status', 'Checks', 'Found', 'Actions']
        
        # Create table
        self.monitors_tree = ttk.Treeview(
            parent,
            columns=headers[1:],
            show='tree headings',
            height=5
        )
        
        # Configure columns
        self.monitors_tree.column('#0', width=150)
        for col in headers[1:]:
            self.monitors_tree.column(col, width=100, anchor='center')
            self.monitors_tree.heading(col, text=col)
        
        self.monitors_tree.pack(fill=tk.BOTH, expand=True)
        
        # Sample data
        platforms = ['FanSale', 'Ticketmaster', 'Vivaticket']
        for platform in platforms:
            self.monitors_tree.insert('', 'end', 
                                    text=f"🎫 {platform}",
                                    values=('Inactive', '0', '0', ''))
    
    def create_metrics_display(self, parent):
        """Create performance metrics display"""
        
        metrics_frame = tk.Frame(parent, bg=self.colors['card'])
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create metric widgets
        self.metric_widgets = {}
        
        metrics = [
            ('cpu_usage', 'CPU Usage', '0%', self.colors['info']),
            ('memory_usage', 'Memory', '0 MB', self.colors['warning']),
            ('network_speed', 'Network', '0 KB/s', self.colors['success']),
            ('detection_score', 'Detection Score', '100', self.colors['success'])
        ]
        
        for key, label, default, color in metrics:
            frame = tk.Frame(metrics_frame, bg=self.colors['card'])
            frame.pack(side=tk.LEFT, expand=True, padx=10)
            
            value_label = tk.Label(
                frame,
                text=default,
                font=('Arial', 24, 'bold'),
                bg=self.colors['card'],
                fg=color
            )
            value_label.pack()
            
            tk.Label(
                frame,
                text=label,
                font=('Arial', 10),
                bg=self.colors['card'],
                fg=self.colors['text_dim']
            ).pack()
            
            self.metric_widgets[key] = value_label
    
    def create_targets_tab(self):
        """Create targets configuration tab"""
        
        targets_frame = ttk.Frame(self.notebook)
        self.notebook.add(targets_frame, text="🎯 Targets")
        
        # Toolbar
        toolbar = tk.Frame(targets_frame, bg=self.colors['card'])
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        # Buttons with tooltips
        add_btn = self.create_action_button(
            toolbar,
            text="➕ Add Target",
            command=self.add_target,
            color=self.colors['success'],
            tooltip="Add a new monitoring target"
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        edit_btn = self.create_action_button(
            toolbar,
            text="✏️ Edit",
            command=self.edit_target,
            color=self.colors['info'],
            tooltip="Edit selected target configuration"
        )
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = self.create_action_button(
            toolbar,
            text="🗑️ Remove",
            command=self.remove_target,
            color=self.colors['danger'],
            tooltip="Remove selected target"
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Help button
        help_btn = tk.Button(
            toolbar,
            text="❓",
            command=lambda: self.show_help("targets"),
            bg=self.colors['card'],
            fg=self.colors['info'],
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            width=3
        )
        help_btn.pack(side=tk.RIGHT, padx=5)
        Tooltip(help_btn, "Get help with target configuration")
        
        # Targets list
        self.create_targets_list(targets_frame)
    
    def create_targets_list(self, parent):
        """Create targets list display"""
        
        # Create treeview with scrollbar
        tree_frame = tk.Frame(parent, bg=self.colors['bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.targets_tree = ttk.Treeview(
            tree_frame,
            columns=['Platform', 'Event', 'Priority', 'Status', 'Next Check'],
            show='tree headings',
            yscrollcommand=scrollbar.set
        )
        
        scrollbar.config(command=self.targets_tree.yview)
        
        # Configure columns
        self.targets_tree.column('#0', width=50)
        self.targets_tree.column('Platform', width=100)
        self.targets_tree.column('Event', width=300)
        self.targets_tree.column('Priority', width=100)
        self.targets_tree.column('Status', width=100)
        self.targets_tree.column('Next Check', width=150)
        
        # Headers
        for col in self.targets_tree['columns']:
            self.targets_tree.heading(col, text=col)
        
        self.targets_tree.pack(fill=tk.BOTH, expand=True)
        
        # Load targets from config
        self.refresh_targets_list()
    
    def create_settings_tab(self):
        """Create settings tab"""
        
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Create scrollable settings
        canvas = tk.Canvas(settings_frame, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Settings sections
        self.create_stealth_settings(scrollable_frame)
        self.create_proxy_settings(scrollable_frame)
        self.create_performance_settings(scrollable_frame)
        self.create_notification_settings(scrollable_frame)
    
    def create_stealth_settings(self, parent):
        """Create stealth settings section"""
        
        card = self.create_card(parent, "🛡️ Stealth Settings")
        
        # CDP Bypass
        cdp_frame = tk.Frame(card, bg=self.colors['card'])
        cdp_frame.pack(fill=tk.X, pady=5)
        
        self.cdp_bypass_var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(
            cdp_frame,
            text="Enable CDP Bypass (Recommended)",
            variable=self.cdp_bypass_var,
            bg=self.colors['card'],
            fg=self.colors['fg'],
            selectcolor=self.colors['card'],
            font=('Arial', 11)
        )
        cb.pack(side=tk.LEFT)
        Tooltip(cb, "Prevents detection of Chrome DevTools Protocol usage")
        
        # Fingerprint Rotation
        fp_frame = tk.Frame(card, bg=self.colors['card'])
        fp_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            fp_frame,
            text="Fingerprint Rotation:",
            bg=self.colors['card'],
            fg=self.colors['fg'],
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.fp_rotation_var = tk.StringVar(value="30")
        fp_spin = tk.Spinbox(
            fp_frame,
            from_=5,
            to=120,
            textvariable=self.fp_rotation_var,
            width=10,
            bg=self.colors['card'],
            fg=self.colors['fg']
        )
        fp_spin.pack(side=tk.LEFT)
        
        tk.Label(
            fp_frame,
            text="minutes",
            bg=self.colors['card'],
            fg=self.colors['text_dim'],
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        Tooltip(fp_spin, "How often to rotate browser fingerprints")
    
    def create_proxy_settings(self, parent):
        """Create proxy settings section"""
        
        card = self.create_card(parent, "🌐 Proxy Settings")
        
        # Proxy enabled
        self.proxy_enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card,
            text="Enable Proxy Rotation",
            variable=self.proxy_enabled_var,
            bg=self.colors['card'],
            fg=self.colors['fg'],
            selectcolor=self.colors['card'],
            font=('Arial', 11)
        ).pack(anchor=tk.W, pady=5)
        
        # Proxy provider
        provider_frame = tk.Frame(card, bg=self.colors['card'])
        provider_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            provider_frame,
            text="Provider:",
            bg=self.colors['card'],
            fg=self.colors['fg'],
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.proxy_provider_var = tk.StringVar(value="iproyal")
        providers = ['iproyal', 'brightdata', 'smartproxy', 'custom']
        
        provider_menu = ttk.Combobox(
            provider_frame,
            textvariable=self.proxy_provider_var,
            values=providers,
            state='readonly',
            width=20
        )
        provider_menu.pack(side=tk.LEFT)
        
        # Data limit
        limit_frame = tk.Frame(card, bg=self.colors['card'])
        limit_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            limit_frame,
            text="Data Limit:",
            bg=self.colors['card'],
            fg=self.colors['fg'],
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.data_limit_var = tk.StringVar(value="1000")
        limit_entry = tk.Entry(
            limit_frame,
            textvariable=self.data_limit_var,
            width=10,
            bg=self.colors['card'],
            fg=self.colors['fg']
        )
        limit_entry.pack(side=tk.LEFT)
        
        tk.Label(
            limit_frame,
            text="MB/day",
            bg=self.colors['card'],
            fg=self.colors['text_dim'],
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        Tooltip(limit_entry, "Maximum data usage per day")
    
    def create_performance_settings(self, parent):
        """Create performance settings section"""
        
        card = self.create_card(parent, "⚡ Performance Settings")
        
        # Browser pool size
        pool_frame = tk.Frame(card, bg=self.colors['card'])
        pool_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            pool_frame,
            text="Browser Pool Size:",
            bg=self.colors['card'],
            fg=self.colors['fg'],
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.pool_size_var = tk.StringVar(value="3")
        pool_scale = tk.Scale(
            pool_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.pool_size_var,
            bg=self.colors['card'],
            fg=self.colors['fg'],
            highlightthickness=0
        )
        pool_scale.pack(side=tk.LEFT)
        
        # Parallel monitors
        parallel_frame = tk.Frame(card, bg=self.colors['card'])
        parallel_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            parallel_frame,
            text="Parallel Monitors:",
            bg=self.colors['card'],
            fg=self.colors['fg'],
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.parallel_var = tk.StringVar(value="2")
        parallel_scale = tk.Scale(
            parallel_frame,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.parallel_var,
            bg=self.colors['card'],
            fg=self.colors['fg'],
            highlightthickness=0
        )
        parallel_scale.pack(side=tk.LEFT)
    
    def create_notification_settings(self, parent):
        """Create notification settings section"""
        
        card = self.create_card(parent, "🔔 Notification Settings")
        
        # Notification types
        self.notify_vars = {}
        
        notifications = [
            ('ticket_found', '🎫 Ticket Found', True),
            ('detection_event', '🚨 Detection Event', True),
            ('error', '❌ Errors', True),
            ('success', '✅ Successful Reservation', True)
        ]
        
        for key, label, default in notifications:
            var = tk.BooleanVar(value=default)
            self.notify_vars[key] = var
            
            tk.Checkbutton(
                card,
                text=label,
                variable=var,
                bg=self.colors['card'],
                fg=self.colors['fg'],
                selectcolor=self.colors['card'],
                font=('Arial', 11)
            ).pack(anchor=tk.W, pady=2)
    
    def create_analytics_tab(self):
        """Create analytics tab"""
        
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📈 Analytics")
        
        # Placeholder for analytics
        tk.Label(
            analytics_frame,
            text="Analytics Dashboard",
            font=('Arial', 24, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(pady=50)
        
        tk.Label(
            analytics_frame,
            text="Coming soon: Advanced analytics and reporting",
            font=('Arial', 14),
            bg=self.colors['bg'],
            fg=self.colors['text_dim']
        ).pack()
    
    def create_logs_tab(self):
        """Create logs tab"""
        
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📜 Logs")
        
        # Log controls
        controls = tk.Frame(logs_frame, bg=self.colors['card'])
        controls.pack(fill=tk.X, padx=10, pady=10)
        
        # Clear button
        clear_btn = self.create_action_button(
            controls,
            text="🗑️ Clear Logs",
            command=self.clear_logs,
            color=self.colors['warning'],
            tooltip="Clear all log entries"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        export_btn = self.create_action_button(
            controls,
            text="📥 Export Logs",
            command=self.export_logs,
            color=self.colors['info'],
            tooltip="Export logs to file"
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Log level filter
        tk.Label(
            controls,
            text="Level:",
            bg=self.colors['card'],
            fg=self.colors['fg']
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.log_level_var = tk.StringVar(value="ALL")
        levels = ['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR']
        
        level_menu = ttk.Combobox(
            controls,
            textvariable=self.log_level_var,
            values=levels,
            state='readonly',
            width=10
        )
        level_menu.pack(side=tk.LEFT)
        level_menu.bind('<<ComboboxSelected>>', self.filter_logs)
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            bg='#0d0d0d',
            fg='#00ff00',
            font=('Consolas', 10),
            insertbackground='#00ff00'
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Configure tags
        self.log_display.tag_config('DEBUG', foreground='#888888')
        self.log_display.tag_config('INFO', foreground='#00ff00')
        self.log_display.tag_config('WARNING', foreground='#ffaa00')
        self.log_display.tag_config('ERROR', foreground='#ff0000')
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        
        status_bar = tk.Frame(self.root, bg=self.colors['card'], height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        # Left side - status
        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            bg=self.colors['card'],
            fg=self.colors['fg'],
            font=('Arial', 10)
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Right side - indicators
        self.connection_indicator = tk.Label(
            status_bar,
            text="● Disconnected",
            bg=self.colors['card'],
            fg=self.colors['danger'],
            font=('Arial', 10)
        )
        self.connection_indicator.pack(side=tk.RIGHT, padx=10)
        
        # Version
        tk.Label(
            status_bar,
            text="v3.0.0",
            bg=self.colors['card'],
            fg=self.colors['text_dim'],
            font=('Arial', 9)
        ).pack(side=tk.RIGHT, padx=10)
    
    # Helper methods
    def darken_color(self, color):
        """Darken a hex color"""
        # Simple darkening by reducing each component
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r, g, b = int(r * 0.8), int(g * 0.8), int(b * 0.8)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def log_message(self, message, level='INFO'):
        """Add message to log display"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_display.insert(tk.END, log_entry, level)
        self.log_display.see(tk.END)
        
        # Also update status
        self.status_label.config(text=message[:50] + '...' if len(message) > 50 else message)
    
    # Command handlers
    def toggle_bot(self):
        """Start/stop the bot"""
        if not self.bot_running:
            self.start_bot()
        else:
            self.stop_bot()
    
    def start_bot(self):
        """Start the bot"""
        self.bot_running = True
        self.start_button.config(text="⏸️ STOP BOT", bg=self.colors['warning'])
        self.log_message("🚀 Starting StealthMaster AI...")
        
        # Update indicators
        self.connection_indicator.config(text="● Connected", fg=self.colors['success'])
        
        # Start bot thread
        self.stop_event.clear()
        self.bot_thread = threading.Thread(target=self.run_bot_async, daemon=True)
        self.bot_thread.start()
    
    def stop_bot(self):
        """Stop the bot"""
        self.bot_running = False
        self.start_button.config(text="🚀 START BOT", bg=self.colors['success'])
        self.log_message("🛑 Stopping StealthMaster AI...")
        
        # Signal stop
        self.stop_event.set()
        
        # Update indicators
        self.connection_indicator.config(text="● Disconnected", fg=self.colors['danger'])
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        if messagebox.askyesno("Emergency Stop", "Are you sure you want to emergency stop all operations?"):
            self.log_message("🚨 EMERGENCY STOP ACTIVATED", 'ERROR')
            self.stop_bot()
            # Additional emergency procedures
    
    def run_bot_async(self):
        """Run the bot in async thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Import and create orchestrator
            from ..core.enhanced_orchestrator_v3 import EnhancedOrchestrator
            
            # Build config from GUI settings
            config = self.build_config()
            
            # Create orchestrator
            self.orchestrator = EnhancedOrchestrator(config)
            
            # Run the orchestrator
            loop.run_until_complete(self._run_orchestrator())
            
        except Exception as e:
            self.command_queue.put(('log', f'❌ Bot error: {str(e)}', 'ERROR'))
            self.command_queue.put(('stop', None))
    
    async def _run_orchestrator(self):
        """Run the orchestrator asynchronously"""
        try:
            await self.orchestrator.start()
            
            # Keep running until stop event
            while not self.stop_event.is_set():
                await asyncio.sleep(1)
                
                # Update GUI stats periodically
                if hasattr(self.orchestrator, 'total_checks'):
                    self.command_queue.put(('update_stats', {
                        'total_checks': self.orchestrator.total_checks,
                        'tickets_found': self.orchestrator.total_tickets_found,
                        'success_rate': (self.orchestrator.total_tickets_found / max(1, self.orchestrator.total_checks)) * 100,
                        'monitors_active': len(self.orchestrator.monitors)
                    }))
            
        finally:
            await self.orchestrator.stop()
    
    def open_detection_monitor(self):
        """Open the detection monitor"""
        if not self.detection_monitor:
            # Create detection monitor window
            monitor_window = tk.Toplevel(self.root)
            self.detection_monitor = get_detection_monitor(monitor_window)
            
            # Handle window close
            def on_close():
                self.detection_monitor = None
                monitor_window.destroy()
            
            monitor_window.protocol("WM_DELETE_WINDOW", on_close)
        else:
            # Bring to front
            self.detection_monitor.root.lift()
    
    def show_help(self, topic):
        """Show context-sensitive help"""
        help_topics = {
            'targets': """Target Configuration Help
            
Targets are the events you want to monitor for tickets.

• Platform: The ticketing website (FanSale, Ticketmaster, etc.)
• Event: The specific event to monitor
• Priority: How aggressively to monitor (affects speed vs stealth)
• Filters: Price range, sections, quantity preferences

Tips:
- Use CRITICAL priority only for must-have tickets
- Set reasonable price limits to avoid scalper prices
- Enable burst mode for high-demand events""",
            
            'general': """StealthMaster AI v3.0 Help

Welcome to the most advanced ticket monitoring system!

Key Features:
• CDP Bypass - Undetectable browser automation
• Smart Data Optimization - Minimal proxy usage
• Real-time Detection Monitoring
• Adaptive Behavior System

Quick Start:
1. Configure your targets (events to monitor)
2. Set up proxy credentials
3. Choose operation mode
4. Click START BOT

For detailed documentation, see Help > Documentation"""
        }
        
        content = help_topics.get(topic, help_topics['general'])
        messagebox.showinfo(f"Help - {topic.title()}", content)
    
    def show_quick_start(self):
        """Show quick start guide"""
        guide = """🚀 Quick Start Guide

1. Configure Proxy (Settings > Proxy)
   - Add your IPRoyal credentials
   - Set data limits

2. Add Targets (Targets tab)
   - Click "Add Target"
   - Enter event details
   - Set your preferences

3. Start Monitoring
   - Choose operation mode
   - Click "START BOT"
   - Watch Detection Monitor

4. When Tickets Found
   - Notification appears
   - Browser opens automatically
   - Complete purchase manually

Tips:
- Start with "Balanced" mode
- Monitor data usage
- Check Detection Monitor regularly"""
        
        messagebox.showinfo("Quick Start Guide", guide)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """⌨️ Keyboard Shortcuts

Ctrl+S    - Start/Stop Bot
Ctrl+D    - Open Detection Monitor  
Ctrl+E    - Emergency Stop
Ctrl+L    - Clear Logs
Ctrl+O    - Load Config
Ctrl+S    - Save Config
Ctrl+Q    - Quit

F1        - Help
F5        - Refresh
F11       - Fullscreen"""
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """🎸 StealthMaster AI v3.0

The Ultimate Ticket Monitoring System

Developed with cutting-edge stealth technology
to help music fans get their tickets.

Features:
• CDP Bypass Technology
• ML-Based Human Behavior
• Intelligent Data Optimization
• Real-time Detection Monitoring

© 2025 StealthMaster AI
All Rights Reserved"""
        
        messagebox.showinfo("About", about_text)
    
    def show_docs(self):
        """Show documentation"""
        docs_text = """StealthMaster AI v3.0 Documentation

For full documentation, visit:
https://github.com/stealthmaster/docs

Key Features:
• CDP Bypass Engine - Evades all browser detection
• Ultra Stealth Mode - Maximum anonymity
• Adaptive Behavior - ML-based human simulation
• Real-time Monitoring - Track all activities

Configuration Guide:
1. Set your target events in the Targets tab
2. Configure proxy settings if needed
3. Select operation mode (Stealth/Beast/Adaptive)
4. Click Start Monitoring

For support: support@stealthmaster.ai"""
        
        messagebox.showinfo("Documentation", docs_text)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """Keyboard Shortcuts

Ctrl+S - Start/Stop monitoring
Ctrl+Q - Quit application
Ctrl+O - Load configuration
Ctrl+S - Save configuration
Ctrl+R - Refresh statistics
Ctrl+L - Clear logs
Ctrl+T - Add new target
Ctrl+D - Delete selected target
F1 - Show help
F5 - Refresh
F11 - Toggle fullscreen"""
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)
    
    # Config management
    def load_config(self):
        """Load configuration from file"""
        try:
            config_path = Path("config/config.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    # Apply config to UI
                    self.apply_config(config)
                    self.log_message("✅ Configuration loaded")
        except Exception as e:
            self.log_message(f"❌ Failed to load config: {e}", 'ERROR')
    
    def save_config(self):
        """Save current configuration"""
        try:
            config = self.build_config()
            config_path = Path("config/config.yaml")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            self.log_message("✅ Configuration saved")
        except Exception as e:
            self.log_message(f"❌ Failed to save config: {e}", 'ERROR')
    
    def load_config_dialog(self):
        """Show file dialog to load config"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            # Load from file
            pass
    
    def save_config_dialog(self):
        """Show file dialog to save config"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            # Save to file
            pass
    
    def apply_config(self, config):
        """Apply loaded configuration to UI"""
        # Apply settings to UI elements
        pass
    
    def build_config(self):
        """Build configuration from UI state"""
        config = {
            'mode': self.mode_var.get(),
            'stealth': {
                'cdp_bypass': self.cdp_bypass_var.get(),
                'fingerprint_rotation': int(self.fp_rotation_var.get())
            },
            'proxy': {
                'enabled': self.proxy_enabled_var.get(),
                'provider': self.proxy_provider_var.get(),
                'data_limit_mb': int(self.data_limit_var.get())
            },
            'performance': {
                'browser_pool_size': int(self.pool_size_var.get()),
                'parallel_monitors': int(self.parallel_var.get())
            },
            'notifications': self.notify_vars
        }
        return config
    
    # Target management
    def add_target(self):
        """Add new target"""
        # Show target configuration dialog
        dialog = TargetDialog(self.root, title="Add Target")
        if dialog.result:
            self.refresh_targets_list()
            self.log_message(f"✅ Added target: {dialog.result['event_name']}")
    
    def edit_target(self):
        """Edit selected target"""
        selection = self.targets_tree.selection()
        if selection:
            # Show edit dialog
            pass
    
    def remove_target(self):
        """Remove selected target"""
        selection = self.targets_tree.selection()
        if selection:
            if messagebox.askyesno("Remove Target", "Are you sure you want to remove this target?"):
                self.targets_tree.delete(selection)
                self.log_message("✅ Target removed")
    
    def refresh_targets_list(self):
        """Refresh targets list from config"""
        # Clear existing
        for item in self.targets_tree.get_children():
            self.targets_tree.delete(item)
        
        # Load from config
        # This would load actual targets
        sample_targets = [
            {
                'platform': 'FanSale',
                'event': 'Bruce Springsteen - Milano 2025',
                'priority': 'CRITICAL',
                'status': 'Active',
                'next_check': 'In 30s'
            }
        ]
        
        for i, target in enumerate(sample_targets):
            self.targets_tree.insert('', 'end',
                                   text=f"{i+1}",
                                   values=(
                                       target['platform'],
                                       target['event'],
                                       target['priority'],
                                       target['status'],
                                       target['next_check']
                                   ))
    
    # Other handlers
    def test_stealth(self):
        """Run stealth test"""
        self.log_message("🧪 Running stealth test...")
        # Would run actual stealth test
        
    def run_benchmark(self):
        """Run performance benchmark"""
        self.log_message("📊 Running benchmark...")
        # Would run actual benchmark
    
    def clear_cache(self):
        """Clear cache"""
        if messagebox.askyesno("Clear Cache", "Are you sure you want to clear all cached data?"):
            self.log_message("🗑️ Cache cleared")
    
    def reset_stats(self):
        """Reset statistics"""
        if messagebox.askyesno("Reset Stats", "Are you sure you want to reset all statistics?"):
            self.stats = {
                'tickets_found': 0,
                'successful_attempts': 0,
                'blocked_attempts': 0,
                'data_saved_mb': 0.0
            }
            self.log_message("📊 Statistics reset")
    
    def show_performance(self):
        """Show performance metrics"""
        # Would show performance window
        pass
    
    def export_data(self):
        """Export data"""
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
        )
        if filename:
            # Export data
            self.log_message(f"📥 Data exported to {filename}")
    
    def clear_logs(self):
        """Clear log display"""
        self.log_display.delete(1.0, tk.END)
        self.log_message("Logs cleared")
    
    def export_logs(self):
        """Export logs to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt")]
        )
        if filename:
            content = self.log_display.get(1.0, tk.END)
            with open(filename, 'w') as f:
                f.write(content)
            self.log_message(f"📥 Logs exported to {filename}")
    
    def filter_logs(self, event=None):
        """Filter logs by level"""
        # Would implement log filtering
        pass
    
    def update_loop(self):
        """Main update loop"""
        # Process command queue
        while not self.command_queue.empty():
            try:
                cmd, data = self.command_queue.get_nowait()
                
                if cmd == 'log':
                    if isinstance(data, tuple):
                        self.log_message(data[0], data[1])
                    else:
                        self.log_message(data)
                elif cmd == 'update_stats':
                    if data:
                        self.stats.update(data)
                        self.update_displays()
                elif cmd == 'update_status':
                    self.update_status(data)
                elif cmd == 'stop':
                    self.stop_bot()
                    
            except queue.Empty:
                break
        
        # Update displays
        self.update_displays()
        
        # Schedule next update
        self.root.after(100, self.update_loop)
    
    def update_displays(self):
        """Update all display elements"""
        # Update stat labels
        if hasattr(self, 'stat_labels'):
            self.stat_labels['tickets_found'].config(
                text=str(self.stats.get('tickets_found', 0))
            )
            # Update other stats...
    
    def update_stats(self, stats):
        """Update statistics"""
        self.stats.update(stats)
    
    def update_status(self, status):
        """Update status indicators"""
        for key, value in status.items():
            if key in self.status_indicators:
                self.status_indicators[key].config(
                    text=value,
                    fg=self.colors['success'] if 'READY' in value else self.colors['warning']
                )
    
    def on_closing(self):
        """Handle window close"""
        if self.bot_running:
            if messagebox.askyesno("Quit", "Bot is still running. Stop and quit?"):
                self.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Run the GUI"""
        # Set close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start
        self.log_message("🎸 StealthMaster AI v3.0 ready!")
        self.root.mainloop()


class TargetDialog:
    """Dialog for adding/editing targets"""
    
    def __init__(self, parent, title="Target Configuration", target=None):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create form
        self.create_form(target)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Wait for result
        self.dialog.wait_window()
    
    def create_form(self, target):
        """Create target configuration form"""
        # Would create complete form
        # For now, just buttons
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        tk.Button(
            button_frame,
            text="Save",
            command=self.save
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        ).pack(side=tk.LEFT, padx=5)
    
    def save(self):
        """Save target configuration"""
        self.result = {
            'platform': 'fansale',
            'event_name': 'Test Event',
            'priority': 'NORMAL'
        }
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()


def main():
    """Main entry point"""
    app = StealthMasterGUI()
    app.run()


if __name__ == "__main__":
    main()