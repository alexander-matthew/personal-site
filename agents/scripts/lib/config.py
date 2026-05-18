"""Tunables for the agent loop. Kept centralized so behavior is one-file editable."""
from __future__ import annotations

# Off-hours window in CDT (24h). Worker refuses to run outside this.
OFF_HOURS_START = 23  # 11pm
OFF_HOURS_END = 6  # 6am

# Daemon polls GitHub state every TICK_SECONDS while it's up.
TICK_SECONDS = 60

# Per-phase timeouts live in the persona file (agents/personas/<name>.md).

# Max review rounds per PR before escalating to a human.
MAX_REVIEW_ROUNDS = 3

# Which agent CLIs must provide an APPROVE verdict before auto-merge.
REQUIRED_REVIEWER_CLIS = ("codex", "gemini")

# PRs larger than this many added+removed lines auto-fail review.
MAX_DIFF_LOC = 400

# Labels the loop owns. Source of truth; .github/labels.yml mirrors this.
LABEL_APPROVED = "agent:approved"
LABEL_IN_PROGRESS = "agent:in-progress"
LABEL_PROPOSAL = "agent:proposal"
LABEL_HALT = "agent:halt"
LABEL_VETO = "agent:veto"
LABEL_NEEDS_HUMAN = "agent:needs-human"
LABEL_PROTECTED_VIOLATION = "agent:protected-violation"
LABEL_TOO_LARGE = "agent:too-large"

# Files/dirs agents are not allowed to modify in PRs.
# A diff touching any of these triggers agent:protected-violation + blocks merge.
PROTECTED_PATHS = (
    ".github/workflows/",
    "infra/",
    "agents/scripts/",
    "agents/personas/",
    "agents/config.py",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.homelab.yml",
    "app/services/oauth.py",
)
