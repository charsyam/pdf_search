from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from suki_helper.services.render_service import RenderService


class PreviewService:
    def __init__(self, render_service: RenderService) -> None:
        self._render_service = render_service
        self._icon_cache: dict[tuple[str, int, int], QIcon] = {}
        self._pixmap_cache: dict[tuple[str, int, int], QPixmap] = {}

    def build_result_pixmap(
        self,
        *,
        file_path: Path,
        page_number: int,
        width: int = 180,
        dpi: int = 72,
    ) -> QPixmap:
        cache_key = (str(file_path), page_number, width)
        cached = self._pixmap_cache.get(cache_key)
        if cached is not None:
            return cached

        pixmap = self._render_service.render_page_pixmap(
            file_path=file_path,
            page_number=page_number,
            dpi=dpi,
        )
        scaled = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        self._pixmap_cache[cache_key] = scaled
        return scaled

    def build_result_icon(
        self,
        *,
        file_path: Path,
        page_number: int,
        width: int = 120,
        dpi: int = 72,
    ) -> QIcon:
        cache_key = (str(file_path), page_number, width)
        cached = self._icon_cache.get(cache_key)
        if cached is not None:
            return cached

        scaled = self.build_result_pixmap(
            file_path=file_path,
            page_number=page_number,
            width=width,
            dpi=dpi,
        )
        icon = QIcon(QPixmap(scaled))
        self._icon_cache[cache_key] = icon
        return icon
