"""Release title parsing (PTT plus anime-specific fixes) and title normalisation."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from PTT import parse_title

from nyaadownloader.core.models import ParsedRelease, Release

_LEADING_GROUP_RE = re.compile(r"^\s*[\[(【]([^\])】]{1,40})[\])】]")
_VERSION_RE = re.compile(r"(?<![a-z0-9])(?:e|ep)?\d{1,4}v(\d)(?![a-z0-9])", re.I)
_BATCH_RE = re.compile(r"\b(batch|complete series|complete season)\b", re.I)
_NON_WORD_RE = re.compile(r"[^\w]+")
_ORDINAL_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)$")
_SHORT_SEASON_RE = re.compile(r"^s(\d{1,2})$")
_ROMAN = {"ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}
_SEASON_WORDS = {"season", "final", "part", "cour", "the"}


def normalize_title(title: str) -> str:
    """Casefold, strip accents and punctuation: ``"Re:Zero – Kaijū"`` → ``"re zero kaiju"``."""
    decomposed = unicodedata.normalize("NFKD", title)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(_NON_WORD_RE.sub(" ", stripped.casefold().replace("_", " ")).split())


def _is_season_token(token: str, allow_bare_digits: bool) -> bool:
    return (
        token in _SEASON_WORDS
        or token in _ROMAN
        or bool(_ORDINAL_RE.match(token))
        or bool(_SHORT_SEASON_RE.match(token))
        or (allow_bare_digits and token.isdigit() and len(token) <= 2)
    )


def season_label_from_tokens(tokens: list[str]) -> str:
    """Turn season-ish tokens into a canonical label: ``["2nd", "season"]`` → ``"Season 2"``."""
    parts: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if token == "final" and nxt == "season":
            parts.append("Final Season")
            i += 2
            continue
        if (ordinal := _ORDINAL_RE.match(token)) and nxt == "season":
            parts.append(f"Season {int(ordinal.group(1))}")
            i += 2
            continue
        if token == "season" and nxt.isdigit():
            parts.append(f"Season {int(nxt)}")
            i += 2
            continue
        if token in ("part", "cour") and nxt.isdigit():
            parts.append(f"Part {int(nxt)}")
            i += 2
            continue
        if short := _SHORT_SEASON_RE.match(token):
            parts.append(f"Season {int(short.group(1))}")
        elif token in _ROMAN:
            parts.append(f"Season {_ROMAN[token]}")
        elif token.isdigit():
            parts.append(f"Season {int(token)}")
        elif token != "the":
            parts.append(token.title())
        i += 1
    return " ".join(dict.fromkeys(parts))


def split_season_suffix(normalized: str, allow_bare_digits: bool = False) -> tuple[str, str]:
    """Split ``"shingeki no kyojin the final season"`` into ``("shingeki no kyojin", "Final Season")``.

    Bare numbers are only treated as seasons when ``allow_bare_digits`` is set, so titles
    such as "Kaiju No. 8" or "Mob Psycho 100" keep their number.
    """
    tokens = normalized.split()
    cut = len(tokens)
    while cut > 1:
        token = tokens[cut - 1]
        numbered = token.isdigit() and tokens[cut - 2] in ("season", "part", "cour")
        if not (numbered or _is_season_token(token, allow_bare_digits)):
            break
        cut -= 1
    suffix = tokens[cut:]
    if not suffix or all(t in ("the", "part", "cour") for t in suffix):
        return normalized, ""
    return " ".join(tokens[:cut]), season_label_from_tokens(suffix)


def combine_season_labels(*labels: str) -> str:
    combined = " ".join(dict.fromkeys(label for label in labels if label))
    # Most groups never tag the first season, so "Season 1" is the same as no season.
    return "" if combined == "Season 1" else combined


@lru_cache(maxsize=4096)
def _parse_cached(name: str) -> dict:
    return parse_title(name, translate_languages=True)


def parse_release(release: Release) -> ParsedRelease:
    data = _parse_cached(release.name)
    name = release.name

    # PTT sometimes picks a trailing tag ("(Weekly)", "[Batch]") as the group: anime
    # releases put the group first, in brackets, so trust that when it is there.
    leading = _LEADING_GROUP_RE.match(name)
    group = leading.group(1).strip() if leading else data.get("group", "")

    version = 1
    if match := _VERSION_RE.search(name):
        version = int(match.group(1))

    episodes = sorted(set(data.get("episodes") or []))
    seasons = sorted(set(data.get("seasons") or []))
    is_batch = (
        len(episodes) > 1
        or bool(_BATCH_RE.search(name))
        or bool(data.get("complete"))
        or (not episodes and bool(seasons))
    )
    if group.casefold() == "batch":
        group = data.get("group", "") if data.get("group", "").casefold() != "batch" else ""

    return ParsedRelease(
        release=release,
        title=data.get("title", "") or name,
        group=group,
        seasons=seasons,
        episodes=episodes,
        resolution=data.get("resolution", ""),
        version=version,
        is_batch=is_batch,
        codec=(data.get("codec") or "").upper(),
        bit_depth=data.get("bit_depth", ""),
        source=data.get("quality", ""),
        audio=list(data.get("audio") or []),
        languages=list(data.get("languages") or []),
        dubbed=bool(data.get("dubbed")),
        season_label=f"Season {seasons[0]}" if len(seasons) == 1 else "",
    )
