from __future__ import annotations

from suki_helper.search.ngram_index import build_page_index
from suki_helper.search.tokenizer import make_2grams


def test_make_2grams_returns_overlapping_pairs() -> None:
    assert make_2grams("해외동포") == ["해외", "외동", "동포"]


def test_build_page_index_tracks_gram_positions() -> None:
    page_index = build_page_index(
        page_number=1,
        original_text="해외 동포",
        normalized_text="해외동포",
        offset_map=[0, 1, 3, 4],
    )

    assert page_index.gram_positions == {
        "해외": [0],
        "외동": [1],
        "동포": [2],
    }
