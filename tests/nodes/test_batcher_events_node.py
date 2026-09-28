"""
Tests for batch_events_node graph module.
"""
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables import RunnableSequence

from src.chrono_s_thompson.core.state import ChronoState, EventList, HistoricalEvent
from src.chrono_s_thompson.graph.nodes.batcher import batch_events_node


@pytest.mark.asyncio
async def test_batch_events_success_small_list():
    """Verify batch_events_node returns candidates directly when event count <= 10."""
    events = [
        HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        )
    ]
    test_state = ChronoState(raw_events=events)
    result = await batch_events_node(test_state)

    assert "batched_events" in result
    assert isinstance(result["batched_events"], EventList)
    assert len(result["batched_events"].events) == 1
    assert result["batched_events"].events[0].year == 1883


@pytest.mark.asyncio
async def test_batch_events_success_large_list_with_mock():
    """Verify batch_events_node uses structured LLM chain when event count > 10."""
    events = [
        HistoricalEvent(
            year=1800 + i,
            title=f"Event {i}",
            page_name=f"Page_{i}",
            category="History",
        )
        for i in range(15)
    ]
    test_state = ChronoState(raw_events=events)
    mock_batch_res = EventList(events=events[:5])

    with patch.object(
        RunnableSequence,
        "ainvoke",
        AsyncMock(return_value=mock_batch_res),
    ):
        result = await batch_events_node(test_state)

        assert "batched_events" in result
        assert isinstance(result["batched_events"], EventList)
        assert len(result["batched_events"].events) > 0


@pytest.mark.asyncio
async def test_batch_events_custom_event():
    """Verify batch_events_node preserves custom_event override when provided."""
    custom_evt = HistoricalEvent(
        year=1969,
        title="Apollo 11 Moon Landing",
        page_name="Apollo_11",
        category="Space",
    )
    test_state = ChronoState(raw_events=[custom_evt], custom_event=custom_evt)
    result = await batch_events_node(test_state)

    assert "batched_events" in result
    assert result["batched_events"].events == [custom_evt]


@pytest.mark.asyncio
async def test_batch_events_empty_raw_events():
    """Verify batch_events_node returns error state payload when raw_events is empty."""
    test_state = ChronoState(raw_events=[])
    result = await batch_events_node(test_state)

    assert result.get("error") is True
    assert "No events available" in result.get("error_msg", "")