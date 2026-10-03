from __future__ import annotations

from conftest import make_release

from nyaadownloader.core.matching import MatchCriteria, TitleMatcher, match_releases
from nyaadownloader.core.models import ParsedRelease
from nyaadownloader.core.parsing import parse_release


def parsed(name: str, rank: int = 0, **kwargs) -> ParsedRelease:
    item = parse_release(make_release(name, **kwargs))
    item.source_rank = rank
    return item


MHA = ("Boku no Hero Academia FINAL SEASON", "My Hero Academia FINAL SEASON")


def test_title_matcher_strict() -> None:
    matcher = TitleMatcher(MHA)
    assert matcher.requested_seasons == {"Final Season"}
    assert matcher.match(parsed("[Erai-raws] Boku no Hero Academia Final Season - 03 [1080p]")) == "Final Season"
    assert matcher.match(parsed("[SubsPlease] Boku no Hero Academia - 160 (1080p) [ABC].mkv")) == ""
    assert matcher.match(parsed("[Erai-raws] Boku no Hero Academia 5th Season - 01 [1080p]")) == "Season 5"
    assert matcher.match(parsed("[SubsPlease] My Hero Academia - 02 (1080p).mkv")) == ""
    # Spin-offs and specials are different shows.
    assert matcher.match(parsed("[SubsPlease] Vigilante - Boku no Hero Academia Illegals S2 - 13 (1080p)")) is None
    assert matcher.match(parsed("[SubsPlease] Boku no Hero Academia - I am a Hero too (1080p).mkv")) is None


def test_title_matcher_loose() -> None:
    release = parsed("[SubsPlease] Vigilante - Boku no Hero Academia Illegals - 13 (1080p)")
    assert TitleMatcher(("Boku no Hero Academia",)).match(release) is None
    assert TitleMatcher(("Boku no Hero Academia",), loose=True).match(release) == ""


def test_match_groups_ranks_and_reports_missing() -> None:
    releases = [
        parsed("[SubsPlease] Sousou no Frieren - 01 (1080p) [A].mkv", rank=0, seeders=50),
        parsed("[Erai-raws] Sousou no Frieren - 01 [1080p][Multiple Subtitle]", rank=1, seeders=900),
        parsed("[SubsPlease] Sousou no Frieren - 02 (1080p) [B].mkv", rank=0, seeders=0),
        parsed("[Erai-raws] Sousou no Frieren - 02 [1080p][Multiple Subtitle]", rank=1, seeders=3),
        parsed("[SubsPlease] Sousou no Frieren - 04 (1080p) [D].mkv", rank=0),
        parsed("[SubsPlease] Sousou no Frieren - 04 (720p) [D].mkv", rank=0),
        parsed("[SubsPlease] Sousou no Frieren S2 - 01 (1080p) [E].mkv", rank=0),
        parsed("[SubsPlease] Sousou no Frieren (01-28) (1080p) [Batch]", rank=0),
        parsed("[SubsPlease] Other Show - 01 (1080p).mkv", rank=0),
        parsed("[SubsPlease] Sousou no Frieren - 05 (1080p) [F].mkv", rank=0, remake=True),
    ]
    result = match_releases(releases, MatchCriteria(aliases=("Sousou no Frieren",), resolution=1080))

    slots = {(s.season_label, s.episode): s for s in result.episodes}
    assert set(slots) == {("", 1), ("", 2), ("", 3), ("", 4), ("Season 2", 1)}
    # Preferred uploader wins over raw seeders…
    assert slots[("", 1)].release.group == "SubsPlease"
    assert len(slots[("", 1)].releases) == 2
    # …unless its torrent is dead.
    assert slots[("", 2)].release.group == "Erai-raws"
    assert slots[("", 3)].missing
    assert [r.resolution for r in slots[("", 4)].releases] == ["1080p"]
    assert [b.release.name for b in result.batches] == ["[SubsPlease] Sousou no Frieren (01-28) (1080p) [Batch]"]
    assert result.season_labels == ["", "Season 2"]
    assert result.preferred_season is None
    assert result.rejected_title == 1
    assert result.rejected_quality == 1
    assert result.rejected_other == 1  # the remake


def test_match_episode_range() -> None:
    releases = [parsed(f"[SubsPlease] One Piece - {n} (1080p) [X].mkv") for n in (1099, 1100, 1102, 1105)]
    criteria = MatchCriteria(aliases=("One Piece",), resolution=None, first_episode=1100, last_episode=1103)
    result = match_releases(releases, criteria)
    assert [(s.episode, s.missing) for s in result.episodes] == [
        (1100, False), (1101, True), (1102, False), (1103, True)]


def test_any_resolution_prefers_higher() -> None:
    releases = [parsed("[SubsPlease] Dandadan - 01 (720p).mkv"), parsed("[SubsPlease] Dandadan - 01 (1080p).mkv")]
    result = match_releases(releases, MatchCriteria(aliases=("Dandadan",), resolution=None))
    assert result.episodes[0].release.resolution == "1080p"


def test_preferred_season_follows_query() -> None:
    releases = [
        parsed("[Erai-raws] Boku no Hero Academia Final Season - 01 [1080p]"),
        parsed("[Erai-raws] Boku no Hero Academia 7th Season - 01 [1080p]"),
    ]
    result = match_releases(releases, MatchCriteria(aliases=MHA))
    assert result.preferred_season == "Final Season"


def test_duplicate_ids_are_ignored() -> None:
    release = parsed("[SubsPlease] Dandadan - 01 (1080p).mkv")
    result = match_releases([release, release], MatchCriteria(aliases=("Dandadan",)))
    assert len(result.episodes[0].releases) == 1
