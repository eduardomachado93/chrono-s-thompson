"""
Tests for publish_article_node graph module.
"""
from unittest.mock import patch

import pytest

from src.chrono_s_thompson.core.state import (
    ChronoState,
    HistoricalEvent,
    RankedSelection,
    VerificationReport,
)
from src.chrono_s_thompson.graph.nodes.publisher import publish_article_node


@pytest.mark.asyncio
async def test_publish_article_success(tmp_path):
    """Verify publish_article_node persists verified article to temporary directory."""
    ranked = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
        ),
        gonzo_hook="The Earth exploded.",
        photo_description="Volcanic ash.",
        query_string="Krakatoa",
    )
    draft = "# VERIFIED KRAKATOA DISPATCH\n\nFactual reportage..."
    report = VerificationReport(is_valid=True)

    state = ChronoState(
        draft_article=draft,
        curated_story=ranked,
        verification_result=report,
    )

    with patch("src.chrono_s_thompson.graph.nodes.publisher.settings.articles_dir", str(tmp_path)):
        result = await publish_article_node(state)

        assert "final_article" in result
        assert "published_path" in result
        assert result["final_article"] == draft
        assert result["published_path"].exists()
        assert result["published_path"].read_text(encoding="utf-8") == draft


@pytest.mark.asyncio
async def test_publish_article_unverified_blocked(tmp_path):
    """Verify publish_article_node blocks persistence when verification failed."""
    ranked = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
        ),
        gonzo_hook="The Earth exploded.",
        photo_description="Volcanic ash.",
        query_string="Krakatoa",
    )
    draft = "# UNVERIFIED DISPATCH\n\nFake claims..."
    failed_report = VerificationReport(is_valid=False)

    state = ChronoState(
        draft_article=draft,
        curated_story=ranked,
        verification_result=failed_report,
    )

    with patch("src.chrono_s_thompson.graph.nodes.publisher.settings.articles_dir", str(tmp_path)):
        result = await publish_article_node(state)

        assert result.get("error") is True
        assert "Cannot publish article that failed verification" in result.get("error_msg", "")
        # Ensure no files were published to tmp_path
        assert list(tmp_path.glob("*.md")) == []
