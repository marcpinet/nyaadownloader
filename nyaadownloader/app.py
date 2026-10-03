"""Application entry point: logging, crash reporting, theme and main window."""

from __future__ import annotations

import contextlib
import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from platformdirs import user_log_path
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from nyaadownloader import APP_NAME, __version__
from nyaadownloader.core.settings import Settings
from nyaadownloader.resources import resource_path

log = logging.getLogger(__name__)


class _LogEmitter(QObject):
    line = Signal(str)


class _QtLogBridge(logging.Handler):
    """Forwards log records to the Activity panel, from any thread."""

    def __init__(self) -> None:
        super().__init__(logging.INFO)
        self.emitter = _LogEmitter()
        self.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        with contextlib.suppress(RuntimeError):  # the window is already gone during shutdown
            self.emitter.line.emit(self.format(record))


def _setup_logging() -> _QtLogBridge:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    try:
        log_dir = user_log_path(APP_NAME, appauthor=False)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_dir / "nyaadownloader.log", maxBytes=1_000_000,
                                           backupCount=2, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.addHandler(file_handler)
    except OSError:
        pass
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    bridge = _QtLogBridge()
    logging.getLogger("nyaadownloader").addHandler(bridge)
    return bridge


def _install_excepthook() -> None:
    def hook(exc_type, exc, tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        details = "".join(traceback.format_exception(exc_type, exc, tb))
        logging.getLogger(__name__).critical("Unhandled error\n%s", details)
        if QApplication.instance():
            box = QMessageBox(QMessageBox.Icon.Critical, APP_NAME,
                              "Something went wrong. The app will keep running, but please report this "
                              "on GitHub with the details below.")
            box.setDetailedText(details)
            box.exec()

    sys.excepthook = hook


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        try:  # own taskbar group and icon instead of python.exe's
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"marcpinet.{APP_NAME}")
        except (AttributeError, OSError):
            pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    icon = QIcon(str(resource_path("nyaa.ico")))
    icon.addFile(str(resource_path("logo.png")))
    app.setWindowIcon(icon)

    bridge = _setup_logging()
    _install_excepthook()
    settings = Settings.load()

    from nyaadownloader.ui import theme
    from nyaadownloader.ui.main_window import MainWindow

    theme.apply(app, settings.theme)
    window = MainWindow(settings, str(resource_path("logo.png")))
    bridge.emitter.line.connect(window.append_activity)
    window.show()
    log.info("%s %s ready.", APP_NAME, __version__)
    return app.exec()
