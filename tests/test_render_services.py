from __future__ import annotations

from pathlib import Path

import fitz
from PySide6.QtWidgets import QApplication

from suki_helper.services.preview_service import PreviewService
from suki_helper.services.render_service import RenderService


def _create_sample_pdf(pdf_path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "alpha beta")
    document.save(pdf_path)
    document.close()


def _get_app() -> QApplication:
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication([])


def test_render_service_returns_non_empty_pixmap(tmp_path: Path) -> None:
    _get_app()
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    service = RenderService()
    pixmap = service.render_page_pixmap(file_path=pdf_path, page_number=1, dpi=120)

    assert not pixmap.isNull()
    assert pixmap.width() > 0
    assert pixmap.height() > 0


def test_preview_service_returns_icon(tmp_path: Path) -> None:
    _get_app()
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    render_service = RenderService()
    preview_service = PreviewService(render_service)
    icon = preview_service.build_result_icon(
        file_path=pdf_path,
        page_number=1,
        width=96,
    )

    assert not icon.isNull()
