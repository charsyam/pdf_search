from __future__ import annotations

from PySide6.QtWidgets import QApplication

from suki_helper.storage.db import bootstrap_storage
from suki_helper.ui.main_window import MainWindow


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication([])


def create_main_window() -> MainWindow:
    bootstrap_storage()
    return MainWindow()
