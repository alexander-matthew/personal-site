"""Three independent halt mechanisms. Any one engaged → halt requested."""
from __future__ import annotations

from .paths import STOP_PATH
from .config import LABEL_HALT
from . import gh


class HaltRequested(RuntimeError):
    """Raised when any kill switch is engaged. Catch at phase boundaries."""


def _stop_file_engaged() -> bool:
    return STOP_PATH.exists()


def _halt_label_engaged() -> bool:
    # The label is searched across open issues + PRs. Either kind halts.
    try:
        hits = gh.search(f"is:open label:{LABEL_HALT}")
        return bool(hits)
    except Exception:
        # Network blip shouldn't engage the kill switch by accident.
        return False


def check(*, reason: str = "phase boundary") -> None:
    """Raise HaltRequested if any kill switch is engaged. Called at phase boundaries."""
    if _stop_file_engaged():
        raise HaltRequested(f"STOP file present at {STOP_PATH} ({reason})")
    if _halt_label_engaged():
        raise HaltRequested(f"agent:halt label is set on an open issue/PR ({reason})")


def status() -> dict:
    """Returns which switches are currently engaged. Cheap, no exception."""
    return {
        "stop_file": _stop_file_engaged(),
        "halt_label": _halt_label_engaged(),
    }
