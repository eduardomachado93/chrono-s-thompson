"""
Integration test for the full LangGraph pipeline workflow including generation, verification, and publication.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.embeddings.fake import FakeEmbeddings
from langchain_core.runnables import RunnableSequence
from langchain_core.vectorstores import InMemoryVectorStore

from src.chrono_s_thompson.core.state import (
    ChronoState,
    ClaimVerification,
    EventList,
    HistoricalEvent,
    RankedSelection,
    VerificationReport,
)
from src.chrono_s_thompson.graph.builder import build_chrono_graph


@pytest.mark.asyncio
async def test_full_graph_success_flow(tmp_path):
    """Verify end-to-end execution of the full graph from fetch to publish when verification passes."""
    mock_raw_events = [
        HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        )
    ]
    mock_batch = EventList(events=mock_raw_events)
    mock_rank = RankedSelection(
        selected_event=mock_raw_events[0],
        gonzo_hook="The Earth exploded.",
        photo_description="Volcanic ash spewing into the sky.",
        query_string="Krakatoa eruption",
    )
    mock_details = {
        "title": "1883 eruption of Krakatoa",
        "page_name": "1883_eruption_of_Krakatoa",
        "url": "https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa",
        "source": "The 1883 eruption of Krakatoa began on 20 May 1883.",
    }

    mock_draft_msg = MagicMock()
    mock_draft_msg.content = """# KRAKATOA APOCALYPSE
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""

    mock_valid_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The volcano erupted in 1883",
                status="supported",
                source_id="S1",
                evidence="The 1883 eruption of Krakatoa began on 20 May 1883.",
            )
        ],
    )

    def fake_get_retriever(docs):
        if docs and hasattr(docs[0], "page_content"):
            vs = InMemoryVectorStore.from_documents(documents=list(docs), embedding=FakeEmbeddings(size=1536))
        else:
            vs = InMemoryVectorStore.from_texts(texts=list(docs), embedding=FakeEmbeddings(size=1536))
        return vs.as_retriever()

    mock_image_result = MagicMock()
    mock_image_result.data = [MagicMock(b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")]

    with patch("src.chrono_s_thompson.graph.nodes.fetcher.mcp_client.get_historical_events", new_callable=AsyncMock) as mock_fetch, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.mcp_client.get_historical_event_details", new_callable=AsyncMock) as mock_get_details, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.get_retriever", side_effect=fake_get_retriever), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.client.images.generate", return_value=mock_image_result), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.settings.images_dir", tmp_path), \
         patch("src.chrono_s_thompson.graph.nodes.publisher.settings.articles_dir", str(tmp_path)), \
         patch.object(RunnableSequence, "ainvoke") as mock_chain_ainvoke:

        mock_fetch.return_value = [e.model_dump() for e in mock_raw_events]
        mock_get_details.return_value = mock_details

        # Sequence of LLM calls across nodes:
        # 1. ranker structured RankedSelection
        # 2. writer draft_article
        # 3. verifier structured VerificationReport
        mock_chain_ainvoke.side_effect = [
            mock_rank,
            mock_draft_msg,
            mock_valid_report,
        ]

        app = build_chrono_graph()
        initial_state = ChronoState(target_date="08/27")
        result = await app.ainvoke(initial_state)

        assert result.get("error") is False
        assert "final_article" in result
        assert "published_path" in result
        assert result["published_path"].exists()


@pytest.mark.asyncio
async def test_full_graph_empty_claims_blocks_publication(tmp_path):
    """Verify that a verification report returning empty claims (claims=[]) fails verification and prevents article publication."""
    mock_raw_events = [
        HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
        )
    ]
    mock_rank = RankedSelection(
        selected_event=mock_raw_events[0],
        gonzo_hook="The Earth exploded.",
        photo_description="Volcanic ash.",
        query_string="Krakatoa",
    )
    mock_details = {
        "title": "1883 eruption of Krakatoa",
        "page_name": "1883_eruption_of_Krakatoa",
        "url": "https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa",
        "source": "The 1883 eruption of Krakatoa began on 20 May 1883.",
    }

    mock_draft_msg = MagicMock()
    mock_draft_msg.content = """# KRAKATOA APOCALYPSE
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""

    mock_empty_claims_report = VerificationReport(
        is_valid=True,
        claims=[],  # Incomplete report without verified claims
    )

    def fake_get_retriever(docs):
        if docs and hasattr(docs[0], "page_content"):
            vs = InMemoryVectorStore.from_documents(documents=list(docs), embedding=FakeEmbeddings(size=1536))
        else:
            vs = InMemoryVectorStore.from_texts(texts=list(docs), embedding=FakeEmbeddings(size=1536))
        return vs.as_retriever()

    mock_image_result = MagicMock()
    mock_image_result.data = [MagicMock(b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")]

    with patch("src.chrono_s_thompson.graph.nodes.fetcher.mcp_client.get_historical_events", new_callable=AsyncMock) as mock_fetch, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.mcp_client.get_historical_event_details", new_callable=AsyncMock) as mock_get_details, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.get_retriever", side_effect=fake_get_retriever), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.client.images.generate", return_value=mock_image_result), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.settings.images_dir", tmp_path), \
         patch("src.chrono_s_thompson.graph.nodes.publisher.settings.articles_dir", str(tmp_path)), \
         patch.object(RunnableSequence, "ainvoke") as mock_chain_ainvoke:

        mock_fetch.return_value = [e.model_dump() for e in mock_raw_events]
        mock_get_details.return_value = mock_details

        # Sequence of LLM calls across nodes:
        mock_chain_ainvoke.side_effect = [
            mock_rank,
            mock_draft_msg,
            mock_empty_claims_report,
            mock_draft_msg,
            mock_empty_claims_report,
            mock_draft_msg,
            mock_empty_claims_report,
        ]

        app = build_chrono_graph()
        initial_state = ChronoState(target_date="08/27")
        result = await app.ainvoke(initial_state)

        assert result.get("error") is True
        assert "Fact verification failed after maximum attempts" in result.get("error_msg", "")
        # Confirm no Markdown file was created
        assert list(tmp_path.glob("*.md")) == []


@pytest.mark.asyncio
async def test_full_graph_verification_failure_blocks_publish(tmp_path):
    """Verify that failed verification blocks article publication after maximum revision attempts."""
    mock_raw_events = [
        HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
        )
    ]
    mock_rank = RankedSelection(
        selected_event=mock_raw_events[0],
        gonzo_hook="The Earth exploded.",
        photo_description="Volcanic ash.",
        query_string="Krakatoa",
    )
    mock_details = {
        "title": "1883 eruption of Krakatoa",
        "page_name": "1883_eruption_of_Krakatoa",
        "url": "https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa",
        "source": "The 1883 eruption of Krakatoa began on 20 May 1883.",
    }

    mock_draft_msg = MagicMock()
    mock_draft_msg.content = "# BAD DISPATCH\nClaims without valid citations [S99]."

    mock_invalid_report = VerificationReport(
        is_valid=False,
        missing_citation_ids=["S99"],
        feedback="Citation [S99] does not exist.",
    )

    def fake_get_retriever(docs):
        if docs and hasattr(docs[0], "page_content"):
            vs = InMemoryVectorStore.from_documents(documents=list(docs), embedding=FakeEmbeddings(size=1536))
        else:
            vs = InMemoryVectorStore.from_texts(texts=list(docs), embedding=FakeEmbeddings(size=1536))
        return vs.as_retriever()

    mock_image_result = MagicMock()
    mock_image_result.data = [MagicMock(b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")]

    with patch("src.chrono_s_thompson.graph.nodes.fetcher.mcp_client.get_historical_events", new_callable=AsyncMock) as mock_fetch, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.mcp_client.get_historical_event_details", new_callable=AsyncMock) as mock_get_details, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.get_retriever", side_effect=fake_get_retriever), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.client.images.generate", return_value=mock_image_result), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.settings.images_dir", tmp_path), \
         patch("src.chrono_s_thompson.graph.nodes.publisher.settings.articles_dir", str(tmp_path)), \
         patch.object(RunnableSequence, "ainvoke") as mock_chain_ainvoke:

        mock_fetch.return_value = [e.model_dump() for e in mock_raw_events]
        mock_get_details.return_value = mock_details

        # Mock LLM sequence calls:
        # 1. ranker structured
        # attempt 0: writer draft, verifier report (fails) -> revision 1
        # attempt 1: writer draft, verifier report (fails) -> revision 2
        # attempt 2: writer draft, verifier report (fails) -> max attempts reached -> error
        mock_chain_ainvoke.side_effect = [
            mock_rank,
            mock_draft_msg,
            mock_invalid_report,
            mock_draft_msg,
            mock_invalid_report,
            mock_draft_msg,
            mock_invalid_report,
        ]

        app = build_chrono_graph()
        initial_state = ChronoState(target_date="08/27")
        result = await app.ainvoke(initial_state)

        assert result.get("error") is True
        assert "Fact verification failed after maximum attempts" in result.get("error_msg", "")
        # Confirm no article was written to tmp_path
        assert list(tmp_path.glob("*.md")) == []


@pytest.mark.asyncio
async def test_full_graph_verifier_llm_service_error_blocks_publication(tmp_path):
    """Verify that an unexpected LLM service error during verification immediately halts full graph execution without writing a Markdown file."""
    mock_raw_events = [
        HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
        )
    ]
    mock_rank = RankedSelection(
        selected_event=mock_raw_events[0],
        gonzo_hook="The Earth exploded.",
        photo_description="Volcanic ash.",
        query_string="Krakatoa",
    )
    mock_details = {
        "title": "1883 eruption of Krakatoa",
        "page_name": "1883_eruption_of_Krakatoa",
        "url": "https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa",
        "source": "The 1883 eruption of Krakatoa began on 20 May 1883.",
    }

    mock_draft_msg = MagicMock()
    mock_draft_msg.content = """# KRAKATOA APOCALYPSE
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""

    def fake_get_retriever(docs):
        if docs and hasattr(docs[0], "page_content"):
            vs = InMemoryVectorStore.from_documents(documents=list(docs), embedding=FakeEmbeddings(size=1536))
        else:
            vs = InMemoryVectorStore.from_texts(texts=list(docs), embedding=FakeEmbeddings(size=1536))
        return vs.as_retriever()

    mock_image_result = MagicMock()
    mock_image_result.data = [MagicMock(b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")]

    with patch("src.chrono_s_thompson.graph.nodes.fetcher.mcp_client.get_historical_events", new_callable=AsyncMock) as mock_fetch, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.mcp_client.get_historical_event_details", new_callable=AsyncMock) as mock_get_details, \
         patch("src.chrono_s_thompson.graph.nodes.indexer.get_retriever", side_effect=fake_get_retriever), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.client.images.generate", return_value=mock_image_result), \
         patch("src.chrono_s_thompson.graph.nodes.photographer.settings.images_dir", tmp_path), \
         patch("src.chrono_s_thompson.graph.nodes.publisher.settings.articles_dir", str(tmp_path)), \
         patch.object(RunnableSequence, "ainvoke") as mock_chain_ainvoke:

        mock_fetch.return_value = [e.model_dump() for e in mock_raw_events]
        mock_get_details.return_value = mock_details

        # Sequence of LLM calls across nodes:
        # 1. ranker structured
        # 2. writer draft_article
        # 3. verifier raises LLM service Exception!
        mock_chain_ainvoke.side_effect = [
            mock_rank,
            mock_draft_msg,
            Exception("OpenAI API service outage: sk-99999999999999999999"),
        ]

        app = build_chrono_graph()
        initial_state = ChronoState(target_date="08/27")
        result = await app.ainvoke(initial_state)

        assert result.get("error") is True
        assert "Fact verification service failed" in result.get("error_msg", "")
        assert "sk-99999999999999999999" not in result.get("error_msg", "")
        # Confirm no Markdown dispatch was generated or saved to disk
        assert list(tmp_path.glob("*.md")) == []
