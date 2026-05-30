#!/usr/bin/env python3
"""Commit the day's diary files and push to main, attributed to a per-CLI bot.

Repurposes the triumvirate bot identities: instead of committing as the human
owner, the daily diary commit is authored by a GitHub App bot
(`claude-bot-...[bot]` by default). Identity + a short-lived push token come from
`agent_loop.lib.bots`.

Degrades safely: if `agent_loop`/PyJWT or the bot keys are unavailable, it falls
back to pushing with the host's existing git/`gh` auth and warns. Generation
never depends on this — see generate_entry.py.

Usage:
  uv run python scripts/deckard/commit_entry.py                  # commit+push as claude bot
  uv run python scripts/deckard/commit_entry.py --cli codex
  uv run python scripts/deckard/commit_entry.py --no-push        # commit only
  uv run python scripts/deckard/commit_entry.py --dry-run        # show, do nothing
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = os.environ.get('DECKARD_REPO', 'alexander-matthew/personal-site')
PATHS = ['app/content/deckard/entries', 'app/static/js/deckard/sketches']


def _git(*args: str, check: bool = True, capture: bool = False, env: dict | None = None):
    return subprocess.run(
        ['git', '-C', str(ROOT), *args],
        check=check, text=True, capture_output=capture,
        env=({**os.environ, **env} if env else None),
    )


def _has_staged_changes() -> bool:
    return _git('diff', '--cached', '--quiet', check=False).returncode != 0


def _import_bots():
    """Import agent_loop's bots module, tolerating layout/version differences.

    The pinned `agent_loop` install may predate the `bots` submodule; fall back
    to the triumvirate source checkout if present on the host.
    """
    import importlib

    for mod in ('agent_loop.lib.bots', 'agent_loop.bots'):
        try:
            return importlib.import_module(mod)
        except Exception:  # noqa: BLE001
            pass
    src = Path.home() / 'code' / 'triumvirate' / 'src'
    if (src / 'agent_loop' / 'lib' / 'bots.py').exists():
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
        try:
            return importlib.import_module('agent_loop.lib.bots')
        except Exception:  # noqa: BLE001
            return None
    return None


def _bot_ctx(cli: str):
    """Return (name, email, extraheader) for the bot, or None to use host auth.

    `extraheader` is an `http.extraheader` value carrying the installation token,
    exactly how triumvirate authenticates bot pushes.
    """
    bots = _import_bots()
    if bots is None:
        print('agent_loop bots module unavailable; using host git auth', file=sys.stderr)
        return None
    try:
        name = bots.bot_login(cli)
        email = bots.bot_email(cli)
        header = bots.http_extraheader(cli, repo=REPO)
        return name, email, header
    except Exception as e:  # noqa: BLE001
        print(f'bot identity/token unavailable ({e}); using host git auth', file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Commit + push the daily diary as a bot.')
    ap.add_argument('--cli', default=os.environ.get('DECKARD_CLI', 'claude'),
                    help='which bot identity to commit as (default: claude)')
    ap.add_argument('--no-push', action='store_true', help='commit but do not push')
    ap.add_argument('--dry-run', action='store_true', help='show actions, change nothing')
    args = ap.parse_args(argv)

    existing = [p for p in PATHS if (ROOT / p).exists()]
    _git('add', '--', *existing)
    if not _has_staged_changes():
        print('no new diary files to commit.')
        return 0

    date = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
    msg = f'diary: entry for {date}'
    ctx = _bot_ctx(args.cli)
    if ctx:
        name, email, header = ctx
    else:
        name, email, header = (f'{args.cli}-diary[bot]',
                               f'{args.cli}-diary@users.noreply.github.com', None)

    if args.dry_run:
        print(f'[dry-run] would commit as {name} <{email}>'
              f"{' (bot token)' if header else ' (host auth)'}: {msg!r}")
        _git('status', '--short')
        return 0

    _git('commit', '-m', msg, env={
        'GIT_AUTHOR_NAME': name, 'GIT_AUTHOR_EMAIL': email,
        'GIT_COMMITTER_NAME': name, 'GIT_COMMITTER_EMAIL': email,
    })
    print(f'committed as {name}')

    if args.no_push:
        return 0

    if header:
        push = _git('-c', f'http.extraheader={header}', 'push',
                    f'https://github.com/{REPO}.git', 'HEAD:main',
                    check=False, capture=True)
    else:
        push = _git('push', 'origin', 'HEAD:main', check=False, capture=True)
    if push.returncode != 0:
        print(f'push failed: {push.stderr.strip()}', file=sys.stderr)
        return 1
    print('pushed to main' + (' as bot' if header else ' (host auth)'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
