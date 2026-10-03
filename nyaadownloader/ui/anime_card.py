"""Side card showing the AniList entry the search is linked to."""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from nyaadownloader.core.anilist import AniListClient
from nyaadownloader.core.models import AnimeInfo
from nyaadownloader.ui import theme
from nyaadownloader.ui.tasks import Task, run_task

log = logging.getLogger(__name__)
COVER_SIZE = QSize(180, 256)


def _rounded(pixmap: QPixmap, size: QSize, radius: float, ratio: float) -> QPixmap:
    target = QPixmap(size * ratio)
    target.setDevicePixelRatio(ratio)
    target.fill(Qt.GlobalColor.transparent)
    scaled = pixmap.scaled(size * ratio, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
    scaled.setDevicePixelRatio(ratio)
    painter = QPainter(target)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
    painter.setClipPath(path)
    x = (scaled.width() / ratio - size.width()) / 2
    y = (scaled.height() / ratio - size.height()) / 2
    painter.drawPixmap(int(-x), int(-y), scaled)
    painter.end()
    return target


class AnimeCard(QFrame):
    unlinkRequested = Signal()

    def __init__(self, anilist: AniListClient, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedWidth(COVER_SIZE.width() + 24)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._anilist = anilist
        self._anime: AnimeInfo | None = None
        self._cover_task: Task | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        self.cover = QLabel()
        self.cover.setFixedSize(COVER_SIZE)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cover)
        layout.addSpacing(4)

        self.title = QLabel(objectName="cardTitle", wordWrap=True)
        self.title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.english = QLabel(objectName="muted", wordWrap=True)
        self.english.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.meta = QLabel(objectName="muted", wordWrap=True)
        for widget in (self.title, self.english, self.meta):
            layout.addWidget(widget)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 4, 0, 0)
        self.open_button = QPushButton("AniList", flat=True)
        self.open_button.setProperty("flat", True)
        self.open_button.setToolTip("Open this anime on AniList")
        self.open_button.clicked.connect(self._open)
        self.unlink_button = QPushButton("Unlink", flat=True)
        self.unlink_button.setProperty("flat", True)
        self.unlink_button.setToolTip("Search the raw text instead of this AniList entry")
        self.unlink_button.clicked.connect(self.unlinkRequested)
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.unlink_button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.refresh_icons()

    def refresh_icons(self) -> None:
        self.open_button.setIcon(theme.icon("external", theme.current().muted, 16))
        self.unlink_button.setIcon(theme.icon("close", theme.current().muted, 16))

    @property
    def anime(self) -> AnimeInfo | None:
        return self._anime

    def show_anime(self, anime: AnimeInfo | None) -> None:
        if anime == self._anime:
            self.setVisible(anime is not None)
            return
        self._anime = anime
        if self._cover_task:
            self._cover_task.cancel()
        if anime is None:
            self.hide()
            return
        self.title.setText(anime.display_title)
        english = anime.english if anime.english and anime.english != anime.display_title else ""
        self.english.setText(english)
        self.english.setVisible(bool(english))
        meta = [p for p in (anime.format, str(anime.year or ""), anime.status) if p]
        if anime.episodes:
            meta.append(f"{anime.episodes} episodes")
        elif anime.aired_episodes:
            meta.append(f"{anime.aired_episodes} episodes aired")
        if anime.next_episode:
            meta.append(f"next: ep. {anime.next_episode}")
        self.meta.setText(" · ".join(meta))
        self.open_button.setVisible(bool(anime.site_url))
        self._placeholder(anime)
        self.show()
        if anime.cover_url:
            self._cover_task = run_task(
                lambda cancel, progress: self._anilist.fetch_image(anime.cover_url),
                on_result=lambda data: self._set_cover(anime, data),
                on_error=lambda exc: log.info("%s", exc),
            )

    def _placeholder(self, anime: AnimeInfo) -> None:
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(COVER_SIZE * ratio)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(anime.color or theme.current().raised))
        painter.drawRoundedRect(0, 0, COVER_SIZE.width(), COVER_SIZE.height(), 8, 8)
        painter.end()
        self.cover.setPixmap(pixmap)

    def _set_cover(self, anime: AnimeInfo, data: bytes) -> None:
        if anime != self._anime:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.cover.setPixmap(_rounded(pixmap, COVER_SIZE, 8, self.devicePixelRatioF()))

    def _open(self) -> None:
        if self._anime and self._anime.site_url:
            QDesktopServices.openUrl(QUrl(self._anime.site_url))
