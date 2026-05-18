"""Pick which reviewer CLI runs against a given PR.

Rules:
  - Sticky per PR. Once a PR has been reviewed by Codex, subsequent rounds
    stay on Codex (and vice versa) for conversational continuity.
  - First-touch is quota-aware: prefer whichever of {codex, gemini} is armed.
  - Tiebreak by load balancing — round-robin across PRs based on db history.

Two functions matter to the rest of the loop:
  - `assigned_reviewer_cli(pr_number)` → the cli already used on this PR
    (None if no prior review).
  - `pick_reviewer_cli(pr_number)` → cli to use *now*. Sticky if assigned,
    fresh pick otherwise. May return a rate-limited cli (caller checks
    quota.is_blocked separately and chooses to wait or skip).

The arbiter is "the cli not used as reviewer on this PR" — see
`pick_arbiter_cli` below.
"""
from __future__ import annotations

import sqlite3

from .paths import DB_PATH
from . import quota


REVIEWER_CLIS = ("codex", "gemini")


# ---- per-PR sticky assignment -----------------------------------------------


def assigned_reviewer_cli(pr_number: int) -> str | None:
    """The cli that has reviewed this PR before. None if no prior review."""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    try:
        row = conn.execute(
            "SELECT agent FROM events "
            "WHERE phase='review' AND action='finish' AND pr_number=? "
            "AND agent IN ('codex','gemini') "
            "ORDER BY ts DESC LIMIT 1",
            (pr_number,),
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


# ---- fresh pick (load balance + quota awareness) ----------------------------


def _last_assignment_cli() -> str | None:
    """The cli used for the most recent fresh first-review across all PRs."""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    try:
        # "First reviews" = the round-1 row for each PR, which we approximate
        # by the earliest finish event per pr_number. Cheaper: just look at
        # the latest review event regardless of round — keeps load roughly even.
        row = conn.execute(
            "SELECT agent FROM events "
            "WHERE phase='review' AND action='finish' "
            "AND agent IN ('codex','gemini') "
            "ORDER BY ts DESC LIMIT 1",
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def fresh_reviewer_cli() -> str:
    """Pick a cli for a PR with no prior review. Prefer armed; round-robin tiebreak."""
    armed = [c for c in REVIEWER_CLIS if not quota.is_blocked(c)[0]]
    if len(armed) == 1:
        return armed[0]
    if not armed:
        # Both blocked. Pick whichever's gate expires sooner so the caller can
        # at least record an attempt and the gate eventually clears.
        soonest = min(REVIEWER_CLIS, key=lambda c: quota.is_blocked(c)[1] or float("inf"))
        return soonest

    # Both armed → round-robin: pick the one *not* used for the most recent assignment.
    last = _last_assignment_cli()
    if last in REVIEWER_CLIS:
        other = "codex" if last == "gemini" else "gemini"
        return other
    # No history → arbitrary but stable default.
    return "codex"


def pick_reviewer_cli(pr_number: int) -> str:
    """Sticky if this PR has been reviewed before, fresh pick otherwise."""
    return assigned_reviewer_cli(pr_number) or fresh_reviewer_cli()


def reviewer_persona_name(cli: str) -> str:
    return {"codex": "reviewer-codex", "gemini": "reviewer-gemini"}[cli]


# ---- arbiter ----------------------------------------------------------------


def pick_arbiter_cli(pr_number: int) -> str | None:
    """The arbiter is the cli that has NOT been used to review this PR.

    Returns None if both clis have somehow reviewed the same PR (shouldn't
    happen under sticky rotation, but might if a previous run swapped). The
    orchestrator interprets None as 'no clean tiebreaker — escalate to human'.
    """
    reviewer = assigned_reviewer_cli(pr_number)
    if reviewer not in REVIEWER_CLIS:
        # No prior reviewer — can't arbitrate something with no review.
        return None
    arbiter = "codex" if reviewer == "gemini" else "gemini"
    # Defensive: check arbiter wasn't also used (e.g., via prior cross-review).
    conn = sqlite3.connect(DB_PATH, timeout=5)
    try:
        row = conn.execute(
            "SELECT 1 FROM events "
            "WHERE phase='review' AND action='finish' AND pr_number=? AND agent=?",
            (pr_number, arbiter),
        ).fetchone()
    finally:
        conn.close()
    if row:
        return None  # both clis have reviewed, no clean third leg
    return arbiter


def arbiter_persona_name(cli: str) -> str:
    return {"codex": "arbiter-codex", "gemini": "arbiter-gemini"}[cli]
