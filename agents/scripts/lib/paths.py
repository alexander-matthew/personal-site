"""Single source of truth for paths the agent loop touches."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = REPO_ROOT / "agents"
SCRIPTS_DIR = AGENTS_DIR / "scripts"
PROMPTS_DIR = AGENTS_DIR / "prompts"

STATE_DIR = AGENTS_DIR / "state"
DB_PATH = STATE_DIR / "runs.sqlite"
LOCK_PATH = STATE_DIR / "loop.lock"
STOP_PATH = AGENTS_DIR / "STOP"
WORKTREES_DIR = STATE_DIR / "worktrees"


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    WORKTREES_DIR.mkdir(parents=True, exist_ok=True)
