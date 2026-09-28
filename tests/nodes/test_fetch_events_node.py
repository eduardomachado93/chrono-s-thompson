"""
Tests for fetch_events_node graph module.
"""
from unittest.mock import AsyncMock, patch

import pytest

from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
from src.chrono_s_thompson.mcp_client.client import MCPClientError


@pytest.mark.asyncio
async def test_fetch_events_success():
    """Verify fetch_events_node populates raw_events when mcp_client retrieves data."""
    mock_events = [
        {
            "year": 1883,
            "title": "Eruption of Krakatoa",
            "page_name": "1883_eruption_of_Krakatoa",
            "category": "General History",
        }
    ]
    test_state = ChronoState(target_date="08/27")
    with patch(
        "src.chrono_s_thompson.graph.nodes.fetcher.mcp_client.get_historical_events",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = mock_events
        result = await fetch_events_node(test_state)

        assert "raw_events" in result
        assert len(result["raw_events"]) == 1
        assert result["raw_events"][0]["year"] == 1883
        mock_get.assert_called_once_with("08/27")


@pytest.mark.asyncio
async def test_fetch_events_missing_target_date():
    """Verify fetch_events_node returns error payload when target_date is not set."""
    test_state = ChronoState(target_date="")
    result = await fetch_events_node(test_state)

    assert result.get("error") is True
    assert "Target date ('target_date') not found" in result.get("error_msg", "")


@pytest.mark.asyncio
async def test_fetch_events_mcp_error():
    """Verify fetch_events_node handles MCPClientError gracefully."""
    test_state = ChronoState(target_date="08/27")
    with patch(
        "src.chrono_s_thompson.graph.nodes.fetcher.mcp_client.get_historical_events",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.side_effect = MCPClientError("Subprocess I/O error")
        result = await fetch_events_node(test_state)

        assert result.get("error") is True
        assert "Error communicating with the MCP Server" in result.get("error_msg", "")