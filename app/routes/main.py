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
    # Sample projects - replace with database or config file later
    sample_projects = [
        {
            'title': 'Project One',
            'description': 'A sample project description.',
            'link': '#',
            'tags': ['Python', 'Flask']
        },
        {
            'title': 'Project Two',
            'description': 'Another sample project.',
            'link': '#',
            'tags': ['JavaScript', 'API']
        }
    ]
    return render_template('projects.html', projects=sample_projects)
