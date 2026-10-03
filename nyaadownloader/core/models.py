from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Category(StrEnum):
    """Nyaa anime categories (the ``c`` query parameter)."""

    ANIME_ALL = "1_0"
    ANIME_ENGLISH = "1_2"
    ANIME_NON_ENGLISH = "1_3"
    ANIME_RAW = "1_4"

    @property
    def label(self) -> str:
        return {
            Category.ANIME_ALL: "All anime",
            Category.ANIME_ENGLISH: "English-translated",
            Category.ANIME_NON_ENGLISH: "Non-English-translated",
            Category.ANIME_RAW: "Raw",
        }[self]


@dataclass(frozen=True, slots=True)
class Release:
    """One torrent as listed on Nyaa."""

    id: int
    name: str
    torrent_url: str
    magnet: str
    info_hash: str
    size_bytes: int
    published: datetime
    seeders: int
    leechers: int
    downloads: int
    trusted: bool = False
    remake: bool = False
    category: str = ""

    @property
    def view_url(self) -> str:
        return self.torrent_url.split("/download/")[0] + f"/view/{self.id}"


@dataclass(slots=True)
class ParsedRelease:
    """A Nyaa release enriched with what could be read from its title."""

    release: Release
    title: str
    group: str = ""
    seasons: list[int] = field(default_factory=list)
    episodes: list[int] = field(default_factory=list)
    resolution: str = ""
    version: int = 1
    is_batch: bool = False
    codec: str = ""
    bit_depth: str = ""
    source: str = ""
    audio: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    dubbed: bool = False
    season_label: str = ""
    """Season variant used to group releases, e.g. ``"Season 2"`` or ``"Final Season"``."""
    source_rank: int = 0
    """Position of the uploader this came from in the user's preference list."""

    @property
    def episode(self) -> int | None:
        return self.episodes[0] if len(self.episodes) == 1 else None

    @property
    def resolution_value(self) -> int:
        digits = self.resolution.rstrip("pi")
        if digits.isdigit():
            return int(digits)
        return {"4k": 2160, "2k": 1440}.get(self.resolution.lower(), 0)

    @property
    def episode_span(self) -> str:
        if not self.episodes:
            return ""
        if len(self.episodes) == 1:
            return str(self.episodes[0])
        return f"{self.episodes[0]}–{self.episodes[-1]}"


@dataclass(frozen=True, slots=True)
class AnimeInfo:
    """An anime entry from AniList, used for title aliases and the info card."""

    id: int
    romaji: str
    english: str = ""
    native: str = ""
    synonyms: tuple[str, ...] = ()
    episodes: int | None = None
    status: str = ""
    format: str = ""
    year: int | None = None
    cover_url: str = ""
    color: str = ""
    site_url: str = ""
    next_episode: int | None = None

    @property
    def display_title(self) -> str:
        return self.romaji or self.english or self.native

    @property
    def aired_episodes(self) -> int | None:
        """Episodes released so far (for airing shows, the one before the next scheduled)."""
        if self.next_episode:
            return self.next_episode - 1
        return self.episodes

    def search_titles(self) -> list[str]:
        """Titles worth sending to Nyaa: romaji first, then English, deduplicated."""
        titles: list[str] = []
        for title in (self.romaji, self.english):
            if title and title.casefold() not in (t.casefold() for t in titles):
                titles.append(title)
        return titles

    def aliases(self) -> list[str]:
        """Every Latin-script name of the show, used to recognise release titles."""
        names = [*self.search_titles(), *self.synonyms]
        return [n for n in dict.fromkeys(names) if n and _is_latin(n)]


def _is_latin(text: str) -> bool:
    # Latin-1 + Latin Extended-A/B covers romanisations such as "Kaijū" or "Shōnen".
    return all(ord(ch) < 0x250 or not ch.isalpha() for ch in text)
