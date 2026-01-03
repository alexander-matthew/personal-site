from flask import Blueprint, render_template

bp = Blueprint('sudoku', __name__, url_prefix='/projects/sudoku')


@bp.route('/')
def index():
    """Sudoku puzzle game with difficulty levels."""
    return render_template('sudoku/index.html')
