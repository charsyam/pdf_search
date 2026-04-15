from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage, QPixmap

from suki_helper.pdf.renderer import render_page_to_png, render_page_to_qimage
from suki_helper.storage.db import AppPaths

INLINE_RENDER_BACKEND = "inline"
PROCESS_RENDER_BACKEND = "process"
DEFAULT_DETAIL_RENDER_DPI = 120


@dataclass(frozen=True)
class RenderRequest:
    file_path: Path
    page_number: int
    dpi: int


class RenderService:
    def __init__(
        self,
        paths: AppPaths | None = None,
        *,
        default_dpi: int = DEFAULT_DETAIL_RENDER_DPI,
        detail_backend: str | None = None,
        memory_cache_limit: int = 8,
    ) -> None:
        self._paths = paths
        self._default_dpi = default_dpi
        self._detail_backend = self._normalize_backend(
            detail_backend or os.environ.get("SUKI_HELPER_DETAIL_RENDER_BACKEND")
        )
        self._memory_cache_limit = max(1, memory_cache_limit)
        self._png_cache: OrderedDict[tuple[str, int, int], bytes] = OrderedDict()
        self._image_cache: OrderedDict[tuple[str, int, int], QImage] = OrderedDict()
        self._pixmap_cache: OrderedDict[tuple[str, int, int], QPixmap] = OrderedDict()

    @property
    def detail_backend(self) -> str:
        return self._detail_backend

    def render_page_png_bytes(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int | None = None,
        backend: str | None = None,
    ) -> bytes:
        resolved_dpi = dpi or self._default_dpi
        cache_key = (str(file_path), page_number, resolved_dpi)
        cached = self._remember_cache_hit(self._png_cache, cache_key)
        if cached is not None:
            return cached

        cache_paths = self._png_cache_paths(
            file_path=file_path,
            page_number=page_number,
            dpi=resolved_dpi,
        )
        for cache_path in cache_paths:
            if cache_path.exists():
                png_bytes = cache_path.read_bytes()
                self._remember_cache_value(self._png_cache, cache_key, png_bytes)
                return png_bytes

        resolved_backend = self._normalize_backend(backend) or self._detail_backend
        if resolved_backend == PROCESS_RENDER_BACKEND:
            png_bytes = self._render_png_via_process(
                file_path=file_path,
                page_number=page_number,
                dpi=resolved_dpi,
                cache_paths=cache_paths,
            )
        else:
            png_bytes = render_page_to_png(
                file_path,
                page_number=page_number,
                dpi=resolved_dpi,
            ).png_bytes
            self._persist_png_cache(cache_paths, png_bytes)

        self._remember_cache_value(self._png_cache, cache_key, png_bytes)
        return png_bytes

    def render_page_pixmap(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int | None = None,
        backend: str | None = None,
    ) -> QPixmap:
        resolved_dpi = dpi or self._default_dpi
        cache_key = (str(file_path), page_number, resolved_dpi)
        cached = self._remember_cache_hit(self._pixmap_cache, cache_key)
        if cached is not None:
            return cached

        image = self.render_page_image(
            file_path=file_path,
            page_number=page_number,
            dpi=resolved_dpi,
            backend=backend,
        )
        pixmap = QPixmap.fromImage(image)
        self._remember_cache_value(self._pixmap_cache, cache_key, pixmap)
        return pixmap

    def render_page_image(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int | None = None,
        backend: str | None = None,
    ) -> QImage:
        resolved_dpi = dpi or self._default_dpi
        cache_key = (str(file_path), page_number, resolved_dpi)
        cached = self._remember_cache_hit(self._image_cache, cache_key)
        if cached is not None:
            return cached

        cache_paths = self._png_cache_paths(
            file_path=file_path,
            page_number=page_number,
            dpi=resolved_dpi,
        )
        for cache_path in cache_paths:
            if cache_path.exists():
                png_bytes = cache_path.read_bytes()
                image = QImage.fromData(png_bytes, "PNG")
                self._remember_cache_value(self._png_cache, cache_key, png_bytes)
                self._remember_cache_value(self._image_cache, cache_key, image)
                return image

        resolved_backend = self._normalize_backend(backend) or self._detail_backend
        if resolved_backend == PROCESS_RENDER_BACKEND:
            png_bytes = self.render_page_png_bytes(
                file_path=file_path,
                page_number=page_number,
                dpi=resolved_dpi,
                backend=PROCESS_RENDER_BACKEND,
            )
            image = QImage.fromData(png_bytes, "PNG")
        else:
            rendered = render_page_to_qimage(
                file_path,
                page_number=page_number,
                dpi=resolved_dpi,
            )
            image = rendered.image
            png_bytes = self._image_to_png_bytes(image)
            self._persist_png_cache(cache_paths, png_bytes)
            self._remember_cache_value(self._png_cache, cache_key, png_bytes)

        self._remember_cache_value(self._image_cache, cache_key, image)
        return image

    def _render_png_via_process(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int,
        cache_paths: list[Path],
    ) -> bytes:
        cache_path = cache_paths[0] if cache_paths else None
        temporary_path: Path | None = None
        if cache_path is None:
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            handle.close()
            temporary_path = Path(handle.name)
            output_path = temporary_path
        else:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            output_path = cache_path

        try:
            command = self._build_external_render_command(
                file_path=file_path,
                page_number=page_number,
                dpi=dpi,
                output_path=output_path,
            )
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(
                    f"External render process failed with exit code {completed.returncode}: {stderr}"
                )
            if not output_path.exists():
                raise RuntimeError("External render process finished without producing an image.")

            png_bytes = output_path.read_bytes()
            if cache_path is not None and temporary_path is None:
                self._persist_png_cache(cache_paths[1:], png_bytes)
            return png_bytes
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def _build_external_render_command(
        self,
        *,
        file_path: Path,
        page_number: int,
        dpi: int,
        output_path: Path,
    ) -> list[str]:
        base_args = [
            "--render-worker",
            "--file",
            str(file_path),
            "--page",
            str(page_number),
            "--dpi",
            str(dpi),
            "--output",
            str(output_path),
        ]
        if getattr(sys, "frozen", False):
            return [sys.executable, *base_args]
        return [sys.executable, "-m", "suki_helper.app.main", *base_args]

    def _persist_png_cache(self, cache_paths: list[Path], png_bytes: bytes) -> None:
        for cache_path in cache_paths:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(png_bytes)

    @staticmethod
    def _image_to_png_bytes(image: QImage) -> bytes:
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        return bytes(buffer.data())

    @staticmethod
    def _normalize_backend(backend: str | None) -> str | None:
        if backend is None:
            return None
        normalized = backend.strip().lower()
        if normalized == PROCESS_RENDER_BACKEND:
            return PROCESS_RENDER_BACKEND
        return INLINE_RENDER_BACKEND

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

    def _remember_cache_value(self, cache: OrderedDict, cache_key: tuple[str, int, int], value: object) -> None:
        cache[cache_key] = value
        cache.move_to_end(cache_key)
        while len(cache) > self._memory_cache_limit:
            cache.popitem(last=False)

    @staticmethod
    def _remember_cache_hit(cache: OrderedDict, cache_key: tuple[str, int, int]) -> object | None:
        cached = cache.get(cache_key)
        if cached is None:
            return None
        cache.move_to_end(cache_key)
        return cached


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
