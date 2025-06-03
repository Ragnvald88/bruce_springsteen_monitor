# src/platforms/ticketmaster.py (Corrected with API Interception)
from __future__ import annotations

import json
import logging
import re
import asyncio
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple, Any
from urllib.parse import urlparse # Import urlparse

from playwright.async_api import Page, BrowserContext, Response, Error as PlaywrightError

from src.profiles.manager import BrowserProfile
from core.errors import BlockedError
from utils.advanced_behavioral_simulation import simulate_advanced_human_behavior, BiometricProfile

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)
dbg_exc_info_platform = False

# Regex to extract Product ID (PID) from Ticketmaster URL
_PID_RE = re.compile(r"-([0-9a-fA-F]{4,})\.html(?:$|\?)", re.IGNORECASE)

# Template for the products API URL
PRODUCT_API_BASE_URL = "https://shop.ticketmaster.it/api/products/"


def _extract_pid_from_url(url: str) -> Optional[str]:
    """Extracts the Product ID (PID) from a Ticketmaster event URL."""
    match = _PID_RE.search(url)
    if match:
        return match.group(1)
    log.warning(f"Ticketmaster: Kon PID niet extraheren uit URL: {url}")
    return None

async def _get_csrf_token(context: BrowserContext) -> Optional[str]:
    """Retrieves the _csrf cookie value from the browser context."""
    try:
        cookies = await context.cookies()
        for cookie in cookies:
            if cookie["name"] == "_csrf":
                return cookie["value"]
    except PlaywrightError as e:
        log.warning(f"Ticketmaster: Playwright fout bij ophalen cookies voor CSRF token: {e}")
    except Exception as e_gen:
        log.error(f"Ticketmaster: Algemene fout bij ophalen CSRF token: {e_gen}", exc_info=dbg_exc_info_platform)
    log.warning("Ticketmaster: CSRF token cookie ('_csrf') niet gevonden in context.")
    return None


async def add_to_basket(
    context: BrowserContext,
    offer_id: str,
    event_page_url: str, # URL of the event page to use as referer
    basket_id: Optional[str] = None,
    quantity: int = 1
) -> Tuple[bool, Optional[str]]:
    """
    Adds an offer to the Ticketmaster basket using API calls,
    but attempts to do so with more context from the browser.
    """
    csrf_token = await _get_csrf_token(context)
    if not csrf_token:
        log.error("Ticketmaster API (add_to_basket): Geen CSRF token. Actie afgebroken.")
        return False, None

    current_basket_id = basket_id
    api_base_url = "https://shop.ticketmaster.it/api"

    # Parse the event_page_url to get the origin
    parsed_event_url = urlparse(event_page_url)
    origin = f"{parsed_event_url.scheme}://{parsed_event_url.netloc}"

    # Define common headers for API requests to look more like XHR
    api_headers = {
        "X-CSRF-Token": csrf_token,
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": origin, # Set Origin based on the event page
        "Referer": event_page_url, # Set Referer to the event page URL
    }

    try:
        if not current_basket_id:
            log.debug(f"Ticketmaster API: Aanmaken nieuwe winkelwagen (OfferID: {offer_id})...")
            create_headers = api_headers.copy()
            # Basket creation might not need Content-Type if no body, or might need different one.
            resp_basket_create = await context.request.post(
                f"{api_base_url}/baskets",
                headers=create_headers,
                timeout=15_000
            )
            if resp_basket_create.status not in [200, 201]: # 200 if existing reused, 201 if new
                log.error(f"Ticketmaster API: Aanmaken/ophalen winkelwagen mislukt (Status: {resp_basket_create.status}). Response: {await resp_basket_create.text(timeout=5000)[:250]}")
                return False, None

            basket_data = await resp_basket_create.json(timeout=5000)
            current_basket_id = basket_data.get("id")
            if not current_basket_id:
                log.error(f"Ticketmaster API: 'id' niet gevonden in winkelwagen response. Data: {basket_data}")
                return False, None
            log.info(f"Ticketmaster API: Winkelwagen ID verkregen/aangemaakt: {current_basket_id}")

        log.info(f"Ticketmaster API: Toevoegen offer_id '{offer_id}' (qty: {quantity}) aan winkelwagen '{current_basket_id}'...")
        add_entry_headers = api_headers.copy()
        add_entry_headers["Content-Type"] = "application/json;charset=UTF-8"

        resp_add_entry = await context.request.post(
            f"{api_base_url}/baskets/{current_basket_id}/entries",
            headers=add_entry_headers,
            data=json.dumps({"offerId": str(offer_id), "quantity": quantity}),
            timeout=20_000
        )

        if resp_add_entry.status == 201:
            log.warning(f"Ticketmaster API: ✅ Ticket (offer_id: {offer_id}) succesvol toegevoegd aan winkelwagen {current_basket_id}!")
            return True, current_basket_id
        else:
            response_text = await resp_add_entry.text(timeout=5000)
            log.error(f"Ticketmaster API: Toevoegen aan winkelwagen mislukt (Status: {resp_add_entry.status}). OfferID: {offer_id}. BasketID: {current_basket_id}. Response: {response_text[:300]}")
            if "TOTAL_ITEM_LIMIT_EXCEEDED" in response_text:
                log.error("Ticketmaster API: Limiet per klant overschreden voor dit item.")
            elif "OFFER_NOT_AVAILABLE" in response_text:
                log.error("Ticketmaster API: Offer is niet langer beschikbaar.")
            return False, current_basket_id

    except PlaywrightError as e_pw_basket:
        log.error(f"Ticketmaster API: Playwright netwerk/timeout fout tijdens add_to_basket: {e_pw_basket}", exc_info=dbg_exc_info_platform)
    except json.JSONDecodeError as e_json_basket:
        log.error(f"Ticketmaster API: JSON decodeerfout tijdens add_to_basket: {e_json_basket}.", exc_info=dbg_exc_info_platform)
    except Exception as e_basket:
        log.error(f"Ticketmaster API: Onverwachte fout tijdens add_to_basket: {e_basket}", exc_info=True)
    return False, current_basket_id

async def monitor(*args, **kwargs):
    return []
async def check_ticketmaster_event(
    page: Page,
    profile: BrowserProfile,
    target_cfg: Dict[str, Any],
    gui_q: Optional[asyncio.Queue] = None,
) -> Optional[List[Dict[str, Any]]]:
    event_url = target_cfg.get("url")
    if not event_url:
        log.error("Ticketmaster: URL ontbreekt in target_cfg.")
        return None

    pid = _extract_pid_from_url(event_url)
    if not pid:
        # PID extraction failure already logged by _extract_pid_from_url
        return None

    expected_api_url_pattern = f"{PRODUCT_API_BASE_URL}{pid}"
    event_name = target_cfg.get("event_name", event_url)

    log.info(f"Ticketmaster [{event_name}]: Navigating to event page to capture API data: {event_url} (Profile: {profile.name})")
    if gui_q: await gui_q.put(("target_status_update", (event_url, f"Navigating (Prof: {profile.name[:10]})", False)))

    raw_response_body = ""
    response_status = -1
    event_data = None
    api_response_object: Optional[Response] = None


    try:
        navigation_timeout = target_cfg.get("navigation_timeout_ms", 30000)  # Default to 30 seconds if not set
        api_capture_timeout = navigation_timeout / 2 # Timeout for waiting for the specific API response

        log.debug(f"Ticketmaster [{event_name}]: Navigating to {event_url} (Timeout: {navigation_timeout}ms). Expecting API call to pattern '*{expected_api_url_pattern}*' (Timeout: {api_capture_timeout}ms).")

        async with page.expect_response(lambda resp: expected_api_url_pattern in resp.url and "products" in resp.url, timeout=api_capture_timeout) as response_info:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=navigation_timeout)
            log.info(f"Ticketmaster [{event_name}]: Page navigation to {page.url} complete.")

            human_intensity_tm = target_cfg.get("human_behavior_intensity", "low") # Or "medium" as a default for the new script
            biometric_params_from_config_tm = {}
            # 'profile' here is the BrowserProfile instance passed to check_ticketmaster_event
            if hasattr(profile, 'extra_js_props') and isinstance(profile.extra_js_props, dict):
                biometric_params_from_config_tm = profile.extra_js_props.get("biometric_profile_config", {})

            current_biometric_profile_tm = BiometricProfile(**biometric_params_from_config_tm)
            log.debug(f"Ticketmaster [{event_name}]: Applying advanced human behavior (Intensity: {human_intensity_tm})") # Adjusted log prefix
            await simulate_advanced_human_behavior(page, intensity=human_intensity_tm, profile=current_biometric_profile_tm)



            log.debug(f"Ticketmaster [{event_name}]: Waiting for API response matching pattern: *{expected_api_url_pattern}*")
            api_response_object = await response_info.value

        response_status = api_response_object.status
        raw_response_body = await api_response_object.text()
        log.info(f"Ticketmaster [{event_name}]: Intercepted API call to {api_response_object.url} (Status: {response_status})")

        if response_status != 200:
            page_content_lower = (await page.content(timeout=5000)).lower()
            if response_status == 403 or \
               ("access denied" in page_content_lower or "blocked" in page_content_lower or "pardon our interruption" in page_content_lower or "robot check" in page_content_lower):
                log.warning(f"Ticketmaster [{event_name}]: WAF Block suspected. Main page content or API status indicates block (API Status {response_status}). API URL: {api_response_object.url}. Response: {raw_response_body[:200]}")
                raise BlockedError(f"Ticketmaster: WAF Block (API Status {response_status}, Profile: {profile.name})")
            log.warning(f"Ticketmaster API: Intercepted non-200 status {response_status} (Profile: {profile.name}) from {api_response_object.url}. Resp: {raw_response_body[:300]}")
            # Consider if other non-200 statuses should also raise BlockedError or just return None
            return None

        if not raw_response_body.strip():
            log.warning(f"Ticketmaster API: Intercepted empty response (Profile: {profile.name}, Status: {response_status}) from {api_response_object.url}.")
            return None

        event_data = json.loads(raw_response_body)

    except PlaywrightError as e_pw:
        log_warning_detail = f"Ticketmaster [{event_name}]: Playwright error during page navigation or API interception (Profile: {profile.name}): {type(e_pw).__name__} - {str(e_pw)[:150]}"
        log.warning(log_warning_detail)
        page_blocked = False
        try:
            if page and not page.is_closed():
                page_content_lower = (await page.content()).lower()
                if ("access denied" in page_content_lower or "blocked" in page_content_lower or "pardon our interruption" in page_content_lower or "robot check" in page_content_lower):
                    log.error(f"Ticketmaster [{event_name}]: Playwright error likely due to WAF block on main page. Content indicates block.")
                    page_blocked = True
        except Exception as content_err:
            log.warning(f"Ticketmaster [{event_name}]: Could not get page content after Playwright error: {content_err}")
        
        if page_blocked:
            raise BlockedError(f"Ticketmaster: WAF Block on main page (Profile: {profile.name}, PlaywrightError {type(e_pw).__name__})") from e_pw
        else:
            raise BlockedError(f"Ticketmaster: Playwright Error (Profile: {profile.name}, {type(e_pw).__name__}, {str(e_pw)[:50]})") from e_pw

    except json.JSONDecodeError:
        log.error(f"Ticketmaster API: JSON parse error from intercepted response (Profile: {profile.name}, Status: {response_status}). Resp: {raw_response_body[:500]}")
        raise BlockedError(f"Ticketmaster: Invalid JSON from API (Profile: {profile.name})")
    except BlockedError:
        raise
    except Exception as e_gen:
        log.error(f"Ticketmaster [{event_name}]: Unexpected error during page navigation or API interception (Profile: {profile.name}): {e_gen}", exc_info=True)
        raise BlockedError(f"Ticketmaster: General check error (Profile: {profile.name}, {str(e_gen)[:50]})") from e_gen


    if not event_data:
        log.info(f"Ticketmaster [{event_name}]: No event_data obtained after interception (Profile: {profile.name}).")
        return None

    available_offers = event_data.get("offers", [])
    if not available_offers:
        log.info(f"Ticketmaster [{event_name}]: No 'offers' in API data (Profile: {profile.name}).")
        if gui_q: await gui_q.put(("target_status_update", (event_url, "No offers (API)", False)))
        return None

    desired_sections_raw = target_cfg.get("desired_sections", [])
    desired_sections_lower = [str(s).lower().strip() for s in desired_sections_raw if isinstance(s, str) and s.strip()]
    hits_found: List[Dict[str, Any]] = []

    for offer in available_offers:
        offer_name_original = offer.get("name", "N/A")
        offer_name_lower = offer_name_original.lower()
        offer_availability = str(offer.get("availability", "UNAVAILABLE")).upper()
        offer_status_field = str(offer.get("status", "")).upper() # Explicitly get the "status" field

        if offer_availability == "UNAVAILABLE":
            log.debug(f"Ticketmaster [{event_name}]: Offer '{offer_name_original}' is UNAVAILABLE (via availability field).")
            continue
        
        # Also check the 'status' field for more definitive unavailability cues
        if offer_status_field in ["SOLD_OUT", "NOT_AVAILABLE_YET", "OFF_SALE", "ITEM_LIMIT_EXCEEDED_FOR_CUSTOMER"]:
            log.debug(f"Ticketmaster [{event_name}]: Offer '{offer_name_original}' status is '{offer_status_field}'.")
            continue
        
        # If availability is not UNAVAILABLE and status is not a known unavailable one, consider it potentially available
        # (or at least not explicitly unavailable from the common fields)

        is_desired_section = not desired_sections_lower
        if not is_desired_section:
            for desired_term in desired_sections_lower:
                if desired_term in offer_name_lower:
                    is_desired_section = True; break
        
        if is_desired_section:
            offer_id = offer.get("id")
            if not offer_id:
                log.warning(f"Ticketmaster [{event_name}]: Valid offer has no 'id' (Profile: {profile.name}): {offer_name_original}. Skipped.")
                continue

            price_info = offer.get("price", {})
            price_value = price_info.get("value", "N/A")
            price_currency = price_info.get("currency", "")
            
            hit_message = f"TM: {offer_name_original} - {price_value}{price_currency} (API Avail: {offer_availability}, API Stat: {offer_status_field or 'N/A'})"

            hits_found.append({
                "message": hit_message,
                "offer_id": str(offer_id),
                "offer_url": event_url,
                "platform_specific_data": {
                    "id": str(offer_id),
                    "name": offer_name_original,
                    "price_details": price_info,
                    "availability_status": offer_availability, # From 'availability' field
                    "api_status_field": offer_status_field,    # From 'status' field
                    "raw_offer_object": dict(offer)
                }
            })
            log.warning(f"Ticketmaster HIT [{event_name}] (Profile: {profile.name}): GEVONDEN! {hit_message}")

    if hits_found:
        if gui_q: await gui_q.put(("target_status_update", (event_url, f"HIT! ({len(hits_found)})", True)))
        return hits_found
    else:
        log.info(f"Ticketmaster [{event_name}]: No matching/available tickets after processing API data (Profile: {profile.name}).")
        if gui_q: await gui_q.put(("target_status_update", (event_url, "No match/avail (API)", False)))
        return None