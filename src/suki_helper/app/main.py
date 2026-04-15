from __future__ import annotations

import sys

from suki_helper.app.bootstrap import create_application, create_main_window
from suki_helper.tools.render_worker import main as render_worker_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--render-worker":
        return render_worker_main(args[1:])

    app = create_application()
    window = create_main_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
