"""
Unit tests for text cleaning and processing helper functions.
"""
from src.chrono_s_thompson.core.helpers import clean_text


def test_clean_text_removes_section_headers_and_image_captions():
    sample_text = """In the House, desultory debate on Fraser's censure motion ended.
=== Dissolution ===
thumb|250px|Protest in [[George Street, Sydney, outside the Sydney Town Hall, about 6:45 pm 11 November 1975 following news of the dismissal.]]
After the appropriation bills were approved by both Houses, they were sent over to Yarralumla.
Fraser asked that both Houses be dissolved for an election on 13December.
== References ==
Some reference text.
"""

    cleaned = clean_text(sample_text)

    assert "=== Dissolution ===" not in cleaned
    assert "thumb|250px" not in cleaned
    assert "== References ==" not in cleaned
    assert "Some reference text" not in cleaned
    assert "13 December" in cleaned
    assert "George Street" not in cleaned
    assert "desultory debate" in cleaned
