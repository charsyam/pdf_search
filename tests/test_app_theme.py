from __future__ import annotations

from PySide6.QtGui import QPalette

from suki_helper.app.bootstrap import create_application_with_paths
from suki_helper.app.theme import apply_theme_mode, load_theme_mode, save_theme_mode
from suki_helper.storage.db import bootstrap_storage


def test_application_uses_saved_light_theme(tmp_path) -> None:
    paths = bootstrap_storage(root_dir=tmp_path)
    save_theme_mode(paths, "light")

    app = create_application_with_paths(paths)
    palette = app.palette()

    assert palette.color(QPalette.Window).name() == "#f4f1e8"
    assert palette.color(QPalette.Base).name() == "#fffdf8"
    assert palette.color(QPalette.Highlight).name() == "#d6b36d"
    assert "#f4f1e8" in app.styleSheet()


def test_theme_mode_persists_to_settings(tmp_path) -> None:
    paths = bootstrap_storage(root_dir=tmp_path)

    save_theme_mode(paths, "dark")

    assert load_theme_mode(paths) == "dark"


def test_application_can_switch_to_system_theme(tmp_path) -> None:
    paths = bootstrap_storage(root_dir=tmp_path)
    app = create_application_with_paths(paths)

    apply_theme_mode(app, "system")

    assert app.styleSheet() == ""
