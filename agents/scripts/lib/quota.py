"""Detect subscription-quota errors and persist a retry-after gate.

Both `claude` and `codex` CLIs can hit their respective subscription rate
limits. When that happens we don't want to burn more quota retrying; we want
to skip the phase, log when the quota resets, and let the next tick (after
that timestamp) try again naturally.

Two pieces:

1. `detect(stderr_text)` — pattern-match the error and return a `RateLimit`
   record with the parsed reset time.
2. `is_blocked(cli)` — check `runs.sqlite` for an active rate-limit event for
   `cli` whose `retry_after_ts` is still in the future.

The orchestrator and phase scripts both call `is_blocked` before dispatch.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import time
from dataclasses import dataclass

from .paths import DB_PATH


# Codex prints (verbatim):
#   ERROR: You've hit your usage limit. Upgrade to Pro (...), visit ... or try
#   again at 9:24 PM.
# Claude's CLI message is similar but uses "Reset" / dates; we accept both
# absolute-time and ISO-ish forms. Gemini's CLI emits messages like
#   "Quota exceeded. Try again at 14:30." or RESOURCE_EXHAUSTED-style errors.
# All three are caught by the same broad fallback pattern.
_CODEX_LIMIT = re.compile(
    r"You['’]ve hit your usage limit.*?try again at\s+(?P<time>[0-9: ]+\s*[APap][Mm])",
    re.S,
)
_CLAUDE_LIMIT_TIME = re.compile(
    r"(?:rate.?limit|usage limit|usage cap|quota).*?(?:reset|resets|retry|try again)\s*(?:at|on)?\s*"
    r"(?P<time>\d{1,2}:\d{2}\s*[APap][Mm]|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}|\d{1,2}:\d{2})",
    re.I | re.S,
)
# Gemini's free-tier messages frequently include the literal phrase
# "resource exhausted" or "quota exceeded" with no explicit reset time; we
# treat that as a generic 1-hour cool-off so the loop doesn't immediately retry.
_GEMINI_GENERIC_LIMIT = re.compile(
    r"(?:RESOURCE_EXHAUSTED|resource\s+exhausted|quota\s+exceeded|429|rateLimitExceeded)",
    re.I,
)


@dataclass(frozen=True)
class RateLimit:
    cli: str                # 'claude' | 'codex'
    detected_at_ts: float
    retry_after_ts: float   # unix timestamp when the quota resets
    raw_message: str        # the matched stderr snippet, for the log


def detect(stderr_text: str, *, cli: str) -> RateLimit | None:
    """Return a RateLimit if the stderr signals a quota hit, else None."""
    if not stderr_text:
        return None

    # Try patterns that include an explicit retry time first.
    for pat in (_CODEX_LIMIT, _CLAUDE_LIMIT_TIME):
        m = pat.search(stderr_text)
        if not m:
            continue
        raw_time = m.group("time").strip()
        now = time.time()
        retry_ts = _parse_when(raw_time, now=now)
        if retry_ts is None or retry_ts <= now:
            continue
        return RateLimit(
            cli=cli,
            detected_at_ts=now,
            retry_after_ts=retry_ts,
            raw_message=stderr_text[m.start():m.end() + 80].strip(),
        )

    # Generic Gemini RESOURCE_EXHAUSTED / 429 without explicit reset → 1-hour gate.
    m = _GEMINI_GENERIC_LIMIT.search(stderr_text)
    if m:
        now = time.time()
        return RateLimit(
            cli=cli,
            detected_at_ts=now,
            retry_after_ts=now + 3600,
            raw_message=stderr_text[max(0, m.start() - 40):m.end() + 80].strip(),
        )

    return None


def _parse_when(text: str, *, now: float) -> float | None:
    """Parse a clock time like '9:24 PM' or an ISO date-time. Local timezone."""
    text = text.strip()

    # ISO form: 2026-05-17T21:24
    m = re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)
    if m:
        try:
            t = dt.datetime.fromisoformat(text)
            # Treat as local time; convert to unix ts.
            return t.timestamp()
        except ValueError:
            return None

    # Clock form: HH:MM AM/PM or H:MM AM/PM
    m = re.fullmatch(r"(\d{1,2}):(\d{2})\s*([APap][Mm])", text)
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3).upper()
    if ampm == "PM" and hour != 12:
        hour += 12
    if ampm == "AM" and hour == 12:
        hour = 0

    today = dt.datetime.fromtimestamp(now)
    candidate = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # If the parsed time is already in the past today, assume tomorrow.
    if candidate.timestamp() <= now:
        candidate += dt.timedelta(days=1)
    return candidate.timestamp()


# ---- db gate --------------------------------------------------------------


def record(rl: RateLimit) -> None:
    """Append a `rate_limited` event with the parsed retry_after_ts."""
    from . import db  # local import to avoid cycles
    db.append(
        phase="quota",
        action="rate_limited",
        agent=rl.cli,
        outcome="skip_until_reset",
        notes={
            "retry_after_ts": rl.retry_after_ts,
            "retry_after_iso": dt.datetime.fromtimestamp(rl.retry_after_ts).isoformat(),
            "raw": rl.raw_message[:300],
        },
    )


def is_blocked(cli: str) -> tuple[bool, float | None]:
    """Returns (blocked, retry_after_ts).

    Reads the most recent `phase=quota, agent=cli` event. If its
    `retry_after_ts` is in the future, the CLI is gated. Otherwise the gate
    has lapsed and `cli` is free to be invoked.
    """
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT notes FROM events "
            "WHERE phase='quota' AND agent=? AND action='rate_limited' "
            "ORDER BY ts DESC LIMIT 1",
            (cli,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row["notes"]:
        return False, None
    try:
        notes = json.loads(row["notes"])
    except Exception:
        return False, None
    ts = notes.get("retry_after_ts")
    if not isinstance(ts, (int, float)):
        return False, None
    if ts <= time.time():
        return False, None
    return True, float(ts)


def gate_message(cli: str) -> str:
    """Human-readable describer for status / log output."""
    blocked, ts = is_blocked(cli)
    if not blocked:
        return f"{cli}: armed"
    iso = dt.datetime.fromtimestamp(ts).strftime("%H:%M")
    return f"{cli}: rate-limited until {iso}"
