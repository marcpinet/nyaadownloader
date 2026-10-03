from __future__ import annotations

import logging
import os
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QModelIndex, QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QGuiApplication, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableView,
    QTabWidget,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from nyaadownloader import APP_NAME, REPO_URL, __version__
from nyaadownloader.core.anilist import AniListClient, resolve_title
from nyaadownloader.core.downloads import DownloadReport, download_torrents
from nyaadownloader.core.errors import NetworkError, NyaaDownloaderError
from nyaadownloader.core.files import sanitize_filename
from nyaadownloader.core.models import Category, ParsedRelease, Release
from nyaadownloader.core.nyaa import NyaaClient, format_size, make_http_client
from nyaadownloader.core.parsing import parse_release
from nyaadownloader.core.search import SearchOutcome, SearchRequest, run_search
from nyaadownloader.core.settings import Settings
from nyaadownloader.resources import logo_pixmap
from nyaadownloader.ui import theme
from nyaadownloader.ui.anime_card import AnimeCard
from nyaadownloader.ui.notify import Notifier
from nyaadownloader.ui.pickers import EpisodeRange, UploaderPicker
from nyaadownloader.ui.results import (
    DATE,
    EPISODE,
    GROUP,
    LEECHERS,
    NAME,
    QUALITY,
    SEEDERS,
    SIZE,
    BatchesModel,
    EpisodesModel,
    EpisodesProxy,
    SortProxy,
    release_tooltip,
    season_display,
)
from nyaadownloader.ui.search_box import SearchBox
from nyaadownloader.ui.settings_dialog import SettingsDialog
from nyaadownloader.ui.tasks import Task, run_task

log = logging.getLogger(__name__)

RESOLUTIONS = (("Any", None), ("480p", 480), ("720p", 720), ("1080p", 1080), ("2160p", 2160))
MAGNET_INTERVAL_MS = 350
MAGNET_CONFIRM_THRESHOLD = 25
NOTIFY_AFTER_SECONDS = 8


def _is_checked(value) -> bool:
    return value in (Qt.CheckState.Checked, Qt.CheckState.Checked.value)


class ReleaseTree(QTreeView):
    """Tree whose Space key toggles the check box of every selected episode."""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and self.selectionModel().selectedRows():
            rows = [i for i in self.selectionModel().selectedRows() if not i.parent().isValid()]
            checkable = [i for i in rows if i.flags() & Qt.ItemFlag.ItemIsUserCheckable]
            if checkable:
                target = (Qt.CheckState.Unchecked if _is_checked(checkable[0].data(Qt.ItemDataRole.CheckStateRole))
                          else Qt.CheckState.Checked)
                for index in checkable:
                    self.model().setData(index, target.value, Qt.ItemDataRole.CheckStateRole)
                return
        super().keyPressEvent(event)


class ReleaseTable(QTableView):
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and self.selectionModel().selectedRows():
            rows = self.selectionModel().selectedRows()
            target = (Qt.CheckState.Unchecked if _is_checked(rows[0].data(Qt.ItemDataRole.CheckStateRole))
                      else Qt.CheckState.Checked)
            for index in rows:
                self.model().setData(index, target.value, Qt.ItemDataRole.CheckStateRole)
            return
        super().keyPressEvent(event)


class Banner(QFrame):
    """Inline, dismissible message with an optional action button."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("banner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        self.icon = QLabel()
        self.text = QLabel(wordWrap=True)
        self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.action = QPushButton()
        self.action.hide()
        self.close_button = QToolButton()
        self.close_button.setProperty("flat", True)
        self.close_button.clicked.connect(self.hide)
        layout.addWidget(self.icon)
        layout.addWidget(self.text, 1)
        layout.addWidget(self.action)
        layout.addWidget(self.close_button)
        self._callback = None
        self.action.clicked.connect(self._run_action)
        self.hide()

    def show_message(self, text: str, level: str = "info", action: str | None = None, callback=None) -> None:
        p = theme.current()
        color = {"error": p.danger, "warning": p.warning}.get(level, p.accent)
        self.setProperty("level", level)
        self.style().unpolish(self)
        self.style().polish(self)
        self.icon.setPixmap(theme.icon("info" if level == "info" else "alert", color, 18).pixmap(18, 18))
        self.close_button.setIcon(theme.icon("close", p.muted, 16))
        self.text.setText(text)
        self._callback = callback
        self.action.setVisible(bool(action))
        if action:
            self.action.setText(action)
        self.show()

    def _run_action(self) -> None:
        callback = self._callback
        self.hide()
        if callback:
            callback()


class EmptyState(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch(2)
        self.icon = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel(objectName="emptyTitle", alignment=Qt.AlignmentFlag.AlignCenter)
        self.body = QLabel(objectName="muted", alignment=Qt.AlignmentFlag.AlignCenter, wordWrap=True)
        self.body.setFixedWidth(540)
        self.body.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.icon)
        layout.addSpacing(6)
        layout.addWidget(self.title)
        layout.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(3)
        self._icon_name = "logo"

    def set_content(self, icon: str, title: str, body: str) -> None:
        self._icon_name = icon
        self.title.setText(title)
        self.body.setText(body)
        self.refresh_icons()

    def refresh_icons(self) -> None:
        if self._icon_name == "logo":
            self.icon.setPixmap(logo_pixmap(132))
        else:
            self.icon.setPixmap(theme.icon(self._icon_name, theme.current().muted, 56).pixmap(56, 56))


WELCOME_TEXT = (
    "Type a title in English or Japanese: suggestions come from AniList and are translated "
    "to the name uploaders actually use.<br><br>"
    "Uploaders are searched in order and the first one is preferred. Remove them all to search everyone.<br>"
    "Untick the episodes you don't want, then grab the .torrent files or send magnets to your client."
)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings, icon_path: str) -> None:
        super().__init__()
        self.settings = settings
        self.http = make_http_client()
        self.nyaa = NyaaClient(settings.base_url, self.http)
        self.anilist = AniListClient(self.http)
        self.notifier = Notifier(self, icon_path)

        self._search_task: Task | None = None
        self._download_task: Task | None = None
        self._outcome: SearchOutcome | None = None
        self._auto_link = True
        self._open_queue: list[QUrl] = []
        self._open_timer = QTimer(self, interval=MAGNET_INTERVAL_MS)
        self._open_timer.timeout.connect(self._open_next)
        self._icons: list[tuple[QWidget, str, str]] = []

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(980, 620)
        self.resize(1280, 800)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self._build_action_bar())
        self.setCentralWidget(central)
        self._build_activity_dock()
        self._build_status_bar()
        self._build_shortcuts()
        self._load_filters()
        self._restore_state()
        self._update_selection()
        self.refresh_icons()
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_system_theme_changed)

    # ------------------------------------------------------------------ build
    def _iconify(self, widget: QWidget, name: str, color: str = "text") -> None:
        self._icons.append((widget, name, color))

    def _build_header(self) -> QWidget:
        header = QFrame(objectName="header")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 0)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(10)
        self.search_box = SearchBox(self.anilist, self.settings.history)
        self.search_box.submitted.connect(self.start_search)
        self.search_box.animeChosen.connect(self._on_anime_chosen)
        self.search_box.textEdited.connect(lambda _: setattr(self, "_auto_link", True))
        logo = QLabel()
        logo.setPixmap(logo_pixmap(40))
        logo.setToolTip(f"{APP_NAME} {__version__}")
        top.addWidget(logo)
        top.addSpacing(2)
        top.addWidget(self.search_box, 1)

        self.search_button = QPushButton("Search")
        self.search_button.setProperty("primary", True)
        self.search_button.setMinimumWidth(110)
        self.search_button.setMinimumHeight(38)
        self.search_button.clicked.connect(self._on_search_button)
        self._iconify(self.search_button, "search", "accent_text")
        top.addWidget(self.search_button)

        self.options_button = QToolButton()
        self.options_button.setToolTip("More options")
        self.options_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.options_button.setMinimumHeight(38)
        self._iconify(self.options_button, "more")
        self.options_button.setMenu(self._build_options_menu())
        top.addWidget(self.options_button)

        self.theme_button = QToolButton()
        self.theme_button.setMinimumHeight(38)
        self.theme_button.clicked.connect(self.toggle_theme)
        top.addWidget(self.theme_button)

        settings_button = QToolButton()
        settings_button.setToolTip("Settings (Ctrl+,)")
        settings_button.setMinimumHeight(38)
        settings_button.clicked.connect(self.open_settings)
        self._iconify(settings_button, "settings")
        top.addWidget(settings_button)
        layout.addLayout(top)

        filters = QHBoxLayout()
        filters.setSpacing(8)
        filters.addWidget(QLabel("Uploaders", objectName="muted"))
        self.uploaders = UploaderPicker()
        filters.addWidget(self.uploaders, 3)
        filters.addSpacing(12)

        filters.addWidget(QLabel("Quality", objectName="muted"))
        self.quality_group = QButtonGroup(self)
        self.quality_group.setExclusive(True)
        segments = QHBoxLayout()
        segments.setSpacing(0)
        for i, (label, value) in enumerate(RESOLUTIONS):
            button = QPushButton(label, checkable=True)
            button.setProperty("segment", True)
            button.setProperty("first", i == 0)
            button.setProperty("last", i == len(RESOLUTIONS) - 1)
            button.setProperty("resolution", value)
            self.quality_group.addButton(button, i)
            segments.addWidget(button)
        filters.addLayout(segments)
        filters.addSpacing(12)

        self.episodes = EpisodeRange()
        filters.addWidget(self.episodes)
        filters.addSpacing(12)

        self.trusted_only = QCheckBox("Trusted only")
        self.trusted_only.setToolTip("Only show releases from uploaders Nyaa marks as trusted (green)")
        filters.addWidget(self.trusted_only)
        filters.addStretch(1)
        layout.addLayout(filters)

        self.search_progress = QProgressBar()
        self.search_progress.setTextVisible(False)
        self.search_progress.setFixedHeight(3)
        self.search_progress.setRange(0, 0)
        progress_holder = QWidget()
        progress_holder.setFixedHeight(3)
        holder_layout = QVBoxLayout(progress_holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(self.search_progress)
        self.search_progress.hide()
        layout.addSpacing(9)
        layout.addWidget(progress_holder)
        return header

    def _build_options_menu(self) -> QMenu:
        menu = QMenu(self)
        self.loose_action = menu.addAction("Loose title matching")
        self.loose_action.setCheckable(True)
        self.loose_action.setToolTip("Also accept releases whose title only resembles the search")
        self.remakes_action = menu.addAction("Include remakes")
        self.remakes_action.setCheckable(True)
        category_menu = menu.addMenu("Category")
        self.category_actions: dict[str, QAction] = {}
        for category in Category:
            action = category_menu.addAction(category.label)
            action.setCheckable(True)
            action.triggered.connect(lambda _=False, c=category: self._set_category(c))
            self.category_actions[category.value] = action
        menu.addSeparator()
        menu.addAction("Analyze a release title…", self.analyze_title)
        menu.addAction("Open download folder", self.open_download_folder)
        menu.addSeparator()
        menu.addAction(f"About {APP_NAME}", self.show_about)
        return menu

    def _build_body(self) -> QWidget:
        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(16)

        side = QVBoxLayout()
        self.card = AnimeCard(self.anilist)
        self.card.unlinkRequested.connect(self._unlink_anime)
        self.card.hide()
        side.addWidget(self.card)
        side.addStretch(1)
        layout.addLayout(side)

        self.stack = QStackedWidget()
        self.empty = EmptyState()
        self.empty.set_content("logo", "Find an anime", WELCOME_TEXT)
        self.stack.addWidget(self.empty)

        results = QWidget()
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(10)
        self.banner = Banner()
        results_layout.addWidget(self.banner)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.season_combo = QComboBox()
        self.season_combo.setMinimumWidth(190)
        self.season_combo.setToolTip("Releases are grouped by how uploaders number seasons")
        self.season_combo.currentIndexChanged.connect(self._on_season_changed)
        toolbar.addWidget(self.season_combo)
        self.summary = QLabel(objectName="muted")
        toolbar.addWidget(self.summary, 1)
        self.hide_missing = QCheckBox("Hide missing")
        self.hide_missing.toggled.connect(self._on_hide_missing)
        toolbar.addWidget(self.hide_missing)
        select_all = QPushButton("Select all")
        select_all.setProperty("flat", True)
        select_all.clicked.connect(lambda: self._check_visible(True))
        select_none = QPushButton("Select none")
        select_none.setProperty("flat", True)
        select_none.clicked.connect(lambda: self._check_visible(False))
        toolbar.addWidget(select_all)
        toolbar.addWidget(select_none)
        results_layout.addLayout(toolbar)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.episodes_model = EpisodesModel(self)
        self.episodes_model.checkedChanged.connect(self._update_selection)
        self.episodes_proxy = EpisodesProxy(self)
        self.episodes_proxy.setSourceModel(self.episodes_model)
        self.tree = ReleaseTree()
        self.tree.setModel(self.episodes_proxy)
        self._setup_view(self.tree)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.doubleClicked.connect(self._on_tree_double_click)
        self.tree.customContextMenuRequested.connect(self._tree_menu)
        self.tabs.addTab(self.tree, "Episodes")

        self.batches_model = BatchesModel(self)
        self.batches_model.checkedChanged.connect(self._update_selection)
        self.batches_proxy = SortProxy(self)
        self.batches_proxy.setSourceModel(self.batches_model)
        self.batches_view = ReleaseTable()
        self.batches_view.setModel(self.batches_proxy)
        self._setup_view(self.batches_view)
        self.batches_view.verticalHeader().hide()
        self.batches_view.setShowGrid(False)
        self.batches_view.customContextMenuRequested.connect(self._batches_menu)
        self.tabs.addTab(self.batches_view, "Batches && specials")
        results_layout.addWidget(self.tabs, 1)

        self.stack.addWidget(results)
        layout.addWidget(self.stack, 1)
        return body

    def _setup_view(self, view: QAbstractItemView) -> None:
        view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view.setSortingEnabled(True)
        view.setAlternatingRowColors(False)
        view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        view.setMouseTracking(True)
        header = view.horizontalHeader() if isinstance(view, QTableView) else view.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(NAME, QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(False)
        widths = {EPISODE: 130, GROUP: 110, QUALITY: 130, SIZE: 84, SEEDERS: 72, LEECHERS: 76, DATE: 96}
        for column, width in widths.items():
            header.resizeSection(column, width)
        header.setSortIndicator(EPISODE, Qt.SortOrder.AscendingOrder)

    def _build_action_bar(self) -> QWidget:
        bar = QFrame(objectName="actionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(8)
        self.selection_label = QLabel()
        layout.addWidget(self.selection_label)
        self.folder_button = QPushButton()
        self.folder_button.setProperty("link", True)
        self.folder_button.setToolTip("Open the download folder (right-click to change it)")
        self.folder_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_button.customContextMenuRequested.connect(lambda _: self._choose_download_dir())
        self.folder_button.clicked.connect(self.open_download_folder)
        self._iconify(self.folder_button, "folder", "accent")
        layout.addWidget(self.folder_button)
        layout.addStretch(1)

        self.download_progress = QProgressBar()
        self.download_progress.setTextVisible(False)
        self.download_progress.setFixedWidth(160)
        self.download_progress.hide()
        layout.addWidget(self.download_progress)
        self.cancel_download = QPushButton("Cancel")
        self.cancel_download.hide()
        self.cancel_download.clicked.connect(self._cancel_download)
        layout.addWidget(self.cancel_download)

        self.copy_button = QPushButton("Copy magnets")
        self.copy_button.setToolTip("Copy the magnet links of the selected releases (Ctrl+Shift+C)")
        self.copy_button.clicked.connect(lambda: self.copy_magnets())
        self._iconify(self.copy_button, "copy")
        self.magnet_button = QPushButton("Open magnets")
        self.magnet_button.setToolTip("Send the selected releases to your torrent client")
        self.magnet_button.clicked.connect(lambda: self.open_magnets())
        self._iconify(self.magnet_button, "magnet")
        self.download_button = QPushButton("Download .torrent")
        self.download_button.setProperty("primary", True)
        self.download_button.setToolTip("Save the .torrent files of the selected releases (Ctrl+S)")
        self.download_button.clicked.connect(lambda: self.download_selected())
        self._iconify(self.download_button, "download", "accent_text")
        for button in (self.copy_button, self.magnet_button, self.download_button):
            button.setMinimumHeight(36)
            layout.addWidget(button)
        return bar

    def _build_activity_dock(self) -> None:
        self.activity = QPlainTextEdit(readOnly=True)
        self.activity.setMaximumBlockCount(5000)
        self.activity.setPlaceholderText("Searches, downloads and errors are logged here.")
        dock_body = QWidget()
        dock_layout = QVBoxLayout(dock_body)
        dock_layout.setContentsMargins(12, 6, 12, 10)
        dock_layout.addWidget(self.activity)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.activity.clear)
        save = QPushButton("Save as…")
        save.clicked.connect(self.save_activity)
        buttons.addWidget(clear)
        buttons.addWidget(save)
        dock_layout.addLayout(buttons)
        self.dock = QDockWidget("Activity", self)
        self.dock.setObjectName("activityDock")
        self.dock.setWidget(dock_body)
        self.dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable
                              | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock)
        self.dock.hide()

    def _build_status_bar(self) -> None:
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        self.activity_button = QToolButton()
        self.activity_button.setText("Activity")
        self.activity_button.setProperty("flat", True)
        self.activity_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.activity_button.setCheckable(True)
        self.activity_button.toggled.connect(self.dock.setVisible)
        self.dock.visibilityChanged.connect(self.activity_button.setChecked)
        self._iconify(self.activity_button, "list", "muted")
        status.addPermanentWidget(self.activity_button)
        version = QLabel(f"v{__version__}  ", objectName="muted")
        status.addPermanentWidget(version)

    def _build_shortcuts(self) -> None:
        bindings = {
            "Ctrl+F": lambda: (self.search_box.setFocus(), self.search_box.selectAll()),
            "Ctrl+L": lambda: (self.search_box.setFocus(), self.search_box.selectAll()),
            "Ctrl+S": self.download_selected,
            "Ctrl+Shift+C": self.copy_magnets,
            "Ctrl+,": self.open_settings,
            "Ctrl+T": self.toggle_theme,
            "Escape": self.cancel_search,
        }
        for keys, slot in bindings.items():
            QShortcut(QKeySequence(keys), self, activated=slot)

    def refresh_icons(self) -> None:
        p = theme.current()
        for widget, name, color in self._icons:
            widget.setIcon(theme.icon(name, getattr(p, color)))
        self.search_box.refresh_icons()
        self.uploaders.refresh_icons()
        self.card.refresh_icons()
        self.empty.refresh_icons()
        dark = p.name == "dark"
        self.theme_button.setIcon(theme.icon("sun" if dark else "moon"))
        self.theme_button.setToolTip(f"Switch to {'light' if dark else 'dark'} theme (Ctrl+T)")
        self._update_folder_button()

    # ------------------------------------------------------------- filters
    def _load_filters(self) -> None:
        s = self.settings
        self.uploaders.set_uploaders(s.uploaders)
        index = next((i for i, (_, v) in enumerate(RESOLUTIONS) if v == s.resolution), 3)
        self.quality_group.button(index).setChecked(True)
        self.trusted_only.setChecked(s.trusted_only)
        self.loose_action.setChecked(s.loose_matching)
        self.remakes_action.setChecked(s.include_remakes)
        self._set_category(Category(s.category))

    def _save_filters(self) -> None:
        s = self.settings
        s.uploaders = self.uploaders.uploaders()
        s.resolution = self._resolution()
        s.trusted_only = self.trusted_only.isChecked()
        s.loose_matching = self.loose_action.isChecked()
        s.include_remakes = self.remakes_action.isChecked()

    def _resolution(self) -> int | None:
        button = self.quality_group.checkedButton()
        return button.property("resolution") if button else None

    def _set_category(self, category: Category) -> None:
        self.settings.category = category.value
        for value, action in self.category_actions.items():
            action.setChecked(value == category.value)

    # -------------------------------------------------------------- search
    def _on_anime_chosen(self, anime) -> None:
        previous = self.card.anime
        self.card.show_anime(anime)
        if anime is not None and (previous is None or previous.id != anime.id):
            # A different show: an episode range picked for the previous one makes no sense.
            self.episodes.reset(anime.aired_episodes)

    def _unlink_anime(self) -> None:
        self._auto_link = False
        self.search_box.set_anime(None, update_text=False)

    def _on_search_button(self) -> None:
        if self._search_task:
            self.cancel_search()
        else:
            self.start_search()

    def _build_request(self, text: str) -> SearchRequest:
        first, last = self.episodes.episode_range()
        return SearchRequest(
            query=text,
            anime=self.search_box.anime,
            uploaders=tuple(self.uploaders.uploaders()),
            resolution=self._resolution(),
            first_episode=first,
            last_episode=last,
            trusted_only=self.trusted_only.isChecked(),
            include_remakes=self.remakes_action.isChecked(),
            loose=self.loose_action.isChecked(),
            category=Category(self.settings.category),
        )

    def start_search(self) -> None:
        text = " ".join(self.search_box.text().split())
        if len(text) < 2:
            self.search_box.setFocus()
            self.statusBar().showMessage("Type at least two characters to search.", 4000)
            return
        if self._search_task:
            self._search_task.cancel()

        request = self._build_request(text)
        self._save_filters()
        self.settings.remember_search(text)
        self.settings.save()
        auto_link = self._auto_link and request.anime is None

        def work(cancel, progress) -> tuple[SearchOutcome, bool]:
            req = request
            linked = False
            if auto_link:
                anime = resolve_title(self.anilist, text)
                if anime is not None:
                    req, linked = replace(req, anime=anime), True
            return run_search(self.nyaa, req, cancel, progress), linked

        log.info("Searching “%s”%s…", text, f" from {', '.join(request.uploaders)}" if request.uploaders else "")
        self._set_searching(True)
        task = run_task(work, on_progress=self._on_search_progress)
        task.signals.result.connect(lambda result: self._on_search_done(task, *result))
        task.signals.error.connect(lambda exc: self._on_search_error(task, exc))
        task.signals.finished.connect(lambda: self._on_search_finished(task))
        self._search_task = task

    def cancel_search(self) -> None:
        if self._search_task:
            self._search_task.cancel()
            log.info("Search cancelled.")
            self._search_task = None
            self._set_searching(False)

    def _set_searching(self, busy: bool) -> None:
        self.search_progress.setVisible(busy)
        self.search_progress.setRange(0, 0)
        self.search_button.setText("Stop" if busy else "Search")
        self._icons = [(w, n, c) for w, n, c in self._icons if w is not self.search_button]
        self._iconify(self.search_button, "stop" if busy else "search", "accent_text")
        self.search_button.setIcon(theme.icon("stop" if busy else "search", theme.current().accent_text))
        if busy and self.stack.currentIndex() == 0:
            self.empty.set_content("search", "Searching Nyaa…", "Fetching every result page in parallel.")

    def _on_search_progress(self, done: int, total: int) -> None:
        if total > 1:
            self.search_progress.setRange(0, total)
            self.search_progress.setValue(done)

    def _on_search_finished(self, task: Task) -> None:
        if task is self._search_task:
            self._search_task = None
            self._set_searching(False)

    def _on_search_error(self, task: Task, exc: Exception) -> None:
        if task is not self._search_task:
            return
        message = str(exc) if isinstance(exc, NyaaDownloaderError) else f"Unexpected error: {exc!r}"
        log.error("Search failed: %s", message)
        if isinstance(exc, NetworkError):
            message += " Check your connection, or set a Nyaa mirror in Settings."
        if self.stack.currentIndex() == 0:
            self.empty.set_content("alert", "Search failed", message)
            self.banner.hide()
        else:
            self.banner.show_message(message, "error", "Retry", self.start_search)

    def _on_search_done(self, task: Task, outcome: SearchOutcome, linked: bool) -> None:
        if task is not self._search_task:
            return
        self._outcome = outcome
        if linked:
            self.search_box.set_anime(outcome.request.anime, update_text=False)
        result = outcome.result
        found = [s for s in result.episodes if not s.missing]
        missing = len(result.episodes) - len(found)
        log.info("“%s”: %d episodes, %d missing, %d batches/specials from %d releases in %.1fs.",
                 outcome.request.query, len(found), missing, len(result.batches), outcome.fetched,
                 outcome.elapsed)

        if not found and not result.batches:
            self.stack.setCurrentIndex(0)
            self.empty.set_content("search", "Nothing matched", self._no_results_hint(outcome))
            self._populate(outcome)
            return

        self.stack.setCurrentIndex(1)
        self._populate(outcome)
        messages = list(outcome.warnings)
        if outcome.truncated:
            messages.append("Nyaa only returns the newest 1000 results: set a last episode to reach older ones.")
        if messages:
            self.banner.show_message(" ".join(messages), "warning")
        else:
            self.banner.hide()
        self.tabs.setCurrentIndex(0 if found else 1)
        if outcome.elapsed > NOTIFY_AFTER_SECONDS and self.settings.notifications:
            self.notifier.notify(APP_NAME, f"Search finished: {len(found)} episodes of {outcome.request.query}.")

    def _no_results_hint(self, outcome: SearchOutcome) -> str:
        result = outcome.result
        tips = []
        if outcome.fetched == 0:
            tips.append("Nyaa returned no release for this search.")
            if outcome.request.anime is None:
                tips.append("Try the Japanese title (pick an AniList suggestion) or check the spelling.")
            if outcome.request.uploaders:
                tips.append("Try removing the selected uploaders to search everyone.")
        else:
            tips.append(f"Nyaa returned {outcome.fetched} releases but none matched:")
            if result.rejected_title:
                hint = ("pick an AniList suggestion while typing, or try “Loose title matching” in the ⋯ menu"
                        if outcome.request.anime is None else "try “Loose title matching” in the ⋯ menu")
                tips.append(f"• {result.rejected_title} had a different title: {hint}.")
            if result.rejected_quality:
                tips.append(f"• {result.rejected_quality} were in another quality: try “Any”.")
            if result.rejected_other:
                tips.append(f"• {result.rejected_other} were remakes or outside the episode range.")
        return "<br>".join(tips)

    def _populate(self, outcome: SearchOutcome) -> None:
        result = outcome.result
        self.episodes_model.set_slots(result.episodes)
        self.batches_model.set_releases(result.batches)

        self.season_combo.blockSignals(True)
        self.season_combo.clear()
        counts = {label: sum(1 for s in result.episodes if s.season_label == label and not s.missing)
                  for label in result.season_labels}
        self.season_combo.addItem(f"All seasons ({sum(counts.values())})", None)
        for label in result.season_labels:
            self.season_combo.addItem(f"{season_display(label)} ({counts[label]})", label)
        preferred = self.season_combo.findData(result.preferred_season) if result.preferred_season else 0
        self.season_combo.setCurrentIndex(max(0, preferred))
        self.season_combo.setVisible(len(result.season_labels) > 1)
        self.season_combo.blockSignals(False)
        self._on_season_changed()

        self.tabs.setTabText(1, f"Batches && specials ({len(result.batches)})")
        self.tree.sortByColumn(EPISODE, Qt.SortOrder.AscendingOrder)
        self._update_folder_button()

    def _on_season_changed(self, *_) -> None:
        season = self.season_combo.currentData()
        self.episodes_proxy.set_season(season)
        self._update_summary()
        self._update_selection()

    def _on_hide_missing(self, hide: bool) -> None:
        self.episodes_proxy.set_hide_missing(hide)
        self._update_summary()

    def _update_summary(self) -> None:
        if not self._outcome:
            self.summary.clear()
            return
        slots = self.episodes_model.slots()
        season = self.season_combo.currentData()
        visible = [s for s in slots if season is None or s.season_label == season]
        missing = sum(1 for s in visible if s.missing)
        self.tabs.setTabText(0, f"Episodes ({len(visible) - missing})")
        parts = [f"{len(visible) - missing} episodes"]
        if missing:
            parts.append(f"{missing} missing")
        parts.append(f"{self._outcome.fetched} releases scanned in {self._outcome.elapsed:.1f}s")
        self.summary.setText(" · ".join(parts))

    def _check_visible(self, checked: bool) -> None:
        if self.tabs.currentIndex() == 0:
            self.episodes_model.set_all_checked(self.episodes_proxy.visible_source_rows(), checked)
        else:
            self.batches_model.set_all_checked(checked)

    # ----------------------------------------------------------- selection
    def selected_releases(self) -> list[ParsedRelease]:
        slots = self.episodes_model.slots()
        episodes = [slots[r].release for r in sorted(self.episodes_proxy.visible_source_rows())
                    if self.episodes_model.is_checked(r) and slots[r].release]
        return episodes + self.batches_model.checked_releases()

    def _update_selection(self) -> None:
        releases = self.selected_releases()
        batches = len(self.batches_model.checked_releases())
        episodes = len(releases) - batches
        if not releases:
            text = "Nothing selected"
        else:
            parts = []
            if episodes:
                parts.append(f"{episodes} episode{'s' * (episodes != 1)}")
            if batches:
                parts.append(f"{batches} batch{'es' * (batches != 1)}")
            size = sum(r.release.size_bytes for r in releases)
            text = f"{' + '.join(parts)} selected · {format_size(size)}"
        self.selection_label.setText(text)
        idle = self._download_task is None
        for button in (self.copy_button, self.magnet_button, self.download_button):
            button.setEnabled(bool(releases) and idle)

    # ----------------------------------------------------------- downloads
    def _target_folder(self) -> Path:
        folder = Path(os.path.expandvars(os.path.expanduser(self.settings.download_dir)))
        if self.settings.subfolder_per_anime and self._outcome:
            request = self._outcome.request
            name = request.anime.display_title if request.anime else request.query
            folder /= sanitize_filename(name)
        return folder

    def _update_folder_button(self) -> None:
        folder = self._target_folder()
        text = str(folder)
        home = str(Path.home())
        if text.startswith(home):
            text = "~" + text[len(home):]
        metrics = self.folder_button.fontMetrics()
        self.folder_button.setText(metrics.elidedText(text, Qt.TextElideMode.ElideMiddle, 340))

    def _choose_download_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Save .torrent files to", self.settings.download_dir)
        if folder:
            self.settings.download_dir = folder
            self.settings.save()
            self._update_folder_button()

    def open_download_folder(self) -> None:
        folder = self._target_folder()
        while not folder.exists() and folder.parent != folder:
            folder = folder.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def download_selected(self, releases: list[ParsedRelease] | None = None) -> None:
        releases = releases or self.selected_releases()
        if not releases or self._download_task:
            return
        folder = self._target_folder()
        log.info("Downloading %d .torrent file(s) to %s…", len(releases), folder)
        self.download_progress.setRange(0, len(releases))
        self.download_progress.setValue(0)
        self.download_progress.show()
        self.cancel_download.show()
        started = datetime.now(UTC)
        task = run_task(
            lambda cancel, progress: download_torrents(self.nyaa, releases, folder, cancel, progress),
            on_result=lambda report: self._on_download_done(report, started),
            on_error=self._on_download_error,
            on_progress=lambda done, total: self.download_progress.setValue(done),
            on_finished=self._on_download_finished,
        )
        self._download_task = task
        self._update_selection()

    def _cancel_download(self) -> None:
        if self._download_task:
            self._download_task.cancel()
            log.info("Download cancelled.")

    def _on_download_finished(self) -> None:
        self._download_task = None
        self.download_progress.hide()
        self.cancel_download.hide()
        self._update_selection()

    def _on_download_error(self, exc: Exception) -> None:
        log.error("Download failed: %s", exc)
        self._show_banner(f"Download failed: {exc}", "error")

    def _on_download_done(self, report: DownloadReport, started: datetime) -> None:
        saved, skipped, failed = len(report.saved), len(report.skipped), len(report.failed)
        for release, reason in report.failed:
            log.error("Could not download “%s”: %s", release.release.name, reason)
        parts = [f"Saved {saved} .torrent file{'s' * (saved != 1)}"]
        if skipped:
            parts.append(f"{skipped} already there")
        if failed:
            parts.append(f"{failed} failed (see Activity)")
        message = ", ".join(parts) + "."
        log.info("%s Folder: %s", message, report.folder)
        self._show_banner(message, "warning" if failed else "info", "Open folder",
                          lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(report.folder))))
        if self.settings.open_torrents_after_download and report.saved:
            self._queue_urls([QUrl.fromLocalFile(str(p)) for p in report.saved])
        elapsed = (datetime.now(UTC) - started).total_seconds()
        if elapsed > NOTIFY_AFTER_SECONDS and self.settings.notifications:
            self.notifier.notify(APP_NAME, message)

    def _show_banner(self, text: str, level: str, action: str | None = None, callback=None) -> None:
        if self.stack.currentIndex() == 1:
            self.banner.show_message(text, level, action, callback)
        else:
            self.statusBar().showMessage(text, 8000)

    def copy_magnets(self, releases: list[ParsedRelease] | None = None) -> None:
        releases = releases or self.selected_releases()
        magnets = [r.release.magnet for r in releases if r.release.magnet]
        if not magnets:
            return
        QApplication.clipboard().setText("\n".join(magnets))
        self.statusBar().showMessage(f"Copied {len(magnets)} magnet link{'s' * (len(magnets) != 1)}.", 5000)
        log.info("Copied %d magnet link(s) to the clipboard.", len(magnets))

    def open_magnets(self, releases: list[ParsedRelease] | None = None) -> None:
        releases = releases or self.selected_releases()
        magnets = [QUrl(r.release.magnet) for r in releases if r.release.magnet]
        if not magnets:
            return
        if len(magnets) > MAGNET_CONFIRM_THRESHOLD:
            answer = QMessageBox.question(
                self, APP_NAME, f"Send {len(magnets)} magnet links to your torrent client?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        log.info("Sending %d magnet link(s) to the torrent client…", len(magnets))
        self._queue_urls(magnets)

    def _queue_urls(self, urls: list[QUrl]) -> None:
        self._open_queue.extend(urls)
        if not self._open_timer.isActive():
            self._open_next()
            self._open_timer.start()

    def _open_next(self) -> None:
        if not self._open_queue:
            self._open_timer.stop()
            return
        url = self._open_queue.pop(0)
        if not QDesktopServices.openUrl(url):
            self._open_queue.clear()
            self._open_timer.stop()
            kind = "magnet links" if url.scheme() == "magnet" else ".torrent files"
            message = (f"No application is registered to open {kind}. Install a torrent client "
                       "(e.g. qBittorrent) or use “Copy magnets”.")
            log.error(message)
            self._show_banner(message, "error")
        elif not self._open_queue:
            self._open_timer.stop()
            self.statusBar().showMessage("Sent to your torrent client.", 5000)

    # -------------------------------------------------------- context menus
    def _on_tree_double_click(self, proxy_index: QModelIndex) -> None:
        index = self.episodes_proxy.mapToSource(proxy_index)
        if index.parent().isValid():
            self.episodes_model.choose(index)
            self.tree.collapse(proxy_index.parent())
        else:
            slot = self.episodes_model.slot_at(index)
            if slot and not slot.missing:
                check = self.episodes_model.index(index.row(), EPISODE)
                checked = self.episodes_model.is_checked(index.row())
                state = Qt.CheckState.Unchecked if checked else Qt.CheckState.Checked
                self.episodes_model.setData(check, state.value, Qt.ItemDataRole.CheckStateRole)

    def _tree_menu(self, pos: QPoint) -> None:
        proxy_index = self.tree.indexAt(pos)
        if not proxy_index.isValid():
            return
        index = self.episodes_proxy.mapToSource(proxy_index)
        release = self.episodes_model.release_at(index)
        if release is None:
            return
        menu = QMenu(self)
        if index.parent().isValid():
            slot = self.episodes_model.slot_at(index)
            menu.addAction(f"Use this release for episode {slot.episode}",
                           lambda: self._on_tree_double_click(proxy_index))
            menu.addSeparator()
        self._release_actions(menu, release)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _batches_menu(self, pos: QPoint) -> None:
        proxy_index = self.batches_view.indexAt(pos)
        if not proxy_index.isValid():
            return
        release = self.batches_model.release_at(self.batches_proxy.mapToSource(proxy_index))
        menu = QMenu(self)
        self._release_actions(menu, release)
        menu.exec(self.batches_view.viewport().mapToGlobal(pos))

    def _release_actions(self, menu: QMenu, release: ParsedRelease) -> None:
        menu.addAction(theme.icon("download"), "Download this .torrent", lambda: self.download_selected([release]))
        menu.addAction(theme.icon("magnet"), "Open this magnet", lambda: self.open_magnets([release]))
        menu.addAction(theme.icon("copy"), "Copy magnet link", lambda: self.copy_magnets([release]))
        menu.addSeparator()
        menu.addAction(theme.icon("external"), "View on Nyaa",
                       lambda: QDesktopServices.openUrl(QUrl(release.release.view_url)))
        menu.addAction("Copy release name", lambda: QApplication.clipboard().setText(release.release.name))

    # ---------------------------------------------------------------- misc
    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if not dialog.exec():
            return
        old_url = self.nyaa.base_url
        dialog.apply()
        self.settings.save()
        if self.settings.base_url.rstrip("/") != old_url:
            self.nyaa = NyaaClient(self.settings.base_url, self.http)
        self._set_category(Category(self.settings.category))
        self.apply_theme()
        self._update_folder_button()

    def apply_theme(self) -> None:
        theme.apply(QApplication.instance(), self.settings.theme)
        self.refresh_icons()
        self.tree.viewport().update()
        self.batches_view.viewport().update()

    def toggle_theme(self) -> None:
        self.settings.theme = "light" if theme.current().name == "dark" else "dark"
        self.settings.save()
        self.apply_theme()

    def _on_system_theme_changed(self, *_) -> None:
        if self.settings.theme == "system":
            self.apply_theme()

    def analyze_title(self) -> None:
        text, ok = QInputDialog.getText(self, "Analyze a release title", "Release title:")
        if not ok or not text.strip():
            return
        dummy = Release(id=0, name=text.strip(), torrent_url="", magnet="", info_hash="", size_bytes=0,
                        published=datetime.now(UTC), seeders=0, leechers=0, downloads=0)
        parsed = parse_release(dummy)
        details = release_tooltip(parsed)
        details = "<br>".join(line for line in details.split("<br>")
                              if not line.startswith(("Size:", "Health:", "Published:")))
        box = QMessageBox(self)
        box.setWindowTitle("Release analysis")
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(details + f"<br>Parsed title: {parsed.title}<br>Batch: {'yes' if parsed.is_batch else 'no'}")
        box.exec()

    def show_about(self) -> None:
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h3>{APP_NAME} {__version__}</h3>"
            "<p>Batch-download anime releases from Nyaa.</p>"
            f"<p><a href='{REPO_URL}'>{REPO_URL}</a></p>"
            "<p>Title suggestions by <a href='https://anilist.co'>AniList</a>. "
            "Release parsing by PTT.</p>")

    def save_activity(self) -> None:
        name, _ = QFileDialog.getSaveFileName(self, "Save activity log", "nyaadownloader-log.txt",
                                              "Text files (*.txt)")
        if name:
            try:
                Path(name).write_text(self.activity.toPlainText(), encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(self, APP_NAME, f"Could not save the log: {exc}")

    def append_activity(self, line: str) -> None:
        self.activity.appendPlainText(line)

    # --------------------------------------------------------------- state
    def _restore_state(self) -> None:
        s = self.settings
        if s.window_geometry:
            self.restoreGeometry(QByteArray.fromBase64(s.window_geometry.encode()))
        if s.window_state:
            self.restoreState(QByteArray.fromBase64(s.window_state.encode()))
        if s.header_state:
            self.tree.header().restoreState(QByteArray.fromBase64(s.header_state.encode()))
            self.tree.header().setSectionResizeMode(NAME, QHeaderView.ResizeMode.Stretch)

    def closeEvent(self, event: QCloseEvent) -> None:
        for task in (self._search_task, self._download_task):
            if task:
                task.cancel()
        s = self.settings
        self._save_filters()
        s.window_geometry = self.saveGeometry().toBase64().data().decode()
        s.window_state = self.saveState().toBase64().data().decode()
        s.header_state = self.tree.header().saveState().toBase64().data().decode()
        s.save()
        super().closeEvent(event)

