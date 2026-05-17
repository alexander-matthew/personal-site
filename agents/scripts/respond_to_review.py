"""Responder phase: Claude addresses Codex's review checklist, pushes commits."""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import agent_run, db, gh, git_worktree, kill_switch, protected  # noqa: E402
from lib.config import (  # noqa: E402
    LABEL_NEEDS_HUMAN, LABEL_PROTECTED_VIOLATION, LABEL_TOO_LARGE,
    MAX_DIFF_LOC, MAX_REVIEW_ROUNDS, TIMEOUT_RESPOND_MIN,
)
from lib.paths import PROMPTS_DIR  # noqa: E402


def _latest_codex_review(pr: dict) -> dict | None:
    """The most recent review-or-comment carrying the structured marker."""
    posts = gh.marker_posts(pr)
    if not posts:
        return None
    p = posts[-1]
    # Keep the response shape stable for callers that read .get('body') and 'submittedAt'.
    return {"body": p["body"], "submittedAt": p["ts"]}


def _parse_review_body(body: str) -> dict:
    v = re.search(r"^##VERDICT:\s*(\S+)", body, re.M)
    s = re.search(r"^##SUMMARY:\s*(.+)$", body, re.M)
    c = re.search(r"^##CHECKLIST:\s*\n(.*?)(?=^##|\Z)", body, re.M | re.S)
    n = re.search(r"^##NOTES:\s*\n(.*?)(?=^---|\Z)", body, re.M | re.S)
    return {
        "verdict": v.group(1) if v else "",
        "summary": s.group(1).strip() if s else "",
        "checklist": c.group(1).strip() if c else "",
        "notes": n.group(1).strip() if n else "",
    }


def _round_number_from_body(body: str) -> int:
    m = re.search(r"Round (\d+)/\d+", body)
    return int(m.group(1)) if m else 1


def _build_prompt(pr: dict, review_parsed: dict, round_n: int) -> str:
    template = (PROMPTS_DIR / "respond.md").read_text()
    issue_ref = re.search(r"Closes\s+#(\d+)", pr.get("body") or "")
    return (template
            .replace("{PR_NUMBER}", str(pr["number"]))
            .replace("{PR_TITLE}", pr["title"])
            .replace("{ISSUE_NUMBER}", issue_ref.group(1) if issue_ref else "?")
            .replace("{REVIEW_SUMMARY}", review_parsed["summary"])
            .replace("{REVIEW_CHECKLIST}", review_parsed["checklist"])
            .replace("{REVIEW_NOTES}", review_parsed["notes"])
            .replace("{ROUND_NUMBER}", str(round_n)))


def respond(pr_number: int) -> int:
    """Returns 0 on success (commits pushed), 1 on no-op, 2 on failure."""
    kill_switch.check(reason="respond_to_review start")
    pr = gh.get_pr(pr_number)
    if pr.get("isDraft"):
        return 1
    latest_review = _latest_codex_review(pr)
    if not latest_review:
        return 1
    parsed = _parse_review_body(latest_review.get("body", ""))
    if parsed["verdict"] != "REQUEST_CHANGES":
        return 1

    # Don't respond if we've already pushed since this review.
    commits = pr.get("commits") or []
    if commits:
        last_commit_ts = commits[-1].get("committedDate") or ""
        review_ts = latest_review.get("submittedAt") or ""
        if last_commit_ts > review_ts:
            db.append(phase="respond", action="skip", pr_number=pr_number,
                      outcome="already_responded")
            return 1

    round_n = _round_number_from_body(latest_review.get("body", ""))
    if round_n >= MAX_REVIEW_ROUNDS:
        gh.add_label(kind="pr", number=pr_number, label=LABEL_NEEDS_HUMAN)
        db.append(phase="respond", action="finish", pr_number=pr_number,
                  outcome="escalated_max_rounds", notes={"round": round_n})
        return 1

    started = time.time()
    db.append(phase="respond", action="start", agent="claude",
              pr_number=pr_number, notes={"round": round_n})

    branch = pr.get("headRefName", "")
    worktree: Path | None = None
    try:
        worktree = git_worktree.create(f"respond-{pr_number}-r{round_n}", base="origin/main")
        subprocess.run(["git", "fetch", "origin", f"{branch}:{branch}", "--force"],
                       cwd=worktree, check=True, capture_output=True)
        subprocess.run(["git", "checkout", branch],
                       cwd=worktree, check=True, capture_output=True)

        prompt = _build_prompt(pr, parsed, round_n + 1)
        proc = agent_run.run_claude(
            prompt=prompt,
            cwd=worktree,
            timeout_min=TIMEOUT_RESPOND_MIN,
        )
        duration = time.time() - started

        # Did the agent add new commits beyond what was already on the branch?
        new_log = subprocess.run(
            ["git", "rev-list", "--count", f"origin/{branch}..HEAD"],
            cwd=worktree, capture_output=True, text=True,
        ).stdout.strip()
        added_commits = int(new_log or "0")

        if proc.returncode != 0 or added_commits == 0:
            db.append(phase="respond", action="error", agent="claude",
                      pr_number=pr_number, duration_s=duration,
                      exit_code=proc.returncode, outcome="no_commits",
                      notes={"stderr": proc.stderr[-1500:],
                             "stdout_tail": proc.stdout[-500:]})
            return 2

        # Re-check guardrails after the new commits.
        adds, dels = git_worktree.diff_stats(worktree)
        too_large = (adds + dels) > MAX_DIFF_LOC
        changed = git_worktree.changed_paths(worktree)
        bad_paths = protected.violations(changed)

        # Push.
        subprocess.run(["git", "push", "origin", branch],
                       cwd=worktree, check=True, capture_output=True)

        comment_lines = [
            f"Responded to round-{round_n} review.",
            f"Added {added_commits} commit(s). Diff now +{adds}/-{dels}.",
        ]
        if bad_paths:
            comment_lines += ["", "⚠️ Touched protected paths:",
                              *[f"- `{p}`" for p in bad_paths]]
            gh.add_label(kind="pr", number=pr_number, label=LABEL_PROTECTED_VIOLATION)
            gh.add_label(kind="pr", number=pr_number, label=LABEL_NEEDS_HUMAN)
        if too_large:
            comment_lines += ["", f"⚠️ Diff now exceeds {MAX_DIFF_LOC} LOC."]
            gh.add_label(kind="pr", number=pr_number, label=LABEL_TOO_LARGE)
        gh.comment(kind="pr", number=pr_number, body="\n".join(comment_lines))

        db.append(phase="respond", action="finish", agent="claude",
                  pr_number=pr_number, duration_s=duration,
                  outcome="commits_pushed",
                  notes={"added_commits": added_commits, "adds": adds, "dels": dels,
                         "protected_violations": bad_paths, "too_large": too_large,
                         "round": round_n + 1})
        return 0

    except kill_switch.HaltRequested as e:
        db.append(phase="respond", action="halted", agent="claude",
                  pr_number=pr_number, notes={"reason": str(e)})
        return 2
    except Exception as e:
        db.append(phase="respond", action="error", agent="claude",
                  pr_number=pr_number, duration_s=time.time() - started,
                  notes={"error": repr(e)})
        return 2
    finally:
        if worktree is not None:
            git_worktree.cleanup(worktree, delete_branch=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: respond_to_review.py <pr_number>", file=sys.stderr)
        sys.exit(2)
    sys.exit(respond(int(sys.argv[1])))
