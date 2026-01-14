from flask import Blueprint, render_template

bp = Blueprint('generative', __name__, url_prefix='/projects/generative')


@bp.route('/')
def index():
    """Generative art gallery with live p5.js editor."""
    return render_template('generative/index.html')
