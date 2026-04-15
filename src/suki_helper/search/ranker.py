from __future__ import annotations

from dataclasses import dataclass
import math


SEPARATOR_CHARACTERS = {" ", "\t", "\n", "\r", "-", "_", "/", ".", ","}


@dataclass(frozen=True)
class RankedMatch:
    exact_compact_match: bool
    adjacent_token_match: bool
    ordered_token_match: bool
    adjacency_rank: int
    ordered_gap_chars: int
    ordered_span_length: int
    proximity_score: float
    gram_overlap_score: float
    rarity_score: float
    first_match_offset: int
    compact_start: int
    compact_end: int
    ordered_span_start: int
    ordered_span_end: int


@dataclass(frozen=True)
class OrderedTokenSpan:
    span_start: int
    span_end: int
    total_gap_chars: int
    token_boundaries: list[tuple[int, int]]
    separator_only: bool


def find_compact_match(
    normalized_page_text: str,
    normalized_query_text: str,
) -> tuple[int, int] | None:
    if not normalized_query_text:
        return None
    start = normalized_page_text.find(normalized_query_text)
    if start < 0:
        return None
    return start, start + len(normalized_query_text)


def score_ranked_match(
    *,
    original_text: str,
    normalized_page_text: str,
    normalized_query_text: str,
    query_tokens: list[str],
    gram_overlap_score: float,
    rarity_score: float,
    require_ordered_match: bool = False,
    separator_only_match: bool = False,
    max_gap_chars: int | None = None,
) -> RankedMatch | None:
    compact_span = find_compact_match(normalized_page_text, normalized_query_text)
    compact_start = compact_span[0] if compact_span is not None else -1
    compact_end = compact_span[1] if compact_span is not None else -1
    exact_compact_match = compact_span is not None

    ordered_span = _find_best_ordered_token_span(
        original_text,
        query_tokens,
        separator_only_match=separator_only_match,
        max_gap_chars=max_gap_chars,
    )
    adjacent_token_match = False
    ordered_token_match = False
    adjacency_rank = 0
    ordered_gap_chars = 10**9
    ordered_span_length = 10**9
    proximity_score = 0.0
    ordered_span_start = -1
    ordered_span_end = -1
    first_match_offset = compact_start if exact_compact_match else -1

    if ordered_span is not None:
        ordered_token_match = True
        adjacency_rank = _adjacency_rank(original_text, ordered_span.token_boundaries)
        adjacent_token_match = adjacency_rank >= 2
        ordered_gap_chars = ordered_span.total_gap_chars
        ordered_span_start = ordered_span.span_start
        ordered_span_end = ordered_span.span_end
        ordered_span_length = ordered_span_end - ordered_span_start
        proximity_score = 1.0 / float(1 + ordered_gap_chars)
        if first_match_offset < 0:
            first_match_offset = ordered_span_start

    if require_ordered_match and not exact_compact_match and not ordered_token_match:
        return None

    if first_match_offset < 0:
        if not query_tokens:
            return None
        token_position = original_text.lower().find(query_tokens[0].lower())
        if token_position >= 0:
            first_match_offset = token_position

    if first_match_offset < 0:
        return None

    return RankedMatch(
        exact_compact_match=exact_compact_match,
        adjacent_token_match=adjacent_token_match,
        ordered_token_match=ordered_token_match,
        adjacency_rank=adjacency_rank,
        ordered_gap_chars=ordered_gap_chars,
        ordered_span_length=ordered_span_length,
        proximity_score=proximity_score,
        gram_overlap_score=gram_overlap_score,
        rarity_score=rarity_score,
        first_match_offset=first_match_offset,
        compact_start=compact_start,
        compact_end=compact_end,
        ordered_span_start=ordered_span_start,
        ordered_span_end=ordered_span_end,
    )


def compute_rarity_score(
    *,
    matched_grams: list[str],
    gram_document_frequencies: dict[str, int],
    total_pages: int,
) -> float:
    if total_pages <= 0 or not matched_grams:
        return 0.0

    score = 0.0
    for gram in matched_grams:
        document_frequency = gram_document_frequencies.get(gram, total_pages)
        score += math.log(
            ((total_pages - document_frequency + 0.5) / (document_frequency + 0.5))
            + 1.0
        )
    return score


def sort_key(
    match: RankedMatch,
    page_number: int,
) -> tuple[int, float, int, int, int, int, float, float, int, int]:
    return (
        int(match.exact_compact_match),
        match.proximity_score,
        -match.ordered_gap_chars,
        -match.ordered_span_length,
        match.adjacency_rank,
        int(match.ordered_token_match),
        match.rarity_score,
        match.gram_overlap_score,
        -match.first_match_offset,
        -page_number,
    )


def _find_best_ordered_token_span(
    original_text: str,
    query_tokens: list[str],
    *,
    separator_only_match: bool,
    max_gap_chars: int | None,
) -> OrderedTokenSpan | None:
    if not query_tokens:
        return None

    lowered_text = original_text.lower()
    lowered_tokens = [token.lower() for token in query_tokens if token]
    if not lowered_tokens:
        return None

    token_occurrences = [
        _find_token_occurrences(lowered_text, token) for token in lowered_tokens
    ]
    if any(not occurrences for occurrences in token_occurrences):
        return None

    best_span: OrderedTokenSpan | None = None

    def search(
        *,
        token_index: int,
        previous_end: int,
        span_start: int,
        total_gap_chars: int,
        token_boundaries: list[tuple[int, int]],
    ) -> None:
        nonlocal best_span

        if token_index >= len(token_occurrences):
            candidate = OrderedTokenSpan(
                span_start=span_start,
                span_end=token_boundaries[-1][1],
                total_gap_chars=total_gap_chars,
                token_boundaries=list(token_boundaries),
                separator_only=_is_separator_only_boundaries(
                    original_text,
                    token_boundaries,
                ),
            )
            if separator_only_match and not candidate.separator_only:
                return
            if _is_better_ordered_span(candidate, best_span):
                best_span = candidate
            return

        for start, end in token_occurrences[token_index]:
            if start < previous_end:
                continue

            next_gap = total_gap_chars
            if token_boundaries:
                next_gap += start - previous_end
                if max_gap_chars is not None and next_gap > max_gap_chars:
                    continue

            if best_span is not None and next_gap > best_span.total_gap_chars:
                continue

            token_boundaries.append((start, end))
            search(
                token_index=token_index + 1,
                previous_end=end,
                span_start=span_start,
                total_gap_chars=next_gap,
                token_boundaries=token_boundaries,
            )
            token_boundaries.pop()

    for start, end in token_occurrences[0]:
        search(
            token_index=1,
            previous_end=end,
            span_start=start,
            total_gap_chars=0,
            token_boundaries=[(start, end)],
        )

    return best_span


def _adjacency_rank(
    original_text: str,
    token_boundaries: list[tuple[int, int]],
) -> int:
    if not token_boundaries:
        return 0

    if len(token_boundaries) == 1:
        return 3

    gap_segments = [
        original_text[token_boundaries[index][1] : token_boundaries[index + 1][0]]
        for index in range(len(token_boundaries) - 1)
    ]
    if all(segment == "" for segment in gap_segments):
        return 4
    if all(segment and _is_punctuation_only(segment) for segment in gap_segments):
        return 3
    if all(segment and segment.isspace() for segment in gap_segments):
        return 2
    return 1


def _is_punctuation_only(text: str) -> bool:
    return all(
        (not character.isalnum())
        and (not character.isspace())
        and character in SEPARATOR_CHARACTERS
        for character in text
    )


def _is_separator_only_boundaries(
    original_text: str,
    token_boundaries: list[tuple[int, int]],
) -> bool:
    if len(token_boundaries) <= 1:
        return True

    gap_segments = [
        original_text[token_boundaries[index][1] : token_boundaries[index + 1][0]]
        for index in range(len(token_boundaries) - 1)
    ]
    return all(
        segment == "" or all(character in SEPARATOR_CHARACTERS for character in segment)
        for segment in gap_segments
    )


def _find_token_occurrences(text: str, token: str) -> list[tuple[int, int]]:
    occurrences: list[tuple[int, int]] = []
    search_start = 0
    while True:
        position = text.find(token, search_start)
        if position < 0:
            return occurrences
        occurrences.append((position, position + len(token)))
        search_start = position + 1


def _is_better_ordered_span(
    candidate: OrderedTokenSpan,
    current: OrderedTokenSpan | None,
) -> bool:
    if current is None:
        return True

    candidate_key = (
        candidate.total_gap_chars,
        candidate.span_end - candidate.span_start,
        candidate.span_start,
    )
    current_key = (
        current.total_gap_chars,
        current.span_end - current.span_start,
        current.span_start,
    )
    return candidate_key < current_key
