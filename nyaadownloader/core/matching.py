"""Pick the right release for every episode out of a pile of Nyaa results."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from nyaadownloader.core.models import ParsedRelease
from nyaadownloader.core.parsing import (
    combine_season_labels,
    normalize_title,
    split_season_suffix,
)

LOOSE_SIMILARITY = 88
MAX_MISSING_SPAN = 500


@dataclass(frozen=True, slots=True)
class MatchCriteria:
    aliases: tuple[str, ...]
    resolution: int | None = None
    first_episode: int = 1
    last_episode: int | None = None
    include_remakes: bool = False
    loose: bool = False

    @property
    def has_explicit_range(self) -> bool:
        return self.first_episode > 1 or self.last_episode is not None


@dataclass(slots=True)
class EpisodeSlot:
    season_label: str
    episode: int
    releases: list[ParsedRelease] = field(default_factory=list)
    """Candidates, best first. Empty when no release was found for this episode."""
    chosen: int = 0

    @property
    def release(self) -> ParsedRelease | None:
        return self.releases[self.chosen] if self.releases else None

    @property
    def missing(self) -> bool:
        return not self.releases


@dataclass(slots=True)
class MatchResult:
    episodes: list[EpisodeSlot]
    batches: list[ParsedRelease]
    season_labels: list[str]
    preferred_season: str | None
    rejected_title: int = 0
    rejected_quality: int = 0
    rejected_other: int = 0


class TitleMatcher:
    """Decides whether a release title is the show being searched, and which season it is."""

    def __init__(self, aliases: tuple[str, ...], loose: bool = False) -> None:
        self.loose = loose
        self._aliases: list[tuple[str, str, str]] = []  # (full, base, season label)
        for alias in aliases:
            full = normalize_title(alias)
            if not full:
                continue
            base, label = split_season_suffix(full)
            self._aliases.append((full, base, label))

    @property
    def requested_seasons(self) -> set[str]:
        return {label for _, _, label in self._aliases if label}

    def match(self, release: ParsedRelease) -> str | None:
        """Return the release's season label ("" for none) if it matches, else ``None``."""
        title = normalize_title(release.title)
        for full, base, _ in self._aliases:
            for prefix in dict.fromkeys((full, base)):
                if title == prefix:
                    remainder = title[len(base):].split()
                    return combine_season_labels(release.season_label, _label(remainder))
                if title.startswith(prefix + " "):
                    remainder = title[len(base):].split()
                    rest_base, label = split_season_suffix(
                        " ".join(["x", *remainder]), allow_bare_digits=True)
                    if rest_base == "x":
                        return combine_season_labels(release.season_label, label)
        if self.loose:
            for full, base, _ in self._aliases:
                if f" {base} " in f" {title} " or fuzz.ratio(title, full) >= LOOSE_SIMILARITY:
                    return release.season_label
        return None


def _label(tokens: list[str]) -> str:
    if not tokens:
        return ""
    return split_season_suffix(" ".join(["x", *tokens]), allow_bare_digits=True)[1]


def rank_key(release: ParsedRelease, criteria: MatchCriteria) -> tuple:
    """Sort key, smaller is better."""
    r = release.release
    return (
        r.seeders == 0,
        release.source_rank,
        -release.resolution_value if criteria.resolution is None else 0,
        not r.trusted,
        r.remake,
        -release.version,
        -r.seeders,
        -r.published.timestamp(),
    )


def match_releases(releases: list[ParsedRelease], criteria: MatchCriteria) -> MatchResult:
    matcher = TitleMatcher(criteria.aliases, criteria.loose)
    by_slot: dict[tuple[str, int], list[ParsedRelease]] = defaultdict(list)
    batches: list[ParsedRelease] = []
    rejected_title = rejected_quality = rejected_other = 0
    seen: set[int] = set()

    for parsed in releases:
        if parsed.release.id in seen:
            continue
        seen.add(parsed.release.id)

        if parsed.release.remake and not criteria.include_remakes:
            rejected_other += 1
            continue
        label = matcher.match(parsed)
        if label is None:
            rejected_title += 1
            continue
        if criteria.resolution is not None and parsed.resolution_value != criteria.resolution:
            rejected_quality += 1
            continue
        parsed.season_label = label

        if parsed.episode is None or parsed.is_batch:
            last = criteria.last_episode
            overlaps = not parsed.episodes or (
                parsed.episodes[-1] >= criteria.first_episode
                and (last is None or parsed.episodes[0] <= last))
            if overlaps:
                batches.append(parsed)
            else:
                rejected_other += 1
            continue

        episode = parsed.episode
        if episode < criteria.first_episode or (
                criteria.last_episode is not None and episode > criteria.last_episode):
            rejected_other += 1
            continue
        by_slot[(label, episode)].append(parsed)

    slots = [EpisodeSlot(label, episode, sorted(found, key=lambda r: rank_key(r, criteria)))
             for (label, episode), found in by_slot.items()]
    slots.extend(_missing_slots(slots, criteria))
    slots.sort(key=lambda s: (s.season_label, s.episode))
    batches.sort(key=lambda r: rank_key(r, criteria))

    labels = sorted({s.season_label for s in slots})
    requested = matcher.requested_seasons & set(labels)
    return MatchResult(
        episodes=slots,
        batches=batches,
        season_labels=labels,
        preferred_season=next(iter(sorted(requested)), None),
        rejected_title=rejected_title,
        rejected_quality=rejected_quality,
        rejected_other=rejected_other,
    )


def _missing_slots(found: list[EpisodeSlot], criteria: MatchCriteria) -> list[EpisodeSlot]:
    """Placeholders for the gaps, so the user sees which episodes could not be found."""
    by_label: dict[str, set[int]] = defaultdict(set)
    for slot in found:
        by_label[slot.season_label].add(slot.episode)
    missing: list[EpisodeSlot] = []
    for label, episodes in by_label.items():
        low = criteria.first_episode if criteria.has_explicit_range else min(episodes)
        high = criteria.last_episode if criteria.last_episode is not None else max(episodes)
        if high - low > MAX_MISSING_SPAN:
            low = max(low, min(episodes))
            high = min(high, max(episodes))
        missing.extend(EpisodeSlot(label, ep) for ep in range(low, high + 1) if ep not in episodes)
    return missing
