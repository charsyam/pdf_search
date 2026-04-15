from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QImage, QPixmap

from suki_helper.pdf.renderer import render_page_to_png


@dataclass(frozen=True)
class RenderRequest:
    file_path: Path
    page_number: int
    dpi: int


class RenderService:
    def __init__(self) -> None:
        self._png_cache: dict[tuple[str, int, int], bytes] = {}
        self._pixmap_cache: dict[tuple[str, int, int], QPixmap] = {}

    def render_page_png_bytes(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int = 160,
    ) -> bytes:
        cache_key = (str(file_path), page_number, dpi)
        cached = self._png_cache.get(cache_key)
        if cached is not None:
            return cached

        rendered = render_page_to_png(
            file_path,
            page_number=page_number,
            dpi=dpi,
        )
        self._png_cache[cache_key] = rendered.png_bytes
        return rendered.png_bytes

    def render_page_pixmap(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int = 160,
    ) -> QPixmap:
        cache_key = (str(file_path), page_number, dpi)
        cached = self._pixmap_cache.get(cache_key)
        if cached is not None:
            return cached

        image = QImage.fromData(
            self.render_page_png_bytes(
                file_path=file_path,
                page_number=page_number,
                dpi=dpi,
            ),
            "PNG",
        )
        pixmap = QPixmap.fromImage(image)
        self._pixmap_cache[cache_key] = pixmap
        return pixmap
