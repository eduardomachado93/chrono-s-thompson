"""
Node responsible for querying the vector store to search relevant historical context.
"""
import logging
from typing import Any, Dict

from src.chrono_s_thompson.core.state import ChronoState

logger = logging.getLogger(__name__)

async def search_context_node(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for performing semantic search in the vector store.

    Args:
        state: The current state of the pipeline containing `retriever` and `curated_story`.

    Returns:
        A dictionary with `retrieved_docs` to mutate ChronoState, or an error payload.
    """
    curated_story = state.curated_story
    retriever = state.retriever

    if not curated_story or retriever is None:
        return {"error": True, "error_msg": "[Node: search_context] Missing curated story or retriever in state."}

    query = curated_story.query_string
    logger.info(f"[Node: search_context] Performing vector search for query: '{query}'...")

    try:
        docs = await retriever.ainvoke(query, **{"k": 12})
        logger.info(f"[Node: search_context] Vector search returned {len(docs)} document chunks.")
        return {"retrieved_docs": docs}
    except Exception as exc:
        return {"error": True, "error_msg": f"[Node: search_context] Vector store search failed: {exc}"}
