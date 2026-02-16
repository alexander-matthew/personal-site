from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter(prefix='/projects/blackjack')


@router.get('/', name='blackjack.index')
async def index(request: Request):
    """Blackjack training game with optimal play tracking."""
    return templates.TemplateResponse(request, 'blackjack/index.html')
