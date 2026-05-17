"""The daemon: polls GitHub state every TICK_SECONDS, dispatches one phase per tick.

Single-process state machine. Phases the orchestrator can dispatch:
  - work       (Claude implements an approved issue → opens PR)
  - review     (Codex reviews a PR with no current Codex review)
  - respond    (Claude addresses Codex's REQUEST_CHANGES)
  - merge      (PR has APPROVE + CI green + clean → auto-merge)
  - propose    (Claude files 1-3 new proposal issues)

Exactly one phase runs per tick. If the tick has nothing to do, sleep TICK_SECONDS
and try again. Daemon exits when:
  - kill switch engaged, OR
  - it's past OFF_HOURS_END and nothing is in flight, OR
  - SIGTERM received.

Concurrency: flock on agents/state/loop.lock keeps ticks single-threaded across
manual `loop tick` invocations and the daemon.
"""
from __future__ import annotations

import datetime as dt
import fcntl
import re
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import db, gh, kill_switch  # noqa: E402
from lib.config import (  # noqa: E402
    LABEL_APPROVED, LABEL_NEEDS_HUMAN, LABEL_PROTECTED_VIOLATION, LABEL_VETO,
    OFF_HOURS_END, OFF_HOURS_START, TICK_SECONDS,
)
from lib.paths import LOCK_PATH, ensure_state_dir  # noqa: E402

import work_issue  # noqa: E402
import review_pr  # noqa: E402
import respond_to_review  # noqa: E402
import merge_gate  # noqa: E402
import propose_issues  # noqa: E402


# ---- signal handling ------------------------------------------------------

_should_stop = False


def _on_sigterm(signum, frame):  # noqa: D401
    global _should_stop
    _should_stop = True


signal.signal(signal.SIGTERM, _on_sigterm)
signal.signal(signal.SIGINT, _on_sigterm)


# ---- time gates -----------------------------------------------------------


def _is_off_hours() -> bool:
    import os
    if os.environ.get("LOOP_FORCE_OFF_HOURS") == "1":
        return True
    h = dt.datetime.now().hour
    if OFF_HOURS_START < OFF_HOURS_END:
        return OFF_HOURS_START <= h < OFF_HOURS_END
    return h >= OFF_HOURS_START or h < OFF_HOURS_END


def _proposer_ran_today() -> bool:
    today_start = time.time() - (time.time() % 86400)
    events = db.recent(200)
    for ev in events:
        if (ev["phase"] == "propose" and ev["action"] in {"finish", "skip"}
                and ev["ts"] >= today_start):
            return True
    return False


# ---- PR classification ----------------------------------------------------


def _latest_codex_verdict(pr: dict) -> str | None:
    posts = gh.marker_posts(pr)
    if not posts:
        return None
    m = re.search(r"##VERDICT:\s*(\S+)", posts[-1]["body"])
    return m.group(1) if m else None


def _commits_since_review(pr: dict) -> bool:
    posts = gh.marker_posts(pr)
    if not posts:
        return True  # No review yet → "since" is trivially true
    last_ts = posts[-1]["ts"]
    commits = pr.get("commits") or []
    if not commits:
        return False
    return (commits[-1].get("committedDate") or "") > last_ts


def _is_agent_pr(pr: dict) -> bool:
    return any(l["name"].startswith("agent:") for l in pr.get("labels", []))


def _is_stalled(pr: dict) -> bool:
    """PR has a 'needs human' or 'veto' label → loop won't touch it."""
    bad = {LABEL_NEEDS_HUMAN, LABEL_VETO, LABEL_PROTECTED_VIOLATION}
    return any(l["name"] in bad for l in pr.get("labels", []))


# ---- the state machine ----------------------------------------------------


def _dispatch() -> tuple[str, int | None]:
    """Decide and run one phase. Returns (phase_name, target_id)."""
    # list_prs is cheap but only returns surface fields; we need reviews+comments
    # to classify state, so we re-fetch each candidate via get_pr (rarely >1-2 PRs).
    open_prs = gh.list_prs(state="open", limit=50)
    candidates = [p for p in open_prs if _is_agent_pr(p) and not _is_stalled(p)]
    candidates.sort(key=lambda p: p["createdAt"])
    agent_prs = [gh.get_pr(p["number"]) for p in candidates]

    for pr in agent_prs:
        verdict = _latest_codex_verdict(pr)

        # PR is approved + no new commits → try to merge.
        if verdict == "APPROVE" and not _commits_since_review(pr):
            rc = merge_gate.evaluate(pr["number"])
            return ("merge", pr["number"]) if rc == 0 else ("merge.skip", pr["number"])

        # PR has unaddressed change-requests → respond.
        if verdict == "REQUEST_CHANGES" and not _commits_since_review(pr):
            rc = respond_to_review.respond(pr["number"])
            return ("respond", pr["number"]) if rc == 0 else ("respond.skip", pr["number"])

        # PR has no review yet, OR new commits since last review → review.
        if verdict is None or _commits_since_review(pr):
            rc = review_pr.review(pr["number"])
            return ("review", pr["number"]) if rc == 0 else ("review.skip", pr["number"])

    # No PR work pending. Consider worker (off-hours only).
    if _is_off_hours():
        approved = gh.list_issues(labels=[LABEL_APPROVED], state="open", limit=5)
        if approved:
            rc = work_issue.run()
            return ("work", None) if rc == 0 else ("work.skip", None)

    # Consider proposer (once per day, off-hours only).
    if _is_off_hours() and not _proposer_ran_today():
        rc = propose_issues.run()
        return ("propose", None) if rc == 0 else ("propose.skip", None)

    return ("noop", None)


def one_tick() -> int:
    """Run a single dispatch step under the loop lock. Used by `loop tick`."""
    ensure_state_dir()
    lock_fp = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        db.append(phase="tick", action="skip", outcome="lock_held")
        print("loop.lock held by another process; skipping", file=sys.stderr)
        return 1
    try:
        try:
            kill_switch.check(reason="tick top")
        except kill_switch.HaltRequested as e:
            db.append(phase="tick", action="halted", notes={"reason": str(e)})
            print(f"Halted: {e}", file=sys.stderr)
            return 2

        started = time.time()
        phase, target = _dispatch()
        duration = time.time() - started
        db.append(
            phase="tick", action="finish",
            outcome=phase, duration_s=duration,
            notes={"target": target} if target else None,
        )
        return 0
    finally:
        try:
            fcntl.flock(lock_fp.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lock_fp.close()


def main() -> int:
    """Run as a daemon. Started by systemd at 23:00 CDT, exits ~06:00."""
    ensure_state_dir()
    db.append(phase="tick", action="daemon_start")

    while not _should_stop:
        # Wrap-up: if we're past OFF_HOURS_END and there are no in-flight PRs to merge, exit.
        if not _is_off_hours():
            agent_prs = [p for p in gh.list_prs(state="open", limit=50)
                         if _is_agent_pr(p) and not _is_stalled(p)]
            if not agent_prs:
                db.append(phase="tick", action="daemon_wrap", outcome="off_hours_done")
                break

        one_tick()

        # Sleep in 5s slices so SIGTERM is responsive.
        slept = 0
        while slept < TICK_SECONDS and not _should_stop:
            time.sleep(min(5, TICK_SECONDS - slept))
            slept += 5

    db.append(phase="tick", action="daemon_exit",
              notes={"sigterm": _should_stop})
    return 0


if __name__ == "__main__":
    sys.exit(main())
