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
            'title': 'PCA & Lasso Explainer',
            'description': 'Visual walkthrough of dimensionality reduction and feature selection, exploring the relationship between PCA and Lasso regression.',
            'link': '/projects/pca-lasso',
            'tags': ['Machine Learning', 'Statistics', 'Education']
        },
    ]
    return render_template('projects.html', projects=sample_projects)
