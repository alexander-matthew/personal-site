from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter(prefix='/resume')

# Timeline entries - fill in your actual experience!
# Each entry has: type, title, org, location (optional), date, description, skills (optional), highlights (optional)
TIMELINE = [
    {
        'type': 'work',
        'title': 'Software Engineer',
        'org': 'Your Current Company',
        'location': 'San Francisco, CA',
        'date': '2023 - Present',
        'description': 'Building products that matter. Replace this with what you actually do.',
        'skills': ['Python', 'Flask', 'AWS', 'React'],
        'highlights': [
            'Led development of key feature X',
            'Improved system performance by Y%',
        ]
    },
    {
        'type': 'work',
        'title': 'Software Engineer',
        'org': 'Previous Company',
        'location': 'New York, NY',
        'date': '2021 - 2023',
        'description': 'Worked on interesting problems. What did you build here?',
        'skills': ['JavaScript', 'Node.js', 'PostgreSQL'],
        'highlights': [
            'Shipped feature that impacted N users',
            'Mentored junior developers',
        ]
    },
    {
        'type': 'work',
        'title': 'Junior Developer',
        'org': 'First Job Inc',
        'location': 'Boston, MA',
        'date': '2019 - 2021',
        'description': 'Where you got your start. What did you learn?',
        'skills': ['Python', 'Django', 'MySQL'],
    },
    {
        'type': 'education',
        'title': 'B.S. Computer Science',
        'org': 'University Name',
        'location': 'City, State',
        'date': '2015 - 2019',
        'description': 'Studied computer science with focus on software engineering.',
        'highlights': [
            'Relevant coursework: Data Structures, Algorithms, Databases',
            'Senior project: Something cool you built',
        ]
    },
]


@router.get('/', name='resume.index')
async def index(request: Request):
    return templates.TemplateResponse(request, 'resume/index.html', {'timeline': TIMELINE})
