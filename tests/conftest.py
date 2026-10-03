from __future__ import annotations

import os
from datetime import UTC, datetime
from itertools import count
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from nyaadownloader.core.models import Release  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
_ids = count(1)


def make_release(name: str, *, seeders: int = 10, trusted: bool = False, remake: bool = False,
                 size: int = 1_000_000, days_ago: int = 0) -> Release:
    release_id = next(_ids)
    return Release(
        id=release_id,
        name=name,
        torrent_url=f"https://nyaa.si/download/{release_id}.torrent",
        magnet=f"magnet:?xt=urn:btih:{release_id:040x}",
        info_hash=f"{release_id:040x}",
        size_bytes=size,
        published=datetime.fromtimestamp(1_700_000_000 - days_ago * 86400, tz=UTC),
        seeders=seeders,
        leechers=0,
        downloads=0,
        trusted=trusted,
        remake=remake,
    )


@pytest.fixture
def search_page() -> str:
    return (FIXTURES / "search_page.html").read_text(encoding="utf-8")
