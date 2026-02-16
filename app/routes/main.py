from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter()


@router.get('/', name='main.home')
async def home(request: Request):
    return templates.TemplateResponse(request, 'home.html')


@router.get('/about', name='main.about')
async def about(request: Request):
    return templates.TemplateResponse(request, 'about.html')


@router.get('/projects', name='main.projects')
async def projects(request: Request):
    sample_projects = [
        {
            'title': 'Spotify Dashboard',
            'description': 'Cyberpunk-themed visualization of my Spotify listening habits, featuring taste evolution, audio profiles, and listening patterns.',
            'link': '/projects/spotify',
            'tags': ['Python', 'Spotify API', 'Data Viz']
        },
        {
            'title': 'Blackjack Trainer',
            'description': 'Practice blackjack with real-time feedback on optimal play. Tracks your decisions vs basic strategy and helps you learn from mistakes.',
            'link': '/projects/blackjack',
            'tags': ['Game', 'Strategy', 'Interactive']
        },
        {
            'title': 'PR Review Tool',
            'description': 'A Claude Code skill for automating code review of firm-specific standards and style guidelines, saving senior developers hours of review time.',
            'link': '/projects/pr-review',
            'tags': ['Claude Code', 'AI', 'Developer Tools']
        },
        {
            'title': 'Sudoku',
            'description': 'Classic puzzle game with three difficulty levels. Features real-time validation, keyboard navigation, and guaranteed unique solutions.',
            'link': '/projects/sudoku',
            'tags': ['Game', 'Puzzle', 'Interactive']
        },
        {
            'title': 'Weather Dashboard',
            'description': 'Real-time global weather with animated themes. Track extreme weather patterns worldwide and see industry impact analysis.',
            'link': '/projects/weather',
            'tags': ['Weather', 'Data Viz', 'API']
        },
    ]
    return templates.TemplateResponse(request, 'projects.html', {'projects': sample_projects})
