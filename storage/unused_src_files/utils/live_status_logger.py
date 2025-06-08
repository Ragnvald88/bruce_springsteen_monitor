#!/usr/bin/env python3
"""
🎸 Live Status Logger - Real-Time Bruce Springsteen Ticket Hunter Status
Provides comprehensive real-time logging with visual status indicators
"""

import logging
import time
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class StatusLevel(Enum):
    """Status levels for live updates"""
    SUCCESS = "SUCCESS"
    WARNING = "WARNING" 
    ERROR = "ERROR"
    INFO = "INFO"
    CRITICAL = "CRITICAL"
    PROGRESS = "PROGRESS"

@dataclass
class StatusUpdate:
    """Real-time status update"""
    timestamp: datetime
    level: StatusLevel
    category: str  # e.g., "BROWSER", "AUTH", "TICKETS", "NETWORK"
    message: str
    details: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None  # 0-100 for progress bars

class LiveStatusLogger:
    """Enhanced real-time status logger with visual feedback"""
    
    def __init__(self, enable_gui_updates: bool = False):
        self.enable_gui_updates = enable_gui_updates
        self.status_queue = queue.Queue()
        self.gui_callback: Optional[Callable] = None
        
        # Status tracking
        self.current_status: Dict[str, StatusUpdate] = {}
        self.status_history: List[StatusUpdate] = []
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        
        # Visual indicators
        self.icons = {
            StatusLevel.SUCCESS: "✅",
            StatusLevel.WARNING: "⚠️",
            StatusLevel.ERROR: "❌", 
            StatusLevel.INFO: "ℹ️",
            StatusLevel.CRITICAL: "🚨",
            StatusLevel.PROGRESS: "🔄"
        }
        
        self.colors = {
            StatusLevel.SUCCESS: Fore.GREEN,
            StatusLevel.WARNING: Fore.YELLOW,
            StatusLevel.ERROR: Fore.RED,
            StatusLevel.INFO: Fore.CYAN,
            StatusLevel.CRITICAL: Fore.RED + Style.BRIGHT,
            StatusLevel.PROGRESS: Fore.BLUE
        }
        
        # Start background status processor
        self.processing = True
        self.processor_thread = threading.Thread(target=self._process_status_updates, daemon=True)
        self.processor_thread.start()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def set_gui_callback(self, callback: Callable):
        """Set callback function for GUI updates"""
        self.gui_callback = callback
        self.enable_gui_updates = True
    
    def log_status(self, level: StatusLevel, category: str, message: str, 
                   details: Optional[Dict[str, Any]] = None, progress: Optional[float] = None):
        """Log a status update with real-time display"""
        update = StatusUpdate(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            details=details or {},
            progress=progress
        )
        
        # Store current status per category
        self.current_status[category] = update
        self.status_history.append(update)
        
        # Keep history manageable
        if len(self.status_history) > 1000:
            self.status_history = self.status_history[-500:]
        
        # Queue for processing
        self.status_queue.put(update)
        
        # Immediate console output for critical updates
        if level in [StatusLevel.CRITICAL, StatusLevel.ERROR]:
            self._print_status_immediately(update)
    
    def start_operation(self, operation_id: str, description: str, estimated_duration: Optional[float] = None):
        """Start tracking a long-running operation"""
        self.active_operations[operation_id] = {
            'description': description,
            'start_time': time.time(),
            'estimated_duration': estimated_duration,
            'progress': 0.0,
            'status': 'running'
        }
        
        self.log_status(StatusLevel.PROGRESS, "OPERATION", f"Starting: {description}", 
                       {"operation_id": operation_id})
    
    def update_operation_progress(self, operation_id: str, progress: float, message: Optional[str] = None):
        """Update progress of an active operation"""
        if operation_id in self.active_operations:
            self.active_operations[operation_id]['progress'] = progress
            
            description = self.active_operations[operation_id]['description']
            display_msg = message or f"{description} - {progress:.1f}%"
            
            self.log_status(StatusLevel.PROGRESS, "OPERATION", display_msg,
                           {"operation_id": operation_id}, progress)
    
    def complete_operation(self, operation_id: str, success: bool = True, message: Optional[str] = None):
        """Complete an active operation"""
        if operation_id in self.active_operations:
            operation = self.active_operations[operation_id]
            duration = time.time() - operation['start_time']
            
            level = StatusLevel.SUCCESS if success else StatusLevel.ERROR
            final_msg = message or f"{operation['description']} {'completed' if success else 'failed'} ({duration:.1f}s)"
            
            self.log_status(level, "OPERATION", final_msg, 
                           {"operation_id": operation_id, "duration": duration})
            
            operation['status'] = 'completed' if success else 'failed'
    
    def log_browser_status(self, action: str, success: bool = True, details: Optional[Dict] = None):
        """Log browser-related status"""
        level = StatusLevel.SUCCESS if success else StatusLevel.ERROR
        icon = "🌐" if success else "💥"
        self.log_status(level, "BROWSER", f"{icon} {action}", details)
    
    def log_auth_status(self, platform: str, success: bool, details: Optional[Dict] = None):
        """Log authentication status"""
        level = StatusLevel.SUCCESS if success else StatusLevel.ERROR
        icon = "🔐" if success else "🔒"
        message = f"{icon} {platform} authentication {'successful' if success else 'failed'}"
        self.log_status(level, "AUTH", message, details)
    
    def log_ticket_status(self, event: str, tickets_found: int = 0, details: Optional[Dict] = None):
        """Log ticket detection status"""
        if tickets_found > 0:
            level = StatusLevel.CRITICAL
            icon = "🎫"
            message = f"{icon} TICKETS FOUND! {tickets_found} available for {event}"
        else:
            level = StatusLevel.INFO
            icon = "🔍"
            message = f"{icon} Monitoring {event} - No tickets available"
        
        self.log_status(level, "TICKETS", message, details)
    
    def log_network_status(self, action: str, status_code: Optional[int] = None, 
                          response_time: Optional[float] = None, blocked: bool = False):
        """Log network request status"""
        if blocked:
            level = StatusLevel.ERROR
            icon = "🚫"
            message = f"{icon} BLOCKED - {action}"
        elif status_code and status_code >= 400:
            level = StatusLevel.WARNING
            icon = "⚠️"
            message = f"{icon} HTTP {status_code} - {action}"
        else:
            level = StatusLevel.SUCCESS
            icon = "🌐"
            message = f"{icon} {action}"
            if response_time:
                message += f" ({response_time:.0f}ms)"
        
        details = {}
        if status_code:
            details['status_code'] = status_code
        if response_time:
            details['response_time'] = response_time
        
        self.log_status(level, "NETWORK", message, details)
    
    def _process_status_updates(self):
        """Background thread to process status updates"""
        while self.processing:
            try:
                # Process queued updates
                while not self.status_queue.empty():
                    update = self.status_queue.get_nowait()
                    self._display_status_update(update)
                    
                    # Send to GUI if enabled
                    if self.enable_gui_updates and self.gui_callback:
                        try:
                            self.gui_callback(update)
                        except Exception as e:
                            self.logger.debug(f"GUI callback error: {e}")
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Status processor error: {e}")
                time.sleep(1)
    
    def _display_status_update(self, update: StatusUpdate):
        """Display a status update in the console"""
        icon = self.icons.get(update.level, "")
        color = self.colors.get(update.level, "")
        
        # Format timestamp
        timestamp = update.timestamp.strftime("%H:%M:%S")
        
        # Build progress bar if available
        progress_bar = ""
        if update.progress is not None:
            bar_length = 20
            filled_length = int(bar_length * update.progress / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            progress_bar = f" [{bar}] {update.progress:.1f}%"
        
        # Format message
        formatted_message = f"{color}{icon} [{timestamp}] {update.category}: {update.message}{progress_bar}{Style.RESET_ALL}"
        
        print(formatted_message)
        
        # Log to file as well
        self.logger.info(f"[{update.category}] {update.message}")
    
    def _print_status_immediately(self, update: StatusUpdate):
        """Immediately print critical status updates"""
        icon = self.icons.get(update.level, "")
        color = self.colors.get(update.level, "")
        
        print(f"\n{color}{Style.BRIGHT}{icon} ALERT: {update.message}{Style.RESET_ALL}\n")
    
    def get_status_dashboard(self) -> str:
        """Get current status dashboard as formatted string"""
        dashboard = f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n"
        dashboard += f"{Fore.YELLOW}🎸 BRUCE SPRINGSTEEN TICKET HUNTER - LIVE STATUS{Style.RESET_ALL}\n"
        dashboard += f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n\n"
        
        # Current status by category
        categories = ["BROWSER", "AUTH", "TICKETS", "NETWORK", "OPERATION"]
        for category in categories:
            if category in self.current_status:
                update = self.current_status[category]
                icon = self.icons.get(update.level, "")
                color = self.colors.get(update.level, "")
                age = (datetime.now() - update.timestamp).total_seconds()
                
                dashboard += f"{color}{icon} {category}: {update.message}{Style.RESET_ALL}"
                if age < 60:
                    dashboard += f" ({age:.0f}s ago)"
                dashboard += "\n"
        
        # Active operations
        if self.active_operations:
            dashboard += f"\n{Fore.BLUE}🔄 ACTIVE OPERATIONS:{Style.RESET_ALL}\n"
            for op_id, op_data in self.active_operations.items():
                if op_data['status'] == 'running':
                    progress = op_data['progress']
                    desc = op_data['description']
                    dashboard += f"   • {desc}: {progress:.1f}%\n"
        
        dashboard += f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n"
        return dashboard
    
    def print_dashboard(self):
        """Print the current status dashboard"""
        print(self.get_status_dashboard())
    
    def stop(self):
        """Stop the status logger"""
        self.processing = False
        if self.processor_thread.is_alive():
            self.processor_thread.join(timeout=2.0)

# Global instance
_live_status_logger: Optional[LiveStatusLogger] = None

def get_live_status_logger() -> LiveStatusLogger:
    """Get the global live status logger instance"""
    global _live_status_logger
    if _live_status_logger is None:
        _live_status_logger = LiveStatusLogger()
    return _live_status_logger

def init_live_status_logging(enable_gui: bool = False) -> LiveStatusLogger:
    """Initialize live status logging"""
    global _live_status_logger
    _live_status_logger = LiveStatusLogger(enable_gui_updates=enable_gui)
    return _live_status_logger

# Convenience functions
def log_browser_status(action: str, success: bool = True, details: Optional[Dict] = None):
    get_live_status_logger().log_browser_status(action, success, details)

def log_auth_status(platform: str, success: bool, details: Optional[Dict] = None):
    get_live_status_logger().log_auth_status(platform, success, details)

def log_ticket_status(event: str, tickets_found: int = 0, details: Optional[Dict] = None):
    get_live_status_logger().log_ticket_status(event, tickets_found, details)

def log_network_status(action: str, status_code: Optional[int] = None, 
                      response_time: Optional[float] = None, blocked: bool = False):
    get_live_status_logger().log_network_status(action, status_code, response_time, blocked)

def start_operation(operation_id: str, description: str, estimated_duration: Optional[float] = None):
    get_live_status_logger().start_operation(operation_id, description, estimated_duration)

def update_operation_progress(operation_id: str, progress: float, message: Optional[str] = None):
    get_live_status_logger().update_operation_progress(operation_id, progress, message)

def complete_operation(operation_id: str, success: bool = True, message: Optional[str] = None):
    get_live_status_logger().complete_operation(operation_id, success, message)

def print_status_dashboard():
    get_live_status_logger().print_dashboard()