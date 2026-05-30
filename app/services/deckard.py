"""Deckard's Diary — entry loading and access.

A "diary entry" is one day's short-form piece (a poem or story fragment) paired
with a deterministic generative-art sketch. Entries are plain JSON files on disk
so the corpus scales by committing files (git is the database); the matching art
algorithm lives as a real ``.js`` file under ``static/`` so the page can both
*run* it and *display the exact same source*.

This module is intentionally dependency-free and side-effect-free at import time
so it is cheap to call per-request and trivial to unit test.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

# app/services/deckard.py -> project root is three parents up.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENTRIES_DIR = _PROJECT_ROOT / 'app' / 'content' / 'deckard' / 'entries'
SKETCHES_DIR = _PROJECT_ROOT / 'app' / 'static' / 'js' / 'deckard' / 'sketches'

# Public, browser-reachable prefix for a sketch file given its date stem.
SKETCH_URL_PREFIX = '/static/js/deckard/sketches'


class EntryNotFound(Exception):
    """Raised when a requested diary date has no entry on disk."""


def _coerce(raw: dict[str, Any], date: str) -> dict[str, Any]:
    """Normalise an on-disk entry into the shape templates rely on.

    Tolerant of partially-specified files so hand-authored and machine-authored
    entries can coexist while the schema settles.
    """
    art = dict(raw.get('art') or {})
    # The sketch source-of-truth is a sibling .js file named after the date.
    art.setdefault('sketch_url', f'{SKETCH_URL_PREFIX}/{date}.js')
    art.setdefault('language', 'javascript')
    art.setdefault('title', 'untitled study')

    poem = raw.get('poem')
    if isinstance(poem, str):
        poem = poem.splitlines()

    return {
        'date': date,
        'day_number': raw.get('day_number'),
        'title': raw.get('title', 'untitled'),
        'form': raw.get('form', 'fragment'),
        'epigraph': raw.get('epigraph'),
        'poem': poem or [],
        'palette': raw.get('palette') or ['#4da6ff', '#e8e8e8', '#6a6a6a'],
        'art': art,
        'colophon': raw.get('colophon'),
        'seed_phrase': raw.get('seed_phrase'),
    }


@lru_cache(maxsize=1)
def _entry_index() -> list[str]:
    """Sorted list of entry dates (YYYY-MM-DD), newest last."""
    if not ENTRIES_DIR.exists():
        return []
    return sorted(p.stem for p in ENTRIES_DIR.glob('*.json'))


def reload() -> None:
    """Drop the cached index. Call after writing a new entry in-process."""
    _entry_index.cache_clear()


def list_dates(newest_first: bool = True) -> list[str]:
    dates = list(_entry_index())
    return list(reversed(dates)) if newest_first else dates


def get_entry(date: str) -> dict[str, Any]:
    path = ENTRIES_DIR / f'{date}.json'
    if not path.exists():
        raise EntryNotFound(date)
    raw = json.loads(path.read_text(encoding='utf-8'))
    return _coerce(raw, date)


def latest_date() -> str | None:
    dates = _entry_index()
    return dates[-1] if dates else None


def latest_entry() -> dict[str, Any] | None:
    date = latest_date()
    return get_entry(date) if date else None


def neighbours(date: str) -> tuple[str | None, str | None]:
    """Return (older, newer) entry dates adjacent to ``date``."""
    dates = _entry_index()
    if date not in dates:
        return (None, None)
    i = dates.index(date)
    older = dates[i - 1] if i > 0 else None
    newer = dates[i + 1] if i < len(dates) - 1 else None
    return (older, newer)


def entry_summaries() -> list[dict[str, Any]]:
    """Lightweight metadata for every entry, newest first (for the archive)."""
    out: list[dict[str, Any]] = []
    for date in list_dates(newest_first=True):
        try:
            e = get_entry(date)
        except (EntryNotFound, json.JSONDecodeError):
            continue
        out.append(
            {
                'date': date,
                'day_number': e['day_number'],
                'title': e['title'],
                'form': e['form'],
                'palette': e['palette'],
            }
        )
    return out
