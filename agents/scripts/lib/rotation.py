"""Pick which reviewer CLI runs against a given PR.

Rules:
  - Consensus: all REQUIRED_REVIEWER_CLIS must provide an APPROVE verdict for
    the CURRENT commit before a PR is eligible for merge.
  - Sticky per round: a specific agent owns its review thread for the current
    commit.
  - Quota-aware: prefer whichever of {codex, gemini} is armed.
  - Arbiter: the third leg of the stool, invoked when consensus fails.
"""
from __future__ import annotations

import sqlite3
import re

from .paths import DB_PATH
from . import quota, gh
from .config import REQUIRED_REVIEWER_CLIS


REVIEWER_CLIS = REQUIRED_REVIEWER_CLIS


# ---- consensus state --------------------------------------------------------


def reviewer_verdicts(pr_number: int) -> dict[str, str]:
    """Latest verdict from each agent for the CURRENT commit of the PR.
    
    Returns a dict {cli: verdict} where verdict is APPROVE | REQUEST_CHANGES | COMMENT.
    Only considers reviews posted *after* the latest commit.
    
    Includes arbiter overrides: if the arbiter posts an APPROVE_FOR_MERGE,
    this is treated as a synthetic APPROVE from the reviewing agent it replaced.
    """
    pr = gh.get_pr(pr_number)
    commits = pr.get("commits") or []
    if not commits:
        return {}
    
    latest_commit_ts = commits[-1].get("committedDate") or ""
    posts = gh.marker_posts(pr)
    
    verdicts = {}
    
    # We also check for arbiter overrides. If an arbiter spoke, we treat its
    # verdict as the definitive one for the agent it replaced.
    # Regex anchors to the trailer line (`*arbiter: <cli>`) to avoid matching
    # the word "arbiter:" inside the prose of the verdict reasoning.
    arb_posts = gh.marker_posts(pr, marker="##ARBITER_VERDICT:")
    if arb_posts and arb_posts[-1]["ts"] > latest_commit_ts:
        m = re.search(r"##ARBITER_VERDICT:\s*(\S+)", arb_posts[-1]["body"])
        if m and m.group(1) == "APPROVE_FOR_MERGE":
            m_arb_agent = re.search(r"\*arbiter:\s*(\w+)", arb_posts[-1]["body"])
            if m_arb_agent:
                arb_agent = m_arb_agent.group(1)
                overridden_agent = "codex" if arb_agent == "gemini" else "gemini"
                verdicts[overridden_agent] = "APPROVE"

    for post in reversed(posts):
        if post["ts"] <= latest_commit_ts:
            break

        # Format trailer: "*Round N/M · reviewer: <agent> · ...*"
        # Anchor the regex to the trailer line so prose mentions of "reviewer:"
        # inside the review body can't spoof the agent identity.
        m_agent = re.search(r"\*Round\s+\d+/\d+\s*·\s*reviewer:\s*(\w+)", post["body"])
        m_verdict = re.search(r"##VERDICT:\s*(\S+)", post["body"])
        
        if m_agent and m_verdict:
            agent = m_agent.group(1)
            verdict = m_verdict.group(1)
            if agent not in verdicts:
                verdicts[agent] = verdict
                
    return verdicts


def pending_reviewer_clis(pr_number: int) -> list[str]:
    """The subset of REQUIRED_REVIEWER_CLIS that haven't reviewed the latest commit."""
    verdicts = reviewer_verdicts(pr_number)
    return [c for c in REQUIRED_REVIEWER_CLIS if c not in verdicts]


def pick_reviewer_cli(pr_number: int) -> str | None:
    """Pick one of the pending reviewers to run next.
    
    Prioritizes:
    1. Pending reviewers that are NOT currently rate-limited.
    2. Load balance tiebreak (fewest total reviews in history).
    Returns None if no reviewers are pending for the current commit.
    """
    pending = pending_reviewer_clis(pr_number)
    if not pending:
        return None
        
    armed = [c for c in pending if not quota.is_blocked(c)[0]]
    if not armed:
        # If all are blocked, pick the one soonest to reset so orchestrator 
        # can log the wait.
        return min(pending, key=lambda c: quota.is_blocked(c)[1] or float("inf"))
    
    if len(armed) == 1:
        return armed[0]
        
    # Tiebreak: pick the one with the fewest total reviews in DB history.
    def total_reviews(cli: str) -> int:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM events WHERE phase='review' AND action='finish' AND agent=?",
                (cli,)
            ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()
            
    return min(armed, key=total_reviews)


def reviewer_persona_name(cli: str) -> str:
    return {"codex": "reviewer-codex", "gemini": "reviewer-gemini"}[cli]


# ---- arbiter ----------------------------------------------------------------


def pick_arbiter_cli(pr_number: int) -> str | None:
    """Choose the cli to arbitrate a stuck PR.

    Selection order, most discriminating first:
      1. Pick the agent that *has reviewed fewer rounds* of this PR — they
         have less invested in their position and can serve as a fresher
         perspective.
      2. Tie-break with quota: prefer whichever is currently armed. Calling
         a blocked cli would just gate the phase and leave the PR stuck.
      3. If all else is equal, alternate based on PR number parity so the
         loop doesn't keep landing on the same cli for tied cases.

    Regex anchors to the `*Round N/M · reviewer: <cli>` trailer so prose
    mentions of "reviewer:" inside a review body can't influence the count.
    """
    pr = gh.get_pr(pr_number)
    posts = gh.marker_posts(pr)

    counts = {c: 0 for c in REVIEWER_CLIS}
    for post in posts:
        m = re.search(r"\*Round\s+\d+/\d+\s*·\s*reviewer:\s*(\w+)", post["body"])
        if m and m.group(1) in counts:
            counts[m.group(1)] += 1

    # Step 1: candidates with the minimum review count on this PR.
    min_count = min(counts.values())
    candidates = [c for c, n in counts.items() if n == min_count]
    if len(candidates) == 1:
        return candidates[0]

    # Step 2: quota tie-break — prefer armed clis.
    armed = [c for c in candidates if not quota.is_blocked(c)[0]]
    if len(armed) == 1:
        return armed[0]
    if not armed:
        # Both blocked: return whichever resets sooner.
        return min(candidates, key=lambda c: quota.is_blocked(c)[1] or float("inf"))

    # Step 3: deterministic alternation by PR parity.
    return armed[pr_number % len(armed)]


def arbiter_persona_name(cli: str) -> str:
    return {"codex": "arbiter-codex", "gemini": "arbiter-gemini"}[cli]
