# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Shared Context (Canonical)

This repository keeps cross-agent context in shared docs so Claude and Codex can follow the same project facts and workflow.
Update shared docs first, then this file only for Claude-specific overlays.

@docs/ai/project-context.md
@docs/ai/engineering-standards.md
@docs/ai/workflow-rules.md

## Project Overview

A FastAPI-based personal website deployed on AWS EC2 with Docker Compose + nginx + Let's Encrypt. Built to showcase personal projects and side interests (not professional work - see LinkedIn for that). Uses uvicorn (ASGI) for serving, httpx for async HTTP calls, and uv for dependency management.

## Project Structure

```
Personal-Site/
├── app/
│   ├── __init__.py          # FastAPI app factory + SITE_CONFIG
│   ├── templating.py        # Jinja2 setup with Flask-compatible url_for
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Main routes (home, about, projects)
│   │   ├── blog.py          # Blog routes
│   │   ├── news.py          # News/press routes
│   │   ├── spotify.py       # Spotify dashboard with OAuth
│   │   ├── blackjack.py     # Blackjack trainer game
│   │   ├── sudoku.py        # Sudoku puzzle game
│   │   ├── pr_review.py     # PR Review tool showcase
│   │   ├── resume.py        # Resume timeline
│   │   ├── weather.py       # Weather dashboard with Open-Meteo API
│   │   └── tools/           # Tools framework (extensible mini-apps)
│   ├── services/
│   │   ├── cache.py             # File-based caching with TTL
│   │   ├── oauth.py             # Async OAuth2 client (Spotify, httpx)
│   │   ├── rate_limit.py        # Rate limiting (FastAPI dependency)
│   │   └── spotify_helpers.py   # Shared Spotify helpers (require_oauth, spotify_request)
│   ├── templates/
│   │   ├── win98_base.html  # Win98 desktop base (primary template)
│   │   ├── win98_window.html # Win98 window chrome wrapper
│   │   ├── base.html        # Legacy base layout (used by 500.html, tools)
│   │   ├── 404.html         # BSOD-style 404 page (standalone)
│   │   ├── 500.html         # Error page (extends base.html)
│   │   ├── home.html        # Landing page (Win98 desktop with icons)
│   │   ├── about.html       # Bio with cycling interests animation
│   │   ├── projects.html    # Project showcase grid
│   │   ├── blog/            # Blog templates
│   │   ├── news/            # News templates
│   │   ├── resume/          # Resume timeline
│   │   ├── spotify/         # Spotify dashboard (Win98 theme)
│   │   ├── blackjack/       # Blackjack trainer UI + game.js
│   │   ├── sudoku/          # Sudoku game UI
│   │   ├── pr_review/       # PR Review showcase
│   │   ├── weather/         # Weather dashboard templates
│   │   └── tools/           # Tools framework templates
│   │       ├── index.html
│   │       ├── base_tool.html
│   │       ├── spotify/index.html
│   │       └── components/  # chart_container, data_card
│   └── static/
│       ├── favicon.svg
│       ├── css/
│       │   ├── win98.css           # Win98 design system (primary)
│       │   ├── style.css           # Legacy styles with CSS variables
│       │   ├── spotify.css         # Deprecated (unlinked, retained on disk)
│       │   ├── resume.css          # Resume timeline styles
│       │   ├── blackjack.css       # Blackjack game styles
│       │   ├── sudoku.css          # Sudoku grid styles
│       │   ├── weather.css         # Weather dashboard styles
│       │   └── tools.css           # Tools framework styles
│       ├── icons/                  # Win98 SVG icons (13 files)
│       └── js/
│           ├── win98.js                 # Win98 interactivity (clock, start menu, dialogs)
│           ├── spotify-ascii.js         # Spotify Win98 component rendering (progress bars, tables, listviews)
│           ├── spotify-player.js        # Spotify Web Playback SDK integration
│           ├── blackjack-engine.js      # Blackjack game logic + strategy
│           ├── blackjack-engine.test.js # Jest tests
│           ├── sudoku-engine.js         # Sudoku generation + validation
│           ├── sudoku-engine.test.js    # Jest tests
│           ├── weather-engine.js        # Weather utilities (WMO codes, formatting)
│           └── weather-engine.test.js   # Jest tests
├── .claude/
│   ├── agents/                  # Subagent definitions (5 agents)
│   └── CLAUDE.md                # This file
├── tests/                   # Python tests (pytest)
├── e2e/                     # End-to-end tests (Playwright)
│   ├── conftest.py
│   └── test_pages.py
├── docs/
│   ├── ARCHITECTURE.md      # Detailed architecture reference
│   ├── EC2_MIGRATION.md     # EC2 deployment migration guide
│   ├── ai/                  # Shared AI context (cross-agent)
│   │   ├── project-context.md
│   │   ├── engineering-standards.md
│   │   └── workflow-rules.md
│   └── plans/               # Archived implementation plans
├── scripts/
│   ├── check_agent_skill_sync.sh  # Verify agent/skill definitions stay in sync
│   └── install_git_hooks.sh       # Install .githooks/ into local repo
├── .githooks/
│   └── pre-commit           # Custom pre-commit hook
├── .github/
│   └── workflows/
│       ├── deploy.yml             # Auto-deploy on merge to main
│       └── agent-skill-sync.yml   # CI check for agent/skill sync
├── skills/                  # Claude Code skill definitions
├── AGENTS.md                # Codex/agent instructions
├── main.py                  # App entry point (uvicorn)
├── pyproject.toml           # Dependencies (managed by uv)
├── .python-version          # Python version pin
├── Dockerfile               # Python 3.11-slim + uv, runs uvicorn
├── docker-compose.yml       # web + nginx + certbot services
├── nginx/
│   └── default.conf.template  # nginx reverse proxy config
├── init-letsencrypt.sh      # Bootstrap Let's Encrypt certificates
├── deploy.sh                # Deploy to EC2 (reads Terraform outputs)
├── infra/
│   ├── main.tf              # EC2 + security group + elastic IP
│   ├── variables.tf         # Terraform variables
│   ├── outputs.tf           # Terraform outputs (IP, SSH command)
│   └── terraform.tfvars.example  # Template for tfvars
├── package.json             # Jest testing for JS engines
└── jest.config.js           # Jest configuration
```

## Key Patterns

### Global Site Config
All site-wide variables are in `SITE_CONFIG` dict in `app/__init__.py`:
```python
SITE_CONFIG = {
    'name': 'Alexander',
    'linkedin_url': '...',
    'github_url': '...',
    'email': '...',
}
```
Access in templates via `{{ site.name }}`, `{{ site.linkedin_url }}`, etc.

### Environment Variables
- `SECRET_KEY` - Session cookie signing secret (required in production; app will not start without it. Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`)
- `FLASK_DEBUG` - Set to `false` in production (defaults to `true` locally, controls uvicorn reload)
- `SPOTIFY_CLIENT_ID` - Spotify API client ID (for Spotify dashboard)
- `SPOTIFY_CLIENT_SECRET` - Spotify API client secret (for Spotify dashboard)
- `DOMAIN` - Domain name for the site (used by nginx and certbot)
- `LETSENCRYPT_EMAIL` - Email for Let's Encrypt certificate notifications

**Security:** App uses lifespan context manager with shared `httpx.AsyncClient` on `request.app.state.http_client`. Session max_age is 1 week. Content-Security-Policy header is added to all responses.

### Adding New Mini-Apps (Routers)
1. Create router in `app/routes/myapp.py`:
   ```python
   from fastapi import APIRouter, Request
   from app.templating import templates

   router = APIRouter(prefix='/myapp')

   @router.get('/', name='myapp.index')
   async def index(request: Request):
       return templates.TemplateResponse(request, 'myapp/index.html')
   ```

2. Register in `app/__init__.py`:
   ```python
   from app.routes import myapp
   app.include_router(myapp.router)
   ```

3. Add templates in `app/templates/myapp/`

4. Add nav link in `app/templates/win98_base.html` (Start Menu)

**Important:** Route names must follow `blueprint.endpoint` convention (e.g., `name='myapp.index'`) to match the custom `url_for()` in templates.

### Template System (Win98 — Primary)

The site uses a **Windows 98 desktop** theme as the primary UI. Two template chains exist:

**Chain 1: Win98 (active)** — `win98_base.html` → `win98_window.html` → page templates
- `win98_base.html`: Desktop area, Start Menu, Taskbar, loads `win98.css` + `win98.js`
- `win98_window.html`: Adds window chrome (title bar, menu bar, status bar)
- `home.html` extends `win98_base.html` directly (desktop with icons)
- All other pages extend `win98_window.html`

**Chain 2: Legacy** — `base.html` → `500.html`, `tools/` templates
- Retained for error pages and inactive tools framework
- Has dark/light toggle with CSS variables

**Win98 Template Blocks:**
- `{% block title %}` - Page title (win98_base)
- `{% block head %}` - Extra CSS/meta in `<head>` (win98_base)
- `{% block body %}` - Entire body content (win98_base)
- `{% block main %}` - Desktop area (win98_base)
- `{% block taskbar_buttons %}` - Taskbar button area (win98_base)
- `{% block scripts %}` - Page-specific JavaScript (win98_base)
- `{% block window_title %}` - Title bar text (win98_window)
- `{% block window_content %}` - Main content area (win98_window)
- `{% block menu_bar %}` - Menu bar row (win98_window)
- `{% block status_bar %}` - Status bar row (win98_window)
- `{% block taskbar_title %}` - Taskbar button text (win98_window)

**Window Icon Convention:** Set `{% set window_icon = 'filename.svg' %}` at the top of child templates.

### External Links
Always use `rel="noopener noreferrer"` with `target="_blank"` for security.

## Development

```bash
uv sync              # Install/update dependencies
uv run python main.py  # Start dev server with uvicorn
```
App runs at http://localhost:5005 with auto-reload.

**Note:** Port 5000 is reserved for another application on this machine. Override with `PORT=8080 uv run python main.py` if needed.

**Dependency management:** Use `uv add <package>` to add new dependencies. Docker uses `uv sync --frozen` directly from `pyproject.toml` and `uv.lock`.

### Parallel Development

When working on multiple features simultaneously, use one of these approaches to run isolated Claude Code sessions:

#### Option 1: Git Worktrees (Recommended)

Worktrees share the same `.git` directory, saving disk space and keeping branches in sync:

```bash
# Create a worktree for a new feature
git worktree add ../Personal-Site-feature-name -b feature/feature-name

# Set up the worktree
cd ../Personal-Site-feature-name
python -m venv .venv
source .venv/bin/activate
uv sync

# Run Claude in this worktree
claude
```

Manage worktrees:
```bash
git worktree list                                  # See all active worktrees
git worktree remove ../Personal-Site-feature-name  # Remove after PR merge
```

#### Option 2: Separate Clones

Use separate clones when you need full isolation (e.g., risky git experiments, same branch in multiple places):

```bash
# Clone to a new directory
git clone git@github.com:amatthew/Personal-Site.git ../Personal-Site-feature-name
cd ../Personal-Site-feature-name
git checkout -b feature/feature-name

# Set up the clone
python -m venv .venv
source .venv/bin/activate
uv sync

# Run Claude in this clone
claude
```

Note: Separate clones use more disk space and require independent fetch/pull operations.

#### Session Naming

Name your Claude sessions with `/rename feature-name` for easy resumption later (`claude --resume feature-name`).

### Pre-commit Hooks

For large tasks, use pre-commit hooks to ensure code quality before commits. Configure hooks in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreCommit": [
      {
        "command": "npm test",
        "description": "Run tests before commit"
      },
      {
        "command": "python -m pytest",
        "description": "Run Python tests"
      }
    ]
  }
}
```

Common pre-commit checks for this project:
- **Linting**: Run `flake8` or `ruff` on Python files
- **Tests**: Run `pytest` for backend, `npm test` for JavaScript
- **Type checking**: Run `mypy` if using type hints

Claude Code will automatically run these hooks before each commit, preventing broken code from being committed.

## Workflow

### Development Cycle

1. **Work & Commit Frequently**: Commit changes continuously as you work
2. **Test Locally**: Run `python main.py` and verify at http://localhost:5005
3. **Create PR on Command**: Only create a pull request when explicitly asked
4. **Deploy After Merge**: After PR is merged, GitHub Actions deploys to EC2

### Branches
- **Never commit directly to main** - always create a feature branch
- Create branches with descriptive names: `feature/add-widget`, `fix/login-bug`
- Commit early and often during development
- Each commit should be atomic and focused
- Push your branch: `git push -u origin branch-name`

### Pull Requests
- **Only create PRs when explicitly requested** by the user
- Do NOT merge PRs - only create them and provide the URL
- The owner will review and merge PRs manually

### Deployment
Deployment is automatic via GitHub Actions. When a PR is merged to main:
1. GitHub Actions triggers the deploy workflow
2. SSH into EC2, `git pull`, `docker compose up -d --build`

Manual deployment (if needed):
```bash
ssh -i ~/.ssh/id_rsa ec2-user@<ELASTIC_IP>
cd ~/personal-site
git pull origin main
docker compose up -d --build
```

### Local Testing
Always test locally before committing:
```bash
uv run python main.py  # Start dev server with uvicorn
# Visit http://localhost:5005
```

## EC2 / Infrastructure

### Initial Setup
```bash
cd infra && terraform init && terraform apply  # Provision EC2 + Elastic IP
# Point DNS A record to the Elastic IP
./deploy.sh                                     # Sync files, bootstrap HTTPS
```

### GitHub Actions Secrets
| Secret | Value |
|--------|-------|
| `EC2_HOST` | Elastic IP from `terraform output elastic_ip` |
| `EC2_USER` | `ec2-user` |
| `EC2_SSH_KEY` | Contents of your SSH private key |

### View Logs
```bash
ssh -i ~/.ssh/id_rsa ec2-user@<ELASTIC_IP>
cd ~/personal-site
docker compose logs -f web     # App logs
docker compose logs -f nginx   # nginx logs
```

## Pages

| Route | Template | Description |
|-------|----------|-------------|
| `/` | home.html | Landing with typing animation |
| `/about` | about.html | Bio with cycling interests |
| `/projects` | projects.html | Project showcase |
| `/blog` | blog/index.html | Blog posts |
| `/blog/{slug}` | blog/post.html | Individual blog post |
| `/news` | news/index.html | Press/news mentions |
| `/projects/spotify` | spotify/index.html | Spotify dashboard with OAuth |
| `/projects/blackjack` | blackjack/index.html | Blackjack trainer game |
| `/projects/sudoku` | sudoku/index.html | Sudoku puzzle game |
| `/projects/pr-review` | pr_review/index.html | PR Review tool showcase |
| `/resume` | resume/index.html | Resume timeline |
| `/projects/weather` | weather/index.html | Weather dashboard with ASCII animation |
| `/tools` | tools/index.html | Tools framework index |

## Mini-Apps

### Spotify Dashboard (`/projects/spotify`)
OAuth-authenticated data visualization with Win98 theme and Web Playback SDK:
- Recently played tracks (last 50)
- Top artists/tracks by time range (4 weeks, 6 months, all time)
- Genre breakdown with percentages
- Audio feature analysis (danceability, energy, valence, etc.)
- Taste evolution comparison
- In-browser playback with Spotify Web Playback SDK

**API Endpoints:** `/api/recent`, `/api/top/<time_range>`, `/api/genres`, `/api/taste-evolution`, `/api/create-playlist` (POST), `/api/token`, `/api/playback-state`, `/api/devices`, and playback control endpoints (`/api/play`, `/api/pause`, `/api/next`, etc.)

### Blackjack Trainer (`/projects/blackjack`)
Interactive game with basic strategy guidance:
- Real money simulation (starting balance: $1000)
- Optimal play feedback using strategy charts
- Hard, soft, and pair hand scenarios
- Visual card display with betting interface

### Sudoku Game (`/projects/sudoku`)
Puzzle game with three difficulty levels:
- Easy, Medium, Hard difficulty selection
- 9x9 grid with real-time validation
- Keyboard navigation support
- Win detection modal

### PR Review Tool (`/projects/pr-review`)
Documentation showcase for automated code review:
- Demonstrates `code_style.md` file system
- GitHub CLI integration examples
- Before/after refactoring examples

### Weather Dashboard (`/projects/weather`)
Real-time weather dashboard:
- Current conditions with temperature, humidity, wind, precipitation
- 7-day forecast with high/low temps and precipitation probability
- City search with autocomplete (Open-Meteo geocoding)
- Geolocation support for automatic location detection

**API Endpoints:** `/api/current`, `/api/forecast`, `/api/geocode`, `/api/extremes/<horizon>`, `/api/industry/<region>`

**Validation:** Uses FastAPI `Query()` with Pydantic validation (ge, le, min_length, max_length, Literal). Returns 422 for validation errors.

## Services

### Cache (`app/services/cache.py`)
File-based caching with TTL support. The `@cached` decorator works with both sync and async functions:
```python
from app.services.cache import cache, cached

# Sync decorator
@cached(ttl_seconds=300, key_prefix='spotify')
def get_spotify_data():
    ...

# Async decorator
@cached(ttl_seconds=600, key_prefix='weather')
async def fetch_weather():
    ...

# Or use instance directly
cached_val = cache.get(cache_key)
cache.set(cache_key, result, ttl_seconds=600)
```

### Rate Limiting (`app/services/rate_limit.py`)
In-memory rate limiting as FastAPI dependency. Store is bounded at 10,000 keys with periodic cleanup and LRU eviction:
```python
from fastapi import Depends
from app.services.rate_limit import rate_limit

@router.get('/api/data', dependencies=[Depends(rate_limit(30, 60))])
async def api_endpoint():
    ...
```

### OAuth (`app/services/oauth.py`)
Async OAuth2 client for external services (currently Spotify). Uses shared `httpx.AsyncClient` from `request.app.state.http_client`. Methods `exchange_code()` and `refresh_token()` require `http_client` keyword argument.

## Testing

Run Python tests:
```bash
uv sync --dev             # Install test deps (pytest, pytest-asyncio, respx)
uv run pytest -v          # Run all Python tests
```

Run JavaScript tests (game engines):
```bash
npm test                  # Run all tests
npm run test:watch        # Watch mode
npm run test:coverage     # Coverage report
```

## Features

- **Win98 Desktop UI**: Primary theme with desktop icons, Start Menu, taskbar, and window chrome
- **Dark/Light Mode**: Toggle in legacy base template only (used by 500 error page)
- **Typing animation**: Home page cycles "Alex" ↔ "Alexander"
- **Interests carousel**: About page fades through interests list
- **Responsive**: Mobile-friendly with breakpoint at 640px
- **Spotify dashboard**: Win98-styled data visualizations (progress bars, tables, listviews) and Web Playback SDK
- **Game engines**: Pure JavaScript with Jest test coverage
- **Security**: CSP headers, secure session cookies, required SECRET_KEY in production
