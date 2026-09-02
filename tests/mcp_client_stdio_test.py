"""
Teste do Client MCP
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient


async def test_chrono_mcp_client() -> None:
    client = ChronoMCPClient()

    try:
        result = await client.get_historical_events("07/21")
        print(result)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chrono_mcp_client())