from __future__ import annotations

import re

_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                   *(f"LPT{i}" for i in range(1, 10))}
MAX_NAME_LENGTH = 180  # leaves room for the folder path within Windows' 260-char limit


def sanitize_filename(name: str, fallback: str = "untitled") -> str:
    """Make ``name`` safe to use as a file or folder name on every OS."""
    cleaned = _INVALID_CHARS_RE.sub(" ", name)
    cleaned = " ".join(cleaned.split()).strip(" .")
    if cleaned.split(".")[0].upper() in _RESERVED_NAMES:
        cleaned = f"_{cleaned}"
    if len(cleaned) > MAX_NAME_LENGTH:
        cleaned = cleaned[:MAX_NAME_LENGTH].rstrip(" .")
    return cleaned or fallback

