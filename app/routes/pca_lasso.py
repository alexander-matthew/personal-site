"""
PCA & Lasso Visual Explainer
Interactive walkthrough of dimensionality reduction and regularization.
"""
from flask import Blueprint, render_template

bp = Blueprint('pca_lasso', __name__, url_prefix='/projects/pca-lasso')


@bp.route('/')
def index():
    """PCA & Lasso explainer main page."""
    return render_template('pca_lasso/index.html')
