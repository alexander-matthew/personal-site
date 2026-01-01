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
│   │   └── news.py          # News/press routes
│   ├── templates/
│   │   ├── base.html        # Base layout with nav + footer
│   │   ├── home.html        # Landing page with typing animation
│   │   ├── about.html       # Bio with cycling interests animation
│   │   ├── projects.html    # Project showcase grid
│   │   ├── blog/            # Blog templates
│   │   └── news/            # News templates
│   └── static/
│       └── css/style.css    # Global styles with CSS variables
├── main.py                  # App entry point
├── Procfile                 # Heroku: gunicorn main:app
├── runtime.txt              # Heroku: python-3.11.9
└── requirements.txt         # Flask + gunicorn
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
- `{% block scripts %}` - JavaScript at end of body

### CSS Variables
Defined in `:root` in style.css:
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
App runs at http://localhost:5000 with auto-reload.

## Deployment

Set environment variables on Heroku:
```bash
heroku config:set SECRET_KEY=your-secure-random-key
heroku config:set FLASK_DEBUG=false
```

Deploy:
```bash
heroku create
git push heroku main
```

## Pages

| Route | Template | Description |
|-------|----------|-------------|
| `/` | home.html | Landing with typing animation |
| `/about` | about.html | Bio with cycling interests |
| `/projects` | projects.html | Project showcase |
| `/blog` | blog/index.html | Blog posts |
| `/news` | news/index.html | Press/news mentions |

## Features

- **Typing animation**: Home page cycles "Alex" ↔ "Alexander"
- **Interests carousel**: About page fades through interests list
- **Responsive**: Mobile-friendly with breakpoint at 640px
- **Footer**: Persistent with GitHub/LinkedIn links + Claude/Heroku credit
