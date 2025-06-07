# src/platforms/vivaticket.py (Corrected & Improved)
from __future__ import annotations

import logging
import random
import asyncio
import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from playwright.async_api import Page, Error as PlaywrightError, Response

# Core project imports
from ..core.errors import BlockedError
from ..profiles.models import BrowserProfile
if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)
dbg_exc_info_platform = False # Set to True for very detailed exception logging

# Vivaticket specific selectors (these might need frequent updates)
VIVATICKET_NO_TICKETS_SELECTORS = [
    "div.alert-warning:has-text('Nessuna disponibilità')", # "No availability"
    "div:text('Non sono presenti biglietti in vendita per questo evento')", # "No tickets for sale for this event"
    "p.zeroResultMSG", # Often used for "no results" messages
]
VIVATICKET_TICKET_ROW_SELECTOR = "tr.ricercaPrezziETContent" # Selector for rows containing ticket info
VIVATICKET_PRICE_SELECTOR = "span.currencyبلیط" # Vivaticket often uses specific class for price, check exact class
VIVATICKET_SECTION_SELECTOR = "td.descr" # Example, selector for section/description within a row
VIVATICKET_AVAILABILITY_INDICATOR = "td.disp > span.available" # Example for a positive availability sign

async def _warm_up_vivaticket_page(page: Page, profile: BrowserProfile, event_url: str) -> bool:
    """
    Performs pre-flight checks or warm-up actions for Vivaticket.
    Attempts to ensure cookies are set for the domain.
    Returns True if pre-flight seems okay, False otherwise.
    """
    log.debug(f"Vivaticket [{profile.name}]: Warming up page/cookie context for {event_url}")
    try:
        # Ensure we are on the correct domain for cookie operations
        # Extract base Vivaticket domain (e.g., https://shop.vivaticket.com)
        parsed_url = asyncio.futures.Future() # Dummy future for type hint
        try:
            from urllib.parse import urlparse
            parsed_url_obj = urlparse(event_url)
            vivaticket_base_url = f"{parsed_url_obj.scheme}://{parsed_url_obj.netloc}"
        except ImportError: # Fallback if urllib.parse is not available (should be)
            vivaticket_base_url = "https://shop.vivaticket.com" # Hardcoded fallback
            log.warning("urllib.parse not available, using hardcoded vivaticket_base_url for cookies.")

        # Attempt to get cookies for the base domain. This can help "activate" the context.
        # If the page isn't on a Vivaticket domain yet, this might be an issue.
        if "vivaticket.com" in page.url.lower() or "vivaticket.it" in page.url.lower():
            await page.context.cookies(urls=[vivaticket_base_url]) 
            log.debug(f"Vivaticket [{profile.name}]: Cookies checked for domain {vivaticket_base_url}")
        else:
            # If the current page URL isn't a Vivaticket domain, navigating first might be necessary
            # or the cookie check might be for a different purpose (e.g. if API is on different domain)
            log.warning(f"Vivaticket [{profile.name}]: Current page URL '{page.url}' may not be ideal for Vivaticket cookie check against '{vivaticket_base_url}'.")
            # Try to get cookies for the specific event_url as well if it's different and valid
            if event_url != page.url and ("vivaticket.com" in event_url.lower() or "vivaticket.it" in event_url.lower()):
                 await page.context.cookies(urls=[event_url])
                 log.debug(f"Vivaticket [{profile.name}]: Also checked cookies for event_url {event_url}")


        # Optional: Perform a dummy request or ensure page is fully loaded if issues persist
        # await page.reload(wait_until="domcontentloaded") # Example
        return True
    except PlaywrightError as e:
        log.warning(f"Vivaticket [{profile.name}]: Playwright error during pre-flight cookie check/warm_up for {event_url}: {e}")
    except Exception as e_gen:
        log.error(f"Vivaticket [{profile.name}]: General error during pre-flight/warm_up for {event_url}: {e_gen}", exc_info=dbg_exc_info_platform)
    return False

async def monitor(*args, **kwargs):
    return []

async def check_vivaticket_event(
    page: Page,
    profile: BrowserProfile, # <--- ADDED ARGUMENT
    target_cfg: Dict[str, Any],
    gui_q: Optional[asyncio.Queue] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Checks Vivaticket event page for available tickets.
    Vivaticket often relies on specific page structures and might not have a stable public API.
    This checker will primarily scrape the page content.
    """
    event_url = target_cfg.get("url")
    if not event_url:
        log.error("Vivaticket: URL ontbreekt in target_cfg.")
        return None

    event_name = target_cfg.get("event_name", event_url)
    # Use profile.name from the passed argument
    current_profile_name = profile.name 
    
    # Add a random query parameter to try and bypass some caching, if not already present
    if "random=" not in event_url:
        separator = "&" if "?" in event_url else "?"
        url_to_check = f"{event_url}{separator}random={random.randint(100000, 999999)}"
    else:
        url_to_check = event_url # Assume random is already handled if present

    log.info(f"Vivaticket [{event_name}]: Start UI check: {url_to_check} (Profile: {current_profile_name})")
    if gui_q: await gui_q.put(("target_status_update", (event_url, f"Checking UI (Profile: {current_profile_name[:15]})", False)))

    try:
        # Perform pre-flight/warm-up actions
        # The "Invalid URL" for cookies warning in your logs likely came from here.
        # We need to ensure `page.context.cookies()` is called appropriately.
        # It's often better to call it with the base domain URL if the page isn't fully navigated yet.
        if not await _warm_up_vivaticket_page(page, profile, url_to_check):
            log.warning(f"Vivaticket [{current_profile_name}]: Pre-flight/warm-up failed. Proceeding with caution.")
            # Depending on strictness, you might choose to return None here

        # Navigate to the page if not already there (page.goto is handled by main.py's get_page_from_context)
        # Ensure the page is at the target URL after any redirects from initial goto
        if page.url.split('?')[0] != url_to_check.split('?')[0]: # Compare base URL without query params
            log.info(f"Vivaticket [{current_profile_name}]: Page URL '{page.url}' differs from target '{url_to_check}'. Navigating again.")
            await page.goto(url_to_check, wait_until="domcontentloaded", timeout=45000)
            log.info(f"Vivaticket [{current_profile_name}]: Re-navigated to {page.url}")


        # 1. Check for "No Tickets Available" messages
        no_tickets_selectors = target_cfg.get("vivaticket_no_tickets_selectors", VIVATICKET_NO_TICKETS_SELECTORS)
        for selector in no_tickets_selectors:
            try:
                if await page.locator(selector).first.is_visible(timeout=3000):
                    log.info(f"Vivaticket [{event_name}]: Geen tickets beschikbaar (indicator: '{selector}', Profile: {current_profile_name}).")
                    if gui_q: await gui_q.put(("target_status_update", (event_url, "Geen tickets (pagina)", False)))
                    return None
            except PlaywrightError: pass
        
        # 2. Look for ticket listings/rows
        # This part is highly dependent on Vivaticket's specific HTML structure for the event.
        # The selectors below are examples and WILL need verification and adjustment.
        ticket_row_selector = target_cfg.get("vivaticket_ticket_row_selector", VIVATICKET_TICKET_ROW_SELECTOR)
        
        try:
            await page.locator(ticket_row_selector).first.wait_for(state="visible", timeout=15000)
        except PlaywrightError:
            log.info(f"Vivaticket [{event_name}]: Geen ticket rows gevonden (selector: '{ticket_row_selector}', Profile: {current_profile_name}, timeout). Mogelijk geen tickets.")
            # Check again for no-ticket messages as sometimes they appear after a delay
            for selector in no_tickets_selectors:
                if await page.locator(selector).first.is_visible(timeout=1000):
                    log.info(f"Vivaticket [{event_name}]: Late 'geen tickets' indicator '{selector}' (Profile: {current_profile_name}).")
                    if gui_q: await gui_q.put(("target_status_update", (event_url, "Geen tickets (laat)", False)))
                    return None
            if gui_q: await gui_q.put(("target_status_update", (event_url, "Geen listings (timeout)", False)))
            return None

        all_rows = await page.locator(ticket_row_selector).all()
        if not all_rows:
            log.info(f"Vivaticket [{event_name}]: Ticket row selector '{ticket_row_selector}' leverde geen elementen op (Profile: {current_profile_name}).")
            if gui_q: await gui_q.put(("target_status_update", (event_url, "Geen listings (selector)", False)))
            return None
            
        log.info(f"Vivaticket [{event_name}]: {len(all_rows)} potentiële ticket rows gevonden (Profile: {current_profile_name}).")

        hits_found: List[Dict[str, Any]] = []
        desired_sections_raw = target_cfg.get("desired_sections", [])
        desired_sections_lower = [str(s).lower().strip() for s in desired_sections_raw if isinstance(s, str) and s.strip()]

        for i, row_loc in enumerate(all_rows):
            try:
                # Extract section/description
                section_text = "N/A"
                section_sel = target_cfg.get("vivaticket_section_selector", VIVATICKET_SECTION_SELECTOR)
                section_loc = row_loc.locator(section_sel).first
                if await section_loc.count():
                    section_text = (await section_loc.inner_text(timeout=1000)).strip()

                # Extract price
                price_text = "N/A"
                price_val = None
                price_sel = target_cfg.get("vivaticket_price_selector", VIVATICKET_PRICE_SELECTOR)
                price_loc = row_loc.locator(price_sel).first
                if await price_loc.count():
                    raw_price = (await price_loc.inner_text(timeout=1000)).strip()
                    # Vivaticket price parsing can be tricky, adjust regex as needed
                    match_price = re.search(r"([\d\.,]+)", raw_price)
                    if match_price:
                        price_text = raw_price # Keep full string
                        try: price_val = float(match_price.group(1).replace(".","").replace(",","."))
                        except ValueError: log.warning(f"Vivaticket: Kon prijs niet parsen uit '{raw_price}'")
                
                # Check availability (e.g., presence of a buy button, specific class, or text)
                # This is highly site-specific. Example:
                availability_sel = target_cfg.get("vivaticket_availability_indicator", VIVATICKET_AVAILABILITY_INDICATOR)
                is_available = await row_loc.locator(availability_sel).count() > 0
                # Alternative: check for a buy button within the row
                # buy_button_loc = row_loc.locator("a[href*='checkout'], button:has-text('Acquista')")
                # is_available = await buy_button_loc.count() > 0

                if not is_available:
                    log.debug(f"Vivaticket [{event_name}]: Row #{i+1} ('{section_text}') niet beschikbaar (Profile: {current_profile_name}).")
                    continue

                # Filter by desired section
                is_desired = not desired_sections_lower
                if not is_desired and section_text != "N/A":
                    listing_section_lower = section_text.lower()
                    for desired_term in desired_sections_lower:
                        if desired_term in listing_section_lower:
                            is_desired = True; break
                
                if is_desired:
                    hit_message = f"Vivaticket: {section_text} - {price_text if price_val is not None else 'Prijs N/A'}"
                    hit_details = {
                        "message": hit_message,
                        "offer_url": page.url, # For Vivaticket, often the main page URL is relevant for the hit context
                        "section": section_text,
                        "price_str": price_text,
                        "price": price_val,
                        "platform_specific_data": {
                            "row_index": i, # Could be useful for trying to click later
                            # Add other scraped data if available
                        }
                    }
                    hits_found.append(hit_details)
                    log.warning(f"Vivaticket HIT [{event_name}] (Profile: {current_profile_name}): GEVONDEN! {hit_message}")

            except PlaywrightError as e_row:
                log.warning(f"Vivaticket [{event_name}]: Playwright fout bij verwerken row #{i+1} (Profile: {current_profile_name}): {e_row}")
            except Exception as e_row_gen:
                log.error(f"Vivaticket [{event_name}]: Algemene fout bij verwerken row #{i+1} (Profile: {current_profile_name}): {e_row_gen}", exc_info=dbg_exc_info_platform)


        if hits_found:
            if gui_q: await gui_q.put(("target_status_update", (event_url, f"HIT! ({len(hits_found)})", True)))
            return hits_found
        else:
            log.info(f"Vivaticket [{event_name}]: Geen tickets gevonden die matchen (Profile: {current_profile_name}).")
            if gui_q: await gui_q.put(("target_status_update", (event_url, "Geen match/criteria", False)))
            return None

    except BlockedError: raise # Re-raise if already a BlockedError
    except PlaywrightError as e_pw:
        log.warning(f"Vivaticket [{event_name}]: Playwright fout tijdens check (Profile: {current_profile_name}): {e_pw}")
        raise BlockedError(f"Vivaticket: Playwright fout (Profile: {current_profile_name}, {str(e_pw)[:50]})") from e_pw
    except Exception as e_gen:
        log.error(f"Vivaticket [{event_name}]: Onverwachte algemene fout tijdens check (Profile: {current_profile_name}): {e_gen}", exc_info=True)
        raise BlockedError(f"Vivaticket: Algemene check fout (Profile: {current_profile_name}, {str(e_gen)[:50]})") from e_gen
