from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedDocument:
    file_path: Path
    page_count: int
    pages: list[ExtractedPage]


def extract_document(file_path: Path) -> ExtractedDocument:
    pages: list[ExtractedPage] = []
    with fitz.open(file_path) as document:
        for page_index, page in enumerate(document, start=1):
            pages.append(
                ExtractedPage(
                    page_number=page_index,
                    text=page.get_text("text"),
                )
            )
        page_count = document.page_count

    return ExtractedDocument(
        file_path=file_path,
        page_count=page_count,
        pages=pages,
    )
