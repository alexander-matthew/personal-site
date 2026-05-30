"""Deckard's Diary routes.

A daily, machine-kept diary: each day a short-form piece and a generative-art
sketch inspired by it, shown together in a small in-browser IDE. The art is
reseeded per viewer and per refresh, so no two readers see the same rendering of
the same algorithm.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services import deckard as diary
from app.templating import templates

router = APIRouter(prefix='/projects/deckard')

# `site` is injected as a Jinja global in templating.py, so the context here only
# needs the entry-specific data.


def _render_entry(request: Request, date: str | None):
    if date is None:
        entry = diary.latest_entry()
    else:
        try:
            entry = diary.get_entry(date)
        except diary.EntryNotFound:
            entry = None

    if entry is None:
        return templates.TemplateResponse(
            request,
            'deckard/empty.html',
            status_code=404 if date else 200,
        )

    older, newer = diary.neighbours(entry['date'])
    return templates.TemplateResponse(
        request,
        'deckard/index.html',
        {
            'entry': entry,
            'older': older,
            'newer': newer,
            'total': len(diary.list_dates()),
        },
    )


@router.get('/', name='deckard.index')
async def index(request: Request):
    return _render_entry(request, None)


@router.get('/archive', name='deckard.archive')
async def archive(request: Request):
    return templates.TemplateResponse(
        request,
        'deckard/archive.html',
        {'entries': diary.entry_summaries()},
    )


@router.get('/api/entries', name='deckard.api_entries')
async def api_entries(request: Request):
    return JSONResponse(diary.entry_summaries())


@router.get('/api/entry/{date}', name='deckard.api_entry')
async def api_entry(request: Request, date: str):
    try:
        return JSONResponse(diary.get_entry(date))
    except diary.EntryNotFound:
        return JSONResponse({'error': 'not found', 'date': date}, status_code=404)


# Dated permalink. Kept last so it does not shadow /archive or /api/*.
@router.get('/{date}', name='deckard.entry')
async def entry(request: Request, date: str):
    return _render_entry(request, date)
