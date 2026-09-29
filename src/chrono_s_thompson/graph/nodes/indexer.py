"""
Node responsible for indexing Wikipedia context into an in-memory vector store in the Chrono S. Thompson LangGraph workflow.
"""
import logging
from typing import Any, Dict

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.chrono_s_thompson.core.state import ChronoState, DetailedEvent
from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient, MCPClientError
from src.chrono_s_thompson.core.vector_store import get_retriever
from src.chrono_s_thompson.core.helpers import clean_text
logger = logging.getLogger(__name__)

mcp_client = ChronoMCPClient()

async def index_selected_event(state: ChronoState) -> Dict[str, Any]:
    """Node in the LangGraph responsible for indexing detailed Wikipedia context for the curated story.

    Args:
        state: The current state of the pipeline containing `curated_story`.

    Returns:
        A dictionary with `detailed_event` and `retriever` to partially mutate ChronoState, or an error payload.
    """
    curated_story = state.curated_story
    if curated_story:
        logger.info("[Node: index_selected_event] Indexing the curated story...")
        try:
            page_name = curated_story.selected_event.page_name
            raw_details = await mcp_client.get_historical_event_details(page_name)

            if isinstance(raw_details, DetailedEvent):
                detailed_event = raw_details
            elif isinstance(raw_details, dict):
                detailed_event = DetailedEvent(
                    title=raw_details.get("title") or curated_story.selected_event.title,
                    source=raw_details.get("source") or "",
                    page_name=raw_details.get("page_name") or page_name,
                    url=raw_details.get("url") or f"https://en.wikipedia.org/wiki/{page_name}",
                )
            else:
                detailed_event = DetailedEvent(
                    title=curated_story.selected_event.title,
                    source="",
                    page_name=page_name,
                    url=f"https://en.wikipedia.org/wiki/{page_name}",
                )

            title = detailed_event.title or curated_story.selected_event.title
            url = detailed_event.url or f"https://en.wikipedia.org/wiki/{page_name}"

            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=400,
                chunk_overlap=50,
            )
            event_source = clean_text(detailed_event.source)
            doc_splits = text_splitter.split_text(event_source)

            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "title": title,
                        "url": url,
                        "page_name": page_name,
                        "is_lead": (idx == 0),
                    }
                )
                for idx, chunk in enumerate(doc_splits)
            ]

            retriever = get_retriever(docs=documents)
            return {"detailed_event": detailed_event, "retriever": retriever}
        except MCPClientError as exc:
            return {"error": True, "error_msg": f"[Node: index_selected_event] Error indexing the curated story: {exc}"}
    return {"error": True, "error_msg": "[Node: index_selected_event] Curated story not found. in state"}