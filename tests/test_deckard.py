"""Tests for Deckard's Diary — service, routes, and the daily generator."""
import importlib.util
import random
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.services import deckard as diary

# Load the generator module by path (scripts/ is not a package on sys.path).
_GEN_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'deckard' / 'generate_entry.py'
_spec = importlib.util.spec_from_file_location('deckard_generate', _GEN_PATH)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


@pytest.fixture(scope='module')
def client():
    return TestClient(create_app())


# --- service ---------------------------------------------------------------


def test_seed_entries_present():
    dates = diary.list_dates()
    assert len(dates) >= 3
    assert dates == sorted(dates, reverse=True)  # newest first by default


def test_get_entry_shape():
    e = diary.get_entry(diary.latest_date())
    for key in ('date', 'title', 'form', 'poem', 'palette', 'art'):
        assert key in e
    assert e['art']['sketch_url'].endswith(f"{e['date']}.js")
    assert isinstance(e['poem'], list) and e['poem']


def test_missing_entry_raises():
    with pytest.raises(diary.EntryNotFound):
        diary.get_entry('1900-01-01')


def test_neighbours_chain():
    dates = diary.list_dates(newest_first=False)
    older, newer = diary.neighbours(dates[0])
    assert older is None
    assert newer == dates[1]
    older, newer = diary.neighbours(dates[-1])
    assert newer is None


def test_summaries_match_index():
    assert len(diary.entry_summaries()) == len(diary.list_dates())


# --- routes ----------------------------------------------------------------


def test_index_renders(client):
    r = client.get('/projects/deckard')
    assert r.status_code == 200
    assert 'deckard-canvas' in r.text
    assert 'deckard-data' in r.text
    assert 'deckard-app.js' in r.text


def test_archive_renders(client):
    r = client.get('/projects/deckard/archive')
    assert r.status_code == 200
    assert 'dk-archive' in r.text


def test_dated_permalink(client):
    r = client.get(f'/projects/deckard/{diary.latest_date()}')
    assert r.status_code == 200


def test_unknown_date_404(client):
    assert client.get('/projects/deckard/2099-12-31').status_code == 404


def test_api_entries(client):
    r = client.get('/projects/deckard/api/entries')
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and data
    assert {'date', 'title', 'form'} <= set(data[0])


def test_api_entry_and_404(client):
    date = diary.latest_date()
    assert client.get(f'/projects/deckard/api/entry/{date}').status_code == 200
    assert client.get('/projects/deckard/api/entry/1900-01-01').status_code == 404


# --- generator -------------------------------------------------------------


@pytest.mark.parametrize('form', gen.FORMS)
def test_offline_generation_validates(form):
    entry, sketch = gen.generate_offline(form, day_number=1, rng=random.Random('seed'))
    gen.validate_entry(entry, sketch)
    assert entry['form'] == form
    assert 'window.__deckardSketch' in sketch


def test_offline_is_deterministic_per_date():
    a = gen.generate_offline('verse', 2, random.Random('2026-06-01'))
    b = gen.generate_offline('verse', 2, random.Random('2026-06-01'))
    assert a[0] == b[0]


def test_forbidden_terms_rejected():
    assert gen.contains_forbidden('a story about a robot')
    assert gen.contains_forbidden('thoughts on artificial intelligence')
    assert gen.contains_forbidden('like in Blade Runner')
    assert gen.contains_forbidden('clean reflective rain') is None


def test_validate_rejects_bad_palette():
    entry, sketch = gen.generate_offline('prose', 1, random.Random('x'))
    entry['palette'] = ['not-a-color']
    with pytest.raises(ValueError):
        gen.validate_entry(entry, sketch)


def test_parse_json_object_strips_fences():
    assert gen._parse_json_object('```json\n{"a": 1}\n```') == {'a': 1}
