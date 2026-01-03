"""
PR Review Tool Showcase
Interactive demonstration of the Claude Code PR Review skill.
"""
from flask import Blueprint, render_template

bp = Blueprint('pr_review', __name__, url_prefix='/projects/pr-review')


@bp.route('/')
def index():
    """PR Review Tool showcase main page."""
    return render_template('pr_review/index.html')
