"""
Purchase Monitor - Real-time insights into ticket availability and purchases
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TicketEvent:
    """Represents a ticket-related event"""
    timestamp: datetime
    platform: str
    event_type: str  # 'found', 'sold', 'price_change', 'new_listing'
    details: Dict[str, Any]
    section: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None


@dataclass
class PlatformStats:
    """Statistics for a single platform"""
    platform: str
    total_scans: int = 0
    tickets_found: int = 0
    tickets_sold: int = 0
    avg_price: float = 0.0
    last_activity: Optional[datetime] = None
    active_listings: List[Dict[str, Any]] = field(default_factory=list)
    recent_sales: List[TicketEvent] = field(default_factory=list)


class PurchaseMonitor:
    """Monitors ticket purchases and provides real-time insights"""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("logs/purchase_insights")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.platform_stats: Dict[str, PlatformStats] = {}
        self.events: List[TicketEvent] = []
        self.session_start = datetime.now()
        
        # Price tracking
        self.price_history: Dict[str, List[tuple[datetime, float]]] = {}
        
        # Alert thresholds
        self.alert_config = {
            'price_drop_threshold': 0.1,  # 10% drop
            'high_activity_threshold': 5,  # 5 tickets in 1 minute
            'target_sections': [],
            'max_price_alert': None
        }
        
    async def log_event(self, event: TicketEvent):
        """Log a ticket event"""
        self.events.append(event)
        
        # Update platform stats
        if event.platform not in self.platform_stats:
            self.platform_stats[event.platform] = PlatformStats(platform=event.platform)
            
        stats = self.platform_stats[event.platform]
        stats.last_activity = event.timestamp
        
        if event.event_type == 'found':
            stats.tickets_found += 1
            self._update_active_listings(stats, event)
        elif event.event_type == 'sold':
            stats.tickets_sold += 1
            stats.recent_sales.append(event)
            stats.recent_sales = stats.recent_sales[-10:]  # Keep last 10
            self._remove_sold_listing(stats, event)
            
        # Track price history
        if event.price and event.section:
            key = f"{event.platform}:{event.section}"
            if key not in self.price_history:
                self.price_history[key] = []
            self.price_history[key].append((event.timestamp, event.price))
            
        # Check for alerts
        await self._check_alerts(event)
        
        # Save to file
        await self._save_event(event)
        
    def _update_active_listings(self, stats: PlatformStats, event: TicketEvent):
        """Update active listings"""
        listing = {
            'id': event.details.get('id', f"{event.section}_{event.price}"),
            'section': event.section,
            'price': event.price,
            'quantity': event.quantity,
            'first_seen': event.timestamp,
            'last_seen': event.timestamp
        }
        
        # Check if listing already exists
        existing = next((l for l in stats.active_listings 
                        if l['id'] == listing['id']), None)
        
        if existing:
            existing['last_seen'] = event.timestamp
        else:
            stats.active_listings.append(listing)
            
    def _remove_sold_listing(self, stats: PlatformStats, event: TicketEvent):
        """Remove sold listing"""
        listing_id = event.details.get('id')
        if listing_id:
            stats.active_listings = [l for l in stats.active_listings 
                                   if l['id'] != listing_id]
                                   
    async def _check_alerts(self, event: TicketEvent):
        """Check if event triggers any alerts"""
        alerts = []
        
        # Price drop alert
        if event.price and event.section:
            price_drop = self._check_price_drop(event.platform, event.section, event.price)
            if price_drop:
                alerts.append(f"Price DROP: {event.section} now €{event.price} "
                            f"(down {price_drop:.1%})")
                
        # Target section alert
        if (event.section and 
            any(target.lower() in event.section.lower() 
                for target in self.alert_config['target_sections'])):
            alerts.append(f"Target section available: {event.section} - €{event.price}")
            
        # Max price alert
        if (event.price and 
            self.alert_config['max_price_alert'] and 
            event.price <= self.alert_config['max_price_alert']):
            alerts.append(f"Ticket under target price: {event.section} - €{event.price}")
            
        # High activity alert
        recent_events = [e for e in self.events[-20:] 
                        if e.platform == event.platform and
                        (event.timestamp - e.timestamp).seconds < 60]
        if len(recent_events) >= self.alert_config['high_activity_threshold']:
            alerts.append(f"HIGH ACTIVITY on {event.platform}: "
                        f"{len(recent_events)} events in last minute")
            
        # Log alerts
        for alert in alerts:
            logger.warning(f"🚨 ALERT: {alert}")
            
    def _check_price_drop(self, platform: str, section: str, current_price: float) -> Optional[float]:
        """Check if price has dropped significantly"""
        key = f"{platform}:{section}"
        history = self.price_history.get(key, [])
        
        if len(history) < 2:
            return None
            
        # Get previous prices (excluding current)
        previous_prices = [p for t, p in history[:-1]]
        if not previous_prices:
            return None
            
        avg_previous = sum(previous_prices) / len(previous_prices)
        drop_percent = (avg_previous - current_price) / avg_previous
        
        if drop_percent >= self.alert_config['price_drop_threshold']:
            return drop_percent
            
        return None
        
    async def _save_event(self, event: TicketEvent):
        """Save event to log file"""
        log_file = self.log_dir / f"events_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        event_data = {
            'timestamp': event.timestamp.isoformat(),
            'platform': event.platform,
            'event_type': event.event_type,
            'section': event.section,
            'price': event.price,
            'quantity': event.quantity,
            'details': event.details
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(event_data) + '\n')
            
    def get_summary(self) -> Dict[str, Any]:
        """Get current monitoring summary"""
        runtime = (datetime.now() - self.session_start).seconds
        
        summary = {
            'session_start': self.session_start.isoformat(),
            'runtime_seconds': runtime,
            'total_events': len(self.events),
            'platforms': {}
        }
        
        for platform, stats in self.platform_stats.items():
            # Calculate average price from active listings
            active_prices = [l['price'] for l in stats.active_listings if l['price']]
            avg_price = sum(active_prices) / len(active_prices) if active_prices else 0
            
            summary['platforms'][platform] = {
                'total_scans': stats.total_scans,
                'tickets_found': stats.tickets_found,
                'tickets_sold': stats.tickets_sold,
                'active_listings': len(stats.active_listings),
                'avg_active_price': round(avg_price, 2),
                'last_activity': stats.last_activity.isoformat() if stats.last_activity else None,
                'recent_sales': [
                    {
                        'time': sale.timestamp.isoformat(),
                        'section': sale.section,
                        'price': sale.price,
                        'quantity': sale.quantity
                    }
                    for sale in stats.recent_sales[-5:]  # Last 5 sales
                ]
            }
            
        return summary
        
    def get_insights(self) -> List[str]:
        """Get actionable insights from monitoring data"""
        insights = []
        
        # Platform activity
        for platform, stats in self.platform_stats.items():
            if stats.last_activity:
                mins_since = (datetime.now() - stats.last_activity).seconds / 60
                if mins_since < 5:
                    insights.append(f"✅ {platform} is ACTIVE (last seen {mins_since:.1f}m ago)")
                elif mins_since < 30:
                    insights.append(f"⚠️ {platform} slow activity ({mins_since:.1f}m since last)")
                else:
                    insights.append(f"❌ {platform} appears INACTIVE ({mins_since:.1f}m)")
                    
        # Price trends
        for key, history in self.price_history.items():
            if len(history) >= 3:
                platform, section = key.split(':', 1)
                prices = [p for _, p in history[-5:]]  # Last 5 prices
                
                if prices[-1] < min(prices[:-1]):
                    insights.append(f"📉 {section} prices DROPPING on {platform}")
                elif prices[-1] > max(prices[:-1]):
                    insights.append(f"📈 {section} prices RISING on {platform}")
                    
        # Availability patterns
        total_active = sum(len(s.active_listings) for s in self.platform_stats.values())
        total_sold = sum(s.tickets_sold for s in self.platform_stats.values())
        
        if total_active > 0:
            insights.append(f"🎫 {total_active} tickets currently available")
        if total_sold > 0:
            insights.append(f"💰 {total_sold} tickets sold this session")
            
        # Recommendations
        if not insights:
            insights.append("🔍 No significant activity detected yet")
            
        return insights
        
    async def display_dashboard(self):
        """Display a text-based dashboard"""
        summary = self.get_summary()
        insights = self.get_insights()
        
        print("\n" + "="*60)
        print("🎸 TICKET PURCHASE MONITOR DASHBOARD")
        print("="*60)
        print(f"Session: {summary['runtime_seconds']//60}m {summary['runtime_seconds']%60}s")
        print(f"Events: {summary['total_events']}")
        print("\nPLATFORM STATUS:")
        
        for platform, data in summary['platforms'].items():
            print(f"\n{platform.upper()}:")
            print(f"  Scans: {data['total_scans']} | Found: {data['tickets_found']} | "
                  f"Sold: {data['tickets_sold']} | Active: {data['active_listings']}")
            if data['avg_active_price'] > 0:
                print(f"  Avg Price: €{data['avg_active_price']}")
            if data['recent_sales']:
                print("  Recent Sales:")
                for sale in data['recent_sales']:
                    print(f"    - {sale['section']}: €{sale['price']} x{sale['quantity']}")
                    
        print("\nINSIGHTS:")
        for insight in insights:
            print(f"  {insight}")
            
        print("="*60)


class PurchaseTracker:
    """Integration class for tracking purchases in the main system"""
    
    def __init__(self):
        self.monitor = PurchaseMonitor()
        self.last_listings: Dict[str, set] = {}
        
    async def track_opportunities(self, platform: str, opportunities: List[Any]):
        """Track ticket opportunities and detect changes"""
        
        # Update scan count
        if platform in self.monitor.platform_stats:
            self.monitor.platform_stats[platform].total_scans += 1
        else:
            self.monitor.platform_stats[platform] = PlatformStats(platform=platform)
            self.monitor.platform_stats[platform].total_scans = 1
            
        # Convert opportunities to comparable format
        current_listings = set()
        for opp in opportunities:
            listing_id = f"{opp.section}_{opp.price}_{opp.quantity}"
            current_listings.add(listing_id)
            
            # Track as found event
            event = TicketEvent(
                timestamp=datetime.now(),
                platform=platform,
                event_type='found',
                section=opp.section,
                price=opp.price,
                quantity=opp.quantity,
                details={'id': listing_id, 'url': opp.url}
            )
            await self.monitor.log_event(event)
            
        # Detect sold tickets (were there before, not anymore)
        if platform in self.last_listings:
            sold_listings = self.last_listings[platform] - current_listings
            
            for listing_id in sold_listings:
                # Parse listing info
                parts = listing_id.split('_')
                if len(parts) >= 3:
                    section = parts[0]
                    price = float(parts[1]) if parts[1].replace('.', '').isdigit() else 0
                    quantity = int(parts[2]) if parts[2].isdigit() else 1
                    
                    event = TicketEvent(
                        timestamp=datetime.now(),
                        platform=platform,
                        event_type='sold',
                        section=section,
                        price=price,
                        quantity=quantity,
                        details={'id': listing_id}
                    )
                    await self.monitor.log_event(event)
                    
        # Update last listings
        self.last_listings[platform] = current_listings
        
    def get_insights(self) -> List[str]:
        """Get current insights"""
        return self.monitor.get_insights()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        return self.monitor.get_summary()
        
    async def show_dashboard(self):
        """Display the dashboard"""
        await self.monitor.display_dashboard()