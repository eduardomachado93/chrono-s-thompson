"""
Test client for ChronoMCPClient using standard input/output.
"""
import sys
import random
from pathlib import Path

import pytest
sys.path.append(str(Path(__file__).parent.parent))
from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient
from typing import List

@pytest.mark.asyncio
async def test_chrono_mcp_client() -> List[dict]:
    """
    Test the ChronoMCPClient by fetching historical events for a specific date.
    """
    client = ChronoMCPClient()
    try:
        return await client.get_historical_events("08/27")
    except Exception as e:
        print(e)
        return []

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_chrono_mcp_client())
    print(f"Fetched {len(result)} historical events")
    print("Sample event:", result[random.randint(0, len(result) - 1)] if result else "No events found")