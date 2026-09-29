"""
Node responsible for validating and re-ranking retrieved historical context documents.
"""
import logging
from typing import Any, Dict

from src.chrono_s_thompson.core.state import ChronoState, SourceMetadata

logger = logging.getLogger(__name__)

async def rerank_context_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for validating and re-ranking vector search results.

    Args:
        state: The current state of the pipeline containing `retrieved_docs` and `curated_story`.

    Returns:
        A dictionary with `reranked_docs` and `sources` to mutate ChronoState, or an error payload.
    """
    retrieved_docs = state.retrieved_docs or []
    curated_story = state.curated_story

    if not curated_story:
        return {"error": True, "error_msg": "[Node: rerank_context] Missing curated story in state."}

    logger.info(f"[Node: rerank_context] Validating and re-ranking {len(retrieved_docs)} retrieved document chunks...")

    event = curated_story.selected_event

    # 1. Validation & Deduplication
    seen_contents = set()
    validated_docs = []

    for doc in retrieved_docs:
        content = doc.page_content if hasattr(doc, "page_content") else str(doc)
        content_strip = content.strip()
        if not content_strip or content_strip in seen_contents:
            continue
        seen_contents.add(content_strip)
        validated_docs.append(doc)

    # 2. Re-ranking: sort by query keyword density and content quality, placing lead document first
    query_words = set(curated_story.query_string.lower().split())

    def score_doc(doc: Any) -> float:
        content = (doc.page_content if hasattr(doc, "page_content") else str(doc)).lower()
        keyword_hits = sum(1 for w in query_words if len(w) > 2 and w in content)
        return keyword_hits * 10 + len(content) * 0.001

    lead_docs = [d for d in validated_docs if getattr(d, "metadata", {}).get("is_lead")]
    other_docs = [d for d in validated_docs if not getattr(d, "metadata", {}).get("is_lead")]
    sorted_others = sorted(other_docs, key=score_doc, reverse=True)

    reranked_docs = (lead_docs + sorted_others)[:8]

    # 3. Build stable source map (S1, S2, ...)
    sources_map: Dict[str, SourceMetadata] = {}
    for idx, doc in enumerate(reranked_docs, start=1):
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

    logger.info(f"[Node: rerank_context] Successfully validated and re-ranked top {len(reranked_docs)} chunks into stable source map.")

    return {
        "reranked_docs": reranked_docs,
        "sources": sources_map,
    }
