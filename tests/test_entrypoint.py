"""
Unit test for the chrono-s-thompson entry point.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from src.chrono_s_thompson import main


def test_entrypoint_main():
    """Verify that calling the entry point invokes the graph pipeline without network or LLM calls."""
    mock_app = MagicMock()
    mock_app.ainvoke = AsyncMock(
        return_value={
            "error": False,
            "published_path": "storage/output/2026-09-28_test_dispatch.md",
        }
    )
    mock_app.get_graph.return_value.draw_ascii.return_value = "Mock Graph Visualization"

    with patch("src.main.build_chrono_graph", return_value=mock_app) as mock_builder:
        main()
        mock_builder.assert_called_once()
        mock_app.ainvoke.assert_called_once()
