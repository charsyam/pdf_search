from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QImage, QPixmap

from suki_helper.pdf.renderer import render_page_to_png
from suki_helper.storage.db import AppPaths


@dataclass(frozen=True)
class RenderRequest:
    file_path: Path
    page_number: int
    dpi: int


class RenderService:
    def __init__(self, paths: AppPaths | None = None) -> None:
        self._paths = paths
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

        cache_paths = self._png_cache_paths(
            file_path=file_path,
            page_number=page_number,
            dpi=dpi,
        )
        for cache_path in cache_paths:
            if cache_path.exists():
                png_bytes = cache_path.read_bytes()
                self._png_cache[cache_key] = png_bytes
                return png_bytes

        rendered = render_page_to_png(
            file_path,
            page_number=page_number,
            dpi=dpi,
        )
        for cache_path in cache_paths:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(rendered.png_bytes)
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

    def _png_cache_paths(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int,
    ) -> list[Path]:
        if self._paths is None:
            return []

        cache_keys = _build_cache_keys(
            file_path=file_path,
            page_number=page_number,
            variant=f"render-{dpi}",
        )
        return [self._paths.renders_dir / f"{cache_key}.png" for cache_key in cache_keys]


def _build_cache_keys(
    *,
    file_path: Path,
    page_number: int,
    variant: str,
) -> list[str]:
    resolved_path = file_path.resolve(strict=False)
    raw_keys = [f"{resolved_path}|{page_number}|{variant}|fallback"]

    if file_path.exists():
        stat = file_path.stat()
        raw_keys.insert(
            0,
            f"{resolved_path}|{stat.st_size}|{stat.st_mtime_ns}|{page_number}|{variant}",
        )

    return [hashlib.sha256(raw_key.encode("utf-8")).hexdigest() for raw_key in raw_keys]
