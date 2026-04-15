from __future__ import annotations


def make_2grams(text: str) -> list[str]:
    if not text:
        return []
    if len(text) == 1:
        return [text]
    return [text[index : index + 2] for index in range(len(text) - 1)]
