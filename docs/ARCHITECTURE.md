# Architecture Reference

> Personal-Site — A FastAPI application styled as a Windows 98 desktop environment.
> This document describes the system architecture and design decisions.

---

## Table of Contents

- [System Overview](#system-overview)
- [Application Lifecycle](#application-lifecycle)
- [Routing & Routers](#routing--routers)
- [Template Architecture](#template-architecture)
- [Static Assets](#static-assets)
- [Services Layer](#services-layer)
- [Authentication](#authentication)
- [Data Flows](#data-flows)
- [Frontend Architecture](#frontend-architecture)
- [Error Handling](#error-handling)
- [Legacy Systems](#legacy-systems)
- [Deployment](#deployment)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│  ┌───────────────────┐  ┌────────────────┐                     │
│  │ Win98 UI (CSS/JS) │  │ Spotify Player │                     │
│  │ Desktop, Taskbar, │  │ (Web Playback  │                     │
│  │ Start Menu, Icons │  │  SDK)          │                     │
│  └────────┬──────────┘  └───────┬────────┘                     │
│           │ fetch                │ fetch                        │
└───────────┼──────────────────────┼──────────────────────────────┘
            │                      │
┌───────────┼──────────────────────┼──────────────────────────────┐
│  EC2 (Docker Compose)            │                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  nginx (reverse proxy, HTTPS termination, Let's Encrypt)  │  │
│  └────────┬──────────────────────┬───────────────────────────┘  │
│  ┌────────▼──────────────────────▼────────────────────────────┐ │
│  │  FastAPI (uvicorn, --proxy-headers)                         │ │
│  │  ┌─────────────────────────────────────────────────────────┤ │
│  │  │  Routers (10 registered)                                │ │
│  │  │  main │ blog │ news │ spotify │ blackjack │ sudoku │ .. │ │
│  │  ├─────────────────────────────────────────────────────────┤ │
│  │  │  Services                                               │ │
│  │  │  ┌──────────┐  ┌───────────┐  ┌──────────────┐         │ │
│  │  │  │ Cache    │  │ OAuth     │  │ Rate Limiter │         │ │
│  │  │  │ (file)   │  │ (Spotify) │  │ (in-memory)  │         │ │
│  │  │  └────┬─────┘  └─────┬─────┘  └──────────────┘         │ │
│  │  ├───────┼───────────────┼─────────────────────────────────┤ │
│  │  │  Shared HTTP Client (httpx.AsyncClient)                 │ │
│  │  └───────┼───────────────┼─────────────────────────────────┘ │
│  │          │               │                                    │
│  └──────────┼───────────────┼────────────────────────────────────┘
│             │               │
│      ┌──────▼──────┐        │
│      │ /tmp cache  │        │
│      │ (JSON files)│        │
│      └─────────────┘        │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                        ┌─────▼──────────────┐
                        │ External APIs      │
                        │ - Spotify Web API  │
                        │ - Open-Meteo       │
                        └────────────────────┘
```

**Stack:** Python 3.11 / FastAPI / Uvicorn / Docker Compose / nginx / AWS EC2
**Frontend:** Vanilla JS, Spotify Web Playback SDK
**External APIs:** Spotify Web API (OAuth 2.0), Open-Meteo (public, no auth)

---

## Application Lifecycle

### Entry Point

**`main.py`** creates the app via the factory and runs the dev server.

```
main.py  →  create_app()  →  FastAPI instance
                ├── Lifespan: create/close shared httpx.AsyncClient
                ├── SECRET_KEY from env (required in production, raises RuntimeError if missing)
                ├── Security headers middleware (CSP, X-Frame-Options, HSTS in production)
                ├── Session middleware (1 week max_age, lax same_site, https_only in production)
                ├── Template globals: injects SITE_CONFIG as {{ site }}
                ├── Error handlers: 404, 500
                └── Router registration (10 routers, in order)
```

### App Factory: `app/__init__.py`

The factory (`create_app()`) performs these steps:

1. Creates FastAPI instance with lifespan context manager
2. Lifespan startup: creates shared `httpx.AsyncClient` on `app.state.http_client`
3. Lifespan shutdown: closes HTTP client to release connections
4. Adds security headers middleware (CSP, X-Frame-Options, Referrer-Policy, HSTS)
5. Adds session middleware (1 week max_age)
6. Validates `SECRET_KEY` (required in production, raises RuntimeError if missing)
7. Registers Jinja globals (`site`, custom `url_for`) for all templates
8. Registers error handlers for 404 and 500
9. Registers all 10 routers with their URL prefixes

### SITE_CONFIG

Global site metadata available in every template as `{{ site }}`:

| Key | Value | Template Usage |
|-----|-------|----------------|
| `name` | `'Alexander'` | `{{ site.name }}` |
| `linkedin_url` | LinkedIn profile URL | `{{ site.linkedin_url }}` |
| `github_url` | GitHub profile URL | `{{ site.github_url }}` |
| `email` | Email address | `{{ site.email }}` |

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SECRET_KEY` | Production | `'dev-key-for-local-only'` | Starlette session signing |
| `FLASK_DEBUG` | No | `'true'` | Debug mode toggle |
| `PORT` | No | `5005` | Server port |
| `SPOTIFY_CLIENT_ID` | For Spotify | — | Spotify OAuth client ID |
| `SPOTIFY_CLIENT_SECRET` | For Spotify | — | Spotify OAuth client secret |

---

## Routing & Routers

### Registration Order

| # | Router | Prefix | File |
|---|-----------|--------|------|
| 1 | `main` | — | `app/routes/main.py` |
| 2 | `blog` | `/blog` | `app/routes/blog.py` |
| 3 | `news` | `/news` | `app/routes/news.py` |
| 4 | `spotify` | `/projects/spotify` | `app/routes/spotify.py` |
| 5 | `blackjack` | `/projects/blackjack` | `app/routes/blackjack.py` |
| 6 | `pr_review` | `/projects/pr-review` | `app/routes/pr_review.py` |
| 7 | `sudoku` | `/projects/sudoku` | `app/routes/sudoku.py` |
| 8 | `weather` | `/projects/weather` | `app/routes/weather.py` |
| 9 | `resume` | `/resume` | `app/routes/resume.py` |
| 10 | `tools` | `/tools` | `app/routes/tools/__init__.py` |

### Complete Route Map

#### Static Content Routes

| Route | Method | Router | Description |
|-------|--------|-----------|-------------|
| `/` | GET | main | Desktop home page |
| `/about` | GET | main | System Properties window |
| `/projects` | GET | main | Project explorer grid |
| `/blog/` | GET | blog | Blog post listing |
| `/blog/<slug>` | GET | blog | Individual blog post |
| `/news/` | GET | news | News/press listing |
| `/resume/` | GET | resume | Resume timeline |
| `/projects/blackjack/` | GET | blackjack | Blackjack game |
| `/projects/sudoku/` | GET | sudoku | Sudoku game |
| `/projects/pr-review/` | GET | pr_review | PR Review showcase |

#### Spotify Routes

**Page & Auth:**

| Route | Method | Description |
|-------|--------|-------------|
| `/projects/spotify/` | GET | Dashboard page |
| `/projects/spotify/auth` | GET | Initiates OAuth redirect |
| `/projects/spotify/callback` | GET | OAuth callback handler |
| `/projects/spotify/logout` | GET | Clears session tokens |

**Data APIs (GET, require auth):**

| Route | Description |
|-------|-------------|
| `/projects/spotify/api/recent` | Last 50 played tracks |
| `/projects/spotify/api/top/<time_range>` | Top artists/tracks (`short_term`, `medium_term`, `long_term`) |
| `/projects/spotify/api/genres` | Genre breakdown from top artists |
| `/projects/spotify/api/taste-evolution` | Artist comparison across time ranges |
| `/projects/spotify/api/token` | Access token for Web Playback SDK |
| `/projects/spotify/api/playback-state` | Current playback state |
| `/projects/spotify/api/devices` | Available playback devices |

**Playback Control APIs (POST, require auth):**

| Route | Description |
|-------|-------------|
| `/projects/spotify/api/create-playlist` | Create private playlist from top tracks |
| `/projects/spotify/api/transfer` | Transfer playback to device |
| `/projects/spotify/api/play` | Start/resume playback |
| `/projects/spotify/api/pause` | Pause playback |
| `/projects/spotify/api/next` | Skip forward |
| `/projects/spotify/api/previous` | Skip backward |
| `/projects/spotify/api/seek` | Seek to position |
| `/projects/spotify/api/volume` | Set volume level |
| `/projects/spotify/api/shuffle` | Toggle shuffle |
| `/projects/spotify/api/repeat` | Set repeat mode |

#### Weather Routes

**Page:**

| Route | Method | Description |
|-------|--------|-------------|
| `/projects/weather/` | GET | Weather dashboard |

**APIs (GET, no auth):**

| Route | Cache TTL | Description |
|-------|-----------|-------------|
| `/projects/weather/api/geocode?city=` | 24 hours | City search / geocoding |
| `/projects/weather/api/current?lat=&lon=` | 10 min | Current conditions |
| `/projects/weather/api/forecast?lat=&lon=` | 30 min | 7-day forecast |
| `/projects/weather/api/extremes/<horizon>` | 30min–6h | Extreme weather (horizons: `today`, `tomorrow`, `3day`, `7day`, `season`, `year`) |
| `/projects/weather/api/industry/<region>` | None | Industry impact data |

---

## Template Architecture

The project uses **two independent template inheritance chains**. The Win98 chain is the active UI; the modern dark chain is retained by legacy code.

### Chain 1: Win98 Theme (Active)

```
win98_base.html
├── home.html (desktop with icons, extends directly)
│
└── win98_window.html (adds window chrome)
    ├── about.html
    ├── projects.html
    ├── blog/index.html
    ├── blog/post.html
    ├── news/index.html
    ├── resume/index.html
    ├── spotify/index.html
    ├── blackjack/index.html
    ├── sudoku/index.html
    ├── weather/index.html
    └── pr_review/index.html
```

**`win98_base.html`** provides:
- Desktop area (`{% block main %}`)
- Start Menu with full site navigation
- Taskbar with Start button, task button area, system tray clock
- Loads `win98.css` and `win98.js`

**`win98_window.html`** adds:
- Fullscreen window overlay with title bar (icon + gradient blue + min/max/close buttons)
- Menu bar slot (`{% block menu_bar %}`)
- Scrollable content area (`{% block window_content %}`)
- Status bar (`{% block status_bar %}`)
- Taskbar button with icon and title

**Template Blocks (Win98 chain):**

| Block | Defined In | Purpose |
|-------|-----------|---------|
| `title` | win98_base | `<title>` tag |
| `head` | win98_base | Extra CSS/meta in `<head>` |
| `body` | win98_base | Entire body content |
| `main` | win98_base | Desktop area |
| `taskbar_buttons` | win98_base | Taskbar button area |
| `scripts` | win98_base | Page-specific JS |
| `window_title` | win98_window | Title bar text |
| `menu_bar` | win98_window | Menu bar row |
| `window_content` | win98_window | Main content |
| `status_bar` | win98_window | Status bar row |
| `taskbar_title` | win98_window | Taskbar button text |

**Window Icon Convention:** Set `{% set window_icon = 'filename.svg' %}` at the top of child templates. Used in both title bar and taskbar button.

**Window Assignments:**

| Page | Window Title | Icon | Win98 Metaphor |
|------|-------------|------|----------------|
| About | System Properties | `computer.svg` | My Computer |
| Projects | C:\Projects | `folder.svg` | Explorer |
| Blog | C:\My Documents | `notepad.svg` | Notepad |
| Blog Post | [title] - Notepad | `notepad.svg` | Notepad |
| News | In the News - IE | `internet.svg` | Internet Explorer |
| Resume | Resume.doc - WordPad | `document.svg` | WordPad |
| Spotify | Spotify - WMP | `cd.svg` | Windows Media Player |
| Blackjack | Blackjack Trainer | `cards.svg` | Card game |
| Sudoku | Sudoku | `game.svg` | Puzzle game |
| Weather | Weather Channel | `weather.svg` | Weather app |
| PR Review | PR Review - Help | `pr-review.svg` | Help viewer |

### Chain 2: Modern Dark Theme (Legacy)

```
base.html
├── 500.html
└── tools/base_tool.html
    └── tools/spotify/index.html
```

Retained for the 500 error page and the legacy tools framework. Uses `style.css` and dark/light theme toggle.

### Standalone: 404 Page

`404.html` has no parent template. It renders a Windows BSOD (Blue Screen of Death) with inline CSS. Click or keypress navigates to `/`.

---

## Static Assets

### CSS

| File | Used By | Purpose |
|------|---------|---------|
| `css/win98.css` | win98_base.html | Complete Win98 design system |
| `css/style.css` | base.html (legacy) | Modern dark/light theme with CSS variables |
| `css/spotify.css` | (deprecated, unlinked) | Retained on disk but no longer loaded |
| `css/resume.css` | resume/index.html | Resume timeline styles |
| `css/blackjack.css` | blackjack/index.html | Blackjack game (supplemented by inline styles) |
| `css/sudoku.css` | sudoku/index.html | Sudoku grid (supplemented by inline styles) |
| `css/weather.css` | weather/index.html | Weather dashboard (supplemented by inline styles) |
| `css/tools.css` | tools/ templates | Tools framework grid/cards |

`win98.css` and `style.css` are mutually exclusive — they serve different template chains. Several app-specific CSS files are loaded but heavily supplemented by inline `<style>` blocks that provide Win98-themed overrides.

### JavaScript

| File | Type | Purpose |
|------|------|---------|
| `js/win98.js` | IIFE | Win98 interactivity: clock, start menu, desktop icons, tabs, window controls, dialog system |
| `js/spotify-ascii.js` | IIFE → `SpotifyASCII` | Win98 HTML component rendering (progress bars, tables, listviews) |
| `js/spotify-player.js` | IIFE → `SpotifyPlayer` | Spotify Web Playback SDK integration (player init, state, UI, device management) |
| `js/blackjack-engine.js` | Classic | Blackjack game logic, strategy charts, card shuffling |
| `js/sudoku-engine.js` | Classic | Sudoku puzzle generation, validation, solver |
| `js/weather-engine.js` | Classic | Weather utilities (WMO code mappings, formatting) |

**Test Files:** `blackjack-engine.test.js`, `sudoku-engine.test.js`, `weather-engine.test.js` (Jest)

**Template-Embedded JS:** `blackjack/game.js` (included in `blackjack/index.html`)

### Third-Party (CDN)

| Library | Version | Used In |
|---------|---------|---------|
| Chart.js | latest | `tools/spotify/index.html` (jsdelivr) |
| Font Awesome | 6.4.0 | `weather/index.html` (cdnjs) |
| Spotify Web Playback SDK | latest | `spotify-player.js` (dynamically loaded from sdk.scdn.co) |

### Icons

`static/icons/` contains 13 SVG files for the Win98 theme: `windows.svg`, `computer.svg`, `folder.svg`, `notepad.svg`, `document.svg`, `cd.svg`, `cards.svg`, `game.svg`, `weather.svg`, `newspaper.svg`, `internet.svg`, `recycle.svg`, `pr-review.svg`.

---

## Services Layer

### File-Based Cache (`app/services/cache.py`)

```
Class: SimpleCache
Location: /tmp/app_cache/
Format: JSON files keyed by MD5 hash
Interface:
  cache.get(key) → value | None
  cache.set(key, value, ttl_seconds=3600)

Decorator: @cached(ttl_seconds=3600, key_prefix='')
  Cache key: {prefix}:{func_name}:{args}:{kwargs}
```

**Note:** The weather router uses the shared `SimpleCache` instance via `cache.get()`/`cache.set()` calls with varying TTLs (10min for current, 30min for forecast, 30min–6h for extremes). The `@cached` decorator works with both sync and async functions (detects via `inspect.iscoroutinefunction`).

### OAuth Client (`app/services/oauth.py`)

```
OAuthClient (base)
  ├── get_auth_url(redirect_uri, state)
  ├── exchange_code(code, redirect_uri)    # Uses Basic auth header
  └── refresh_token(refresh_token)

SpotifyOAuth(OAuthClient)
  ├── Reads SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET from env
  ├── Scopes: user-read-recently-played, user-top-read,
  │           user-read-currently-playing, user-read-playback-state,
  │           user-modify-playback-state, streaming, playlist-modify-private
  └── is_configured property
```

**Note:** Both `spotify.py` and `tools/spotify.py` import helpers from `app/services/spotify_helpers.py` (shared `require_oauth`, `refresh_spotify_token`, `spotify_request`). The `SpotifyOAuth` class in `app/services/oauth.py` is the single OAuth implementation.

### Rate Limiter (`app/services/rate_limit.py`)

```
@rate_limit(max_requests=60, window_seconds=60)
  Key: {function_name}:{client_ip}
  Algorithm: Sliding window
  Storage: In-memory defaultdict (resets on restart)
  On limit: Returns 429 JSON
```

Used by all Spotify endpoints (auth, data, and playback control) and all Weather API endpoints.

---

## Authentication

### Spotify OAuth 2.0 (Active Implementation)

**File:** `app/routes/spotify.py` (uses shared helpers from `app/services/spotify_helpers.py`)

**Scopes:**
- `user-read-recently-played`
- `user-top-read`
- `user-read-currently-playing`
- `user-read-playback-state`
- `user-modify-playback-state`
- `streaming`
- `playlist-modify-private`

**Flow:**

```
User clicks "Connect"
  │
  ▼
/projects/spotify/auth
  │  Generates Spotify authorization URL
  │  Redirects to accounts.spotify.com/authorize
  │
  ▼
User authorizes on Spotify
  │
  ▼
/projects/spotify/callback?code=...
  │  Exchanges code for tokens (credentials in POST body)
  │  Stores access_token + refresh_token in Starlette session
  │  Redirects to dashboard
  │
  ▼
Dashboard loads, JS fetches /api/* endpoints
  │  Each endpoint checks session for access_token
  │  On 401 from Spotify: auto-refreshes token, retries once
  │
  ▼
/projects/spotify/logout
    Clears both tokens from session
```

**Guard:** `require_oauth()` function checks `session['spotify_access_token']`, returns 401 JSON if missing.

**Token Refresh:** `_refresh_spotify_token()` POSTs to token endpoint with `grant_type=refresh_token`, updates session.

**Session Keys:**
- `spotify_access_token`
- `spotify_refresh_token`

---

## Data Flows

### Spotify

```
Frontend (fetch)
  │
  ▼
/api/* endpoint
  │  @require_oauth checks session
  │
  ▼
_spotify_request(endpoint)
  │  GET/POST to api.spotify.com/v1{endpoint}
  │  Authorization: Bearer {access_token}
  │
  ├─ 200 → Return JSON to frontend
  │
  └─ 401 → _refresh_spotify_token()
            │  POST to accounts.spotify.com/api/token
            │  Update session
            └─ Retry original request once
```

**Web Playback SDK** runs separately:
1. `spotify-player.js` loads SDK from `sdk.scdn.co`
2. Fetches token from `/api/token`
3. Creates Spotify player instance in browser
4. Manages playback state, device transfer, volume
5. Dispatches `audioProfileChange` events

### Weather

```
Page Load
  │
  ├─ Try browser geolocation
  ├─ Fallback: localStorage('weather_last_city')
  └─ Default: New York
  │
  ▼
/api/current?lat=...&lon=...
  │  Check /tmp/weather_cache (TTL: 10min)
  │  On miss: GET api.open-meteo.com/v1/forecast
  │  Map WMO code → weather_theme + weather_text + weather_icon
  │  Return enriched JSON
  │
  ▼
/api/forecast?lat=...&lon=...
  │  Check cache (TTL: 30min)
  │  On miss: GET api.open-meteo.com
  │  Return 7-day forecast JSON
  │
  ▼
Frontend renders data
```

**City Search:**
```
User types (debounced 300ms)
  → /api/geocode?city=...
    → geocoding-api.open-meteo.com/v1/search
      → Up to 5 results
        → User selects → load weather → save to localStorage
```

---

## Frontend Architecture

### Win98 Design System (`win98.css`)

A dedicated CSS framework implementing the full Win98 visual language:

| Component | CSS Selector | Description |
|-----------|-------------|-------------|
| Desktop | `.win98-desktop` | Full viewport teal (#008080) background |
| 3D Borders | `.win98-outset` / `.win98-inset` / `.win98-etched` | Classic raised/sunken/etched borders |
| Desktop Icons | `.win98-icon` | Grid-laid icons with selection highlight |
| Taskbar | `.win98-taskbar` | Fixed bottom bar with 3D borders |
| Start Button | `.win98-start-btn` | Windows logo + "Start" text |
| Start Menu | `.win98-start-menu` | Popup with blue sidebar and nav items |
| Windows | `.win98-window` | Full window chrome with title bar gradient |
| Buttons | `.win98-btn` | 3D raised buttons with active press state |
| Form Controls | `.win98-input` / `.win98-select` | Inset-border inputs |
| Tabs | `.win98-tabs` | Raised tab buttons with active state trick |
| Scrollbars | `::-webkit-scrollbar` | Themed scrollbar styling |
| Dialogs | `.win98-dialog-overlay` | Modal windows with overlay |

**Color Variables:**

| Variable | Value | Usage |
|----------|-------|-------|
| `--win98-desktop` | `#008080` | Desktop background |
| `--win98-gray` | `#c0c0c0` | Window/panel backgrounds |
| `--win98-title-blue` | `#000080` | Title bar start color |
| `--win98-title-blue-end` | `#1084d0` | Title bar gradient end |
| `--win98-highlight` | `#000080` | Selection backgrounds |
| `--win98-highlight-text` | `#ffffff` | Selection text |
| `--win98-btn-face` | `#c0c0c0` | Button surface |
| `--win98-btn-highlight` | `#ffffff` | Button light edge |
| `--win98-btn-shadow` | `#808080` | Button shadow edge |
| `--win98-btn-dark` | `#000000` | Button dark edge |
| `--win98-font` | MS Sans Serif stack | System font |
| `--win98-font-size` | `11px` | Base font size |

### Win98 JavaScript (`win98.js`)

| Feature | Lines | Mechanism |
|---------|-------|-----------|
| Clock | 9-29 | Updates `.win98-clock` every 60s, 12-hour format |
| Start Menu | 31-60 | Toggle on click, close on outside click / Escape |
| Desktop Icons | 62-96 | Click to select, double-click to navigate |
| Tabs | 98-120 | Generic tab switching for `.win98-tabs` |
| Window Controls | 122-144 | Close/Minimize → navigate to `/`, Maximize is decorative |
| Dialog System | 146-229 | `win98Alert(msg, title)` and `win98Confirm(msg, title)` (Promise-based) |

### Client-Side State (localStorage)

| Key | Type | Purpose |
|-----|------|---------|
| `theme` | `'dark'` \| `'light'` | Dark/light mode preference (legacy, base.html only) |
| `weather_last_city` | JSON `{ lat, lon, name }` | Last searched weather city |
| `spotify_player_volume` | float (0-1) | Playback volume level |

---

## Error Handling

### Server-Side

**Global error handlers** (`app/__init__.py`):
- **404:** Renders standalone BSOD page (`404.html`)
- **500:** Renders error page via `base.html` chain (`500.html`)

**Blog:** Raises `HTTPException(status_code=404)` if post slug not found.

**Spotify API endpoints:**
- Missing auth → 401 JSON `{ error: 'Not authenticated' }`
- Spotify API failure → error JSON with original HTTP status code
- Token expiry → auto-refresh and retry (once)

**Weather API endpoints:**
- Missing/invalid parameters → 422 JSON (FastAPI Query validation)
- External API failure → 502 JSON (catches `httpx.HTTPError`)
- Individual location failures in extremes endpoint → silently skipped

### Client-Side

- All `fetch()` calls wrapped in try/catch
- Failed loads display "Failed to load data" in the container
- Errors logged to console
- Weather shows spinner during load, error icon on failure

---

## Legacy Systems

### Tools Framework (Legacy but Active)

**Files:** `app/routes/tools/__init__.py`, `app/routes/tools/spotify.py`, `app/templates/tools/`

An extensible mini-app system with a registry pattern. Predates the current router-per-app architecture.

```python
TOOLS_REGISTRY = []
register_tool({ id, name, description, icon, tags, requires_auth })
```

Routes mount at `/tools/*`. Uses the `base.html` chain, cyberpunk Spotify theme, Chart.js radar charts, and the shared OAuth/rate-limiter services.

**Status:** The tools router IS registered in `create_app()` and its routes are active at `/tools/`.

### Modern Dark Theme (Partially Active)

**Files:** `base.html`, `css/style.css`

The original theme with CSS custom properties and dark/light toggle. Still used by `500.html` and the legacy tools framework.

### Shared Spotify Helpers

Both Spotify route files (`app/routes/spotify.py` and `app/routes/tools/spotify.py`) import from `app/services/spotify_helpers.py`, which provides `require_oauth()`, `refresh_spotify_token()`, and `spotify_request()`. The `SpotifyOAuth` class lives in `app/services/oauth.py`.

---

## Deployment

### Platform

AWS EC2 (t3.micro, Amazon Linux 2023) with Docker Compose. Automatic deployment via GitHub Actions SSH on merge to `main`.

### Architecture

```
EC2 Instance
├── Docker Compose
│   ├── web       — Python app (Dockerfile: python:3.11-slim + uv)
│   ├── nginx     — Reverse proxy, HTTPS termination (nginx:1.27-alpine)
│   └── certbot   — Let's Encrypt certificate renewal
├── certbot/      — SSL certs (Let's Encrypt)
└── .env          — Environment variables (written by deploy.sh)
```

### Runtime

| File | Purpose |
|------|---------|
| `Dockerfile` | Builds app image: python:3.11-slim, uv sync, uvicorn with `--proxy-headers` |
| `docker-compose.yml` | Orchestrates web + nginx + certbot services |
| `nginx/default.conf.template` | HTTP→HTTPS redirect, reverse proxy to `web:8000` |

### Infrastructure (Terraform)

| File | Purpose |
|------|---------|
| `infra/main.tf` | EC2, security group (SSH/HTTP/HTTPS), elastic IP |
| `infra/variables.tf` | Domain, secrets, SSH key path, region, instance type |
| `infra/outputs.tf` | Elastic IP, SSH command, next steps |

### Deploy Pipeline

```
PR merged to main
  → GitHub Actions workflow triggers
    → SSH into EC2 (appleboy/ssh-action)
      → git pull origin main
      → docker compose up -d --build
```

### Initial Deploy

```bash
cd infra && terraform init && terraform apply   # Provision EC2
# Point DNS A record → Elastic IP
./deploy.sh                                      # Sync files, bootstrap HTTPS
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115.0 | Web framework |
| uvicorn | >=0.34.0 | ASGI server |
| httpx | >=0.28.0 | Async HTTP client |
| jinja2 | >=3.1.0 | Template engine |
| python-dotenv | >=1.0.0 | Environment variable loading |
| itsdangerous | >=2.2.0 | Session signing |
| pytest-playwright | >=0.5.0 | End-to-end browser testing (dev) |

### Testing

**JavaScript Tests:**
```bash
npm test              # Jest — blackjack, sudoku, weather engines
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

**Python Tests:**
```bash
uv sync --dev         # Install test deps (pytest, pytest-asyncio, respx)
uv run pytest -v      # Run all Python tests
```

Test coverage: `tests/test_cache.py`, `tests/test_oauth.py`, `tests/test_rate_limit.py`, `tests/test_routes.py`, `tests/test_spotify_helpers.py`, `tests/test_templating.py`

**End-to-End Tests (Playwright):**
```bash
uv run pytest e2e/ -v       # Run e2e tests (requires playwright browsers)
```

Test files: `e2e/conftest.py` (fixtures, server setup), `e2e/test_pages.py` (page smoke tests)
