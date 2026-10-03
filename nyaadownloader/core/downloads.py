from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from nyaadownloader.core.errors import Cancelled, NyaaDownloaderError
from nyaadownloader.core.files import sanitize_filename
from nyaadownloader.core.models import ParsedRelease
from nyaadownloader.core.nyaa import NyaaClient


@dataclass(slots=True)
class DownloadReport:
    folder: Path
    saved: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failed: list[tuple[ParsedRelease, str]] = field(default_factory=list)

    @property
    def paths(self) -> list[Path]:
        return [*self.saved, *self.skipped]


def torrent_path(folder: Path, release: ParsedRelease) -> Path:
    return folder / f"{sanitize_filename(release.release.name, fallback=str(release.release.id))}.torrent"


def download_torrents(
    client: NyaaClient,
    releases: list[ParsedRelease],
    folder: Path,
    cancel: threading.Event | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    max_workers: int = 4,
) -> DownloadReport:
    """Save every release's .torrent into ``folder``; already present files are kept."""
    report = DownloadReport(folder)
    folder.mkdir(parents=True, exist_ok=True)
    todo: list[tuple[ParsedRelease, Path]] = []
    for release in releases:
        path = torrent_path(folder, release)
        if path.exists() and path.stat().st_size > 0:
            report.skipped.append(path)
        else:
            todo.append((release, path))

    done = len(report.skipped)
    if on_progress:
        on_progress(done, len(releases))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(client.download_torrent, r.release, p, cancel): r for r, p in todo}
        for future in as_completed(futures):
            release = futures[future]
            try:
                report.saved.append(future.result())
            except Cancelled:
                for pending in futures:
                    pending.cancel()
                raise
            except (NyaaDownloaderError, OSError) as exc:
                report.failed.append((release, str(exc)))
            done += 1
            if on_progress:
                on_progress(done, len(releases))
    return report
