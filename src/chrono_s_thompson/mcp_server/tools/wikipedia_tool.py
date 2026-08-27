import logging
from typing import Any, Dict, List
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


async def fetch_on_this_day_events(date_str: str) -> List[Dict[str, Any]]:
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
    normalized_events: List[Dict[str, Any]] = []

    for item in raw_events:
        year = item.get("year")
        text = item.get("text", "").strip()
        pages = item.get("pages", [])
        
        # Extracts a more detailed summary from the first referenced page, if available
        detailed_extract = pages[0].get("extract", text) if pages else text

        if year and text:
            normalized_events.append({
                "year": year,
                "title": text,
                "description": detailed_extract,
                "category": "General History"
            })

    logger.info(f"Success: {len(normalized_events)} events retrieved for the day {date_str}.")
    return normalized_events