"""Filter inputs: uploader chips with a searchable list, and the episode range selector."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from nyaadownloader.ui import theme

# Nyaa accounts checked to exist, most popular first.
KNOWN_UPLOADERS = (
    "SubsPlease", "Erai-raws", "Judas", "Ember_Encodes", "Yameii", "varyg1001", "DKB0512",
    "Tsundere-Raws", "Raze876", "LostYears", "NanDesuKa", "DameDesuYo", "Cerberus", "Commie",
    "neoborn", "Kametsu", "Vodes", "smol", "motbob", "LoliHouse", "Chihiro", "Aergia", "Golumpa",
    "sff", "HorribleSubs",
)
CUSTOM_ROLE = Qt.ItemDataRole.UserRole + 20


class _Chip(QFrame):
    removed = Signal(str)
    menuRequested = Signal(str, QPoint)

    def __init__(self, name: str, rank: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("chip")
        self.name = name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 2, 3, 2)
        layout.setSpacing(5)
        rank_label = QLabel(str(rank), objectName="chipRank")
        rank_label.setToolTip("Priority: when several uploaders have an episode, the lowest number wins")
        layout.addWidget(rank_label)
        layout.addWidget(QLabel(name))
        close = QToolButton(objectName="chipClose")
        close.setIcon(theme.icon("close", theme.current().muted, 12))
        close.setToolTip(f"Remove {name}")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(lambda: self.removed.emit(self.name))
        layout.addWidget(close)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.menuRequested.emit(self.name, self.mapToGlobal(pos)))


class _UploaderPopup(QFrame):
    """Searchable, checkable list of uploaders; typing an unknown name offers to add it."""

    toggled = Signal(str, bool)
    cleared = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("popup")
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.search = QLineEdit(placeholderText="Search or type a Nyaa user name")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        self.search.installEventFilter(self)
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setMinimumHeight(260)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list)
        footer = QHBoxLayout()
        hint = QLabel("Checked uploaders are searched in order.", objectName="muted", wordWrap=True)
        footer.addWidget(hint, 1)
        clear = QPushButton("Anyone")
        clear.setToolTip("Search every uploader on Nyaa")
        clear.clicked.connect(self._clear)
        footer.addWidget(clear)
        layout.addLayout(footer)
        self._selected: list[str] = []

    def open(self, anchor: QWidget, selected: list[str]) -> None:
        self._selected = list(selected)
        self.search.clear()
        self._rebuild()
        pos = anchor.mapToGlobal(QPoint(0, anchor.height() + 4))
        self.move(pos)
        self.show()
        self.search.setFocus()

    def _names(self) -> list[str]:
        known = {k.casefold() for k in KNOWN_UPLOADERS}
        custom = [s for s in self._selected if s.casefold() not in known]
        return [*custom, *KNOWN_UPLOADERS]

    def _rebuild(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        chosen = {s.casefold() for s in self._selected}
        for name in self._names():
            item = QListWidgetItem(name)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
            item.setCheckState(Qt.CheckState.Checked if name.casefold() in chosen else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self._add_item = QListWidgetItem()
        self._add_item.setData(CUSTOM_ROLE, True)
        self._add_item.setForeground(self.palette().link())
        self.list.insertItem(0, self._add_item)
        self.list.blockSignals(False)
        self._filter(self.search.text())

    def _filter(self, text: str) -> None:
        needle = text.strip().casefold()
        exact = False
        for row in range(1, self.list.count()):
            item = self.list.item(row)
            name = item.text().casefold()
            item.setHidden(bool(needle) and needle not in name)
            exact = exact or name == needle
        show_add = bool(needle) and not exact
        self._add_item.setHidden(not show_add)
        if show_add:
            self._add_item.setText(f"Add “{text.strip()}”")
        visible = [self.list.item(r) for r in range(self.list.count()) if not self.list.item(r).isHidden()]
        known = [item for item in visible if not item.data(CUSTOM_ROLE)]
        if visible:
            self.list.setCurrentItem(known[0] if needle and known else visible[0])

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        if item.data(CUSTOM_ROLE):
            self._add_custom()

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if item.data(CUSTOM_ROLE):
            return
        checked = item.checkState() == Qt.CheckState.Checked
        name = item.text()
        if checked and name.casefold() not in (s.casefold() for s in self._selected):
            self._selected.append(name)
        elif not checked:
            self._selected = [s for s in self._selected if s.casefold() != name.casefold()]
        self.toggled.emit(name, checked)

    def _add_custom(self) -> None:
        name = self.search.text().strip()
        if not name:
            return
        if name.casefold() not in (s.casefold() for s in self._selected):
            self._selected.append(name)
            self.toggled.emit(name, True)
        self.search.clear()
        self._rebuild()

    def _clear(self) -> None:
        self.cleared.emit()
        self.hide()

    def eventFilter(self, obj, event) -> bool:
        if obj is self.search and isinstance(event, QKeyEvent) and event.type() == QKeyEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                QApplication.sendEvent(self.list, event)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = self.list.currentItem()
                if item is None or item.isHidden() or item.data(CUSTOM_ROLE):
                    self._add_custom()
                else:
                    item.setCheckState(Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked
                                       else Qt.CheckState.Checked)
                return True
        return super().eventFilter(obj, event)


class UploaderPicker(QWidget):
    """Selected uploaders as removable, ordered chips, plus a button to add more."""

    changed = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._uploaders: list[str] = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._anyone = QLabel("Anyone", objectName="muted")
        self._anyone.setToolTip("No uploader selected: every uploader on Nyaa is searched")
        self.add_button = QPushButton("Add")
        self.add_button.setToolTip("Choose which uploaders to search")
        self.add_button.clicked.connect(self._open_popup)
        self._popup = _UploaderPopup(self)
        self._popup.toggled.connect(self._on_toggled)
        self._popup.cleared.connect(lambda: self.set_uploaders([]))
        self._chips: list[_Chip] = []
        self._rebuild()

    def uploaders(self) -> list[str]:
        return list(self._uploaders)

    def set_uploaders(self, names: list[str]) -> None:
        unique: list[str] = []
        for name in names:
            if name.strip() and name.casefold() not in (u.casefold() for u in unique):
                unique.append(name.strip())
        if unique == self._uploaders:
            return
        self._uploaders = unique
        self._rebuild()
        self.changed.emit(self.uploaders())

    def refresh_icons(self) -> None:
        self.add_button.setIcon(theme.icon("users", theme.current().text, 16))
        self._rebuild()

    def _rebuild(self) -> None:
        for chip in self._chips:
            self._layout.removeWidget(chip)
            chip.deleteLater()
        self._chips = []
        while self._layout.count():
            self._layout.takeAt(0)
        if not self._uploaders:
            self._layout.addWidget(self._anyone)
            self._anyone.show()
        else:
            self._anyone.hide()
        for rank, name in enumerate(self._uploaders, start=1):
            chip = _Chip(name, rank, self)
            chip.removed.connect(self._remove)
            chip.menuRequested.connect(self._chip_menu)
            self._chips.append(chip)
            self._layout.addWidget(chip)
        self._layout.addWidget(self.add_button)
        self._layout.addStretch(1)

    def _open_popup(self) -> None:
        self._popup.open(self.add_button, self._uploaders)

    def _on_toggled(self, name: str, checked: bool) -> None:
        if checked:
            self.set_uploaders([*self._uploaders, name])
        else:
            self._remove(name)

    def _remove(self, name: str) -> None:
        self.set_uploaders([u for u in self._uploaders if u.casefold() != name.casefold()])

    def _chip_menu(self, name: str, pos: QPoint) -> None:
        index = self._uploaders.index(name)
        menu = QMenu(self)
        first = menu.addAction("Make first choice", lambda: self._move(index, 0))
        first.setEnabled(index > 0)
        left = menu.addAction("Move left", lambda: self._move(index, index - 1))
        left.setEnabled(index > 0)
        right = menu.addAction("Move right", lambda: self._move(index, index + 1))
        right.setEnabled(index < len(self._uploaders) - 1)
        menu.addSeparator()
        menu.addAction("Remove", lambda: self._remove(name))
        menu.exec(pos)

    def _move(self, old: int, new: int) -> None:
        names = list(self._uploaders)
        names.insert(new, names.pop(old))
        self.set_uploaders(names)


class EpisodeRange(QWidget):
    """'All episodes', 'From episode N' or 'Episodes N to M', with spin boxes shown only when needed."""

    ALL, FROM, BETWEEN = range(3)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.mode = QComboBox()
        self.mode.addItem("All episodes", self.ALL)
        self.mode.addItem("From episode", self.FROM)
        self.mode.addItem("Episodes", self.BETWEEN)
        self.mode.setToolTip("Which episodes to look for")
        self.first = QSpinBox(minimum=1, maximum=9999)
        self.first.setFixedWidth(64)
        self.first.setToolTip("First episode")
        self.to_label = QLabel("to", objectName="muted")
        self.last = QSpinBox(minimum=1, maximum=9999)
        self.last.setFixedWidth(64)
        self.last.setToolTip("Last episode")
        for widget in (self.mode, self.first, self.to_label, self.last):
            layout.addWidget(widget)
        self._known_count: int | None = None
        self.mode.currentIndexChanged.connect(self._on_mode)
        self.first.valueChanged.connect(self._on_first)
        self.last.valueChanged.connect(lambda v: self.first.setValue(min(self.first.value(), v)))
        self.reset()
        self._on_mode()

    def episode_range(self) -> tuple[int, int | None]:
        mode = self.mode.currentData()
        if mode == self.ALL:
            return 1, None
        if mode == self.FROM:
            return self.first.value(), None
        return self.first.value(), self.last.value()

    def reset(self, known_count: int | None = None) -> None:
        """Back to 'All episodes' (e.g. for a new anime), remembering how many episodes it has."""
        self._known_count = known_count
        self.mode.setCurrentIndex(self.ALL)
        self.first.setValue(1)
        self.last.setValue(max(1, known_count or 12))

    def _on_mode(self) -> None:
        mode = self.mode.currentData()
        self.first.setVisible(mode != self.ALL)
        self.to_label.setVisible(mode == self.BETWEEN)
        self.last.setVisible(mode == self.BETWEEN)
        if mode == self.BETWEEN and self.last.value() < self.first.value():
            self.last.setValue(max(self.first.value(), self._known_count or self.first.value()))

    def _on_first(self, value: int) -> None:
        if self.last.value() < value:
            self.last.setValue(value)
