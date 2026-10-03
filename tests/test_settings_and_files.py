from __future__ import annotations

import json
from pathlib import Path

import httpx
from conftest import make_release

from nyaadownloader.core.downloads import download_torrents, torrent_path
from nyaadownloader.core.files import sanitize_filename
from nyaadownloader.core.nyaa import NyaaClient
from nyaadownloader.core.parsing import parse_release
from nyaadownloader.core.settings import HISTORY_SIZE, Settings


def test_settings_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    settings = Settings(uploaders=["ASW"], resolution=None, theme="light")
    settings.save(path)
    loaded = Settings.load(path)
    assert loaded.uploaders == ["ASW"]
    assert loaded.resolution is None
    assert loaded.theme == "light"


def test_settings_ignore_bad_values(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"uploaders": "SubsPlease", "resolution": True, "theme": "neon",
                                "trusted_only": "yes", "category": "9_9", "unknown": 1}))
    loaded = Settings.load(path)
    defaults = Settings()
    assert loaded.uploaders == defaults.uploaders
    assert loaded.resolution == defaults.resolution
    assert loaded.theme == "system"
    assert loaded.trusted_only is False
    assert loaded.category == defaults.category


def test_settings_survive_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{not json")
    assert Settings.load(path) == Settings()


def test_history_is_deduplicated_and_capped() -> None:
    settings = Settings()
    history = settings.history
    for i in range(HISTORY_SIZE + 5):
        settings.remember_search(f"show {i}")
    settings.remember_search("SHOW 3")
    assert settings.history is history
    assert len(history) == HISTORY_SIZE
    assert history[0] == "SHOW 3"
    assert sum(h.casefold() == "show 3" for h in history) == 1


def test_sanitize_filename() -> None:
    assert sanitize_filename('[Group] Show: "Part" 1/2?') == "[Group] Show Part 1 2"
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename(" ... ") == "untitled"
    assert len(sanitize_filename("x" * 400)) <= 180


def test_download_torrents_skips_existing_and_reports_failures(tmp_path: Path) -> None:
    good, bad, existing = (parse_release(make_release(n)) for n in ("[A] Show - 01", "[A] Show - 02", "[A] Show - 03"))
    torrent_path(tmp_path, existing).write_bytes(b"d1:ae")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(f"/{bad.release.id}.torrent"):
            return httpx.Response(404)
        return httpx.Response(200, content=b"d1:ae")

    client = NyaaClient(http=httpx.Client(transport=httpx.MockTransport(handler)))
    progress = []
    report = download_torrents(client, [good, bad, existing], tmp_path, on_progress=lambda d, t: progress.append(d))
    assert report.saved == [torrent_path(tmp_path, good)]
    assert report.skipped == [torrent_path(tmp_path, existing)]
    assert [r for r, _ in report.failed] == [bad]
    assert progress[-1] == 3
