from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QTextEdit,
)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("suki-helper")
        self.resize(1400, 900)
        self._build_ui()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_left_pane())
        splitter.addWidget(self._build_right_pane())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 5)
        self.setCentralWidget(splitter)

    def _build_left_pane(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        self.pdf_selector = QComboBox()
        self.pdf_selector.addItem("No indexed PDFs")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search keyword and press Enter")

        self.result_count_label = QLabel("Results: 0")
        self.result_list = QListWidget()

        layout.addWidget(QLabel("PDF"))
        layout.addWidget(self.pdf_selector)
        layout.addWidget(QLabel("Search"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.result_count_label)
        layout.addWidget(self.result_list, 1)
        return container

    def _build_right_pane(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        self.page_title_label = QLabel("No page selected")
        self.page_viewer = QTextEdit()
        self.page_viewer.setReadOnly(True)
        self.page_viewer.setPlainText(
            "High-resolution page preview will appear here."
        )

        layout.addWidget(self.page_title_label)
        layout.addWidget(self.page_viewer, 1)
        return container
