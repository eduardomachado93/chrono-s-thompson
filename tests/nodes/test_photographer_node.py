#tests.nodes.test_photographer_node.py
"""
This is a test file for the take_photograph_node function in the photographer graph module. It sets up a test scenario with a sample ranked selection and a ChronoState, then calls the take_photograph_node function and prints the result or any exceptions that occur.
"""
import pytest

from src.chrono_s_thompson.graph.nodes.photographer import take_photograph_node
from src.chrono_s_thompson.core.state import ChronoState, RankedSelection, HistoricalEvent
from typing import Any, Dict

@pytest.mark.asyncio
async def test_take_photograph() -> Dict[str, Any]:
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883, 
            title="Eruption of Krakatoa reaches its violent climax.",
            page_name="1883_eruption_of_Krakatoa",
            category="General History"
        ),
        gonzo_hook="Forget rulers and treaties: here the Earth lost its composure, exploded in screams, and showed that nature also knows how to make a power play — with right flames in the sky, killer waves, and a roar so obscene it became a global legend.",
    )
    test_photographer_state: ChronoState = {
        "target_date": "08/27",
        "raw_events": [],
        "detailed_event": None,
        "curated_story": ranked_selection,
        "final_article": None,
        "published_path": None,
        "filename": None,
        "custom_event": None
    }
    try:
        result = await take_photograph_node(test_photographer_state)
        return result
    except Exception as e:
        print(e)
        return {"filename": None}

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_take_photograph())