# src/ui/detection_dashboard.py
"""
Advanced Detection Monitoring Dashboard
Real-time visualization of anti-detection metrics
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..core.detection_monitor import get_detection_monitor
from ..utils.enhanced_logger import setup_enhanced_logging

import logging
logger = logging.getLogger(__name__)


class DetectionDashboard:
    """Advanced GUI dashboard for detection monitoring"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🛡️ Stealth Detection Monitor - Bruce Springsteen Ticket Hunter")
        self.root.geometry("1400x900")
        
        # Initialize detection monitor
        self.monitor = get_detection_monitor()
        
        # Update queue
        self.update_queue = queue.Queue()
        
        # Style configuration
        self.setup_styles()
        
        # Create UI
        self.create_widgets()
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_worker, daemon=True)
        self.update_thread.start()
        
        # Schedule UI updates
        self.root.after(100, self.process_updates)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Configure modern dark theme styles"""
        style = ttk.Style()
        
        # Colors
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'success': '#00ff00',
            'warning': '#ffaa00',
            'error': '#ff4444',
            'info': '#00aaff',
            'frame': '#2d2d2d',
            'button': '#3d3d3d',
            'entry': '#3d3d3d'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk styles
        style.configure('Title.TLabel', font=('Arial', 20, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Status.TLabel', font=('Consolas', 10))
        style.configure('Metric.TLabel', font=('Arial', 12))
    
    def create_widgets(self):
        """Create all dashboard widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🛡️ Stealth Detection Monitor",
            font=('Arial', 24, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        title_label.pack(pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Overview tab
        self.overview_frame = tk.Frame(self.notebook, bg=self.colors['frame'])
        self.notebook.add(self.overview_frame, text="Overview")
        self.create_overview_tab()
        
        # Platform metrics tab
        self.platforms_frame = tk.Frame(self.notebook, bg=self.colors['frame'])
        self.notebook.add(self.platforms_frame, text="Platform Metrics")
        self.create_platforms_tab()
        
        # Events log tab
        self.events_frame = tk.Frame(self.notebook, bg=self.colors['frame'])
        self.notebook.add(self.events_frame, text="Events Log")
        self.create_events_tab()
        
        # Alerts tab
        self.alerts_frame = tk.Frame(self.notebook, bg=self.colors['frame'])
        self.notebook.add(self.alerts_frame, text="Alerts")
        self.create_alerts_tab()
        
        # Control panel at bottom
        self.create_control_panel(main_frame)
    
    def create_overview_tab(self):
        """Create overview metrics display"""
        # Global metrics frame
        global_frame = tk.LabelFrame(
            self.overview_frame,
            text="Global Metrics",
            bg=self.colors['frame'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        global_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Metric displays
        self.global_metrics = {}
        metrics = [
            ("Total Attempts", "total_attempts", self.colors['info']),
            ("Successful Access", "total_success", self.colors['success']),
            ("Blocked Access", "total_blocks", self.colors['error']),
            ("Success Rate", "global_success_rate", self.colors['info']),
            ("Active Sessions", "active_sessions", self.colors['success'])
        ]
        
        # Create metric labels in grid
        for i, (label, key, color) in enumerate(metrics):
            frame = tk.Frame(global_frame, bg=self.colors['frame'])
            frame.grid(row=i // 3, column=i % 3, padx=20, pady=10, sticky='w')
            
            tk.Label(
                frame,
                text=f"{label}:",
                bg=self.colors['frame'],
                fg=self.colors['fg'],
                font=('Arial', 10)
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                frame,
                text="0",
                bg=self.colors['frame'],
                fg=color,
                font=('Arial', 14, 'bold')
            )
            value_label.pack(side=tk.LEFT, padx=(10, 0))
            
            self.global_metrics[key] = value_label
        
        # Recent blocks frame
        blocks_frame = tk.LabelFrame(
            self.overview_frame,
            text="Recent Blocks",
            bg=self.colors['frame'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        blocks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Recent blocks listbox
        self.blocks_listbox = tk.Listbox(
            blocks_frame,
            bg=self.colors['entry'],
            fg=self.colors['fg'],
            font=('Consolas', 10),
            height=10
        )
        self.blocks_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for blocks
        blocks_scroll = ttk.Scrollbar(self.blocks_listbox, orient=tk.VERTICAL)
        blocks_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.blocks_listbox.config(yscrollcommand=blocks_scroll.set)
        blocks_scroll.config(command=self.blocks_listbox.yview)
    
    def create_platforms_tab(self):
        """Create platform-specific metrics display"""
        # Platform frames container
        self.platform_frames = {}
        
        # Create scrollable frame
        canvas = tk.Canvas(self.platforms_frame, bg=self.colors['frame'])
        scrollbar = ttk.Scrollbar(self.platforms_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['frame'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Platform metrics will be dynamically created
        self.platforms_container = scrollable_frame
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_platform_metric_frame(self, platform: str, parent: tk.Widget):
        """Create metric frame for a platform"""
        frame = tk.LabelFrame(
            parent,
            text=f"📊 {platform.upper()}",
            bg=self.colors['frame'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create metric labels
        metrics = {}
        metric_info = [
            ("Success Rate", "success_rate", "%"),
            ("Current Streak", "current_streak", ""),
            ("Max Streak", "max_streak", ""),
            ("Avg Response", "avg_response_time_ms", "ms"),
            ("Health Score", "health_score", "/100"),
            ("Blocks", "blocked_access", ""),
            ("Rate Limits", "rate_limits_hit", ""),
            ("Bot Detections", "bot_detections", "")
        ]
        
        # Create 2-column grid
        for i, (label, key, unit) in enumerate(metric_info):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(
                frame,
                text=f"{label}:",
                bg=self.colors['frame'],
                fg=self.colors['fg'],
                font=('Arial', 10)
            ).grid(row=row, column=col, sticky='w', padx=(10, 5), pady=2)
            
            value_label = tk.Label(
                frame,
                text=f"0{unit}",
                bg=self.colors['frame'],
                fg=self.colors['info'],
                font=('Arial', 10, 'bold')
            )
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20), pady=2)
            
            metrics[key] = (value_label, unit)
        
        self.platform_frames[platform] = (frame, metrics)
    
    def create_events_tab(self):
        """Create events log display"""
        # Controls frame
        controls_frame = tk.Frame(self.events_frame, bg=self.colors['frame'])
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Filter controls
        tk.Label(
            controls_frame,
            text="Filter:",
            bg=self.colors['frame'],
            fg=self.colors['fg']
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Platform filter
        self.platform_filter = ttk.Combobox(
            controls_frame,
            values=["All", "fansale", "ticketmaster", "vivaticket"],
            width=15
        )
        self.platform_filter.set("All")
        self.platform_filter.pack(side=tk.LEFT, padx=5)
        
        # Event type filter
        self.event_filter = ttk.Combobox(
            controls_frame,
            values=["All", "ACCESS_GRANTED", "ACCESS_DENIED", "BOT_DETECTED", 
                   "CAPTCHA_TRIGGERED", "LOGIN_SUCCESS", "LOGIN_FAILED"],
            width=20
        )
        self.event_filter.set("All")
        self.event_filter.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        tk.Button(
            controls_frame,
            text="Refresh",
            command=self.refresh_events,
            bg=self.colors['button'],
            fg=self.colors['fg']
        ).pack(side=tk.LEFT, padx=10)
        
        # Events display
        events_frame = tk.Frame(self.events_frame, bg=self.colors['frame'])
        events_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create Treeview for events
        columns = ('Time', 'Platform', 'Event', 'Profile', 'Success', 'Details')
        self.events_tree = ttk.Treeview(
            events_frame,
            columns=columns,
            show='headings',
            height=20
        )
        
        # Configure columns
        self.events_tree.heading('Time', text='Time')
        self.events_tree.heading('Platform', text='Platform')
        self.events_tree.heading('Event', text='Event Type')
        self.events_tree.heading('Profile', text='Profile ID')
        self.events_tree.heading('Success', text='Success')
        self.events_tree.heading('Details', text='Details')
        
        # Column widths
        self.events_tree.column('Time', width=150)
        self.events_tree.column('Platform', width=100)
        self.events_tree.column('Event', width=150)
        self.events_tree.column('Profile', width=150)
        self.events_tree.column('Success', width=80)
        self.events_tree.column('Details', width=300)
        
        # Scrollbars
        vsb = ttk.Scrollbar(events_frame, orient="vertical", command=self.events_tree.yview)
        hsb = ttk.Scrollbar(events_frame, orient="horizontal", command=self.events_tree.xview)
        self.events_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack
        self.events_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        events_frame.grid_rowconfigure(0, weight=1)
        events_frame.grid_columnconfigure(0, weight=1)
    
    def create_alerts_tab(self):
        """Create alerts display"""
        # Active alerts frame
        alerts_frame = tk.LabelFrame(
            self.alerts_frame,
            text="Active Alerts",
            bg=self.colors['frame'],
            fg=self.colors['fg'],
            font=('Arial', 12, 'bold')
        )
        alerts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Alerts listbox
        self.alerts_listbox = tk.Listbox(
            alerts_frame,
            bg=self.colors['entry'],
            fg=self.colors['fg'],
            font=('Arial', 11),
            height=20
        )
        self.alerts_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_control_panel(self, parent):
        """Create control panel with buttons"""
        control_frame = tk.Frame(parent, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Clear metrics button
        tk.Button(
            control_frame,
            text="Clear All Metrics",
            command=self.clear_all_metrics,
            bg=self.colors['error'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        # Clear platform button
        tk.Button(
            control_frame,
            text="Clear Platform",
            command=self.clear_platform_metrics,
            bg=self.colors['warning'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        # Export button
        tk.Button(
            control_frame,
            text="Export Logs",
            command=self.export_logs,
            bg=self.colors['button'],
            fg=self.colors['fg'],
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="Status: Active",
            bg=self.colors['bg'],
            fg=self.colors['success'],
            font=('Arial', 10)
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def update_worker(self):
        """Background thread to fetch updates"""
        while self.running:
            try:
                # Get dashboard data
                data = self.monitor.get_dashboard_data()
                self.update_queue.put(('update', data))
                
                # Sleep before next update
                time.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Update worker error: {e}")
                time.sleep(5)
    
    def process_updates(self):
        """Process updates from queue"""
        try:
            while not self.update_queue.empty():
                action, data = self.update_queue.get_nowait()
                
                if action == 'update':
                    self.update_dashboard(data)
                
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Update processing error: {e}")
        
        # Schedule next update
        if self.running:
            self.root.after(100, self.process_updates)
    
    def update_dashboard(self, data: Dict[str, Any]):
        """Update all dashboard elements"""
        try:
            # Update global metrics
            global_metrics = data.get('global_metrics', {})
            for key, label in self.global_metrics.items():
                value = global_metrics.get(key, 0)
                if key == 'global_success_rate':
                    label.config(text=f"{value:.1f}%")
                else:
                    label.config(text=str(value))
            
            # Update recent blocks
            recent_blocks = global_metrics.get('recent_blocks', [])
            self.blocks_listbox.delete(0, tk.END)
            for block in recent_blocks[-10:]:  # Show last 10
                timestamp = datetime.fromtimestamp(block['timestamp']).strftime('%H:%M:%S')
                text = f"{timestamp} - {block['platform']} - {block['event_type']} - {block['profile_id']}"
                self.blocks_listbox.insert(0, text)
            
            # Update platform metrics
            platforms = data.get('platforms', {})
            for platform, metrics in platforms.items():
                if platform not in self.platform_frames:
                    self.create_platform_metric_frame(platform, self.platforms_container)
                
                if platform in self.platform_frames:
                    _, metric_labels = self.platform_frames[platform]
                    for key, (label, unit) in metric_labels.items():
                        value = metrics.get(key, 0)
                        if isinstance(value, float):
                            label.config(text=f"{value:.1f}{unit}")
                        else:
                            label.config(text=f"{value}{unit}")
                        
                        # Color code based on value
                        if key == 'health_score':
                            if value >= 80:
                                label.config(fg=self.colors['success'])
                            elif value >= 50:
                                label.config(fg=self.colors['warning'])
                            else:
                                label.config(fg=self.colors['error'])
                        elif key == 'success_rate':
                            if value >= 90:
                                label.config(fg=self.colors['success'])
                            elif value >= 70:
                                label.config(fg=self.colors['warning'])
                            else:
                                label.config(fg=self.colors['error'])
            
            # Update alerts
            alerts = data.get('alerts', [])
            self.alerts_listbox.delete(0, tk.END)
            for alert in alerts:
                timestamp = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
                severity_icon = "🔴" if alert['severity'] == 'high' else "🟡"
                text = f"{severity_icon} {timestamp} - {alert['platform']} - {alert['message']}"
                self.alerts_listbox.insert(0, text)
                
                # Color based on severity
                if alert['severity'] == 'high':
                    self.alerts_listbox.itemconfig(0, {'fg': self.colors['error']})
                else:
                    self.alerts_listbox.itemconfig(0, {'fg': self.colors['warning']})
        
        except Exception as e:
            logger.error(f"Dashboard update error: {e}")
    
    def refresh_events(self):
        """Refresh events display"""
        try:
            # Clear existing
            for item in self.events_tree.get_children():
                self.events_tree.delete(item)
            
            # Get filter values
            platform_filter = self.platform_filter.get()
            event_filter = self.event_filter.get()
            
            # Get recent events
            events = self.monitor.get_recent_events(limit=100)
            
            # Apply filters and display
            for event in events:
                # Apply platform filter
                if platform_filter != "All" and event['platform'] != platform_filter:
                    continue
                
                # Apply event type filter
                if event_filter != "All" and event['event_type'] != event_filter:
                    continue
                
                # Format data
                timestamp = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                success = "✅" if event['success'] else "❌"
                details = json.dumps(event.get('details', {}))[:100] + "..."
                
                # Insert into tree
                self.events_tree.insert(
                    '',
                    0,
                    values=(
                        timestamp,
                        event['platform'],
                        event['event_type'],
                        event['profile_id'][:20] + "...",
                        success,
                        details
                    )
                )
        
        except Exception as e:
            logger.error(f"Events refresh error: {e}")
            messagebox.showerror("Error", f"Failed to refresh events: {str(e)}")
    
    def clear_all_metrics(self):
        """Clear all metrics after confirmation"""
        if messagebox.askyesno("Confirm", "Clear all metrics? This cannot be undone."):
            self.monitor.clear_metrics()
            messagebox.showinfo("Success", "All metrics cleared")
    
    def clear_platform_metrics(self):
        """Clear metrics for selected platform"""
        # Get platforms
        platforms = list(self.monitor.platform_metrics.keys())
        if not platforms:
            messagebox.showinfo("Info", "No platform metrics to clear")
            return
        
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Platform")
        dialog.geometry("300x150")
        
        tk.Label(dialog, text="Select platform to clear:").pack(pady=10)
        
        platform_var = tk.StringVar()
        platform_combo = ttk.Combobox(
            dialog,
            textvariable=platform_var,
            values=platforms,
            state='readonly'
        )
        platform_combo.pack(pady=10)
        platform_combo.set(platforms[0])
        
        def clear_selected():
            platform = platform_var.get()
            if platform:
                self.monitor.clear_metrics(platform)
                messagebox.showinfo("Success", f"Metrics cleared for {platform}")
                dialog.destroy()
        
        tk.Button(
            dialog,
            text="Clear",
            command=clear_selected
        ).pack(pady=10)
    
    def export_logs(self):
        """Export detection logs"""
        try:
            # Create export directory
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"detection_logs_{timestamp}.json"
            
            # Get all data
            data = {
                "export_time": datetime.now().isoformat(),
                "dashboard_data": self.monitor.get_dashboard_data(),
                "all_events": self.monitor.get_recent_events(limit=1000)
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            messagebox.showinfo("Success", f"Logs exported to {filename}")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Failed to export logs: {str(e)}")
    
    def on_closing(self):
        """Handle window close"""
        self.running = False
        self.root.destroy()


def run_detection_dashboard():
    """Run the detection dashboard"""
    root = tk.Tk()
    app = DetectionDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    run_detection_dashboard()