"""Tests for the /version endpoint."""
import re
from datetime import datetime


def test_version_returns_200_and_shape(client):
    resp = client.get('/version')
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {'sha', 'built_at'}


def test_version_sha_is_non_empty_hex(client):
    resp = client.get('/version')
    sha = resp.json()['sha']
    assert isinstance(sha, str)
    assert sha
    # `git rev-parse --short HEAD` returns lowercase hex; the env-var fallback
    # also produces a hex slice. "unknown" only appears when git is unavailable.
    assert re.fullmatch(r'[0-9a-f]+', sha), f'sha {sha!r} is not hex'


def test_version_built_at_is_iso_utc(client):
    resp = client.get('/version')
    built_at = resp.json()['built_at']
    parsed = datetime.fromisoformat(built_at)
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_version_built_at_stable_across_requests(client):
    first = client.get('/version').json()['built_at']
    second = client.get('/version').json()['built_at']
    assert first == second
