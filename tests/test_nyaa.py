from __future__ import annotations

import re
import threading
from pathlib import Path

import httpx
import pytest

from nyaadownloader.core.errors import Cancelled, NetworkError, UnknownUploaderError
from nyaadownloader.core.nyaa import (
    NyaaClient,
    build_magnet,
    build_query,
    format_size,
    parse_search_page,
    parse_size,
)


def test_parse_search_page(search_page: str) -> None:
    releases, total = parse_search_page(search_page)
    assert total == 160
    assert [r.id for r in releases] == [2000003, 2000002, 2000001]

    trusted, remake, plain = releases
    assert trusted.name == "[SubsPlease] Sousou no Frieren - 03 (1080p) [7EF3F175].mkv"
    assert trusted.trusted and not trusted.remake
    assert trusted.torrent_url == "https://nyaa.si/download/2000003.torrent"
    assert trusted.view_url == "https://nyaa.si/view/2000003"
    assert trusted.info_hash == "676de9a8ec48fe5d210dd7f743c2a74b97b05d8a"
    assert trusted.magnet.startswith("magnet:?xt=urn:btih:676de9a8") and "&amp;" not in trusted.magnet
    assert trusted.size_bytes == int(1.4 * 1024 ** 3)
    assert (trusted.seeders, trusted.leechers, trusted.downloads) == (126, 1, 20345)
    assert trusted.published.timestamp() == 1696000000
    assert trusted.category == "1_2"

    assert remake.remake and not remake.trusted
    assert remake.name == "[Someone] Sousou no Frieren & Friends - 02 [720p].mkv"
    assert remake.info_hash == "5997f3ea2f32c6729f572b6b10a59946092b3c3f"

    assert plain.magnet == "" and plain.info_hash == ""
    assert plain.size_bytes == 800
    assert plain.category == "1_3"


def test_parse_search_page_without_results() -> None:
    assert parse_search_page("<html><h3>No results found</h3></html>") == ([], None)


@pytest.mark.parametrize(("text", "expected"), [
    ("1.5 GiB", int(1.5 * 1024 ** 3)),
    ("350.5 MiB", int(350.5 * 1024 ** 2)),
    ("12 KiB", 12 * 1024),
    ("800 Bytes", 800),
    ("garbage", 0),
])
def test_parse_size(text: str, expected: int) -> None:
    assert parse_size(text) == expected


def test_format_size() -> None:
    assert format_size(512) == "512 B"
    assert format_size(1536) == "1.5 KiB"
    assert format_size(3 * 1024 ** 3) == "3.0 GiB"


def test_build_query_strips_operators_and_combines_titles() -> None:
    assert build_query(["Sousou no Frieren"]) == "Sousou no Frieren"
    assert build_query(["Re:Zero -Starting Life"], ["1080p"]) == "Re:Zero Starting Life 1080p"
    assert build_query(["Erai-raws (test) | x"]) == "Erai-raws test x"
    assert build_query(["Boku no Hero Academia", "My Hero Academia", "boku no hero academia"], ["720p"]) == (
        "((Boku no Hero Academia)|(My Hero Academia)|(boku no hero academia)) 720p")


def test_build_magnet() -> None:
    magnet = build_magnet("abc", "[Group] Show - 01.mkv")
    assert magnet.startswith("magnet:?xt=urn:btih:abc&dn=%5BGroup%5D%20Show%20-%2001.mkv&tr=")
    assert magnet.count("&tr=") == 5


def _page(ids: list[int], total: int) -> str:
    rows = "".join(
        f'<tr class="default"><td colspan="2"><a href="/view/{i}" title="[G] Show - {i:02d} [1080p]">x</a></td>'
        f'<td class="text-center"><a href="/download/{i}.torrent"></a></td>'
        f'<td class="text-center">1 GiB</td><td class="text-center" data-timestamp="1700000000">d</td>'
        f'<td class="text-center">1</td><td class="text-center">0</td><td class="text-center">0</td></tr>'
        for i in ids)
    return f"<table>{rows}</table><div>Displaying results 1-75 out of {total} results.</div>"


def _client(handler) -> NyaaClient:
    return NyaaClient(http=httpx.Client(transport=httpx.MockTransport(handler)), max_workers=3)


def test_search_fetches_every_page() -> None:
    seen_pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["p"])
        seen_pages.append(request.url.params["p"])
        assert request.url.params["q"] == "show"
        assert request.url.params["u"] == "SubsPlease"
        assert request.url.params["f"] == "2"
        start = (page - 1) * 75
        return httpx.Response(200, text=_page(list(range(start, min(start + 75, 160))), 160))

    progress: list[tuple[int, int]] = []
    releases, total = _client(handler).search("show", uploader="SubsPlease", trusted_only=True,
                                              on_progress=lambda d, t: progress.append((d, t)))
    assert total == 160
    assert len(releases) == 160
    assert sorted(seen_pages) == ["1", "2", "3"]
    assert progress[-1] == (3, 3)


def test_search_respects_max_pages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_page(list(range(75)), 5000))

    releases, total = _client(handler).search("show", max_pages=2)
    assert total == 5000
    assert len(releases) == 150


def test_unknown_uploader() -> None:
    client = _client(lambda request: httpx.Response(404, text="Not found"))
    with pytest.raises(UnknownUploaderError):
        client.search("show", uploader="nobody")


def test_retries_rate_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nyaadownloader.core.nyaa._sleep", lambda seconds, cancel: None)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "1"})
        return httpx.Response(200, text=_page([1], 1))

    releases, _ = _client(handler).search("show")
    assert len(releases) == 1 and calls["n"] == 3


def test_gives_up_on_server_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nyaadownloader.core.nyaa._sleep", lambda seconds, cancel: None)
    client = _client(lambda request: httpx.Response(503))
    with pytest.raises(NetworkError, match="503"):
        client.search("show")


def test_connection_errors_become_network_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(NetworkError, match="Could not reach"):
        _client(handler).search("show")


def test_cancelled_before_request() -> None:
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        _client(lambda request: httpx.Response(200, text="")).search("show", cancel=cancel)


def test_download_torrent(tmp_path: Path, search_page: str) -> None:
    release = parse_search_page(search_page)[0][0]

    def handler(request: httpx.Request) -> httpx.Response:
        assert re.search(r"/download/2000003\.torrent$", str(request.url))
        return httpx.Response(200, content=b"d8:announce3:urle")

    target = tmp_path / "sub" / "file.torrent"
    assert _client(handler).download_torrent(release, target) == target
    assert target.read_bytes() == b"d8:announce3:urle"
    assert not list(tmp_path.rglob("*.part"))


def test_download_rejects_html(tmp_path: Path, search_page: str) -> None:
    release = parse_search_page(search_page)[0][0]
    client = _client(lambda request: httpx.Response(200, text="<html>DDoS protection</html>"))
    with pytest.raises(NetworkError):
        client.download_torrent(release, tmp_path / "x.torrent")
    assert not (tmp_path / "x.torrent").exists()
