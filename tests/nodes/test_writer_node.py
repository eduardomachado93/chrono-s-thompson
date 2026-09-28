"""
This module contains tests for the writer.py module. It sets up a test scenario with a sample ChronoState, then calls the write_article_node function and verifies the output or handles any exceptions.
"""
import pytest
from typing import Any, Dict

from src.chrono_s_thompson.graph.nodes.writer import write_article_node
from src.chrono_s_thompson.core.state import ChronoState, HistoricalEvent, RankedSelection
from src.chrono_s_thompson.core.vector_store import get_retriever

@pytest.mark.asyncio
async def test_write_article() -> Dict[str, Any]:
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883, 
            title="Eruption of Krakatoa reaches its violent climax.",
            page_name="1883_eruption_of_Krakatoa",
            category="General History"
        ),
        gonzo_hook="Forget rulers and treaties: here the Earth lost its composure, exploded in screams, and showed that nature also knows how to make a power play — with right flames in the sky, killer waves, and a roar so obscene it became a global legend.",
        photo_description="A dramatic, chaotic scene of Krakatoa erupting violently with dark ash clouds and volcanic lightning.",
        query_string="Krakatoa eruption 1883 explosion tsunami impact"
    )
    sample_docs = (
        "The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883 and peaked on 27 August 1883.",
        "Over 70% of the island of Krakatoa and its surrounding archipelago were destroyed as it collapsed into a caldera.",
        "The explosion was heard 3,110 km away in Perth, Western Australia, and is considered one of the loudest sounds in recorded history."
    )
    retriever = get_retriever(docs=sample_docs)
    test_state = ChronoState(
        target_date="08/27",
        curated_story=ranked_selection,
        retriever=retriever,
        photo_filename="1883_krakatoa_eruption.jpg"
    )
    try:
        result = await write_article_node(test_state)
        return result
    except Exception as e:
        print(e)
        return {"error": True, "error_msg": str(e)}

@pytest.mark.asyncio
async def test_write_article_missing_state() -> Dict[str, Any]:
    test_state = ChronoState()
    result = await write_article_node(test_state)
    assert result.get("error") is True
    return result

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_write_article())
    if result and "final_article" in result and result["final_article"]:
        print(f"\n--- Final Article Generated ---\n")
        print(result["final_article"][:500] + "...\n")
        print(f"Published Path: {result.get('published_path')}")
    else:
        print(f"Failed to generate article: {result.get('error_msg')}")
