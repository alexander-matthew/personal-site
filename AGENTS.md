# AGENTS.md

Repository instructions for Codex and other coding agents.

## Intent

This repo supports a parallel Claude + Codex workflow with minimal duplication.
Canonical project facts and workflow guidance live in shared docs under `docs/ai/`.

## Canonical Shared Context

Read these first for repository context:

1. `docs/ai/project-context.md`
2. `docs/ai/engineering-standards.md`
3. `docs/ai/workflow-rules.md`

If any guidance conflicts with implementation details, code is source of truth.

## Project Snapshot

- Stack: FastAPI, Jinja2 templates, uvicorn, httpx, uv dependency management
- UI: Win98 theme (`win98_base.html`, `win98_window.html`) plus legacy `base.html`
- Deploy: AWS EC2, Docker Compose, nginx, certbot/Let's Encrypt
- Tests: `uv run pytest -v` and `npm test`

## Non-Negotiables

- Do not commit directly to `main`; use feature branches.
- Keep changes atomic and focused.
- Use `uv` for Python dependency and run commands.
- Route names should follow the established `router.endpoint` naming pattern used by templates.
- Keep docs accurate when changing architecture, deployment, or workflow.

## Documentation Sync Rule

When changing repo-level behavior, update docs in this order:

1. Shared docs in `docs/ai/*` (canonical)
2. Tool-specific overlays (`.claude/CLAUDE.md`, skill docs, etc.) only as needed

## Agent/Skill Parity

Claude agents and Codex skills are mirrored by name:

- Claude: `.claude/agents/<name>.md`
- Codex: `skills/<name>/SKILL.md`

Run parity check:

```bash
bash scripts/check_agent_skill_sync.sh
```

Install local git hook (one-time per clone):

```bash
npm run setup:hooks
```

## Deployment Pointers

- Runbook: `docs/EC2_MIGRATION.md`
- Architecture reference: `docs/ARCHITECTURE.md`
- Deploy script: `./deploy.sh`
- CI deploy workflow: `.github/workflows/deploy.yml`
