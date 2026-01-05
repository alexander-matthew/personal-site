from flask import Blueprint, render_template

bp = Blueprint('synth', __name__, url_prefix='/projects/synth')


@bp.route('/')
def index():
    """Web-based analog synthesizer with arpeggiator."""
    return render_template('synth/index.html')
