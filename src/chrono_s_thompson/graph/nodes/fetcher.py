#src/chrono_s_thompson/graph/nodes/fetcher.py
"""
Node responsible for fetching historical facts from the MCP Server in the Chrono S. Thompson LangGraph workflow.
"""
import logging
from typing import Any, Dict

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient, MCPClientError

logger = logging.getLogger(__name__)

mcp_client = ChronoMCPClient()

async def fetch_events_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for fetching historical facts via the MCP Server.

    Args:
        state: The current state of the pipeline containing at least `target_date` ('MM/DD').

    Returns:
        A dictionary with the key `raw_events` to partially mutate the ChronoState.
    """
    target_date = state.get("target_date")
    if not target_date:
        logger.error("Target date ('target_date') not found in graph state.")
        return {"raw_events": []}
    if state.get("raw_events") and len(state.get("raw_events")) > 0:
        logger.info("[Node: fetch_events] Raw events already present in state; skipping fetch.")
        return {"raw_events": state.get("raw_events")}
    
    logger.info(f"[Node: fetch_events] Querying MCP Server for the date: {target_date}")

    try:
        events = await mcp_client.get_historical_events(target_date)
        logger.info(
            f"[Node: fetch_events] Success: {len(events)} historical events retrieved via MCP."
        )
        return {"raw_events": events}

    except MCPClientError as exc:
        logger.error(
            f"[Node: fetch_events] Error communicating with the MCP Server: {exc}",
            exc_info=True
        )
        # Return an empty list to avoid abrupt graph interruption
        return {"raw_events": []}