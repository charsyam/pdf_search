from __future__ import annotations

from suki_helper.search.normalizer import normalize_for_search


def test_normalize_for_search_removes_whitespace_and_preserves_mapping() -> None:
    normalized = normalize_for_search("해외 동포")

    assert normalized.normalized_text == "해외동포"
    assert normalized.norm_to_original_map == [0, 1, 3, 4]


def test_normalize_for_search_applies_nfkc_and_lowercasing() -> None:
    normalized = normalize_for_search("Ａ B\tＣ")

    assert normalized.normalized_text == "abc"
    assert normalized.norm_to_original_map == [0, 2, 4]
