from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class TaskWorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class TaskWorker(QRunnable):
    def __init__(self, task: Callable[[], Any]) -> None:
        super().__init__()
        self._task = task
        self.signals = TaskWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._task()
        except Exception as exc:  # pragma: no cover - defensive runtime path
            self.signals.failed.emit(str(exc))
            return
        self.signals.finished.emit(result)
