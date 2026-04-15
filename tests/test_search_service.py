from __future__ import annotations

from pathlib import Path

from suki_helper.services.search_service import SearchService
from suki_helper.storage.db import AppPaths


def _make_paths(tmp_path: Path) -> AppPaths:
    from suki_helper.storage.db import bootstrap_storage

    return bootstrap_storage(root_dir=tmp_path)


def _register_indexed_document(
    tmp_path: Path,
    *,
    file_name: str,
    pages: list[str],
) -> tuple[AppPaths, Path]:
    import os

    import fitz

    from suki_helper.pdf.extractor import extract_document
    from suki_helper.storage.db import DocumentFingerprint
    from suki_helper.storage.repositories import (
        rebuild_index_db,
        update_document_indexed_state,
        upsert_document_record,
    )

    paths = _make_paths(tmp_path)
    pdf_path = tmp_path / file_name
    document = fitz.open()
    for page_text in pages:
        page = document.new_page()
        page.insert_text((72, 72), page_text)
    document.save(pdf_path)
    document.close()

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
    return paths, pdf_path


def test_search_service_returns_ranked_matches_for_selected_pdf(tmp_path: Path) -> None:
    paths, pdf_path = _register_indexed_document(
        tmp_path,
        file_name="sample.pdf",
        pages=[
            "dongpo haeoe",
            "haeoe-dongpo",
            "haeoe dongpo",
            "haeoe is where dongpo live",
        ],
    )

    service = SearchService(paths)
    results = service.search(file_path=pdf_path, query="haeoe dongpo")

    assert [result.page_number for result in results] == [2, 3, 4, 1]
    assert results[0].adjacent_token_match is True
    assert results[-1].ordered_token_match is False


def test_search_service_scopes_search_to_selected_pdf(tmp_path: Path) -> None:
    paths, pdf_path = _register_indexed_document(
        tmp_path,
        file_name="first.pdf",
        pages=["alpha beta"],
    )
    _, other_pdf_path = _register_indexed_document(
        tmp_path,
        file_name="second.pdf",
        pages=["alpha beta"],
    )

    service = SearchService(paths)
    first_results = service.search(file_path=pdf_path, query="alpha beta")
    second_results = service.search(file_path=other_pdf_path, query="alpha beta")

    assert len(first_results) == 1
    assert len(second_results) == 1
    # The selected file boundary is enforced by each per-PDF index DB.
    assert first_results[0].page_number == 1
    assert second_results[0].page_number == 1


def test_search_service_returns_empty_for_blank_query(tmp_path: Path) -> None:
    paths, pdf_path = _register_indexed_document(
        tmp_path,
        file_name="sample.pdf",
        pages=["alpha beta"],
    )

    service = SearchService(paths)

    assert service.search(file_path=pdf_path, query="   ") == []
