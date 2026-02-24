from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter(prefix='/resume')

TIMELINE = [
    {
        'type': 'work',
        'title': 'Manager, Investment Strategies',
        'org': 'NISA Investment Advisors, LLC',
        'location': 'St Louis, MO',
        'date': 'Dec 2024 - Present',
        'description': 'Institutional Derivatives Solutions with a focus on:',
        'highlights': [
            'Alpha Strategies',
            'Alternative Risk Premia',
            'Duration Overlay',
            'Tail Risk Hedging',
        ],
    },
    {
        'type': 'work',
        'title': 'Senior Analyst, Investment Strategies',
        'org': 'NISA Investment Advisors, LLC',
        'location': 'St Louis, MO',
        'date': 'Jan 2023 - Dec 2024',
    },
    {
        'type': 'work',
        'title': 'Analyst, Investment Strategies',
        'org': 'NISA Investment Advisors, LLC',
        'location': 'St Louis, MO',
        'date': 'Jun 2020 - Jan 2023',
    },
    {
        'type': 'work',
        'title': 'Intern, Investment Strategies',
        'org': 'NISA Investment Advisors, LLC',
        'date': 'Jun 2019 - Aug 2019',
    },
    {
        'type': 'work',
        'title': 'Financial Planning Intern',
        'org': 'Paschall & Associates',
        'location': 'Gastonia, NC',
        'date': 'May 2018 - Aug 2018',
    },
    {
        'type': 'work',
        'title': 'Process Improvement Intern',
        'org': 'Dixon Quick Coupling',
        'location': 'Dallas, NC',
        'date': 'Oct 2015 - Dec 2015',
    },
    {
        'type': 'education',
        'title': "Bachelor's Degree, Statistics",
        'org': 'The University of North Carolina at Chapel Hill',
        'date': '2016 - 2020',
        'highlights': [
            'Division I Fencing Team',
            'Sigma Nu Fraternity',
            'Richard A. Baddour Leadership Academy',
        ],
    },
    {
        'type': 'certification',
        'title': 'Chartered Financial Analyst (CFA)',
        'org': 'CFA Institute',
        'date': 'March 2023',
    },
    {
        'type': 'certification',
        'title': 'Series 3 - National Commodities Futures Exam',
        'org': 'FINRA',
        'date': 'February 2022',
    },
]


@router.get('/', name='resume.index')
async def index(request: Request):
    return templates.TemplateResponse(request, 'resume/index.html', {'timeline': TIMELINE})
