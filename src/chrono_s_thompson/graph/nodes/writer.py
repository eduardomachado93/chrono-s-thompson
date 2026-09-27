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
    curated_story = state.get("curated_story")
    if not curated_story:
        logger.error("[Node: writer] No curated story available for writing.")
        return {"final_article": None, "published_path": None}

    retriever = state.get("retriever")
    if retriever is None:
        logger.error("[Node: writer] No retriever available for writing.")
        return {"final_article": None, "published_path": None}

    event = curated_story.selected_event
    hook = curated_story.gonzo_hook
    target_date = state.get("target_date", "Today")
    docs = await retriever.ainvoke(hook, **{"k": 10})
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
            "hook": hook,
            "context": context
        })

        article_content = response.content

        # 2. Persistência em disco
        output_dir: Path = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime("%Y-%m-%d")
        safe_title = "".join(c for c in event.title[:30] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{now_str}_{event.year}_{safe_title}.md"
        file_path = output_dir / filename

        file_path.write_text(article_content, encoding="utf-8")
        logger.info(f"[Node: writer] Article persisted successfully at: {file_path}")

        return {
            "final_article": article_content,
            "published_path": str(file_path)
        }

    except Exception as exc:
        logger.error(f"[Node: writer] Failed to generate article: {exc}", exc_info=True)
        return {"final_article": None, "published_path": None}