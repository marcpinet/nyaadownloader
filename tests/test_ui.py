from __future__ import annotations

import pytest
from conftest import make_release
from PySide6.QtCore import Qt

from nyaadownloader.core.matching import MatchCriteria, match_releases
from nyaadownloader.core.parsing import parse_release
from nyaadownloader.core.search import SearchOutcome, SearchRequest
from nyaadownloader.core.settings import Settings
from nyaadownloader.ui import theme
from nyaadownloader.ui.main_window import MainWindow
from nyaadownloader.ui.results import EPISODE


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr(Settings, "save", lambda self, path=None: None)
    theme.apply(qtbot_app(), "dark")
    win = MainWindow(Settings(download_dir=str(tmp_path)), "")
    qtbot.addWidget(win)
    return win


def qtbot_app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance()


def outcome() -> SearchOutcome:
    names = [
        "[SubsPlease] Dandadan - 01 (1080p).mkv",
        "[Erai-raws] Dandadan - 01 [1080p]",
        "[SubsPlease] Dandadan - 03 (1080p).mkv",
        "[SubsPlease] Dandadan S2 - 01 (1080p).mkv",
        "[SubsPlease] Dandadan (01-12) (1080p) [Batch]",
    ]
    releases = [parse_release(make_release(n, size=1024 ** 3)) for n in names]
    request = SearchRequest("Dandadan")
    result = match_releases(releases, MatchCriteria(aliases=("Dandadan",)))
    return SearchOutcome(request=request, result=result, fetched=len(names), truncated=False, elapsed=0.4)


def show(window: MainWindow, out: SearchOutcome) -> None:
    token = window._search_task = object()  # the handler ignores results of stale searches
    window._on_search_done(token, out, False)
    window._search_task = None


def test_results_are_listed_and_selected(window: MainWindow) -> None:
    show(window, outcome())
    assert window.stack.currentIndex() == 1
    assert window.episodes_proxy.rowCount() == 4  # 01, 02 (missing), 03, S2·01
    assert window.season_combo.count() == 3
    assert window.tabs.tabText(1) == "Batches && specials (1)"
    assert [r.release.name for r in window.selected_releases()] == [
        "[SubsPlease] Dandadan - 01 (1080p).mkv",
        "[SubsPlease] Dandadan - 03 (1080p).mkv",
        "[SubsPlease] Dandadan S2 - 01 (1080p).mkv",
    ]
    assert window.selection_label.text().startswith("3 episodes selected · 3.0 GiB")
    assert window.download_button.isEnabled()


def test_season_filter_limits_selection(window: MainWindow) -> None:
    show(window, outcome())
    window.season_combo.setCurrentIndex(window.season_combo.findData("Season 2"))
    assert window.episodes_proxy.rowCount() == 1
    assert len(window.selected_releases()) == 1
    assert window.tabs.tabText(0) == "Episodes (1)"


def test_choosing_an_alternative(window: MainWindow) -> None:
    show(window, outcome())
    model = window.episodes_model
    first = model.index(0, EPISODE)
    assert model.rowCount(first) == 1
    model.choose(model.index(0, EPISODE, first))
    assert model.release_at(first).group == "Erai-raws"
    assert model.release_at(model.index(0, EPISODE, first)).group == "SubsPlease"


def test_unchecking_and_select_none(window: MainWindow) -> None:
    show(window, outcome())
    model = window.episodes_model
    model.setData(model.index(0, EPISODE), Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole)
    assert len(window.selected_releases()) == 2
    window._check_visible(False)
    assert window.selected_releases() == []
    assert not window.download_button.isEnabled()
    assert window.selection_label.text() == "Nothing selected"


def test_copy_magnets(window: MainWindow, qtbot) -> None:
    show(window, outcome())
    window.copy_magnets()
    clipboard = qtbot_app().clipboard().text().splitlines()
    assert len(clipboard) == 3 and all(m.startswith("magnet:?") for m in clipboard)


def test_no_results_page(window: MainWindow) -> None:
    empty = SearchOutcome(request=SearchRequest("zzz"), result=match_releases([], MatchCriteria(aliases=("zzz",))),
                          fetched=0, truncated=False, elapsed=0.1)
    show(window, empty)
    assert window.stack.currentIndex() == 0
    assert window.empty.title.text() == "Nothing matched"


def test_theme_switch_does_not_crash(window: MainWindow) -> None:
    show(window, outcome())
    for mode in ("light", "dark"):
        window.settings.theme = mode
        window.apply_theme()
        assert theme.current().name == mode


def test_uploader_picker_order_and_dedup(qtbot) -> None:
    from nyaadownloader.ui.pickers import UploaderPicker

    picker = UploaderPicker()
    qtbot.addWidget(picker)
    changes = []
    picker.changed.connect(changes.append)
    picker.set_uploaders(["SubsPlease", "Erai-raws", "subsplease", " "])
    assert picker.uploaders() == ["SubsPlease", "Erai-raws"]
    picker._move(1, 0)
    assert picker.uploaders() == ["Erai-raws", "SubsPlease"]
    picker._remove("SUBSPLEASE")
    assert picker.uploaders() == ["Erai-raws"]
    assert len(changes) == 3


def test_episode_range_modes(qtbot) -> None:
    from nyaadownloader.ui.pickers import EpisodeRange

    widget = EpisodeRange()
    qtbot.addWidget(widget)
    assert widget.episode_range() == (1, None)
    widget.mode.setCurrentIndex(EpisodeRange.FROM)
    widget.first.setValue(5)
    assert widget.episode_range() == (5, None)
    widget.mode.setCurrentIndex(EpisodeRange.BETWEEN)
    widget.last.setValue(3)  # can't end before it starts
    assert widget.episode_range() == (3, 3)
    widget.reset(known_count=24)
    assert widget.episode_range() == (1, None)
    widget.mode.setCurrentIndex(EpisodeRange.BETWEEN)
    assert widget.episode_range() == (1, 24)


def test_theme_toggle_button(window: MainWindow) -> None:
    window.settings.theme = "dark"
    window.apply_theme()
    window.theme_button.click()
    assert window.settings.theme == "light" and theme.current().name == "light"
    assert "dark" in window.theme_button.toolTip()
    window.theme_button.click()
    assert window.settings.theme == "dark"
