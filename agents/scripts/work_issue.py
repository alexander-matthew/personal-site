"""Worker phase: Claude implements one approved issue in a worktree, opens PR.

Called by the orchestrator (or `loop tick`) when the state machine sees an
`agent:approved` issue and no in-flight PR.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import agent_run, db, gh, git_worktree, kill_switch  # noqa: E402
from lib import protected  # noqa: E402
from lib.config import (  # noqa: E402
    LABEL_APPROVED, LABEL_IN_PROGRESS, LABEL_NEEDS_HUMAN,
    LABEL_PROTECTED_VIOLATION, LABEL_TOO_LARGE,
    MAX_DIFF_LOC, TIMEOUT_WORK_MIN,
)
from lib.paths import PROMPTS_DIR  # noqa: E402


def _slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
    return s[:48] or "issue"


def _pick_issue() -> dict | None:
    issues = gh.list_issues(labels=[LABEL_APPROVED], state="open", limit=20)
    # Skip any already in progress.
    fresh = [
        i for i in issues
        if not any(l["name"] == LABEL_IN_PROGRESS for l in i.get("labels", []))
    ]
    if not fresh:
        return None
    fresh.sort(key=lambda i: i["createdAt"])
    return fresh[0]


def _build_prompt(issue: dict) -> str:
    template = (PROMPTS_DIR / "work.md").read_text()
    return (template
            .replace("{ISSUE_NUMBER}", str(issue["number"]))
            .replace("{ISSUE_TITLE}", issue["title"])
            .replace("{ISSUE_BODY}", issue.get("body") or ""))


def run() -> int:
    """Returns 0 on success (PR opened), 1 on no-op, 2 on failure."""
    kill_switch.check(reason="work_issue start")

    issue = _pick_issue()
    if not issue:
        db.append(phase="work", action="skip", outcome="no_approved_issue")
        return 1

    n = issue["number"]
    title = issue["title"]
    branch = f"agent/{n}-{_slug(title)}"
    db.append(phase="work", action="start", agent="claude", issue_number=n,
              notes={"branch": branch, "title": title})

    gh.add_label(kind="issue", number=n, label=LABEL_IN_PROGRESS)
    started = time.time()
    worktree: Path | None = None
    try:
        worktree = git_worktree.create(branch, base="origin/main")
        prompt = _build_prompt(issue)

        proc = agent_run.run_claude(
            prompt=prompt,
            cwd=worktree,
            timeout_min=TIMEOUT_WORK_MIN,
        )
        duration = time.time() - started

        if proc.returncode != 0:
            db.append(phase="work", action="error", agent="claude",
                      issue_number=n, exit_code=proc.returncode,
                      duration_s=duration,
                      notes={"stderr": proc.stderr[-2000:]})
            gh.remove_label(kind="issue", number=n, label=LABEL_IN_PROGRESS)
            return 2

        # Did the agent actually commit anything?
        if not git_worktree.has_commits_since_base(worktree):
            db.append(phase="work", action="error", agent="claude",
                      issue_number=n, duration_s=duration,
                      outcome="no_commits",
                      notes={"stdout_tail": proc.stdout[-500:]})
            gh.remove_label(kind="issue", number=n, label=LABEL_IN_PROGRESS)
            return 2

        # Diff size check.
        adds, dels = git_worktree.diff_stats(worktree)
        too_large = (adds + dels) > MAX_DIFF_LOC

        # Protected-paths check.
        changed = git_worktree.changed_paths(worktree)
        bad_paths = protected.violations(changed)

        # Push regardless (the user can see what happened), but flag the PR.
        git_worktree.push(worktree, branch)

        body_lines = [
            f"Closes #{n}",
            "",
            "Authored by the agent loop (Claude worker).",
            "",
            f"Diff: +{adds}/-{dels} across {len(changed)} files.",
        ]
        if too_large:
            body_lines += ["", f"⚠️ Diff exceeds {MAX_DIFF_LOC} LOC. Auto-flagged for human review."]
        if bad_paths:
            body_lines += ["", "⚠️ Diff touches protected paths:", "",
                           *[f"- `{p}`" for p in bad_paths]]
        body = "\n".join(body_lines)

        labels = ["agent:authored-by-claude"]
        if too_large:
            labels.append(LABEL_TOO_LARGE)
        if bad_paths:
            labels.append(LABEL_PROTECTED_VIOLATION)
            labels.append(LABEL_NEEDS_HUMAN)

        pr_number = gh.create_pr(
            head=branch,
            base="main",
            title=title,
            body=body,
            labels=labels,
        )

        outcome = "opened"
        if bad_paths:
            outcome = "opened_protected_violation"
        elif too_large:
            outcome = "opened_too_large"

        db.append(phase="work", action="finish", agent="claude",
                  issue_number=n, pr_number=pr_number, outcome=outcome,
                  duration_s=duration,
                  notes={"adds": adds, "dels": dels,
                         "files": len(changed),
                         "protected_violations": bad_paths})
        return 0

    except kill_switch.HaltRequested as e:
        db.append(phase="work", action="halted", agent="claude",
                  issue_number=n, notes={"reason": str(e)})
        gh.remove_label(kind="issue", number=n, label=LABEL_IN_PROGRESS)
        return 2
    except Exception as e:
        db.append(phase="work", action="error", agent="claude",
                  issue_number=n, duration_s=time.time() - started,
                  notes={"error": repr(e)})
        gh.remove_label(kind="issue", number=n, label=LABEL_IN_PROGRESS)
        return 2
    finally:
        if worktree is not None:
            git_worktree.cleanup(worktree)


if __name__ == "__main__":
    sys.exit(run())
