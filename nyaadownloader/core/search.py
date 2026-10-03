"""High-level search: query Nyaa for every uploader, parse, match and rank."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from nyaadownloader.core.errors import UnknownUploaderError
from nyaadownloader.core.matching import MatchCriteria, MatchResult, match_releases
from nyaadownloader.core.models import AnimeInfo, Category, ParsedRelease, Release
from nyaadownloader.core.nyaa import MAX_PAGES, PAGE_SIZE, NyaaClient, build_query
from nyaadownloader.core.parsing import normalize_title, parse_release, split_season_suffix

RESULT_CAP = MAX_PAGES * PAGE_SIZE
EPISODES_PER_REFINED_QUERY = 12
MAX_REFINED_EPISODES = 120


@dataclass(frozen=True, slots=True)
class SearchRequest:
    query: str
    anime: AnimeInfo | None = None
    uploaders: tuple[str, ...] = ()
    resolution: int | None = 1080
    first_episode: int = 1
    last_episode: int | None = None
    trusted_only: bool = False
    include_remakes: bool = False
    loose: bool = False
    category: Category = Category.ANIME_ENGLISH

    def search_titles(self) -> list[str]:
        """Titles sent to Nyaa, without season suffixes so every numbering style is found."""
        titles = self.anime.search_titles() if self.anime else []
        titles.append(self.query)
        bases = (split_season_suffix(normalize_title(t))[0] for t in titles)
        return [b for b in dict.fromkeys(bases) if b]

    def aliases(self) -> tuple[str, ...]:
        names = [*(self.anime.aliases() if self.anime else []), self.query]
        return tuple(n for n in dict.fromkeys(names) if n.strip())

    def criteria(self) -> MatchCriteria:
        return MatchCriteria(
            aliases=self.aliases(),
            resolution=self.resolution,
            first_episode=self.first_episode,
            last_episode=self.last_episode,
            include_remakes=self.include_remakes,
            loose=self.loose,
        )


@dataclass(slots=True)
class SearchOutcome:
    request: SearchRequest
    result: MatchResult
    fetched: int
    truncated: bool
    elapsed: float
    warnings: list[str] = field(default_factory=list)


class _Progress:
    """Aggregates page progress from several concurrent queries."""

    def __init__(self, callback: Callable[[int, int], None] | None) -> None:
        self._callback = callback
        self._lock = threading.Lock()
        self._jobs: dict[object, tuple[int, int]] = {}

    def for_job(self, key: object) -> Callable[[int, int], None]:
        def report(done: int, total: int) -> None:
            with self._lock:
                self._jobs[key] = (done, total)
                done_sum = sum(d for d, _ in self._jobs.values())
                total_sum = sum(t for _, t in self._jobs.values())
            if self._callback:
                self._callback(done_sum, total_sum)
        return report


def _episode_term_chunks(first: int, last: int) -> list[str]:
    numbers = list(range(first, last + 1))
    chunks = []
    for i in range(0, len(numbers), EPISODES_PER_REFINED_QUERY):
        forms: list[str] = []
        for n in numbers[i:i + EPISODES_PER_REFINED_QUERY]:
            forms.append(str(n))
            if n < 10:
                forms.append(f"{n:02d}")
        chunks.append("(" + "|".join(forms) + ")")
    return chunks


def run_search(
    client: NyaaClient,
    request: SearchRequest,
    cancel: threading.Event | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> SearchOutcome:
    started = time.perf_counter()
    progress = _Progress(on_progress)
    extra = [f"{request.resolution}p"] if request.resolution else []
    query = build_query(request.search_titles(), extra)
    uploaders: list[str | None] = list(request.uploaders) or [None]

    releases: list[tuple[Release, int]] = []
    warnings: list[str] = []
    truncated = False
    unknown = 0
    for rank, uploader in enumerate(uploaders):
        def fetch(q: str, key: object, uploader: str | None = uploader) -> tuple[list[Release], int]:
            return client.search(q, uploader=uploader, category=request.category,
                                 trusted_only=request.trusted_only, cancel=cancel,
                                 on_progress=progress.for_job(key))
        try:
            found, total = fetch(query, (rank, "main"))
        except UnknownUploaderError as exc:
            warnings.append(str(exc))
            unknown += 1
            continue
        releases.extend((r, rank) for r in found)

        if total > RESULT_CAP:
            # Nyaa stops at 1000 results, newest first: for long-running shows ask again
            # for the exact episode numbers so older episodes are not silently missed.
            last = request.last_episode or (request.anime.aired_episodes if request.anime else None)
            if last is not None and last - request.first_episode < MAX_REFINED_EPISODES:
                for i, terms in enumerate(_episode_term_chunks(request.first_episode, last)):
                    found, _ = fetch(f"{query} {terms}", (rank, i))
                    releases.extend((r, rank) for r in found)
            else:
                truncated = True

    if unknown and unknown == len(uploaders):
        raise UnknownUploaderError(", ".join(u for u in request.uploaders))

    parsed: list[ParsedRelease] = []
    for release, rank in releases:
        item = parse_release(release)
        item.source_rank = rank
        parsed.append(item)
    result = match_releases(parsed, request.criteria())
    return SearchOutcome(
        request=request,
        result=result,
        fetched=len({r.id for r, _ in releases}),
        truncated=truncated,
        elapsed=time.perf_counter() - started,
        warnings=warnings,
    )
