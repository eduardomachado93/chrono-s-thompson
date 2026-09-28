"""
Node responsible for persisting verified Gonzo dispatches to disk in the Chrono S. Thompson LangGraph workflow.
"""
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict

from pydantic import FilePath

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState

logger = logging.getLogger(__name__)

async def publish_article_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for persisting the verified article draft to disk.

    Args:
        state: The current state of the pipeline containing `draft_article`, `verification_result`, `curated_story`, and `photo_file_path`.

    Returns:
        A dictionary with `final_article`, `published_path`, and `photo_file_path` to partially mutate ChronoState, or an error payload.
    """
    draft_article = state.draft_article
    verification_result = state.verification_result
    curated_story = state.curated_story

    if not draft_article or not curated_story:
        return {"error": True, "error_msg": "[Node: publish_article] Missing draft article or curated story for publishing."}

    if not verification_result or not verification_result.is_valid:
        return {"error": True, "error_msg": "[Node: publish_article] Cannot publish article that failed verification or is unverified."}

    event = curated_story.selected_event
    output_dir: Path = Path(settings.articles_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{now_str}_{event.year}_{safe_title}.md"
    file_path = output_dir / filename

    try:
        file_path.write_text(draft_article, encoding="utf-8")
        logger.info(f"[Node: publish_article] Article successfully published at: {file_path}")

        return {
            "final_article": draft_article,
            "published_path": FilePath(file_path),
            "photo_file_path": state.photo_file_path,
        }
    except Exception as exc:
        return {"error": True, "error_msg": f"[Node: publish_article] Failed to save article file: {exc}"}
