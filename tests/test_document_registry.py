from __future__ import annotations

from pathlib import Path

import fitz

from suki_helper.services.document_registry import DocumentRegistryService
from suki_helper.storage.db import bootstrap_storage


def _create_sample_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "alpha beta")
    document.save(pdf_path)
    document.close()


def test_document_registry_registers_pdf_and_lists_it(tmp_path: Path) -> None:
    paths = bootstrap_storage(root_dir=tmp_path)
    service = DocumentRegistryService(paths)
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    registered = service.register_pdf(pdf_path)
    documents = service.list_documents()

    assert registered.file_path == pdf_path
    assert registered.status == "indexed"
    assert len(documents) == 1
    assert documents[0].file_name == "sample.pdf"
