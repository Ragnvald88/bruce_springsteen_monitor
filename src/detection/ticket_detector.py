"""
Advanced Ticket Detection System
Platform-specific detection with ML-based verification
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionResult:
    """Result of ticket detection"""
    confidence: float
    has_tickets: bool
    found_elements: Dict[str, int]
    details: Optional[Dict[str, Any]] = None


class PlatformDetectionRules(ABC):
    """Base class for platform-specific detection rules"""
    
    @abstractmethod
    async def check_dom_structure(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Check DOM structure for tickets"""
        pass
    
    @abstractmethod
    async def analyze_content(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Analyze page content for ticket indicators"""
        pass
    
    async def check_interactive_elements(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Check for interactive ticket purchase elements"""
        return {'confidence': 0.5, 'found': False}
    
    async def check_availability(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Check ticket availability status"""
        return {'confidence': 0.5, 'available': True}


class FansaleDetectionRules(PlatformDetectionRules):
    """Fansale-specific detection rules"""
    
    async def check_dom_structure(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Check Fansale DOM structure for tickets"""
        
        # Fansale-specific selectors (updated for 2025)
        selectors = {
            'ticket_containers': [
                '.ticket-listing-item',
                '.offer-row',
                '[data-test="ticket-offer"]',
                '.listing-container .offer',
                'div[class*="TicketOffer"]',
                '.event-tickets-list',
                '.tickets-available'
            ],
            'price_elements': [
                '.ticket-price',
                '.offer-price',
                'span[class*="price"]',
                '[data-test="offer-price"]',
                '.price-tag',
                '.prezzo'
            ],
            'availability': [
                '.available-tickets',
                '.tickets-left',
                'button[class*="buy"]',
                'a[href*="/checkout"]',
                '.add-to-cart',
                '[data-action="add-to-basket"]'
            ]
        }
        
        found_elements = {}
        confidence = 0
        
        for element_type, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    if hasattr(page, "query_selector_all"):
                        elements = await page.query_selector_all(selector)
                        if elements:
                            found_elements[element_type] = len(elements)
                            confidence += 0.3
                            break
                    elif hasattr(page, "find_elements_by_css_selector"):
                        elements = page.find_elements_by_css_selector(selector)
                        if elements:
                            found_elements[element_type] = len(elements)
                            confidence += 0.3
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
        
        return {
            'found_elements': found_elements,
            'confidence': min(confidence, 1.0),
            'has_tickets': len(found_elements) >= 2
        }
    
    async def analyze_content(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Analyze page content for ticket indicators"""
        
        if not content:
            try:
                content = await page.content() if hasattr(page, 'content') else page.page_source
            except:
                content = ""
        
        # Fansale-specific keywords (Italian + English)
        positive_indicators = {
            'high_confidence': [
                'acquista ora', 'buy now',
                'aggiungi al carrello', 'add to cart',
                'disponibile', 'available',
                'seleziona biglietti', 'select tickets',
                'procedi all\'acquisto', 'proceed to checkout',
                'biglietti disponibili', 'tickets available'
            ],
            'medium_confidence': [
                'prezzo', 'price',
                'settore', 'sector', 
                'fila', 'row',
                'posto', 'seat',
                'quantità', 'quantity',
                'tipologia', 'type'
            ]
        }
        
        negative_indicators = [
            'sold out', 'esaurito',
            'non disponibile', 'not available',
            'terminato', 'finished',
            'coming soon', 'prossimamente',
            'waitlist', 'lista d\'attesa'
        ]
        
        # Calculate confidence based on keyword presence
        confidence = 0
        found_keywords = []
        
        content_lower = content.lower()
        
        # Check positive indicators
        for conf_level, keywords in positive_indicators.items():
            weight = 0.4 if conf_level == 'high_confidence' else 0.2
            for keyword in keywords:
                if keyword in content_lower:
                    confidence += weight
                    found_keywords.append(keyword)
        
        # Check negative indicators (reduce confidence)
        for keyword in negative_indicators:
            if keyword in content_lower:
                confidence -= 0.5
        
        return {
            'confidence': max(0, min(confidence, 1.0)),
            'found_keywords': found_keywords,
            'has_negative_indicators': any(neg in content_lower for neg in negative_indicators)
        }


class TicketmasterDetectionRules(PlatformDetectionRules):
    """Ticketmaster-specific detection rules"""
    
    async def check_dom_structure(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Check Ticketmaster DOM structure for tickets"""
        
        selectors = {
            'ticket_containers': [
                '.ticket-listing',
                '.event-ticket',
                '[data-event-ticketlist]',
                '.quick-picks',
                '.ticket-selection',
                '[data-testid="ticket-shelf"]'
            ],
            'price_elements': [
                '.price-range',
                '.ticket-price',
                '[data-testid="offer-price"]',
                '.PriceDisplay'
            ],
            'availability': [
                'button[aria-label*="tickets"]',
                '.buy-button',
                '[data-testid="buy-button"]',
                'a[href*="/purchase"]'
            ]
        }
        
        found_elements = {}
        confidence = 0
        
        for element_type, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    if hasattr(page, "query_selector_all"):
                        elements = await page.query_selector_all(selector)
                        if elements:
                            found_elements[element_type] = len(elements)
                            confidence += 0.35
                            break
                except:
                    pass
        
        return {
            'found_elements': found_elements,
            'confidence': min(confidence, 1.0),
            'has_tickets': len(found_elements) >= 2
        }
    
    async def analyze_content(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Analyze Ticketmaster page content"""
        
        if not content:
            try:
                content = await page.content() if hasattr(page, 'content') else page.page_source
            except:
                content = ""
        
        positive_indicators = {
            'high_confidence': [
                'find tickets', 'get tickets',
                'see tickets', 'buy tickets',
                'available now', 'on sale'
            ],
            'medium_confidence': [
                'price range', 'seat map',
                'section', 'row'
            ]
        }
        
        negative_indicators = [
            'sold out', 'no tickets available',
            'check back later', 'currently unavailable'
        ]
        
        confidence = 0
        content_lower = content.lower()
        
        # Check indicators
        for conf_level, keywords in positive_indicators.items():
            weight = 0.4 if conf_level == 'high_confidence' else 0.2
            for keyword in keywords:
                if keyword in content_lower:
                    confidence += weight
        
        # Check negative
        for keyword in negative_indicators:
            if keyword in content_lower:
                confidence -= 0.6
        
        return {
            'confidence': max(0, min(confidence, 1.0)),
            'has_negative_indicators': any(neg in content_lower for neg in negative_indicators)
        }


class VivaticketDetectionRules(PlatformDetectionRules):
    """Vivaticket-specific detection rules"""
    
    async def check_dom_structure(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Check Vivaticket DOM structure"""
        
        selectors = {
            'ticket_containers': [
                '.ticket-available',
                '.ticket-row',
                '.biglietto-disponibile',
                '.event-tickets'
            ],
            'price_elements': [
                '.ticket-price',
                '.prezzo-biglietto'
            ],
            'availability': [
                '.buy-ticket-button',
                'button[class*="acquista"]'
            ]
        }
        
        found_elements = {}
        confidence = 0
        
        for element_type, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    if hasattr(page, "query_selector_all"):
                        elements = await page.query_selector_all(selector)
                        if elements:
                            found_elements[element_type] = len(elements)
                            confidence += 0.35
                            break
                except:
                    pass
        
        return {
            'found_elements': found_elements,
            'confidence': min(confidence, 1.0),
            'has_tickets': len(found_elements) >= 2
        }
    
    async def analyze_content(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Analyze Vivaticket page content"""
        
        if not content:
            try:
                content = await page.content() if hasattr(page, 'content') else page.page_source
            except:
                content = ""
        
        positive_indicators = [
            'biglietti disponibili', 'acquista',
            'compra ora', 'disponibile'
        ]
        
        negative_indicators = [
            'esaurito', 'non disponibile',
            'sold out'
        ]
        
        confidence = 0
        content_lower = content.lower()
        
        for keyword in positive_indicators:
            if keyword in content_lower:
                confidence += 0.3
        
        for keyword in negative_indicators:
            if keyword in content_lower:
                confidence -= 0.6
        
        return {
            'confidence': max(0, min(confidence, 1.0)),
            'has_negative_indicators': any(neg in content_lower for neg in negative_indicators)
        }


class TicketDetector:
    """
    Sophisticated ticket detection system with platform-specific rules
    """
    
    def __init__(self):
        self.platform_rules = {
            'fansale': FansaleDetectionRules(),
            'ticketmaster': TicketmasterDetectionRules(),
            'vivaticket': VivaticketDetectionRules()
        }
        
        # Detection confidence thresholds
        self.confidence_threshold = 0.7
        
    async def detect_tickets(self, page: Any, platform: str, content: str = None) -> Dict[str, Any]:
        """
        Detect tickets with platform-specific rules
        Returns detection result with confidence score
        """
        
        # Get platform-specific rules
        rules = self.platform_rules.get(platform.lower())
        if not rules:
            logger.warning(f"No specific rules for platform {platform}, using generic detection")
            return await self._generic_detection(page, content)
        
        # Multi-stage detection
        detection_stages = [
            ('dom_structure', rules.check_dom_structure),
            ('content_analysis', rules.analyze_content),
            ('interactive_elements', rules.check_interactive_elements),
            ('availability_indicators', rules.check_availability)
        ]
        
        results = {}
        total_confidence = 0
        stage_count = 0
        
        for stage_name, stage_func in detection_stages:
            try:
                stage_result = await stage_func(page, content)
                results[stage_name] = stage_result
                
                # Weight different stages differently
                weight = 1.0
                if stage_name == 'dom_structure':
                    weight = 1.5  # DOM structure is most reliable
                elif stage_name == 'content_analysis':
                    weight = 1.2
                
                total_confidence += stage_result.get('confidence', 0) * weight
                stage_count += weight
                
            except Exception as e:
                logger.error(f"Detection stage {stage_name} failed: {e}")
                results[stage_name] = {'error': str(e), 'confidence': 0}
        
        # Calculate overall confidence
        avg_confidence = total_confidence / stage_count if stage_count > 0 else 0
        
        # Determine if tickets are found
        tickets_found = avg_confidence >= self.confidence_threshold
        
        # Get ticket count from DOM structure if available
        ticket_count = 0
        if 'dom_structure' in results and 'found_elements' in results['dom_structure']:
            ticket_count = results['dom_structure']['found_elements'].get('ticket_containers', 0)
        
        return {
            'tickets_found': tickets_found,
            'confidence': avg_confidence,
            'ticket_count': ticket_count,
            'details': results,
            'recommendation': self._get_recommendation(avg_confidence, results)
        }
    
    async def _generic_detection(self, page: Any, content: str = None) -> Dict[str, Any]:
        """Generic ticket detection for unsupported platforms"""
        
        if not content:
            try:
                content = await page.content() if hasattr(page, 'content') else page.page_source
            except:
                content = ""
        
        # Generic indicators
        positive_indicators = [
            'add to cart', 'buy now', 'purchase',
            'select tickets', 'available', 'in stock'
        ]
        
        negative_indicators = [
            'sold out', 'unavailable', 'no tickets',
            'coming soon', 'waitlist'
        ]
        
        content_lower = content.lower()
        
        # Count indicators
        positive_count = sum(1 for ind in positive_indicators if ind in content_lower)
        negative_count = sum(1 for ind in negative_indicators if ind in content_lower)
        
        # Calculate confidence
        confidence = 0
        if positive_count > 0 and negative_count == 0:
            confidence = min(1.0, positive_count * 0.3)
        elif positive_count > negative_count:
            confidence = 0.5
        else:
            confidence = 0.1
        
        return {
            'tickets_found': confidence >= 0.5,
            'confidence': confidence,
            'ticket_count': 0,
            'details': {
                'generic_detection': {
                    'positive_indicators': positive_count,
                    'negative_indicators': negative_count
                }
            },
            'recommendation': 'Using generic detection - results may be less accurate'
        }
    
    def _get_recommendation(self, confidence: float, results: Dict[str, Any]) -> str:
        """Get recommendation based on detection results"""
        
        if confidence >= 0.9:
            return "High confidence - tickets very likely available"
        elif confidence >= self.confidence_threshold:
            return "Tickets detected with good confidence"
        elif confidence >= 0.5:
            return "Possible tickets detected - manual verification recommended"
        elif confidence >= 0.3:
            return "Low confidence - may be false positive"
        else:
            return "No tickets detected or page may be blocking detection"
