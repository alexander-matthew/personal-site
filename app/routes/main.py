from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/projects')
def projects():
    sample_projects = [
        {
            'title': 'Spotify Dashboard',
            'description': 'Cyberpunk-themed visualization of my Spotify listening habits, featuring taste evolution, audio profiles, and listening patterns.',
            'link': '/projects/spotify',
            'tags': ['Python', 'Spotify API', 'Data Viz']
        },
        {
            'title': 'Blackjack Trainer',
            'description': 'Practice blackjack with real-time feedback on optimal play. Tracks your decisions vs basic strategy and helps you learn from mistakes.',
            'link': '/projects/blackjack',
            'tags': ['Game', 'Strategy', 'Interactive']
        },
        {
            'title': 'PR Review Tool',
            'description': 'A Claude Code skill for automating code review of firm-specific standards and style guidelines, saving senior developers hours of review time.',
            'link': '/projects/pr-review',
            'tags': ['Claude Code', 'AI', 'Developer Tools']
        },
        {
            'title': 'Sudoku',
            'description': 'Classic puzzle game with three difficulty levels. Features real-time validation, keyboard navigation, and guaranteed unique solutions.',
            'link': '/projects/sudoku',
            'tags': ['Game', 'Puzzle', 'Interactive']
        },
        {
            'title': 'Weather Dashboard',
            'description': 'Real-time global weather with animated themes. Track extreme weather patterns worldwide and see industry impact analysis.',
            'link': '/projects/weather',
            'tags': ['Weather', 'Data Viz', 'API']
        },
        {
            'title': 'Generative Art Gallery',
            'description': 'Interactive p5.js playground with live code editing. Explore and modify generative art sketches featuring particles, fractals, and procedural patterns.',
            'link': '/projects/generative',
            'tags': ['Creative Coding', 'p5.js', 'Interactive']
        },
    ]
    return render_template('projects.html', projects=sample_projects)
