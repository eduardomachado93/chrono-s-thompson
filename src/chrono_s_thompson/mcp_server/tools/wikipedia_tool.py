import logging
from typing import Any, Dict, List
import httpx

from chrono_s_thompson.core.state import HistoricalEvent
from config.settings import settings

logger = logging.getLogger(__name__)

async def fetch_on_this_day_events(date_str: str) -> List[HistoricalEvent]:
    """Queries the official Wikimedia API to get historical events of the day.
    Args:
        date_str: Date in 'MM/DD' format (e.g., '08/27').
        
    Returns:
        Normalized list containing the main historical facts that occurred on that day.
    """
    try:
        month, day = date_str.strip().split("/")
        # Ensures zero padding if necessary (e.g. '8/9' -> '08/09')
        month = f"{int(month):02d}"
        day = f"{int(day):02d}"
    except (ValueError, AttributeError) as exc:
        logger.error(f"Invalid date format received: '{date_str}'. Expected 'MM/DD'.")
        raise ValueError(f"Invalid date format: '{date_str}'. Use 'MM/DD'.") from exc

    endpoint = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{month}/{day}"
    headers = {
        "User-Agent": settings.wikipedia_user_agent,
        "Accept": "application/json"
    }

    logger.info(f"Fetching historical events for {month}/{day} via Wikimedia API...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, timeout=12.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.error(f"HTTP request failed for the Wikimedia API: {exc}")
            return []
    
    raw_events = data.get("events", [])
    normalized_events: List[HistoricalEvent] = []

    for item in raw_events:
        year = item.get("year")
        text = item.get("text", "").strip()
        pages = item.get("pages", [])
        article_title = pages[0].get("title", text) if pages else ""

        if year and text:
            normalized_events.append(HistoricalEvent(
                year=year,
                title=text,
                page_name=article_title,
                category="General History"
            ))

    logger.info(f"Success: {len(normalized_events)} events retrieved for the day {date_str}.")
    return normalized_events

async def fetch_event_details(page_name: str) -> Dict[str, Any]:
    """Fetches detailed information about a specific historical event from the Wikimedia API.
    
    Args:
        page_name: Unique identifier for the historical event.
    """
    endpoint = f"https://en.wikipedia.org/w/rest.php/v1/page/{page_name}?redirect=true"
    headers = {
        "User-Agent": settings.wikipedia_user_agent,
        "Accept": "application/json"
    }

    logger.info(f"Fetching details for historical event ID: {page_name} via Wikimedia API...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, timeout=12.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.error(f"HTTP request failed for the Wikimedia API: {exc}")
            return {"error": str(exc)}

    return data