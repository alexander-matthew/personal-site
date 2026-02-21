# Project Context (Shared)

Canonical, tool-agnostic repository context for AI assistants.

## Overview

Personal website built with FastAPI and server-rendered Jinja templates.
Primary interface is a Windows 98 desktop style UI.

## Core Stack

- Python 3.11
- FastAPI + uvicorn
- Jinja2 templating
- httpx for async external API calls
- uv for Python dependency management
- Docker Compose + nginx + certbot on EC2

## Key Directories

- `app/routes/`: FastAPI routers (`main`, `blog`, `news`, `spotify`, `blackjack`, `sudoku`, `weather`, `resume`, `pr_review`, `tools`)
- `app/services/`: cache, OAuth, rate limiting, Spotify helpers
- `app/templates/`: Win98 and legacy template chains
- `app/static/`: CSS, JavaScript, icons
- `tests/`: Python tests (pytest)
- `e2e/`: End-to-end tests (Playwright)
- `infra/`: Terraform for EC2 infrastructure
- `scripts/`: Helper scripts (agent/skill sync check, git hooks installer)
- `.githooks/`: Custom pre-commit hook
- `.github/workflows/`: CI/CD (deploy, agent-skill sync)
- `skills/`: Claude Code skill definitions
- `docs/`: architecture, deployment, and shared AI context docs
- `AGENTS.md`: Codex/agent instructions (root level)

## Template Architecture

- Active chain: `win98_base.html` -> `win98_window.html` -> most pages
- Home page extends `win98_base.html` directly
- Legacy chain: `base.html` still used by `500.html` and tools pages

## Runtime Notes

- Local dev entry point: `main.py`
- Default dev port: `5005` (`PORT` env var overrides)
- Production deployment uses Docker and runs behind nginx

## Environment Variables

- `SECRET_KEY` (required in production)
- `FLASK_DEBUG` (`true` locally, `false` in production)
- `PORT` (local dev server port override)
- `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`
- `DOMAIN` / `LETSENCRYPT_EMAIL` (deploy/runtime)
