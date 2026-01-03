from flask import Blueprint, render_template

bp = Blueprint('blackjack', __name__, url_prefix='/projects/blackjack')


@bp.route('/')
def index():
    """Blackjack training game with optimal play tracking."""
    return render_template('blackjack/index.html')
