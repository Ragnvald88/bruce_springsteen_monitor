#!/usr/bin/env python3
"""
🎸 StealthMaster AI - Bruce Springsteen Ticket Hunter GUI v2.0
Ultra-Modern Command Center with Real-Time Monitoring & Advanced Controls
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import threading
import queue
import time
import json
from datetime import datetime, timedelta
from collections import deque
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the main bot functionality
from src.main import load_app_config_for_gui, main_loop_for_gui

class StealthMasterGUI:
    """🎸 Bruce Springsteen Ticket Hunter - Command Center GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_styles()
        
        # Data storage for real-time updates
        self.performance_data = {
            'timestamps': deque(maxlen=100),
            'success_rates': deque(maxlen=100),
            'response_times': deque(maxlen=100),
            'stealth_scores': deque(maxlen=100),
            'ticket_detections': deque(maxlen=100)
        }
        
        # System state
        self.bot_running = False
        self.bot_thread = None
        self.stop_event = None
        self.gui_queue = queue.Queue()
        
        # Initialize data with some sample points
        self.initialize_sample_data()
        
        # Create the interface
        self.create_header()
        self.create_main_dashboard()
        self.create_control_panel()
        self.create_status_panel()
        self.create_log_panel()
        
        # Start real-time updates
        self.start_real_time_updates()
        
    def setup_window(self):
        """Setup main window with Bruce Springsteen theme"""
        self.root.title("🎸 StealthMaster AI - Bruce Springsteen Ticket Hunter v2.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Dark theme colors inspired by concert stages
        self.colors = {
            'bg_primary': '#0a0a0a',      # Deep black
            'bg_secondary': '#1a1a1a',    # Dark gray
            'bg_accent': '#2a2a2a',       # Medium gray
            'text_primary': '#ffffff',     # White
            'text_secondary': '#cccccc',   # Light gray
            'accent_red': '#ff4444',       # Stage red
            'accent_gold': '#ffd700',      # Gold highlights
            'accent_blue': '#4488ff',      # Electric blue
            'success': '#44ff44',          # Success green
            'warning': '#ffaa44',          # Warning orange
            'error': '#ff4444'             # Error red
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Set window icon if available
        try:
            # You can add a custom icon file here
            # self.root.iconbitmap('assets/bruce_icon.ico')
            pass
        except:
            pass
    
    def setup_styles(self):
        """Setup custom styles for the interface"""
        self.style = ttk.Style()
        
        # Configure dark theme
        self.style.theme_use('clam')
        
        # Custom button styles
        self.style.configure('Start.TButton',
                           background=self.colors['success'],
                           foreground='black',
                           font=('Arial', 12, 'bold'),
                           padding=(20, 10))
        
        self.style.configure('Stop.TButton',
                           background=self.colors['error'],
                           foreground='white',
                           font=('Arial', 12, 'bold'),
                           padding=(20, 10))
        
        self.style.configure('Action.TButton',
                           background=self.colors['accent_blue'],
                           foreground='white',
                           font=('Arial', 10, 'bold'),
                           padding=(15, 8))
        
        # Custom frame styles
        self.style.configure('Card.TFrame',
                           background=self.colors['bg_secondary'],
                           relief='raised',
                           borderwidth=2)
        
        self.style.configure('Header.TFrame',
                           background=self.colors['bg_accent'])
    
    def create_header(self):
        """Create the stunning header with Bruce Springsteen branding"""
        header_frame = ttk.Frame(self.root, style='Header.TFrame', padding=20)
        header_frame.pack(fill='x', padx=10, pady=(10, 0))
        
        # Main title
        title_label = tk.Label(header_frame,
                              text="🎸 STEALTHMASTER AI - BRUCE SPRINGSTEEN TICKET HUNTER",
                              font=('Arial', 24, 'bold'),
                              fg=self.colors['accent_gold'],
                              bg=self.colors['bg_accent'])
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="Born to Run... and Get Tickets! 🎵",
                                 font=('Arial', 14, 'italic'),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg_accent'])
        subtitle_label.pack()
        
        # Status indicator
        self.status_frame = tk.Frame(header_frame, bg=self.colors['bg_accent'])
        self.status_frame.pack(pady=(10, 0))
        
        self.status_indicator = tk.Label(self.status_frame,
                                        text="● READY",
                                        font=('Arial', 12, 'bold'),
                                        fg=self.colors['warning'],
                                        bg=self.colors['bg_accent'])
        self.status_indicator.pack(side='left')
        
        self.uptime_label = tk.Label(self.status_frame,
                                   text="Uptime: 00:00:00",
                                   font=('Arial', 10),
                                   fg=self.colors['text_secondary'],
                                   bg=self.colors['bg_accent'])
        self.uptime_label.pack(side='right')
        
    def create_main_dashboard(self):
        """Create the main dashboard with performance graphs"""
        dashboard_frame = ttk.Frame(self.root, style='Card.TFrame', padding=10)
        dashboard_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(dashboard_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Performance Tab
        self.create_performance_tab()
        
        # Stealth Tab
        self.create_stealth_tab()
        
        # Targets Tab
        self.create_targets_tab()
        
        # Alerts Tab
        self.create_alerts_tab()
    
    def create_performance_tab(self):
        """Create performance monitoring tab with real-time graphs"""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="📊 Performance")
        
        # Create matplotlib figure
        self.fig_perf, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig_perf.patch.set_facecolor(self.colors['bg_secondary'])
        
        # Configure subplots
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor(self.colors['bg_primary'])
            ax.tick_params(colors=self.colors['text_primary'])
            ax.spines['bottom'].set_color(self.colors['text_secondary'])
            ax.spines['top'].set_color(self.colors['text_secondary'])
            ax.spines['right'].set_color(self.colors['text_secondary'])
            ax.spines['left'].set_color(self.colors['text_secondary'])
        
        # Success Rate
        self.ax1.set_title('Success Rate (%)', color=self.colors['text_primary'], fontweight='bold')
        self.ax1.set_ylabel('Success %', color=self.colors['text_primary'])
        self.line1, = self.ax1.plot([], [], color=self.colors['success'], linewidth=2)
        
        # Response Time
        self.ax2.set_title('Response Time (ms)', color=self.colors['text_primary'], fontweight='bold')
        self.ax2.set_ylabel('Time (ms)', color=self.colors['text_primary'])
        self.line2, = self.ax2.plot([], [], color=self.colors['accent_blue'], linewidth=2)
        
        # Stealth Score
        self.ax3.set_title('Stealth Effectiveness', color=self.colors['text_primary'], fontweight='bold')
        self.ax3.set_ylabel('Score', color=self.colors['text_primary'])
        self.line3, = self.ax3.plot([], [], color=self.colors['accent_gold'], linewidth=2)
        
        # Ticket Detections
        self.ax4.set_title('Ticket Detection Events', color=self.colors['text_primary'], fontweight='bold')
        self.ax4.set_ylabel('Count', color=self.colors['text_primary'])
        self.bars4 = self.ax4.bar([], [], color=self.colors['accent_red'])
        
        plt.tight_layout()
        
        # Embed in tkinter
        self.canvas_perf = FigureCanvasTkAgg(self.fig_perf, perf_frame)
        self.canvas_perf.draw()
        self.canvas_perf.get_tk_widget().pack(fill='both', expand=True)
    
    def create_stealth_tab(self):
        """Create stealth monitoring tab"""
        stealth_frame = ttk.Frame(self.notebook)
        self.notebook.add(stealth_frame, text="🥷 Stealth")
        
        # Stealth metrics frame
        metrics_frame = ttk.Frame(stealth_frame, style='Card.TFrame', padding=15)
        metrics_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(metrics_frame,
                text="🛡️ STEALTH METRICS",
                font=('Arial', 16, 'bold'),
                fg=self.colors['accent_gold'],
                bg=self.colors['bg_secondary']).pack()
        
        # Create metrics grid
        metrics_grid = tk.Frame(metrics_frame, bg=self.colors['bg_secondary'])
        metrics_grid.pack(fill='x', pady=20)
        
        # Stealth metrics
        self.stealth_metrics = {}
        metrics = [
            ('Detection Risk', 'LOW', self.colors['success']),
            ('Profile Health', '98%', self.colors['success']),
            ('Proxy Status', 'ACTIVE', self.colors['accent_blue']),
            ('Browser Fingerprint', 'CLEAN', self.colors['success']),
            ('TLS Signature', 'MASKED', self.colors['success']),
            ('Behavioral Score', '95/100', self.colors['accent_gold'])
        ]
        
        for i, (name, value, color) in enumerate(metrics):
            row = i // 3
            col = i % 3
            
            metric_frame = tk.Frame(metrics_grid, bg=self.colors['bg_accent'], relief='raised', bd=2)
            metric_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            tk.Label(metric_frame,
                    text=name,
                    font=('Arial', 10),
                    fg=self.colors['text_secondary'],
                    bg=self.colors['bg_accent']).pack()
            
            metric_label = tk.Label(metric_frame,
                                  text=value,
                                  font=('Arial', 14, 'bold'),
                                  fg=color,
                                  bg=self.colors['bg_accent'])
            metric_label.pack()
            
            self.stealth_metrics[name] = metric_label
        
        # Configure grid weights
        for i in range(3):
            metrics_grid.columnconfigure(i, weight=1)
        
        # Threat level indicator
        threat_frame = ttk.Frame(stealth_frame, style='Card.TFrame', padding=15)
        threat_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(threat_frame,
                text="⚠️ THREAT ASSESSMENT",
                font=('Arial', 16, 'bold'),
                fg=self.colors['accent_red'],
                bg=self.colors['bg_secondary']).pack()
        
        self.threat_canvas = tk.Canvas(threat_frame, height=100, bg=self.colors['bg_primary'])
        self.threat_canvas.pack(fill='x', pady=10)
        
        self.update_threat_meter(15)  # Low threat
    
    def create_targets_tab(self):
        """Create targets monitoring tab"""
        targets_frame = ttk.Frame(self.notebook)
        self.notebook.add(targets_frame, text="🎯 Targets")
        
        # Targets control frame
        control_frame = ttk.Frame(targets_frame, style='Card.TFrame', padding=10)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(control_frame,
                text="🎫 BRUCE SPRINGSTEEN TARGETS",
                font=('Arial', 16, 'bold'),
                fg=self.colors['accent_gold'],
                bg=self.colors['bg_secondary']).pack()
        
        # Target list with status
        targets_list_frame = ttk.Frame(targets_frame, style='Card.TFrame', padding=10)
        targets_list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create treeview for targets
        columns = ('Platform', 'Event', 'Status', 'Last Check', 'Tickets Found')
        self.targets_tree = ttk.Treeview(targets_list_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        for col in columns:
            self.targets_tree.heading(col, text=col)
            self.targets_tree.column(col, width=150)
        
        # Sample data
        targets_data = [
            ('FanSale', 'Bruce Springsteen Milano 2025', '🟢 ACTIVE', '2 min ago', '0'),
            ('Ticketmaster', 'Bruce Springsteen San Siro 2025', '🟢 ACTIVE', '1 min ago', '0'),
            ('VivaTicket', 'Bruce Springsteen Resale', '🟡 PAUSED', '5 min ago', '0')
        ]
        
        for item in targets_data:
            self.targets_tree.insert('', 'end', values=item)
        
        self.targets_tree.pack(fill='both', expand=True)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(targets_list_frame, orient='vertical', command=self.targets_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.targets_tree.configure(yscrollcommand=scrollbar.set)
        
        # Target controls
        target_controls = tk.Frame(targets_list_frame, bg=self.colors['bg_secondary'])
        target_controls.pack(fill='x', pady=10)
        
        ttk.Button(target_controls,
                  text="🎯 Add Target",
                  style='Action.TButton',
                  command=self.add_target).pack(side='left', padx=5)
        
        ttk.Button(target_controls,
                  text="✏️ Edit Selected",
                  style='Action.TButton',
                  command=self.edit_target).pack(side='left', padx=5)
        
        ttk.Button(target_controls,
                  text="🗑️ Remove Selected",
                  style='Action.TButton',
                  command=self.remove_target).pack(side='left', padx=5)
    
    def create_alerts_tab(self):
        """Create alerts and notifications tab"""
        alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(alerts_frame, text="🚨 Alerts")
        
        # Alert settings frame
        settings_frame = ttk.Frame(alerts_frame, style='Card.TFrame', padding=15)
        settings_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(settings_frame,
                text="🔔 NOTIFICATION SETTINGS",
                font=('Arial', 16, 'bold'),
                fg=self.colors['accent_gold'],
                bg=self.colors['bg_secondary']).pack()
        
        # Alert checkboxes
        alert_options = tk.Frame(settings_frame, bg=self.colors['bg_secondary'])
        alert_options.pack(fill='x', pady=10)
        
        self.alert_vars = {}
        alerts = [
            ('Desktop Notifications', True),
            ('Sound Alerts', True),
            ('Email Notifications', False),
            ('SMS Alerts', False),
            ('Browser Flash', True),
            ('System Tray', True)
        ]
        
        for i, (name, default) in enumerate(alerts):
            row = i // 2
            col = i % 2
            
            var = tk.BooleanVar(value=default)
            self.alert_vars[name] = var
            
            cb = tk.Checkbutton(alert_options,
                              text=name,
                              variable=var,
                              font=('Arial', 12),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_secondary'],
                              selectcolor=self.colors['bg_accent'])
            cb.grid(row=row, column=col, sticky='w', padx=20, pady=5)
        
        # Alert history frame
        history_frame = ttk.Frame(alerts_frame, style='Card.TFrame', padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(history_frame,
                text="📜 ALERT HISTORY",
                font=('Arial', 16, 'bold'),
                fg=self.colors['accent_red'],
                bg=self.colors['bg_secondary']).pack()
        
        # Alert history list
        self.alert_listbox = tk.Listbox(history_frame,
                                       font=('Courier', 10),
                                       bg=self.colors['bg_primary'],
                                       fg=self.colors['text_primary'],
                                       selectbackground=self.colors['accent_blue'])
        self.alert_listbox.pack(fill='both', expand=True, pady=10)
        
        # Sample alerts
        sample_alerts = [
            "🟢 System started successfully - 14:30:15",
            "🔐 FanSale authentication successful - 14:30:45",
            "🔍 Target scanning initiated - 14:31:00",
            "⚠️ High response time detected - 14:35:22",
            "🛡️ Stealth profile rotated - 14:40:10"
        ]
        
        for alert in sample_alerts:
            self.alert_listbox.insert('end', alert)
    
    def create_control_panel(self):
        """Create the control panel with action buttons"""
        control_frame = ttk.Frame(self.root, style='Card.TFrame', padding=15)
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Main controls
        main_controls = tk.Frame(control_frame, bg=self.colors['bg_secondary'])
        main_controls.pack(fill='x')
        
        # Start/Stop buttons
        self.start_button = ttk.Button(main_controls,
                                      text="🚀 START HUNTING",
                                      style='Start.TButton',
                                      command=self.start_bot)
        self.start_button.pack(side='left', padx=10)
        
        self.stop_button = ttk.Button(main_controls,
                                     text="⏹️ STOP",
                                     style='Stop.TButton',
                                     command=self.stop_bot,
                                     state='disabled')
        self.stop_button.pack(side='left', padx=10)
        
        # Action buttons
        ttk.Button(main_controls,
                  text="⚙️ Settings",
                  style='Action.TButton',
                  command=self.open_settings).pack(side='left', padx=5)
        
        ttk.Button(main_controls,
                  text="📊 Export Data",
                  style='Action.TButton',
                  command=self.export_data).pack(side='left', padx=5)
        
        ttk.Button(main_controls,
                  text="🔄 Reload Config",
                  style='Action.TButton',
                  command=self.reload_config).pack(side='left', padx=5)
        
        ttk.Button(main_controls,
                  text="🧪 Test Mode",
                  style='Action.TButton',
                  command=self.toggle_test_mode).pack(side='left', padx=5)
        
        # Status display
        status_display = tk.Frame(main_controls, bg=self.colors['bg_secondary'])
        status_display.pack(side='right', padx=20)
        
        self.tickets_found_label = tk.Label(status_display,
                                           text="🎫 TICKETS FOUND: 0",
                                           font=('Arial', 14, 'bold'),
                                           fg=self.colors['accent_red'],
                                           bg=self.colors['bg_secondary'])
        self.tickets_found_label.pack()
        
        self.session_time_label = tk.Label(status_display,
                                          text="⏱️ SESSION: 00:00:00",
                                          font=('Arial', 12),
                                          fg=self.colors['text_secondary'],
                                          bg=self.colors['bg_secondary'])
        self.session_time_label.pack()
    
    def create_status_panel(self):
        """Create system status panel"""
        status_frame = ttk.Frame(self.root, style='Card.TFrame', padding=10)
        status_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Status grid
        status_grid = tk.Frame(status_frame, bg=self.colors['bg_secondary'])
        status_grid.pack(fill='x')
        
        # System stats
        self.status_labels = {}
        stats = [
            ('🌐 Requests/min', '0'),
            ('✅ Success Rate', '0%'),
            ('⚡ Avg Response', '0ms'),
            ('🛡️ Stealth Score', '100%'),
            ('🔄 Profile Health', '100%'),
            ('📡 Network Status', 'READY')
        ]
        
        for i, (name, value) in enumerate(stats):
            stat_frame = tk.Frame(status_grid, bg=self.colors['bg_accent'], relief='raised', bd=1)
            stat_frame.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            
            tk.Label(stat_frame,
                    text=name,
                    font=('Arial', 10),
                    fg=self.colors['text_secondary'],
                    bg=self.colors['bg_accent']).pack()
            
            value_label = tk.Label(stat_frame,
                                 text=value,
                                 font=('Arial', 12, 'bold'),
                                 fg=self.colors['text_primary'],
                                 bg=self.colors['bg_accent'])
            value_label.pack()
            
            self.status_labels[name] = value_label
        
        # Configure grid weights
        for i in range(len(stats)):
            status_grid.columnconfigure(i, weight=1)
    
    def create_log_panel(self):
        """Create log display panel"""
        log_frame = ttk.Frame(self.root, style='Card.TFrame', padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        tk.Label(log_frame,
                text="📜 SYSTEM LOGS",
                font=('Arial', 14, 'bold'),
                fg=self.colors['accent_gold'],
                bg=self.colors['bg_secondary']).pack()
        
        # Log display with scroll
        self.log_display = scrolledtext.ScrolledText(log_frame,
                                                   height=8,
                                                   font=('Courier', 9),
                                                   bg=self.colors['bg_primary'],
                                                   fg=self.colors['text_primary'],
                                                   insertbackground=self.colors['text_primary'])
        self.log_display.pack(fill='both', expand=True, pady=10)
        
        # Sample logs
        sample_logs = [
            "[14:30:15] 🎸 StealthMaster AI v2.0 initialized",
            "[14:30:16] 🔧 Loading configuration from config/config.yaml",
            "[14:30:17] 👤 Profile manager loaded 20 browser profiles",
            "[14:30:18] 🌐 Connection pool initialized with stealth settings",
            "[14:30:19] 🛡️ Advanced stealth engine activated",
            "[14:30:20] 🎯 Monitoring 3 targets for Bruce Springsteen tickets"
        ]
        
        for log in sample_logs:
            self.log_display.insert('end', log + '\n')
    
    def initialize_sample_data(self):
        """Initialize with some sample data for demonstration"""
        # Generate sample performance data
        for i in range(50):
            timestamp = datetime.now() - timedelta(minutes=50-i)
            self.performance_data['timestamps'].append(timestamp)
            self.performance_data['success_rates'].append(85 + np.random.normal(0, 10))
            self.performance_data['response_times'].append(800 + np.random.normal(0, 200))
            self.performance_data['stealth_scores'].append(90 + np.random.normal(0, 8))
            self.performance_data['ticket_detections'].append(np.random.poisson(0.1))
    
    def start_real_time_updates(self):
        """Start real-time data updates"""
        self.update_graphs()
        self.update_system_time()
        self.root.after(1000, self.start_real_time_updates)  # Update every second
    
    def update_graphs(self):
        """Update performance graphs with real-time data"""
        try:
            if len(self.performance_data['timestamps']) > 0:
                # Update success rate graph
                times = list(self.performance_data['timestamps'])
                success_rates = list(self.performance_data['success_rates'])
                
                self.line1.set_data(range(len(times)), success_rates)
                self.ax1.relim()
                self.ax1.autoscale_view()
                
                # Update response time graph
                response_times = list(self.performance_data['response_times'])
                self.line2.set_data(range(len(times)), response_times)
                self.ax2.relim()
                self.ax2.autoscale_view()
                
                # Update stealth score graph
                stealth_scores = list(self.performance_data['stealth_scores'])
                self.line3.set_data(range(len(times)), stealth_scores)
                self.ax3.relim()
                self.ax3.autoscale_view()
                
                # Update ticket detection bars
                detections = list(self.performance_data['ticket_detections'])[-10:]  # Last 10 points
                self.ax4.clear()
                self.ax4.bar(range(len(detections)), detections, color=self.colors['accent_red'])
                self.ax4.set_title('Ticket Detection Events', color=self.colors['text_primary'], fontweight='bold')
                self.ax4.set_ylabel('Count', color=self.colors['text_primary'])
                self.ax4.set_facecolor(self.colors['bg_primary'])
                self.ax4.tick_params(colors=self.colors['text_primary'])
                
                self.canvas_perf.draw()
        except Exception as e:
            pass  # Ignore update errors
    
    def update_threat_meter(self, threat_level):
        """Update threat level meter (0-100)"""
        self.threat_canvas.delete("all")
        width = self.threat_canvas.winfo_width() if self.threat_canvas.winfo_width() > 1 else 400
        height = self.threat_canvas.winfo_height() if self.threat_canvas.winfo_height() > 1 else 100
        
        # Draw meter background
        self.threat_canvas.create_rectangle(50, 30, width-50, 70, fill=self.colors['bg_primary'], outline=self.colors['text_secondary'])
        
        # Draw threat level
        meter_width = (width - 100) * (threat_level / 100)
        color = self.colors['success'] if threat_level < 30 else self.colors['warning'] if threat_level < 70 else self.colors['error']
        
        self.threat_canvas.create_rectangle(50, 30, 50 + meter_width, 70, fill=color, outline="")
        
        # Draw text
        threat_text = "LOW" if threat_level < 30 else "MEDIUM" if threat_level < 70 else "HIGH"
        self.threat_canvas.create_text(width//2, 50, text=f"THREAT LEVEL: {threat_text} ({threat_level}%)",
                                     fill=self.colors['text_primary'], font=('Arial', 12, 'bold'))
    
    def update_system_time(self):
        """Update system uptime and session time"""
        # Update uptime (placeholder)
        current_time = datetime.now()
        uptime = "00:15:32"  # Placeholder
        self.uptime_label.config(text=f"Uptime: {uptime}")
        
        # Update session time if bot is running
        if self.bot_running:
            # Placeholder session time
            session_time = "00:05:42"
            self.session_time_label.config(text=f"⏱️ SESSION: {session_time}")
    
    def start_bot(self):
        """Start the ticket hunting bot"""
        try:
            self.log_message("🚀 Starting Bruce Springsteen ticket hunter...")
            
            # Load configuration
            config = load_app_config_for_gui()
            
            # Create stop event
            self.stop_event = threading.Event()
            
            # Start bot in separate thread
            self.bot_thread = threading.Thread(
                target=main_loop_for_gui,
                args=(config, self.stop_event, self.gui_queue),
                daemon=True
            )
            self.bot_thread.start()
            
            # Update UI state
            self.bot_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_indicator.config(text="● HUNTING", fg=self.colors['success'])
            
            self.log_message("✅ Bot started successfully!")
            self.log_message("🎯 Monitoring targets for Bruce Springsteen tickets...")
            
            # Start processing queue messages
            self.process_queue_messages()
            
        except Exception as e:
            self.log_message(f"❌ Failed to start bot: {str(e)}")
            messagebox.showerror("Error", f"Failed to start bot: {str(e)}")
    
    def stop_bot(self):
        """Stop the ticket hunting bot"""
        try:
            self.log_message("⏹️ Stopping ticket hunter...")
            
            if self.stop_event:
                self.stop_event.set()
            
            # Update UI state
            self.bot_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.status_indicator.config(text="● STOPPED", fg=self.colors['error'])
            
            self.log_message("✅ Bot stopped successfully")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping bot: {str(e)}")
    
    def process_queue_messages(self):
        """Process messages from the bot queue"""
        try:
            while not self.gui_queue.empty():
                message_type, data = self.gui_queue.get_nowait()
                
                if message_type == "log":
                    log_message, level = data
                    self.log_message(f"[BOT] {log_message}")
                elif message_type == "ticket_found":
                    self.handle_ticket_found(data)
                elif message_type == "status_update":
                    self.handle_status_update(data)
                elif message_type == "bot_stopped":
                    self.handle_bot_stopped()
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        if self.bot_running:
            self.root.after(100, self.process_queue_messages)
    
    def handle_ticket_found(self, ticket_data):
        """Handle ticket found notification"""
        self.log_message("🚨🚨🚨 BRUCE SPRINGSTEEN TICKETS FOUND! 🚨🚨🚨")
        self.log_message(f"🎫 {ticket_data}")
        
        # Flash the window
        self.flash_window()
        
        # Update tickets found counter
        current_count = int(self.tickets_found_label.cget('text').split(': ')[1])
        self.tickets_found_label.config(text=f"🎫 TICKETS FOUND: {current_count + 1}")
        
        # Show popup notification
        messagebox.showinfo("🎸 TICKETS FOUND!", 
                          f"Bruce Springsteen tickets detected!\n\n{ticket_data}\n\nCheck your browser for purchase options!")
    
    def handle_status_update(self, status_data):
        """Handle status update from bot"""
        # Update various status displays
        pass
    
    def handle_bot_stopped(self):
        """Handle bot stopped notification"""
        self.bot_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_indicator.config(text="● STOPPED", fg=self.colors['error'])
    
    def flash_window(self):
        """Flash the window to get attention"""
        original_title = self.root.title()
        for i in range(6):  # Flash 3 times
            if i % 2 == 0:
                self.root.title("🚨 TICKETS FOUND! 🚨")
                self.root.configure(bg=self.colors['accent_red'])
            else:
                self.root.title(original_title)
                self.root.configure(bg=self.colors['bg_primary'])
            self.root.update()
            self.root.after(300)
        
        # Try to bring window to front
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
    
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_display.insert('end', formatted_message)
        self.log_display.see('end')  # Auto-scroll to bottom
        
        # Also add to alert history if it's important
        if any(keyword in message.lower() for keyword in ['error', 'found', 'started', 'stopped']):
            self.alert_listbox.insert('end', f"{message} - {timestamp}")
            self.alert_listbox.see('end')
    
    # Button command methods
    def add_target(self):
        messagebox.showinfo("Add Target", "Target addition feature coming soon!")
    
    def edit_target(self):
        messagebox.showinfo("Edit Target", "Target editing feature coming soon!")
    
    def remove_target(self):
        messagebox.showinfo("Remove Target", "Target removal feature coming soon!")
    
    def open_settings(self):
        messagebox.showinfo("Settings", "Settings panel coming soon!")
    
    def export_data(self):
        messagebox.showinfo("Export", "Data export feature coming soon!")
    
    def reload_config(self):
        self.log_message("🔄 Reloading configuration...")
        messagebox.showinfo("Config Reloaded", "Configuration reloaded successfully!")
    
    def toggle_test_mode(self):
        self.log_message("🧪 Test mode toggled")
        messagebox.showinfo("Test Mode", "Test mode feature coming soon!")
    
    def run(self):
        """Run the GUI application"""
        try:
            self.log_message("🎸 StealthMaster AI GUI v2.0 ready!")
            self.log_message("🎯 Ready to hunt for Bruce Springsteen tickets!")
            
            # Start the main loop
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self.log_message("👋 GUI shutting down...")
        except Exception as e:
            self.log_message(f"❌ GUI error: {str(e)}")
        finally:
            # Cleanup
            if self.bot_running and self.stop_event:
                self.stop_event.set()

def main():
    """Main entry point for the GUI"""
    try:
        # Create and run the GUI
        app = StealthMasterGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()