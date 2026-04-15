from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from suki_helper.storage.db import AppPaths


ThemeMode = Literal["light", "dark", "system"]
DEFAULT_THEME_MODE: ThemeMode = "light"


def apply_theme_mode(app: QApplication, mode: ThemeMode) -> None:
    if mode == "dark":
        _apply_dark_theme(app)
        return
    if mode == "system":
        _apply_system_theme(app)
        return
    _apply_light_theme(app)


def load_theme_mode(paths: AppPaths) -> ThemeMode:
    settings = _load_settings(paths.settings_json_path)
    mode = settings.get("theme_mode", DEFAULT_THEME_MODE)
    if mode in {"light", "dark", "system"}:
        return mode
    return DEFAULT_THEME_MODE


def save_theme_mode(paths: AppPaths, mode: ThemeMode) -> None:
    settings = _load_settings(paths.settings_json_path)
    settings["theme_mode"] = mode
    paths.settings_json_path.parent.mkdir(parents=True, exist_ok=True)
    paths.settings_json_path.write_text(
        json.dumps(settings, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _load_settings(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _apply_light_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f4f1e8"))
    palette.setColor(QPalette.WindowText, QColor("#2f2a22"))
    palette.setColor(QPalette.Base, QColor("#fffdf8"))
    palette.setColor(QPalette.AlternateBase, QColor("#f7f2e7"))
    palette.setColor(QPalette.ToolTipBase, QColor("#fffdf8"))
    palette.setColor(QPalette.ToolTipText, QColor("#2f2a22"))
    palette.setColor(QPalette.Text, QColor("#2f2a22"))
    palette.setColor(QPalette.Button, QColor("#efe8da"))
    palette.setColor(QPalette.ButtonText, QColor("#2f2a22"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#d6b36d"))
    palette.setColor(QPalette.HighlightedText, QColor("#1f1a14"))
    palette.setColor(QPalette.PlaceholderText, QColor("#7d7468"))
    palette.setColor(QPalette.Light, QColor("#ffffff"))
    palette.setColor(QPalette.Midlight, QColor("#e5dccb"))
    palette.setColor(QPalette.Dark, QColor("#b7aa93"))
    palette.setColor(QPalette.Mid, QColor("#cdc2ad"))
    palette.setColor(QPalette.Shadow, QColor("#8d806b"))

    disabled_text = QColor("#9d9487")
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#d8d1c5"))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#8f8679"))

    app.setPalette(palette)
    app.setStyleSheet(
        """
        QWidget {
            color: #2f2a22;
            background-color: #f4f1e8;
        }
        QMainWindow, QMenuBar, QMenu, QStatusBar {
            background-color: #f4f1e8;
        }
        QLineEdit, QComboBox, QListWidget, QScrollArea, QSpinBox {
            background-color: #fffdf8;
            border: 1px solid #d7ccbb;
            border-radius: 8px;
        }
        QPushButton {
            background-color: #efe8da;
            border: 1px solid #cbbda7;
            border-radius: 8px;
            padding: 6px 10px;
        }
        QPushButton:disabled {
            background-color: #e5dfd3;
            color: #9d9487;
            border-color: #d0c7b8;
        }
        QListWidget::item:selected {
            background-color: #ead8b0;
            color: #1f1a14;
        }
        QMenu::item:selected {
            background-color: #ead8b0;
        }
        """
    )


def _apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1f1c"))
    palette.setColor(QPalette.WindowText, QColor("#ece7dc"))
    palette.setColor(QPalette.Base, QColor("#252723"))
    palette.setColor(QPalette.AlternateBase, QColor("#2d2f2a"))
    palette.setColor(QPalette.ToolTipBase, QColor("#252723"))
    palette.setColor(QPalette.ToolTipText, QColor("#ece7dc"))
    palette.setColor(QPalette.Text, QColor("#ece7dc"))
    palette.setColor(QPalette.Button, QColor("#31342d"))
    palette.setColor(QPalette.ButtonText, QColor("#ece7dc"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#c99b4b"))
    palette.setColor(QPalette.HighlightedText, QColor("#161713"))
    palette.setColor(QPalette.PlaceholderText, QColor("#9f998d"))
    palette.setColor(QPalette.Light, QColor("#4a4d46"))
    palette.setColor(QPalette.Midlight, QColor("#3a3d37"))
    palette.setColor(QPalette.Dark, QColor("#171815"))
    palette.setColor(QPalette.Mid, QColor("#2e302b"))
    palette.setColor(QPalette.Shadow, QColor("#0f100d"))

    disabled_text = QColor("#787368")
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor("#5f5545"))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor("#c0b6a3"))

    app.setPalette(palette)
    app.setStyleSheet(
        """
        QWidget {
            color: #ece7dc;
            background-color: #1e1f1c;
        }
        QMainWindow, QMenuBar, QMenu, QStatusBar {
            background-color: #1e1f1c;
        }
        QLineEdit, QComboBox, QListWidget, QScrollArea, QSpinBox {
            background-color: #252723;
            border: 1px solid #4b4e46;
            border-radius: 8px;
        }
        QPushButton {
            background-color: #31342d;
            border: 1px solid #5b5f55;
            border-radius: 8px;
            padding: 6px 10px;
        }
        QPushButton:disabled {
            background-color: #272924;
            color: #787368;
            border-color: #40433c;
        }
        QListWidget::item:selected {
            background-color: #8b6a34;
            color: #fff9ed;
        }
        QMenu::item:selected {
            background-color: #8b6a34;
        }
        """
    )


def _apply_system_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    app.setStyleSheet("")
