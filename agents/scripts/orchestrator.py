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

from lib import db, gh, kill_switch, quota, rotation  # noqa: E402
from lib.config import (  # noqa: E402
    LABEL_APPROVED, LABEL_NEEDS_HUMAN, LABEL_PROPOSAL, LABEL_PROTECTED_VIOLATION,
    LABEL_VETO, MAX_REVIEW_ROUNDS, OFF_HOURS_END, OFF_HOURS_START, TICK_SECONDS,
)
from lib.persona import Persona  # noqa: E402
from lib.paths import LOCK_PATH, ensure_state_dir  # noqa: E402

import work_issue  # noqa: E402
import review_pr  # noqa: E402
import respond_to_review  # noqa: E402
import merge_gate  # noqa: E402
import propose_issues  # noqa: E402
import arbitrate_pr  # noqa: E402
import triage_proposals  # noqa: E402
import security_check  # noqa: E402
import drift_watcher  # noqa: E402


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
    return _phase_ran_today("propose")


def _triage_ran_today() -> bool:
    return _phase_ran_today("triage")


def _phase_ran_today(phase: str) -> bool:
    today_start = time.time() - (time.time() % 86400)
    events = db.recent(200)
    for ev in events:
        if (ev["phase"] == phase and ev["action"] in {"finish", "skip"}
                and ev["ts"] >= today_start):
            return True
    return False


def _drift_ran_this_week() -> bool:
    """drift_watcher fires once per Sunday at most."""
    week_ago = time.time() - 7 * 86400
    events = db.recent(500)
    for ev in events:
        if (ev["phase"] == "drift" and ev["action"] in {"finish", "skip"}
                and ev["ts"] >= week_ago):
            return True
    return False


# ---- PR classification ----------------------------------------------------


def _is_arbiter_override(post: dict) -> bool:
    return "Arbiter override" in post["body"]


def _latest_codex_verdict(pr: dict) -> str | None:
    """Reviewer's latest VERDICT (excludes arbiter's APPROVE override comments)."""
    posts = [p for p in gh.marker_posts(pr) if not _is_arbiter_override(p)]
    if not posts:
        return None
    m = re.search(r"##VERDICT:\s*(\S+)", posts[-1]["body"])
    return m.group(1) if m else None


def _latest_arbiter_verdict(pr: dict) -> tuple[str | None, str | None]:
    """Returns (verdict, ts). None if no arbiter has been invoked on this PR."""
    posts = gh.marker_posts(pr, marker="##ARBITER_VERDICT:")
    if not posts:
        return None, None
    m = re.search(r"##ARBITER_VERDICT:\s*(\S+)", posts[-1]["body"])
    return (m.group(1) if m else None), posts[-1]["ts"]


def _reviewer_rounds(pr: dict) -> int:
    """How many reviewer marker posts exist (excluding arbiter)."""
    return len([p for p in gh.marker_posts(pr) if not _is_arbiter_override(p)])


def _commits_since_review(pr: dict) -> bool:
    posts = [p for p in gh.marker_posts(pr) if not _is_arbiter_override(p)]
    if not posts:
        return True  # No review yet → "since" is trivially true
    last_ts = posts[-1]["ts"]
    commits = pr.get("commits") or []
    if not commits:
        return False
    return (commits[-1].get("committedDate") or "") > last_ts


def _commits_since_arbiter(pr: dict) -> bool:
    """True if engineer has committed since the latest arbiter verdict."""
    _, arb_ts = _latest_arbiter_verdict(pr)
    if not arb_ts:
        return False
    commits = pr.get("commits") or []
    if not commits:
        return False
    return (commits[-1].get("committedDate") or "") > arb_ts


def _is_agent_pr(pr: dict) -> bool:
    return any(l["name"].startswith("agent:") for l in pr.get("labels", []))


def _is_stalled(pr: dict) -> bool:
    """PR has a 'needs human' or 'veto' label → loop won't touch it."""
    bad = {LABEL_NEEDS_HUMAN, LABEL_VETO, LABEL_PROTECTED_VIOLATION}
    return any(l["name"] in bad for l in pr.get("labels", []))


# ---- the state machine ----------------------------------------------------


def _persona_blocked(persona_name: str) -> bool:
    """True if the CLI behind this persona is currently rate-limited."""
    persona = Persona.load(persona_name)
    blocked, _ = quota.is_blocked(persona.cli)
    return blocked


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
        arb_verdict, _ = _latest_arbiter_verdict(pr)

        # ---- arbiter has spoken on this PR ----
        if arb_verdict is not None:
            # APPROVE_FOR_MERGE: arbiter posted a synthetic ##VERDICT: APPROVE,
            # so the reviewer-verdict check below sees APPROVE and falls into
            # the merge branch. Don't dispatch anything here.
            if arb_verdict == "REQUEST_FINAL_CHANGES":
                if _commits_since_arbiter(pr):
                    # Engineer addressed the final-changes ask → arbiter looks
                    # one more time (re-arbitrate). After this second look, the
                    # arbiter can only APPROVE or ESCALATE — no further loops.
                    rc = arbitrate_pr.arbitrate(pr["number"])
                    return ("arbitrate", pr["number"]) if rc == 0 else ("arbitrate.skip", pr["number"])
                # Engineer hasn't responded yet to the final-changes ask → respond.
                if _persona_blocked("engineer"):
                    continue
                rc = respond_to_review.respond(pr["number"])
                return ("respond", pr["number"]) if rc == 0 else ("respond.skip", pr["number"])
            # ESCALATE_TO_HUMAN is handled by _is_stalled (the arbiter applied
            # agent:needs-human, so the PR was filtered out before this loop).

        # ---- reviewer rounds capped → arbiter takes over ----
        # When the reviewer has emitted MAX_REVIEW_ROUNDS verdicts and the last
        # one is REQUEST_CHANGES, we do NOT dispatch round (cap+1). Instead the
        # arbiter judges the standoff. The engineer doesn't get a 4th attempt
        # under the regular reviewer — the arbiter chooses whether to give them
        # one more pass via REQUEST_FINAL_CHANGES.
        if (verdict == "REQUEST_CHANGES"
                and _reviewer_rounds(pr) >= MAX_REVIEW_ROUNDS
                and arb_verdict is None):
            rc = arbitrate_pr.arbitrate(pr["number"])
            return ("arbitrate", pr["number"]) if rc == 0 else ("arbitrate.skip", pr["number"])

        # ---- normal reviewer / engineer / merge flow ----
        # PR is approved + no new commits → security check (if needed) then merge.
        if verdict == "APPROVE" and not _commits_since_review(pr):
            labels = {l["name"] for l in pr.get("labels", [])}
            if ("agent:security-cleared" not in labels
                    and "agent:security-flag" not in labels):
                # Hasn't been scanned. security_check.check() handles "not
                # sensitive" by applying the cleared label without an LLM call,
                # so this is cheap when no sensitive paths are touched.
                if _persona_blocked("security"):
                    continue  # retry next tick once gemini's armed
                rc = security_check.check(pr["number"])
                return ("security", pr["number"]) if rc == 0 else ("security.skip", pr["number"])
            # Already scanned. If flagged, merge gate refuses (agent:needs-human
            # was also applied so _is_stalled would have filtered, but if we got
            # here merge_gate still re-checks).
            rc = merge_gate.evaluate(pr["number"])
            return ("merge", pr["number"]) if rc == 0 else ("merge.skip", pr["number"])

        # PR has unaddressed change-requests → engineer responds.
        if verdict == "REQUEST_CHANGES" and not _commits_since_review(pr):
            if _persona_blocked("engineer"):
                continue
            rc = respond_to_review.respond(pr["number"])
            return ("respond", pr["number"]) if rc == 0 else ("respond.skip", pr["number"])

        # PR has no review yet, OR new commits since last review → reviewer.
        if verdict is None or _commits_since_review(pr):
            # Quota-aware via rotation: pick whichever reviewer cli is armed
            # for THIS PR (sticky if already-assigned, fresh otherwise).
            chosen = rotation.pick_reviewer_cli(pr["number"])
            blocked, _ = quota.is_blocked(chosen)
            if blocked:
                continue
            rc = review_pr.review(pr["number"])
            return ("review", pr["number"]) if rc == 0 else ("review.skip", pr["number"])

    # No PR work pending. Consider engineer working a new issue (off-hours only).
    if _is_off_hours() and not _persona_blocked("engineer"):
        approved = gh.list_issues(labels=[LABEL_APPROVED], state="open", limit=5)
        if approved:
            rc = work_issue.run()
            return ("work", None) if rc == 0 else ("work.skip", None)

    # Consider proposer (once per day, off-hours only).
    if (_is_off_hours()
            and not _proposer_ran_today()
            and not _persona_blocked("proposer")):
        rc = propose_issues.run()
        return ("propose", None) if rc == 0 else ("propose.skip", None)

    # Consider triage (once per day, off-hours, after proposer has run today
    # and there are unhandled proposals).
    if (_is_off_hours()
            and not _triage_ran_today()
            and _proposer_ran_today()
            and not _persona_blocked("triage")):
        proposals = gh.list_issues(labels=[LABEL_PROPOSAL], state="open", limit=5)
        if proposals:
            rc = triage_proposals.run()
            return ("triage", None) if rc == 0 else ("triage.skip", None)

    # Consider drift_watcher (once per week, Sundays, off-hours).
    # Sunday = weekday() == 6. Avoid double-firing within the same week by
    # checking the last 7 days of drift events.
    if (_is_off_hours()
            and dt.datetime.now().weekday() == 6
            and not _drift_ran_this_week()
            and not _persona_blocked("drift_watcher")):
        rc = drift_watcher.run()
        return ("drift", None) if rc == 0 else ("drift.skip", None)

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
