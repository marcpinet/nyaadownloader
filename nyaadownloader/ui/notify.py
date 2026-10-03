"""Desktop notifications, only when the window is not in front."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QWidget

from nyaadownloader import APP_NAME

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, window: QWidget, icon_path: str) -> None:
        self._window = window
        self._icon_path = icon_path
        self._tray: QSystemTrayIcon | None = None

    def notify(self, title: str, message: str) -> None:
        if self._window.isActiveWindow():
            return
        QApplication.alert(self._window)
        if sys.platform == "win32" and self._toast(title, message):
            return
        if QSystemTrayIcon.isSystemTrayAvailable():
            if self._tray is None:
                self._tray = QSystemTrayIcon(self._window.windowIcon(), self._window)
                self._tray.activated.connect(lambda *_: self._raise())
                self._tray.messageClicked.connect(self._raise)
            self._tray.show()
            self._tray.showMessage(title, message, self._window.windowIcon(), 6000)

    def _toast(self, title: str, message: str) -> bool:
        try:
            from winotify import Notification, audio
        except ImportError:
            return False
        try:
            toast = Notification(app_id=APP_NAME, title=title, msg=message, icon=self._icon_path)
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception as exc:  # winotify shells out to PowerShell, which may be blocked
            log.info("Toast notification failed: %s", exc)
            return False
        return True

    def _raise(self) -> None:
        self._window.showNormal()
        self._window.raise_()
        self._window.activateWindow()
