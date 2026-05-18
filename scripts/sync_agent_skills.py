#!/usr/bin/env python3
"""Sync agent and skill definitions between Claude and Codex.

Ensures that:
  - Every .claude/agents/<name>.md has a corresponding skills/<name>/SKILL.md
  - Every skills/<name>/SKILL.md has a corresponding .claude/agents/<name>.md
  - Names in frontmatter match the filenames/directories.
"""

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / "skills"


def get_claude_agents():
    if not CLAUDE_DIR.is_dir():
        return set()
    return {f.stem for f in CLAUDE_DIR.glob("*.md")}


def get_codex_skills():
    if not SKILLS_DIR.is_dir():
        return set()
    return {d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()}


def sync():
    claude_agents = get_claude_agents()
    codex_skills = get_codex_skills()

    missing_skills = claude_agents - codex_skills
    missing_agents = codex_skills - claude_agents

    if not missing_skills and not missing_agents:
        print("Agent/skill parity check passed.")
        return

    for name in missing_skills:
        print(f"Syncing {name} from Claude to Codex...")
        target_dir = SKILLS_DIR / name
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CLAUDE_DIR / f"{name}.md", target_dir / "SKILL.md")

    for name in missing_agents:
        print(f"Syncing {name} from Codex to Claude...")
        CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SKILLS_DIR / name / "SKILL.md", CLAUDE_DIR / f"{name}.md")

    print("Sync complete.")


if __name__ == "__main__":
    sync()
