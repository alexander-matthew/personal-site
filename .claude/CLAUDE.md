# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask-based personal website designed for Heroku deployment. Built to showcase personal projects and side interests (not professional work - see LinkedIn for that).

## Project Structure

```
Personal-Site/
├── app/
│   ├── __init__.py          # Flask app factory + SITE_CONFIG
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Main routes (home, about, projects)
│   │   ├── blog.py          # Blog routes
│   │   ├── news.py          # News/press routes
│   │   ├── spotify.py       # Spotify dashboard with OAuth
│   │   ├── blackjack.py     # Blackjack trainer game
│   │   ├── sudoku.py        # Sudoku puzzle game
│   │   ├── pr_review.py     # PR Review tool showcase
│   │   ├── weather.py       # Weather dashboard with Open-Meteo API
│   │   └── tools/           # Tools framework (extensible mini-apps)
│   ├── services/
│   │   ├── cache.py         # File-based caching with TTL
│   │   ├── oauth.py         # OAuth2 client (Spotify)
│   │   └── rate_limit.py    # In-memory rate limiting
│   ├── templates/
│   │   ├── base.html        # Base layout with nav + footer
│   │   ├── home.html        # Landing page with typing animation
│   │   ├── about.html       # Bio with cycling interests animation
│   │   ├── projects.html    # Project showcase grid
│   │   ├── blog/            # Blog templates
│   │   ├── news/            # News templates
│   │   ├── spotify/         # Spotify dashboard (cyberpunk theme)
│   │   ├── blackjack/       # Blackjack trainer UI
│   │   ├── sudoku/          # Sudoku game UI
│   │   ├── pr_review/       # PR Review showcase
│   │   ├── weather/         # Weather dashboard templates
│   │   └── tools/           # Tools framework templates
│   └── static/
│       ├── css/
│       │   ├── style.css           # Global styles with CSS variables
│       │   ├── spotify-cyberpunk.css  # Spotify retro-futuristic theme
│       │   ├── blackjack.css       # Blackjack game styles
│       │   ├── sudoku.css          # Sudoku grid styles
│       │   ├── weather.css         # Weather dashboard styles
│       │   └── tools.css           # Tools framework styles
│       └── js/
│           ├── ascii-background.js      # Three.js ASCII particle animation
│           ├── blackjack-engine.js      # Blackjack game logic + strategy
│           ├── blackjack-engine.test.js # Jest tests
│           ├── sudoku-engine.js         # Sudoku generation + validation
│           ├── sudoku-engine.test.js    # Jest tests
│           └── weather-engine.js        # Weather utilities (WMO codes, formatting)
├── .claude/
│   ├── agents/
│   │   └── ui-designer.md       # UI styling agent documentation
│   └── CLAUDE.md                # This file
├── main.py                  # App entry point
├── Procfile                 # Heroku: gunicorn main:app
├── runtime.txt              # Heroku: python-3.11.9
├── requirements.txt         # Flask + gunicorn + requests
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
- `SECRET_KEY` - Flask session secret (required in production)
- `FLASK_DEBUG` - Set to `false` in production (defaults to `true` locally)
- `SPOTIFY_CLIENT_ID` - Spotify API client ID (for Spotify dashboard)
- `SPOTIFY_CLIENT_SECRET` - Spotify API client secret (for Spotify dashboard)

### Adding New Mini-Apps (Blueprints)
1. Create blueprint in `app/routes/myapp.py`:
   ```python
   from flask import Blueprint, render_template
   bp = Blueprint('myapp', __name__, url_prefix='/myapp')

   @bp.route('/')
   def index():
       return render_template('myapp/index.html')
   ```

2. Register in `app/__init__.py`:
   ```python
   from app.routes import myapp
   app.register_blueprint(myapp.bp)
   ```

3. Add templates in `app/templates/myapp/`

4. Add nav link in `app/templates/base.html`

### Template Blocks
Base template provides these blocks:
- `{% block title %}` - Page title
- `{% block head %}` - Extra CSS/meta tags
- `{% block content %}` - Main page content
- `{% block scripts %}` - Page-specific JavaScript (after base scripts)

### Theme System

The site supports **dark mode** (default) and **light mode** with a toggle button in the navbar.

**Dark Mode** (`.home-dark` class on body):
- Black background (#0a0a0a) with animated Three.js ASCII particle cloud
- Light text (#e5e5e5 primary, #a3a3a3 secondary)
- Blue accent (#60a5fa) for links
- Semi-transparent card backgrounds

**Light Mode** (no class):
- White background, dark text
- ASCII animation hidden
- Standard light theme styling

Theme preference is stored in `localStorage` and persists across sessions. The toggle is automatic via `base.html` - no per-page configuration needed.

**CSS Variables** (defined in `:root`, overridden by `.home-dark`):
- `--primary-color`: Link/accent color
- `--text-color`: Main text
- `--text-light`: Secondary text
- `--bg-color`: Background
- `--bg-secondary`: Footer/card backgrounds
- `--border-color`: Borders

### External Links
Always use `rel="noopener noreferrer"` with `target="_blank"` for security.

## Development

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
App runs at http://localhost:5001 with auto-reload.

**Note:** Port 5000 is reserved for another application on this machine. This project uses port 5001 by default. Override with `PORT=8080 python main.py` if needed.

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
pip install -r requirements.txt

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
pip install -r requirements.txt

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
2. **Test Locally**: Run `python main.py` and verify at http://localhost:5001
3. **Create PR on Command**: Only create a pull request when explicitly asked
4. **Deploy After Merge**: After PR is merged, deploy to Heroku

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
2. Code is pushed to Heroku automatically
3. Heroku builds and deploys the app

Manual deployment (if needed):
```bash
git push heroku main
```

### Local Testing
Always test locally before committing:
```bash
source .venv/bin/activate
python main.py
# Visit http://localhost:5001
```

## Heroku Configuration

App: `mighty-shelf-14141`

Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secure-random-key
heroku config:set FLASK_DEBUG=false
heroku config:set SPOTIFY_CLIENT_ID=your-spotify-client-id
heroku config:set SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
```

Deploy manually:
```bash
git push heroku main
```

View logs:
```bash
heroku logs --tail
```

## Pages

| Route | Template | Description |
|-------|----------|-------------|
| `/` | home.html | Landing with typing animation |
| `/about` | about.html | Bio with cycling interests |
| `/projects` | projects.html | Project showcase |
| `/blog` | blog/index.html | Blog posts |
| `/news` | news/index.html | Press/news mentions |
| `/projects/spotify` | spotify/index.html | Spotify dashboard with OAuth |
| `/projects/blackjack` | blackjack/index.html | Blackjack trainer game |
| `/projects/sudoku` | sudoku/index.html | Sudoku puzzle game |
| `/projects/pr-review` | pr_review/index.html | PR Review tool showcase |
| `/projects/weather` | weather/index.html | Weather dashboard with ASCII animation |
| `/tools` | tools/index.html | Tools framework index |

## Mini-Apps

### Spotify Dashboard (`/projects/spotify`)
OAuth-authenticated data visualization with cyberpunk theme:
- Recently played tracks (last 50)
- Top artists/tracks by time range (4 weeks, 6 months, all time)
- Genre breakdown with percentages
- Audio feature analysis (danceability, energy, valence, etc.)
- Taste evolution comparison

**API Endpoints:** `/api/recent`, `/api/top/<time_range>`, `/api/genres`, `/api/audio-features`, `/api/taste-evolution`

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
Real-time weather with dynamic ASCII background animations:
- Current conditions with temperature, humidity, wind, precipitation
- 7-day forecast with high/low temps and precipitation probability
- City search with autocomplete (Open-Meteo geocoding)
- Geolocation support for automatic location detection
- Weather-reactive ASCII background with distinct motion patterns:
  - **Sunny**: Gentle upward heat shimmer
  - **Partly Cloudy**: Moderate billowing with drift
  - **Cloudy**: Large slow horizontal waves
  - **Rainy**: Fast downward streaks angled by wind
  - **Stormy**: Heavy rain with chaotic bursts
  - **Snowy**: Gentle swaying descent with wind drift
  - **Foggy**: Very slow, large particle drift

**API Endpoints:** `/api/current`, `/api/forecast`, `/api/geocode`

**Integration:** Dispatches `weatherchange` custom events that the ASCII background (`ascii-background.js`) listens for to update particle animation patterns in real-time.

## Services

### Cache (`app/services/cache.py`)
File-based caching with TTL support:
```python
from app.services.cache import cached

@cached(ttl_seconds=300, key_prefix='spotify')
def get_spotify_data():
    ...
```

### Rate Limiting (`app/services/rate_limit.py`)
In-memory rate limiting decorator:
```python
from app.services.rate_limit import rate_limit

@rate_limit(max_requests=30, window_seconds=60)
def api_endpoint():
    ...
```

### OAuth (`app/services/oauth.py`)
OAuth2 client for external services (currently Spotify).

## Testing

Run JavaScript tests (game engines):
```bash
npm test                  # Run all tests
npm run test:watch        # Watch mode
npm run test:coverage     # Coverage report
```

## Features

- **Dark/Light Mode**: Toggle in navbar, preference saved in localStorage
- **ASCII Background**: Three.js particle cloud rendered as ASCII characters (dark mode only), with weather-reactive animation patterns
- **Typing animation**: Home page cycles "Alex" ↔ "Alexander"
- **Interests carousel**: About page fades through interests list
- **Responsive**: Mobile-friendly with breakpoint at 640px
- **Footer**: GitHub/LinkedIn icons with Claude/Heroku credit
- **Cyberpunk theme**: Spotify dashboard with retro-futuristic styling
- **Game engines**: Pure JavaScript with Jest test coverage
