from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter(prefix='/news')


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
        'description': 'Recognized by Gaston County as the top student at Highland School of Technology.'
    },
    {
        'title': 'Highland Tech Students Score Big',
        'source': 'Gaston Gazette',
        'date': '2015-08-06',
        'url': 'https://www.gastongazette.com/story/lifestyle/family/2015/08/06/highland-tech-students-score-big/33729848007/',
        'description': 'Placed 5th in the country in a stock market simulation game, achieving a 50% return in 14 weeks.'
    },
]


@router.get('/', name='news.index')
async def index(request: Request):
    """In the News listing page."""
    return templates.TemplateResponse(request, 'news/index.html', {'articles': ARTICLES})
