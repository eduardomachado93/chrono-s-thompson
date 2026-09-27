#tests.nodes.test_indexer_node.py
"""
This module contains tests for the fetch_events_node.py module. It sets up a test scenario with a sample ChronoState, then calls the fetch_events_node function
"""
import pytest

from src.chrono_s_thompson.graph.nodes.indexer import index_selected_event
from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent, RankedSelection
from typing import Any, Dict

@pytest.mark.asyncio
async def test_index_selected_event() -> Dict[str, Any]:
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883, 
            title="Eruption of Krakatoa reaches its violent climax.",
            page_name="1883_eruption_of_Krakatoa",
            category="General History"
        ),
        gonzo_hook="Forget rulers and treaties: here the Earth lost its composure, exploded in screams, and showed that nature also knows how to make a power play — with right flames in the sky, killer waves, and a roar so obscene it became a global legend.",
    )
    test_state: ChronoState = {
        "target_date": "08/27",
        "raw_events": [],
        "detailed_event": None,
        "curated_story": ranked_selection,
        "final_article": None,
        "published_path": None,
        "filename": None,
        "custom_event": None,
        "retriever": None
    }
    try:
        return await index_selected_event(test_state)
    except Exception as e:
        print(e)
        return {"raw_events": []}

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_index_selected_event())
    docs = result['retriever'].invoke("Forget rulers and treaties: here the Earth lost its composure, exploded in screams, and showed that nature also knows how to make a power play — with right flames in the sky, killer waves, and a roar so obscene it became a global legend.")
    print(f"Retrieved {len(docs)} documents for the Krakatoa eruption.")