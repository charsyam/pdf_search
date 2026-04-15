from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from suki_helper.search.tokenizer import make_2grams


@dataclass(frozen=True)
class PageIndexData:
    page_number: int
    original_text: str
    normalized_text: str
    offset_map: list[int]
    gram_positions: dict[str, list[int]]


def build_page_index(
    *,
    page_number: int,
    original_text: str,
    normalized_text: str,
    offset_map: list[int],
) -> PageIndexData:
    gram_positions: dict[str, list[int]] = defaultdict(list)

    if len(normalized_text) == 1:
        gram_positions[normalized_text].append(0)
    else:
        for position, gram in enumerate(make_2grams(normalized_text)):
            gram_positions[gram].append(position)

    return PageIndexData(
        page_number=page_number,
        original_text=original_text,
        normalized_text=normalized_text,
        offset_map=offset_map,
        gram_positions=dict(gram_positions),
    )
