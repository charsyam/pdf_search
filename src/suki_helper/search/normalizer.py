from __future__ import annotations

from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class NormalizedText:
    original_text: str
    normalized_text: str
    norm_to_original_map: list[int]


def normalize_for_search(text: str) -> NormalizedText:
    normalized_characters: list[str] = []
    norm_to_original_map: list[int] = []

    for original_index, character in enumerate(text):
        folded = unicodedata.normalize("NFKC", character)
        for folded_character in folded:
            if folded_character.isspace():
                continue
            lowered = folded_character.lower()
            normalized_characters.append(lowered)
            norm_to_original_map.append(original_index)

    return NormalizedText(
        original_text=text,
        normalized_text="".join(normalized_characters),
        norm_to_original_map=norm_to_original_map,
    )
