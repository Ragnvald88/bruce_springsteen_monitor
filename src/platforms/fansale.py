# src/platforms/fansale.py (Ultra-Robust Multi-Section Version)
from __future__ import annotations

import logging
import random
import asyncio
import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING, Tuple, Set
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

from playwright.async_api import Page, Error as PlaywrightError, Locator, ElementHandle

# Core project imports
from core.errors import BlockedError
from src.profiles.manager import BrowserProfile

# Import behavioral simulation
from utils.advanced_behavioral_simulation import simulate_advanced_human_behavior, BiometricProfile

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

@dataclass
class SectionInfo:
    """Structured section information"""
    full_name: str
    normalized_name: str
    sector_type: str  # prato, anello, tribuna, etc.
    sector_variant: Optional[str] = None  # A, B, numerato, etc.
    row: Optional[str] = None
    seats: List[str] = None
    entrance: Optional[str] = None

class FansaleSelectors:
    """Enhanced selectors based on actual Fansale DOM structure"""
    # Cookie/Overlay handling
    COOKIE_ACCEPT = [
        "button#onetrust-accept-btn-handler",
        "button[aria-label*='Accept']",
        "button:has-text('Accetta')",
        "div.cookie-consent button.accept",
    ]
    
    # Main listing page
    NO_TICKETS_INDICATORS = [
        "div.alert-content:has-text('non sono disponibili biglietti')",
        "div.event-list-empty",
        "text=Nessun biglietto trovato",
        "text=non sono state trovate offerte"
    ]
    
    # Ticket cards and details
    TICKET_CARD = "div.EventEntry.js-EventEntry[data-offer-id]"
    TICKET_SECTION = "div.EventEntryRow"
    TICKET_PRICE = "span.moneyValueFormat"
    TICKET_QUANTITY = "div.EventEntryRow:has-text('bigliett')"
    
    # Detail view selectors
    DETAIL_CONTAINER = "div.Card-DetailC"
    TICKET_CHECKBOXES = "input.Checkbox[name='tickets']"
    QUANTITY_DROPDOWN = "button.Dropdown"
    SEAT_DESCRIPTION = "span.OfferEntry-SeatDescription, span.js-DetailC-SeatDescription"
    SUBMIT_BUTTON = "button[type='submit']:has-text('Acquista')"
    
    # Trust and availability indicators
    FAIR_DEAL_ICON = "span.FairDealIcon"
    TICKETCHECK_ICON = "span.TicketcheckIcon"
    OFFER_ENDED = "text=L'offerta è terminata"
    RECAPTCHA = "div.g-recaptcha, iframe[src*='recaptcha']"

# Enhanced Italian patterns with section recognition
class ItalianPatterns:
    PRICE_REGEX = re.compile(r"€\s*([\d.,]+)")
    
    # Comprehensive section patterns
    SECTION_PATTERNS = {
        # Format: pattern -> (sector_type, variant_extractor)
        r"(?i)prato\s+([a-z])": ("prato", lambda m: m.group(1).upper()),
        r"(?i)anello\s+(blu|rosso|verde)\s+(\d+)": ("anello", lambda m: f"{m.group(1)}_{m.group(2)}"),
        r"(?i)tribuna\s+(est|ovest|nord|sud)": ("tribuna", lambda m: m.group(1)),
        r"(?i)parterre\s+(\d+)?": ("parterre", lambda m: m.group(1) or "generale"),
        r"(?i)pit\s*(\d+)?": ("pit", lambda m: m.group(1) or "1"),
        r"(?i)(\d+)\s+anello": ("anello", lambda m: f"livello_{m.group(1)}"),
    }
    
    # Seat detail patterns
    SEAT_PATTERN = re.compile(r"Fila\s+(\d+)\s*\|\s*Posto\s+([\d,\s]+)")
    ENTRANCE_PATTERN = re.compile(r"(?i)ingresso\s+(\d+)")
    
    # Section aliases for matching
    SECTION_ALIASES = {
        "prato": ["lawn", "general admission", "ga"],
        "anello": ["ring", "tier", "livello"],
        "tribuna": ["tribune", "stand"],
        "parterre": ["floor", "platea"],
    }

class TicketMatcher:
    """Advanced ticket matching logic"""
    
    @staticmethod
    def parse_section(section_text: str) -> SectionInfo:
        """Parse section text into structured info"""
        info = SectionInfo(
            full_name=section_text,
            normalized_name=section_text.lower().strip(),
            sector_type="unknown"
        )
        
        # Try to match section patterns
        for pattern, (sector_type, variant_extractor) in ItalianPatterns.SECTION_PATTERNS.items():
            match = re.search(pattern, section_text)
            if match:
                info.sector_type = sector_type
                try:
                    info.sector_variant = variant_extractor(match)
                except:
                    pass
                break
        
        # Extract entrance
        entrance_match = ItalianPatterns.ENTRANCE_PATTERN.search(section_text)
        if entrance_match:
            info.entrance = entrance_match.group(1)
        
        # Extract seat details
        seat_match = ItalianPatterns.SEAT_PATTERN.search(section_text)
        if seat_match:
            info.row = seat_match.group(1)
            seats_str = seat_match.group(2)
            info.seats = [s.strip() for s in seats_str.split(",")]
        
        return info
    
    @staticmethod
    def matches_criteria(section_info: SectionInfo, desired_sections: List[str], 
                        strict_mode: bool = False) -> Tuple[bool, float]:
        """
        Check if section matches criteria and return match score
        Returns: (matches, score) where score is 0.0-1.0
        """
        if not desired_sections:
            return True, 1.0
        
        best_score = 0.0
        
        for desired in desired_sections:
            desired_lower = desired.lower().strip()
            
            # Exact match
            if desired_lower == section_info.normalized_name:
                return True, 1.0
            
            # Sector type match
            if desired_lower == section_info.sector_type:
                best_score = max(best_score, 0.8)
            
            # Sector + variant match (e.g., "prato a")
            if section_info.sector_variant:
                combined = f"{section_info.sector_type} {section_info.sector_variant}".lower()
                if desired_lower in combined or combined in desired_lower:
                    return True, 0.95
            
            # Partial match
            if not strict_mode:
                if desired_lower in section_info.normalized_name:
                    best_score = max(best_score, 0.7)
                elif section_info.normalized_name in desired_lower:
                    best_score = max(best_score, 0.6)
                
                # Alias matching
                for base_type, aliases in ItalianPatterns.SECTION_ALIASES.items():
                    if section_info.sector_type == base_type:
                        if any(alias in desired_lower for alias in aliases):
                            best_score = max(best_score, 0.5)
        
        return best_score > 0.5, best_score

async def check_fansale_event(
    page: Page,
    profile: BrowserProfile,
    target_cfg: Dict[str, Any],
    gui_q: Optional[asyncio.Queue] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Ultra-robust Fansale ticket checking with multi-section support
    """
    biometric_config_dict = profile.extra_js_props.get("biometric_profile_config", {})
    current_biometric_profile_instance = BiometricProfile(**biometric_config_dict)
    event_url = target_cfg.get("url")
    if not event_url:
        log.error("FanSale: Missing URL in target configuration")
        return None

    event_name = target_cfg.get("event_name", "Unknown Event")
    profile_name = profile.name
    
    log.info(f"FanSale [{event_name}]: Starting check with profile {profile_name}")
    
    if gui_q:
        await gui_q.put(("target_status_update", (event_url, f"Checking (Profile: {profile_name[:15]})", False)))

    try:
        # Let behavioral simulation handle human-like interactions
        behavior_intensity = target_cfg.get("human_behavior_intensity", "medium")
        if behavior_intensity != "none":
            biometric_config = profile.extra_js_props.get("biometric_profile_config", {})
            biometric_profile_instance = BiometricProfile(**biometric_config)
            await simulate_advanced_human_behavior(page, intensity=behavior_intensity, profile=biometric_profile_instance)
        
        # Handle cookie consent
        await _handle_cookie_consent(page, profile_name)
        
        # Small stabilization delay
        await asyncio.sleep(random.uniform(1.5, 2.5))
        
        # Check for "no tickets" indicators
        no_tickets_found = await _check_no_tickets(page, event_name, gui_q, event_url)
        if no_tickets_found:
            return None
        
        # Extract all ticket listings with enhanced parsing
        all_listings = await _extract_all_ticket_listings(page, target_cfg, profile_name)
        
        if not all_listings:
            log.info(f"FanSale [{event_name}]: No listings found")
            if gui_q:
                await gui_q.put(("target_status_update", (event_url, "No listings", False)))
            return None
        
        # Group listings by section for analysis
        section_groups = _group_listings_by_section(all_listings)
        
        # Log section availability
        log.info(f"FanSale [{event_name}]: Found tickets in {len(section_groups)} different sections:")
        for section, listings in section_groups.items():
            price_range = _get_price_range(listings)
            log.info(f"  - {section}: {len(listings)} listings, €{price_range['min']:.2f}-€{price_range['max']:.2f}")
        
        # Apply intelligent filtering with price consideration
        hits = await _intelligent_filter_tickets(
            all_listings, 
            section_groups,
            target_cfg, 
            event_name, 
            profile_name
        )
        
        if hits:
            log.warning(f"FanSale HIT [{event_name}]: Found {len(hits)} matching tickets!")
            # Sort hits by preference score and price
            hits = _sort_hits_by_preference(hits, target_cfg)
            
            if gui_q:
                best_hit = hits[0]
                status_msg = f"HIT! {best_hit['section_info'].sector_type} €{best_hit['price']:.2f}"
                await gui_q.put(("target_status_update", (event_url, status_msg, True)))
            return hits
        else:
            log.info(f"FanSale [{event_name}]: No matching tickets found")
            if gui_q:
                await gui_q.put(("target_status_update", (event_url, "Nessuna corrispondenza", False)))
            return None
            
    except BlockedError:
        raise
    except Exception as e:
        log.error(f"FanSale [{event_name}]: Error during check: {e}", exc_info=True)
        raise BlockedError(f"FanSale check error: {str(e)[:100]}") from e

async def _check_no_tickets(page: Page, event_name: str, gui_q: Optional[asyncio.Queue], event_url: str) -> bool:
    """Check for no tickets indicators"""
    for selector in FansaleSelectors.NO_TICKETS_INDICATORS:
        try:
            if await page.locator(selector).is_visible(timeout=1000):
                log.info(f"FanSale [{event_name}]: No tickets indicator found: {selector}")
                if gui_q:
                    await gui_q.put(("target_status_update", (event_url, "Nessun biglietto", False)))
                return True
        except:
            pass
    return False

async def monitor(*args, **kwargs):
    return []

async def _extract_all_ticket_listings(
    page: Page, 
    target_cfg: Dict[str, Any],
    profile_name: str
) -> List[Dict[str, Any]]:
    """Extract all ticket listings with enhanced section parsing"""
    listings = []
    
    try:
        # Wait for listings
        await page.wait_for_selector(FansaleSelectors.TICKET_CARD, timeout=10000)
        
        # Get all ticket cards
        ticket_cards = await page.locator(FansaleSelectors.TICKET_CARD).all()
        
        log.info(f"FanSale [{profile_name}]: Found {len(ticket_cards)} ticket cards")
        
        for i, card in enumerate(ticket_cards):
            try:
                # Extract comprehensive ticket details
                offer_id = await card.get_attribute("data-offer-id")
                
                # Get all text content for section parsing
                all_text = await card.inner_text()
                
                # Try multiple methods to extract section
                section_text = await _extract_section_text(card, all_text)
                
                # Parse section into structured info
                section_info = TicketMatcher.parse_section(section_text)
                
                # Get price
                price_elem = card.locator(FansaleSelectors.TICKET_PRICE).first
                price_text = await price_elem.inner_text() if await price_elem.count() else ""
                price_value = _parse_italian_price(price_text)
                
                # Get quantity if available
                quantity = await _extract_quantity(card, all_text)
                
                # Check trust indicators
                has_fair_deal = await card.locator(FansaleSelectors.FAIR_DEAL_ICON).count() > 0
                has_ticketcheck = await card.locator(FansaleSelectors.TICKETCHECK_ICON).count() > 0
                
                listing = {
                    "offer_id": offer_id,
                    "section": section_text.strip(),
                    "section_info": section_info,
                    "price_str": price_text,
                    "price": price_value,
                    "quantity": quantity,
                    "trust_indicators": {
                        "fair_deal": has_fair_deal,
                        "ticketcheck": has_ticketcheck
                    },
                    "card_index": i,
                    "platform_specific_data": {
                        "offer_id": offer_id,
                        "has_trust_badges": has_fair_deal or has_ticketcheck,
                        "full_text": all_text[:200]  # Store for debugging
                    }
                }
                
                listings.append(listing)
                
                # Natural delay between extractions
                if i < len(ticket_cards) - 1:
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                    
            except Exception as e:
                log.warning(f"FanSale: Error extracting listing {i}: {e}")
                continue
                
    except PlaywrightError as e:
        log.warning(f"FanSale: Error waiting for listings: {e}")
    
    return listings

async def _extract_section_text(card: Locator, full_text: str) -> str:
    """Try multiple methods to extract section information"""
    # Method 1: Look for section-specific elements
    section_patterns = [
        "Ingr\\.",
        "Settore",
        "Anello",
        "Prato",
        "Tribuna",
        "Parterre"
    ]
    
    for pattern in section_patterns:
        elem = card.locator(f"text=/{pattern}/i").first
        if await elem.count():
            parent = card.locator("div.EventEntryRow").filter(has=elem).first
            if await parent.count():
                return await parent.inner_text()
    
    # Method 2: Extract from full text using regex
    section_line_pattern = re.compile(r"((?:Ingr\.|Settore|Prato|Anello|Tribuna).*?)(?:\n|$)", re.IGNORECASE)
    match = section_line_pattern.search(full_text)
    if match:
        return match.group(1)
    
    # Method 3: Look for seat description
    seat_desc = card.locator(FansaleSelectors.SEAT_DESCRIPTION).first
    if await seat_desc.count():
        return await seat_desc.inner_text()
    
    return "Unknown Section"

async def _extract_quantity(card: Locator, full_text: str) -> int:
    """Extract ticket quantity from card"""
    # Look for quantity patterns
    qty_patterns = [
        r"(\d+)\s*bigliett",
        r"quantità[:\s]+(\d+)",
        r"qty[:\s]+(\d+)"
    ]
    
    for pattern in qty_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 1  # Default to 1 if not found

def _group_listings_by_section(listings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group listings by normalized section"""
    groups = defaultdict(list)
    
    for listing in listings:
        section_info = listing["section_info"]
        # Create a grouping key
        if section_info.sector_variant:
            key = f"{section_info.sector_type}_{section_info.sector_variant}"
        else:
            key = section_info.sector_type
        
        groups[key].append(listing)
    
    return dict(groups)

def _get_price_range(listings: List[Dict[str, Any]]) -> Dict[str, float]:
    """Get min and max prices from listings"""
    prices = [l["price"] for l in listings if l["price"] is not None]
    if not prices:
        return {"min": 0.0, "max": 0.0}
    return {"min": min(prices), "max": max(prices)}

async def _intelligent_filter_tickets(
    all_listings: List[Dict[str, Any]],
    section_groups: Dict[str, List[Dict[str, Any]]],
    target_cfg: Dict[str, Any],
    event_name: str,
    profile_name: str
) -> List[Dict[str, Any]]:
    """Apply intelligent filtering with section and price consideration"""
    desired_sections = target_cfg.get("desired_sections", [])
    max_price = target_cfg.get("max_price_per_ticket")
    min_price = target_cfg.get("min_price_per_ticket")
    prefer_trust_badges = target_cfg.get("prefer_trust_badges", True)
    strict_section_match = target_cfg.get("strict_section_match", False)
    
    hits = []
    
    for listing in all_listings:
        # Price filtering
        if max_price and listing["price"] and listing["price"] > max_price:
            continue
        if min_price and listing["price"] and listing["price"] < min_price:
            continue
        
        # Section matching with score
        matches, match_score = TicketMatcher.matches_criteria(
            listing["section_info"], 
            desired_sections, 
            strict_section_match
        )
        
        if matches:
            # Add match score to listing
            listing["match_score"] = match_score
            
            # Bonus for trust badges
            if prefer_trust_badges and listing["trust_indicators"]["fair_deal"]:
                listing["match_score"] += 0.1
            
            # Create detailed message
            listing["message"] = f"{listing['section']} - {listing['price_str']}"
            if listing["quantity"] > 1:
                listing["message"] += f" ({listing['quantity']} tickets)"
            if listing["offer_id"]:
                listing["message"] += f" [ID: {listing['offer_id']}]"
            
            hits.append(listing)
            log.warning(f"FanSale HIT [{event_name}]: {listing['message']} (Score: {match_score:.2f})")
    
    return hits

def _sort_hits_by_preference(hits: List[Dict[str, Any]], target_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Sort hits by preference (match score, trust, price)"""
    price_weight = target_cfg.get("price_importance", 0.3)  # 0.0-1.0
    
    def sort_key(hit):
        score = hit["match_score"]
        
        # Price component (lower is better)
        if hit["price"]:
            # Normalize price to 0-1 range (assuming max €500)
            price_score = 1.0 - (hit["price"] / 500.0)
            score += price_score * price_weight
        
        # Trust badge bonus
        if hit["trust_indicators"]["fair_deal"]:
            score += 0.15
        
        return -score  # Negative for descending order
    
    return sorted(hits, key=sort_key)

def _parse_italian_price(price_str: str) -> Optional[float]:
    """Parse Italian price format (€ 139,15)"""
    if not price_str:
        return None
    
    match = ItalianPatterns.PRICE_REGEX.search(price_str)
    if match:
        try:
            # Italian format uses comma for decimals
            price = match.group(1).replace(".", "").replace(",", ".")
            return float(price)
        except ValueError:
            log.warning(f"Could not parse price: {price_str}")
    return None

async def _handle_cookie_consent(page: Page, profile_name: str) -> bool:
    """Handle cookie consent banners"""
    for selector in FansaleSelectors.COOKIE_ACCEPT:
        try:
            button = page.locator(selector).first
            if await button.is_visible(timeout=2000):
                log.debug(f"FanSale [{profile_name}]: Found cookie button: {selector}")
                await button.click(delay=random.uniform(100, 300))
                await asyncio.sleep(random.uniform(1.0, 2.0))
                return True
        except:
            continue
    return False

async def click_specific_ticket_listing_and_proceed(
    page: Page,
    profile: BrowserProfile,
    hit_info: Dict[str, Any],
    target_cfg: Dict[str, Any]
) -> bool:
    """
    Enhanced purchase flow with intelligent ticket selection
    """
    event_name = hit_info.get("event_name", "Unknown")
    offer_id = hit_info.get("offer_id") or hit_info.get("platform_specific_data", {}).get("offer_id")
    
    if not offer_id:
        log.error(f"FanSale Purchase [{event_name}]: No offer_id found")
        return False
    
    section_info = hit_info.get("section_info")
    log.info(f"FanSale Purchase [{event_name}]: Attempting to purchase {section_info.full_name} for €{hit_info['price']:.2f}")
    
    try:
        # Find and click the specific ticket card
        ticket_selector = f"{FansaleSelectors.TICKET_CARD}[data-offer-id='{offer_id}']"
        ticket_card = page.locator(ticket_selector).first
        
        if not await ticket_card.count():
            log.error(f"FanSale Purchase [{event_name}]: Ticket card not found for offer {offer_id}")
            # Try to find it by section text as fallback
            fallback_card = await _find_ticket_by_section(page, section_info)
            if fallback_card:
                ticket_card = fallback_card
            else:
                return False
        
        # Ensure card is in viewport
        await ticket_card.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Click with natural movement
        await ticket_card.hover()
        await asyncio.sleep(random.uniform(0.2, 0.4))
        await ticket_card.click()
        
        # Wait for detail view
        try:
            await page.wait_for_selector(FansaleSelectors.DETAIL_CONTAINER, timeout=10000)
        except:
            log.error(f"FanSale Purchase [{event_name}]: Detail view did not load")
            return False
        
        # Check if offer is still available
        if await page.locator(FansaleSelectors.OFFER_ENDED).is_visible(timeout=2000):
            log.warning(f"FanSale Purchase [{event_name}]: Offer has ended (L'offerta è terminata)")
            return False
        
        # Smart ticket selection based on quantity preferences
        selected = await _smart_ticket_selection(page, target_cfg, event_name)
        if not selected:
            return False
        
        # Check for reCAPTCHA
        recaptcha_present = await page.locator(FansaleSelectors.RECAPTCHA).count() > 0
        if recaptcha_present:
            log.warning(f"FanSale Purchase [{event_name}]: reCAPTCHA detected - manual intervention required")
            # Could integrate with captcha solving service here
            
        # Find and click purchase button
        purchase_success = await _complete_purchase(page, event_name)
        
        if purchase_success:
            log.info(f"FanSale Purchase [{event_name}]: Purchase initiated - pausing for manual completion")
            await page.pause()
            return True
            
        return False
            
    except Exception as e:
        log.error(f"FanSale Purchase [{event_name}]: Error during purchase flow: {e}", exc_info=True)
        return False

async def _find_ticket_by_section(page: Page, section_info: SectionInfo) -> Optional[Locator]:
    """Fallback method to find ticket by section text"""
    all_cards = await page.locator(FansaleSelectors.TICKET_CARD).all()
    
    for card in all_cards:
        card_text = await card.inner_text()
        if section_info.full_name in card_text:
            return card
    
    return None

async def _smart_ticket_selection(page: Page, target_cfg: Dict[str, Any], event_name: str) -> bool:
    """Intelligently select tickets based on preferences"""
    checkboxes = await page.locator(FansaleSelectors.TICKET_CHECKBOXES).all()
    
    if not checkboxes:
        log.error(f"FanSale Purchase [{event_name}]: No ticket checkboxes found")
        return False
    
    desired_quantity = target_cfg.get("desired_ticket_quantity", len(checkboxes))
    max_quantity = target_cfg.get("max_ticket_quantity", 4)
    
    # Determine how many to select
    to_select = min(len(checkboxes), desired_quantity, max_quantity)
    
    log.info(f"FanSale Purchase [{event_name}]: Selecting {to_select} of {len(checkboxes)} available tickets")
    
    # Select tickets
    selected_count = 0
    for i, checkbox in enumerate(checkboxes):
        if selected_count >= to_select:
            break
            
        if not await checkbox.is_checked():
            await checkbox.check()
            selected_count += 1
            
            # Natural delay between selections
            if selected_count < to_select:
                await asyncio.sleep(random.uniform(0.2, 0.4))
    
    return selected_count > 0

async def _complete_purchase(page: Page, event_name: str) -> bool:
    """Complete the purchase process"""
    # Try multiple selectors for purchase button
    purchase_selectors = [
        FansaleSelectors.SUBMIT_BUTTON,
        "button:has-text('Acquista')",
        "button:has-text('Procedi')",
        "input[type='submit']",
        "button[type='submit']"
    ]
    
    for selector in purchase_selectors:
        button = page.locator(selector).first
        if await button.count() and await button.is_visible():
            log.warning(f"FanSale Purchase [{event_name}]: Clicking purchase button...")
            await button.click()
            
            # Wait for navigation or response
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            return True
    
    # If no button found, try form submission
    try:
        await page.evaluate("document.getElementById('detailCSectionForm').submit()")
        return True
    except:
        log.error(f"FanSale Purchase [{event_name}]: Could not find or click purchase button")
        return False

# Additional analysis function for section availability patterns
async def analyze_fansale_availability(
    page: Page,
    target_cfg: Dict[str, Any]
) -> Dict[str, Any]:
    """Comprehensive analysis of ticket availability by section"""
    
    all_listings = await _extract_all_ticket_listings(page, target_cfg, "analysis")
    section_groups = _group_listings_by_section(all_listings)
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "total_listings": len(all_listings),
        "sections": {},
        "price_distribution": {
            "overall": {"min": float('inf'), "max": 0, "avg": 0},
            "by_section": {}
        },
        "trust_badge_stats": {
            "fair_deal_count": sum(1 for l in all_listings if l["trust_indicators"]["fair_deal"]),
            "ticketcheck_count": sum(1 for l in all_listings if l["trust_indicators"]["ticketcheck"])
        }
    }
    
    # Analyze each section
    for section_key, listings in section_groups.items():
        prices = [l["price"] for l in listings if l["price"]]
        
        section_analysis = {
            "count": len(listings),
            "example_full_name": listings[0]["section"] if listings else "",
            "sector_type": listings[0]["section_info"].sector_type if listings else "unknown",
            "price_range": _get_price_range(listings),
            "avg_price": sum(prices) / len(prices) if prices else 0,
            "quantities_available": sum(l["quantity"] for l in listings),
            "trust_badges": sum(1 for l in listings if l["trust_indicators"]["fair_deal"])
        }
        
        analysis["sections"][section_key] = section_analysis
        
        # Update price distribution
        if prices:
            analysis["price_distribution"]["overall"]["min"] = min(
                analysis["price_distribution"]["overall"]["min"], 
                min(prices)
            )
            analysis["price_distribution"]["overall"]["max"] = max(
                analysis["price_distribution"]["overall"]["max"], 
                max(prices)
            )
            analysis["price_distribution"]["by_section"][section_key] = {
                "min": min(prices),
                "max": max(prices),
                "avg": section_analysis["avg_price"]
            }
    
    # Calculate overall average
    all_prices = [l["price"] for l in all_listings if l["price"]]
    if all_prices:
        analysis["price_distribution"]["overall"]["avg"] = sum(all_prices) / len(all_prices)
    
    return analysis