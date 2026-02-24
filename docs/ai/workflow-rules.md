# Workflow Rules (Shared)

Repository workflow rules intended to work for both Claude and Codex.

## Branching

- Never commit directly to `main`.
- Use descriptive feature/fix branch names.
- Keep commits atomic and scoped.

## Pull Requests

- Open PRs only when requested.
- Do not merge without explicit instruction.

## Local Validation

Recommended checks before handoff:

```bash
uv run pytest -v
npm test
```

Verify local app behavior with:

```bash
uv run python main.py
```

## Parallel Agent Workflow

Use separate worktrees per agent session to minimize interference.

Example:

```bash
git worktree add ../personal-site-claude-task -b task/claude-task
git worktree add ../personal-site-codex-task -b task/codex-task
```

Notes:

- Do not use the same branch in two worktrees simultaneously.
- Keep each agent's changes isolated, then integrate via cherry-pick, rebase, or PR merge.
- Remove stale worktrees after integration:

```bash
git worktree remove ../personal-site-claude-task
git worktree remove ../personal-site-codex-task
```

## Agent/Skill Sync Check

Native definitions must exist in both locations:

- `.claude/agents/<name>.md`
- `skills/<name>/SKILL.md`

Run:

```bash
bash scripts/check_agent_skill_sync.sh
```

Or via npm:

```bash
npm run check:agent-sync
```

Install local pre-commit hook (one-time per clone):

```bash
npm run setup:hooks
```

CI also enforces parity on push/PR via `.github/workflows/agent-skill-sync.yml`.

## Deployment Workflow

- CI deployment triggers on push to `main`.
- Deploy implementation: `.github/workflows/deploy.yml`
- Manual/initial provisioning guidance: `docs/EC2_MIGRATION.md`
