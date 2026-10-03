"""Minimal, fast Nyaa client.

Nyaa has no JSON API. The RSS feed is capped at 75 items and ignores paging, so this
scrapes the HTML listing instead: it is paginated (75 rows per page, 1000 results max)
and carries everything needed (seeders, size, date, magnet, trusted/remake flags).
"""

from __future__ import annotations

import html
import math
import re
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import httpx

from nyaadownloader import APP_NAME, REPO_URL, __version__
from nyaadownloader.core.errors import Cancelled, NetworkError, UnknownUploaderError
from nyaadownloader.core.models import Category, Release

DEFAULT_BASE_URL = "https://nyaa.si"
PAGE_SIZE = 75
MAX_PAGES = 1000 // PAGE_SIZE + 1  # Nyaa never returns more than 1000 results.

TRACKERS = (
    "http://nyaa.tracker.wf:7777/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
)

ProgressCallback = Callable[[int, int], None]

_ROW_RE = re.compile(r'<tr class="(?P<cls>[^"]*)">(?P<body>.*?)</tr>', re.S)
_VIEW_RE = re.compile(r'<a href="/view/(\d+)" title="([^"]*)"')
_CATEGORY_RE = re.compile(r'href="/\?c=(\d_\d)"')
_TORRENT_RE = re.compile(r'href="(/download/\d+\.torrent)"')
_MAGNET_RE = re.compile(r'href="(magnet:\?[^"]+)"')
_CELL_RE = re.compile(r'<td class="text-center"(?: data-timestamp="(\d+)")?>\s*([^<]*?)\s*</td>')
_TOTAL_RE = re.compile(r"out of (\d+) results")
_HASH_RE = re.compile(r"btih:([0-9a-fA-F]{40}|[A-Z2-7]{32})")
_SIZE_RE = re.compile(r"([\d.]+)\s*([KMGTP]?i?B|Bytes)", re.I)
_QUERY_OPERATOR_RE = re.compile(r'[|+"*()~\\]|(?:(?<=\s)|^)-')

_SIZE_UNITS = {"B": 0, "BYTES": 0, "KIB": 1, "MIB": 2, "GIB": 3, "TIB": 4, "PIB": 5,
               "KB": 1, "MB": 2, "GB": 3, "TB": 4, "PB": 5}


def make_http_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": f"{APP_NAME}/{__version__} (+{REPO_URL})"},
        timeout=httpx.Timeout(15.0, connect=10.0),
        follow_redirects=True,
        transport=httpx.HTTPTransport(retries=2),
        limits=httpx.Limits(max_connections=8, max_keepalive_connections=8),
    )


def parse_size(text: str) -> int:
    match = _SIZE_RE.search(text)
    if not match:
        return 0
    value, unit = float(match.group(1)), match.group(2).upper()
    return int(value * 1024 ** _SIZE_UNITS.get(unit, 0))


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def build_magnet(info_hash: str, name: str) -> str:
    trackers = "".join(f"&tr={quote(t, safe='')}" for t in TRACKERS)
    return f"magnet:?xt=urn:btih:{info_hash}&dn={quote(name, safe='')}{trackers}"


def _clean_term(term: str) -> str:
    """Strip characters Nyaa's search engine would read as operators."""
    return " ".join(_QUERY_OPERATOR_RE.sub(" ", term).split())


def build_query(titles: Iterable[str], extra_terms: Iterable[str] = ()) -> str:
    """Build a Nyaa query matching any of ``titles`` and all of ``extra_terms``."""
    cleaned = [t for t in dict.fromkeys(_clean_term(t) for t in titles) if t]
    if len(cleaned) > 1:
        query = "(" + "|".join(f"({t})" for t in cleaned) + ")"
    else:
        query = cleaned[0] if cleaned else ""
    extras = " ".join(t for t in (_clean_term(e) for e in extra_terms) if t)
    return f"{query} {extras}".strip()


def parse_search_page(page: str, base_url: str = DEFAULT_BASE_URL) -> tuple[list[Release], int | None]:
    """Return the releases listed on a search page and the total result count."""
    releases: list[Release] = []
    for row in _ROW_RE.finditer(page):
        body = row.group("body")
        view = _VIEW_RE.search(body)
        torrent = _TORRENT_RE.search(body)
        if not view or not torrent:
            continue
        cells = _CELL_RE.findall(body)
        if len(cells) < 5:
            continue
        size_text, (timestamp, _), seeders, leechers, downloads = (
            cells[0][1], cells[1], cells[2][1], cells[3][1], cells[4][1])
        name = html.unescape(view.group(2))
        magnet_match = _MAGNET_RE.search(body)
        magnet = html.unescape(magnet_match.group(1)) if magnet_match else ""
        hash_match = _HASH_RE.search(magnet)
        info_hash = hash_match.group(1).lower() if hash_match else ""
        if not magnet and info_hash:
            magnet = build_magnet(info_hash, name)
        category = _CATEGORY_RE.search(body)
        classes = row.group("cls").split()
        releases.append(Release(
            id=int(view.group(1)),
            name=name,
            torrent_url=base_url.rstrip("/") + torrent.group(1),
            magnet=magnet,
            info_hash=info_hash,
            size_bytes=parse_size(size_text),
            published=datetime.fromtimestamp(int(timestamp or 0), tz=UTC),
            seeders=_to_int(seeders),
            leechers=_to_int(leechers),
            downloads=_to_int(downloads),
            trusted="success" in classes,
            remake="danger" in classes,
            category=category.group(1) if category else "",
        ))
    total = _TOTAL_RE.search(page)
    return releases, int(total.group(1)) if total else None


def _to_int(text: str) -> int:
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return 0


class NyaaClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, http: httpx.Client | None = None,
                 max_workers: int = 4) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = http or make_http_client()
        self._owns_http = http is None
        self._max_workers = max_workers

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def search(
        self,
        query: str,
        *,
        uploader: str | None = None,
        category: Category = Category.ANIME_ENGLISH,
        trusted_only: bool = False,
        max_pages: int = MAX_PAGES,
        cancel: threading.Event | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> tuple[list[Release], int]:
        """Fetch every result page for ``query`` (newest first), in parallel after page 1.

        Returns the releases and the total number of matches Nyaa reported, which can
        exceed what was fetched since Nyaa stops at 1000 results.
        """
        params = {"q": query, "c": category.value, "f": "2" if trusted_only else "0",
                  "s": "id", "o": "desc"}
        if uploader:
            params["u"] = uploader

        first = self._get_page(params, 1, cancel, uploader)
        releases, total = parse_search_page(first, self.base_url)
        pages = min(max_pages, math.ceil((total or len(releases)) / PAGE_SIZE)) if releases else 1
        done = 1
        if on_progress:
            on_progress(done, pages)
        if pages <= 1:
            return releases, total or len(releases)

        def fetch(page: int) -> list[Release]:
            return parse_search_page(self._get_page(params, page, cancel, uploader), self.base_url)[0]

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            for page_releases in pool.map(fetch, range(2, pages + 1)):
                releases.extend(page_releases)
                done += 1
                if on_progress:
                    on_progress(done, pages)
        return releases, total or len(releases)

    def download_torrent(self, release: Release, destination: Path,
                         cancel: threading.Event | None = None) -> Path:
        response = self._request(release.torrent_url, None, cancel)
        if not response.content.startswith(b"d"):  # bencoded dictionaries start with "d"
            raise NetworkError(f"Nyaa did not return a torrent file for “{release.name}”.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination.with_suffix(destination.suffix + ".part")
        tmp.write_bytes(response.content)
        tmp.replace(destination)
        return destination

    def _get_page(self, params: dict[str, str], page: int, cancel: threading.Event | None,
                  uploader: str | None) -> str:
        response = self._request(self.base_url + "/", {**params, "p": str(page)}, cancel,
                                 allow_404=uploader is not None)
        if response.status_code == 404:
            raise UnknownUploaderError(uploader or "")
        return response.text

    def _request(self, url: str, params: dict[str, str] | None, cancel: threading.Event | None,
                 allow_404: bool = False, attempts: int = 4) -> httpx.Response:
        delay = 1.0
        for attempt in range(attempts):
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            try:
                response = self._http.get(url, params=params)
            except httpx.HTTPError as exc:
                if attempt == attempts - 1:
                    raise NetworkError(f"Could not reach {httpx.URL(url).host}: {exc}") from exc
            else:
                if response.status_code == 404 and allow_404:
                    return response
                if response.status_code < 400:
                    return response
                retryable = response.status_code == 429 or response.status_code >= 500
                if not retryable or attempt == attempts - 1:
                    raise NetworkError(f"{httpx.URL(url).host} answered HTTP {response.status_code}.")
                delay = _retry_after(response) or delay
            _sleep(delay, cancel)
            delay *= 2
        raise AssertionError("unreachable")


def _retry_after(response: httpx.Response) -> float | None:
    try:
        return min(float(response.headers.get("Retry-After", "")), 30.0)
    except ValueError:
        return None


def _sleep(seconds: float, cancel: threading.Event | None) -> None:
    if cancel is None:
        time.sleep(seconds)
    elif cancel.wait(seconds):
        raise Cancelled()
