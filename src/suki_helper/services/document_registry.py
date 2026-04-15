from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from suki_helper.pdf.extractor import extract_document
from suki_helper.storage.db import AppPaths, DocumentFingerprint, connect_sqlite
from suki_helper.storage.repositories import (
    delete_document_record,
    rebuild_index_db,
    update_document_indexed_state,
    upsert_document_record,
)


@dataclass(frozen=True)
class RegisteredDocument:
    file_path: Path
    file_name: str
    page_count: int
    status: str


class DocumentRegistryService:
    def __init__(self, paths: AppPaths) -> None:
        self._paths = paths

    def register_pdf(self, file_path: Path) -> RegisteredDocument:
        stat = os.stat(file_path)
        fingerprint = DocumentFingerprint(
            file_path=file_path,
            file_size=stat.st_size,
            file_mtime=stat.st_mtime,
        )
        _, index_db_path = upsert_document_record(self._paths, fingerprint)
        extracted_document = extract_document(file_path)
        rebuild_index_db(index_db_path, extracted_document)
        update_document_indexed_state(
            self._paths,
            file_path,
            page_count=extracted_document.page_count,
        )
        return RegisteredDocument(
            file_path=file_path,
            file_name=file_path.name,
            page_count=extracted_document.page_count,
            status="indexed",
        )

    def list_documents(self) -> list[RegisteredDocument]:
        with connect_sqlite(self._paths.catalog_db_path) as connection:
            rows = connection.execute(
                """
                SELECT file_path, file_name, page_count, status
                FROM documents
                ORDER BY file_name ASC
                """
            ).fetchall()

        return [
            RegisteredDocument(
                file_path=Path(row["file_path"]),
                file_name=row["file_name"],
                page_count=row["page_count"],
                status=row["status"],
            )
            for row in rows
        ]

    def remove_pdf(self, file_path: Path) -> bool:
        removed_index_db_path = delete_document_record(self._paths, file_path)
        if removed_index_db_path is None:
            return False

        if removed_index_db_path.exists():
            removed_index_db_path.unlink()
        return True
