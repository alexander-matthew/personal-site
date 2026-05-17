"""/lab — public-facing view of the agent loop's recent activity.

Reads from agents/state/runs.sqlite (gitignored, per-host) and the GitHub API
via the same `lib.gh` shim the daemon uses. Cheap server-side render; the page
is meant to be human-readable, not a real-time dashboard.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Request

from app.templating import templates


# Make agents/scripts/lib importable without installing it as a package.
_AGENT_SCRIPTS = Path(__file__).resolve().parents[2] / "agents" / "scripts"
if str(_AGENT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_AGENT_SCRIPTS))


router = APIRouter()


def _load_state() -> dict:
    """Best-effort load of loop state. Page degrades gracefully if anything is missing."""
    out: dict = {
        "events": [],
        "open_agent_prs": [],
        "approved_issues": [],
        "proposals": [],
        "halted": False,
        "summary": {},
        "error": None,
    }
    try:
        from lib import db, gh, kill_switch  # type: ignore
        from lib.config import LABEL_APPROVED, LABEL_PROPOSAL  # type: ignore
    except Exception as e:
        out["error"] = f"Agent lib not importable: {e!r}"
        return out

    try:
        out["events"] = db.recent(30)
    except Exception as e:
        out["error"] = f"runs.sqlite unreadable: {e!r}"

    try:
        out["summary"] = db.today_summary()
    except Exception:
        pass

    try:
        out["halted"] = any(kill_switch.status().values())
    except Exception:
        pass

    try:
        prs = gh.list_prs(state="open", limit=30)
        out["open_agent_prs"] = [
            p for p in prs
            if any(l["name"].startswith("agent:") for l in p.get("labels", []))
        ]
    except Exception:
        pass

    try:
        out["approved_issues"] = gh.list_issues(
            labels=[LABEL_APPROVED], state="open", limit=10,
        )
    except Exception:
        pass

    try:
        out["proposals"] = gh.list_issues(
            labels=[LABEL_PROPOSAL], state="open", limit=10,
        )
    except Exception:
        pass

    return out


@router.get("/lab", name="lab.index")
async def lab_index(request: Request):
    state = _load_state()
    return templates.TemplateResponse(
        request, "lab/index.html", {"state": state},
    )
