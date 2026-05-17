"""Merge gate: pure logic, no agent. Decides whether to auto-merge a PR."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import db, gh, kill_switch, protected  # noqa: E402
from lib.config import (  # noqa: E402
    LABEL_NEEDS_HUMAN, LABEL_PROTECTED_VIOLATION, LABEL_TOO_LARGE,
    LABEL_VETO, MAX_DIFF_LOC,
)


def _ci_state(pr: dict) -> str:
    """Returns 'green' | 'pending' | 'failing' | 'unknown'."""
    rolls = pr.get("statusCheckRollup") or []
    if not rolls:
        return "unknown"
    states = set()
    for r in rolls:
        # gh returns either GraphQL CheckRun shape ({status,conclusion})
        # or commit-status shape ({state}).
        c = r.get("conclusion") or r.get("state")
        s = r.get("status")
        if s and s != "COMPLETED":
            states.add("pending")
        if c:
            states.add(c.upper())
    if "pending" in states or {"IN_PROGRESS", "QUEUED", "WAITING"} & states:
        return "pending"
    bad = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
    if bad & states:
        return "failing"
    if states <= {"SUCCESS", "COMPLETED", "NEUTRAL", "SKIPPED"}:
        return "green"
    return "unknown"


def _latest_codex_verdict(pr: dict) -> str | None:
    """Latest review with our structured marker → 'APPROVE' | 'REQUEST_CHANGES' | 'COMMENT'."""
    reviews = [r for r in (pr.get("reviews") or [])
               if "##VERDICT:" in (r.get("body") or "")]
    if not reviews:
        return None
    m = re.search(r"##VERDICT:\s*(\S+)", reviews[-1].get("body", ""))
    return m.group(1) if m else None


def _gate_reasons(pr: dict) -> list[str]:
    """Returns [] if mergeable, else a list of blocker reasons."""
    reasons: list[str] = []

    labels = {l["name"] for l in pr.get("labels", [])}
    if LABEL_VETO in labels:
        reasons.append(f"{LABEL_VETO} label set")
    if LABEL_NEEDS_HUMAN in labels:
        reasons.append(f"{LABEL_NEEDS_HUMAN} label set")
    if LABEL_PROTECTED_VIOLATION in labels:
        reasons.append(f"{LABEL_PROTECTED_VIOLATION} label set")
    if LABEL_TOO_LARGE in labels:
        reasons.append(f"{LABEL_TOO_LARGE} label set")
    if pr.get("isDraft"):
        reasons.append("PR is draft")

    # Latest review must be APPROVE.
    verdict = _latest_codex_verdict(pr)
    if verdict != "APPROVE":
        reasons.append(f"latest codex verdict is {verdict or 'none'}")

    # Re-check protected paths (defense in depth).
    files = pr.get("files") or []
    bad = protected.violations([f.get("path") for f in files if f.get("path")])
    if bad:
        reasons.append(f"diff touches protected paths: {bad}")

    # Re-check diff size.
    adds = pr.get("additions", 0)
    dels = pr.get("deletions", 0)
    if (adds + dels) > MAX_DIFF_LOC:
        reasons.append(f"diff is {adds + dels} LOC, cap is {MAX_DIFF_LOC}")

    # CI green.
    state = _ci_state(pr)
    if state != "green":
        reasons.append(f"CI state is {state}")

    # gh's own mergeable computation.
    mergeable = (pr.get("mergeable") or "").upper()
    if mergeable in {"CONFLICTING", "UNKNOWN"} and mergeable != "MERGEABLE":
        # UNKNOWN is transient; surface but don't block.
        if mergeable == "CONFLICTING":
            reasons.append("PR has merge conflicts")

    return reasons


def evaluate(pr_number: int) -> int:
    """Returns 0 on merge, 1 on hold (with reasons logged), 2 on error."""
    kill_switch.check(reason="merge_gate start")
    try:
        pr = gh.get_pr(pr_number)
    except Exception as e:
        db.append(phase="merge", action="error", pr_number=pr_number,
                  notes={"error": repr(e)})
        return 2

    reasons = _gate_reasons(pr)
    if reasons:
        db.append(phase="merge", action="skip", pr_number=pr_number,
                  outcome="held",
                  notes={"reasons": reasons})
        return 1

    started = time.time()
    db.append(phase="merge", action="start", pr_number=pr_number)
    try:
        gh.merge_pr(number=pr_number, method="squash")
    except Exception as e:
        db.append(phase="merge", action="error", pr_number=pr_number,
                  duration_s=time.time() - started,
                  notes={"error": repr(e)})
        return 2

    db.append(phase="merge", action="finish", pr_number=pr_number,
              outcome="merged", duration_s=time.time() - started)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: merge_gate.py <pr_number>", file=sys.stderr)
        sys.exit(2)
    sys.exit(evaluate(int(sys.argv[1])))
