from __future__ import annotations

from pathlib import Path

import fitz
from PySide6.QtWidgets import QApplication

from suki_helper.services.preview_service import PreviewService
from suki_helper.services.render_service import RenderService
from suki_helper.storage.db import bootstrap_storage


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


def test_render_service_persists_png_disk_cache(tmp_path: Path) -> None:
    _get_app()
    paths = bootstrap_storage(root_dir=tmp_path)
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    service = RenderService(paths)
    png_bytes = service.render_page_png_bytes(file_path=pdf_path, page_number=1, dpi=144)

    assert png_bytes
    assert any(paths.renders_dir.glob("*.png"))


def test_preview_service_persists_thumbnail_disk_cache(tmp_path: Path) -> None:
    _get_app()
    paths = bootstrap_storage(root_dir=tmp_path)
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    render_service = RenderService(paths)
    preview_service = PreviewService(render_service, paths)
    pixmap = preview_service.build_result_pixmap(
        file_path=pdf_path,
        page_number=1,
        width=180,
        dpi=144,
    )

    assert not pixmap.isNull()
    assert any(paths.thumbs_dir.glob("*.png"))


def test_render_service_uses_disk_cache_when_source_pdf_is_missing(tmp_path: Path) -> None:
    _get_app()
    paths = bootstrap_storage(root_dir=tmp_path)
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    service = RenderService(paths)
    first_png = service.render_page_png_bytes(file_path=pdf_path, page_number=1, dpi=144)
    pdf_path.unlink()

    second_png = service.render_page_png_bytes(file_path=pdf_path, page_number=1, dpi=144)

    assert second_png == first_png


def test_preview_service_uses_disk_cache_when_source_pdf_is_missing(tmp_path: Path) -> None:
    _get_app()
    paths = bootstrap_storage(root_dir=tmp_path)
    pdf_path = tmp_path / "sample.pdf"
    _create_sample_pdf(pdf_path)

    render_service = RenderService(paths)
    preview_service = PreviewService(render_service, paths)
    first_pixmap = preview_service.build_result_pixmap(
        file_path=pdf_path,
        page_number=1,
        width=180,
        dpi=144,
    )
    pdf_path.unlink()

    second_pixmap = preview_service.build_result_pixmap(
        file_path=pdf_path,
        page_number=1,
        width=180,
        dpi=144,
    )

    assert not first_pixmap.isNull()
    assert not second_pixmap.isNull()
