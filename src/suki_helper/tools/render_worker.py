from __future__ import annotations

import argparse
from pathlib import Path

from suki_helper.pdf.renderer import render_page_to_png


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a single PDF page to PNG.")
    parser.add_argument("--file", required=True, help="PDF file path")
    parser.add_argument("--page", required=True, type=int, help="1-based page number")
    parser.add_argument("--dpi", required=True, type=int, help="Render DPI")
    parser.add_argument("--output", required=True, help="Output PNG path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    rendered = render_page_to_png(
        Path(args.file),
        page_number=args.page,
        dpi=args.dpi,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(rendered.png_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
