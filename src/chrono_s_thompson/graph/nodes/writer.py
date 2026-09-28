"""
Node responsible for generating and persisting Gonzo dispatches in the Chrono S. Thompson LangGraph workflow.
"""
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import FilePath

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import GONZO_WRITER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", GONZO_WRITER_SYSTEM_PROMPT),
    ("user", """LOCAL/DATA TEMPORAL: {target_date} of {year}
EVENT: {title}
GONZO EDITORIAL HOOK: {hook}

HISTORICAL CONTEXT DOCUMENTS:
{context}

Write the full article with your visceral style, weaving the historical reportage.""")
])

async def write_article_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for writing the final Gonzo article using retrieved context and state payload.

    Args:
        state: The current state of the pipeline containing `curated_story`, `retriever`, `target_date`, `photo_filename`, and `photo_file_path`.

    Returns:
        A dictionary with `final_article`, `published_path`, and `photo_file_path` to partially mutate ChronoState, or an error payload.
    """
    curated_story = state.curated_story
    retriever = state.retriever
    if not curated_story or retriever is None:
        return {"error": True, "error_msg": "Error on getting the required states."}

    event = curated_story.selected_event
    query = curated_story.query_string
    target_date = state.target_date
    docs = await retriever.ainvoke(query, **{"k": 12})
    context = "\n\n".join([d.page_content for d in docs]) if docs else "No specific archival documents found."

    llm = ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        temperature=settings.temperature
    )

    chain = writer_prompt | llm

    try:
        logger.info(f"[Node: writer] Writing Gonzo dispatch for: '{event.title}'...")
        response = await chain.ainvoke({
            "target_date": target_date,
            "year": event.year,
            "title": event.title,
            "hook": curated_story.gonzo_hook,
            "context": context,
            "image_filename": state.photo_filename
        })

        article_content = response.content

        output_dir: Path = Path(settings.articles_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{now_str}_{event.year}_{safe_title}.md"
        file_path = output_dir / filename

        file_path.write_text(article_content, encoding="utf-8")
        logger.info(f"[Node: writer] Article persisted successfully at: {file_path}")

        return {
            "final_article": article_content,
            "published_path": FilePath(file_path),
            "photo_file_path": state.photo_file_path
        }

    except Exception as exc:
        return {"error": True, "error_msg": f"[Node: writer] Failed to generate article: {exc}"}