from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from suki_helper.services.document_registry import DocumentRegistryService, RegisteredDocument
from suki_helper.services.search_service import SearchResult, SearchService


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        document_registry: DocumentRegistryService,
        search_service: SearchService,
    ) -> None:
        super().__init__()
        self._document_registry = document_registry
        self._search_service = search_service
        self._documents_by_index: list[RegisteredDocument] = []
        self._results: list[SearchResult] = []
        self.setWindowTitle("suki-helper")
        self.resize(1400, 900)
        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._refresh_document_selector()

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

        self.open_button = QPushButton("Add PDF")
        self.pdf_selector = QComboBox()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search keyword and press Enter")

        self.result_count_label = QLabel("Results: 0")
        self.result_list = QListWidget()
        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(self._build_empty_state())
        self.left_stack.addWidget(self.result_list)

        layout.addWidget(self.open_button)
        layout.addWidget(QLabel("PDF"))
        layout.addWidget(self.pdf_selector)
        layout.addWidget(QLabel("Search"))
        layout.addWidget(self.search_input)
        layout.addWidget(self.result_count_label)
        layout.addWidget(self.left_stack, 1)
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

    def _build_empty_state(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addStretch(1)

        title = QLabel("Select a PDF to start")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        description = QLabel(
            "No indexed PDF is available yet.\nAdd a PDF first, then choose it and search."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666;")

        self.empty_state_button = QPushButton("Choose PDF")
        self.empty_state_button.setFixedWidth(180)

        button_row = QWidget()
        button_layout = QVBoxLayout(button_row)
        button_layout.addWidget(self.empty_state_button, alignment=Qt.AlignHCenter)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(button_row)
        layout.addStretch(1)
        return container

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        self.add_pdf_action = QAction("Add PDF", self)
        self.add_pdf_action.setShortcut("Ctrl+O")
        file_menu.addAction(self.add_pdf_action)

    def _connect_signals(self) -> None:
        self.open_button.clicked.connect(self._open_pdf_files)
        self.empty_state_button.clicked.connect(self._open_pdf_files)
        self.add_pdf_action.triggered.connect(self._open_pdf_files)
        self.search_input.returnPressed.connect(self._run_search)
        self.result_list.currentRowChanged.connect(self._display_selected_result)

    def _open_pdf_files(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open PDF files",
            "",
            "PDF Files (*.pdf)",
        )
        if not file_paths:
            return

        for file_path in file_paths:
            self._document_registry.register_pdf(Path(file_path))

        self._refresh_document_selector()

    def _refresh_document_selector(self) -> None:
        self._documents_by_index = self._document_registry.list_documents()
        self.pdf_selector.clear()
        if not self._documents_by_index:
            self.pdf_selector.addItem("No indexed PDFs")
            self.pdf_selector.setEnabled(False)
            self.search_input.setEnabled(False)
            self.result_count_label.setText("Results: 0")
            self.left_stack.setCurrentIndex(0)
            return

        self.pdf_selector.setEnabled(True)
        self.search_input.setEnabled(True)
        for document in self._documents_by_index:
            self.pdf_selector.addItem(
                f"{document.file_name} ({document.page_count} pages)"
            )
        self.left_stack.setCurrentIndex(1)

    def _run_search(self) -> None:
        selected_document = self._selected_document()
        if selected_document is None:
            self.result_count_label.setText("Results: 0")
            self.result_list.clear()
            self.left_stack.setCurrentIndex(0)
            return

        self._results = self._search_service.search(
            file_path=selected_document.file_path,
            query=self.search_input.text(),
        )
        self.result_list.clear()
        self.left_stack.setCurrentIndex(1)

        for result in self._results:
            item = QListWidgetItem(
                f"Page {result.page_number}: "
                f"{result.context_before}[{result.context_match}]{result.context_after}"
            )
            self.result_list.addItem(item)

        self.result_count_label.setText(f"Results: {len(self._results)}")
        if self._results:
            self.result_list.setCurrentRow(0)
        else:
            self.page_title_label.setText("No page selected")
            self.page_viewer.setPlainText(
                "No search result. Try another keyword."
            )

    def _display_selected_result(self, row_index: int) -> None:
        if row_index < 0 or row_index >= len(self._results):
            return

        result = self._results[row_index]
        self.page_title_label.setText(f"Page {result.page_number}")
        self.page_viewer.setPlainText(result.original_text)

    def _selected_document(self) -> RegisteredDocument | None:
        current_index = self.pdf_selector.currentIndex()
        if current_index < 0 or current_index >= len(self._documents_by_index):
            return None
        return self._documents_by_index[current_index]
