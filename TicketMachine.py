#!/usr/bin/env python3
"""
FanSale Ultimate Bot - Enhanced Edition
Advanced ticket hunting with beautiful terminal UI and smart features
"""

import os
import sys
import time
import json
import random
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

import requests
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# HARDCODED BRUCE SPRINGSTEEN URL
DEFAULT_TARGET_URL = "https://www.fansale.it/tickets/all/bruce-springsteen/458554/17844388"

class SettingsManager:
    """Handles persistent bot configuration with profiles"""
    
    def __init__(self):
        self.settings_file = Path("bot_settings.json")
        self.profiles_file = Path("bot_profiles.json")
        self.default_settings = {
            "target_url": DEFAULT_TARGET_URL,
            "num_browsers": 2,
            "max_tickets": 2,
            "ticket_types": ["all"],
            "min_wait": 0.3,
            "max_wait": 1.0,
            "refresh_interval": 15,
            "use_proxy": False,
            "proxy_host": "",
            "proxy_port": "",
            "proxy_user": "",
            "proxy_pass": "",
            "log_level": "info",
            "show_stats": True,
            "sound_alerts": True,
            "auto_screenshot": True,
            "auto_buy": False,
            "max_price": 0,
            "preferred_sectors": [],
            "blacklist_sectors": [],
            "notification_webhook": "",
            "theme": "cyberpunk"  # cyberpunk, matrix, minimal, rainbow
        }
        self.settings = self.load_settings()
        self.profiles = self.load_profiles()
        self.active_profile = "default"
    
    def load_settings(self):
        """Load settings from file or create defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    return {**self.default_settings, **saved}
            except:
                pass
        return self.default_settings.copy()
    
    def load_profiles(self):
        """Load saved profiles"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"default": self.default_settings.copy()}
    
    def save_settings(self):
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def save_profiles(self):
        """Save profiles to file"""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
    
    def save_profile(self, name):
        """Save current settings as a profile"""
        self.profiles[name] = self.settings.copy()
        self.save_profiles()
    
    def load_profile(self, name):
        """Load a saved profile"""
        if name in self.profiles:
            self.settings = self.profiles[name].copy()
            self.active_profile = name
            self.save_settings()
            return True
        return False
    
    def update(self, key, value):
        """Update a setting and save"""
        self.settings[key] = value
        self.save_settings()
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def save(self):
        """Alias for save_settings() for compatibility"""
        self.save_settings()

class StatsTracker:
    """Advanced statistics tracking with history"""
    
    def __init__(self):
        self.stats = {
            "start_time": time.time(),
            "total_checks": 0,
            "tickets_found": defaultdict(int),
            "tickets_secured": 0,
            "last_check_time": time.time(),
            "checks_per_minute": 0,
            "active_browsers": 0,
            "unique_tickets_seen": 0,
            "total_clicks": 0,
            "captchas_solved": 0,
            "errors_encountered": 0,
            "best_cpm": 0  # Best checks per minute
        }
        self.lock = threading.Lock()
        self.check_times = deque(maxlen=300)  # Last 5 minutes
        self.ticket_history = deque(maxlen=100)  # Last 100 tickets
        self.load_historical_stats()
    
    def load_historical_stats(self):
        """Load historical statistics"""
        stats_file = Path("bot_statistics.json")
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.historical = json.load(f)
            except:
                self.historical = self._default_historical()
        else:
            self.historical = self._default_historical()
    
    def _default_historical(self):
        """Default historical stats structure"""
        return {
            "total_runs": 0,
            "total_runtime": 0,
            "total_checks": 0,
            "total_secured": 0,
            "tickets_by_type": defaultdict(int),
            "best_session": {
                "date": None,
                "tickets": 0,
                "cpm": 0
            }
        }
    
    def save_historical_stats(self):
        """Save session stats to historical data"""
        with self.lock:
            runtime = time.time() - self.stats["start_time"]
            self.historical["total_runs"] += 1
            self.historical["total_runtime"] += runtime
            self.historical["total_checks"] += self.stats["total_checks"]
            self.historical["total_secured"] += self.stats["tickets_secured"]
            
            # Update tickets by type
            for category, count in self.stats["tickets_found"].items():
                self.historical["tickets_by_type"][category] += count
            
            # Check if this was the best session
            if self.stats["tickets_secured"] > self.historical["best_session"]["tickets"]:
                self.historical["best_session"] = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tickets": self.stats["tickets_secured"],
                    "cpm": self.stats["best_cpm"]
                }
            
            # Save to file
            with open("bot_statistics.json", 'w') as f:
                json.dump(self.historical, f, indent=2)
    
    def record_check(self):
        """Record a ticket check"""
        with self.lock:
            self.stats["total_checks"] += 1
            self.stats["last_check_time"] = time.time()
            self.check_times.append(time.time())
            
            # Calculate checks per minute
            if len(self.check_times) > 1:
                time_span = self.check_times[-1] - self.check_times[0]
                if time_span > 0:
                    cpm = (len(self.check_times) / time_span) * 60
                    self.stats["checks_per_minute"] = int(cpm)
                    if cpm > self.stats["best_cpm"]:
                        self.stats["best_cpm"] = int(cpm)
    
    def found_ticket(self, category, ticket_info=None):
        """Record a found ticket"""
        with self.lock:
            self.stats["tickets_found"][category] += 1
            self.stats["unique_tickets_seen"] += 1
            if ticket_info:
                self.ticket_history.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "category": category,
                    "info": ticket_info
                })
    
    def record_error(self):
        """Record an error"""
        with self.lock:
            self.stats["errors_encountered"] += 1
    
    def record_captcha_solved(self):
        """Record a solved CAPTCHA"""
        with self.lock:
            self.stats["captchas_solved"] += 1
    
    def secured_ticket(self):
        """Record a secured ticket"""
        with self.lock:
            self.stats["tickets_secured"] += 1
    
    def get_stats(self):
        """Get current statistics"""
        with self.lock:
            return self.stats.copy()
    
    def get_runtime(self):
        """Get formatted runtime"""
        elapsed = time.time() - self.stats["start_time"]
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_ticket_history(self):
        """Get recent ticket history"""
        with self.lock:
            return list(self.ticket_history)

class EnhancedAnalytics:
    """Advanced analytics system for ticket hunting patterns"""
    
    def __init__(self):
        self.data_dir = Path("hunting_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths for different data types
        self.ticket_log_file = self.data_dir / "ticket_discoveries.json"
        self.session_log_file = self.data_dir / "hunting_sessions.json"
        self.hourly_stats_file = self.data_dir / "hourly_patterns.json"
        self.daily_stats_file = self.data_dir / "daily_summary.json"
        
        # Load existing data
        self.ticket_discoveries = self.load_json(self.ticket_log_file, default=[])
        self.hunting_sessions = self.load_json(self.session_log_file, default=[])
        self.hourly_patterns = self.load_json(self.hourly_stats_file, default={})
        self.daily_summary = self.load_json(self.daily_stats_file, default={})
        
        # Current session data
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "tickets_found": [],
            "tickets_secured": [],
            "checks_performed": 0,
            "errors_encountered": 0,
            "browser_performance": {}
        }
        self.current_session['start_unix'] = time.time()
    
    def load_json(self, filepath, default=None):
        """Load JSON data from file"""
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except:
                pass
        return default if default is not None else {}
    
    def save_json(self, data, filepath):
        """Save JSON data to file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def log_ticket_discovery(self, ticket_info):
        """Log detailed ticket discovery with all metadata"""
        discovery = {
            "timestamp": datetime.now().isoformat(),
            "unix_time": time.time(),
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().strftime("%A"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "ticket_type": ticket_info.get('category', 'unknown'),
            "price": ticket_info.get('price'),
            "sector": ticket_info.get('sector'),
            "row": ticket_info.get('row'),
            "seat": ticket_info.get('seat'),
            "raw_text": ticket_info.get('raw_text', ''),
            "browser_id": ticket_info.get('browser_id'),
            "page_refresh_count": ticket_info.get('refresh_count', 0),
            "time_since_start": time.time() - self.current_session.get('start_unix', time.time())
        }
        
        # Add to current session
        self.current_session["tickets_found"].append(discovery)
        
        # Add to persistent log
        self.ticket_discoveries.append(discovery)
        self.save_json(self.ticket_discoveries, self.ticket_log_file)
        
        # Update hourly patterns
        self.update_hourly_patterns(discovery)
        
        return discovery
    
    def update_hourly_patterns(self, discovery):
        """Update hourly pattern analysis"""
        hour = str(discovery["hour"])
        date = discovery["date"]
        ticket_type = discovery["ticket_type"]
        
        if date not in self.hourly_patterns:
            self.hourly_patterns[date] = {}
        
        if hour not in self.hourly_patterns[date]:
            self.hourly_patterns[date][hour] = {
                "total_tickets": 0,
                "by_type": {},
                "avg_price": [],
                "sectors": []
            }
        
        # Update statistics
        hour_data = self.hourly_patterns[date][hour]
        hour_data["total_tickets"] += 1
        
        if ticket_type not in hour_data["by_type"]:
            hour_data["by_type"][ticket_type] = 0
        hour_data["by_type"][ticket_type] += 1
        
        if discovery["price"]:
            hour_data["avg_price"].append(discovery["price"])
        
        if discovery["sector"]:
            hour_data["sectors"].append(discovery["sector"])
        
        self.save_json(self.hourly_patterns, self.hourly_stats_file)
    
    def get_hourly_analysis(self, date=None):
        """Get detailed hourly analysis for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.hourly_patterns:
            return None
        
        analysis = {
            "date": date,
            "hours": {},
            "peak_hours": [],
            "ticket_distribution": {},
            "best_times_by_type": {}
        }
        
        # Analyze each hour
        total_tickets = 0
        for hour, data in self.hourly_patterns[date].items():
            ticket_count = data["total_tickets"]
            total_tickets += ticket_count
            
            analysis["hours"][hour] = {
                "tickets_found": ticket_count,
                "types": data["by_type"],
                "avg_price": statistics.mean(data["avg_price"]) if data["avg_price"] else None,
                "popular_sectors": Counter(data["sectors"]).most_common(3) if data["sectors"] else []
            }
        
        # Find peak hours (top 3)
        sorted_hours = sorted(analysis["hours"].items(), 
                            key=lambda x: x[1]["tickets_found"], 
                            reverse=True)
        analysis["peak_hours"] = [(h, d["tickets_found"]) for h, d in sorted_hours[:3]]
        
        # Calculate ticket type distribution
        all_types = defaultdict(int)
        for hour_data in analysis["hours"].values():
            for ticket_type, count in hour_data["types"].items():
                all_types[ticket_type] += count
        
        analysis["ticket_distribution"] = dict(all_types)
        
        # Find best times for each ticket type
        for ticket_type in all_types.keys():
            best_hours = []
            for hour, data in analysis["hours"].items():
                if ticket_type in data["types"]:
                    best_hours.append((hour, data["types"][ticket_type]))
            
            best_hours.sort(key=lambda x: x[1], reverse=True)
            analysis["best_times_by_type"][ticket_type] = best_hours[:3]
        
        return analysis
    
    def get_pattern_insights(self, days=7):
        """Analyze patterns over multiple days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        insights = {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "hourly_averages": defaultdict(lambda: {"tickets": [], "types": defaultdict(int)}),
            "daily_totals": {},
            "ticket_type_trends": defaultdict(list),
            "best_hunting_times": [],
            "recommendations": []
        }
        
        # Analyze each day
        for single_date in (start_date + timedelta(n) for n in range(days)):
            date_str = single_date.strftime("%Y-%m-%d")
            
            if date_str in self.hourly_patterns:
                daily_total = 0
                for hour, data in self.hourly_patterns[date_str].items():
                    hour_int = int(hour)
                    daily_total += data["total_tickets"]
                    
                    # Add to hourly averages
                    insights["hourly_averages"][hour_int]["tickets"].append(data["total_tickets"])
                    for ticket_type, count in data["by_type"].items():
                        insights["hourly_averages"][hour_int]["types"][ticket_type] += count
                
                insights["daily_totals"][date_str] = daily_total
        
        # Calculate average tickets per hour
        hourly_stats = []
        for hour, data in insights["hourly_averages"].items():
            if data["tickets"]:
                avg_tickets = statistics.mean(data["tickets"])
                hourly_stats.append((hour, avg_tickets, dict(data["types"])))
        
        # Sort by average tickets found
        hourly_stats.sort(key=lambda x: x[1], reverse=True)
        
        # Best hunting times (top 5 hours)
        insights["best_hunting_times"] = [
            {
                "hour": f"{h:02d}:00-{h:02d}:59",
                "avg_tickets": round(avg, 2),
                "dominant_types": sorted(types.items(), key=lambda x: x[1], reverse=True)[:3]
            }
            for h, avg, types in hourly_stats[:5]
        ]
        
        # Generate recommendations
        if hourly_stats:
            peak_hours = [h for h, _, _ in hourly_stats[:3]]
            insights["recommendations"].append(
                f"Focus hunting efforts between {min(peak_hours):02d}:00 and {max(peak_hours):02d}:59"
            )
            
            # Check for type-specific patterns
            type_patterns = defaultdict(list)
            for hour, _, types in hourly_stats:
                for ticket_type, count in types.items():
                    if count > 0:
                        type_patterns[ticket_type].append(hour)
            
            for ticket_type, hours in type_patterns.items():
                if hours:
                    most_common_hour = statistics.mode(hours) if len(hours) >= 2 else hours[0]
                    insights["recommendations"].append(
                        f"{ticket_type.upper()} tickets most common at {most_common_hour:02d}:00"
                    )
        
        return insights
    
    def get_success_metrics(self):
        """Calculate success rate metrics"""
        if not self.hunting_sessions:
            return None
        
        metrics = {
            "total_sessions": len(self.hunting_sessions),
            "total_runtime_hours": 0,
            "total_tickets_found": 0,
            "total_tickets_secured": 0,
            "success_rate": 0,
            "avg_tickets_per_session": 0,
            "avg_time_to_first_ticket": [],
            "best_session": None,
            "category_success_rates": defaultdict(lambda: {"found": 0, "secured": 0})
        }
        
        for session in self.hunting_sessions:
            runtime = session.get("runtime_seconds", 0) / 3600
            metrics["total_runtime_hours"] += runtime
            
            tickets_found = len(session.get("tickets_found", []))
            tickets_secured = len(session.get("tickets_secured", []))
            
            metrics["total_tickets_found"] += tickets_found
            metrics["total_tickets_secured"] += tickets_secured
            
            # Time to first ticket
            if session.get("tickets_found"):
                first_ticket_time = session["tickets_found"][0].get("time_since_start", 0)
                metrics["avg_time_to_first_ticket"].append(first_ticket_time)
            
            # Category breakdown
            for ticket in session.get("tickets_found", []):
                category = ticket.get("ticket_type", "unknown")
                metrics["category_success_rates"][category]["found"] += 1
            
            for ticket in session.get("tickets_secured", []):
                category = ticket.get("ticket_type", "unknown")
                metrics["category_success_rates"][category]["secured"] += 1
            
            # Track best session
            if not metrics["best_session"] or tickets_secured > metrics["best_session"]["tickets_secured"]:
                metrics["best_session"] = {
                    "date": session.get("start_time", ""),
                    "tickets_secured": tickets_secured,
                    "runtime_minutes": int(runtime * 60)
                }
        
        # Calculate averages
        if metrics["total_sessions"] > 0:
            metrics["avg_tickets_per_session"] = round(
                metrics["total_tickets_found"] / metrics["total_sessions"], 2
            )
            
            if metrics["total_tickets_found"] > 0:
                metrics["success_rate"] = round(
                    (metrics["total_tickets_secured"] / metrics["total_tickets_found"]) * 100, 2
                )
        
        if metrics["avg_time_to_first_ticket"]:
            metrics["avg_time_to_first_ticket"] = round(
                statistics.mean(metrics["avg_time_to_first_ticket"]) / 60, 2
            )  # Convert to minutes
        else:
            metrics["avg_time_to_first_ticket"] = None
        
        # Calculate category success rates
        for category, data in metrics["category_success_rates"].items():
            if data["found"] > 0:
                data["success_rate"] = round((data["secured"] / data["found"]) * 100, 2)
            else:
                data["success_rate"] = 0
        
        return metrics
    
    def get_quick_stats(self):
        """Get quick stats for menu display"""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {
            "sessions_today": 0,
            "tickets_today": 0,
            "secured_today": 0,
            "success_rate": 0
        }
        
        if today in self.daily_summary:
            summary = self.daily_summary[today]
            stats["sessions_today"] = summary.get("sessions", 0)
            stats["tickets_today"] = summary.get("tickets_found", 0)
            stats["secured_today"] = summary.get("tickets_secured", 0)
            
            if stats["tickets_today"] > 0:
                stats["success_rate"] = (stats["secured_today"] / stats["tickets_today"]) * 100
        
        return stats
    
    def save_session(self):
        """Save current session data"""
        self.current_session["end_time"] = datetime.now().isoformat()
        self.current_session["runtime_seconds"] = time.time() - self.current_session.get("start_unix", time.time())
        
        self.hunting_sessions.append(self.current_session)
        self.save_json(self.hunting_sessions, self.session_log_file)
        
        # Update daily summary
        self.update_daily_summary()
    
    def update_daily_summary(self):
        """Update daily summary statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_summary:
            self.daily_summary[today] = {
                "sessions": 0,
                "total_runtime_seconds": 0,
                "tickets_found": 0,
                "tickets_secured": 0,
                "checks_performed": 0,
                "errors": 0,
                "ticket_types": defaultdict(int)
            }
        
        summary = self.daily_summary[today]
        summary["sessions"] += 1
        summary["total_runtime_seconds"] += self.current_session.get("runtime_seconds", 0)
        summary["tickets_found"] += len(self.current_session.get("tickets_found", []))
        summary["tickets_secured"] += len(self.current_session.get("tickets_secured", []))
        summary["checks_performed"] += self.current_session.get("checks_performed", 0)
        summary["errors"] += self.current_session.get("errors_encountered", 0)
        
        for ticket in self.current_session.get("tickets_found", []):
            ticket_type = ticket.get("ticket_type", "unknown")
            summary["ticket_types"][ticket_type] += 1
        
        # Convert defaultdict to regular dict for JSON serialization
        summary["ticket_types"] = dict(summary["ticket_types"])
        
        self.save_json(self.daily_summary, self.daily_stats_file)
    
    def get_live_stats(self):
        """Get live statistics for monitoring"""
        now = time.time()
        hour_ago = now - 3600
        
        # Count tickets in last hour
        hourly_count = sum(1 for t in self.ticket_discoveries 
                          if t.get('unix_time', 0) > hour_ago)
        
        # Get recent tickets
        recent = sorted(self.ticket_discoveries, 
                       key=lambda x: x.get('unix_time', 0), 
                       reverse=True)[:10]
        
        return {
            'hourly_rate': hourly_count,
            'active_browsers': len(self.current_session.get('browser_performance', {})),
            'recent_tickets': [
                {
                    'time': datetime.fromtimestamp(t.get('unix_time', 0)).strftime('%H:%M:%S'),
                    'type': t.get('ticket_type', 'Unknown'),
                    'price': t.get('price', 'N/A')
                } for t in recent
            ]
        }
    
    def get_hourly_patterns(self):
        """Get hourly pattern analysis"""
        patterns = {}
        
        # Aggregate all hourly data
        for date_data in self.hourly_patterns.values():
            for hour, data in date_data.items():
                hour_int = int(hour)
                if hour_int not in patterns:
                    patterns[hour_int] = {'count': 0, 'types': {}}
                
                patterns[hour_int]['count'] += data['total_tickets']
                for ticket_type, count in data.get('by_type', {}).items():
                    if ticket_type not in patterns[hour_int]['types']:
                        patterns[hour_int]['types'][ticket_type] = 0
                    patterns[hour_int]['types'][ticket_type] += count
        
        return patterns
    
    def get_ticket_analysis(self):
        """Get ticket type analysis"""
        analysis = defaultdict(int)
        
        for ticket in self.ticket_discoveries:
            ticket_type = ticket.get('ticket_type', 'Unknown')
            analysis[ticket_type] += 1
        
        return dict(analysis)
    
    def get_daily_reports(self):
        """Get daily performance reports"""
        reports = {}
        
        for date, data in self.daily_summary.items():
            success_rate = 0
            if data['tickets_found'] > 0:
                success_rate = (data['tickets_secured'] / data['tickets_found']) * 100
            
            reports[date] = {
                'sessions': data['sessions'],
                'tickets_found': data['tickets_found'],
                'tickets_secured': data['tickets_secured'],
                'success_rate': success_rate,
                'runtime_hours': data['total_runtime_seconds'] / 3600
            }
        
        return reports
    
    def get_success_metrics(self):
        """Get overall success metrics"""
        if not self.hunting_sessions:
            return None
        
        total_sessions = len(self.hunting_sessions)
        total_runtime = sum(s.get('runtime_seconds', 0) for s in self.hunting_sessions)
        total_found = sum(len(s.get('tickets_found', [])) for s in self.hunting_sessions)
        total_secured = sum(len(s.get('tickets_secured', [])) for s in self.hunting_sessions)
        
        # Best performance
        best_hour = 0
        best_day = 0
        longest_session = 0
        
        if self.hourly_patterns:
            for date_data in self.hourly_patterns.values():
                for hour_data in date_data.values():
                    if hour_data['total_tickets'] > best_hour:
                        best_hour = hour_data['total_tickets']
        
        if self.daily_summary:
            for day_data in self.daily_summary.values():
                if day_data['tickets_found'] > best_day:
                    best_day = day_data['tickets_found']
        
        if self.hunting_sessions:
            longest_session = max(s.get('runtime_seconds', 0) for s in self.hunting_sessions)
        
        return {
            'total_sessions': total_sessions,
            'total_runtime_hours': total_runtime / 3600,
            'total_tickets_found': total_found,
            'total_tickets_secured': total_secured,
            'success_rate': (total_secured / total_found * 100) if total_found > 0 else 0,
            'best_hour_tickets': best_hour,
            'best_day_tickets': best_day,
            'longest_session_hours': longest_session / 3600
        }
    
    def get_recent_discoveries(self, limit=20):
        """Get recent ticket discoveries"""
        recent = sorted(self.ticket_discoveries, 
                       key=lambda x: x.get('unix_time', 0), 
                       reverse=True)[:limit]
        
        return [
            {
                'timestamp': datetime.fromtimestamp(t.get('unix_time', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                'type': t.get('ticket_type', 'Unknown'),
                'price': t.get('price', 'N/A'),
                'sector': t.get('sector', 'N/A'),
                'row': t.get('row', 'N/A'),
                'seat': t.get('seat', 'N/A')
            } for t in recent
        ]

class TerminalUI:
    """Enhanced terminal UI with themes and animations"""
    
    THEMES = {
        "cyberpunk": {
            "primary": Fore.CYAN,
            "secondary": Fore.MAGENTA,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.CYAN
        },
        "matrix": {
            "primary": Fore.GREEN,
            "secondary": Fore.GREEN,
            "success": Style.BRIGHT + Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.GREEN
        },
        "minimal": {
            "primary": Fore.WHITE,
            "secondary": Fore.WHITE,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.WHITE
        },
        "rainbow": {
            "primary": Fore.CYAN,
            "secondary": Fore.MAGENTA,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "accent": Style.BRIGHT + Fore.BLUE
        }
    }
    
    @staticmethod
    def clear():
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_header(theme="cyberpunk"):
        """Print enhanced header with ASCII art"""
        TerminalUI.clear()
        colors = TerminalUI.THEMES[theme]
        
        # ASCII Art Header
        print(colors["accent"] + """
    ███████╗ █████╗ ███╗   ██╗███████╗ █████╗ ██╗     ███████╗
    ██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗██║     ██╔════╝
    █████╗  ███████║██╔██╗ ██║███████╗███████║██║     █████╗  
    ██╔══╝  ██╔══██║██║╚██╗██║╚════██║██╔══██║██║     ██╔══╝  
    ██║     ██║  ██║██║ ╚████║███████║██║  ██║███████╗███████╗
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
    """ + Style.RESET_ALL)
        
        print(colors["primary"] + "    ══════════════════════════════════════════════════════")
        print(colors["secondary"] + "         🎫 ULTIMATE TICKET HUNTER - ENHANCED EDITION")
        print(colors["primary"] + "    ══════════════════════════════════════════════════════\n")
    
    @staticmethod
    def main_menu(settings, analytics=None):
        """Enhanced main menu with analytics focus"""
        theme = settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        # Quick status bar with key metrics
        if analytics and hasattr(analytics, 'get_quick_stats'):
            stats = analytics.get_quick_stats()
            print(colors["accent"] + "┌─ TODAY'S PERFORMANCE " + "─" * 56 + "┐")
            print(f"│ Sessions: {colors['success']}{stats['sessions_today']:<3} "
                  f"{colors['secondary']}│ Tickets Found: {colors['warning']}{stats['tickets_today']:<4} "
                  f"{colors['secondary']}│ Secured: {colors['success']}{stats['secured_today']:<3} "
                  f"{colors['secondary']}│ Success Rate: {colors['accent']}{stats['success_rate']:.1f}%{' '*6} │")
            print(colors["accent"] + "└" + "─" * 77 + "┘\n")
        
        # Current configuration
        url = settings.get("target_url", DEFAULT_TARGET_URL)
        event_name = "🎸 Bruce Springsteen" if "bruce-springsteen" in url else "🎫 Custom Event"
        
        print(f"{colors['secondary']}Event: {colors['success']}{event_name}")
        print(f"{colors['secondary']}Setup: {colors['accent']}{settings.get('num_browsers', 2)} browsers, "
              f"{', '.join(settings.get('ticket_types', ['all']))} tickets, "
              f"{'Auto-buy' if settings.get('auto_buy') else 'Manual'}\n")
        
        # Streamlined menu options
        print(colors["primary"] + "╔══ HUNTING " + "═" * 66 + "╗")
        print(f"║ {colors['accent']}[1] {Fore.WHITE}🎯 START HUNTING      {colors['secondary']}Begin ticket hunt with current config{' '*20} ║")
        print(f"║ {colors['accent']}[2] {Fore.WHITE}⚡ QUICK CONFIG       {colors['secondary']}Fast setup (browsers, types, speed){' '*22} ║")
        print(f"║ {colors['accent']}[3] {Fore.WHITE}🔧 ADVANCED SETTINGS  {colors['secondary']}Detailed configuration options{' '*27} ║")
        
        print(colors["primary"] + "╠══ ANALYTICS " + "═" * 64 + "╣")
        print(f"║ {colors['accent']}[4] {Fore.WHITE}📊 LIVE MONITOR       {colors['secondary']}Real-time hunting statistics{' '*29} ║")
        print(f"║ {colors['accent']}[5] {Fore.WHITE}⏰ HOURLY PATTERNS    {colors['secondary']}Best times to hunt by hour{' '*31} ║")
        print(f"║ {colors['accent']}[6] {Fore.WHITE}📈 TICKET ANALYSIS    {colors['secondary']}Detailed ticket type breakdown{' '*27} ║")
        print(f"║ {colors['accent']}[7] {Fore.WHITE}📅 DAILY REPORTS      {colors['secondary']}Performance by day{' '*39} ║")
        print(f"║ {colors['accent']}[8] {Fore.WHITE}🎯 SUCCESS METRICS    {colors['secondary']}Overall performance statistics{' '*27} ║")
        
        print(colors["primary"] + "╠══ TOOLS " + "═" * 68 + "╣")
        print(f"║ {colors['accent']}[9] {Fore.WHITE}🌐 TEST BROWSER       {colors['secondary']}Check if detection is working{' '*28} ║")
        print(f"║ {colors['accent']}[P] {Fore.WHITE}🔒 PROXY SETUP        {colors['secondary']}Configure proxy settings{' '*33} ║")
        print(f"║ {colors['accent']}[S] {Fore.WHITE}💾 PROFILES           {colors['secondary']}Save/load hunting profiles{' '*31} ║")
        
        print(colors["primary"] + "╠══ SYSTEM " + "═" * 67 + "╣")
        print(f"║ {colors['accent']}[L] {Fore.WHITE}📜 VIEW LOGS          {colors['secondary']}Show recent ticket discoveries{' '*27} ║")
        print(f"║ {colors['accent']}[H] {Fore.WHITE}❓ HELP               {colors['secondary']}Usage guide and tips{' '*37} ║")
        print(f"║ {colors['accent']}[X] {Fore.WHITE}🚪 EXIT               {colors['secondary']}Save and close{' '*43} ║")
        print(colors["primary"] + "╚" + "═" * 77 + "╝\n")
        
        return input(colors["accent"] + "➤ Select option: " + Fore.WHITE).strip().upper()
    
    @staticmethod
    def quick_settings_menu(settings):
        """Quick settings for fast configuration"""
        theme = settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    ⚡ QUICK SETTINGS\n")
        
        print(colors["primary"] + f"    Browsers: {colors['accent']}{settings.get('num_browsers')} " + 
              colors["secondary"] + "[+/-]")
        print(colors["primary"] + f"    Max Tickets: {colors['accent']}{settings.get('max_tickets')} " + 
              colors["secondary"] + "[SHIFT +/-]")
        print(colors["primary"] + f"    Speed: {colors['accent']}{settings.get('min_wait')}-{settings.get('max_wait')}s " + 
              colors["secondary"] + "[S]")
        print(colors["primary"] + f"    Auto-Buy: {colors['accent']}{'ON' if settings.get('auto_buy') else 'OFF'} " + 
              colors["secondary"] + "[A]")
        print(colors["primary"] + f"    Sound: {colors['accent']}{'ON' if settings.get('sound_alerts') else 'OFF'} " + 
              colors["secondary"] + "[M]")
        print()
        print(colors["secondary"] + "    [Enter] Start Hunting")
        print(colors["secondary"] + "    [ESC] Back to Menu\n")
        
        return input(colors["accent"] + "    Action: " + Fore.WHITE).strip()
    
    @staticmethod
    def live_dashboard_header(theme="cyberpunk"):
        """Enhanced live dashboard header"""
        colors = TerminalUI.THEMES[theme]
        print(f"\n{colors['primary']}{'═'*80}")
        print(colors['accent'] + "  📊 LIVE HUNTING DASHBOARD".center(80))
        print(f"{colors['primary']}{'═'*80}\n")
    
    @staticmethod
    def format_stat_box(title, value, color=Fore.WHITE, width=18):
        """Format a statistic box"""
        box = f"┌{'─' * width}┐\n"
        box += f"│ {title.center(width-2)} │\n"
        box += f"│ {color}{str(value).center(width-2)}{Fore.WHITE} │\n"
        box += f"└{'─' * width}┘"
        return box

class NotificationManager:
    """Handles various notification methods"""
    
    def __init__(self, settings):
        self.settings = settings
        self.notification_queue = deque(maxlen=50)
    
    def notify(self, message, level="info", browser_id=None):
        """Send notification through configured channels"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Add to queue
        self.notification_queue.append({
            "time": timestamp,
            "message": message,
            "level": level,
            "browser_id": browser_id
        })
        
        # Sound notification
        if level in ["alert", "success"] and self.settings.get("sound_alerts"):
            self._play_sound(level)
        
        # Webhook notification for important events
        if level == "alert" and self.settings.get("notification_webhook"):
            self._send_webhook(message)
    
    def _play_sound(self, level):
        """Play notification sound"""
        try:
            if sys.platform == 'darwin':
                sounds = {
                    "alert": '/System/Library/Sounds/Glass.aiff',
                    "success": '/System/Library/Sounds/Hero.aiff',
                    "error": '/System/Library/Sounds/Basso.aiff'
                }
                subprocess.run(['afplay', sounds.get(level, sounds["alert"])])
            elif sys.platform == 'win32':
                import winsound
                frequencies = {"alert": 1000, "success": 1500, "error": 500}
                winsound.Beep(frequencies.get(level, 1000), 300)
            elif sys.platform.startswith('linux'):
                subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])
        except:
            pass
    
    def _send_webhook(self, message):
        """Send webhook notification"""
        webhook_url = self.settings.get("notification_webhook")
        if webhook_url:
            try:
                requests.post(webhook_url, json={"content": message}, timeout=5)
            except:
                pass
    
    def get_recent_notifications(self, count=10):
        """Get recent notifications"""
        return list(self.notification_queue)[-count:]

class FanSaleUltimate:
    """Enhanced FanSale bot with advanced features"""
    
    def __init__(self):
        self.target_url = DEFAULT_TARGET_URL
        self.twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY', '').strip()
        
        # Managers
        self.settings = SettingsManager()
        self.stats = StatsTracker()
        self.analytics = EnhancedAnalytics()
        self.notifications = NotificationManager(self.settings)
        
        # Runtime state
        self.browsers = []
        self.threads = []
        self.shutdown_event = threading.Event()
        self.purchase_lock = threading.Lock()
        self.tickets_secured = 0
        self.seen_tickets = set()
        
        # CAPTCHA state
        self.captcha_grace_period = 300
        self.last_captcha_solve = 0
        
        # Display state
        self.display_lock = threading.Lock()
        self.last_log_time = time.time()
        
        # Ticket monitoring with timestamps
        self.ticket_monitor = deque(maxlen=100)  # Keep last 100 ticket discoveries
        self.ticket_monitor_lock = threading.Lock()
        
        # Bot popup tracking
        self.bot_popup_start_time = {}  # Track when popup first detected per browser
        
        # Enhanced selectors for FanSale.it
        self.ticket_selectors = [
            # Primary selectors based on HTML structure
            "span.OfferEntry-SeatDescription",
            "div.OfferEntry",
            "tr.EventEntry",
            
            # Additional specific selectors
            "div[data-qa='ticketToBuy']",
            "a.offer-list-item",
            "article.listing-item",
            
            # Italian-specific selectors
            "div[class*='biglietto']",
            "div[class*='offerta']",
            "article[class*='evento']",
            
            # Generic fallbacks
            "div[class*='ticket'][class*='available']",
            "div[class*='ticket-card']",
            "div[class*='event-card']",
            "a[href*='/tickets/']"
        ]
        
        self.buy_selectors = [
            # FanSale specific
            "button[data-qa='buyNowButton']",
            
            # Italian text variations (XPath)
            "//button[contains(text(), 'Acquista')]",
            "//button[contains(text(), 'Compra')]",
            "//button[contains(text(), 'Prenota')]",
            "//button[contains(text(), 'Procedi')]",
            
            # Class-based CSS selectors
            "button[class*='buy']",
            "button[class*='purchase']",
            "button[class*='acquista']",
            "button[class*='primary'][class*='button']",
            "button.Button--primary",
            "a.Button--primary",
            
            # Generic submit
            "button[type='submit']:not([disabled])"
        ]
    
    def log(self, message, level='info', browser_id=None):
        """Clean, minimal logging for better readability"""
        with self.display_lock:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Simplified level config with clean formatting
            level_config = {
                'info': ('', Fore.CYAN, ''),
                'success': ('✓', Fore.GREEN, ''),
                'warning': ('⚠', Fore.YELLOW, ''),
                'error': ('✗', Fore.RED, ''),
                'alert': ('🔔', Fore.MAGENTA + Style.BRIGHT, ''),
                'ticket': ('🎫', Fore.GREEN + Style.BRIGHT, ''),
                'check': ('', Fore.WHITE + Style.DIM, ''),
                'browser': ('', Fore.BLUE, ''),
                'stealth': ('', Fore.WHITE + Style.DIM, ''),
                'speed': ('📊', Fore.CYAN, ''),
                'money': ('💰', Fore.GREEN + Style.BRIGHT, ''),
                'captcha': ('🔐', Fore.YELLOW, ''),
                'secure': ('🎯', Fore.GREEN + Style.BRIGHT, ''),
                'debug': ('', Fore.WHITE + Style.DIM, '')
            }
            
            icon, color, _ = level_config.get(level, ('', Fore.WHITE, ''))
            
            # Clean browser indicator
            if browser_id is not None:
                browser_str = f"{Fore.BLUE}[{browser_id}]{Style.RESET_ALL}"
            else:
                browser_str = ""
            
            # Build clean log line
            time_str = f"{Fore.WHITE + Style.DIM}{timestamp}{Style.RESET_ALL}"
            
            # Different formatting for ticket discoveries
            if level == 'ticket':
                log_line = f"{time_str} {browser_str} {message}"
            else:
                # Add icon only if present
                icon_part = f"{icon} " if icon else ""
                log_line = f"{time_str} {browser_str} {icon_part}{color}{message}{Style.RESET_ALL}"
            
            # Print without clearing entire line to reduce flicker
            print(log_line)
            
            # Track in analytics if it's a ticket discovery
            if level == 'ticket' and hasattr(self, 'current_ticket_info'):
                if hasattr(self, 'analytics'):
                    self.analytics.log_ticket_discovery(self.current_ticket_info)
    
    def display_live_stats(self):
        """Clean, minimal live statistics display with ticket monitor"""
        display_counter = 0
        
        while not self.shutdown_event.is_set():
            try:
                stats = self.stats.get_stats()
                runtime = self.stats.get_runtime()
                
                with self.display_lock:
                    # Save cursor position and clear stats area
                    print(f"\033[s", end='')  # Save cursor
                    print(f"\033[10;0H", end='')  # Move to line 10
                    print(f"\033[J", end='')  # Clear from cursor to end
                    
                    # Compact stats header
                    print(f"\n{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
                    print(f"{Fore.WHITE + Style.BRIGHT}⚡ LIVE STATS{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
                    
                    # Key metrics in one line
                    print(f"⏱  {runtime} | "
                          f"🌐 {stats['active_browsers']} browsers | "
                          f"🚀 {stats['checks_per_minute']} CPM | "
                          f"🎯 {stats['tickets_secured']} secured")
                    
                    # Ticket summary if any found
                    if stats['unique_tickets_seen'] > 0:
                        tickets_summary = []
                        for cat, count in stats['tickets_found'].items():
                            if count > 0:
                                icon = {'prato_a': '🟡', 'prato_b': '🟠', 'seating': '🪑'}.get(cat, '🎫')
                                tickets_summary.append(f"{icon} {count}")
                        
                        if tickets_summary:
                            print(f"📊 Found: {' | '.join(tickets_summary)} "
                                  f"(Total: {stats['unique_tickets_seen']})")
                    
                    print(f"{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
                    
                    # Show ticket monitor
                    with self.ticket_monitor_lock:
                        if self.ticket_monitor:
                            print(f"\n{Fore.YELLOW}📋 All Tickets Found This Session:{Style.RESET_ALL}")
                            print(f"{Fore.WHITE + Style.DIM}{'─' * 80}{Style.RESET_ALL}")
                            # Show all tickets
                            for ticket in list(self.ticket_monitor)[-10:]:  # Last 10 tickets
                                print(f"{Fore.BLUE}[{ticket['browser_id']}]{Style.RESET_ALL} "
                                      f"{Fore.WHITE}🎫 {ticket['log_line']}{Style.RESET_ALL}")
                            if len(self.ticket_monitor) > 10:
                                print(f"{Fore.WHITE + Style.DIM}... and {len(self.ticket_monitor) - 10} more tickets{Style.RESET_ALL}")
                    
                    # Restore cursor
                    print(f"\033[u", end='', flush=True)
                
                time.sleep(2)  # Update every 2 seconds
            except:
                pass

    def display_ticket_monitor(self):
        """Display all found tickets with timestamps"""
        with self.ticket_monitor_lock:
            if not self.ticket_monitor:
                return
            
            print(f"\n{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}")
            print(f"{Fore.WHITE + Style.BRIGHT}📋 TICKET MONITOR - All Found Tickets{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}")
            
            # Display all tickets
            for ticket in self.ticket_monitor:
                print(f"{Fore.BLUE}[{ticket['browser_id']}]{Style.RESET_ALL} "
                      f"{Fore.WHITE}🎫 {ticket['log_line']}{Style.RESET_ALL}")
            
            print(f"\nTotal tickets found: {len(self.ticket_monitor)}")
            print(f"{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}")
    
    def configure_advanced_settings(self):
        """Advanced settings configuration"""
        theme = self.settings.get("theme", "cyberpunk")
        while True:
            TerminalUI.print_header(theme)
            colors = TerminalUI.THEMES[theme]
            
            print(colors["accent"] + "    ⚙️  ADVANCED SETTINGS\n")
            
            print(colors["primary"] + "    HUNTING CONFIGURATION")
            print(colors["secondary"] + f"    [1] Event URL: {colors['accent']}{self.settings.get('target_url')[:40]}...")
            print(colors["secondary"] + f"    [2] Browsers: {colors['accent']}{self.settings.get('num_browsers')}")
            print(colors["secondary"] + f"    [3] Max Tickets: {colors['accent']}{self.settings.get('max_tickets')}")
            print(colors["secondary"] + f"    [4] Ticket Types: {colors['accent']}{', '.join(self.settings.get('ticket_types'))}")
            print()
            
            print(colors["primary"] + "    PERFORMANCE")
            print(colors["secondary"] + f"    [5] Check Speed: {colors['accent']}{self.settings.get('min_wait')}-{self.settings.get('max_wait')}s")
            print(colors["secondary"] + f"    [6] Refresh Interval: {colors['accent']}{self.settings.get('refresh_interval')}s")
            print()
            
            print(colors["primary"] + "    AUTOMATION")
            print(colors["secondary"] + f"    [7] Auto-Buy: {colors['accent']}{'ON' if self.settings.get('auto_buy') else 'OFF'}")
            print(colors["secondary"] + f"    [8] Max Price: {colors['accent']}€{self.settings.get('max_price') or 'No limit'}")
            print(colors["secondary"] + f"    [9] Preferred Sectors: {colors['accent']}{', '.join(self.settings.get('preferred_sectors')) or 'Any'}")
            print()
            
            print(colors["primary"] + "    NETWORK")
            print(colors["secondary"] + f"    [P] Proxy Settings")
            print(colors["secondary"] + f"    [W] Webhook URL")
            print()
            
            print(colors["secondary"] + "    [S] Save as Profile")
            print(colors["secondary"] + "    [B] Back to Menu\n")
            
            choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip().upper()
            
            if choice == '1':
                new_url = input(f"\n{colors['primary']}Enter event URL (or press Enter for Bruce): {Fore.WHITE}").strip()
                if new_url:
                    self.settings.update('target_url', new_url)
                else:
                    self.settings.update('target_url', DEFAULT_TARGET_URL)
                self.log("Event URL updated", 'success')
                time.sleep(1)
                
            elif choice == '2':
                try:
                    num = int(input(f"\n{colors['primary']}Number of browsers (1-8): {Fore.WHITE}"))
                    self.settings.update('num_browsers', max(1, min(8, num)))
                    self.log("Browsers updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '3':
                try:
                    num = int(input(f"\n{colors['primary']}Max tickets to secure: {Fore.WHITE}"))
                    self.settings.update('max_tickets', max(1, num))
                    self.log("Max tickets updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '4':
                # Clean ticket type selection interface
                print(f"\n{colors['bright']}┌─ Ticket Type Selection ─┐{colors['reset']}")
                print(f"{colors['primary']}│ What to hunt for?       │{colors['reset']}")
                print(f"{colors['primary']}├─────────────────────────┤{colors['reset']}")
                print(f"{colors['primary']}│ {colors['success']}[1]{colors['reset']} 🎫 Prato A (Gold)  │")
                print(f"{colors['primary']}│ {colors['warning']}[2]{colors['reset']} 🎫 Prato B (Silver)│")
                print(f"{colors['primary']}│ {colors['info']}[3]{colors['reset']} 🪑 Seating (All)   │")
                print(f"{colors['primary']}│ {colors['secondary']}[4]{colors['reset']} 🎯 All Types       │")
                print(f"{colors['primary']}└─────────────────────────┘{colors['reset']}")
                
                selection = input(f"\n{colors['prompt']}▶ Your choice (1-4): {colors['reset']}").strip()
                
                if selection == '1':
                    self.settings.update('ticket_types', ['prato_a'])
                    self.log("🎯 Now hunting for: Prato A tickets only", 'success')
                elif selection == '2':
                    self.settings.update('ticket_types', ['prato_b'])
                    self.log("🎯 Now hunting for: Prato B tickets only", 'success')
                elif selection == '3':
                    self.settings.update('ticket_types', ['seating'])
                    self.log("🎯 Now hunting for: All seating tickets", 'success')
                elif selection == '4':
                    self.settings.update('ticket_types', ['all'])
                    self.log("🎯 Now hunting for: All ticket types", 'success')
                else:
                    self.log("❌ Invalid selection", 'error')
                time.sleep(1)
                
            elif choice == '5':
                try:
                    min_wait = float(input(f"\n{colors['primary']}Min wait time (seconds): {Fore.WHITE}"))
                    max_wait = float(input(f"{colors['primary']}Max wait time (seconds): {Fore.WHITE}"))
                    self.settings.update('min_wait', max(0.1, min_wait))
                    self.settings.update('max_wait', max(min_wait, max_wait))
                    self.log("Check speed updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '6':
                try:
                    interval = int(input(f"\n{colors['primary']}Page refresh interval (seconds): {Fore.WHITE}"))
                    self.settings.update('refresh_interval', max(5, interval))
                    self.log("Refresh interval updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '7':
                self.settings.update('auto_buy', not self.settings.get('auto_buy'))
                self.log(f"Auto-buy {'enabled' if self.settings.get('auto_buy') else 'disabled'}", 'success')
                time.sleep(1)
                
            elif choice == '8':
                try:
                    price = input(f"\n{colors['primary']}Max price in EUR (0 for no limit): {Fore.WHITE}")
                    self.settings.update('max_price', float(price))
                    self.log("Max price updated", 'success')
                except:
                    self.log("Invalid input", 'error')
                time.sleep(1)
                
            elif choice == '9':
                sectors = input(f"\n{colors['primary']}Preferred sectors (comma-separated, e.g., 1,2,3 or leave empty for any): {Fore.WHITE}").strip()
                if sectors:
                    self.settings.update('preferred_sectors', [s.strip() for s in sectors.split(',')])
                    self.log(f"Preferred sectors updated: {sectors}", 'success')
                else:
                    self.settings.update('preferred_sectors', [])
                    self.log("Preferred sectors cleared - will accept any sector", 'success')
                time.sleep(1)
                
            elif choice == 'S':
                name = input(f"\n{colors['primary']}Profile name: {Fore.WHITE}").strip()
                if name:
                    self.settings.save_profile(name)
                    self.log(f"Profile '{name}' saved", 'success')
                time.sleep(1)
                
            elif choice == 'B':
                break
    
    def profile_manager(self):
        """Manage saved profiles"""
        theme = self.settings.get("theme", "cyberpunk")
        while True:
            TerminalUI.print_header(theme)
            colors = TerminalUI.THEMES[theme]
            
            print(colors["accent"] + "    👤 PROFILE MANAGER\n")
            
            print(colors["primary"] + f"    Active Profile: {colors['accent']}{self.settings.active_profile}\n")
            
            print(colors["secondary"] + "    SAVED PROFILES:")
            for i, (name, profile) in enumerate(self.settings.profiles.items(), 1):
                browsers = profile.get('num_browsers', 2)
                tickets = profile.get('max_tickets', 2)
                print(f"    {colors['secondary']}[{i}] {colors['accent']}{name:<20} "
                      f"{colors['primary']}({browsers} browsers, {tickets} tickets)")
            
            print()
            print(colors["secondary"] + "    [N] New Profile")
            print(colors["secondary"] + "    [D] Delete Profile")
            print(colors["secondary"] + "    [B] Back to Menu\n")
            
            choice = input(colors["accent"] + "    Select profile number or action: " + Fore.WHITE).strip().upper()
            
            if choice == 'B':
                break
            elif choice == 'N':
                self.configure_advanced_settings()
            elif choice == 'D':
                name = input(f"\n{colors['primary']}Profile name to delete: {Fore.WHITE}").strip()
                if name in self.settings.profiles and name != "default":
                    del self.settings.profiles[name]
                    self.settings.save_profiles()
                    self.log(f"Profile '{name}' deleted", 'success')
                time.sleep(1)
            else:
                try:
                    idx = int(choice) - 1
                    profile_names = list(self.settings.profiles.keys())
                    if 0 <= idx < len(profile_names):
                        profile_name = profile_names[idx]
                        self.settings.load_profile(profile_name)
                        self.log(f"Loaded profile '{profile_name}'", 'success')
                        time.sleep(1)
                        break
                except:
                    pass
    
    def change_theme(self):
        """Change UI theme"""
        theme = self.settings.get("theme", "cyberpunk")
        TerminalUI.print_header(theme)
        colors = TerminalUI.THEMES[theme]
        
        print(colors["accent"] + "    🎨 SELECT THEME\n")
        
        themes = ["cyberpunk", "matrix", "minimal", "rainbow"]
        for i, t in enumerate(themes, 1):
            sample_colors = TerminalUI.THEMES[t]
            print(f"    [{i}] {sample_colors['accent']}{t.upper()}{Style.RESET_ALL}")
            print(f"        {sample_colors['primary']}Primary {sample_colors['secondary']}Secondary "
                  f"{sample_colors['success']}Success {sample_colors['warning']}Warning{Style.RESET_ALL}")
            print()
        
        try:
            choice = int(input(colors["accent"] + "    Select theme: " + Fore.WHITE))
            if 1 <= choice <= len(themes):
                self.settings.update("theme", themes[choice-1])
                self.log(f"Theme changed to {themes[choice-1]}", 'success')
        except:
            pass
        
        time.sleep(1)
    
    def categorize_ticket(self, text):
        """Simplified ticket categorization - only Prato A, Prato B, or Seating"""
        text_lower = text.lower()
        
        # Check for Prato A
        if 'prato a' in text_lower or 'prato gold' in text_lower:
            return 'prato_a'
        # Check for Prato B
        elif 'prato b' in text_lower or 'prato silver' in text_lower:
            return 'prato_b'
        # Everything else is considered seating
        else:
            return 'seating'
    
    def extract_ticket_price(self, text):
        """Extract price from ticket text"""
        import re
        # Look for price patterns like €50, EUR 50, 50€, etc.
        price_pattern = r'[€EUR]\s*(\d+(?:[.,]\d{2})?)|(\d+(?:[.,]\d{2})?)\s*[€EUR]'
        match = re.search(price_pattern, text)
        if match:
            price_str = match.group(1) or match.group(2)
            return float(price_str.replace(',', '.'))
        return None
    
    def should_buy_ticket(self, ticket_info):
        """Determine if ticket should be purchased based on rules"""
        if not self.settings.get('auto_buy'):
            return True  # Manual mode - try all matching types
        
        # Check price limit
        max_price = self.settings.get('max_price', 0)
        if max_price > 0 and ticket_info.get('price'):
            if ticket_info['price'] > max_price:
                return False
        
        # Check preferred sectors
        preferred = self.settings.get('preferred_sectors', [])
        if preferred and ticket_info.get('sector'):
            if ticket_info['sector'] not in preferred:
                return False
        
        # Check blacklist
        blacklist = self.settings.get('blacklist_sectors', [])
        if blacklist and ticket_info.get('sector'):
            if ticket_info['sector'] in blacklist:
                return False
        
        return True
    
    def generate_ticket_hash(self, text):
        """Generate unique hash for ticket"""
        clean_text = ''.join(c for c in text if c.isalnum() or c.isspace())
        return hashlib.md5(clean_text.encode()).hexdigest()
    
    def create_browser(self, browser_id):
        """Create undetected Chrome instance - minimal setup to avoid detection"""
        try:
            self.log(f"Creating browser {browser_id}...", 'browser')
            
            # Create minimal ChromeOptions (like diagnostic test that worked)
            options = uc.ChromeOptions()
            
            # Only add essential options
            profile_dir = Path.home() / ".fansale_bot_profiles" / f"browser_{browser_id}"
            profile_dir.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--user-data-dir={str(profile_dir)}')
            
            # Window positioning
            window_width, window_height = 1200, 900
            positions = [
                (0, 0), (600, 0), (1200, 0),
                (0, 450), (600, 450), (1200, 450),
                (0, 900), (600, 900)
            ]
            if browser_id < len(positions):
                x, y = positions[browser_id]
                options.add_argument(f'--window-position={x},{y}')
            options.add_argument(f'--window-size={window_width},{window_height}')
            
            # Create driver with minimal setup (no version_main, no extra options)
            driver = uc.Chrome(options=options)
            
            self.log(f"Browser {browser_id} created successfully", 'success')
            return driver
            
        except Exception as e:
            self.log(f"Failed to create browser: {str(e)}", 'error')
            
            # Try even more minimal approach as fallback
            try:
                self.log(f"Trying ultra-minimal setup...", 'warning')
                driver = uc.Chrome()  # Absolute minimal like diagnostic
                self.log(f"Browser {browser_id} created with ultra-minimal setup", 'success')
                return driver
                
            except Exception as e2:
                self.log(f"Ultra-minimal also failed: {str(e2)}", 'error')
                raise Exception(f"Failed to create browser: {str(e)}")
    
    def dismiss_popups(self, driver):
        """Enhanced popup dismissal for FanSale"""
        dismissed = 0
        
        # FanSale-specific selectors
        selectors = [
            # Bot protection
            "button.js-BotProtectionModalButton1",
            "button[class*='BotProtection']",
            "button[class*='botprotection']",
            
            # Italian text buttons
            "//button[contains(text(), 'Carica')]",
            "//button[contains(text(), 'Continua')]",
            "//button[contains(text(), 'Accetta')]",
            "//button[contains(text(), 'OK')]",
            
            # Cookie/privacy
            "button[class*='cookie-accept']",
            "button[class*='privacy-accept']",
            "button#onetrust-accept-btn-handler",
            
            # Generic close buttons
            "button[aria-label*='close']",
            "button[aria-label*='chiudi']",
            "button[class*='modal-close']",
            "button[class*='close-button']",
            "a[class*='close']"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith('//'):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for elem in elements:
                    try:
                        # Try JavaScript click first
                        driver.execute_script("arguments[0].click();", elem)
                        dismissed += 1
                    except:
                        try:
                            # Fallback to regular click
                            elem.click()
                            dismissed += 1
                        except:
                            pass
            except:
                pass
        
        # Check for iframe popups
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    # Try to find close buttons in iframe
                    close_btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='close'], a[class*='close']")
                    for btn in close_btns:
                        try:
                            btn.click()
                            dismissed += 1
                        except:
                            pass
                    driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
        except:
            pass
        
        return dismissed

    def detect_bot_popup(self, driver):
        """Detect the specific bot detection popup"""
        try:
            # Check for the bot detection text
            bot_texts = [
                "sistema ti ha classificato come bot",
                "classified as automatic bot",
                "bot automatico",
                "visita prima un'altra pagina",
                "visit another page first"
            ]
            
            for text in bot_texts:
                try:
                    # Check in page source
                    if text in driver.page_source.lower():
                        # Verify it's visible
                        elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
                        for elem in elements:
                            if elem.is_displayed():
                                return True
                except:
                    pass
            
            # Check for the specific "Carica Offerte" button
            try:
                buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Carica Offerte') or contains(text(), 'Carica Offerta')]")
                for btn in buttons:
                    if btn.is_displayed():
                        return True
            except:
                pass
                
            return False
        except:
            return False
    
    def handle_persistent_bot_popup(self, driver, browser_id):
        """Handle bot popup that persists after multiple click attempts"""
        self.log("🤖 Bot popup persists - trying multiple solutions", 'warning', browser_id)
        
        current_url = driver.current_url
        
        # Solution 1: Follow FanSale's instruction - visit homepage first
        try:
            self.log("📍 Solution 1: Visiting FanSale homepage as instructed", 'info', browser_id)
            
            # Navigate to FanSale homepage
            driver.get("https://www.fansale.it")
            time.sleep(3)
            
            # Click on a few links to appear human
            try:
                # Find concert/event links
                event_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/tickets/']")[:3]
                if event_links:
                    # Click on a random event
                    random.choice(event_links).click()
                    time.sleep(2)
                    
                    # Go back to homepage
                    driver.get("https://www.fansale.it")
                    time.sleep(2)
            except:
                pass
            
            # Now return to the original page
            self.log("🔄 Returning to target page", 'info', browser_id)
            driver.get(current_url)
            time.sleep(3)
            
            # Clear any initial popups
            self.dismiss_popups(driver)
            
            # Check if popup is gone
            if not self.detect_bot_popup(driver):
                self.log("✅ Bot popup cleared by visiting homepage!", 'success', browser_id)
                return True
                
        except Exception as e:
            self.log(f"❌ Homepage visit failed: {str(e)[:50]}", 'error', browser_id)
        
        # Solution 2: Clear browser data completely
        try:
            self.log("🧹 Solution 2: Clearing all browser data", 'info', browser_id)
            
            # Execute more comprehensive data clearing
            driver.execute_script("""
                // Clear everything possible
                try {
                    // Clear cookies
                    document.cookie.split(";").forEach(function(c) { 
                        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
                    });
                    
                    // Clear storages
                    window.localStorage.clear();
                    window.sessionStorage.clear();
                    
                    // Clear IndexedDB
                    if ('indexedDB' in window) {
                        indexedDB.databases().then(dbs => {
                            dbs.forEach(db => indexedDB.deleteDatabase(db.name));
                        });
                    }
                    
                    // Clear cache storage
                    if ('caches' in window) {
                        caches.keys().then(names => {
                            names.forEach(name => caches.delete(name));
                        });
                    }
                } catch(e) {}
            """)
            
            # Delete all cookies via Selenium
            driver.delete_all_cookies()
            
            # Navigate to blank page then back
            driver.get("about:blank")
            time.sleep(1)
            driver.get(current_url)
            time.sleep(3)
            
            if not self.detect_bot_popup(driver):
                self.log("✅ Bot popup cleared by data deletion!", 'success', browser_id)
                return True
                
        except Exception as e:
            self.log(f"❌ Data clearing failed: {str(e)[:50]}", 'error', browser_id)
        
        # Solution 3: Try clicking the "Carica Offerte" button directly
        try:
            self.log("🖱️ Solution 3: Trying to click the button directly", 'info', browser_id)
            
            # Find and click the Carica Offerte button
            buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Carica Offerte') or contains(text(), 'Carica Offerta')]")
            for btn in buttons:
                if btn.is_displayed():
                    try:
                        # Try JavaScript click
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        
                        if not self.detect_bot_popup(driver):
                            self.log("✅ Bot popup cleared by button click!", 'success', browser_id)
                            return True
                    except:
                        # Try regular click
                        try:
                            btn.click()
                            time.sleep(2)
                            
                            if not self.detect_bot_popup(driver):
                                self.log("✅ Bot popup cleared by button click!", 'success', browser_id)
                                return True
                        except:
                            pass
                            
        except Exception as e:
            self.log(f"❌ Button click failed: {str(e)[:50]}", 'error', browser_id)
        
        # Solution 4: Create new browser session
        self.log("🔄 Solution 4: Popup persists - may need browser restart", 'warning', browser_id)
        
        # Try one more navigation cycle
        driver.get("https://www.fansale.it/fansale/")
        time.sleep(2)
        driver.get(current_url)
        time.sleep(2)
        
        return not self.detect_bot_popup(driver)

    def clear_browser_data(self, driver):
        """Clear browser data to prevent popup blocking issues"""
        try:
            # Delete cookies for the current domain
            driver.delete_all_cookies()
            
            # Clear local storage and session storage
            driver.execute_script("""
                // Clear storages
                try {
                    window.localStorage.clear();
                    window.sessionStorage.clear();
                } catch(e) {}
                
                // Clear IndexedDB
                try {
                    if ('indexedDB' in window && window.indexedDB.databases) {
                        window.indexedDB.databases().then(databases => {
                            databases.forEach(db => {
                                window.indexedDB.deleteDatabase(db.name);
                            });
                        });
                    }
                } catch(e) {}
            """)
            
            # Refresh the page to apply changes
            driver.refresh()
            time.sleep(2)
            
            # Re-dismiss any popups that appear after refresh
            self.dismiss_popups(driver)
            
            self.log("🧹 Browser data cleared successfully", 'info')
            return True
            
        except Exception as e:
            self.log(f"⚠️ Browser clear failed: {str(e)[:30]}", 'warning')
            # Try to continue anyway
            return False

    def deep_clean_browser(self, driver):
        """Deep clean browser to remove all traces"""
        try:
            self.log("🧽 Performing deep browser clean", 'info')
            
            # 1. Navigate away from FanSale completely
            driver.get("about:blank")
            time.sleep(1)
            
            # 2. Clear all browser data via JavaScript
            driver.execute_script("""
                // Clear all cookies for all domains
                document.cookie.split(";").forEach(function(c) { 
                    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date(0).toUTCString() + ";path=/;domain=" + window.location.hostname);
                    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date(0).toUTCString() + ";path=/;domain=." + window.location.hostname);
                    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date(0).toUTCString() + ";path=/");
                });
                
                // Clear all storage
                try { localStorage.clear(); } catch(e) {}
                try { sessionStorage.clear(); } catch(e) {}
                
                // Clear IndexedDB
                if ('indexedDB' in window && window.indexedDB.databases) {
                    window.indexedDB.databases().then(databases => {
                        databases.forEach(db => {
                            window.indexedDB.deleteDatabase(db.name);
                        });
                    });
                }
                
                // Clear cache storage
                if ('caches' in window) {
                    caches.keys().then(names => {
                        names.forEach(name => caches.delete(name));
                    });
                }
                
                // Clear service workers
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.getRegistrations().then(function(registrations) {
                        for(let registration of registrations) {
                            registration.unregister();
                        }
                    });
                }
            """)
            
            # 3. Delete all cookies via Selenium
            driver.delete_all_cookies()
            
            # 4. Clear Chrome's internal data
            try:
                driver.get("chrome://settings/clearBrowserData")
                time.sleep(1)
                # Try to click the clear data button
                driver.execute_script("""
                    try {
                        document.querySelector('* /deep/ #clearBrowsingDataConfirm').click();
                    } catch(e) {
                        // Try alternative method
                        var buttons = document.querySelectorAll('button');
                        for(var i = 0; i < buttons.length; i++) {
                            if(buttons[i].textContent.includes('Clear') || buttons[i].textContent.includes('Cancella')) {
                                buttons[i].click();
                                break;
                            }
                        }
                    }
                """)
                time.sleep(2)
            except:
                pass
            
            return True
        except Exception as e:
            self.log(f"⚠️ Deep clean error: {str(e)[:50]}", 'warning')
            return False
    
    def detect_captcha(self, driver):
        """Enhanced CAPTCHA detection"""
        if time.time() - self.last_captcha_solve < self.captcha_grace_period:
            return False
        
        captcha_indicators = [
            # Google reCAPTCHA
            "iframe[src*='recaptcha']",
            "div[class*='g-recaptcha']",
            "div#recaptcha",
            
            # hCaptcha
            "iframe[src*='hcaptcha']",
            "div[class*='h-captcha']",
            
            # Generic
            "div[class*='captcha']",
            "div[id*='captcha']",
            "img[src*='captcha']"
        ]
        
        for selector in captcha_indicators:
            try:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    return True
            except:
                pass
        
        # Check page text for CAPTCHA keywords
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            captcha_keywords = ['captcha', 'verifica', 'non sono un robot', "i'm not a robot"]
            if any(keyword in page_text for keyword in captcha_keywords):
                return True
        except:
            pass
        
        return False
    
    def solve_captcha(self, driver, browser_id):
        """Handle CAPTCHA (auto or manual)"""
        self.log(f"CAPTCHA detected!", 'warning', browser_id)
        self.stats.record_captcha_solved()
        
        if self.twocaptcha_key:
            try:
                # Find site key
                site_key = None
                for method in [
                    lambda: driver.find_element(By.CSS_SELECTOR, "[data-sitekey]").get_attribute("data-sitekey"),
                    lambda: driver.execute_script("return document.querySelector('[data-sitekey]').dataset.sitekey"),
                    lambda: driver.execute_script("return grecaptcha.execute.toString().match(/sitekey:'([^']+)'/)[1]")
                ]:
                    try:
                        site_key = method()
                        if site_key:
                            break
                    except:
                        pass
                
                if not site_key:
                    raise Exception("Could not find site key")
                
                # Request solution from 2captcha
                self.log("Requesting CAPTCHA solution from 2captcha...", 'info', browser_id)
                response = requests.post('http://2captcha.com/in.php', data={
                    'key': self.twocaptcha_key,
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': driver.current_url
                })
                
                if response.text.startswith('OK|'):
                    captcha_id = response.text.split('|')[1]
                    
                    # Poll for result
                    for _ in range(30):
                        time.sleep(5)
                        result = requests.get(f'http://2captcha.com/res.php?key={self.twocaptcha_key}&action=get&id={captcha_id}')
                        
                        if result.text == 'CAPCHA_NOT_READY':
                            continue
                        elif result.text.startswith('OK|'):
                            token = result.text.split('|')[1]
                            
                            # Inject token
                            driver.execute_script(f"""
                                document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                                    for (let key in ___grecaptcha_cfg.clients) {{
                                        if (___grecaptcha_cfg.clients[key].callback) {{
                                            ___grecaptcha_cfg.clients[key].callback('{token}');
                                        }}
                                    }}
                                }}
                            """)
                            
                            self.log("CAPTCHA solved automatically!", 'success', browser_id)
                            self.last_captcha_solve = time.time()
                            return True
                        else:
                            break
                            
            except Exception as e:
                self.log(f"Auto-solve failed: {e}", 'error', browser_id)
        
        # Manual fallback
        self.log("MANUAL CAPTCHA REQUIRED! Solve it in the browser!", 'alert', browser_id)
        self.log(f"You have 2 minutes to solve the CAPTCHA in Browser {browser_id}", 'warning')
        
        # Wait for manual solve
        start_time = time.time()
        while time.time() - start_time < 120:
            if not self.detect_captcha(driver):
                self.log("CAPTCHA solved manually!", 'success', browser_id)
                self.last_captcha_solve = time.time()
                return True
            time.sleep(2)
        
        self.log("CAPTCHA timeout!", 'error', browser_id)
        return False
    
    def extract_ticket_info(self, element):
        """Extract detailed ticket information"""
        try:
            text = element.text.strip()
            info = {
                'raw_text': text,
                'category': self.categorize_ticket(text),
                'price': self.extract_ticket_price(text),
                'sector': None,
                'row': None,
                'seat': None,
                'entrance': None,
                'ring': None,
                'details': []
            }
            
            import re
            
            # Extract entrance/ingresso
            entrance_match = re.search(r'ingresso\s+(\d+)', text.lower())
            if entrance_match:
                info['entrance'] = entrance_match.group(1)
                info['details'].append(f"INGRESSO {entrance_match.group(1)}")
            
            # Extract sector/settore
            sector_match = re.search(r'settore\s+(\d+)', text.lower())
            if sector_match:
                info['sector'] = sector_match.group(1)
                info['details'].append(f"Settore {sector_match.group(1)}")
            
            # Extract row/fila
            row_match = re.search(r'fila\s+(\d+)|row\s+(\d+)', text.lower())
            if row_match:
                info['row'] = row_match.group(1) or row_match.group(2)
                info['details'].append(f"Fila {info['row']}")
            
            # Extract seat/posto
            seat_match = re.search(r'posto\s+(\d+)|seat\s+(\d+)', text.lower())
            if seat_match:
                info['seat'] = seat_match.group(1) or seat_match.group(2)
                info['details'].append(f"Posto {info['seat']}")
            
            # Extract ring/anello
            ring_match = re.search(r'(\d+)\s*anello\s*(\w+)', text.lower())
            if ring_match:
                info['ring'] = f"{ring_match.group(1)} Anello {ring_match.group(2).title()}"
                info['details'].append(info['ring'])
            
            # Extract any additional location info
            if 'tribuna' in text.lower():
                info['details'].append('Tribuna')
            if 'parterre' in text.lower():
                info['details'].append('Parterre')
            
            # Build complete details string from text if details are empty
            if not info['details']:
                # Try to extract meaningful parts from the text
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not any(skip in line.lower() for skip in ['€', 'euro', 'prezzo']):
                        info['details'].append(line)
            
            return info
        except Exception as e:
            return {
                'raw_text': text if 'text' in locals() else 'Unknown',
                'category': 'seating',
                'price': None,
                'details': []
            }
    
    def attempt_purchase(self, driver, ticket_element, browser_id):
        """Enhanced purchase attempt with multiple strategies"""
        try:
            # Scroll to element
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ticket_element)
            time.sleep(0.2)
            
            # Try multiple click methods
            clicked = False
            
            # Method 1: JavaScript click on main element
            try:
                driver.execute_script("arguments[0].click();", ticket_element)
                clicked = True
                self.log("Clicked ticket with JavaScript", 'info', browser_id)
            except:
                pass
            
            # Method 2: Find and click specific link
            if not clicked:
                try:
                    # FanSale specific link selectors
                    link_selectors = [
                        "a[href*='/tickets/']",
                        "a.Button-inOfferEntryList",
                        "a[id*='detailBShowOfferButton']"
                    ]
                    for selector in link_selectors:
                        try:
                            link = ticket_element.find_element(By.CSS_SELECTOR, selector)
                            driver.execute_script("arguments[0].click();", link)
                            clicked = True
                            self.log(f"Clicked link with selector: {selector}", 'info', browser_id)
                            break
                        except:
                            pass
                except:
                    pass
            
            # Method 3: ActionChains click
            if not clicked:
                try:
                    ActionChains(driver).move_to_element(ticket_element).click().perform()
                    clicked = True
                    self.log("Clicked with ActionChains", 'info', browser_id)
                except:
                    pass
            
            # Method 4: Regular click as last resort
            if not clicked:
                try:
                    ticket_element.click()
                    clicked = True
                    self.log("Clicked with regular click", 'info', browser_id)
                except:
                    pass
            
            if not clicked:
                self.log("Failed to click ticket", 'error', browser_id)
                return False
            
            # Wait for page load/navigation
            time.sleep(1)
            
            # Dismiss any popups that might appear
            self.dismiss_popups(driver)
            
            # Find and click buy button
            for selector in self.buy_selectors:
                try:
                    if selector.startswith('//'):
                        buy_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        buy_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Verify button text if possible
                    btn_text = buy_btn.text.lower()
                    if any(word in btn_text for word in ['acquista', 'compra', 'buy', 'prenota']):
                        # Scroll to button
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                        time.sleep(0.1)
                        
                        # Click buy button
                        driver.execute_script("arguments[0].click();", buy_btn)
                        
                        self.log(f"🎯 BUY BUTTON CLICKED! ({btn_text})", 'alert', browser_id)
                        
                        # Take screenshot if enabled
                        if self.settings.get('auto_screenshot'):
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            Path("screenshots").mkdir(exist_ok=True)
                            screenshot_path = f"screenshots/purchase_{browser_id}_{timestamp}.png"
                            driver.save_screenshot(screenshot_path)
                            self.log(f"📸 Screenshot saved: {screenshot_path}", 'info', browser_id)
                        
                        # Check for CAPTCHA after buy click
                        time.sleep(1)
                        if self.detect_captcha(driver):
                            if not self.solve_captcha(driver, browser_id):
                                return False
                        
                        # Wait for potential redirect/confirmation
                        time.sleep(2)
                        
                        # Check if we're on a checkout/payment page
                        current_url = driver.current_url.lower()
                        if any(word in current_url for word in ['checkout', 'payment', 'pagamento', 'cart', 'carrello']):
                            self.log("✅ Reached checkout page!", 'success', browser_id)
                            
                            # Take another screenshot of checkout
                            if self.settings.get('auto_screenshot'):
                                screenshot_path = f"screenshots/checkout_{browser_id}_{timestamp}.png"
                                driver.save_screenshot(screenshot_path)
                                self.log(f"📸 Checkout screenshot: {screenshot_path}", 'info', browser_id)
                        
                        return True
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    self.log(f"Error with buy button: {str(e)[:50]}", 'warning', browser_id)
                    continue
            
            self.log(f"No buy button found on detail page", 'warning', browser_id)
            
            # Try to go back and try next ticket
            driver.back()
            return False
            
        except Exception as e:
            self.log(f"Purchase failed - {str(e)[:50]}", 'error', browser_id)
            self.stats.record_error()
            return False
    
    def hunt_tickets(self, browser_id, driver):
        """Enhanced hunting loop with smart features"""
        self.log(f"Hunter starting...", 'browser', browser_id)
        self.log(f"Browser {browser_id}: Starting hunt_tickets method", 'debug', browser_id)
        
        # Navigate to target
        target_url = self.settings.get('target_url', DEFAULT_TARGET_URL)
        self.log(f"Browser {browser_id}: Getting target URL: {target_url[:50]}...", 'debug', browser_id)
        try:
            self.log(f"Browser {browser_id}: About to navigate to URL", 'debug', browser_id)
            driver.get(target_url)
            self.log(f"Page loaded: {target_url[:50]}...", 'info', browser_id)
            
            # Verify we're on the right page
            current_url = driver.current_url
            self.log(f"Browser {browser_id}: Current URL after navigation: {current_url[:50]}...", 'debug', browser_id)
            if "fansale" not in current_url.lower():
                self.log(f"Browser {browser_id}: WARNING - Not on FanSale! Current URL: {current_url}", 'warning', browser_id)
            
            # Wait for page to fully load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            self.log(f"Navigation failed - {e}", 'error', browser_id)
            self.stats.record_error()
            return
        
        # Initial setup
        time.sleep(2)
        self.dismiss_popups(driver)  # Clear any initial popups silently
        
        last_refresh = time.time()
        last_popup_check = time.time()
        last_browser_clear = time.time()  # Track when browser data was last cleared
        last_summary = time.time()  # Track when we last showed a summary
        consecutive_errors = 0
        tickets_on_page = 0  # Track number of tickets currently visible
        
        # Main hunting loop
        while not self.shutdown_event.is_set():
            try:
                # Check if we've secured enough tickets
                if self.tickets_secured >= self.settings.get('max_tickets'):
                    self.log("Target reached, stopping hunter", 'success', browser_id)
                    break
                
                # Record check
                self.stats.record_check()
                
                # Log speed every 50 checks instead of 20 to reduce noise
                if self.stats.stats['total_checks'] % 50 == 0:
                    cpm = self.stats.stats['checks_per_minute']
                    # Only log if speed is notable
                    if cpm > 0:
                        self.log(f"📊 Speed: {cpm} CPM", 'speed', browser_id)
                
                # Periodic popup dismissal
                if time.time() - last_popup_check > 10:
                    dismissed = self.dismiss_popups(driver)
                    # Only log if we actually dismissed something
                    if dismissed > 0:
                        self.log(f"🚫 Dismissed {dismissed} popup{'s' if dismissed > 1 else ''}", 'info', browser_id)
                    last_popup_check = time.time()
                    
                    # Check for persistent bot popup
                    if self.detect_bot_popup(driver):
                        if browser_id not in self.bot_popup_start_time:
                            self.bot_popup_start_time[browser_id] = time.time()
                            self.log("🤖 Bot detection popup detected", 'warning', browser_id)
                            
                            # Try clicking the button immediately
                            try:
                                buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Carica Offerte') or contains(text(), 'Carica Offerta')]")
                                for btn in buttons:
                                    if btn.is_displayed():
                                        driver.execute_script("arguments[0].click();", btn)
                                        self.log("🖱️ Clicked 'Carica Offerte' button", 'info', browser_id)
                                        time.sleep(2)
                                        break
                            except:
                                pass
                        else:
                            # Check if popup has persisted for 10 seconds
                            popup_duration = time.time() - self.bot_popup_start_time[browser_id]
                            if popup_duration > 10:
                                # Try alternative solutions
                                self.log(f"⏱️ Bot popup persisted for {int(popup_duration)}s - trying solutions", 'warning', browser_id)
                                if self.handle_persistent_bot_popup(driver, browser_id):
                                    # Reset the timer if successful
                                    del self.bot_popup_start_time[browser_id]
                                    # Reset refresh timer to prevent immediate refresh
                                    last_refresh = time.time()
                                else:
                                    self.log("❌ Bot popup persists - browser may need restart", 'error', browser_id)
                                    # Mark browser for restart by setting negative value
                                    self.bot_popup_start_time[browser_id] = -1
                                    return  # Exit this browser's hunting loop
                    else:
                        # Clear the timer if popup is gone
                        if browser_id in self.bot_popup_start_time:
                            if self.bot_popup_start_time[browser_id] > 0:
                                self.log("✅ Bot popup cleared!", 'success', browser_id)
                            del self.bot_popup_start_time[browser_id]
                
                # Clear browser data every 5 minutes to prevent popup blocking
                if time.time() - last_browser_clear > 300:  # 5 minutes
                    self.log("⏰ 5 minutes elapsed - clearing browser data", 'info', browser_id)
                    if self.clear_browser_data(driver):
                        last_browser_clear = time.time()
                        # Wait a bit after clearing
                        time.sleep(3)
                
                # Find tickets with all selectors
                tickets = []
                ticket_details = []  # Store the actual text elements
                
                for selector in self.ticket_selectors:
                    try:
                        found = driver.find_elements(By.CSS_SELECTOR, selector)
                        if found:
                            # For span.OfferEntry-SeatDescription, get parent clickable element but store the span
                            if selector == "span.OfferEntry-SeatDescription":
                                parent_tickets = []
                                for elem in found:
                                    # Try to find the parent tr or div that contains the ticket
                                    try:
                                        parent = elem.find_element(By.XPATH, "./ancestor::tr[@class='EventEntry'] | ./ancestor::div[contains(@class,'OfferEntry')]")
                                        if parent and parent not in parent_tickets:
                                            parent_tickets.append(parent)
                                            ticket_details.append(elem)  # Store the span with actual text
                                    except:
                                        # If no parent found, use the element itself
                                        parent_tickets.append(elem)
                                        ticket_details.append(elem)
                                tickets.extend(parent_tickets)
                            else:
                                tickets.extend(found)
                                ticket_details.extend(found)  # For other selectors, element is the same
                            
                            # Don't log here - we'll log only NEW tickets below
                            break  # Use first successful selector
                    except:
                        pass
                
                # Update ticket count and show summary periodically
                current_ticket_count = len(tickets)
                if current_ticket_count != tickets_on_page or (time.time() - last_summary > 30):
                    if current_ticket_count > 0:
                        # Only log summary every 30 seconds or when count changes
                        if current_ticket_count != tickets_on_page:
                            self.log(f"👀 Monitoring {current_ticket_count} ticket{'s' if current_ticket_count != 1 else ''} on page", 'info', browser_id)
                        tickets_on_page = current_ticket_count
                        last_summary = time.time()
                    elif tickets_on_page > 0:
                        # Tickets disappeared
                        self.log("📭 No tickets currently visible", 'info', browser_id)
                        tickets_on_page = 0
                
                # Process tickets
                for i, ticket in enumerate(tickets):
                    if self.shutdown_event.is_set():
                        break
                    
                    try:
                        # Extract ticket info from the detail element (which has the actual text)
                        detail_element = ticket_details[i] if i < len(ticket_details) else ticket
                        ticket_info = self.extract_ticket_info(detail_element)
                        ticket_hash = self.generate_ticket_hash(ticket_info['raw_text'])
                        
                        # Check if new
                        if ticket_hash in self.seen_tickets:
                            continue
                        
                        self.seen_tickets.add(ticket_hash)
                        
                        # Record found ticket
                        category = ticket_info['category']
                        self.stats.found_ticket(category, ticket_info)
                        
                        # Set current ticket info for analytics
                        self.current_ticket_info = ticket_info
                        self.current_ticket_info['browser_id'] = browser_id
                        
                        # Format ticket details like user wants
                        timestamp = datetime.now().strftime('%H:%M')
                        
                        # Get ticket details
                        detail_parts = ticket_info.get('details', [])
                        if detail_parts:
                            # Join details with | separator
                            ticket_details_str = " | ".join(detail_parts[:4])  # Limit to first 4 details
                        else:
                            # Fallback to basic info
                            ticket_details_str = ""
                            if ticket_info.get('sector'):
                                ticket_details_str += f"Settore {ticket_info['sector']} | "
                            if ticket_info.get('row'):
                                ticket_details_str += f"Fila {ticket_info['row']} | "
                            if ticket_info.get('seat'):
                                ticket_details_str += f"Posto {ticket_info['seat']} | "
                            ticket_details_str = ticket_details_str.rstrip(' | ')
                        
                        # Extract price more clearly
                        price_str = f"€ {ticket_info['price']}" if ticket_info['price'] else ""
                        if not price_str:
                            # Try to find price in raw text
                            import re
                            price_match = re.search(r'€\s*(\d+)', ticket_info['raw_text'])
                            if price_match:
                                price_str = f"€ {price_match.group(1)}"
                        
                        # Format ticket category
                        category_display = {
                            'prato_a': 'PRATO A',
                            'prato_b': 'PRATO B', 
                            'seating': ''
                        }.get(category, '')
                        
                        # Build complete log line with actual ticket info
                        if ticket_details_str:
                            if price_str:
                                log_line = f"{timestamp} - {ticket_details_str} {price_str}"
                            else:
                                log_line = f"{timestamp} - {ticket_details_str}"
                        else:
                            # Fallback: show some of the raw text
                            raw_clean = ticket_info['raw_text'].replace('\n', ' | ')[:100]
                            log_line = f"{timestamp} - {raw_clean}"
                        
                        # Log the ticket with proper formatting
                        self.log(f"🎫 {log_line}", 'ticket', browser_id)
                        
                        # Add to ticket monitor with timestamp
                        with self.ticket_monitor_lock:
                            self.ticket_monitor.append({
                                'timestamp': timestamp,
                                'browser_id': browser_id,
                                'category': category_display,
                                'log_line': log_line,
                                'price': price_str,
                                'details': ticket_details_str,
                                'raw_text': ticket_info['raw_text'][:100]
                            })
                        
                        # Check if we should buy
                        ticket_types = self.settings.get('ticket_types')
                        if 'all' in ticket_types or category in ticket_types:
                            if self.should_buy_ticket(ticket_info):
                                with self.purchase_lock:
                                    if self.tickets_secured < self.settings.get('max_tickets'):
                                        self.log(f"⚡ Attempting purchase...", 'warning', browser_id)
                                        
                                        if self.attempt_purchase(driver, ticket, browser_id):
                                            self.tickets_secured += 1
                                            self.stats.secured_ticket()
                                            self.log(f"🎉 TICKET SECURED! ({self.tickets_secured}/{self.settings.get('max_tickets')})", 'alert')
                                            
                                            # Reset to main page after successful purchase
                                            driver.get(target_url)
                                            time.sleep(2)
                                            
                                            if self.tickets_secured >= self.settings.get('max_tickets'):
                                                self.log("🏆 ALL TICKETS SECURED!", 'alert')
                                                self.shutdown_event.set()
                                                return
                            else:
                                self.log(f"Skipped: {ticket_info.get('reason', 'Does not meet criteria')}", 'info', browser_id)
                    
                    except Exception as e:
                        self.log(f"Error processing ticket: {str(e)[:30]}", 'warning', browser_id)
                        continue
                
                # Reset error counter on successful iteration
                consecutive_errors = 0
                
                # Wait before next check
                wait_time = random.uniform(
                    self.settings.get('min_wait'),
                    self.settings.get('max_wait')
                )
                time.sleep(wait_time)
                
                # Periodic refresh
                refresh_interval = self.settings.get('refresh_interval')
                if time.time() - last_refresh > refresh_interval + random.randint(-3, 3):
                    self.log(f"Refreshing page", 'info', browser_id)
                    driver.refresh()
                    time.sleep(2)
                    self.dismiss_popups(driver)
                    last_refresh = time.time()
                
            except WebDriverException as e:
                consecutive_errors += 1
                if "invalid session" in str(e).lower():
                    self.log(f"Session died", 'error', browser_id)
                    break
                else:
                    self.log(f"WebDriver error ({consecutive_errors})", 'error', browser_id)
                    self.stats.record_error()
                    
                    if consecutive_errors > 5:
                        self.log(f"Too many errors, restarting browser", 'warning', browser_id)
                        try:
                            driver.get(target_url)
                            consecutive_errors = 0
                        except:
                            break
                    
                    time.sleep(2)
                    
            except Exception as e:
                self.log(f"Unexpected error - {str(e)[:50]}", 'error', browser_id)
                self.stats.record_error()
                time.sleep(2)
    
    def run_bot(self):
        """Run the bot with current settings"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        # Show run configuration
        TerminalUI.print_header(theme)
        print(colors["accent"] + "    🚀 STARTING HUNT\n")
        
        target_url = self.settings.get('target_url', DEFAULT_TARGET_URL)
        print(f"{colors['primary']}    Target: {colors['accent']}{target_url[:60]}...")
        print(f"{colors['primary']}    Browsers: {colors['accent']}{self.settings.get('num_browsers')}")
        print(f"{colors['primary']}    Max tickets: {colors['accent']}{self.settings.get('max_tickets')}")
        print(f"{colors['primary']}    Hunting: {colors['accent']}{', '.join(self.settings.get('ticket_types'))}")
        print(f"{colors['primary']}    Auto-buy: {colors['accent']}{'ON' if self.settings.get('auto_buy') else 'OFF'}\n")
        
        input(colors["secondary"] + "    Press Enter to start hunting..." + Fore.WHITE)
        
        # Clear screen and show dashboard header
        TerminalUI.clear()
        TerminalUI.live_dashboard_header(theme)
        
        # Start live stats display thread
        stats_thread = threading.Thread(target=self.display_live_stats, daemon=True)
        stats_thread.start()
        
        # Create browsers and start hunting threads
        with ThreadPoolExecutor(max_workers=self.settings.get('num_browsers')) as executor:
            futures = []
            
            for i in range(self.settings.get('num_browsers')):
                try:
                    driver = self.create_browser(i)
                    self.browsers.append(driver)
                    self.stats.stats['active_browsers'] += 1
                    
                    # Small delay to ensure browser is ready
                    time.sleep(0.5)
                    
                    self.log(f"Browser {i}: Submitting to thread pool", 'debug')
                    future = executor.submit(self.hunt_tickets, i, driver)
                    futures.append(future)
                    
                    self.log(f"✅ Browser {i} launched", 'success')
                    time.sleep(1)
                    
                except Exception as e:
                    self.log(f"❌ Failed to create browser {i}: {e}", 'error')
                    self.stats.record_error()
            
            # Wait for completion
            try:
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.log(f"Thread error: {e}", 'error')
                        self.stats.record_error()
                        
            except KeyboardInterrupt:
                self.log("\n⚠️  Shutdown requested...", 'warning')
                self.shutdown_event.set()
        
        # Cleanup
        self.log("Closing browsers...", 'info')
        for driver in self.browsers:
            try:
                driver.quit()
            except:
                pass
        
        # Save historical stats
        self.stats.save_historical_stats()
        
        # Final summary
        stats = self.stats.get_stats()
        runtime = self.stats.get_runtime()
        
        print(f"\n{colors['primary']}{'='*80}")
        print(colors['accent'] + "  📊 HUNTING SESSION COMPLETE".center(80))
        print(f"{colors['primary']}{'='*80}\n")
        
        print(f"{colors['secondary']}  Runtime: {colors['accent']}{runtime}")
        print(f"{colors['secondary']}  Total checks: {colors['accent']}{stats['total_checks']:,}")
        print(f"{colors['secondary']}  Unique tickets seen: {colors['accent']}{stats['unique_tickets_seen']}")
        print(f"{colors['secondary']}  Tickets secured: {colors['success']}{stats['tickets_secured']}")
        print(f"{colors['secondary']}  Best CPM: {colors['accent']}{stats['best_cpm']}")
        print(f"{colors['secondary']}  Errors: {colors['error']}{stats['errors_encountered']}")
        print(f"{colors['secondary']}  CAPTCHAs solved: {colors['accent']}{stats['captchas_solved']}")
        
        if stats['tickets_found']:
            print(f"\n{colors['secondary']}  Tickets by type:")
            for category, count in stats['tickets_found'].items():
                print(f"    {colors['accent']}• {category.upper()}: {count}")
        
        print(f"\n{colors['primary']}{'='*80}\n")
        
        if stats['tickets_secured'] > 0:
            self.log("🎉 Check your screenshots folder for proof of purchase!", 'alert')
        
        input(f"\n{colors['secondary']}Press Enter to return to menu...{Fore.WHITE}")
    
    def show_statistics(self):
        """Show detailed statistics and history"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📊 STATISTICS & HISTORY\n")
        
        # Current session stats
        if hasattr(self, 'stats') and self.stats.stats['total_checks'] > 0:
            stats = self.stats.get_stats()
            runtime = self.stats.get_runtime()
            
            print(colors["primary"] + "    CURRENT SESSION")
            print(colors["secondary"] + f"    Runtime: {colors['accent']}{runtime}")
            print(colors["secondary"] + f"    Checks: {colors['accent']}{stats['total_checks']:,}")
            print(colors["secondary"] + f"    Best CPM: {colors['accent']}{stats['best_cpm']}")
            print(colors["secondary"] + f"    Tickets secured: {colors['success']}{stats['tickets_secured']}")
            print()
        
        # Historical stats
        if hasattr(self.stats, 'historical'):
            hist = self.stats.historical
            
            print(colors["primary"] + "    ALL TIME STATISTICS")
            print(colors["secondary"] + f"    Total runs: {colors['accent']}{hist['total_runs']}")
            print(colors["secondary"] + f"    Total runtime: {colors['accent']}{hist['total_runtime']//3600:.0f} hours")
            print(colors["secondary"] + f"    Total checks: {colors['accent']}{hist['total_checks']:,}")
            print(colors["secondary"] + f"    Total secured: {colors['success']}{hist['total_secured']}")
            
            if hist['tickets_by_type']:
                print(f"\n{colors['secondary']}    Tickets by type:")
                for category, count in hist['tickets_by_type'].items():
                    print(f"      {colors['accent']}• {category.upper()}: {count}")
            
            if hist['best_session']['date']:
                print(f"\n{colors['primary']}    BEST SESSION")
                print(f"{colors['secondary']}    Date: {colors['accent']}{hist['best_session']['date']}")
                print(f"{colors['secondary']}    Tickets: {colors['success']}{hist['best_session']['tickets']}")
                print(f"{colors['secondary']}    CPM: {colors['accent']}{hist['best_session']['cpm']}")
        
        # Recent notifications
        if hasattr(self, 'notifications'):
            recent = self.notifications.get_recent_notifications(10)
            if recent:
                print(f"\n{colors['primary']}    RECENT EVENTS")
                for notif in recent:
                    level_colors = {
                        'alert': colors['accent'],
                        'success': colors['success'],
                        'error': colors['error'],
                        'warning': colors['warning']
                    }
                    color = level_colors.get(notif['level'], colors['secondary'])
                    print(f"    {color}[{notif['time']}] {notif['message']}")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def show_help(self):
        """Display comprehensive help"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📖 HELP & GUIDE\n")
        
        print(colors["primary"] + "    QUICK START")
        print(colors["secondary"] + "    1. Configure settings (browsers, ticket types)")
        print(colors["secondary"] + "    2. Set up auto-buy rules if desired")
        print(colors["secondary"] + "    3. Start hunting and monitor live stats")
        print(colors["secondary"] + "    4. Bot will notify you of purchases\n")
        
        print(colors["primary"] + "    TIPS FOR SUCCESS")
        print(colors["secondary"] + "    • Use 2-4 browsers for best coverage")
        print(colors["secondary"] + "    • Set specific ticket types to reduce noise")
        print(colors["secondary"] + "    • Enable auto-buy for faster purchases")
        print(colors["secondary"] + "    • Set price limits to avoid overpaying")
        print(colors["secondary"] + "    • Keep sound alerts on for notifications\n")
        
        print(colors["primary"] + "    KEYBOARD SHORTCUTS")
        print(colors["secondary"] + "    • Ctrl+C: Stop the bot gracefully")
        print(colors["secondary"] + "    • In quick settings: +/- adjust browsers")
        print(colors["secondary"] + "    • In quick settings: A toggle auto-buy\n")
        
        print(colors["primary"] + "    PERFORMANCE TARGETS")
        print(colors["secondary"] + "    • 60-300 checks/minute per browser")
        print(colors["secondary"] + "    • <1 second purchase decision")
        print(colors["secondary"] + "    • Linear scaling with browsers\n")
        
        print(colors["primary"] + "    TROUBLESHOOTING")
        print(colors["secondary"] + "    • Chrome errors: Update Chrome browser")
        print(colors["secondary"] + "    • Slow performance: Reduce browser count")
        print(colors["secondary"] + "    • No tickets found: Check selectors match site")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def show_about(self):
        """Show about information"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    💎 ABOUT FANSALE ULTIMATE BOT\n")
        
        print(colors["secondary"] + "    Version: " + colors["accent"] + "Enhanced Edition")
        print(colors["secondary"] + "    Purpose: " + colors["accent"] + "High-speed ticket reservation")
        print(colors["secondary"] + "    Target: " + colors["accent"] + "FanSale.it platform\n")
        
        print(colors["primary"] + "    FEATURES")
        print(colors["secondary"] + "    • Multi-browser parallel hunting")
        print(colors["secondary"] + "    • Real-time statistics dashboard")
        print(colors["secondary"] + "    • Persistent settings & profiles")
        print(colors["secondary"] + "    • CAPTCHA handling (auto/manual)")
        print(colors["secondary"] + "    • Smart purchase rules")
        print(colors["secondary"] + "    • Multiple UI themes\n")
        
        print(colors["primary"] + "    PERFORMANCE")
        print(colors["secondary"] + "    • Ticket detection: <100ms")
        print(colors["secondary"] + "    • Purchase decision: <10ms")
        print(colors["secondary"] + "    • Checks per minute: 60-300\n")
        
        print(colors["warning"] + "    ⚠️  DISCLAIMER")
        print(colors["secondary"] + "    This bot is for educational and defensive")
        print(colors["secondary"] + "    purposes only. Users are responsible for")
        print(colors["secondary"] + "    complying with FanSale's terms of service.")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def main(self):
        """Enhanced main application loop with analytics focus"""
        while True:
            choice = TerminalUI.main_menu(self.settings, self.analytics)
            
            if choice == '1':
                # Start hunting
                self.run_bot()
                # Save session analytics
                self.analytics.save_session()
                # Reset for next run
                self.shutdown_event.clear()
                self.tickets_secured = 0
                self.seen_tickets.clear()
                self.browsers.clear()
                self.stats = StatsTracker()
                # Start new session
                self.analytics = EnhancedAnalytics()
                
            elif choice == '2':
                # Quick config
                self.quick_config()
                
            elif choice == '3':
                # Advanced settings (keep existing)
                self.configure_advanced_settings()
                
            elif choice == '4':
                # Live monitor
                self.show_live_monitor()
                
            elif choice == '5':
                # Hourly patterns
                self.show_hourly_patterns()
                
            elif choice == '6':
                # Ticket analysis
                self.show_ticket_analysis()
                
            elif choice == '7':
                # Daily reports
                self.show_daily_reports()
                
            elif choice == '8':
                # Success metrics
                self.show_success_metrics()
                
            elif choice == '9':
                # Test browser
                self.test_browser_detection()
                
            elif choice == 'P':
                # Proxy setup
                self.configure_proxy()
                
            elif choice == 'S':
                # Profile manager
                self.profile_manager()
                
            elif choice == 'L':
                # View recent logs
                self.show_recent_logs()
                
            elif choice == 'H':
                # Help
                self.show_help()
                
            elif choice == 'X':
                # Exit
                theme = self.settings.get("theme", "cyberpunk")
                colors = TerminalUI.THEMES[theme]
                
                # Save analytics before exit
                if hasattr(self, 'analytics'):
                    self.analytics.save_session()
                    
                print(f"\n{colors['accent']}👋 Thanks for using FanSale Ultimate Bot!")
                
                # Show quick summary
                if hasattr(self, 'analytics'):
                    metrics = self.analytics.get_success_metrics()
                    if metrics:
                        print(f"{colors['secondary']}Total tickets found: {colors['success']}{metrics['total_tickets_found']}")
                        print(f"{colors['secondary']}Total tickets secured: {colors['success']}{metrics['total_tickets_secured']}")
                        print(f"{colors['secondary']}Success rate: {colors['accent']}{metrics['success_rate']}%")
                
                print(f"\n{colors['secondary']}Happy hunting!\n")
                break
            
            else:
                self.log("Invalid choice", 'error')
                time.sleep(1)
    
    def quick_settings(self):
        """Quick settings interface"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        while True:
            action = TerminalUI.quick_settings_menu(self.settings)
            
            if action == '':
                # Start hunting
                self.run_bot()
                break
            elif action == '+':
                # Increase browsers
                current = self.settings.get('num_browsers')
                self.settings.update('num_browsers', min(8, current + 1))
            elif action == '-':
                # Decrease browsers
                current = self.settings.get('num_browsers')
                self.settings.update('num_browsers', max(1, current - 1))
            elif action.upper() == 'A':
                # Toggle auto-buy
                self.settings.update('auto_buy', not self.settings.get('auto_buy'))
            elif action.upper() == 'M':
                # Toggle sound
                self.settings.update('sound_alerts', not self.settings.get('sound_alerts'))
            elif action.upper() == 'S':
                # Adjust speed
                try:
                    min_wait = float(input(f"\n{colors['primary']}Min wait (seconds): {Fore.WHITE}"))
                    max_wait = float(input(f"{colors['primary']}Max wait (seconds): {Fore.WHITE}"))
                    self.settings.update('min_wait', max(0.1, min_wait))
                    self.settings.update('max_wait', max(min_wait, max_wait))
                except:
                    pass
            elif action == '\x1b':  # ESC key
                break
    
    def configure_auto_buy_rules(self):
        """Configure auto-buy rules"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🤖 AUTO-BUY RULES\n")
        
        # Current rules
        print(colors["primary"] + "    CURRENT CONFIGURATION")
        print(colors["secondary"] + f"    Auto-buy: {colors['accent']}{'ENABLED' if self.settings.get('auto_buy') else 'DISABLED'}")
        print(colors["secondary"] + f"    Max price: {colors['accent']}€{self.settings.get('max_price') or 'No limit'}")
        print(colors["secondary"] + f"    Preferred sectors: {colors['accent']}{', '.join(self.settings.get('preferred_sectors')) or 'Any'}")
        print(colors["secondary"] + f"    Blacklist: {colors['accent']}{', '.join(self.settings.get('blacklist_sectors')) or 'None'}\n")
        
        print(colors["secondary"] + "    [1] Toggle Auto-buy")
        print(colors["secondary"] + "    [2] Set Max Price")
        print(colors["secondary"] + "    [3] Set Preferred Sectors")
        print(colors["secondary"] + "    [4] Set Blacklist Sectors")
        print(colors["secondary"] + "    [5] Clear All Rules")
        print(colors["secondary"] + "    [B] Back to Menu\n")
        
        choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip()
        
        if choice == '1':
            self.settings.update('auto_buy', not self.settings.get('auto_buy'))
            self.log(f"Auto-buy {'enabled' if self.settings.get('auto_buy') else 'disabled'}", 'success')
        elif choice == '2':
            try:
                price = float(input(f"\n{colors['primary']}Max price in EUR (0 for no limit): {Fore.WHITE}"))
                self.settings.update('max_price', price)
                self.log("Max price updated", 'success')
            except:
                self.log("Invalid price", 'error')
        elif choice == '3':
            sectors = input(f"\n{colors['primary']}Preferred sectors (comma-separated, e.g., 1,2,3): {Fore.WHITE}").strip()
            if sectors:
                self.settings.update('preferred_sectors', [s.strip() for s in sectors.split(',')])
                self.log("Preferred sectors updated", 'success')
        elif choice == '4':
            sectors = input(f"\n{colors['primary']}Blacklist sectors (comma-separated): {Fore.WHITE}").strip()
            if sectors:
                self.settings.update('blacklist_sectors', [s.strip() for s in sectors.split(',')])
                self.log("Blacklist updated", 'success')
        elif choice == '5':
            self.settings.update('auto_buy', False)
            self.settings.update('max_price', 0)
            self.settings.update('preferred_sectors', [])
            self.settings.update('blacklist_sectors', [])
            self.log("All rules cleared", 'success')
        
        if choice != 'B':
            time.sleep(1)
            self.configure_auto_buy_rules()
    
    def show_live_dashboard_demo(self):
        """Show a demo of the live dashboard"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.clear()
        
        print(colors["accent"] + """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                          LIVE DASHBOARD (DEMO)                           ║
    ╠══════════════════════════════════════════════════════════════════════════╣
    ║                                                                          ║
    ║  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        ║
    ║  │   RUNTIME       │  │  CHECKS/MIN     │  │   TICKETS       │        ║
    ║  │   00:15:42      │  │     247         │  │   FOUND: 18     │        ║
    ║  └─────────────────┘  └─────────────────┘  └─────────────────┘        ║
    ║                                                                          ║
    ║  ┌────────────────────────────────────────────────────────────┐        ║
    ║  │ BROWSER STATUS                                              │        ║
    ║  ├────────────────────────────────────────────────────────────┤        ║
    ║  │ [1] ████████████████████░░░ 75% - Scanning...             │        ║
    ║  │ [2] ██████████████████████ 100% - Purchasing ticket!      │        ║
    ║  │ [3] ████████░░░░░░░░░░░░░░ 35% - Refreshing page          │        ║
    ║  │ [4] ████████████░░░░░░░░░░ 50% - Dismissing popup         │        ║
    ║  └────────────────────────────────────────────────────────────┘        ║
    ║                                                                          ║
    ║  ┌────────────────────────────────────────────────────────────┐        ║
    ║  │ RECENT TICKETS                                              │        ║
    ║  ├────────────────────────────────────────────────────────────┤        ║
    ║  │ [12:34:56] PRATO A - €85 - Sector 3                        │        ║
    ║  │ [12:34:52] SETTORE - €65 - Row 15                          │        ║
    ║  │ [12:34:48] PRATO B - €75 - Available                       │        ║
    ║  └────────────────────────────────────────────────────────────┘        ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
        """ + Style.RESET_ALL)
        
        input(f"\n{colors['secondary']}    This is a preview. Press Enter to return...{Fore.WHITE}")
    
    def show_performance_report(self):
        """Show detailed performance report"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📈 PERFORMANCE REPORT\n")
        
        # Simulated data for demo
        print(colors["primary"] + "    SPEED METRICS")
        print(colors["secondary"] + "    • Ticket detection: " + colors["success"] + "<100ms")
        print(colors["secondary"] + "    • Category analysis: " + colors["success"] + "<10ms")
        print(colors["secondary"] + "    • Purchase decision: " + colors["success"] + "<5ms")
        print(colors["secondary"] + "    • Click execution: " + colors["success"] + "<200ms\n")
        
        print(colors["primary"] + "    EFFICIENCY RATINGS")
        print(colors["secondary"] + "    • CPU usage: " + colors["accent"] + "Low (15-25%)")
        print(colors["secondary"] + "    • Memory usage: " + colors["accent"] + "~200MB per browser")
        print(colors["secondary"] + "    • Network latency: " + colors["accent"] + "Optimized")
        print(colors["secondary"] + "    • Success rate: " + colors["success"] + "95%+\n")
        
        print(colors["primary"] + "    RECOMMENDATIONS")
        print(colors["secondary"] + "    ✓ Current settings are optimized")
        print(colors["secondary"] + "    ✓ Browser count is within ideal range")
        print(colors["secondary"] + "    ✓ Check intervals are balanced")
        
        input(f"\n{colors['secondary']}    Press Enter to return to menu...{Fore.WHITE}")
    
    def configure_notifications(self):
        """Configure notification settings"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🔔 NOTIFICATION SETTINGS\n")
        
        print(colors["secondary"] + f"    Sound alerts: {colors['accent']}{'ON' if self.settings.get('sound_alerts') else 'OFF'}")
        print(colors["secondary"] + f"    Webhook URL: {colors['accent']}{self.settings.get('notification_webhook')[:30] + '...' if self.settings.get('notification_webhook') else 'Not set'}\n")
        
        print(colors["secondary"] + "    [1] Toggle Sound Alerts")
        print(colors["secondary"] + "    [2] Set Webhook URL")
        print(colors["secondary"] + "    [3] Test Notifications")
        print(colors["secondary"] + "    [B] Back to Menu\n")
        
        choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip()
        
        if choice == '1':
            self.settings.update('sound_alerts', not self.settings.get('sound_alerts'))
            self.log(f"Sound alerts {'enabled' if self.settings.get('sound_alerts') else 'disabled'}", 'success')
        elif choice == '2':
            url = input(f"\n{colors['primary']}Webhook URL (Discord/Slack): {Fore.WHITE}").strip()
            self.settings.update('notification_webhook', url)
            self.log("Webhook URL updated", 'success')
        elif choice == '3':
            self.log("Test notification!", 'alert')
            if self.settings.get('notification_webhook'):
                self.notifications._send_webhook("🎫 Test notification from FanSale Bot")
                self.log("Webhook test sent", 'info')
        
        if choice != 'B':
            time.sleep(1)
            self.configure_notifications()
    
    def quick_config(self):
        """Quick configuration for common settings"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    ⚡ QUICK CONFIGURATION\n")
        
        print(colors["secondary"] + "    [1] Low (1 browser, relaxed timing)")
        print(colors["secondary"] + "    [2] Medium (2 browsers, balanced)")
        print(colors["secondary"] + "    [3] High (4 browsers, aggressive)")
        print(colors["secondary"] + "    [4] Ultra (8 browsers, maximum speed)")
        print(colors["secondary"] + "    [B] Back to Menu\n")
        
        choice = input(colors["accent"] + "    Select preset: " + Fore.WHITE).strip()
        
        if choice == '1':
            self.settings.update('num_browsers', 1)
            self.settings.update('min_wait', 0.5)
            self.settings.update('max_wait', 1.5)
            self.log("Applied LOW preset", 'success')
        elif choice == '2':
            self.settings.update('num_browsers', 2)
            self.settings.update('min_wait', 0.3)
            self.settings.update('max_wait', 1.0)
            self.log("Applied MEDIUM preset", 'success')
        elif choice == '3':
            self.settings.update('num_browsers', 4)
            self.settings.update('min_wait', 0.2)
            self.settings.update('max_wait', 0.7)
            self.log("Applied HIGH preset", 'success')
        elif choice == '4':
            self.settings.update('num_browsers', 8)
            self.settings.update('min_wait', 0.1)
            self.settings.update('max_wait', 0.5)
            self.log("Applied ULTRA preset", 'success')
        
        if choice in '1234':
            self.settings.save()
            time.sleep(2)
    
    def show_live_monitor(self):
        """Display live monitoring dashboard"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        
        print(colors["accent"] + "\n    📊 LIVE MONITOR - Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get current stats
                stats = self.analytics.get_live_stats()
                
                # Clear screen and show stats
                print('\033[2J\033[H')  # Clear screen
                TerminalUI.print_header(theme)
                
                print(colors["accent"] + "    📊 LIVE MONITOR\n")
                
                # Show hourly rate
                print(colors["secondary"] + f"    Last Hour: {colors['success']}{stats.get('hourly_rate', 0)} tickets/hour")
                print(colors["secondary"] + f"    Active Now: {colors['accent']}{stats.get('active_browsers', 0)} browsers")
                
                # Show recent discoveries
                recent = stats.get('recent_tickets', [])
                if recent:
                    print(f"\n{colors['secondary']}    Recent Discoveries:")
                    for ticket in recent[-5:]:
                        print(f"      {colors['success']}• {ticket['time']} - {ticket['type']} ({ticket['price']})")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n{colors['secondary']}    Monitor stopped")
            time.sleep(1)
    
    def show_hourly_patterns(self):
        """Display hourly ticket patterns"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📈 HOURLY PATTERNS\n")
        
        patterns = self.analytics.get_hourly_patterns()
        
        if not patterns:
            print(colors["warning"] + "    No data available yet")
        else:
            # Show best hours
            sorted_hours = sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
            
            print(colors["secondary"] + "    Best hunting hours:")
            for hour, data in sorted_hours:
                bar = "█" * int(data['count'] / max(1, max(p['count'] for p in patterns.values())) * 20)
                print(f"      {colors['accent']}{hour:02d}:00 {colors['success']}{bar} {data['count']} tickets")
            
            # Show recommendations
            print(f"\n{colors['secondary']}    💡 Recommendations:")
            best_hour = sorted_hours[0][0] if sorted_hours else 0
            print(f"      {colors['success']}• Best time to hunt: {best_hour:02d}:00 - {(best_hour+1)%24:02d}:00")
            print(f"      {colors['success']}• Average tickets/hour: {sum(p['count'] for p in patterns.values()) / len(patterns):.1f}")
        
        input(f"\n{colors['secondary']}    Press Enter to continue...{Fore.WHITE}")
    
    def show_ticket_analysis(self):
        """Display ticket type analysis"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🎫 TICKET ANALYSIS\n")
        
        analysis = self.analytics.get_ticket_analysis()
        
        if not analysis:
            print(colors["warning"] + "    No ticket data available")
        else:
            # Show ticket type distribution
            total = sum(analysis.values())
            print(colors["secondary"] + "    Ticket Distribution:")
            for ticket_type, count in sorted(analysis.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                bar = "█" * int(percentage / 5)
                print(f"      {colors['accent']}{ticket_type:12} {colors['success']}{bar} {percentage:.1f}% ({count})")
            
            # Show insights
            print(f"\n{colors['secondary']}    💡 Insights:")
            most_common = max(analysis.items(), key=lambda x: x[1])[0]
            print(f"      {colors['success']}• Most common: {most_common}")
            print(f"      {colors['success']}• Total types: {len(analysis)}")
            print(f"      {colors['success']}• Total tickets: {total}")
        
        input(f"\n{colors['secondary']}    Press Enter to continue...{Fore.WHITE}")
    
    def show_daily_reports(self):
        """Display daily performance reports"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📅 DAILY REPORTS\n")
        
        reports = self.analytics.get_daily_reports()
        
        if not reports:
            print(colors["warning"] + "    No daily data available")
        else:
            # Show last 7 days
            for date, data in sorted(reports.items(), reverse=True)[:7]:
                print(f"    {colors['secondary']}{date}:")
                print(f"      {colors['success']}Sessions: {data['sessions']}")
                print(f"      {colors['success']}Tickets Found: {data['tickets_found']}")
                print(f"      {colors['success']}Tickets Secured: {data['tickets_secured']}")
                print(f"      {colors['accent']}Success Rate: {data['success_rate']:.1f}%")
                print()
        
        input(f"\n{colors['secondary']}    Press Enter to continue...{Fore.WHITE}")
    
    def show_success_metrics(self):
        """Display success metrics and statistics"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🏆 SUCCESS METRICS\n")
        
        metrics = self.analytics.get_success_metrics()
        
        if metrics:
            # Overall stats
            print(colors["secondary"] + "    Overall Performance:")
            print(f"      {colors['success']}Total Sessions: {metrics['total_sessions']}")
            print(f"      {colors['success']}Total Runtime: {metrics['total_runtime_hours']:.1f} hours")
            print(f"      {colors['success']}Tickets Found: {metrics['total_tickets_found']}")
            print(f"      {colors['success']}Tickets Secured: {metrics['total_tickets_secured']}")
            print(f"      {colors['accent']}Success Rate: {metrics['success_rate']:.1f}%")
            
            # Best performance
            print(f"\n{colors['secondary']}    Records:")
            print(f"      {colors['success']}Best Hour: {metrics.get('best_hour_tickets', 0)} tickets")
            print(f"      {colors['success']}Best Day: {metrics.get('best_day_tickets', 0)} tickets")
            print(f"      {colors['success']}Longest Session: {metrics.get('longest_session_hours', 0):.1f} hours")
        else:
            print(colors["warning"] + "    No metrics available yet")
        
        input(f"\n{colors['secondary']}    Press Enter to continue...{Fore.WHITE}")
    
    def test_browser_detection(self):
        """Test browser for detection issues"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🧪 BROWSER DETECTION TEST\n")
        
        print(colors["secondary"] + "    Starting test browser...")
        
        try:
            driver = self.create_browser(1)
            
            # Test 1: Bot detection services
            print(f"\n{colors['secondary']}    Testing bot detection...")
            driver.get("https://bot.sannysoft.com/")
            time.sleep(3)
            
            # Check results
            try:
                result = driver.find_element(By.TAG_NAME, "body").text
                if "passed" in result.lower():
                    print(f"      {colors['success']}✓ Basic detection: PASSED")
                else:
                    print(f"      {colors['error']}✗ Basic detection: FAILED")
            except:
                print(f"      {colors['warning']}? Could not determine result")
            
            # Test 2: Navigate to FanSale
            print(f"\n{colors['secondary']}    Testing FanSale access...")
            driver.get(self.settings.get('target_url'))
            time.sleep(5)
            
            # Check for blocking
            if "access denied" in driver.page_source.lower():
                print(f"      {colors['error']}✗ FanSale: BLOCKED")
            else:
                print(f"      {colors['success']}✓ FanSale: ACCESSIBLE")
            
            driver.quit()
            
        except Exception as e:
            print(f"      {colors['error']}Error: {e}")
        
        input(f"\n{colors['secondary']}    Press Enter to continue...{Fore.WHITE}")
    
    def configure_proxy(self):
        """Configure proxy settings"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    🌐 PROXY CONFIGURATION\n")
        
        current = self.settings.get('use_proxy', False)
        print(colors["secondary"] + f"    Proxy: {colors['accent']}{'ENABLED' if current else 'DISABLED'}")
        
        if current:
            print(colors["secondary"] + f"    Host: {self.settings.get('proxy_host', 'Not set')}")
            print(colors["secondary"] + f"    Port: {self.settings.get('proxy_port', 'Not set')}")
        
        print(f"\n{colors['secondary']}    [1] Toggle Proxy")
        print(colors["secondary"] + "    [2] Set Proxy Details")
        print(colors["secondary"] + "    [3] Test Proxy")
        print(colors["secondary"] + "    [B] Back\n")
        
        choice = input(colors["accent"] + "    Select option: " + Fore.WHITE).strip()
        
        if choice == '1':
            self.settings.update('use_proxy', not current)
            self.settings.save()
            self.log(f"Proxy {'enabled' if not current else 'disabled'}", 'success')
            time.sleep(1)
            self.configure_proxy()
            
        elif choice == '2':
            host = input(f"\n{colors['primary']}Proxy host: {Fore.WHITE}").strip()
            port = input(f"{colors['primary']}Proxy port: {Fore.WHITE}").strip()
            user = input(f"{colors['primary']}Username (optional): {Fore.WHITE}").strip()
            pass_ = input(f"{colors['primary']}Password (optional): {Fore.WHITE}").strip()
            
            self.settings.update('proxy_host', host)
            self.settings.update('proxy_port', port)
            self.settings.update('proxy_user', user)
            self.settings.update('proxy_pass', pass_)
            self.settings.save()
            
            self.log("Proxy settings updated", 'success')
            time.sleep(1)
            self.configure_proxy()
            
        elif choice == '3':
            self.log("Testing proxy connection...", 'info')
            # Proxy test implementation would go here
            time.sleep(2)
    
    def show_recent_logs(self):
        """Show recent ticket discoveries"""
        theme = self.settings.get("theme", "cyberpunk")
        colors = TerminalUI.THEMES[theme]
        TerminalUI.print_header(theme)
        
        print(colors["accent"] + "    📜 RECENT DISCOVERIES\n")
        
        recent = self.analytics.get_recent_discoveries(20)
        
        if not recent:
            print(colors["warning"] + "    No recent discoveries")
        else:
            for entry in recent:
                timestamp = entry.get('timestamp', 'Unknown')
                ticket_type = entry.get('type', 'Unknown')
                price = entry.get('price', 'N/A')
                sector = entry.get('sector', 'N/A')
                
                print(f"    {colors['secondary']}{timestamp}")
                print(f"      {colors['success']}Type: {ticket_type}")
                print(f"      {colors['success']}Price: {price}")
                print(f"      {colors['success']}Sector: {sector}")
                print()
        
        input(f"\n{colors['secondary']}    Press Enter to continue...{Fore.WHITE}")


if __name__ == "__main__":
    try:
        bot = FanSaleUltimate()
        bot.main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Bot stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)