# `agents/` — the autonomous engineering loop

This directory contains the **agent loop** that ships PRs against this repo
overnight. Subscription-driven (no Anthropic / OpenAI API at runtime): the
`claude` and `codex` CLIs are invoked headlessly on the homelab host. The
public-facing view is the `/lab` page on the site.

## Pipeline

Claude is the sole **producer**. Codex is the sole **reviewer**. The dialog
continues until convergence or a guard rail trips.

```
[approved issue] ──▶ claude worker  ──▶ PR opens
                                          │
                                          ▼
                                     codex reviewer  ──▶ APPROVE? ──▶ merge-gate
                                          │                              │
                                          ▼                              ▼
                                  request-changes                    auto-merge
                                          │
                                          ▼
                                  claude responder ──▶ (loop back to reviewer, up to 3 rounds)
```

The orchestrator daemon runs **23:00–06:00 CDT** every night via
`personal-site-loop.timer`. Inside, a 60-second poll loop dispatches exactly
one phase per tick based on the state machine in `orchestrator.py:_dispatch()`.

## Phases

| Phase | Script | Agent | What it does |
|---|---|---|---|
| propose | `propose_issues.py` | Claude | Scans repo + recent git log, files 1-3 `agent:proposal` issues |
| work | `work_issue.py` | Claude | Claims oldest `agent:approved` issue, implements in worktree, opens PR |
| review | `review_pr.py` | Codex | Reads PR diff in read-only sandbox, posts structured review |
| respond | `respond_to_review.py` | Claude | Addresses Codex's checklist, pushes follow-up commits |
| merge | `merge_gate.py` | (none) | Pure logic: gates merge on approve + CI green + clean diff |

Each phase logs `start` / `finish` / `error` / `skip` rows to
`agents/state/runs.sqlite` so the `/lab` page and `loop` CLI have a single
source of truth.

## Guard rails

The loop is **fully autonomous on merge** (no human in the loop), so guard
rails matter. Defense in depth:

1. **Protected paths.** Listed in `agents/scripts/lib/config.py:PROTECTED_PATHS`
   — `.github/workflows/`, `infra/`, `agents/scripts/`, `agents/prompts/`,
   `Dockerfile`, `docker-compose*.yml`, `app/services/oauth.py`. Any touch:
   wrapper labels the PR `agent:protected-violation` AND `agent:needs-human`,
   merge gate refuses.
2. **Diff cap.** 400 lines added+removed. PRs over the cap are labeled
   `agent:too-large` and merge gate refuses.
3. **Round cap.** Max 3 review iterations per PR. Past that, label
   `agent:needs-human` is applied and the loop stops touching the PR.
4. **CI green required.** The merge gate evaluates GitHub's status-check
   rollup; anything not `SUCCESS` (or the moral equivalent) holds the merge.
5. **Filesystem isolation.** Each agent run gets a fresh `git worktree` under
   `agents/state/worktrees/`. Claude is invoked with no `--add-dir`, which
   confines its writes to the worktree even in `bypassPermissions` mode.
   Codex runs in `--sandbox read-only`.

## Kill switches — three of them, any one halts the loop

1. **`sudo systemctl stop personal-site-loop.service`** — kills the running
   daemon. cgroup-mode systemd propagates SIGTERM to in-flight agent
   subprocesses. Cleanup (worktree removal, label rollback) runs in `finally`
   blocks.
2. **`touch agents/STOP`** — checked at every phase boundary inside the
   process. Survives across nightly timer fires.
3. **`agent:halt` label** on any open issue or PR — orchestrator queries at
   the top of every tick.

The convenience entry point is `agents/scripts/loop halt`, which engages all
three at once. `agents/scripts/loop resume` reverses (1) and (2); the label
must be removed manually because it's per-issue.

Per-PR escape hatch: add `agent:veto` to a specific PR and the merge gate
will skip it without halting the rest of the loop.

## Observability

Three views, all reading the same `runs.sqlite`:

| View | How |
|---|---|
| Raw event stream | `journalctl -u personal-site-loop.service -f` |
| Terminal dashboard | `agents/scripts/loop status` |
| Public page | `https://<host>/lab` |

```sh
agents/scripts/loop status         # one-screen pipeline state
agents/scripts/loop journal -l 30  # last 30 sqlite events, pretty-printed
agents/scripts/loop list           # open loop-labeled issues + PRs
agents/scripts/loop tick           # force one state-machine step (testing)
agents/scripts/loop halt           # engage all kill switches
agents/scripts/loop resume         # reverse halt
```

## Adding work to the queue

```sh
# Manual issue, ready for the next nightly run:
gh issue create \
    --title "Add a /version endpoint returning git SHA + build time" \
    --body  "..." \
    --label "agent:approved" --label "type:feature" --label "effort:s"
```

The Issue template at `.github/ISSUE_TEMPLATE/agent-task.md` is the structured
form of this for human triage of proposals.

## File layout

```
agents/
  README.md                            (this file)
  scripts/
    loop                               # the CLI — status / tick / halt / resume / journal / list
    orchestrator.py                    # the daemon
    work_issue.py                      # phase: worker (Claude)
    review_pr.py                       # phase: reviewer (Codex)
    respond_to_review.py               # phase: responder (Claude)
    merge_gate.py                      # phase: merge (pure logic)
    propose_issues.py                  # phase: proposer (Claude)
    lib/
      agent_run.py                     # subprocess wrappers for claude / codex
      config.py                        # tunables: timeouts, caps, label names, protected paths
      db.py                            # sqlite event log
      gh.py                            # gh CLI wrappers
      git_worktree.py                  # worktree mgmt
      kill_switch.py                   # check() + status()
      paths.py                         # path constants
      protected.py                     # diff vs PROTECTED_PATHS
  prompts/
    work.md, review.md, respond.md, propose.md
  state/                               # gitignored, per-host
    runs.sqlite                        # event log
    loop.lock                          # flock for one-tick-at-a-time
    worktrees/                         # per-phase worktrees, force-removed after use
```

## Why this design

- **Subscription-only.** Both CLIs auth via the user's plan; the loop owns no
  API key material. The Anthropic SDK is not imported anywhere in the FastAPI
  app, only the CLI is invoked from out-of-band scripts.
- **Asymmetric agents.** Single producer + single critic is easier to reason
  about than round-robin. The dialog stays legible as a single conversation
  on the PR.
- **One process, one log, one kill point.** A daemon-of-one is much easier to
  introspect than a fleet of cron-fired jobs.
- **Polling, with a webhook upgrade path.** Today the daemon polls `gh` every
  60s. Once the Cloudflare Tunnel is live and the site has a public hostname,
  a `POST /webhook/github` endpoint becomes a drop-in replacement —
  near-instant instead of 60s, no other code changes needed.
