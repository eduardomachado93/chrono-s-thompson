"""
This module contains tests for the rank_events_node.py module. It sets up a test scenario with a sample ChronoState, then calls the rank_events_node function and prints the result or any exceptions that occur.
"""
import pytest

from src.chrono_s_thompson.graph.nodes.ranker import rank_events_node
from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent, EventList
from typing import Any, Dict

@pytest.mark.asyncio
async def test_rank_events() -> Dict[str, Any]:
    historical_event1 = HistoricalEvent(
                    year=1883,
                    title="Eruption of Krakatoa reaches its violent climax.",
                    page_name="The catastrophic volcanic explosion generated the loudest sound in recorded history...",
                    category="General History"
                )
    historical_event2 = HistoricalEvent(
                    year=1963,
                    title="Martin Luther King Jr. delivers his 'I Have a Dream' speech.",
                    page_name="During the March on Washington for Jobs and Freedom, Martin Luther King Jr. delivered his iconic speech...",
                    category="Civil Rights"
                )
    test_state = ChronoState(
        batched_events=EventList(events=[historical_event1, historical_event2]),
    )
    try:
        return await rank_events_node(test_state)
    except Exception as e:
        print(e)
        return {"curated_story": None}

@pytest.mark.asyncio
async def test_rank_events_custom_event() -> Dict[str, Any]:
    custom_evt = HistoricalEvent(
        year=1998,
        title="Google is founded by Larry Page and Sergey Brin.",
        page_name="Google",
        category="Technology"
    )
    test_state = ChronoState(custom_event=custom_evt)
    result = await rank_events_node(test_state)
    assert "curated_story" in result
    return result

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_rank_events())
    if result and "curated_story" in result and result["curated_story"]:
        print(f"Ranked Event: {result['curated_story'].selected_event.title}")
    else:
        print("No ranked event found.")