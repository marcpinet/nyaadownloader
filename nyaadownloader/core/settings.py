"""User preferences, stored as JSON in the roaming config folder."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from platformdirs import user_config_path, user_downloads_path

from nyaadownloader import APP_NAME
from nyaadownloader.core.models import Category
from nyaadownloader.core.nyaa import DEFAULT_BASE_URL

log = logging.getLogger(__name__)
HISTORY_SIZE = 15


def config_dir() -> Path:
    return user_config_path(APP_NAME, appauthor=False, roaming=True)


def _default_download_dir() -> str:
    return str(user_downloads_path() / APP_NAME)


@dataclass
class Settings:
    download_dir: str = field(default_factory=_default_download_dir)
    subfolder_per_anime: bool = True
    uploaders: list[str] = field(default_factory=lambda: ["SubsPlease", "Erai-raws"])
    resolution: int | None = 1080
    trusted_only: bool = False
    include_remakes: bool = False
    loose_matching: bool = False
    category: str = Category.ANIME_ENGLISH.value
    base_url: str = DEFAULT_BASE_URL
    open_torrents_after_download: bool = False
    notifications: bool = True
    theme: str = "system"
    history: list[str] = field(default_factory=list)
    window_geometry: str = ""
    window_state: str = ""
    header_state: str = ""

    @classmethod
    def load(cls, path: Path | None = None) -> Settings:
        path = path or config_dir() / "settings.json"
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError) as exc:
            log.warning("Ignoring unreadable settings file %s: %s", path, exc)
            return cls()
        settings = cls()
        if not isinstance(raw, dict):
            return settings
        defaults = asdict(settings)
        for f in fields(cls):
            if f.name not in raw:
                continue
            value, default = raw[f.name], defaults[f.name]
            if f.name == "resolution":
                if value is None or (isinstance(value, int) and not isinstance(value, bool)):
                    settings.resolution = value
            elif isinstance(default, list):
                if isinstance(value, list) and all(isinstance(v, str) for v in value):
                    setattr(settings, f.name, value)
            elif type(value) is type(default):
                setattr(settings, f.name, value)
        if settings.category not in {c.value for c in Category}:
            settings.category = Category.ANIME_ENGLISH.value
        if settings.theme not in ("system", "dark", "light"):
            settings.theme = "system"
        return settings

    def save(self, path: Path | None = None) -> None:
        path = path or config_dir() / "settings.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, path)
        except OSError as exc:
            log.warning("Could not save settings to %s: %s", path, exc)

    def remember_search(self, query: str) -> None:
        query = " ".join(query.split())
        if not query:
            return
        # In place: the search box keeps a reference to this list.
        self.history[:] = [query, *(h for h in self.history if h.casefold() != query.casefold())]
        del self.history[HISTORY_SIZE:]
