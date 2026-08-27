import asyncio
import json
import logging
import sys
from typing import List
from mcp.server.fastmcp import FastMCP
import json

from src.chrono_s_thompson.mcp_server.tools.wikipedia_tool import fetch_on_this_day_events

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
    return json.dumps(events, ensure_ascii=False)


if __name__ == "__main__":
    logger.info("MCP server running...")
    mcp.run(transport="stdio")
