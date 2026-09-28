"""
Tests for take_photograph_node graph module.
"""
import base64
from unittest.mock import MagicMock, patch

import pytest

from src.chrono_s_thompson.core.state import (
    ChronoState,
    HistoricalEvent,
    RankedSelection,
)
from src.chrono_s_thompson.graph.nodes.photographer import take_photograph_node


@pytest.mark.asyncio
async def test_take_photograph_success():
    """Verify take_photograph_node generates image file and returns photo_filename & photo_file_path."""
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        ),
        gonzo_hook="The Earth exploded in screams.",
        photo_description="A volcanic eruption spewing ash and lava into the sky.",
        query_string="Krakatoa eruption ash plume",
    )
    test_state = ChronoState(curated_story=ranked_selection)

    fake_b64 = base64.b64encode(b"fake_image_bytes").decode("utf-8")
    mock_img_item = MagicMock()
    mock_img_item.b64_json = fake_b64
    mock_response = MagicMock()
    mock_response.data = [mock_img_item]

    with patch(
        "src.chrono_s_thompson.graph.nodes.photographer.client.images.generate",
        return_value=mock_response,
    ) as mock_gen:
        result = await take_photograph_node(test_state)

        assert "photo_filename" in result
        assert "photo_file_path" in result
        assert result["photo_filename"].endswith(".png")
        assert result["photo_file_path"].exists()
        mock_gen.assert_called_once()


@pytest.mark.asyncio
async def test_take_photograph_missing_curated_story():
    """Verify take_photograph_node returns error payload when curated_story is missing."""
    test_state = ChronoState()
    result = await take_photograph_node(test_state)

    assert result.get("error_msg") is not None
    assert "No curated story available" in result.get("error_msg", "")


@pytest.mark.asyncio
async def test_take_photograph_openai_failure():
    """Verify take_photograph_node returns error state on OpenAI API exception."""
    ranked_selection = RankedSelection(
        selected_event=HistoricalEvent(
            year=1883,
            title="Eruption of Krakatoa",
            page_name="1883_eruption_of_Krakatoa",
            category="General History",
        ),
        gonzo_hook="The Earth exploded in screams.",
        photo_description="A volcanic eruption spewing ash and lava.",
        query_string="Krakatoa eruption ash plume",
    )
    test_state = ChronoState(curated_story=ranked_selection)

    with patch(
        "src.chrono_s_thompson.graph.nodes.photographer.client.images.generate",
        side_effect=Exception("API key error"),
    ):
        result = await take_photograph_node(test_state)

        assert result.get("error") is True
        assert "Failed to generate photo" in result.get("error_msg", "")