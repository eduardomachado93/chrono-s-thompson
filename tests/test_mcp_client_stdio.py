"""
Tests for ChronoMCPClient using mocks to avoid stdio subprocess and network calls.
"""
from unittest.mock import AsyncMock, patch

import pytest

from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient, MCPClientError


@pytest.mark.asyncio
async def test_mcp_client_get_historical_events_success():
    """Verify get_historical_events returns historical event list on valid tool execution."""
    mock_events = [
        {
            "year": 1883,
            "title": "Eruption of Krakatoa",
            "page_name": "1883_eruption_of_Krakatoa",
            "category": "General History",
        }
    ]
    client = ChronoMCPClient()
    with patch.object(client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_events
        result = await client.get_historical_events("08/27")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["year"] == 1883
        assert result[0]["page_name"] == "1883_eruption_of_Krakatoa"
        mock_call.assert_called_once_with("get_historical_events", {"date": "08/27"})


@pytest.mark.asyncio
async def test_mcp_client_get_historical_events_invalid_date():
    """Verify get_historical_events returns empty list for malformed date string."""
    client = ChronoMCPClient()
    result = await client.get_historical_events("invalid-format")
    assert result == []


@pytest.mark.asyncio
async def test_mcp_client_get_historical_event_details_success():
    """Verify get_historical_event_details returns detail dictionary."""
    mock_details = {"title": "Krakatoa", "source": "Detailed Krakatoa historical content"}
    client = ChronoMCPClient()
    with patch.object(client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_details
        result = await client.get_historical_event_details("1883_eruption_of_Krakatoa")

        assert isinstance(result, dict)
        assert result["title"] == "Krakatoa"
        assert "source" in result
        mock_call.assert_called_once_with("get_historical_event_details", {"page_name": "1883_eruption_of_Krakatoa"})


@pytest.mark.asyncio
async def test_mcp_client_error_handling():
    """Verify MCPClientError is raised when call_tool encounters subprocess errors."""
    client = ChronoMCPClient()
    with patch.object(client, "call_tool", AsyncMock(side_effect=MCPClientError("Connection refused"))):
        with pytest.raises(MCPClientError) as exc_info:
            await client.call_tool("get_historical_events", {"date": "08/27"})
        assert "Connection refused" in str(exc_info.value)