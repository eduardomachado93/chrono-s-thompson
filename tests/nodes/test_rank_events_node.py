"""
Tests for rank_events_node graph module.
"""
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables import RunnableSequence

from src.chrono_s_thompson.core.state import (
    ChronoState,
    EventList,
    HistoricalEvent,
    RankedSelection,
)
from src.chrono_s_thompson.graph.nodes.ranker import rank_events_node


@pytest.mark.asyncio
async def test_rank_events_success():
    """Verify rank_events_node returns RankedSelection on valid LLM curation."""
    event1 = HistoricalEvent(
        year=1883,
        title="Eruption of Krakatoa",
        page_name="1883_eruption_of_Krakatoa",
        category="General History",
    )
    event2 = HistoricalEvent(
        year=1963,
        title="I Have a Dream Speech",
        page_name="I_Have_a_Dream",
        category="Civil Rights",
    )
    test_state = ChronoState(batched_events=EventList(events=[event1, event2]))

    mock_ranked = RankedSelection(
        selected_event=event1,
        gonzo_hook="The Earth exploded in violent screams.",
        photo_description="Volcanic eruption plume.",
        query_string="Krakatoa 1883 eruption details",
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_ranked)):
        result = await rank_events_node(test_state)

        assert "curated_story" in result
        assert isinstance(result["curated_story"], RankedSelection)
        assert result["curated_story"].selected_event.year == 1883
        assert result["curated_story"].photo_description == "Volcanic eruption plume."
        assert result["curated_story"].query_string == "Krakatoa 1883 eruption details"


@pytest.mark.asyncio
async def test_rank_events_custom_event():
    """Verify rank_events_node ranks custom_event when provided in ChronoState."""
    custom_evt = HistoricalEvent(
        year=1998,
        title="Google is founded",
        page_name="Google",
        category="Technology",
    )
    test_state = ChronoState(custom_event=custom_evt)

    mock_ranked = RankedSelection(
        selected_event=custom_evt,
        gonzo_hook="Two garage grads index the human mind.",
        photo_description="Vintage computer server in garage.",
        query_string="Google founding 1998 Page Brin",
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_ranked)):
        result = await rank_events_node(test_state)

        assert "curated_story" in result
        assert result["curated_story"].selected_event.title == "Google is founded"


@pytest.mark.asyncio
async def test_rank_events_empty_batched_events():
    """Verify rank_events_node returns error payload when no events are available for ranking."""
    test_state = ChronoState(batched_events=EventList(events=[]))
    result = await rank_events_node(test_state)

    assert result.get("error") is True
    assert "No events available for ranking" in result.get("error_msg", "")