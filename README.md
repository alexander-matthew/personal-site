# Personal Site

A Flask-based personal website to showcase side projects and interests. Built for fun, not for work (see LinkedIn for that).

**Live Site:** [acm-personal-site.herokuapp.com](https://acm-personal-site.herokuapp.com)

## Features

### Mini-Apps

- **Spotify Dashboard** - OAuth-authenticated data visualization with a cyberpunk theme. View listening history, top artists, genre breakdowns, and audio feature analysis.

- **Blackjack Trainer** - Interactive game with basic strategy guidance. Learn optimal play with real-time feedback on your decisions.

- **Sudoku Game** - Puzzle game with Easy, Medium, and Hard difficulty levels. Features real-time validation and keyboard navigation.

- **PR Review Tool** - Documentation showcase for automated code review workflows.

### Site Features

- Typing animation on the home page
- Responsive design (mobile-friendly)
- Blog and news/press sections
- Dark theme with CSS variables

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Deployment:** Heroku
- **Testing:** Jest (JavaScript game engines)

## Project Structure

```
Personal-Site/
├── app/
│   ├── routes/          # Flask blueprints (main, blog, spotify, etc.)
│   ├── services/        # Cache, OAuth, rate limiting
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS and JavaScript
├── main.py              # App entry point
├── Procfile             # Heroku configuration
└── requirements.txt     # Python dependencies
```

## Local Development

```bash
# Clone the repo
git clone https://github.com/alexander-matthew/Personal-Site.git
cd Personal-Site

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

Visit [http://localhost:5000](http://localhost:5000)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret (required in production) |
| `FLASK_DEBUG` | Set to `false` in production |
| `SPOTIFY_CLIENT_ID` | Spotify API client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify API client secret |

## Testing

```bash
npm test          # Run JavaScript tests
npm run test:watch    # Watch mode
```

## License

This is a personal project. Feel free to use it as inspiration for your own site.
