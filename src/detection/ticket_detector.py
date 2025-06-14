

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
