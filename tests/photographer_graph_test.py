"""
Photographer Graph Test
"""
from src.chrono_s_thompson.graph.nodes.photographer import take_photograph_node
from src.chrono_s_thompson.core.state import ChronoState, RankedSelection, HistoricalEvent

async def test_take_photograph() -> None:
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883, 
            title="Eruption of Krakatoa reaches its violent climax.",
            description="The catastrophic volcanic explosion generated the loudest sound in recorded history...",
            category="General History"
        ),
        gonzo_hook="Forget rulers and treaties: here the Earth lost its composure, exploded in screams, and showed that nature also knows how to make a power play — with right flames in the sky, killer waves, and a roar so obscene it became a global legend.",
        suggested_modern_topic="Extreme climate crises and our era of ignored alerts, mega-disasters and environmental collapse treated as just another notification on your cell phone."
    )
    test_photographer_state: ChronoState = {
        "target_date": "08/27",
        "raw_events": [],
        "curated_story": ranked_selection,
        "modern_context": None,
        "final_article": None,
        "published_path": None
    }
    try:
        result = await take_photograph_node(test_photographer_state)
        print(result)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_take_photograph())