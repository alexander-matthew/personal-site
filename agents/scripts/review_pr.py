"""Reviewer phase: Codex reads a PR diff and posts a structured review.

Codex runs read-only inside a worktree checked out at the PR's head. Its
final agent message is parsed by the strict marker format described in
agents/prompts/review.md. Whatever Codex says, the wrapper enforces:
  - PRs touching protected paths are forced to REQUEST_CHANGES.
  - PRs over the diff cap are forced to REQUEST_CHANGES.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import agent_run, db, gh, git_worktree, kill_switch, protected  # noqa: E402
from lib.config import (  # noqa: E402
    LABEL_NEEDS_HUMAN, LABEL_PROTECTED_VIOLATION, LABEL_TOO_LARGE,
    MAX_DIFF_LOC, MAX_REVIEW_ROUNDS, TIMEOUT_REVIEW_MIN,
)
from lib.paths import PROMPTS_DIR  # noqa: E402


# ---- structured-output parsing --------------------------------------------


_MARKER_VERDICT = re.compile(r"^##VERDICT:\s*(APPROVE|REQUEST_CHANGES|COMMENT)\s*$", re.M)
_MARKER_SUMMARY = re.compile(r"^##SUMMARY:\s*(.+)$", re.M)
_MARKER_CHECKLIST = re.compile(r"^##CHECKLIST:\s*\n(.*?)(?=^##|\Z)", re.M | re.S)
_MARKER_NOTES = re.compile(r"^##NOTES:\s*\n(.*?)\Z", re.M | re.S)


def _parse_review(text: str) -> dict | None:
    v = _MARKER_VERDICT.search(text)
    s = _MARKER_SUMMARY.search(text)
    c = _MARKER_CHECKLIST.search(text)
    n = _MARKER_NOTES.search(text)
    if not (v and s and c):
        return None
    return {
        "verdict": v.group(1),
        "summary": s.group(1).strip(),
        "checklist": c.group(1).strip(),
        "notes": n.group(1).strip() if n else "",
    }


# ---- round counting -------------------------------------------------------


def _round_number(pr_number: int) -> int:
    """How many Codex reviews are already on this PR (1-indexed for the next one)."""
    pr = gh.get_pr(pr_number)
    reviews = pr.get("reviews") or []
    codex_reviews = [r for r in reviews
                     if (r.get("author") or {}).get("login", "").lower().startswith("alexander")]
    # Codex posts via the user's gh auth, so reviews show up as the user.
    # We disambiguate by the structured marker in the body.
    codex_reviews = [r for r in codex_reviews if "##VERDICT:" in (r.get("body") or "")]
    return len(codex_reviews) + 1


def _needs_review(pr: dict) -> bool:
    """True if PR has no Codex review since its last commit."""
    if pr.get("isDraft"):
        return False
    reviews = [r for r in (pr.get("reviews") or [])
               if "##VERDICT:" in (r.get("body") or "")]
    if not reviews:
        return True
    last_review = reviews[-1]
    last_review_ts = last_review.get("submittedAt") or ""
    commits = pr.get("commits") or []
    if not commits:
        return False
    last_commit_ts = commits[-1].get("committedDate") or ""
    return last_commit_ts > last_review_ts


# ---- main -----------------------------------------------------------------


def _build_prompt(pr: dict, issue_body: str) -> str:
    template = (PROMPTS_DIR / "review.md").read_text()
    return (template
            .replace("{PR_NUMBER}", str(pr["number"]))
            .replace("{PR_TITLE}", pr["title"])
            .replace("{ISSUE_NUMBER}", str(_extract_issue_ref(pr.get("body") or "")))
            .replace("{ADDITIONS}", str(pr.get("additions", 0)))
            .replace("{DELETIONS}", str(pr.get("deletions", 0)))
            .replace("{CHANGED_FILES}", str(pr.get("changedFiles", 0)))
            .replace("{PR_BODY}", pr.get("body") or "")
            .replace("{ISSUE_BODY}", issue_body))


def _extract_issue_ref(pr_body: str) -> int | None:
    m = re.search(r"Closes\s+#(\d+)", pr_body)
    return int(m.group(1)) if m else None


def review(pr_number: int) -> int:
    """Returns 0 on success, 1 on skip, 2 on failure."""
    kill_switch.check(reason="review_pr start")

    pr = gh.get_pr(pr_number)
    if not _needs_review(pr):
        db.append(phase="review", action="skip", pr_number=pr_number,
                  outcome="already_current")
        return 1

    round_n = _round_number(pr_number)
    if round_n > MAX_REVIEW_ROUNDS:
        gh.add_label(kind="pr", number=pr_number, label=LABEL_NEEDS_HUMAN)
        db.append(phase="review", action="finish", pr_number=pr_number,
                  outcome="escalated_max_rounds",
                  notes={"rounds": round_n})
        return 1

    # Hard pre-checks the wrapper enforces regardless of Codex's opinion.
    adds = pr.get("additions", 0)
    dels = pr.get("deletions", 0)
    too_large = (adds + dels) > MAX_DIFF_LOC
    changed = [f.get("path") for f in (pr.get("files") or [])]
    bad_paths = protected.violations([p for p in changed if p])

    started = time.time()
    db.append(phase="review", action="start", agent="codex",
              pr_number=pr_number, notes={"round": round_n})

    # Build worktree at the PR head for Codex to inspect.
    branch = pr.get("headRefName", "")
    worktree: Path | None = None
    try:
        worktree = git_worktree.create(f"review-{pr_number}-r{round_n}", base="origin/main")
        # Bring the PR branch in for Codex's context.
        import subprocess
        subprocess.run(["git", "fetch", "origin", f"{branch}:{branch}", "--force"],
                       cwd=worktree, check=True, capture_output=True)
        subprocess.run(["git", "checkout", branch],
                       cwd=worktree, check=True, capture_output=True)

        issue_number = _extract_issue_ref(pr.get("body") or "")
        issue_body = ""
        if issue_number:
            try:
                issue_body = (gh.get_issue(issue_number) or {}).get("body", "") or ""
            except Exception:
                pass

        prompt = _build_prompt(pr, issue_body)
        proc, final_msg = agent_run.run_codex(
            prompt=prompt,
            cwd=worktree,
            timeout_min=TIMEOUT_REVIEW_MIN,
            sandbox="read-only",
        )

        parsed = _parse_review(final_msg)
        # If structured parse failed, fall back to a comment so the run isn't wasted.
        if not parsed:
            gh.comment(
                kind="pr", number=pr_number,
                body=("⚠️ Reviewer agent produced unparseable output. Raw last message:\n\n"
                      f"```\n{final_msg[:3000]}\n```"),
            )
            db.append(phase="review", action="error", agent="codex",
                      pr_number=pr_number, duration_s=time.time() - started,
                      outcome="parse_failed",
                      notes={"stdout_tail": proc.stdout[-500:]})
            return 2

        # Wrapper-enforced overrides (Codex cannot approve if these fail).
        enforced_verdict = parsed["verdict"]
        if bad_paths or too_large:
            enforced_verdict = "REQUEST_CHANGES"
            extra = []
            if bad_paths:
                extra.append("**Protected-path violations** (wrapper-enforced):\n"
                             + "\n".join(f"- `{p}`" for p in bad_paths))
                gh.add_label(kind="pr", number=pr_number, label=LABEL_PROTECTED_VIOLATION)
            if too_large:
                extra.append(f"**Diff exceeds {MAX_DIFF_LOC} LOC** (+{adds}/-{dels}, wrapper-enforced).")
                gh.add_label(kind="pr", number=pr_number, label=LABEL_TOO_LARGE)
            parsed["checklist"] = "\n".join(extra) + "\n\n" + parsed["checklist"]

        # Construct the review body — keep the markers so we can detect/count later.
        review_body = (
            f"##VERDICT: {enforced_verdict}\n"
            f"##SUMMARY: {parsed['summary']}\n"
            f"##CHECKLIST:\n{parsed['checklist']}\n"
            f"##NOTES:\n{parsed['notes']}\n"
            f"\n---\n*Round {round_n}/{MAX_REVIEW_ROUNDS} · reviewer: codex · {time.strftime('%Y-%m-%d %H:%M')}*"
        )

        verdict_to_flag = {
            "APPROVE": "approve",
            "REQUEST_CHANGES": "request-changes",
            "COMMENT": "comment",
        }
        gh.review(pr_number=pr_number,
                  verdict=verdict_to_flag[enforced_verdict],
                  body=review_body)

        db.append(phase="review", action="finish", agent="codex",
                  pr_number=pr_number, duration_s=time.time() - started,
                  outcome=enforced_verdict.lower(),
                  notes={"round": round_n,
                         "model_verdict": parsed["verdict"],
                         "enforced_verdict": enforced_verdict,
                         "protected_violations": bad_paths,
                         "too_large": too_large})
        return 0

    except kill_switch.HaltRequested as e:
        db.append(phase="review", action="halted", agent="codex",
                  pr_number=pr_number, notes={"reason": str(e)})
        return 2
    except Exception as e:
        db.append(phase="review", action="error", agent="codex",
                  pr_number=pr_number, duration_s=time.time() - started,
                  notes={"error": repr(e)})
        return 2
    finally:
        if worktree is not None:
            git_worktree.cleanup(worktree)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: review_pr.py <pr_number>", file=sys.stderr)
        sys.exit(2)
    sys.exit(review(int(sys.argv[1])))
