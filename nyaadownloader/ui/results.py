"""Item models for the Episodes tree and the Batches table."""

from __future__ import annotations

from datetime import UTC, datetime

from PySide6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont

from nyaadownloader.core.matching import EpisodeSlot
from nyaadownloader.core.models import ParsedRelease
from nyaadownloader.core.nyaa import format_size
from nyaadownloader.ui import theme

SORT_ROLE = Qt.ItemDataRole.UserRole + 1
RELEASE_ROLE = Qt.ItemDataRole.UserRole + 2

COLUMNS = ("Episode", "Release", "Group", "Quality", "Size", "Seeders", "Leechers", "Date")
EPISODE, NAME, GROUP, QUALITY, SIZE, SEEDERS, LEECHERS, DATE = range(len(COLUMNS))

AnyIndex = QModelIndex | QPersistentModelIndex


def season_display(label: str) -> str:
    return label or "Main numbering"


def season_short(label: str) -> str:
    """Compact form for the Episode column: "Season 2" → "S2", "Final Season Part 2" → "Final P2"."""
    return (label.replace("Final Season", "Final").replace("Season ", "S").replace("Part ", "P"))


def quality_text(r: ParsedRelease) -> str:
    return " ".join(p for p in (r.resolution, r.codec, r.bit_depth) if p)


def relative_date(when: datetime) -> str:
    delta = datetime.now(UTC) - when
    days = delta.days
    if days < 1:
        hours = delta.seconds // 3600
        return f"{hours} h ago" if hours else "just now"
    if days < 30:
        return f"{days} d ago"
    return when.astimezone().strftime("%Y-%m-%d")


def display_name(r: ParsedRelease) -> str:
    """Release name without the leading "[Group]", which has its own column."""
    name = r.release.name
    if r.group:
        for opening, closing in ("[]", "()", "【】"):
            prefix = f"{opening}{r.group}{closing}"
            if name.startswith(prefix):
                return name[len(prefix):].strip() or name
    return name


def release_tooltip(r: ParsedRelease) -> str:
    rel = r.release
    lines = [f"<b>{_escape(rel.name)}</b>", ""]
    facts = [
        ("Group", r.group),
        ("Episodes", r.episode_span),
        ("Season", r.season_label),
        ("Quality", quality_text(r)),
        ("Source", r.source),
        ("Audio", ", ".join(r.audio)),
        ("Languages", ", ".join(r.languages[:8]) + ("…" if len(r.languages) > 8 else "")),
        ("Version", f"v{r.version}" if r.version > 1 else ""),
        ("Size", format_size(rel.size_bytes)),
        ("Health", f"{rel.seeders} seeders · {rel.leechers} leechers · {rel.downloads} downloads"),
        ("Published", rel.published.astimezone().strftime("%Y-%m-%d %H:%M")),
        ("Status", "Trusted uploader" if rel.trusted else ("Remake" if rel.remake else "")),
    ]
    lines += [f"{k}: {_escape(v)}" for k, v in facts if v]
    return "<br>".join(lines)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _seeders_color(seeders: int) -> QColor:
    p = theme.current()
    if seeders == 0:
        return QColor(p.danger)
    if seeders < 5:
        return QColor(p.warning)
    return QColor(p.success)


def release_cell(r: ParsedRelease, column: int, role: int):
    rel = r.release
    if role == Qt.ItemDataRole.DisplayRole:
        return {
            NAME: display_name(r),
            GROUP: r.group,
            QUALITY: quality_text(r),
            SIZE: format_size(rel.size_bytes),
            SEEDERS: str(rel.seeders),
            LEECHERS: str(rel.leechers),
            DATE: relative_date(rel.published),
        }.get(column)
    if role == SORT_ROLE:
        return {
            NAME: rel.name.casefold(),
            GROUP: r.group.casefold(),
            QUALITY: r.resolution_value,
            SIZE: rel.size_bytes,
            SEEDERS: rel.seeders,
            LEECHERS: rel.leechers,
            DATE: rel.published.timestamp(),
        }.get(column)
    if role == Qt.ItemDataRole.ForegroundRole and column == SEEDERS:
        return _seeders_color(rel.seeders)
    if role == Qt.ItemDataRole.ToolTipRole and column in (NAME, GROUP, QUALITY):
        return release_tooltip(r)
    if role == Qt.ItemDataRole.DecorationRole and column == NAME:
        p = theme.current()
        if rel.remake:
            return theme.dot_icon(p.danger)
        if rel.trusted:
            return theme.dot_icon(p.success)
        return theme.dot_icon(p.border)
    if role == Qt.ItemDataRole.TextAlignmentRole and column in (SIZE, SEEDERS, LEECHERS):
        return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if role == RELEASE_ROLE:
        return r
    return None


class EpisodesModel(QAbstractItemModel):
    """Top level: one row per episode showing its chosen release. Children: alternatives."""

    checkedChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._slots: list[EpisodeSlot] = []
        self._checked: set[int] = set()

    # -- data management ---------------------------------------------------
    def set_slots(self, slots: list[EpisodeSlot]) -> None:
        self.beginResetModel()
        self._slots = slots
        self._checked = {i for i, s in enumerate(slots) if not s.missing}
        self.endResetModel()
        self.checkedChanged.emit()

    def slots(self) -> list[EpisodeSlot]:
        return self._slots

    def slot_at(self, index: AnyIndex) -> EpisodeSlot | None:
        if not index.isValid():
            return None
        row = index.row() if index.internalId() == 0 else index.internalId() - 1
        return self._slots[row]

    def release_at(self, index: AnyIndex) -> ParsedRelease | None:
        if not index.isValid():
            return None
        slot = self.slot_at(index)
        if index.internalId() == 0:
            return slot.release
        return self._alternatives(slot)[index.row()]

    def checked_releases(self) -> list[ParsedRelease]:
        return [self._slots[i].release for i in sorted(self._checked) if self._slots[i].release]

    def set_all_checked(self, rows: list[int] | None, checked: bool) -> None:
        rows = range(len(self._slots)) if rows is None else rows
        for row in rows:
            if self._slots[row].missing:
                continue
            if checked:
                self._checked.add(row)
            else:
                self._checked.discard(row)
        if self._slots:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._slots) - 1, 0),
                                  [Qt.ItemDataRole.CheckStateRole])
        self.checkedChanged.emit()

    def is_checked(self, row: int) -> bool:
        return row in self._checked

    def choose(self, index: AnyIndex) -> None:
        """Make the alternative at ``index`` the release used for its episode."""
        if not index.isValid() or index.internalId() == 0:
            return
        row = index.internalId() - 1
        slot = self._slots[row]
        alternative = self._alternatives(slot)[index.row()]
        slot.chosen = slot.releases.index(alternative)
        self._checked.add(row)
        parent = self.index(row, 0)
        last_col = len(COLUMNS) - 1
        self.dataChanged.emit(parent, self.index(row, last_col))
        if count := self.rowCount(parent):
            self.dataChanged.emit(self.index(0, 0, parent), self.index(count - 1, last_col, parent))
        self.checkedChanged.emit()

    @staticmethod
    def _alternatives(slot: EpisodeSlot) -> list[ParsedRelease]:
        return [r for i, r in enumerate(slot.releases) if i != slot.chosen]

    # -- Qt model API --------------------------------------------------------
    def index(self, row: int, column: int, parent: AnyIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            return self.createIndex(row, column, 0)
        return self.createIndex(row, column, parent.row() + 1)

    def parent(self, index: AnyIndex = QModelIndex()) -> QModelIndex:  # type: ignore[override]
        if not index.isValid() or index.internalId() == 0:
            return QModelIndex()
        return self.createIndex(index.internalId() - 1, 0, 0)

    def rowCount(self, parent: AnyIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return len(self._slots)
        if parent.internalId() != 0 or parent.column() != 0:
            return 0
        return max(0, len(self._slots[parent.row()].releases) - 1)

    def columnCount(self, parent: AnyIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return COLUMNS[section]
        return None

    def flags(self, index: AnyIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.internalId() == 0 and index.column() == EPISODE and not self._slots[index.row()].missing:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: AnyIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        column = index.column()
        is_top = index.internalId() == 0
        slot = self.slot_at(index)
        release = self.release_at(index)

        if column == EPISODE:
            if is_top:
                if role == Qt.ItemDataRole.DisplayRole:
                    prefix = f"{season_short(slot.season_label)} · " if slot.season_label else ""
                    return f"{prefix}{slot.episode:02d}"
                if role == Qt.ItemDataRole.ToolTipRole:
                    return f"{season_display(slot.season_label)}, episode {slot.episode}"
                if role == Qt.ItemDataRole.CheckStateRole and not slot.missing:
                    return Qt.CheckState.Checked if index.row() in self._checked else Qt.CheckState.Unchecked
                if role == SORT_ROLE:
                    return (slot.season_label, slot.episode)
                if role == Qt.ItemDataRole.FontRole:
                    font = QFont()
                    font.setWeight(QFont.Weight.DemiBold)
                    return font
            elif role == Qt.ItemDataRole.DisplayRole:
                return "alt."
            if role == Qt.ItemDataRole.ForegroundRole and not is_top:
                return QColor(theme.current().muted)
            return None

        if slot.missing:
            if column == NAME and role == Qt.ItemDataRole.DisplayRole:
                return "Not found on Nyaa"
            if role == Qt.ItemDataRole.ForegroundRole:
                return QColor(theme.current().muted)
            if column == NAME and role == Qt.ItemDataRole.FontRole:
                font = QFont()
                font.setItalic(True)
                return font
            return None

        if role == Qt.ItemDataRole.ForegroundRole and not is_top and column != SEEDERS:
            return QColor(theme.current().muted)
        return release_cell(release, column, role)

    def setData(self, index: AnyIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.CheckStateRole or not index.isValid() or index.internalId() != 0:
            return False
        row = index.row()
        if Qt.CheckState(value) == Qt.CheckState.Checked:
            self._checked.add(row)
        else:
            self._checked.discard(row)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
        self.checkedChanged.emit()
        return True


class EpisodesProxy(QSortFilterProxyModel):
    """Filters episodes by season label, optionally hiding missing ones."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._season: str | None = None
        self._hide_missing = False
        self.setSortRole(SORT_ROLE)

    def set_season(self, season: str | None) -> None:
        self._refilter(lambda: setattr(self, "_season", season))

    def set_hide_missing(self, hide: bool) -> None:
        self._refilter(lambda: setattr(self, "_hide_missing", hide))

    def _refilter(self, change) -> None:
        if hasattr(self, "beginFilterChange"):  # Qt >= 6.10
            self.beginFilterChange()
            change()
            self.endFilterChange(QSortFilterProxyModel.Direction.Rows)
        else:
            change()
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: AnyIndex) -> bool:
        if source_parent.isValid():
            return True
        slot = self.sourceModel().slots()[source_row]
        if self._season is not None and slot.season_label != self._season:
            return False
        return not (self._hide_missing and slot.missing)

    def lessThan(self, left: AnyIndex, right: AnyIndex) -> bool:
        a, b = left.data(SORT_ROLE), right.data(SORT_ROLE)
        if a is None or b is None:
            return (a is None) < (b is None)
        return a < b

    def visible_source_rows(self) -> list[int]:
        return [self.mapToSource(self.index(r, 0)).row() for r in range(self.rowCount())]


class BatchesModel(QAbstractTableModel):
    checkedChanged = Signal()
    COLUMNS = ("Episodes", *COLUMNS[1:])

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._releases: list[ParsedRelease] = []
        self._checked: set[int] = set()

    def set_releases(self, releases: list[ParsedRelease]) -> None:
        self.beginResetModel()
        self._releases = releases
        self._checked = set()
        self.endResetModel()
        self.checkedChanged.emit()

    def release_at(self, index: AnyIndex) -> ParsedRelease | None:
        return self._releases[index.row()] if index.isValid() else None

    def checked_releases(self) -> list[ParsedRelease]:
        return [self._releases[i] for i in sorted(self._checked)]

    def set_all_checked(self, checked: bool) -> None:
        self._checked = set(range(len(self._releases))) if checked else set()
        if self._releases:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._releases) - 1, 0))
        self.checkedChanged.emit()

    def rowCount(self, parent: AnyIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._releases)

    def columnCount(self, parent: AnyIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def flags(self, index: AnyIndex) -> Qt.ItemFlag:
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == EPISODE:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def data(self, index: AnyIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r = self._releases[index.row()]
        if index.column() == EPISODE:
            if role == Qt.ItemDataRole.DisplayRole:
                span = r.episode_span or "Special"
                return f"{season_short(r.season_label)} · {span}" if r.season_label else span
            if role == Qt.ItemDataRole.CheckStateRole:
                return Qt.CheckState.Checked if index.row() in self._checked else Qt.CheckState.Unchecked
            if role == SORT_ROLE:
                return (r.season_label, r.episodes[0] if r.episodes else -1)
            return None
        return release_cell(r, index.column(), role)

    def setData(self, index: AnyIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.CheckStateRole or not index.isValid():
            return False
        if Qt.CheckState(value) == Qt.CheckState.Checked:
            self._checked.add(index.row())
        else:
            self._checked.discard(index.row())
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
        self.checkedChanged.emit()
        return True


class SortProxy(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSortRole(SORT_ROLE)

    def lessThan(self, left: AnyIndex, right: AnyIndex) -> bool:
        a, b = left.data(SORT_ROLE), right.data(SORT_ROLE)
        if a is None or b is None:
            return (a is None) < (b is None)
        return a < b
