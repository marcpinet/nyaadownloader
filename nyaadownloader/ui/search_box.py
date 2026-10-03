"""Search field with AniList-powered suggestions and recent searches."""

from __future__ import annotations

import logging

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QCompleter, QLineEdit, QStyle, QStyledItemDelegate, QStyleOptionViewItem

from nyaadownloader.core.anilist import AniListClient
from nyaadownloader.core.models import AnimeInfo
from nyaadownloader.ui import theme
from nyaadownloader.ui.tasks import Task, run_task

log = logging.getLogger(__name__)

ANIME_ROLE = Qt.ItemDataRole.UserRole + 10
SUBTITLE_ROLE = Qt.ItemDataRole.UserRole + 11
MIN_LOOKUP_LENGTH = 3


def describe(anime: AnimeInfo) -> str:
    parts = []
    if anime.english and anime.english.casefold() != anime.romaji.casefold():
        parts.append(anime.english)
    parts += [p for p in (anime.format, str(anime.year or "")) if p]
    if anime.episodes:
        parts.append(f"{anime.episodes} eps")
    if anime.status and anime.status != "Finished":
        parts.append(anime.status)
    return " · ".join(parts)


class _SuggestionDelegate(QStyledItemDelegate):
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        return QSize(option.rect.width(), 46 if index.data(SUBTITLE_ROLE) else 32)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        p = theme.current()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(p.selection))
            painter.drawRoundedRect(option.rect.adjusted(2, 1, -2, -1), 6, 6)
        rect = option.rect.adjusted(12, 5, -12, -5)
        subtitle = index.data(SUBTITLE_ROLE)
        title_font = QFont(option.font)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(p.text))
        title_rect = QRect(rect.left(), rect.top(), rect.width(), rect.height() // 2 if subtitle else rect.height())
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         painter.fontMetrics().elidedText(index.data(Qt.ItemDataRole.DisplayRole),
                                                          Qt.TextElideMode.ElideRight, rect.width()))
        if subtitle:
            painter.setFont(option.font)
            painter.setPen(QColor(p.muted))
            sub_rect = QRect(rect.left(), rect.top() + rect.height() // 2, rect.width(), rect.height() // 2)
            painter.drawText(sub_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             painter.fontMetrics().elidedText(subtitle, Qt.TextElideMode.ElideRight, rect.width()))
        painter.restore()


class SearchBox(QLineEdit):
    animeChosen = Signal(object)  # AnimeInfo | None
    submitted = Signal()

    def __init__(self, anilist: AniListClient, history: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("search")
        self.setPlaceholderText("Search an anime by its English or Japanese title, e.g. “Frieren”")
        self.setClearButtonEnabled(True)
        self._anilist = anilist
        self._history = history
        self._anime: AnimeInfo | None = None
        self._lookup_task: Task | None = None
        self._just_activated = False

        self._search_action = QAction(theme.icon("search", theme.current().muted), "", self)
        self.addAction(self._search_action, QLineEdit.ActionPosition.LeadingPosition)
        self._history_action = QAction(theme.icon("history", theme.current().muted), "Recent searches", self)
        self._history_action.triggered.connect(self.show_history)
        self.addAction(self._history_action, QLineEdit.ActionPosition.TrailingPosition)

        self._model = QStandardItemModel(self)
        self._completer = QCompleter(self._model, self)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self._completer.setMaxVisibleItems(8)
        self._completer.activated[QModelIndex].connect(self._on_activated)
        popup = self._completer.popup()
        popup.setItemDelegate(_SuggestionDelegate(popup))
        popup.setObjectName("suggestions")

        self._debounce = QTimer(self, singleShot=True, interval=300)
        self._debounce.timeout.connect(self._lookup)
        self.textEdited.connect(self._on_edited)
        self.returnPressed.connect(self._on_return)

    @property
    def anime(self) -> AnimeInfo | None:
        return self._anime

    def set_anime(self, anime: AnimeInfo | None, update_text: bool = True) -> None:
        self._anime = anime
        if anime and update_text:
            self.setText(anime.display_title)
        self.animeChosen.emit(anime)

    def refresh_icons(self) -> None:
        muted = theme.current().muted
        self._search_action.setIcon(theme.icon("search", muted))
        self._history_action.setIcon(theme.icon("history", muted))

    def show_history(self) -> None:
        self._model.clear()
        for entry in self._history:
            self._model.appendRow(QStandardItem(entry))
        if self._model.rowCount():
            self._popup()

    def _popup(self) -> None:
        rect = self.rect()
        rect.setWidth(max(rect.width(), 420))
        self._completer.complete(rect)

    def _on_edited(self, text: str) -> None:
        if self._anime and text != self._anime.display_title:
            self.set_anime(None, update_text=False)
        if len(text.strip()) >= MIN_LOOKUP_LENGTH:
            self._debounce.start()
        else:
            self._debounce.stop()
            self._completer.popup().hide()

    def _on_return(self) -> None:
        if self._just_activated:  # the completer forwards the Enter that picked a suggestion
            return
        self._debounce.stop()
        if self._lookup_task:
            self._lookup_task.cancel()
        popup = self._completer.popup()
        if popup.isVisible():
            current = popup.currentIndex()
            popup.hide()
            if current.isValid():
                self._on_activated(current)
                return
        self.submitted.emit()

    def _lookup(self) -> None:
        text = self.text().strip()
        if self._lookup_task:
            self._lookup_task.cancel()

        def done(results: list[AnimeInfo]) -> None:
            if self.text().strip() != text or not self.hasFocus():
                return
            self._model.clear()
            for anime in results:
                item = QStandardItem(anime.display_title)
                item.setData(anime, ANIME_ROLE)
                item.setData(describe(anime), SUBTITLE_ROLE)
                self._model.appendRow(item)
            if results:
                self._popup()
                self._completer.popup().setCurrentIndex(QModelIndex())

        self._lookup_task = run_task(
            lambda cancel, progress: self._anilist.search(text),
            on_result=done,
            on_error=lambda exc: log.info("AniList suggestions unavailable: %s", exc),
        )

    def _on_activated(self, index: QModelIndex) -> None:
        self._just_activated = True
        QTimer.singleShot(0, lambda: setattr(self, "_just_activated", False))
        self._debounce.stop()
        anime = index.data(ANIME_ROLE)
        if anime:
            self.set_anime(anime)
        else:
            self.setText(index.data(Qt.ItemDataRole.DisplayRole))
            self.set_anime(None, update_text=False)
        self.submitted.emit()
