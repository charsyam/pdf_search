from __future__ import annotations

from suki_helper.workers.task_worker import TaskWorker


def test_task_worker_reports_finished_result() -> None:
    worker = TaskWorker(lambda: 42)
    captured: list[object] = []
    worker.signals.finished.connect(captured.append)

    worker.run()

    assert captured == [42]


def test_task_worker_reports_failure() -> None:
    def _raise_error() -> object:
        raise RuntimeError("boom")

    worker = TaskWorker(_raise_error)
    captured: list[str] = []
    worker.signals.failed.connect(captured.append)

    worker.run()

    assert captured == ["boom"]
