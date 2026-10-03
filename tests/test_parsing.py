from __future__ import annotations

import pytest
from conftest import make_release

from nyaadownloader.core.parsing import (
    combine_season_labels,
    normalize_title,
    parse_release,
    split_season_suffix,
)


def test_normalize_title() -> None:
    assert normalize_title("Re:Zero kara Hajimeru") == "re zero kara hajimeru"
    assert normalize_title("Kaijū No. 8") == "kaiju no 8"
    assert normalize_title("  Dr.  STONE – New_World ") == "dr stone new world"


@pytest.mark.parametrize(("title", "expected"), [
    ("shingeki no kyojin the final season", ("shingeki no kyojin", "Final Season")),
    ("boku no hero academia 2nd season", ("boku no hero academia", "Season 2")),
    ("overlord iv", ("overlord", "Season 4")),
    ("dandadan s2", ("dandadan", "Season 2")),
    ("dr stone new world part 2", ("dr stone new world", "Part 2")),
    ("sousou no frieren season 2", ("sousou no frieren", "Season 2")),
    # Numbers that are part of the title are kept.
    ("kaiju no 8", ("kaiju no 8", "")),
    ("mob psycho 100", ("mob psycho 100", "")),
    ("86", ("86", "")),
])
def test_split_season_suffix(title: str, expected: tuple[str, str]) -> None:
    assert split_season_suffix(title) == expected


def test_split_season_suffix_bare_digits_when_allowed() -> None:
    assert split_season_suffix("x 2", allow_bare_digits=True) == ("x", "Season 2")


def test_combine_season_labels() -> None:
    assert combine_season_labels("Season 2", "Season 2") == "Season 2"
    assert combine_season_labels("", "Final Season") == "Final Season"
    assert combine_season_labels("Season 1") == ""


def test_parse_release_basic() -> None:
    parsed = parse_release(make_release("[SubsPlease] Sousou no Frieren - 05 (1080p) [8E3F8FA5].mkv"))
    assert parsed.title == "Sousou no Frieren"
    assert parsed.group == "SubsPlease"
    assert parsed.episodes == [5] and parsed.episode == 5
    assert parsed.resolution == "1080p" and parsed.resolution_value == 1080
    assert not parsed.is_batch


def test_parse_release_prefers_leading_group() -> None:
    parsed = parse_release(make_release("[Judas] Sousou no Frieren - S01E28 [1080p][HEVC x265 10bit] (Weekly)"))
    assert parsed.group == "Judas"
    assert parsed.episodes == [28]
    assert parsed.codec == "HEVC"


def test_parse_release_version_and_season() -> None:
    name = "[Erai-raws] Boku no Hero Academia 5th Season - 05v2 [1080p][Multiple Subtitle]"
    parsed = parse_release(make_release(name))
    assert parsed.version == 2
    assert parsed.seasons == [5] and parsed.season_label == "Season 5"
    assert parsed.episode == 5


@pytest.mark.parametrize("name", [
    "[SubsPlease] Boku no Hero Academia (160-171) (1080p) [Batch]",
    "[Erai-raws] Sousou no Frieren - 01 ~ 28 [1080p][HEVC][BATCH][Multiple Subtitle]",
    "[EMBER] Kaiju No. 8 (2024) (Season 1) [BDRip] [1080p Dual Audio HEVC 10 bits DDP] (Batch)",
])
def test_parse_release_batches(name: str) -> None:
    parsed = parse_release(make_release(name))
    assert parsed.is_batch
    assert parsed.episode is None
    assert parsed.group.casefold() != "batch"
