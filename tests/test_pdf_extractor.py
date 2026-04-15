from __future__ import annotations

from pathlib import Path

import fitz

from suki_helper.pdf.extractor import extract_document


def _create_sample_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    first_page = document.new_page()
    first_page.insert_text((72, 72), "First page text")

    second_page = document.new_page()
    second_page.insert_text((72, 72), "Second page text")

    document.save(pdf_path)
    document.close()


def test_extract_document_returns_page_text_and_count(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    extracted = extract_document(pdf_path)

    assert extracted.file_path == pdf_path
    assert extracted.page_count == 2
    assert [page.page_number for page in extracted.pages] == [1, 2]
    assert "First page text" in extracted.pages[0].text
    assert "Second page text" in extracted.pages[1].text
