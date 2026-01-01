from flask import Blueprint, render_template

bp = Blueprint('news', __name__, url_prefix='/news')


# External articles/press mentions - ordered newest first
ARTICLES = [
    {
        'title': "Men's Fencing Roster - Alex Matthew",
        'source': 'UNC Athletics',
        'date': '2019',
        'url': 'https://goheels.com/sports/fencing/roster/alex-matthew/16661',
        'description': "Senior sabre fencer and statistics major competing on UNC's men's fencing team."
    },
    {
        'title': 'Our Best & Brightest of 2016',
        'source': 'Gaston Gazette',
        'date': '2016-04-14',
        'url': 'https://www.gastongazette.com/story/news/2016/04/14/our-best-amp-brightest-of-2016/31973293007/',
        'description': 'Recognized among top students in Gaston County.'
    },
    {
        'title': 'Highland Tech Students Score Big',
        'source': 'Gaston Gazette',
        'date': '2015-08-06',
        'url': 'https://www.gastongazette.com/story/lifestyle/family/2015/08/06/highland-tech-students-score-big/33729848007/',
        'description': 'Highland School of Technology students recognized for achievements.'
    },
]


@bp.route('/')
def index():
    """In the News listing page."""
    return render_template('news/index.html', articles=ARTICLES)
