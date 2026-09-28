"""
Tests for search_context_node and rerank_context_node.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.documents import Document

from src.chrono_s_thompson.core.state import (
    ChronoState,
    HistoricalEvent,
    RankedSelection,
)
from src.chrono_s_thompson.graph.nodes.reranker import rerank_context_node
from src.chrono_s_thompson.graph.nodes.searcher import search_context_node


@pytest.fixture
def sample_curated_story():
    return RankedSelection(
        selected_event=HistoricalEvent(
            year=1975,
            title="1975 Australian constitutional crisis",
            page_name="1975_Australian_constitutional_crisis",
        ),
        gonzo_hook="The Governor-General sacks the Prime Minister.",
        photo_description="Crowd protesting outside town hall.",
        query_string="Australian constitutional crisis dismissal Whitlam Fraser 1975",
    )


@pytest.mark.asyncio
async def test_search_context_success(sample_curated_story):
    """Verify search_context_node queries vector store retriever and returns retrieved_docs."""
    from langchain_core.embeddings.fake import FakeEmbeddings
    from langchain_core.vectorstores import InMemoryVectorStore

    vs = InMemoryVectorStore.from_texts(
        texts=["Whitlam was dismissed by Kerr in 1975."],
        embedding=FakeEmbeddings(size=1536)
    )
    retriever = vs.as_retriever()

    state = ChronoState(curated_story=sample_curated_story, retriever=retriever)
    result = await search_context_node(state)

    assert result.get("error") is not True
    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) == 1
    assert result["retrieved_docs"][0].page_content == "Whitlam was dismissed by Kerr in 1975."


@pytest.mark.asyncio
async def test_rerank_context_success(sample_curated_story):
    """Verify rerank_context_node validates, ranks, and maps retrieved_docs to sources."""
    docs = [
        Document(
            page_content="Whitlam was dismissed as Prime Minister by Governor-General Sir John Kerr on 11 November 1975.",
            metadata={"title": "1975 Australian constitutional crisis", "url": "https://en.wikipedia.org/wiki/1975_Australian_constitutional_crisis"}
        ),
        Document(
            page_content="Malcolm Fraser was commissioned as caretaker Prime Minister following the dismissal.",
            metadata={"title": "1975 Australian constitutional crisis", "url": "https://en.wikipedia.org/wiki/1975_Australian_constitutional_crisis"}
        ),
        # Duplicate doc
        Document(
            page_content="Whitlam was dismissed as Prime Minister by Governor-General Sir John Kerr on 11 November 1975.",
            metadata={"title": "1975 Australian constitutional crisis", "url": "https://en.wikipedia.org/wiki/1975_Australian_constitutional_crisis"}
        )
    ]

    state = ChronoState(curated_story=sample_curated_story, retrieved_docs=docs)
    result = await rerank_context_node(state)

    assert result.get("error") is not True
    assert "reranked_docs" in result
    assert "sources" in result
    # Duplicate doc should be removed
    assert len(result["reranked_docs"]) == 2
    assert "S1" in result["sources"]
    assert "S2" in result["sources"]
    assert result["sources"]["S1"].id == "S1"
