"""
Tests for verify_article_node graph module.
"""
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.runnables import RunnableSequence

from src.chrono_s_thompson.core.state import (
    ChronoState,
    ClaimVerification,
    SourceMetadata,
    VerificationReport,
)
from src.chrono_s_thompson.graph.nodes.verifier import verify_article_node


@pytest.fixture
def sample_sources():
    return {
        "S1": SourceMetadata(
            id="S1",
            title="1883 eruption of Krakatoa",
            url="https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            content="The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883.",
        )
    }


@pytest.mark.asyncio
async def test_verifier_valid_citations_success(sample_sources):
    """Verify verify_article_node passes valid draft with cited source IDs and supported claims."""
    draft = """# KRAKATOA APOCALYPSE
The volcano erupted violently in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        cited_ids=["S1"],
        missing_citation_ids=[],
        claims=[
            ClaimVerification(
                claim="The volcano erupted violently in 1883",
                status="supported",
                source_id="S1",
                evidence="The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883.",
            )
        ],
        feedback=None,
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        assert result.get("error") is not True
        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is True
        assert result.get("verification_feedback") is None
        assert "Automated LLM fact-checking" in report.limitation_notice


@pytest.mark.asyncio
async def test_verifier_nonexistent_citation_id(sample_sources):
    """Verify verify_article_node rejects draft containing unattached citation IDs like [S99]."""
    draft = """# KRAKATOA DISPATCH
Alien forces triggered the blast [S99].

---

### Sources
- [S99] [Fake Source](http://example.com)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "S99" in report.missing_citation_ids
        assert "S99" in result.get("verification_feedback", "")
        assert result.get("revision_attempts") == 1


@pytest.mark.asyncio
async def test_verifier_unsupported_claim(sample_sources):
    """Verify verify_article_node fails when claims are unsupported by source evidence."""
    draft = """# KRAKATOA DISPATCH
Napoleon visited Krakatoa during the explosion [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=False,
        claims=[
            ClaimVerification(
                claim="Napoleon visited Krakatoa during the explosion",
                status="unsupported",
                source_id="S1",
            )
        ],
        feedback="Napoleon was dead before 1883.",
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report.is_valid is False
        assert "unsupported" in result.get("verification_feedback", "").lower()


@pytest.mark.asyncio
async def test_verifier_max_attempts_exceeded(sample_sources):
    """Verify verify_article_node returns error payload when maximum revision attempts are reached."""
    draft = """# BAD DISPATCH
The volcano erupted violently [S1].
Unverified claims without valid sources [S99].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=2,  # Already at max attempts
    )

    mock_llm_report = VerificationReport(is_valid=False, claims=[])

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        assert result.get("error") is True
        assert "Fact verification failed after maximum attempts" in result.get("error_msg", "")


@pytest.mark.asyncio
async def test_verifier_llm_failure_blocks_publication(sample_sources, caplog):
    """Verify LLM verification failure results in unverified status (is_valid=False), logs sanitized messages, and halts graph execution without setting feedback."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    fake_secret = "sk-12345678901234567890"
    secret_key_error = f"API connection error: {fake_secret}"
    with patch.object(RunnableSequence, "ainvoke", AsyncMock(side_effect=Exception(secret_key_error))):
        result = await verify_article_node(state)

        assert result.get("error") is True
        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert result.get("verification_feedback") is None
        assert fake_secret not in result.get("error_msg", "")
        assert fake_secret not in caplog.text
        assert "[REDACTED]" in result.get("error_msg", "")
        assert "[REDACTED]" in caplog.text


@pytest.mark.asyncio
async def test_verifier_missing_inline_citations_in_body_rejected(sample_sources):
    """Verify article with valid sources section but no inline citations in body is rejected even if LLM mock returns is_valid=True."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted violently in 1883.

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The volcano erupted violently in 1883",
                status="supported",
                source_id="S1",
                evidence="The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883.",
            )
        ],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "Missing inline citations in the body text" in result.get("verification_feedback", "")

@pytest.mark.asyncio
async def test_verifier_empty_claims_rejected(sample_sources):
    """Verify verify_article_node rejects report with claims=[] when draft has content and inline citations."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[],  # Empty claims list
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "contains no claims to verify" in result.get("verification_feedback", "")


@pytest.mark.asyncio
async def test_verifier_claim_nonexistent_source_id_rejected(sample_sources):
    """Verify verify_article_node rejects report if a claim references a source_id not present in state.sources."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The volcano erupted in 1883",
                status="supported",
                source_id="S999",  # Nonexistent source_id
                evidence="The 1883 eruption of Krakatoa",
            )
        ],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "invalid source_id" in result.get("verification_feedback", "")


@pytest.mark.asyncio
async def test_verifier_claim_empty_evidence_rejected(sample_sources):
    """Verify verify_article_node rejects report if a claim lacks a supporting evidence snippet."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The volcano erupted in 1883",
                status="supported",
                source_id="S1",
                evidence="",  # Empty evidence snippet
            )
        ],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "lacks supporting evidence" in result.get("verification_feedback", "")


@pytest.mark.asyncio
async def test_verifier_claim_mismatched_evidence_rejected(sample_sources):
    """Verify verify_article_node rejects report if evidence snippet is not literally contained in the source content."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The volcano erupted in 1883",
                status="supported",
                source_id="S1",
                evidence="Alien spaceships triggered the eruption on Mars",  # Mismatched snippet
            )
        ],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "was not found in source" in result.get("verification_feedback", "")


@pytest.mark.asyncio
async def test_verifier_claim_unsupported_status_rejected(sample_sources):
    """Verify verify_article_node rejects report if any claim status is unsupported or contradicted."""
    draft = """# KRAKATOA DISPATCH
The volcano erupted in 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The volcano erupted in 1883",
                status="unsupported",
                source_id="S1",
                evidence="The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883.",
            )
        ],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is False
        assert "unsupported status" in result.get("verification_feedback", "")


@pytest.mark.asyncio
async def test_verifier_valid_claim_literal_evidence_success(sample_sources):
    """Verify verify_article_node passes when source_id exists, cited inline in body, status is supported, and literal snippet matches."""
    draft = """# KRAKATOA APOCALYPSE
The eruption began on 20 May 1883 [S1].

---

### Sources
- [S1] [1883 eruption of Krakatoa](https://en.wikipedia.org/wiki/1883_eruption_of_Krakatoa)
"""
    state = ChronoState(
        draft_article=draft,
        sources=sample_sources,
        revision_attempts=0,
    )

    mock_llm_report = VerificationReport(
        is_valid=True,
        claims=[
            ClaimVerification(
                claim="The eruption began on 20 May 1883",
                status="supported",
                source_id="S1",
                evidence="The 1883 eruption of Krakatoa in the Dutch East Indies began on 20 May 1883.",
            )
        ],
    )

    with patch.object(RunnableSequence, "ainvoke", AsyncMock(return_value=mock_llm_report)):
        result = await verify_article_node(state)

        report = result.get("verification_result")
        assert report is not None
        assert report.is_valid is True
        assert result.get("verification_feedback") is None


