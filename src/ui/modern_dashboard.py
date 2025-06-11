"""
Modern Enhanced Dashboard for StealthMaster
Features real-time graphs, notifications, and improved UX
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from datetime import datetime, timedelta
import threading
import json
import time
from typing import Dict, Any, Optional, List
import queue
from collections import deque
import math

# Try importing graph libraries
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.animation import FuncAnimation
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from ..database.statistics import stats_manager
from ..utils.logging import get_logger
# Config will be injected when needed

logger = get_logger(__name__)


class ModernDashboard:
    """
    Modern Enhanced Dashboard with improved UX and real-time features
    """
    
    def __init__(self, parent: Optional[tk.Tk] = None):
        self.parent = parent or tk.Tk()
        self.parent.title("StealthMaster - Advanced Dashboard")
        self.parent.geometry("1600x1000")
        
        # Modern color scheme
        self.colors = {
            'bg': '#0f0f0f',
            'card_bg': '#1a1a1a',
            'text': '#ffffff',
            'text_dim': '#888888',
            'accent': '#00d4ff',
            'success': '#00ff88',
            'danger': '#ff3366',
            'warning': '#ffaa00',
            'info': '#00aaff',
            'graph_line': '#00d4ff',
            'graph_fill': '#00d4ff33'
        }
        
        # Set dark theme
        self.parent.configure(bg=self.colors['bg'])
        self._setup_modern_theme()
        
        # Data structures
        self.update_queue = queue.Queue()
        self.notifications = deque(maxlen=5)
        self.success_rate_history = deque(maxlen=60)  # Last 60 data points
        self.platform_data = {}
        
        # Session tracking
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_start = datetime.now()
        stats_manager.start_session(self.session_id)
        
        # Create UI
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Process GUI updates
        self._process_updates()
        
        # Show welcome notification
        self.add_notification("Dashboard initialized successfully", "success")
        
        logger.info("Modern dashboard initialized")
    
    def _setup_modern_theme(self):
        """Configure modern dark theme"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure widget styles
        style.configure("Card.TFrame", 
                       background=self.colors['card_bg'],
                       relief="flat",
                       borderwidth=1)
        
        style.configure("Header.TLabel",
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=("SF Pro Display", 24, "bold"))
        
        style.configure("Title.TLabel",
                       background=self.colors['card_bg'],
                       foreground=self.colors['text'],
                       font=("SF Pro Display", 14, "bold"))
        
        style.configure("Metric.TLabel",
                       background=self.colors['card_bg'],
                       foreground=self.colors['text'],
                       font=("SF Pro Display", 32, "bold"))
        
        style.configure("MetricLabel.TLabel",
                       background=self.colors['card_bg'],
                       foreground=self.colors['text_dim'],
                       font=("SF Pro Display", 10))
        
        style.configure("Modern.TButton",
                       background=self.colors['accent'],
                       foreground=self.colors['bg'],
                       borderwidth=0,
                       focuscolor='none',
                       font=("SF Pro Display", 11, "bold"))
        
        style.map("Modern.TButton",
                 background=[('active', self.colors['info'])])
    
    def _create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.parent, bg=self.colors['bg'], height=80)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        # Logo and title
        title_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        title_frame.pack(side="left", fill="y")
        
        title = tk.Label(title_frame, text="🎫 StealthMaster",
                        font=("SF Pro Display", 28, "bold"),
                        bg=self.colors['bg'], fg=self.colors['text'])
        title.pack(side="left")
        
        subtitle = tk.Label(title_frame, text="  Advanced Ticketing Dashboard",
                          font=("SF Pro Display", 14),
                          bg=self.colors['bg'], fg=self.colors['text_dim'])
        subtitle.pack(side="left", padx=(10, 0))
        
        # Live status indicator
        self.status_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        self.status_frame.pack(side="right", fill="y")
        
        self.status_dot = tk.Label(self.status_frame, text="●",
                                 font=("SF Pro Display", 16),
                                 bg=self.colors['bg'], fg=self.colors['success'])
        self.status_dot.pack(side="left")
        
        self.status_text = tk.Label(self.status_frame, text="ACTIVE",
                                  font=("SF Pro Display", 12, "bold"),
                                  bg=self.colors['bg'], fg=self.colors['success'])
        self.status_text.pack(side="left", padx=(5, 20))
        
        # Session info
        self.session_label = tk.Label(self.status_frame, 
                                    text=f"Session: {self.session_id[-8:]}",
                                    font=("SF Pro Display", 10),
                                    bg=self.colors['bg'], fg=self.colors['text_dim'])
        self.session_label.pack(side="left")
    
    def _create_main_content(self):
        """Create main content area with cards"""
        # Main container
        main_container = tk.Frame(self.parent, bg=self.colors['bg'])
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left column - Stats and graphs
        left_column = tk.Frame(main_container, bg=self.colors['bg'])
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Key metrics row
        self._create_key_metrics(left_column)
        
        # Success rate graph
        if HAS_MATPLOTLIB:
            self._create_success_graph(left_column)
        
        # Platform performance
        self._create_platform_cards(left_column)
        
        # Right column - Activity and controls
        right_column = tk.Frame(main_container, bg=self.colors['bg'], width=400)
        right_column.pack(side="right", fill="both", padx=(10, 0))
        right_column.pack_propagate(False)
        
        # Notifications
        self._create_notifications_panel(right_column)
        
        # Activity feed
        self._create_activity_feed(right_column)
        
        # Quick actions
        self._create_quick_actions(right_column)
    
    def _create_key_metrics(self, parent):
        """Create key metrics cards"""
        metrics_frame = tk.Frame(parent, bg=self.colors['bg'])
        metrics_frame.pack(fill="x", pady=(0, 20))
        
        self.metric_cards = {}
        metrics = [
            ("found", "Tickets Found", self.colors['info']),
            ("reserved", "Reserved", self.colors['success']),
            ("failed", "Failed", self.colors['danger']),
            ("rate", "Success Rate", self.colors['warning'])
        ]
        
        for key, label, color in metrics:
            card = self._create_metric_card(metrics_frame, label, "0", color)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.metric_cards[key] = card
    
    def _create_metric_card(self, parent, label, value, color):
        """Create a single metric card"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], 
                       highlightbackground=color, highlightthickness=2)
        card.configure(relief="flat")
        
        # Value
        value_label = tk.Label(card, text=value, 
                             font=("SF Pro Display", 36, "bold"),
                             bg=self.colors['card_bg'], fg=color)
        value_label.pack(pady=(15, 5))
        
        # Label
        label_text = tk.Label(card, text=label,
                            font=("SF Pro Display", 11),
                            bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        label_text.pack(pady=(0, 15))
        
        # Store references
        card.value_label = value_label
        card.color = color
        
        return card
    
    def _create_success_graph(self, parent):
        """Create real-time success rate graph"""
        graph_frame = tk.Frame(parent, bg=self.colors['card_bg'], height=200)
        graph_frame.pack(fill="x", pady=(0, 20))
        graph_frame.pack_propagate(False)
        
        # Title
        title = tk.Label(graph_frame, text="Success Rate Trend",
                        font=("SF Pro Display", 12, "bold"),
                        bg=self.colors['card_bg'], fg=self.colors['text'])
        title.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 2), dpi=100, facecolor=self.colors['card_bg'])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.colors['card_bg'])
        
        # Style the graph
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color(self.colors['text_dim'])
        self.ax.spines['left'].set_color(self.colors['text_dim'])
        self.ax.tick_params(colors=self.colors['text_dim'])
        self.ax.set_ylim(0, 100)
        self.ax.set_ylabel('Success %', color=self.colors['text_dim'])
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Initialize with empty data
        self.success_line, = self.ax.plot([], [], color=self.colors['graph_line'], linewidth=2)
        self.ax.fill_between([], [], alpha=0.3, color=self.colors['graph_line'])
    
    def _create_platform_cards(self, parent):
        """Create platform performance cards"""
        platforms_frame = tk.Frame(parent, bg=self.colors['bg'])
        platforms_frame.pack(fill="x")
        
        title = tk.Label(platforms_frame, text="Platform Performance",
                        font=("SF Pro Display", 14, "bold"),
                        bg=self.colors['bg'], fg=self.colors['text'])
        title.pack(anchor="w", pady=(0, 10))
        
        self.platform_cards = {}
        platforms = ["ticketmaster", "fansale", "vivaticket"]
        
        for platform in platforms:
            card = self._create_platform_card(platforms_frame, platform)
            card.pack(fill="x", pady=5)
            self.platform_cards[platform] = card
    
    def _create_platform_card(self, parent, platform):
        """Create a single platform card"""
        card = tk.Frame(parent, bg=self.colors['card_bg'])
        
        # Header
        header_frame = tk.Frame(card, bg=self.colors['card_bg'])
        header_frame.pack(fill="x", padx=15, pady=10)
        
        name = tk.Label(header_frame, text=platform.title(),
                       font=("SF Pro Display", 12, "bold"),
                       bg=self.colors['card_bg'], fg=self.colors['text'])
        name.pack(side="left")
        
        status = tk.Label(header_frame, text="●",
                         font=("SF Pro Display", 12),
                         bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        status.pack(side="right")
        
        # Stats
        stats_frame = tk.Frame(card, bg=self.colors['card_bg'])
        stats_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Create stat labels
        stats_text = tk.Label(stats_frame, 
                            text="Found: 0 | Reserved: 0 | Success: 0%",
                            font=("SF Pro Display", 10),
                            bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        stats_text.pack(side="left")
        
        # Store references
        card.status = status
        card.stats = stats_text
        
        return card
    
    def _create_notifications_panel(self, parent):
        """Create notifications panel"""
        notif_frame = tk.Frame(parent, bg=self.colors['card_bg'], height=120)
        notif_frame.pack(fill="x", pady=(0, 10))
        notif_frame.pack_propagate(False)
        
        title = tk.Label(notif_frame, text="Notifications",
                        font=("SF Pro Display", 12, "bold"),
                        bg=self.colors['card_bg'], fg=self.colors['text'])
        title.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.notif_container = tk.Frame(notif_frame, bg=self.colors['card_bg'])
        self.notif_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))
    
    def _create_activity_feed(self, parent):
        """Create activity feed"""
        feed_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        feed_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        title = tk.Label(feed_frame, text="Live Activity",
                        font=("SF Pro Display", 12, "bold"),
                        bg=self.colors['card_bg'], fg=self.colors['text'])
        title.pack(anchor="w", padx=15, pady=10)
        
        # Create text widget
        self.feed_text = tk.Text(feed_frame, height=15, wrap=tk.WORD,
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=("SF Pro Mono", 9),
                               relief="flat", 
                               highlightthickness=0)
        self.feed_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Configure tags
        self.feed_text.tag_config("info", foreground=self.colors['info'])
        self.feed_text.tag_config("success", foreground=self.colors['success'])
        self.feed_text.tag_config("error", foreground=self.colors['danger'])
        self.feed_text.tag_config("warning", foreground=self.colors['warning'])
        self.feed_text.tag_config("timestamp", foreground=self.colors['text_dim'])
    
    def _create_quick_actions(self, parent):
        """Create quick actions panel"""
        actions_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        actions_frame.pack(fill="x")
        
        title = tk.Label(actions_frame, text="Quick Actions",
                        font=("SF Pro Display", 12, "bold"),
                        bg=self.colors['card_bg'], fg=self.colors['text'])
        title.pack(anchor="w", padx=15, pady=(10, 10))
        
        buttons_frame = tk.Frame(actions_frame, bg=self.colors['card_bg'])
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Create modern buttons
        self._create_action_button(buttons_frame, "📊 Export Stats", self._export_stats)
        self._create_action_button(buttons_frame, "🔄 Reset Session", self._reset_session)
        self._create_action_button(buttons_frame, "⚙️ Settings", self._show_settings)
        self._create_action_button(buttons_frame, "📈 Analytics", self._show_analytics)
    
    def _create_action_button(self, parent, text, command):
        """Create modern action button"""
        btn = tk.Button(parent, text=text, command=command,
                       bg=self.colors['accent'], fg=self.colors['bg'],
                       font=("SF Pro Display", 10, "bold"),
                       relief="flat", bd=0,
                       padx=15, pady=8,
                       cursor="hand2",
                       activebackground=self.colors['info'])
        btn.pack(pady=3, fill="x")
        
        # Hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg=self.colors['info']))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.colors['accent']))
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        status_bar = tk.Frame(self.parent, bg=self.colors['card_bg'], height=30)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        # Duration
        self.duration_label = tk.Label(status_bar, text="Duration: 00:00:00",
                                     font=("SF Pro Display", 9),
                                     bg=self.colors['card_bg'], 
                                     fg=self.colors['text_dim'])
        self.duration_label.pack(side="left", padx=20)
        
        # Memory usage
        self.memory_label = tk.Label(status_bar, text="Memory: 0 MB",
                                   font=("SF Pro Display", 9),
                                   bg=self.colors['card_bg'], 
                                   fg=self.colors['text_dim'])
        self.memory_label.pack(side="left", padx=20)
        
        # CPU usage
        self.cpu_label = tk.Label(status_bar, text="CPU: 0%",
                                font=("SF Pro Display", 9),
                                bg=self.colors['card_bg'], 
                                fg=self.colors['text_dim'])
        self.cpu_label.pack(side="left", padx=20)
        
        # Version
        version_label = tk.Label(status_bar, text="StealthMaster 2025",
                               font=("SF Pro Display", 9),
                               bg=self.colors['card_bg'], 
                               fg=self.colors['text_dim'])
        version_label.pack(side="right", padx=20)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.parent.bind("<Control-e>", lambda e: self._export_stats())
        self.parent.bind("<Control-r>", lambda e: self._reset_session())
        self.parent.bind("<Control-s>", lambda e: self._show_settings())
        self.parent.bind("<F5>", lambda e: self.refresh_stats())
    
    def add_notification(self, message: str, type: str = "info"):
        """Add notification to panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.notifications.append({
            'message': message,
            'type': type,
            'timestamp': timestamp
        })
        self.update_queue.put(("notification", None))
    
    def add_log_entry(self, message: str, level: str = "info"):
        """Add entry to activity feed"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\\n"
        self.update_queue.put(("log", entry, level))
    
    def update_stats(self):
        """Update all statistics displays"""
        try:
            summary = stats_manager.get_summary()
            self.update_queue.put(("stats", summary))
            
            # Update platform stats
            for platform_data in summary.get("platform_breakdown", []):
                platform = platform_data["platform"]
                self.update_queue.put(("platform", platform, platform_data))
            
            # Update success rate history
            if summary["total_found"] > 0:
                rate = (summary["total_reserved"] / summary["total_found"]) * 100
            else:
                rate = 0
            self.success_rate_history.append(rate)
            self.update_queue.put(("graph", None))
            
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")
    
    def _update_loop(self):
        """Background thread for periodic updates"""
        while self.running:
            try:
                self.update_stats()
                
                # Update system metrics
                import psutil
                process = psutil.Process()
                memory = process.memory_info().rss / 1024 / 1024  # MB
                cpu = process.cpu_percent(interval=0.1)
                self.update_queue.put(("system", {"memory": memory, "cpu": cpu}))
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Update loop error: {e}")
                time.sleep(5)
    
    def _process_updates(self):
        """Process queued GUI updates"""
        try:
            while True:
                try:
                    update = self.update_queue.get_nowait()
                    
                    if update[0] == "log":
                        _, entry, level = update
                        # Insert with timestamp styling
                        self.feed_text.insert(tk.END, entry[:11], "timestamp")
                        self.feed_text.insert(tk.END, entry[11:], level)
                        self.feed_text.see(tk.END)
                        
                        # Limit feed size
                        lines = int(self.feed_text.index('end-1c').split('.')[0])
                        if lines > 100:
                            self.feed_text.delete('1.0', '2.0')
                    
                    elif update[0] == "stats":
                        _, summary = update
                        # Update metric cards with animation
                        self._update_metric_card("found", str(summary["total_found"]))
                        self._update_metric_card("reserved", str(summary["total_reserved"]))
                        self._update_metric_card("failed", str(summary["total_failed"]))
                        self._update_metric_card("rate", f"{summary['overall_success_rate']:.1f}%")
                    
                    elif update[0] == "platform":
                        _, platform, data = update
                        if platform in self.platform_cards:
                            card = self.platform_cards[platform]
                            # Update status color based on success rate
                            if data['success_rate'] > 70:
                                card.status.config(fg=self.colors['success'])
                            elif data['success_rate'] > 40:
                                card.status.config(fg=self.colors['warning'])
                            else:
                                card.status.config(fg=self.colors['danger'])
                            
                            # Update stats
                            stats_text = f"Found: {data['found']} | Reserved: {data['reserved']} | Success: {data['success_rate']:.1f}%"
                            card.stats.config(text=stats_text)
                    
                    elif update[0] == "notification":
                        self._update_notifications()
                    
                    elif update[0] == "graph" and HAS_MATPLOTLIB:
                        self._update_graph()
                    
                    elif update[0] == "system":
                        _, metrics = update
                        self.memory_label.config(text=f"Memory: {metrics['memory']:.0f} MB")
                        self.cpu_label.config(text=f"CPU: {metrics['cpu']:.1f}%")
                        
                        # Update duration
                        duration = datetime.now() - self.session_start
                        hours = int(duration.total_seconds() // 3600)
                        minutes = int((duration.total_seconds() % 3600) // 60)
                        seconds = int(duration.total_seconds() % 60)
                        self.duration_label.config(text=f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
                    
                except queue.Empty:
                    break
            
        except Exception as e:
            logger.error(f"GUI update error: {e}")
        
        # Schedule next update
        self.parent.after(100, self._process_updates)
    
    def _update_metric_card(self, key, value):
        """Update metric card with fade animation"""
        if key in self.metric_cards:
            card = self.metric_cards[key]
            card.value_label.config(text=value)
            # Flash effect
            card.value_label.config(fg=self.colors['text'])
            self.parent.after(100, lambda: card.value_label.config(fg=card.color))
    
    def _update_notifications(self):
        """Update notifications display"""
        # Clear existing
        for widget in self.notif_container.winfo_children():
            widget.destroy()
        
        # Add notifications
        for notif in reversed(self.notifications):
            notif_frame = tk.Frame(self.notif_container, bg=self.colors['card_bg'])
            notif_frame.pack(fill="x", pady=2)
            
            # Icon
            icons = {
                'success': '✓',
                'error': '✗',
                'warning': '!',
                'info': 'i'
            }
            icon = tk.Label(notif_frame, text=icons.get(notif['type'], 'i'),
                          font=("SF Pro Display", 10, "bold"),
                          bg=self.colors['card_bg'],
                          fg=self.colors[notif['type']])
            icon.pack(side="left", padx=(0, 8))
            
            # Message
            msg = tk.Label(notif_frame, text=notif['message'],
                         font=("SF Pro Display", 9),
                         bg=self.colors['card_bg'], fg=self.colors['text'])
            msg.pack(side="left", fill="x", expand=True)
            
            # Time
            time_label = tk.Label(notif_frame, text=notif['timestamp'],
                                font=("SF Pro Display", 8),
                                bg=self.colors['card_bg'], 
                                fg=self.colors['text_dim'])
            time_label.pack(side="right")
    
    def _update_graph(self):
        """Update success rate graph"""
        if not self.success_rate_history:
            return
        
        # Clear and redraw
        self.ax.clear()
        self.ax.set_facecolor(self.colors['card_bg'])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color(self.colors['text_dim'])
        self.ax.spines['left'].set_color(self.colors['text_dim'])
        self.ax.tick_params(colors=self.colors['text_dim'])
        self.ax.set_ylim(0, 100)
        
        # Plot data
        x = list(range(len(self.success_rate_history)))
        y = list(self.success_rate_history)
        
        self.ax.plot(x, y, color=self.colors['graph_line'], linewidth=2)
        self.ax.fill_between(x, y, alpha=0.3, color=self.colors['graph_line'])
        
        # Add grid
        self.ax.grid(True, alpha=0.1, color=self.colors['text_dim'])
        
        self.canvas.draw()
    
    def refresh_stats(self):
        """Force refresh all statistics"""
        self.add_notification("Refreshing statistics...", "info")
        self.update_stats()
    
    def _export_stats(self):
        """Export statistics to file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv")]
            )
            
            if filename:
                format = "csv" if filename.endswith(".csv") else "json"
                data = stats_manager.export_stats(format)
                
                with open(filename, "w") as f:
                    f.write(data)
                
                self.add_notification(f"Exported to {filename.split('/')[-1]}", "success")
                self.add_log_entry(f"Statistics exported to {filename}", "success")
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.add_notification("Export failed", "error")
    
    def _reset_session(self):
        """Reset current session"""
        try:
            # Confirm dialog
            result = messagebox.askyesno("Reset Session",
                                       "Are you sure you want to reset the current session?\\n"
                                       "This will clear all statistics.")
            
            if result:
                # End current session
                stats_manager.end_session(self.session_id)
                
                # Start new session
                self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.session_start = datetime.now()
                stats_manager.start_session(self.session_id)
                
                # Clear data
                self.success_rate_history.clear()
                
                # Update UI
                self.session_label.config(text=f"Session: {self.session_id[-8:]}")
                self.add_notification("Session reset successfully", "success")
                self.add_log_entry("Session reset", "warning")
                
        except Exception as e:
            logger.error(f"Session reset failed: {e}")
            self.add_notification("Reset failed", "error")
    
    def _show_settings(self):
        """Show settings dialog"""
        # Create settings window
        settings_window = tk.Toplevel(self.parent)
        settings_window.title("Settings")
        settings_window.geometry("600x400")
        settings_window.configure(bg=self.colors['bg'])
        
        # Add settings content
        title = tk.Label(settings_window, text="Settings",
                        font=("SF Pro Display", 18, "bold"),
                        bg=self.colors['bg'], fg=self.colors['text'])
        title.pack(pady=20)
        
        info = tk.Label(settings_window, 
                       text="Settings configuration coming soon...",
                       font=("SF Pro Display", 12),
                       bg=self.colors['bg'], fg=self.colors['text_dim'])
        info.pack()
        
        self.add_notification("Settings opened", "info")
    
    def _show_analytics(self):
        """Show detailed analytics"""
        self.add_notification("Analytics view coming soon", "info")
        self.add_log_entry("Analytics requested", "info")
    
    def run(self):
        """Start the dashboard"""
        self.parent.mainloop()
    
    def close(self):
        """Clean up and close dashboard"""
        self.running = False
        stats_manager.end_session(self.session_id)
        self.parent.quit()


def launch_modern_dashboard():
    """Launch the modern dashboard"""
    dashboard = ModernDashboard()
    dashboard.parent.protocol("WM_DELETE_WINDOW", dashboard.close)
    dashboard.run()


if __name__ == "__main__":
    launch_modern_dashboard()