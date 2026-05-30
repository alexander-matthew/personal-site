from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter()


@router.get('/', name='main.home')
async def home(request: Request):
    projects = [
        {
            'title': 'Spotify Dashboard',
            'description': 'Visualization of my Spotify listening habits, featuring taste evolution, audio profiles, and listening patterns.',
            'link': '/projects/spotify',
            'tags': ['Python', 'Spotify API', 'Data Viz']
        },
        {
            'title': 'Blackjack Trainer',
            'description': 'Practice blackjack with real-time feedback on optimal play. Tracks your decisions vs basic strategy.',
            'link': '/projects/blackjack',
            'tags': ['Game', 'Strategy', 'Interactive']
        },
        {
            'title': 'PR Review Tool',
            'description': 'A Claude Code skill for automating code review of firm-specific standards and style guidelines.',
            'link': '/projects/pr-review',
            'tags': ['Claude Code', 'AI', 'Developer Tools']
        },
        {
            'title': 'Sudoku',
            'description': 'Classic puzzle game with three difficulty levels. Real-time validation and keyboard navigation.',
            'link': '/projects/sudoku',
            'tags': ['Game', 'Puzzle', 'Interactive']
        },
        {
            'title': 'Weather Dashboard',
            'description': 'Real-time global weather with city search, forecasts, and animated themes.',
            'link': '/projects/weather',
            'tags': ['Weather', 'Data Viz', 'API']
        },
        {
            'title': "Deckard's Diary",
            'description': 'A diary kept one day at a time: a short piece and the generative art it seeds, shown together in a small in-browser IDE.',
            'link': '/projects/deckard',
            'tags': ['Generative', 'Canvas', 'Daily']
        },
    ]
    return templates.TemplateResponse(request, 'home.html', {'projects': projects})


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
        {
            'title': "Deckard's Diary",
            'description': "A machine-kept diary: each day a short piece — poem or story — and a generative-art sketch it inspires, with the source on display in a small in-browser IDE. Reseeded per viewer and per refresh.",
            'link': '/projects/deckard',
            'tags': ['Generative', 'Canvas', 'Daily']
        },
    ]
    return templates.TemplateResponse(request, 'projects.html', {'projects': sample_projects})
