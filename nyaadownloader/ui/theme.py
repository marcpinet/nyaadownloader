"""Colours, stylesheet and icons. Follows the OS light/dark setting unless overridden."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class Palette:
    name: str
    window: str
    surface: str
    raised: str
    border: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    accent_text: str
    success: str
    warning: str
    danger: str
    selection: str


DARK = Palette(
    name="dark", window="#0f1115", surface="#161920", raised="#1e222b", border="#2a2f3a",
    text="#e7e9ee", muted="#8b93a6", accent="#5b8cff", accent_hover="#7aa2ff",
    accent_text="#ffffff", success="#3fb950", warning="#d9a634", danger="#f2645a",
    selection="#24314f",
)
LIGHT = Palette(
    name="light", window="#f4f5f8", surface="#ffffff", raised="#eef0f4", border="#d9dde5",
    text="#1a1e26", muted="#5f6779", accent="#3566f0", accent_hover="#2453d6",
    accent_text="#ffffff", success="#1f883d", warning="#9a6700", danger="#cf222e",
    selection="#dce6ff",
)

_current: Palette = DARK


def current() -> Palette:
    return _current


def resolve(mode: str) -> Palette:
    if mode == "dark":
        return DARK
    if mode == "light":
        return LIGHT
    scheme = QGuiApplication.styleHints().colorScheme()
    return LIGHT if scheme == Qt.ColorScheme.Light else DARK


def apply(app: QApplication, mode: str) -> Palette:
    global _current
    _current = p = resolve(mode)
    app.setStyle("Fusion")
    qp = QPalette()
    roles = {
        QPalette.ColorRole.Window: p.window,
        QPalette.ColorRole.WindowText: p.text,
        QPalette.ColorRole.Base: p.surface,
        QPalette.ColorRole.AlternateBase: p.raised,
        QPalette.ColorRole.Text: p.text,
        QPalette.ColorRole.Button: p.raised,
        QPalette.ColorRole.ButtonText: p.text,
        QPalette.ColorRole.Highlight: p.selection,
        QPalette.ColorRole.HighlightedText: p.text,
        QPalette.ColorRole.ToolTipBase: p.raised,
        QPalette.ColorRole.ToolTipText: p.text,
        QPalette.ColorRole.PlaceholderText: p.muted,
        QPalette.ColorRole.Link: p.accent,
        QPalette.ColorRole.Mid: p.border,
    }
    for role, color in roles.items():
        qp.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        qp.setColor(QPalette.ColorGroup.Disabled, role, QColor(p.muted))
    app.setPalette(qp)
    app.setStyleSheet(stylesheet(p, _write_check_image(p)))
    icon.cache_clear()
    return p


def _write_check_image(p: Palette) -> str:
    """Stylesheets can only load images from files, so drop the checkmark in the temp dir."""
    path = Path(tempfile.gettempdir()) / f"nyaadownloader-check-{p.name}.svg"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="{p.accent_text}" stroke-width="3.2" stroke-linecap="round" '
           f'stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg>')
    try:
        if not path.exists() or path.read_text() != svg:
            path.write_text(svg)
    except OSError:
        return ""
    return path.as_posix()


def stylesheet(p: Palette, check_image: str = "") -> str:
    check = f'image: url("{check_image}");' if check_image else ""
    return f"""
    * {{ outline: none; }}
    QMainWindow, QDialog {{ background: {p.window}; }}
    QToolTip {{ background: {p.raised}; color: {p.text}; border: 1px solid {p.border};
                padding: 6px 8px; border-radius: 6px; }}
    QLabel#muted, QLabel[muted="true"] {{ color: {p.muted}; }}
    QLabel#title {{ font-size: 15pt; font-weight: 600; }}
    QLabel#sectionTitle {{ font-weight: 600; }}
    QLabel#emptyTitle {{ font-size: 16pt; font-weight: 600; }}
    QLabel#cardTitle {{ font-size: 12pt; font-weight: 600; }}
    QLabel#badge {{ background: {p.raised}; border: 1px solid {p.border}; border-radius: 9px;
                    padding: 1px 8px; color: {p.muted}; }}

    QFrame#header {{ background: {p.surface}; border-bottom: 1px solid {p.border}; }}
    QFrame#actionBar {{ background: {p.surface}; border-top: 1px solid {p.border}; }}
    QFrame#card {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 10px; }}
    QFrame#chip {{ background: {p.raised}; border: 1px solid {p.border}; border-radius: 13px; }}
    QFrame#chip:hover {{ border-color: {p.muted}; }}
    QLabel#chipRank {{ color: {p.accent}; font-weight: 700; }}
    QToolButton#chipClose {{ background: transparent; border: none; border-radius: 9px; padding: 3px; }}
    QToolButton#chipClose:hover {{ background: {p.border}; }}
    QFrame#popup {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 8px; }}
    QListWidget {{ background: {p.surface}; border: none; outline: none; }}
    QListWidget::item {{ padding: 5px 6px; border-radius: 5px; }}
    QListWidget::item:hover {{ background: {p.raised}; }}
    QListWidget::item:selected {{ background: {p.selection}; color: {p.text}; }}
    QListWidget::indicator {{ width: 15px; height: 15px; border-radius: 4px; border: 1px solid {p.muted};
        background: {p.surface}; }}
    QListWidget::indicator:checked {{ background: {p.accent}; border-color: {p.accent}; {check} }}
    QFrame#banner {{ background: {p.raised}; border: 1px solid {p.border}; border-radius: 8px; }}
    QFrame#banner[level="error"] {{ border-color: {p.danger}; }}
    QFrame#banner[level="warning"] {{ border-color: {p.warning}; }}

    QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {{
        background: {p.raised}; color: {p.text}; border: 1px solid {p.border};
        border-radius: 7px; padding: 5px 9px; selection-background-color: {p.accent};
        selection-color: {p.accent_text};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{ border-color: {p.accent}; }}
    QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: {p.muted}; }}
    QLineEdit#search {{ font-size: 12pt; padding: 8px 10px; border-radius: 9px; }}
    QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{ background: {p.surface}; border: 1px solid {p.border};
        selection-background-color: {p.selection}; padding: 4px; }}

    QPushButton, QToolButton {{
        background: {p.raised}; color: {p.text}; border: 1px solid {p.border};
        border-radius: 7px; padding: 6px 12px;
    }}
    QPushButton:hover, QToolButton:hover {{ border-color: {p.muted}; }}
    QPushButton:pressed, QToolButton:pressed {{ background: {p.border}; }}
    QPushButton:disabled, QToolButton:disabled {{ color: {p.muted}; border-color: {p.border}; }}
    QPushButton[primary="true"] {{ background: {p.accent}; color: {p.accent_text}; border-color: {p.accent};
        font-weight: 600; }}
    QPushButton[primary="true"]:hover {{ background: {p.accent_hover}; border-color: {p.accent_hover}; }}
    QPushButton[primary="true"]:disabled {{ background: {p.raised}; color: {p.muted}; border-color: {p.border}; }}
    QPushButton[flat="true"], QToolButton[flat="true"] {{ background: transparent; border-color: transparent; }}
    QPushButton[flat="true"]:hover, QToolButton[flat="true"]:hover {{ background: {p.raised}; }}
    QPushButton[link="true"] {{ background: transparent; border: none; color: {p.accent}; padding: 2px 4px; }}
    QPushButton[link="true"]:hover {{ text-decoration: underline; }}
    QToolButton::menu-indicator {{ image: none; width: 0; }}

    QPushButton[segment="true"] {{ border-radius: 0; padding: 5px 11px; margin: 0; }}
    QPushButton[segment="true"][first="true"] {{ border-top-left-radius: 7px; border-bottom-left-radius: 7px; }}
    QPushButton[segment="true"][last="true"] {{ border-top-right-radius: 7px; border-bottom-right-radius: 7px; }}
    QPushButton[segment="true"]:checked {{ background: {p.accent}; color: {p.accent_text}; border-color: {p.accent}; }}

    QCheckBox {{ spacing: 7px; }}
    QCheckBox::indicator, QTreeView::indicator, QTableView::indicator {{
        width: 15px; height: 15px; border-radius: 4px; border: 1px solid {p.muted}; background: {p.surface};
    }}
    QCheckBox::indicator:checked, QTreeView::indicator:checked, QTableView::indicator:checked {{
        background: {p.accent}; border-color: {p.accent}; {check}
    }}

    QTreeView, QTableView {{
        background: {p.surface}; alternate-background-color: {p.surface}; border: 1px solid {p.border};
        border-radius: 10px; gridline-color: transparent; selection-background-color: {p.selection};
        selection-color: {p.text};
    }}
    QTreeView::item, QTableView::item {{ padding: 4px 2px; border: none; }}
    QTreeView::item:hover, QTableView::item:hover {{ background: {p.raised}; }}
    QTreeView::item:selected, QTableView::item:selected {{ background: {p.selection}; }}
    QHeaderView {{ background: transparent; }}
    QHeaderView::section {{
        background: {p.surface}; color: {p.muted}; border: none; border-bottom: 1px solid {p.border};
        padding: 6px 6px; font-weight: 600;
    }}
    QHeaderView::section:first {{ border-top-left-radius: 10px; }}

    QTabWidget::pane {{ border: none; }}
    QTabBar::tab {{ background: transparent; color: {p.muted}; padding: 7px 14px; border: none;
                    border-bottom: 2px solid transparent; font-weight: 600; }}
    QTabBar::tab:selected {{ color: {p.text}; border-bottom-color: {p.accent}; }}
    QTabBar::tab:hover {{ color: {p.text}; }}

    QProgressBar {{ background: {p.raised}; border: none; border-radius: 2px; max-height: 4px; }}
    QProgressBar::chunk {{ background: {p.accent}; border-radius: 2px; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle {{ background: {p.border}; border-radius: 4px; min-height: 30px; min-width: 30px; }}
    QScrollBar::handle:hover {{ background: {p.muted}; }}
    QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
        background: none; border: none; width: 0; height: 0; }}

    QMenu {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 8px; padding: 5px; }}
    QMenu::item {{ padding: 6px 22px 6px 12px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {p.raised}; }}
    QMenu::item:disabled {{ color: {p.muted}; }}
    QMenu::separator {{ height: 1px; background: {p.border}; margin: 4px 6px; }}
    QMenu::indicator {{ width: 14px; height: 14px; left: 4px; }}

    QStatusBar {{ background: {p.surface}; color: {p.muted}; border-top: 1px solid {p.border}; }}
    QStatusBar::item {{ border: none; }}
    QDockWidget {{ color: {p.text}; }}
    QDockWidget::title {{ background: {p.surface}; padding: 6px 10px; border-top: 1px solid {p.border}; }}
    QSplitter::handle {{ background: transparent; }}
    """


# 24×24 stroke icons; "currentColor" is replaced when rendering.
_SVG = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "settings": '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/>'
                '<circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>',
    "magnet": '<path d="M6 3v8a6 6 0 0 0 12 0V3M6 7h4M14 7h4"/>',
    "copy": '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 '
            '1-1h10a1 1 0 0 1 1 1v1"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "history": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "filter": '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21v-1a6 6 0 0 1 12 0v1M16 4a4 4 0 0 1 0 8M22 21v-1a6 '
             '6 0 0 0-4-5.6"/>',
    "check": '<path d="m5 12 5 5 9-10"/>',
    "more": '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    "tv": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="m8 2 4 4 4-4"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4'
           'M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    "alert": '<path d="M12 3 2 21h20zM12 10v4M12 18h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
}


@lru_cache(maxsize=256)
def icon(name: str, color: str | None = None, size: int = 18) -> QIcon:
    color = color or _current.text
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_SVG[name]}</svg>')
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    result = QIcon()
    for scale in (1, 2):
        pixmap = QPixmap(size * scale, size * scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter, QRectF(0, 0, size * scale, size * scale))
        painter.end()
        pixmap.setDevicePixelRatio(scale)
        result.addPixmap(pixmap)
    return result


def dot_icon(color: str, size: int = 10) -> QIcon:
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(QRectF(size * 0.5, size * 0.5, size, size))
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)
