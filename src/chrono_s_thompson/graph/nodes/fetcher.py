"""
Node responsible for fetching historical facts from the MCP Server in the Chrono S. Thompson LangGraph workflow.
"""
import logging
from typing import Any, Dict

from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent
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
    target_date = state.target_date
    if not target_date:
        return {"error": True, "error_msg": "Target date ('target_date') not found in graph state"}
    if state.raw_events and len(state.raw_events) > 0:
        logger.info("[Node: fetch_events] Raw events already present in state; skipping fetch.")
        return {"raw_events": state.raw_events}
    
    logger.info(f"[Node: fetch_events] Querying MCP Server for the date: {target_date}")

    try:
        events = await mcp_client.get_historical_events(target_date)
        events = [
            e if isinstance(e, HistoricalEvent) else HistoricalEvent.model_validate(e)
            for e in events
        ]
        logger.info(
            f"[Node: fetch_events] Success: {len(events)} historical events retrieved via MCP."
        )
        return {"raw_events": events}
    except MCPClientError as exc:
        return {"error": True, "error_msg": f"[Node: fetch_events] Error communicating with the MCP Server: {exc}"}