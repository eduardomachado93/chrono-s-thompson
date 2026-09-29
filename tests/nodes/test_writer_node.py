"""
Tests for write_article_node graph module.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.embeddings.fake import FakeEmbeddings
from langchain_core.runnables import RunnableSequence
from langchain_core.vectorstores import InMemoryVectorStore

from src.chrono_s_thompson.core.state import (
    ChronoState,
    HistoricalEvent,
    RankedSelection,
)
from src.chrono_s_thompson.graph.nodes.writer import write_article_node


@pytest.mark.asyncio
async def test_write_article_success():
    """Verify write_article_node synthesizes article, saves markdown file, and returns output paths."""
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa reaches its violent climax.",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        ),
        gonzo_hook="The Earth lost its composure and exploded in screams.",
        photo_description="A volcanic eruption spewing ash and lava.",
        query_string="Krakatoa eruption 1883 explosion",
    )
    docs = [
        "The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883 and peaked on 27 August 1883."
    ]
    vs = InMemoryVectorStore.from_texts(texts=docs, embedding=FakeEmbeddings(size=1536))
    retriever = vs.as_retriever()

    test_state = ChronoState(
        target_date="08/27",
        curated_story=ranked_selection,
        retriever=retriever,
        photo_filename="1883_krakatoa_eruption.png",
    )

    mock_ai_msg = MagicMock()
    mock_ai_msg.content = "# GONZO REPORT: KRAKATOA APOCALYPSE\n\nIt was 1883..."

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_ai_msg)):
        result = await write_article_node(test_state)

        assert "draft_article" in result
        assert "sources" in result
        assert "GONZO REPORT: KRAKATOA APOCALYPSE" in result["draft_article"]
        assert "S1" in result["sources"]


@pytest.mark.asyncio
async def test_write_article_missing_state():
    """Verify write_article_node returns error payload when required state (curated_story or retriever) is missing."""
    test_state = ChronoState()
    result = await write_article_node(test_state)

    assert result.get("error") is True
    assert "Curated story not found" in result.get("error_msg", "")


@pytest.mark.asyncio
async def test_write_article_llm_failure():
    """Verify write_article_node handles LLM chain execution failure gracefully."""
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        ),
        gonzo_hook="The Earth exploded in screams.",
        photo_description="A volcanic eruption spewing ash and lava.",
        query_string="Krakatoa eruption",
    )
    vs = InMemoryVectorStore.from_texts(
        texts=["Sample text"], embedding=FakeEmbeddings(size=1536)
    )
    test_state = ChronoState(
        target_date="08/27",
        curated_story=ranked_selection,
        retriever=vs.as_retriever(),
    )

    with patch.object(
        RunnableSequence,
        "ainvoke",
        AsyncMock(side_effect=Exception("OpenAI quota exceeded")),
    ):
        result = await write_article_node(test_state)

        assert result.get("error") is True
        assert "Failed to generate article" in result.get("error_msg", "")
