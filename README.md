# Personal Site

A FastAPI personal website styled as a Windows 98 desktop, with interactive mini-apps and API-backed dashboards.

## Features

- Windows 98 desktop UI with taskbar/start menu metaphors
- Spotify dashboard with OAuth and playback controls
- Blackjack trainer, Sudoku, and Weather apps
- Blog, news, resume, and project pages

## Tech Stack

- Backend: Python 3.11, FastAPI, Uvicorn, Jinja2
- Frontend: HTML, CSS, Vanilla JavaScript
- Deployment: Docker Compose, nginx, Let's Encrypt, AWS EC2
- Testing: Pytest (Python), Jest (JavaScript game engines)

## Project Structure

```text
personal-site/
├── app/
│   ├── routes/          # FastAPI routers (main, blog, spotify, etc.)
│   ├── services/        # Cache, OAuth, rate limiting
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS, icons
├── tests/               # Python tests (pytest)
├── e2e/                 # End-to-end tests (Playwright)
├── docs/                # Architecture and deployment docs
├── infra/               # Terraform for EC2 infrastructure
├── scripts/             # Helper scripts
├── .github/workflows/   # CI/CD (deploy, agent-skill sync)
├── main.py              # Local app entry point
├── pyproject.toml       # Python dependencies (managed by uv)
├── Dockerfile
└── docker-compose.yml
```

## Local Development

```bash
git clone https://github.com/alexander-matthew/personal-site.git
cd personal-site

cp .env.example .env
uv sync --dev
uv run python main.py
```

App runs at `http://127.0.0.1:5005` by default.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Production | Session signing key |
| `FLASK_DEBUG` | No | Set `false` in production (controls local reload mode) |
| `PORT` | No | Local dev server port (default `5005`) |
| `SPOTIFY_CLIENT_ID` | Spotify features | Spotify OAuth client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify features | Spotify OAuth client secret |
| `DOMAIN` | Docker/nginx deploy | Public domain used by nginx/certbot |
| `LETSENCRYPT_EMAIL` | Docker/nginx deploy | Email for cert renewal notices |

## Testing

```bash
# Python (unit)
uv run pytest -v

# Python (end-to-end, requires playwright browsers)
uv run pytest e2e/ -v

# JavaScript
npm test
npm run test:watch
```

## Deployment

- Infrastructure: Terraform files in `infra/`
- Runtime: `docker-compose.yml` (`web`, `nginx`, `certbot`)
- App deploy script: `./deploy.sh`
- CI deploy: `.github/workflows/deploy.yml`

See `docs/ARCHITECTURE.md` and `docs/EC2_MIGRATION.md` for deployment details.
