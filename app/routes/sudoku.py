from fastapi import APIRouter, Request
from app.templating import templates

router = APIRouter(prefix='/projects/sudoku')


@router.get('/', name='sudoku.index')
async def index(request: Request):
    """Sudoku puzzle game with difficulty levels."""
    return templates.TemplateResponse(request, 'sudoku/index.html')
