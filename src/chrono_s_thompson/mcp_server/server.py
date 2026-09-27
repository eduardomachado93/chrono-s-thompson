import asyncio
import json
import logging
import sys
from typing import List
from fastmcp import FastMCP


from src.chrono_s_thompson.mcp_server.tools.wikipedia_tool import fetch_on_this_day_events, fetch_event_details

# Logging configuration sending to stderr (to avoid polluting the stdio output used by the MCP)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("ChronoMCPServer")

# Instantiate the FastMCP server
mcp = FastMCP(
    name="Chrono-Historical-Server",
    instructions="MCP Server for retrieving and curating factual historical data and events of the era."
)

@mcp.tool(
    name="get_historical_events",
    description="Returns a list of historical facts that occurred on a specific calendar date (MM/DD format)."
)
async def get_historical_events(date: str) -> str:
    """MCP tool to obtain events from Wikipedia 'On this day'.
    
    Args:
        date: String with the date in 'MM/DD' format (e.g., '08/27' for August 27).
    Returns:
        JSON serialized string containing the list of historical events.
    """
    events = await fetch_on_this_day_events(date)
    return json.dumps([event.model_dump() for event in events], ensure_ascii=False)

@mcp.tool(
    name="get_historical_event_details",
    description="Returns detailed information about a specific historical event."
)
async def get_historical_event_details(page_name: str) -> str:
    """MCP tool to obtain detailed information about a specific historical event.
    
    Args:
        page_name: String identifier for the historical event.
    Returns:
        JSON serialized string containing detailed information about the event.
    """
    event_details = await fetch_event_details(page_name)
    return json.dumps(event_details, ensure_ascii=False)

if __name__ == "__main__":
    logger.info("MCP server running...")
    mcp.run(transport="stdio")
