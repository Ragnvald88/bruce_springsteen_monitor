"""
Ticket History Tracker with Category Detection
Real-time and persistent tracking of all ticket detections
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import aiofiles
from tinydb import TinyDB, Query

from ..utils.logging import get_logger

logger = get_logger(__name__)


class TicketHistoryTracker:
    """Advanced ticket tracking with categorization and analytics"""
    
    def __init__(self, db_path: str = "data/ticket_history.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.history_db = TinyDB(str(self.db_path))
        self.session_stats = defaultdict(lambda: defaultdict(int))
        self.current_session_id = None
        
        # Category patterns for Italian ticket platforms
        self.category_patterns = {
            'prato_a': [
                'PRATO A', 'SETTORE A', 'TRIBUNA A', 'ANELLO A',
                'PRIMO ANELLO', 'FIRST RING', 'SECTOR A'
            ],
            'prato_b': [
                'PRATO B', 'SETTORE B', 'TRIBUNA B', 'ANELLO B',
                'SECONDO ANELLO', 'SECOND RING', 'SECTOR B'
            ],
            'vip': [
                'VIP', 'GOLD', 'PREMIUM', 'HOSPITALITY', 'PLATINUM',
                'EXECUTIVE', 'BUSINESS', 'LOUNGE'
            ],
            'pit': [
                'PIT', 'PARTERRE', 'POSTO IN PIEDI', 'STANDING',
                'FRONT STAGE', 'GOLDEN CIRCLE'
            ],
            'numbered': [
                'NUMERATO', 'NUMBERED', 'POSTO NUMERATO', 'ASSIGNED SEAT',
                'TRIBUNA NUMERATA'
            ],
            'general': [
                'GENERALE', 'GENERAL', 'STANDARD', 'NORMALE'
            ]
        }
        
        # Real-time update callbacks
        self.update_callbacks = []
    
    def set_session_id(self, session_id: str):
        """Set current session ID for tracking"""
        self.current_session_id = session_id
        logger.info(f"History tracker session started: {session_id}")
    
    async def record_detection(self, platform: str, event: str, page_content: str, 
                             confidence: float, ticket_details: Dict[str, Any] = None):
        """Record a ticket detection with automatic categorization"""
        
        # Categorize ticket
        category = self._categorize_ticket(page_content)
        
        # Extract additional details if available
        price_range = self._extract_price_range(page_content)
        availability = self._extract_availability(page_content)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform.lower(),
            'event': event,
            'category': category,
            'confidence': round(confidence, 3),
            'session_id': self.current_session_id,
            'price_range': price_range,
            'availability': availability,
            'details': ticket_details or {}
        }
        
        # Save to database
        self.history_db.insert(record)
        
        # Update session stats
        self.session_stats[platform][category] += 1
        
        # Log detection
        logger.info(f"Recorded {category} ticket on {platform} (confidence: {confidence:.1%})")
        
        # Trigger real-time updates
        await self._notify_updates()
    
    def _categorize_ticket(self, content: str) -> str:
        """Determine ticket category from page content"""
        content_upper = content.upper()
        
        # Check each category pattern
        for category, patterns in self.category_patterns.items():
            if any(pattern in content_upper for pattern in patterns):
                return category
        
        # Default to general if no specific category found
        return 'general'
    
    def _extract_price_range(self, content: str) -> Optional[Dict[str, float]]:
        """Extract price information from content"""
        import re
        
        # Look for price patterns
        price_pattern = r'€\s*(\d+(?:[.,]\d{2})?)'
        prices = re.findall(price_pattern, content)
        
        if prices:
            # Convert to floats
            float_prices = []
            for price in prices:
                try:
                    # Replace comma with dot for European format
                    price_float = float(price.replace(',', '.'))
                    if 10 <= price_float <= 5000:  # Reasonable ticket price range
                        float_prices.append(price_float)
                except:
                    continue
            
            if float_prices:
                return {
                    'min': min(float_prices),
                    'max': max(float_prices),
                    'avg': sum(float_prices) / len(float_prices)
                }
        
        return None
    
    def _extract_availability(self, content: str) -> str:
        """Determine availability status"""
        content_lower = content.lower()
        
        # Check for availability indicators
        if any(term in content_lower for term in ['sold out', 'esaurito', 'terminato']):
            return 'sold_out'
        elif any(term in content_lower for term in ['ultimi', 'last', 'pochi']):
            return 'limited'
        elif any(term in content_lower for term in ['disponibile', 'available']):
            return 'available'
        
        return 'unknown'
    
    def get_formatted_history(self) -> Dict[str, Any]:
        """Get history formatted for display"""
        history = {}
        
        for platform in ['fansale', 'ticketmaster', 'vivaticket']:
            platform_data = self.history_db.search(Query().platform == platform)
            
            # Calculate category breakdown
            category_counts = defaultdict(int)
            confidence_sum = 0
            price_data = []
            
            for record in platform_data:
                category_counts[record['category']] += 1
                confidence_sum += record['confidence']
                
                if record.get('price_range'):
                    price_data.append(record['price_range']['avg'])
            
            history[platform] = {
                'total_detections': len(platform_data),
                'prato_a': category_counts.get('prato_a', 0),
                'prato_b': category_counts.get('prato_b', 0),
                'vip': category_counts.get('vip', 0),
                'pit': category_counts.get('pit', 0),
                'numbered': category_counts.get('numbered', 0),
                'general': category_counts.get('general', 0),
                'avg_confidence': confidence_sum / len(platform_data) if platform_data else 0,
                'avg_price': sum(price_data) / len(price_data) if price_data else 0,
                'last_detection': platform_data[-1]['timestamp'] if platform_data else None
            }
        
        # Add session totals
        history['session_totals'] = dict(self.session_stats)
        
        return history
    
    def get_category_trends(self, platform: str, hours: int = 24) -> Dict[str, List[int]]:
        """Get hourly category trends for a platform"""
        from datetime import timedelta
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        recent_data = self.history_db.search(
            (Query().platform == platform) & 
            (Query().timestamp >= cutoff_time)
        )
        
        # Group by hour and category
        hourly_data = defaultdict(lambda: defaultdict(int))
        
        for record in recent_data:
            timestamp = datetime.fromisoformat(record['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            category = record['category']
            hourly_data[hour_key][category] += 1
        
        # Format for display
        trends = defaultdict(list)
        sorted_hours = sorted(hourly_data.keys())
        
        for hour in sorted_hours:
            for category in self.category_patterns.keys():
                trends[category].append(hourly_data[hour].get(category, 0))
        
        return dict(trends)
    
    def get_detection_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive analytics"""
        all_records = self.history_db.all()
        
        if not all_records:
            return {'message': 'No detection history available'}
        
        analytics = {
            'total_detections': len(all_records),
            'platforms': {},
            'categories': defaultdict(int),
            'time_analysis': {},
            'price_analysis': {},
            'recommendations': []
        }
        
        # Platform breakdown
        for platform in ['fansale', 'ticketmaster', 'vivaticket']:
            platform_records = [r for r in all_records if r['platform'] == platform]
            analytics['platforms'][platform] = {
                'count': len(platform_records),
                'percentage': (len(platform_records) / len(all_records)) * 100
            }
        
        # Category analysis
        for record in all_records:
            analytics['categories'][record['category']] += 1
        
        # Time-based patterns
        hour_counts = defaultdict(int)
        for record in all_records:
            hour = datetime.fromisoformat(record['timestamp']).hour
            hour_counts[hour] += 1
        
        # Find peak hours
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        analytics['time_analysis']['peak_hours'] = [h[0] for h in peak_hours]
        
        # Price analysis
        all_prices = []
        for record in all_records:
            if record.get('price_range') and record['price_range'].get('avg'):
                all_prices.append(record['price_range']['avg'])
        
        if all_prices:
            analytics['price_analysis'] = {
                'average': sum(all_prices) / len(all_prices),
                'min': min(all_prices),
                'max': max(all_prices)
            }
        
        # Generate recommendations
        if analytics['categories']['prato_a'] > analytics['categories']['prato_b']:
            analytics['recommendations'].append("Prato A tickets appear more frequently - focus monitoring here")
        
        if analytics['time_analysis']['peak_hours']:
            peak_str = ', '.join([f"{h}:00" for h in analytics['time_analysis']['peak_hours']])
            analytics['recommendations'].append(f"Increase monitoring during peak hours: {peak_str}")
        
        return analytics
    
    def add_update_callback(self, callback):
        """Add callback for real-time updates"""
        self.update_callbacks.append(callback)
    
    async def _notify_updates(self):
        """Notify all registered callbacks of updates"""
        for callback in self.update_callbacks:
            try:
                await callback(self.get_formatted_history())
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    def export_history(self, filepath: str = None) -> str:
        """Export history to JSON file"""
        if not filepath:
            filepath = f"ticket_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'records': self.history_db.all(),
            'analytics': self.get_detection_analytics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported history to {filepath}")
        return filepath


# Global instance
history_tracker = TicketHistoryTracker()
