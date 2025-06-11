"""
Ticket Statistics Tracking System
Persistent storage of ticket operation metrics
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TicketStats:
    """Statistics for a specific ticket category"""
    platform: str
    event_name: str
    category: str
    found_count: int = 0
    reserved_count: int = 0
    failed_count: int = 0
    last_found: Optional[str] = None
    last_reserved: Optional[str] = None
    last_failed: Optional[str] = None
    avg_search_time_ms: float = 0.0
    avg_reserve_time_ms: float = 0.0
    success_rate: float = 0.0


class StatsManager:
    """
    Manages ticket statistics with SQLite persistence
    Thread-safe implementation for concurrent access
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.home() / ".stealthmaster" / "statistics.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.Lock()
        self._init_database()
        self._performance_cache = {}
        
        logger.info(f"Initialized statistics database at: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Ticket statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    found_count INTEGER DEFAULT 0,
                    reserved_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    last_found TIMESTAMP,
                    last_reserved TIMESTAMP,
                    last_failed TIMESTAMP,
                    avg_search_time_ms REAL DEFAULT 0.0,
                    avg_reserve_time_ms REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, event_name, category)
                )
            """)
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    platform TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Session summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    total_searches INTEGER DEFAULT 0,
                    total_reservations INTEGER DEFAULT 0,
                    total_failures INTEGER DEFAULT 0,
                    stealth_detections INTEGER DEFAULT 0,
                    avg_response_time_ms REAL DEFAULT 0.0
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform_event ON ticket_stats(platform, event_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON performance_metrics(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON performance_metrics(timestamp)")
            
            conn.commit()
    
    def record_ticket_found(self, platform: str, event_name: str, category: str, search_time_ms: float):
        """Record that a ticket was found"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Update or insert stats
                    cursor.execute("""
                        INSERT INTO ticket_stats (platform, event_name, category, found_count, last_found, avg_search_time_ms)
                        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, ?)
                        ON CONFLICT(platform, event_name, category) DO UPDATE SET
                            found_count = found_count + 1,
                            last_found = CURRENT_TIMESTAMP,
                            avg_search_time_ms = (avg_search_time_ms * found_count + ?) / (found_count + 1),
                            updated_at = CURRENT_TIMESTAMP
                    """, (platform, event_name, category, search_time_ms, search_time_ms))
                    
                    conn.commit()
                    logger.debug(f"Recorded ticket found: {platform}/{event_name}/{category}")
                    
            except Exception as e:
                logger.error(f"Failed to record ticket found: {e}")
    
    def record_ticket_reserved(self, platform: str, event_name: str, category: str, reserve_time_ms: float):
        """Record successful ticket reservation"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO ticket_stats (platform, event_name, category, reserved_count, last_reserved, avg_reserve_time_ms)
                        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, ?)
                        ON CONFLICT(platform, event_name, category) DO UPDATE SET
                            reserved_count = reserved_count + 1,
                            last_reserved = CURRENT_TIMESTAMP,
                            avg_reserve_time_ms = (avg_reserve_time_ms * reserved_count + ?) / (reserved_count + 1),
                            updated_at = CURRENT_TIMESTAMP
                    """, (platform, event_name, category, reserve_time_ms, reserve_time_ms))
                    
                    conn.commit()
                    logger.info(f"Recorded ticket reserved: {platform}/{event_name}/{category}")
                    
            except Exception as e:
                logger.error(f"Failed to record ticket reserved: {e}")
    
    def record_ticket_failed(self, platform: str, event_name: str, category: str, reason: str = ""):
        """Record failed ticket operation"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO ticket_stats (platform, event_name, category, failed_count, last_failed)
                        VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(platform, event_name, category) DO UPDATE SET
                            failed_count = failed_count + 1,
                            last_failed = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                    """, (platform, event_name, category))
                    
                    conn.commit()
                    logger.warning(f"Recorded ticket failure: {platform}/{event_name}/{category} - {reason}")
                    
            except Exception as e:
                logger.error(f"Failed to record ticket failure: {e}")
    
    def get_stats(self, platform: Optional[str] = None, event_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get statistics, optionally filtered by platform/event"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    query = """
                        SELECT *, 
                               CASE WHEN (reserved_count + failed_count) > 0 
                                    THEN CAST(reserved_count AS REAL) / (reserved_count + failed_count) * 100
                                    ELSE 0 END as success_rate
                        FROM ticket_stats
                        WHERE 1=1
                    """
                    params = []
                    
                    if platform:
                        query += " AND platform = ?"
                        params.append(platform)
                    
                    if event_name:
                        query += " AND event_name = ?"
                        params.append(event_name)
                    
                    query += " ORDER BY updated_at DESC"
                    
                    cursor.execute(query, params)
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(row))
                    
                    return results
                    
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                return []
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall summary statistics"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Overall totals
                    cursor.execute("""
                        SELECT 
                            SUM(found_count) as total_found,
                            SUM(reserved_count) as total_reserved,
                            SUM(failed_count) as total_failed,
                            COUNT(DISTINCT platform) as platforms_used,
                            COUNT(DISTINCT event_name) as events_tracked
                        FROM ticket_stats
                    """)
                    
                    totals = cursor.fetchone()
                    
                    # Platform breakdown
                    cursor.execute("""
                        SELECT 
                            platform,
                            SUM(found_count) as found,
                            SUM(reserved_count) as reserved,
                            SUM(failed_count) as failed,
                            AVG(avg_search_time_ms) as avg_search_ms,
                            AVG(avg_reserve_time_ms) as avg_reserve_ms
                        FROM ticket_stats
                        GROUP BY platform
                    """)
                    
                    platforms = []
                    for row in cursor.fetchall():
                        platforms.append({
                            "platform": row[0],
                            "found": row[1] or 0,
                            "reserved": row[2] or 0,
                            "failed": row[3] or 0,
                            "avg_search_ms": row[4] or 0,
                            "avg_reserve_ms": row[5] or 0,
                            "success_rate": (row[2] / (row[2] + row[3]) * 100) if (row[2] + row[3]) > 0 else 0
                        })
                    
                    # Recent activity
                    cursor.execute("""
                        SELECT * FROM ticket_stats
                        ORDER BY updated_at DESC
                        LIMIT 10
                    """)
                    
                    recent = []
                    for row in cursor.fetchall():
                        recent.append({
                            "platform": row[1],
                            "event": row[2],
                            "category": row[3],
                            "last_action": max(filter(None, [row[7], row[8], row[9]]), default="Never")
                        })
                    
                    return {
                        "total_found": totals[0] or 0,
                        "total_reserved": totals[1] or 0,
                        "total_failed": totals[2] or 0,
                        "platforms_used": totals[3] or 0,
                        "events_tracked": totals[4] or 0,
                        "overall_success_rate": (totals[1] / (totals[1] + totals[2]) * 100) if (totals[1] + totals[2]) > 0 else 0,
                        "platform_breakdown": platforms,
                        "recent_activity": recent
                    }
                    
            except Exception as e:
                logger.error(f"Failed to get summary: {e}")
                return {
                    "total_found": 0,
                    "total_reserved": 0,
                    "total_failed": 0,
                    "platforms_used": 0,
                    "events_tracked": 0,
                    "overall_success_rate": 0,
                    "platform_breakdown": [],
                    "recent_activity": []
                }
    
    def record_performance_metric(self, session_id: str, operation: str, duration_ms: float, 
                                success: bool, platform: Optional[str] = None):
        """Record performance metric"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO performance_metrics (session_id, operation, duration_ms, success, platform)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, operation, duration_ms, success, platform))
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Failed to record performance metric: {e}")
    
    def start_session(self, session_id: str):
        """Start a new tracking session"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO session_summary (session_id, start_time)
                        VALUES (?, CURRENT_TIMESTAMP)
                    """, (session_id,))
                    
                    conn.commit()
                    logger.info(f"Started statistics session: {session_id}")
                    
            except Exception as e:
                logger.error(f"Failed to start session: {e}")
    
    def end_session(self, session_id: str):
        """End tracking session and calculate summary"""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    # Calculate session metrics
                    cursor.execute("""
                        SELECT 
                            COUNT(CASE WHEN operation = 'search' THEN 1 END) as searches,
                            COUNT(CASE WHEN operation = 'reserve' AND success = 1 THEN 1 END) as reservations,
                            COUNT(CASE WHEN success = 0 THEN 1 END) as failures,
                            AVG(duration_ms) as avg_response
                        FROM performance_metrics
                        WHERE session_id = ?
                    """, (session_id,))
                    
                    metrics = cursor.fetchone()
                    
                    cursor.execute("""
                        UPDATE session_summary
                        SET end_time = CURRENT_TIMESTAMP,
                            total_searches = ?,
                            total_reservations = ?,
                            total_failures = ?,
                            avg_response_time_ms = ?
                        WHERE session_id = ?
                    """, (metrics[0] or 0, metrics[1] or 0, metrics[2] or 0, 
                         metrics[3] or 0, session_id))
                    
                    conn.commit()
                    logger.info(f"Ended statistics session: {session_id}")
                    
            except Exception as e:
                logger.error(f"Failed to end session: {e}")
    
    def export_stats(self, format: str = "json") -> str:
        """Export statistics in specified format"""
        stats = self.get_summary()
        
        if format == "json":
            return json.dumps(stats, indent=2, default=str)
        elif format == "csv":
            # Simple CSV export of platform breakdown
            lines = ["Platform,Found,Reserved,Failed,Success Rate"]
            for platform in stats["platform_breakdown"]:
                lines.append(f"{platform['platform']},{platform['found']},{platform['reserved']},"
                           f"{platform['failed']},{platform['success_rate']:.1f}%")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global instance
stats_manager = StatsManager()