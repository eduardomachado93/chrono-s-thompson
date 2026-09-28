"""
Tests for index_selected_event graph module.
"""
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.embeddings.fake import FakeEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from src.chrono_s_thompson.core.state import (
    ChronoState,
    HistoricalEvent,
    RankedSelection,
)
from src.chrono_s_thompson.graph.nodes.indexer import index_selected_event
from src.chrono_s_thompson.mcp_client.client import MCPClientError


@pytest.mark.asyncio
async def test_index_selected_event_success():
    """Verify index_selected_event creates VectorStoreRetriever and returns detailed_event."""
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa reaches its violent climax.",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        ),
        gonzo_hook="The Earth exploded in screams.",
        photo_description="A volcanic eruption spewing ash and lava into the sky.",
        query_string="Volcanic eruption spewing ash and lava",
    )
    test_state = ChronoState(curated_story=ranked_selection)

    mock_details = {
        "title": "1883 eruption of Krakatoa",
        "source": "The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883 and peaked on 27 August 1883.",
    }

    def fake_get_retriever(docs):
        if docs and hasattr(docs[0], "page_content"):
            vs = InMemoryVectorStore.from_documents(
                documents=list(docs), embedding=FakeEmbeddings(size=1536)
            )
        else:
            vs = InMemoryVectorStore.from_texts(
                texts=list(docs), embedding=FakeEmbeddings(size=1536)
            )
        return vs.as_retriever()

    with patch(
        "src.chrono_s_thompson.graph.nodes.indexer.mcp_client.get_historical_event_details",
        new_callable=AsyncMock,
    ) as mock_get_details:
        mock_get_details.return_value = mock_details
        with patch(
            "src.chrono_s_thompson.graph.nodes.indexer.get_retriever",
            side_effect=fake_get_retriever,
        ):
            result = await index_selected_event(test_state)

            assert "detailed_event" in result
            assert "retriever" in result
            assert result["detailed_event"]["title"] == "1883 eruption of Krakatoa"
            assert result["retriever"] is not None

            # Verify retriever functionality and metadata
            retrieved_docs = result["retriever"].invoke("Krakatoa")
            assert len(retrieved_docs) > 0
            assert "Krakatoa" in retrieved_docs[0].page_content
            assert retrieved_docs[0].metadata["page_name"] == "1883_eruption_of_Krakatoa"


@pytest.mark.asyncio
async def test_index_selected_event_missing_curated_story():
    """Verify index_selected_event returns error payload when curated_story is missing."""
    test_state = ChronoState()
    result = await index_selected_event(test_state)

    assert result.get("error") is True
    assert "Curated Story not found" in result.get("error_msg", "")


@pytest.mark.asyncio
async def test_index_selected_event_mcp_failure():
    """Verify index_selected_event returns error state on MCP error."""
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        ),
        gonzo_hook="The Earth exploded in screams.",
        photo_description="A volcanic eruption spewing ash and lava.",
        query_string="Volcanic eruption spewing ash and lava",
    )
    test_state = ChronoState(curated_story=ranked_selection)

    with patch(
        "src.chrono_s_thompson.graph.nodes.indexer.mcp_client.get_historical_event_details",
        side_effect=MCPClientError("Wikipedia API network failure"),
    ):
        result = await index_selected_event(test_state)

        assert result.get("error") is True
        assert "Error indexing the curated story" in result.get("error_msg", "")