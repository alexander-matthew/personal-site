---
name: "document-maintainer"
description: "Keep project documentation accurate and lean after feature/refactor work. Use to update docs, remove stale content, and preserve high information density."
---

# Document Maintainer

Use this skill after significant code, architecture, or workflow changes.

## Scope

- May read any project files needed for verification.
- Should only edit Markdown documentation files.
- Prioritize `docs/ai/*`, then tool-specific overlays (`AGENTS.md`, `.claude/CLAUDE.md`) if needed.

## Workflow

1. Inspect code and diffs to understand what changed.
2. Validate current docs against source code and scripts.
3. Delete stale or inferable content first.
4. Update only non-obvious conventions, commands, and gotchas.
5. Keep docs concise, accurate, and cross-linked.

## Quality Bar

- Every statement should be actionable or decision-relevant.
- Prefer concise bullets/tables over long prose.
- Avoid repeating what is obvious from code structure.
