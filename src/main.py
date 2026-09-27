import asyncio
from datetime import datetime
import logging
import sys

from config.settings import settings
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


async def main():
    today_str = datetime.now().strftime("%m/%d")
    logger.info(f"🕶️  Iniciando despacho de Chrono S. Thompson para {today_str}...")

    app = build_chrono_graph()

    initial_state = {
        "target_date": today_str,
        "raw_events": [],
        "curated_story": None,
        "modern_context": None,
        "final_article": None,
        "published_path": None,
    }

    result = await app.ainvoke(initial_state)

    print("\n" + "=" * 60)
    print("📰  DESPACHO GONZO PUBLICADO COM SUCESSO!")
    print("=" * 60)
    print(f"📁 Arquivo salvo em: {result.get('published_path')}\n")
    print(result.get("final_article"))


if __name__ == "__main__":
    asyncio.run(main())