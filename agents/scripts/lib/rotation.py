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
    arb_posts = gh.marker_posts(pr, marker="##ARBITER_VERDICT:")
    latest_arb = None
    if arb_posts and arb_posts[-1]["ts"] > latest_commit_ts:
        m = re.search(r"##ARBITER_VERDICT:\s*(\S+)", arb_posts[-1]["body"])
        if m and m.group(1) == "APPROVE_FOR_MERGE":
            # Find which agent was NOT the arbiter — that's the one we're overriding.
            m_arb_agent = re.search(r"arbiter:\s*(\w+)", arb_posts[-1]["body"])
            if m_arb_agent:
                arb_agent = m_arb_agent.group(1)
                overridden_agent = "codex" if arb_agent == "gemini" else "gemini"
                verdicts[overridden_agent] = "APPROVE"

    for post in reversed(posts):
        if post["ts"] <= latest_commit_ts:
            break
        
        # Format: "*Round N/M · reviewer: <agent> · ...*"
        m_agent = re.search(r"reviewer:\s*(\w+)", post["body"])
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
    """The arbiter is the cli that has NOT been used to review this PR.

    Under consensus, multiple agents review. The arbiter is the one that has
    reviewed the FEWEST rounds on this PR (usually the one that wasn't the 
    bottleneck).
    """
    pr = gh.get_pr(pr_number)
    posts = gh.marker_posts(pr)
    
    counts = {"codex": 0, "gemini": 0}
    for post in posts:
        m = re.search(r"reviewer:\s*(\w+)", post["body"])
        if m:
            agent = m.group(1)
            if agent in counts:
                counts[agent] += 1
                
    # Pick the one with the fewest reviews.
    arbiter = min(counts, key=counts.get)
    return arbiter


def arbiter_persona_name(cli: str) -> str:
    return {"codex": "arbiter-codex", "gemini": "arbiter-gemini"}[cli]
