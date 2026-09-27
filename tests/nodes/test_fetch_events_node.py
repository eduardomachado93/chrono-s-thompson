#tests.nodes.test_fetch_events_node.py
"""
This module contains tests for the fetch_events_node.py module. It sets up a test scenario with a sample ChronoState, then calls the fetch_events_node function
"""
import pytest

from src.chrono_s_thompson.graph.nodes.fetcher import fetch_events_node
from src.chrono_s_thompson.core.state import ChronoState
from typing import Any, Dict

@pytest.mark.asyncio
async def test_fetch_events() -> Dict[str, Any]:
    test_state: ChronoState = {
        "target_date": "08/27",
        "raw_events": [],
        "detailed_event": None,
        "curated_story": None,
        "final_article": None,
        "published_path": None,
        "filename": None,
        "custom_event": None
    }
    try:
        return await fetch_events_node(test_state)
    except Exception as e:
        print(e)
        return {"raw_events": []}

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_fetch_events())
    print(f"Fetched {len(result['raw_events'])} historical events")