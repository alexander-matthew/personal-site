"""Protected-path enforcement. Agents must not modify these files."""
from __future__ import annotations

from .config import PROTECTED_PATHS


def violations(changed_paths: list[str]) -> list[str]:
    """Return the subset of changed paths that match a protected prefix."""
    hits = []
    for p in changed_paths:
        for prefix in PROTECTED_PATHS:
            if p == prefix.rstrip("/") or p.startswith(prefix):
                hits.append(p)
                break
    return hits
