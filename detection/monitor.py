# stealthmaster/detection/monitor.py
"""Advanced real-time detection monitoring system."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from collections import defaultdict
import json
import re

from playwright.async_api import Page, Response, Request, ConsoleMessage

logger = logging.getLogger(__name__)


class DetectionType(Enum):
    """Types of detection events."""
    
    CAPTCHA = "captcha"
    CLOUDFLARE = "cloudflare"
    RATE_LIMIT = "rate_limit"
    FINGERPRINT = "fingerprint"
    BEHAVIORAL = "behavioral"
    CDP_DETECTION = "cdp_detection"
    IP_BLOCK = "ip_block"
    SESSION_INVALID = "session_invalid"
    UNKNOWN = "unknown"


class MonitoringLevel(Enum):
    """Monitoring intensity levels."""
    
    LOW = 1      # Basic monitoring
    MEDIUM = 2   # Standard monitoring
    HIGH = 3     # Intensive monitoring
    PARANOID = 4 # Maximum monitoring


class DetectionEvent:
    """Represents a detection event."""
    
    def __init__(
        self,
        detection_type: DetectionType,
        confidence: float,
        indicators: List[str],
        url: str,
        timestamp: datetime,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize detection event."""
        self.detection_type = detection_type
        self.confidence = confidence
        self.indicators = indicators
        self.url = url
        self.timestamp = timestamp
        self.details = details or {}
        self.id = f"{detection_type.value}_{timestamp.timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.detection_type.value,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "url": self.url,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


class DetectionMonitor:
    """Real-time detection monitoring system."""
    
    def __init__(self):
        """Initialize detection monitor."""
        self._monitored_pages: Dict[str, Dict[str, Any]] = {}
        self._detection_events: List[DetectionEvent] = []
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # Detection patterns
        self._detection_patterns = self._load_detection_patterns()
        
        # Statistics
        self._stats = {
            "total_detections": 0,
            "detections_by_type": defaultdict(int),
            "detections_by_url": defaultdict(int),
            "false_positives": 0
        }
    
    def _load_detection_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load detection patterns."""
        return {
            DetectionType.CAPTCHA: [
                {"pattern": r"captcha", "confidence": 0.9, "flags": re.IGNORECASE},
                {"pattern": r"recaptcha", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"hcaptcha", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"funcaptcha", "confidence": 0.9, "flags": re.IGNORECASE},
                {"pattern": r"challenge-form", "confidence": 0.85, "flags": re.IGNORECASE},
                {"pattern": r"arkose", "confidence": 0.9, "flags": re.IGNORECASE},
            ],
            DetectionType.CLOUDFLARE: [
                {"pattern": r"cf-challenge", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"cloudflare", "confidence": 0.7, "flags": re.IGNORECASE},
                {"pattern": r"checking your browser", "confidence": 0.9, "flags": re.IGNORECASE},
                {"pattern": r"ray id", "confidence": 0.8, "flags": re.IGNORECASE},
                {"pattern": r"__cf_chl", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"cf_clearance", "confidence": 0.9, "flags": re.IGNORECASE},
            ],
            DetectionType.RATE_LIMIT: [
                {"pattern": r"rate limit", "confidence": 0.9, "flags": re.IGNORECASE},
                {"pattern": r"too many requests", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"429", "confidence": 0.85, "flags": 0},
                {"pattern": r"quota exceeded", "confidence": 0.9, "flags": re.IGNORECASE},
                {"pattern": r"throttle", "confidence": 0.8, "flags": re.IGNORECASE},
            ],
            DetectionType.FINGERPRINT: [
                {"pattern": r"suspicious activity", "confidence": 0.8, "flags": re.IGNORECASE},
                {"pattern": r"automated", "confidence": 0.7, "flags": re.IGNORECASE},
                {"pattern": r"bot detected", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"browser verification", "confidence": 0.85, "flags": re.IGNORECASE},
            ],
            DetectionType.CDP_DETECTION: [
                {"pattern": r"CDP.*detected", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"DevTools.*detected", "confidence": 0.9, "flags": re.IGNORECASE},
                {"pattern": r"automation.*detected", "confidence": 0.85, "flags": re.IGNORECASE},
                {"pattern": r"Runtime\.enable", "confidence": 0.95, "flags": 0},
            ],
            DetectionType.IP_BLOCK: [
                {"pattern": r"access denied", "confidence": 0.8, "flags": re.IGNORECASE},
                {"pattern": r"ip.*blocked", "confidence": 0.95, "flags": re.IGNORECASE},
                {"pattern": r"forbidden", "confidence": 0.7, "flags": re.IGNORECASE},
                {"pattern": r"403", "confidence": 0.6, "flags": 0},
            ]
        }
    
    async def start_monitoring(
        self,
        page: Page,
        level: MonitoringLevel = MonitoringLevel.HIGH,
        custom_patterns: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> None:
        """
        Start monitoring a page for detection events.
        
        Args:
            page: Page to monitor
            level: Monitoring intensity level
            custom_patterns: Additional detection patterns
        """
        page_id = str(id(page))
        
        if page_id in self._monitored_pages:
            logger.warning(f"Page {page_id} already being monitored")
            return
        
        # Store monitoring configuration
        self._monitored_pages[page_id] = {
            "page": page,
            "level": level,
            "started_at": datetime.now(),
            "events": [],
            "custom_patterns": custom_patterns or {}
        }
        
        # Set up event listeners
        await self._setup_listeners(page, level)
        
        # Start monitoring task
        task = asyncio.create_task(self._monitor_page(page_id))
        self._monitoring_tasks[page_id] = task
        
        logger.info(f"Started monitoring page {page_id} at level {level.name}")
    
    async def _setup_listeners(self, page: Page, level: MonitoringLevel) -> None:
        """Set up page event listeners."""
        # Response monitoring
        page.on("response", lambda response: asyncio.create_task(
            self._on_response(page, response)
        ))
        
        # Console monitoring (high level and above)
        if level.value >= MonitoringLevel.HIGH.value:
            page.on("console", lambda msg: asyncio.create_task(
                self._on_console(page, msg)
            ))
        
        # Request monitoring (paranoid level)
        if level == MonitoringLevel.PARANOID:
            page.on("request", lambda request: asyncio.create_task(
                self._on_request(page, request)
            ))
        
        # Dialog monitoring
        page.on("dialog", lambda dialog: asyncio.create_task(
            self._on_dialog(page, dialog)
        ))
        
        # Page error monitoring
        page.on("pageerror", lambda error: asyncio.create_task(
            self._on_page_error(page, error)
        ))
    
    async def _monitor_page(self, page_id: str) -> None:
        """Main monitoring loop for a page."""
        config = self._monitored_pages[page_id]
        page = config["page"]
        level = config["level"]
        
        while page_id in self._monitored_pages:
            try:
                # Check if page is still valid
                if page.is_closed():
                    break
                
                # Periodic content analysis
                if level.value >= MonitoringLevel.MEDIUM.value:
                    await self._analyze_page_content(page)
                
                # JavaScript detection checks (high level)
                if level.value >= MonitoringLevel.HIGH.value:
                    await self._check_js_detection(page)
                
                # Network analysis (paranoid level)
                if level == MonitoringLevel.PARANOID:
                    await self._analyze_network_patterns(page)
                
                # Wait before next check
                interval = self._get_check_interval(level)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error for page {page_id}: {e}")
                await asyncio.sleep(5)
    
    async def _on_response(self, page: Page, response: Response) -> None:
        """Handle response events."""
        try:
            # Check status codes
            if response.status == 429:
                await self._create_detection_event(
                    page,
                    DetectionType.RATE_LIMIT,
                    0.95,
                    ["HTTP 429 response"],
                    {"status_code": 429, "url": response.url}
                )
            elif response.status == 403:
                # Could be IP block or other restriction
                await self._analyze_403_response(page, response)
            
            # Check response headers
            headers = await response.headers()
            
            # Cloudflare detection
            if "cf-ray" in headers or "cf-cache-status" in headers:
                if response.status >= 400:
                    await self._create_detection_event(
                        page,
                        DetectionType.CLOUDFLARE,
                        0.8,
                        ["Cloudflare headers with error status"],
                        {"headers": dict(headers), "status": response.status}
                    )
            
            # Check for challenge URLs
            if "challenge" in response.url or "captcha" in response.url:
                await self._create_detection_event(
                    page,
                    DetectionType.CAPTCHA,
                    0.85,
                    ["Challenge URL detected"],
                    {"challenge_url": response.url}
                )
                
        except Exception as e:
            logger.debug(f"Response monitoring error: {e}")
    
    async def _on_console(self, page: Page, message: ConsoleMessage) -> None:
        """Handle console messages."""
        try:
            text = message.text
            
            # Check for CDP detection messages
            if "CDP" in text or "DevTools" in text or "Runtime.enable" in text:
                await self._create_detection_event(
                    page,
                    DetectionType.CDP_DETECTION,
                    0.9,
                    ["Console message indicates CDP detection"],
                    {"console_text": text, "type": message.type}
                )
            
            # Check for security warnings
            security_keywords = ["security", "violation", "blocked", "refused"]
            if any(keyword in text.lower() for keyword in security_keywords):
                logger.warning(f"Security console message: {text}")
                
        except Exception as e:
            logger.debug(f"Console monitoring error: {e}")
    
    async def _on_request(self, page: Page, request: Request) -> None:
        """Handle request events for paranoid monitoring."""
        # Track request patterns for behavioral analysis
        page_id = str(id(page))
        if page_id in self._monitored_pages:
            self._monitored_pages[page_id].setdefault("requests", []).append({
                "url": request.url,
                "method": request.method,
                "timestamp": datetime.now()
            })
    
    async def _on_dialog(self, page: Page, dialog: Any) -> None:
        """Handle dialog events."""
        try:
            message = dialog.message
            
            # Check for bot detection dialogs
            if any(word in message.lower() for word in ["bot", "automated", "suspicious"]):
                await self._create_detection_event(
                    page,
                    DetectionType.BEHAVIORAL,
                    0.85,
                    ["Suspicious dialog message"],
                    {"dialog_message": message}
                )
            
            # Auto-dismiss dialogs
            await dialog.dismiss()
            
        except Exception as e:
            logger.debug(f"Dialog handling error: {e}")
    
    async def _on_page_error(self, page: Page, error: str) -> None:
        """Handle page errors."""
        logger.error(f"Page error detected: {error}")
    
    async def _analyze_page_content(self, page: Page) -> None:
        """Analyze page content for detection indicators."""
        try:
            # Get page content
            content = await page.content()
            
            # Check all detection patterns
            for detection_type, patterns in self._detection_patterns.items():
                indicators = []
                max_confidence = 0.0
                
                for pattern_info in patterns:
                    pattern = pattern_info["pattern"]
                    confidence = pattern_info["confidence"]
                    flags = pattern_info.get("flags", 0)
                    
                    if re.search(pattern, content, flags):
                        indicators.append(pattern)
                        max_confidence = max(max_confidence, confidence)
                
                if indicators and max_confidence >= 0.7:
                    await self._create_detection_event(
                        page,
                        detection_type,
                        max_confidence,
                        indicators,
                        {"content_analysis": True}
                    )
                    
        except Exception as e:
            logger.debug(f"Content analysis error: {e}")
    
    async def _check_js_detection(self, page: Page) -> None:
        """Check for JavaScript-based detection."""
        try:
            # Check for common detection properties
            detection_signals = await page.evaluate("""
                () => {
                    const signals = [];
                    
                    // CDP detection
                    if (window.chrome && window.chrome.runtime && !window.chrome.runtime.id) {
                        signals.push('chrome.runtime.id missing');
                    }
                    
                    // WebDriver detection
                    if (navigator.webdriver) {
                        signals.push('navigator.webdriver is true');
                    }
                    
                    // Permissions detection
                    if (navigator.permissions && navigator.permissions.query) {
                        // Check if permissions behave unnaturally
                        const perms = ['geolocation', 'notifications'];
                        for (const perm of perms) {
                            try {
                                navigator.permissions.query({name: perm}).then(result => {
                                    if (result.state === 'granted' && !document.hasFocus()) {
                                        signals.push(`Suspicious ${perm} permission state`);
                                    }
                                });
                            } catch (e) {}
                        }
                    }
                    
                    // Canvas fingerprinting detection
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                        ctx.fillText('test', 2, 2);
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        // Check if canvas data is too uniform (sign of spoofing)
                        const uniqueValues = new Set(imageData.data);
                        if (uniqueValues.size < 10) {
                            signals.push('Canvas fingerprint anomaly detected');
                        }
                    }
                    
                    // Check for automation indicators
                    if (window.document.documentElement.getAttribute('webdriver')) {
                        signals.push('webdriver attribute detected');
                    }
                    
                    // Check for CDP domains
                    const cdpDomains = ['Runtime', 'Page', 'Network', 'DOM'];
                    for (const domain of cdpDomains) {
                        if (window[domain] && typeof window[domain].enable === 'function') {
                            signals.push(`CDP domain ${domain} exposed`);
                        }
                    }
                    
                    return signals;
                }
            """)
            
            if detection_signals.length > 0:
                await self._create_detection_event(
                    page,
                    DetectionType.FINGERPRINT,
                    min(0.6 + len(detection_signals) * 0.1, 0.95),
                    detection_signals,
                    {"js_detection": True}
                )
                
        except Exception as e:
            logger.debug(f"JS detection check error: {e}")
    
    async def _analyze_network_patterns(self, page: Page) -> None:
        """Analyze network patterns for suspicious behavior."""
        page_id = str(id(page))
        if page_id not in self._monitored_pages:
            return
        
        requests = self._monitored_pages[page_id].get("requests", [])
        if len(requests) < 10:
            return
        
        # Analyze request timing
        recent_requests = requests[-20:]
        timestamps = [r["timestamp"] for r in recent_requests]
        
        # Check for too regular intervals (bot-like)
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            
            # Low variance suggests automated behavior
            if variance < 0.1 and avg_interval < 2:
                await self._create_detection_event(
                    page,
                    DetectionType.BEHAVIORAL,
                    0.75,
                    ["Suspiciously regular request intervals"],
                    {"avg_interval": avg_interval, "variance": variance}
                )
    
    async def _analyze_403_response(self, page: Page, response: Response) -> None:
        """Analyze 403 responses to determine cause."""
        try:
            text = await response.text()
            
            # Check for IP block indicators
            ip_block_keywords = ["ip", "blocked", "banned", "blacklist", "forbidden"]
            if any(keyword in text.lower() for keyword in ip_block_keywords):
                await self._create_detection_event(
                    page,
                    DetectionType.IP_BLOCK,
                    0.85,
                    ["403 response with IP block indicators"],
                    {"response_text": text[:500]}
                )
            else:
                await self._create_detection_event(
                    page,
                    DetectionType.UNKNOWN,
                    0.7,
                    ["403 Forbidden response"],
                    {"url": response.url}
                )
                
        except Exception as e:
            logger.debug(f"403 analysis error: {e}")
    
    async def _create_detection_event(
        self,
        page: Page,
        detection_type: DetectionType,
        confidence: float,
        indicators: List[str],
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create and process a detection event."""
        # Avoid duplicate events
        page_id = str(id(page))
        recent_events = self._monitored_pages.get(page_id, {}).get("events", [])
        
        # Check if similar event was recently created
        now = datetime.now()
        for event in recent_events[-5:]:
            if (event.detection_type == detection_type and
                (now - event.timestamp).total_seconds() < 5):
                return
        
        # Create event
        event = DetectionEvent(
            detection_type=detection_type,
            confidence=confidence,
            indicators=indicators,
            url=page.url,
            timestamp=now,
            details=details
        )
        
        # Store event
        self._detection_events.append(event)
        if page_id in self._monitored_pages:
            self._monitored_pages[page_id]["events"].append(event)
        
        # Update statistics
        self._stats["total_detections"] += 1
        self._stats["detections_by_type"][detection_type.value] += 1
        self._stats["detections_by_url"][page.url] += 1
        
        # Notify callbacks
        await self._notify_callbacks(event)
        
        logger.warning(
            f"Detection event: {detection_type.value} "
            f"(confidence: {confidence:.2f}) on {page.url}"
        )
    
    async def _notify_callbacks(self, event: DetectionEvent) -> None:
        """Notify registered callbacks of detection event."""
        # Type-specific callbacks
        for callback in self._callbacks.get(event.detection_type.value, []):
            try:
                await callback(event) if asyncio.iscoroutinefunction(callback) else callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # Global callbacks
        for callback in self._callbacks.get("*", []):
            try:
                await callback(event) if asyncio.iscoroutinefunction(callback) else callback(event)
            except Exception as e:
                logger.error(f"Global callback error: {e}")
    
    def register_callback(
        self,
        detection_type: Optional[DetectionType] = None,
        callback: Callable = None
    ) -> None:
        """
        Register a callback for detection events.
        
        Args:
            detection_type: Type to monitor, or None for all
            callback: Function to call on detection
        """
        key = detection_type.value if detection_type else "*"
        self._callbacks[key].append(callback)
    
    async def force_check(self, page: Page) -> Dict[str, Any]:
        """
        Force an immediate detection check.
        
        Args:
            page: Page to check
            
        Returns:
            Detection results
        """
        await self._analyze_page_content(page)
        await self._check_js_detection(page)
        
        # Get recent events for this page
        page_id = str(id(page))
        events = self._monitored_pages.get(page_id, {}).get("events", [])
        
        # Find most recent high-confidence detection
        recent_detection = None
        for event in reversed(events[-10:]):
            if event.confidence >= 0.7:
                recent_detection = event
                break
        
        if recent_detection:
            return {
                "detected": True,
                "type": recent_detection.detection_type.value,
                "confidence": recent_detection.confidence,
                "indicators": recent_detection.indicators,
                "details": recent_detection.details
            }
        
        return {
            "detected": False,
            "type": None,
            "confidence": 0.0,
            "indicators": []
        }
    
    async def stop_monitoring(self, page: Page) -> None:
        """Stop monitoring a page."""
        page_id = str(id(page))
        
        # Cancel monitoring task
        if page_id in self._monitoring_tasks:
            task = self._monitoring_tasks[page_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._monitoring_tasks[page_id]
        
        # Remove from monitored pages
        if page_id in self._monitored_pages:
            del self._monitored_pages[page_id]
        
        logger.info(f"Stopped monitoring page {page_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "total_detections": self._stats["total_detections"],
            "detections_by_type": dict(self._stats["detections_by_type"]),
            "detections_by_url": dict(self._stats["detections_by_url"]),
            "false_positives": self._stats["false_positives"],
            "active_monitors": len(self._monitored_pages),
            "total_events": len(self._detection_events)
        }
    
    def get_recent_events(
        self,
        limit: int = 10,
        detection_type: Optional[DetectionType] = None
    ) -> List[DetectionEvent]:
        """Get recent detection events."""
        events = self._detection_events
        
        if detection_type:
            events = [e for e in events if e.detection_type == detection_type]
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def clear_events(self) -> None:
        """Clear stored detection events."""
        self._detection_events.clear()
        for page_data in self._monitored_pages.values():
            page_data["events"].clear()
    
    def _get_check_interval(self, level: MonitoringLevel) -> float:
        """Get check interval based on monitoring level."""
        intervals = {
            MonitoringLevel.LOW: 10.0,
            MonitoringLevel.MEDIUM: 5.0,
            MonitoringLevel.HIGH: 2.0,
            MonitoringLevel.PARANOID: 1.0
        }
        return intervals.get(level, 5.0)