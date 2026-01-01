from flask import Blueprint, render_template

bp = Blueprint('news', __name__, url_prefix='/news')


# External articles/press mentions - ordered newest first
ARTICLES = [
    {
        'title': 'Sample Article About Me',
        'source': 'Tech Publication',
        'date': '2026-01-01',
        'url': 'https://example.com/article',
        'description': 'A brief description of what this article is about.'
    },
]


@bp.route('/')
def index():
    """In the News listing page."""
    return render_template('news/index.html', articles=ARTICLES)
