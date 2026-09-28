"""
Main entry point for the Chrono S. Thompson application.
"""
import asyncio
from datetime import datetime
import logging
import sys

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.builder import build_chrono_graph

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("ChronoMain")


async def run_async_main():
    today_str = datetime.now().strftime("%m/%d")
    logger.info(f"🕶️  Starting Chrono S. Thompson dispatch for {today_str}...")

    app = build_chrono_graph()
    print(app.get_graph().draw_ascii())

    initial_state = ChronoState()
    result = await app.ainvoke(initial_state)
    if not result.get("error"):
        print("\n" + "=" * 60)
        print("📰  GONZO DISPATCH PUBLISHED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 File saved to: {result.get('published_path')}\n")
    else:
        print("\n" + "=" * 60)
        print(result.get("error_msg"))

def main():
    """
    runs the async main function
    """
    asyncio.run(run_async_main())

if __name__ == "__main__":  
    main()