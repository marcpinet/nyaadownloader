"""AniList lookups: turn "My Hero Academia" into the romaji title uploaders actually use."""

from __future__ import annotations

import httpx

from nyaadownloader.core.errors import NetworkError
from nyaadownloader.core.models import AnimeInfo
from nyaadownloader.core.parsing import normalize_title

API_URL = "https://graphql.anilist.co"

_SEARCH_QUERY = """
query ($search: String, $perPage: Int) {
  Page(perPage: $perPage) {
    media(search: $search, type: ANIME, sort: SEARCH_MATCH, isAdult: false) {
      id siteUrl episodes status format seasonYear synonyms
      title { romaji english native }
      coverImage { large color }
      nextAiringEpisode { episode }
    }
  }
}
"""


class AniListClient:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http
        self._cache: dict[str, list[AnimeInfo]] = {}

    def search(self, text: str, limit: int = 8) -> list[AnimeInfo]:
        key = " ".join(text.casefold().split())
        if key in self._cache:
            return self._cache[key]
        try:
            response = self._http.post(
                API_URL,
                json={"query": _SEARCH_QUERY, "variables": {"search": text, "perPage": limit}},
                timeout=10.0,
            )
            response.raise_for_status()
            media = response.json()["data"]["Page"]["media"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise NetworkError(f"AniList lookup failed: {exc}") from exc
        results = [_to_info(m) for m in media]
        self._cache[key] = results
        return results

    def fetch_image(self, url: str) -> bytes:
        try:
            response = self._http.get(url, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise NetworkError(f"Could not load cover: {exc}") from exc
        return response.content


def _to_info(media: dict) -> AnimeInfo:
    title = media.get("title") or {}
    cover = media.get("coverImage") or {}
    airing = media.get("nextAiringEpisode") or {}
    return AnimeInfo(
        id=media["id"],
        romaji=title.get("romaji") or "",
        english=title.get("english") or "",
        native=title.get("native") or "",
        synonyms=tuple(media.get("synonyms") or ()),
        episodes=media.get("episodes"),
        status=(media.get("status") or "").replace("_", " ").title(),
        format=(media.get("format") or "").replace("_", " "),
        year=media.get("seasonYear"),
        cover_url=cover.get("large") or "",
        color=cover.get("color") or "",
        site_url=media.get("siteUrl") or "",
        next_episode=airing.get("episode"),
    )


def resolve_title(client: AniListClient, text: str) -> AnimeInfo | None:
    """Best AniList entry for free text typed by the user, or ``None`` if unsure.

    Prefers an entry with a name equal to ``text``; otherwise takes the most relevant
    entry having ``text`` as whole words inside one of its names ("Frieren" →
    "Sousou no Frieren"), which is what people usually mean by a short title.
    """
    wanted = normalize_title(text)
    if not wanted:
        return None
    try:
        candidates = client.search(text, limit=6)
    except NetworkError:
        return None
    names = [(anime, [normalize_title(n) for n in (anime.romaji, anime.english, *anime.synonyms) if n])
             for anime in candidates]
    for anime, normalized in names:
        if wanted in normalized:
            return anime
    for anime, normalized in names:
        if any(f" {wanted} " in f" {n} " for n in normalized):
            return anime
    return None
