"""Run blocking work on Qt's thread pool and get results back on the GUI thread."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from nyaadownloader.core.errors import Cancelled

log = logging.getLogger(__name__)


class _Signals(QObject):
    progress = Signal(int, int)
    result = Signal(object)
    error = Signal(object)
    finished = Signal()


class Task(QRunnable):
    """``fn(cancel_event, progress_callback)`` executed off the GUI thread.

    Signals are delivered on the GUI thread. A cancelled task emits neither ``result``
    nor ``error``, only ``finished``.
    """

    _alive: set[Task] = set()

    def __init__(self, fn: Callable[[threading.Event, Callable[[int, int], None]], Any]) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.fn = fn
        self.cancel_event = threading.Event()
        self.signals = _Signals()
        self.signals.finished.connect(lambda: Task._alive.discard(self))

    @property
    def cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            result = self.fn(self.cancel_event, self.signals.progress.emit)
        except Cancelled:
            pass
        except Exception as exc:  # reported to the GUI, which decides how to show it
            if not self.cancelled:
                log.debug("Task failed", exc_info=exc)
                self.signals.error.emit(exc)
        else:
            if not self.cancelled:
                self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


def run_task(
    fn: Callable[[threading.Event, Callable[[int, int], None]], Any],
    on_result: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    on_finished: Callable[[], None] | None = None,
) -> Task:
    task = Task(fn)
    if on_result:
        task.signals.result.connect(on_result)
    if on_error:
        task.signals.error.connect(on_error)
    if on_progress:
        task.signals.progress.connect(on_progress)
    if on_finished:
        task.signals.finished.connect(on_finished)
    Task._alive.add(task)
    QThreadPool.globalInstance().start(task)
    return task
