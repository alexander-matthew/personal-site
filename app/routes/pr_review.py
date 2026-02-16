"""
PR Review Tool Showcase
Interactive demonstration of the Claude Code PR Review skill.
"""
from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter(prefix='/projects/pr-review')


@router.get('/', name='pr_review.index')
async def index(request: Request):
    """PR Review Tool showcase main page."""
    return templates.TemplateResponse(request, 'pr_review/index.html')
