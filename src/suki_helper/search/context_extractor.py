from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedContext:
    context_before: str
    context_match: str
    context_after: str


def extract_context(
    original_text: str,
    *,
    start_offset: int,
    end_offset: int,
    window: int = 60,
) -> ExtractedContext:
    before_start = max(0, start_offset - window)
    after_end = min(len(original_text), end_offset + window)

    return ExtractedContext(
        context_before=original_text[before_start:start_offset],
        context_match=original_text[start_offset:end_offset],
        context_after=original_text[end_offset:after_end],
    )
