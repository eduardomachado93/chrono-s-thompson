#src.chrono_s_thompson.graph.nodes.indexer
import logging
from typing import Any, Dict
from src.chrono_s_thompson.core.state import ChronoState
from src.chrono_s_thompson.mcp_client.client import ChronoMCPClient, MCPClientError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.chrono_s_thompson.core.vector_store import get_retriever
from src.chrono_s_thompson.core.helpers import clean_text
logger = logging.getLogger(__name__)

mcp_client = ChronoMCPClient()

async def index_selected_event(state: ChronoState) -> Dict[str, Any]:
    """
    Indexer Node - Event Indexing and Storage.

    This node is responsible for indexing and storing historical events in a structured format.
    It processes the raw events and prepares them for further analysis or retrieval.
    """
    curated_story = state.curated_story
    if curated_story:
        logger.info("[Node: index_selected_event] Indexing the curated story...")
        try:
            event_details = await mcp_client.get_historical_event_details(curated_story.selected_event.page_name)
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=400,
                chunk_overlap=50,
            )
            event_source = clean_text(event_details.get("source", ""))
            doc_splits = text_splitter.split_text(event_source)
            retriever = get_retriever(docs=tuple(doc_splits))
            return {"detailed_event": event_details, "retriever": retriever}
        except MCPClientError as exc:
            return {"error": True, "error_msg": f"[Node: index_selected_event] Error indexing the curated story: {exc}"}
    return {"error": True, "error_msg": "Curated Story not found."}