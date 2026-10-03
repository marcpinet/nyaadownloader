from __future__ import annotations

import pytest
from conftest import make_release

from nyaadownloader.core.errors import UnknownUploaderError
from nyaadownloader.core.models import AnimeInfo
from nyaadownloader.core.search import SearchRequest, run_search


class FakeNyaa:
    def __init__(self, results: dict[str | None, list], totals: dict[str | None, int] | None = None,
                 unknown: set[str] = frozenset()) -> None:
        self.results = results
        self.totals = totals or {}
        self.unknown = unknown
        self.calls: list[tuple[str, str | None]] = []

    def search(self, query, *, uploader=None, category=None, trusted_only=False, cancel=None, on_progress=None):
        self.calls.append((query, uploader))
        if uploader in self.unknown:
            raise UnknownUploaderError(uploader)
        if on_progress:
            on_progress(1, 1)
        found = self.results.get(uploader, [])
        return found, self.totals.get(uploader, len(found))


def test_search_titles_drop_season_suffix_and_use_anilist_names() -> None:
    anime = AnimeInfo(id=1, romaji="Boku no Hero Academia FINAL SEASON", english="My Hero Academia FINAL SEASON",
                      synonyms=("MHA 8", "僕のヒーローアカデミア"))
    request = SearchRequest("my hero academia final season", anime=anime)
    assert request.search_titles() == ["boku no hero academia", "my hero academia"]
    assert "僕のヒーローアカデミア" not in request.aliases()
    assert "MHA 8" in request.aliases()


def test_run_search_ranks_by_uploader_order() -> None:
    nyaa = FakeNyaa({
        "SubsPlease": [make_release("[SubsPlease] Dandadan - 01 (1080p).mkv", seeders=5)],
        "Erai-raws": [make_release("[Erai-raws] Dandadan - 01 [1080p]", seeders=500)],
    })
    outcome = run_search(nyaa, SearchRequest("Dandadan", uploaders=("SubsPlease", "Erai-raws")))
    assert [u for _, u in nyaa.calls] == ["SubsPlease", "Erai-raws"]
    assert nyaa.calls[0][0] == "dandadan 1080p"
    assert outcome.result.episodes[0].release.group == "SubsPlease"
    assert outcome.fetched == 2


def test_run_search_refines_when_nyaa_caps_results() -> None:
    nyaa = FakeNyaa({None: [make_release("[SubsPlease] One Piece - 1100 (1080p).mkv")]}, totals={None: 5000})
    outcome = run_search(nyaa, SearchRequest("One Piece", first_episode=1, last_episode=20))
    refined = [q for q, _ in nyaa.calls[1:]]
    assert len(refined) == 2
    assert refined[0].startswith("one piece 1080p (1|01|2|02|")
    assert not outcome.truncated


def test_run_search_flags_truncation_without_range() -> None:
    nyaa = FakeNyaa({None: []}, totals={None: 5000})
    assert run_search(nyaa, SearchRequest("One Piece")).truncated


def test_unknown_uploader_is_a_warning_unless_all_fail() -> None:
    nyaa = FakeNyaa({"SubsPlease": []}, unknown={"nobody"})
    outcome = run_search(nyaa, SearchRequest("Dandadan", uploaders=("nobody", "SubsPlease")))
    assert outcome.warnings and "nobody" in outcome.warnings[0]
    with pytest.raises(UnknownUploaderError):
        run_search(FakeNyaa({}, unknown={"nobody"}), SearchRequest("Dandadan", uploaders=("nobody",)))
