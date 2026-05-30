# GEMINI.md for Personal-Site

This file provides project-specific guidance for the Gemini CLI agent working on the personal website project.

## Project Structure & Commands

- **Install dependencies**: `uv sync`
- **Run dev server**: `uv run python main.py` (Default: http://localhost:5005)
- **Run Python tests**: `uv run pytest -v`
- **Run JS tests**: `npm test`
- **Deployment**: Automatic via GitHub Actions on push to `main`.

## Architectural Patterns

- **App Factory**: `app/__init__.py` contains `SITE_CONFIG`.
- **Theme**: Palantir-inspired dark theme. Uses `palantir_base.html` and `palantir_page.html`.
- **Mini-Apps**: Modular routers in `app/routes/` registered in the factory.
- **JS Engines**: Pure JavaScript logic in `static/js/` (e.g., `blackjack-engine.js`) with Jest coverage.

## Engineering Standards

- **Shared Context**: Canonical docs in `docs/ai/` take precedence.
- **Router Convention**: Follow `blueprint.endpoint` naming for `url_for` stability.
- **External Links**: Mandatory `rel="noopener noreferrer"` with `target="_blank"`.
- **Client Handling**: Use `request.app.state.http_client` for async outbound calls.

## Gemini Specifics

- **Consensus Workflow**: PRs require `APPROVE` from all required reviewers (Codex + Gemini).
- **Memory**: Use `MEMORY.md` in the project root (git-ignored) for private local notes.
- **Sub-Agents**: Use `invoke_agent` for batch refactors or high-volume data processing.
