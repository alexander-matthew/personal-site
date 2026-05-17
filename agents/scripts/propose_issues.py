"""Proposer phase: Claude scans the repo + recent activity, files 1-3 proposals."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import agent_run, db, gh, git_worktree, kill_switch  # noqa: E402
from lib.config import LABEL_PROPOSAL, TIMEOUT_PROPOSE_MIN  # noqa: E402
from lib.paths import PROMPTS_DIR  # noqa: E402


_BLOCK = re.compile(
    r"##PROPOSAL\s*\n"
    r"##TITLE:\s*(?P<title>.+?)\s*\n"
    r"##LABELS:\s*(?P<labels>.+?)\s*\n"
    r"##BODY:\s*\n(?P<body>.*?)\n##END",
    re.S,
)


def _parse_proposals(text: str) -> list[dict]:
    out = []
    for m in _BLOCK.finditer(text):
        labels = [l.strip() for l in m.group("labels").split(",") if l.strip()]
        out.append({
            "title": m.group("title").strip(),
            "labels": labels,
            "body": m.group("body").strip(),
        })
    return out


def run() -> int:
    """Returns 0 on success (proposals filed), 1 on no-op, 2 on failure."""
    kill_switch.check(reason="propose_issues start")

    started = time.time()
    db.append(phase="propose", action="start", agent="claude")

    worktree: Path | None = None
    try:
        worktree = git_worktree.create(f"propose-{int(started)}", base="origin/main")
        prompt = (PROMPTS_DIR / "propose.md").read_text()
        proc = agent_run.run_claude(
            prompt=prompt,
            cwd=worktree,
            timeout_min=TIMEOUT_PROPOSE_MIN,
            max_turns=40,
        )
        duration = time.time() - started

        if proc.returncode != 0:
            db.append(phase="propose", action="error", agent="claude",
                      exit_code=proc.returncode, duration_s=duration,
                      notes={"stderr": proc.stderr[-1500:]})
            return 2

        proposals = _parse_proposals(proc.stdout)
        if not proposals:
            db.append(phase="propose", action="skip", agent="claude",
                      duration_s=duration, outcome="no_proposals",
                      notes={"stdout_tail": proc.stdout[-500:]})
            return 1

        filed = []
        for p in proposals[:3]:  # cap defense
            labels = [LABEL_PROPOSAL] + p["labels"]
            try:
                # gh issue create returns a URL ending in /issues/N
                from lib.gh import _run  # type: ignore
                out = _run([
                    "issue", "create",
                    "--title", p["title"],
                    "--body", p["body"],
                    *sum([["--label", l] for l in labels], []),
                ])
                num = int(out.strip().rsplit("/", 1)[-1])
                filed.append(num)
            except Exception as e:
                db.append(phase="propose", action="error", agent="claude",
                          notes={"error": repr(e), "title": p["title"]})

        db.append(phase="propose", action="finish", agent="claude",
                  duration_s=duration, outcome="filed",
                  notes={"issues": filed, "count": len(filed)})
        return 0 if filed else 1

    except kill_switch.HaltRequested as e:
        db.append(phase="propose", action="halted", agent="claude",
                  notes={"reason": str(e)})
        return 2
    except Exception as e:
        db.append(phase="propose", action="error", agent="claude",
                  duration_s=time.time() - started,
                  notes={"error": repr(e)})
        return 2
    finally:
        if worktree is not None:
            git_worktree.cleanup(worktree, delete_branch=True)


if __name__ == "__main__":
    sys.exit(run())
