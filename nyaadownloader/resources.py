"""Bundled files, found both from source and inside the PyInstaller executable."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
    return base / "nyaadownloader" / "assets" / name


@lru_cache(maxsize=16)
def logo_pixmap(size: int, ratio: float = 2.0) -> QPixmap:
    pixmap = QPixmap(str(resource_path("logo.png")))
    if pixmap.isNull():
        return pixmap
    scaled = pixmap.scaled(int(size * ratio), int(size * ratio), Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
    scaled.setDevicePixelRatio(ratio)
    return scaled
