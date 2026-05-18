# `agents/` — the autonomous engineering loop

This directory contains the **agent loop** that ships PRs against this repo
overnight. Subscription-driven (no Anthropic / OpenAI / Google API at runtime):
the `claude`, `codex`, and `gemini` CLIs are invoked headlessly on the homelab
host. The public-facing view is the `/lab` page on the site.

## The triumvirate

| Persona | Real-world analog | Permissions | CLI |
|---|---|---|---|
| **engineer** | Software engineer | write code in worktree, run tests, git commit | Claude (`bypassPermissions`) |
| **proposer** | Product manager (spec-driven) | read-only — files specs as issues, no code | Claude (Edit/Write disallowed) |
| **drift_watcher** | Staff IC, weekly housekeeping | read-only — wide-context audits, files cleanup issues | Claude (Edit/Write disallowed) |
| **reviewer** | Senior reviewer | read-only — critiques diff, can't push | **Codex or Gemini** (sticky per PR) |
| **arbiter** | Skip-level / staff IC | read-only — tiebreaks deadlocked PRs | **the other of Codex/Gemini** |
| **triage** | Triage PM | read-only — auto-approves low-risk specs | Gemini |
| **security** | AppSec | read-only — adversarial pre-merge pass on sensitive PRs | Gemini |

The engineer who wrote a feature is who builds it — `engineer` handles both
new work and review responses. The reviewer/arbiter pair always provides
three distinct perspectives on every PR that goes to arbitration: the
producer (Claude), the critic of record (Codex or Gemini), and the tiebreaker
(whichever of Codex/Gemini wasn't the critic).

## Pipeline

```
                  ┌──────────────┐
[approved issue]─▶│   engineer   │─▶ PR opens
                  │   (Claude)   │
                  └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   reviewer   │  ← Codex or Gemini, sticky per PR
                  │ (rotation)   │
                  └──────────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
           APPROVE   REQ_CHANGES  cap @ 3 rounds
              │          │          │
              ▼          ▼          ▼
        ┌─────────┐  engineer  ┌──────────┐
        │security │   (loop)   │  arbiter │  ← the OTHER cli
        │  scan   │            │          │
        └────┬────┘            └────┬─────┘
             │                      │
        CLEAR│FLAG     ┌────────────┼────────────┐
             │         │            │            │
             ▼         ▼            ▼            ▼
        merge-gate  approve     final_changes  human
                       │            │
                       ▼            └─▶ engineer (one last pass)
                   auto-merge              ▼
                                       arbiter again (max once more)
```

The orchestrator daemon runs **23:00–06:00 CDT** every night via
`personal-site-loop.timer`. A 60-second poll loop dispatches exactly one phase
per tick based on the state machine in `orchestrator.py:_dispatch()`.

## Phases

| Phase | Script | Persona (CLI) | What it does |
|---|---|---|---|
| propose | `propose_issues.py` | proposer (Claude) | Scans recent activity, files 1-3 `agent:proposal` issues |
| triage | `triage_proposals.py` | triage (Gemini) | Auto-approves low-risk proposals (type:content/polish/docs + effort:s); leaves others for human |
| work | `work_issue.py` | engineer (Claude) | Claims oldest `agent:approved` issue, implements in worktree, opens PR |
| review | `review_pr.py` | reviewer-codex OR reviewer-gemini | Reads PR diff in read-only sandbox, posts structured review |
| respond | `respond_to_review.py` | engineer (Claude) | Addresses reviewer's checklist, pushes follow-up commits |
| arbitrate | `arbitrate_pr.py` | arbiter-codex OR arbiter-gemini (whichever wasn't reviewer) | Tiebreaks stuck PRs after MAX_REVIEW_ROUNDS |
| security | `security_check.py` | security (Gemini) | Adversarial scan of PRs touching sensitive paths before merge |
| merge | `merge_gate.py` | (none) | Pure logic: APPROVE + CI green + no flags + diff clean → squash-merge |
| drift | `drift_watcher.py` | drift_watcher (Claude) | Weekly (Sundays) repo-wide audit; files cleanup `agent:proposal` issues |

Each phase logs `start` / `finish` / `error` / `skip` rows to
`agents/state/runs.sqlite` so the `/lab` page and `loop` CLI have a single
source of truth.

## Guard rails

The loop is **fully autonomous on merge** (no human in the loop), so guard
rails matter. Defense in depth:

1. **Protected paths.** Listed in `agents/scripts/lib/config.py:PROTECTED_PATHS`
   — `.github/workflows/`, `infra/`, `agents/scripts/`, `agents/personas/`,
   `Dockerfile`, `docker-compose*.yml`, `app/services/oauth.py`. Any touch:
   wrapper labels the PR `agent:protected-violation` AND `agent:needs-human`,
   merge gate refuses.
2. **Diff cap.** 400 lines added+removed. PRs over the cap are labeled
   `agent:too-large` and merge gate refuses.
3. **Round cap → arbiter.** Max 3 reviewer rounds per PR. Past that, the
   arbiter (the cli not used as reviewer) takes over. The arbiter can approve
   for merge, request one final pass, or escalate to `agent:needs-human` — but
   no fourth reviewer round happens.
4. **Security scan on sensitive PRs.** PRs touching `app/services/oauth.py`,
   middleware, auth, new endpoints, or new dependencies get an adversarial
   pre-merge pass from the `security` (Gemini) persona. FLAG verdict applies
   `agent:security-flag` + `agent:needs-human`.
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

## Threat model & guardrails (public repo)

The repo is internet-visible. Defenses, in order from "blocks the most
attackers" to "defense in depth":

1. **GitHub interaction limit set to `collaborators_only`.** Configured at the
   repo level and renewed monthly by
   `.github/workflows/renew-interaction-limit.yml`. Outside users can read
   the repo but cannot open issues, comment, or review PRs — so an attacker
   cannot land prompt-injection content in any artifact an agent reads.

2. **Trusted-author filter on marker posts.** `gh.marker_posts()` calls
   `trust.filter_trusted_marker_posts()` so that even if a future collaborator
   (or an automation bug) lets through a comment containing `##VERDICT:`,
   only posts authored by `TRUSTED_AUTHORS` are honored as real reviews.
   The orchestrator, merge-gate, and arbiter all flow through this filter.

3. **PR-eligibility gate.** Only PRs labeled `agent:authored-by-claude` are
   eligible for the loop. That label is applied by `work_issue.py` at the
   moment of `gh pr create` — there is no other path. Attackers can't apply
   labels (no write access), so attacker-opened PRs never enter the pipeline.

4. **Issue-eligibility gate.** Worker considers only issues with
   `agent:approved` AND authored by a trusted user. Both signals required.

5. **Untrusted-content wrappers in prompts.** When an agent's prompt
   includes prose that ultimately came from outside the loop (issue bodies,
   PR descriptions), the wrapper uses `trust.wrap_untrusted(...)` to mark
   the block as "data, not instructions to you" with an explicit preamble.
   Defense for the day GitHub's interaction limit accidentally lapses or
   when we add a new collaborator.

What we are **not** defending against:
- A trusted collaborator (you) intentionally injecting bad content.
- Compromise of the host running the agents (the agents can read `~/.ssh/`,
  `~/.config/gh/`, etc.; see CLAUDE.md's "Files that must NEVER be committed
  anywhere" section).

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
