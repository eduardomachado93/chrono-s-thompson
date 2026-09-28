import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import settings
from src.chrono_s_thompson.core.state import ChronoState, SourceMetadata
from src.chrono_s_thompson.graph.prompts.gonzo_prompts import GONZO_WRITER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", GONZO_WRITER_SYSTEM_PROMPT),
    ("user", """LOCAL/DATA TEMPORAL: {target_date} of {year}
EVENT: {title}
GONZO EDITORIAL HOOK: {hook}

HISTORICAL CONTEXT DOCUMENTS:
{context}

{feedback_section}

Write the full article in your visceral style, weaving the historical reportage and placing inline citations like [S1], [S2] where supported.""")
])

import re

def format_sources_section(article_content: str, sources_map: Dict[str, SourceMetadata]) -> str:
    """Ensures the '### Fontes' section displays the primary page URL at the top and collapsible text snippets for each cited ID."""
    if not sources_map:
        return article_content

    parts = re.split(r'###\s*(Fontes|Sources)', article_content, flags=re.IGNORECASE)
    body = parts[0].strip()

    cited_ids = sorted(list(set(re.findall(r'\[(S\d+)\]', body))), key=lambda x: int(x[1:]))
    if not cited_ids:
        cited_ids = sorted(list(sources_map.keys()), key=lambda x: int(x[1:]))

    first_source = next(iter(sources_map.values()))
    primary_title = first_source.title
    primary_url = first_source.url

    fontes_lines = [
        "### Sources",
        f"**Source Page**: [{primary_title}]({primary_url})\n"
    ]

    for sid in cited_ids:
        if sid in sources_map:
            s_meta = sources_map[sid]
            snippet = s_meta.content.strip()
            quoted = "\n> ".join(snippet.split("\n"))
            fontes_lines.append(
                f"<details>\n<summary><strong>[{sid}] Cited Excerpt</strong></summary>\n\n> {quoted}\n\n</details>\n"
            )

    sources_block = "\n".join(fontes_lines)

    footer_match = re.search(r'(\*— Chrono S\. Thompson.*)', article_content)
    footer = f"\n\n{footer_match.group(1)}" if footer_match else ""

    body = re.sub(r'---\s*###\s*(Fontes|Sources)[\s\S]*$', '', body, flags=re.IGNORECASE).strip()
    body = re.sub(r'\*— Chrono S\. Thompson.*$', '', body, flags=re.IGNORECASE).strip()

    return f"{body}\n\n---\n\n{sources_block}\n\n---\n{footer}".strip()

async def write_article_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for drafting the Gonzo article using retrieved context and stable source IDs.

    Args:
        state: The current state of the pipeline containing `curated_story`, `sources`, `reranked_docs`, `target_date`, `photo_filename`, and optional `verification_feedback`.

    Returns:
        A dictionary with `draft_article` and `sources` to partially mutate ChronoState, or an error payload.
    """
    curated_story = state.curated_story
    if not curated_story:
        return {"error": True, "error_msg": "Error on getting the required states."}

    event = curated_story.selected_event
    target_date = state.target_date

    sources_map: Dict[str, SourceMetadata] = state.sources or {}
    docs = state.reranked_docs or state.retrieved_docs or []

    # Fallback for standalone invocation if sources/docs not pre-populated
    if not sources_map and not docs and state.retriever is not None:
        docs = await state.retriever.ainvoke(curated_story.query_string, **{"k": 12})

    if not sources_map and docs:
        for idx, doc in enumerate(docs, start=1):
            source_id = f"S{idx}"
            meta = getattr(doc, "metadata", {}) or {}
            title = meta.get("title") or event.title
            url = meta.get("url") or f"https://en.wikipedia.org/wiki/{event.page_name}"
            page_name = meta.get("page_name") or event.page_name
            content = doc.page_content if hasattr(doc, "page_content") else str(doc)

            source_obj = SourceMetadata(
                id=source_id,
                title=title,
                url=url,
                page_name=page_name,
                content=content
            )
            sources_map[source_id] = source_obj

    context_blocks = []
    if sources_map:
        for sid, s_meta in sources_map.items():
            context_blocks.append(
                f"[{sid}]\nTitle: {s_meta.title}\nURL: {s_meta.url}\nContent: {s_meta.content}"
            )
        context = "\n\n".join(context_blocks)
    else:
        context = "No specific archival documents found."

    feedback_section = ""
    if state.verification_feedback:
        feedback_section = f"REVISION INSTRUCTIONS (Previous draft failed verification):\n{state.verification_feedback}\n"

    llm = ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        temperature=settings.temperature
    )

    chain = writer_prompt | llm

    try:
        logger.info(f"[Node: writer] Writing Gonzo dispatch draft for: '{event.title}'...")
        response = await chain.ainvoke({
            "target_date": target_date,
            "year": event.year,
            "title": event.title,
            "hook": curated_story.gonzo_hook,
            "context": context,
            "feedback_section": feedback_section,
            "image_filename": state.photo_filename or "default.png"
        })

        raw_article = response.content
        formatted_article = format_sources_section(raw_article, sources_map)

        return {
            "draft_article": formatted_article,
            "sources": sources_map,
        }

    except Exception as exc:
        return {"error": True, "error_msg": f"[Node: writer] Failed to generate article: {exc}"}