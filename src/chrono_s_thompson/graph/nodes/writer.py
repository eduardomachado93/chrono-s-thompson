#src/chrono_s_thompson/graph/nodes/writer.py
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import GONZO_WRITER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=settings.model_name,
    api_key=settings.openai_api_key.get_secret_value(),
    temperature=settings.temperature
)

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", GONZO_WRITER_SYSTEM_PROMPT),
    ("user", """LOCAL/DATA TEMPORAL: {target_date} of {year}
EVENT: {title}
IMPACT DETAILS: {description}
GONZO EDITORIAL HOOK: {hook}

MODERN PARALLEL:
{modern_context}

Write the full article with your visceral style, weaving the historical reportage and final reflexion on contemporary times.""")
])


async def write_article_node(state: ChronoState) -> Dict[str, Any]:
    """Final node for writing and persisting the article in Markdown format.

    Args:
        state: State containing 'curated_story', 'modern_context' and 'target_date'.

    Returns:
        Dictionary with keys 'final_article' and 'published_path'.
    """
    curated_story = state.get("curated_story")
    if not curated_story:
        logger.error("[Node: writer] No curated story available for writing.")
        return {"final_article": None, "published_path": None}

    event = curated_story.selected_event
    hook = curated_story.gonzo_hook
    modern_context = state.get("modern_context", "No registered modern context.")
    target_date = state.get("target_date", "Today")

    logger.info(
        f"[Node: writer] Writing Gonzo dispatch for the event of {event.year}: '{event.title}'..."
    )

    chain = writer_prompt | llm

    try:
        response = await chain.ainvoke({
            "target_date": target_date,
            "year": event.year,
            "title": event.title,
            "description": event.description,
            "hook": hook,
            "modern_context": modern_context,
            "filename": state.get("filename", "No photo available.")
        })

        article_content = str(response.content)

        # Ensure the output directory exists
        output_dir: Path = settings.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate a standard filename: YYYY-MM-DD-YEAR.md
        now_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{now_str}_{event.year}_{safe_title}.md"
        file_path = output_dir / filename

        # Persist the file on disk
        file_path.write_text(article_content, encoding="utf-8")
        logger.info(f"[Node: writer] Article persisted successfully at: {file_path}")

        return {
            "final_article": article_content,
            "published_path": str(file_path)
        }

    except Exception as exc:
        logger.error(f"[Node: writer] Failed to generate the article: {exc}", exc_info=True)
        return {"final_article": None, "published_path": None}