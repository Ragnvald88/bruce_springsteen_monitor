"""
Enhanced UI Dashboard with Statistics Display
Real-time ticket operation metrics and performance monitoring
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import tkinter.font as tkfont
from datetime import datetime
import threading
import json
import time
from typing import Dict, Any, Optional
import queue

from ..database.statistics import stats_manager
from ..utils.logging import get_logger
from ..config import config

logger = get_logger(__name__)


class EnhancedDashboard:
    """
    V4 Enhanced Dashboard with comprehensive statistics
    """
    
    def __init__(self, parent: Optional[tk.Tk] = None):
        self.parent = parent or tk.Tk()
        self.parent.title("StealthMaster V4 - Enhanced Dashboard")
        self.parent.geometry("1400x900")
        
        # Set dark theme
        self.parent.configure(bg="#1e1e1e")
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure dark theme colors
        self._setup_dark_theme(style)
        
        # Update queue for thread-safe GUI updates
        self.update_queue = queue.Queue()
        
        # Session tracking
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        stats_manager.start_session(self.session_id)
        
        # Create UI components
        self._create_header()
        self._create_statistics_panel()
        self._create_live_feed()
        self._create_platform_panels()
        self._create_performance_metrics()
        self._create_control_panel()
        
        # Start update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Process GUI updates
        self._process_updates()
        
        logger.info("Enhanced dashboard initialized")
    
    def _setup_dark_theme(self, style):
        """Configure dark theme styling"""
        # Colors
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        select_color = "#3d3d3d"
        accent_color = "#0d7377"
        success_color = "#28a745"
        danger_color = "#dc3545"
        
        # Configure styles
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TFrame", background=bg_color, borderwidth=1, relief="solid")
        style.configure("TButton", background=select_color, foreground=fg_color, borderwidth=0)
        style.map("TButton", background=[("active", accent_color)])
        
        style.configure("Success.TLabel", foreground=success_color)
        style.configure("Danger.TLabel", foreground=danger_color)
        style.configure("Accent.TLabel", foreground=accent_color)
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Heading.TLabel", font=("Arial", 12, "bold"))
    
    def _create_header(self):
        """Create header with title and session info"""
        header_frame = ttk.Frame(self.parent)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Title
        title = ttk.Label(header_frame, text="🎫 StealthMaster V4 Dashboard", style="Title.TLabel")
        title.pack(side="left", padx=10)
        
        # Session info
        self.session_label = ttk.Label(header_frame, text=f"Session: {self.session_id}", style="Accent.TLabel")
        self.session_label.pack(side="right", padx=10)
        
        # Status indicator
        self.status_label = ttk.Label(header_frame, text="● ACTIVE", style="Success.TLabel")
        self.status_label.pack(side="right", padx=10)
    
    def _create_statistics_panel(self):
        """Create main statistics overview panel"""
        stats_frame = ttk.LabelFrame(self.parent, text="📊 Overall Statistics", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Create stat cards
        self.stat_cards = {}
        stats_config = [
            ("Total Found", "total_found", "#17a2b8"),
            ("Total Reserved", "total_reserved", "#28a745"),
            ("Total Failed", "total_failed", "#dc3545"),
            ("Success Rate", "success_rate", "#ffc107"),
            ("Active Platforms", "platforms", "#6c757d"),
            ("Events Tracked", "events", "#6610f2")
        ]
        
        for i, (label, key, color) in enumerate(stats_config):
            card_frame = ttk.Frame(stats_frame)
            card_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            # Value label (big number)
            value_label = tk.Label(card_frame, text="0", font=("Arial", 24, "bold"),
                                 bg="#1e1e1e", fg=color)
            value_label.pack()
            
            # Label
            label_text = tk.Label(card_frame, text=label, font=("Arial", 10),
                                bg="#1e1e1e", fg="#888888")
            label_text.pack()
            
            self.stat_cards[key] = value_label
        
        # Configure grid weights
        for i in range(len(stats_config)):
            stats_frame.columnconfigure(i, weight=1)
    
    def _create_live_feed(self):
        """Create live activity feed"""
        feed_frame = ttk.LabelFrame(self.parent, text="🔴 Live Activity Feed", padding=10)
        feed_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create text widget for feed
        self.feed_text = scrolledtext.ScrolledText(feed_frame, height=8, wrap=tk.WORD,
                                                  bg="#2d2d2d", fg="#ffffff",
                                                  font=("Consolas", 10))
        self.feed_text.pack(fill="both", expand=True)
        
        # Configure tags for different message types
        self.feed_text.tag_config("info", foreground="#17a2b8")
        self.feed_text.tag_config("success", foreground="#28a745")
        self.feed_text.tag_config("error", foreground="#dc3545")
        self.feed_text.tag_config("warning", foreground="#ffc107")
    
    def _create_platform_panels(self):
        """Create platform-specific statistics panels"""
        platforms_frame = ttk.Frame(self.parent)
        platforms_frame.pack(fill="x", padx=10, pady=5)
        
        self.platform_stats = {}
        platforms = ["ticketmaster", "fansale", "vivaticket"]
        
        for i, platform in enumerate(platforms):
            # Platform frame
            platform_frame = ttk.LabelFrame(platforms_frame, text=f"🌐 {platform.title()}", padding=10)
            platform_frame.grid(row=0, column=i, padx=5, sticky="nsew")
            
            # Statistics
            stats_text = tk.Text(platform_frame, height=6, width=30,
                               bg="#2d2d2d", fg="#ffffff", font=("Consolas", 9))
            stats_text.pack(fill="both", expand=True)
            stats_text.insert("1.0", "Loading statistics...")
            stats_text.config(state="disabled")
            
            self.platform_stats[platform] = stats_text
        
        # Configure grid weights
        for i in range(len(platforms)):
            platforms_frame.columnconfigure(i, weight=1)
    
    def _create_performance_metrics(self):
        """Create performance metrics panel"""
        perf_frame = ttk.LabelFrame(self.parent, text="⚡ Performance Metrics", padding=10)
        perf_frame.pack(fill="x", padx=10, pady=5)
        
        # Create metric displays
        self.perf_metrics = {}
        metrics = [
            ("Avg Search Time", "avg_search", "ms"),
            ("Avg Reserve Time", "avg_reserve", "ms"),
            ("Browser Pool", "pool_size", "contexts"),
            ("Memory Usage", "memory", "MB"),
            ("CPU Usage", "cpu", "%"),
            ("Network Latency", "latency", "ms")
        ]
        
        for i, (label, key, unit) in enumerate(metrics):
            metric_frame = ttk.Frame(perf_frame)
            metric_frame.grid(row=0, column=i, padx=5, pady=5)
            
            # Label
            tk.Label(metric_frame, text=label, font=("Arial", 9),
                    bg="#1e1e1e", fg="#888888").pack()
            
            # Value
            value_label = tk.Label(metric_frame, text=f"0 {unit}",
                                 font=("Arial", 12, "bold"),
                                 bg="#1e1e1e", fg="#ffffff")
            value_label.pack()
            
            self.perf_metrics[key] = (value_label, unit)
        
        # Configure grid weights
        for i in range(len(metrics)):
            perf_frame.columnconfigure(i, weight=1)
    
    def _create_control_panel(self):
        """Create control buttons panel"""
        control_frame = ttk.Frame(self.parent)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Buttons
        ttk.Button(control_frame, text="📊 Export Stats",
                  command=self._export_stats).pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="🔄 Reset Session",
                  command=self._reset_session).pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="⚙️ Settings",
                  command=self._show_settings).pack(side="left", padx=5)
        
        # Session duration
        self.duration_label = ttk.Label(control_frame, text="Duration: 00:00:00")
        self.duration_label.pack(side="right", padx=10)
    
    def add_log_entry(self, message: str, level: str = "info"):
        """Add entry to live feed"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self.update_queue.put(("log", entry, level))
    
    def update_stats(self):
        """Update all statistics displays"""
        try:
            # Get summary from database
            summary = stats_manager.get_summary()
            
            # Update stat cards
            self.update_queue.put(("stats", summary))
            
            # Update platform stats
            for platform_data in summary.get("platform_breakdown", []):
                platform = platform_data["platform"]
                self.update_queue.put(("platform", platform, platform_data))
            
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")
    
    def _update_loop(self):
        """Background thread for periodic updates"""
        start_time = time.time()
        
        while self.running:
            try:
                # Update stats every 2 seconds
                self.update_stats()
                
                # Update duration
                duration = int(time.time() - start_time)
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.update_queue.put(("duration", duration_str))
                
                # Update performance metrics (mock data for now)
                perf_data = {
                    "avg_search": 250,
                    "avg_reserve": 180,
                    "pool_size": 10,
                    "memory": 320,
                    "cpu": 15,
                    "latency": 45
                }
                self.update_queue.put(("performance", perf_data))
                
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
                        self.feed_text.insert(tk.END, entry, level)
                        self.feed_text.see(tk.END)
                        
                        # Limit feed size
                        lines = int(self.feed_text.index('end-1c').split('.')[0])
                        if lines > 100:
                            self.feed_text.delete('1.0', '2.0')
                    
                    elif update[0] == "stats":
                        _, summary = update
                        self.stat_cards["total_found"].config(text=str(summary["total_found"]))
                        self.stat_cards["total_reserved"].config(text=str(summary["total_reserved"]))
                        self.stat_cards["total_failed"].config(text=str(summary["total_failed"]))
                        self.stat_cards["success_rate"].config(text=f"{summary['overall_success_rate']:.1f}%")
                        self.stat_cards["platforms"].config(text=str(summary["platforms_used"]))
                        self.stat_cards["events"].config(text=str(summary["events_tracked"]))
                    
                    elif update[0] == "platform":
                        _, platform, data = update
                        if platform in self.platform_stats:
                            stats_text = self.platform_stats[platform]
                            stats_text.config(state="normal")
                            stats_text.delete("1.0", tk.END)
                            
                            text = f"Found: {data['found']}\n"
                            text += f"Reserved: {data['reserved']}\n"
                            text += f"Failed: {data['failed']}\n"
                            text += f"Success Rate: {data['success_rate']:.1f}%\n"
                            text += f"Avg Search: {data['avg_search_ms']:.0f}ms\n"
                            text += f"Avg Reserve: {data['avg_reserve_ms']:.0f}ms"
                            
                            stats_text.insert("1.0", text)
                            stats_text.config(state="disabled")
                    
                    elif update[0] == "duration":
                        _, duration = update
                        self.duration_label.config(text=f"Duration: {duration}")
                    
                    elif update[0] == "performance":
                        _, perf_data = update
                        for key, value in perf_data.items():
                            if key in self.perf_metrics:
                                label, unit = self.perf_metrics[key]
                                label.config(text=f"{value} {unit}")
                    
                except queue.Empty:
                    break
            
        except Exception as e:
            logger.error(f"GUI update error: {e}")
        
        # Schedule next update
        self.parent.after(100, self._process_updates)
    
    def _export_stats(self):
        """Export statistics to file"""
        try:
            from tkinter import filedialog, messagebox
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                format = "csv" if filename.endswith(".csv") else "json"
                data = stats_manager.export_stats(format)
                
                with open(filename, "w") as f:
                    f.write(data)
                
                messagebox.showinfo("Export Complete", f"Statistics exported to {filename}")
                self.add_log_entry(f"Exported statistics to {filename}", "success")
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.add_log_entry(f"Export failed: {e}", "error")
    
    def _reset_session(self):
        """Reset current session"""
        try:
            # End current session
            stats_manager.end_session(self.session_id)
            
            # Start new session
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            stats_manager.start_session(self.session_id)
            
            # Update UI
            self.session_label.config(text=f"Session: {self.session_id}")
            self.add_log_entry("Session reset", "warning")
            
        except Exception as e:
            logger.error(f"Session reset failed: {e}")
    
    def _show_settings(self):
        """Show settings dialog"""
        # Placeholder for settings dialog
        self.add_log_entry("Settings dialog not implemented yet", "info")
    
    def run(self):
        """Start the dashboard"""
        self.parent.mainloop()
    
    def close(self):
        """Clean up and close dashboard"""
        self.running = False
        stats_manager.end_session(self.session_id)
        self.parent.quit()


def launch_dashboard():
    """Launch the enhanced dashboard"""
    dashboard = EnhancedDashboard()
    
    # Handle window close
    dashboard.parent.protocol("WM_DELETE_WINDOW", dashboard.close)
    
    dashboard.run()


if __name__ == "__main__":
    launch_dashboard()