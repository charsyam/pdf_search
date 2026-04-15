from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import fitz

from suki_helper.pdf.extractor import extract_document
from suki_helper.storage.db import (
    DocumentFingerprint,
    bootstrap_storage,
    decode_int_list,
)
from suki_helper.storage.repositories import (
    rebuild_index_db,
    update_document_indexed_state,
    upsert_document_record,
)


def _create_sample_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "ab cd")
    document.save(pdf_path)
    document.close()


def test_rebuild_index_db_persists_pages_and_postings(tmp_path: Path) -> None:
    paths = bootstrap_storage(root_dir=tmp_path)
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    stat = os.stat(pdf_path)
    fingerprint = DocumentFingerprint(
        file_path=pdf_path,
        file_size=stat.st_size,
        file_mtime=stat.st_mtime,
    )
    _, index_db_path = upsert_document_record(paths, fingerprint)

    extracted = extract_document(pdf_path)
    rebuild_index_db(index_db_path, extracted)
    update_document_indexed_state(paths, pdf_path, page_count=extracted.page_count)

    with sqlite3.connect(index_db_path) as connection:
        page_row = connection.execute(
            "SELECT page_number, normalized_text, offset_map_blob FROM pages"
        ).fetchone()
        gram_rows = connection.execute(
            "SELECT gram, positions_blob FROM gram_postings ORDER BY gram"
        ).fetchall()

    assert page_row[0] == 1
    assert page_row[1] == "abcd"
    assert decode_int_list(page_row[2]) == [0, 1, 3, 4]
    assert [(row[0], decode_int_list(row[1])) for row in gram_rows] == [
        ("ab", [0]),
        ("bc", [1]),
        ("cd", [2]),
    ]
