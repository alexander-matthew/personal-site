"""Tests for the /version endpoint."""
import re
import subprocess
from datetime import datetime
from unittest.mock import patch

import pytest

from app.routes import version as version_module


def _current_short_sha() -> str:
    return subprocess.run(
        ['git', 'rev-parse', '--short', 'HEAD'],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_version_returns_200_and_shape(client):
    resp = client.get('/version')
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {'sha', 'built_at'}


def test_version_sha_matches_git_rev_parse(client):
    resp = client.get('/version')
    sha = resp.json()['sha']
    assert sha == _current_short_sha()
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


def test_read_sha_invokes_git_rev_parse_short_head():
    """_read_sha must always call `git rev-parse --short HEAD` (issue #20 contract)."""
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout='deadbee\n', stderr='')
    with patch.object(version_module.subprocess, 'run', return_value=fake) as mock_run:
        assert version_module._read_sha() == 'deadbee'
    args, kwargs = mock_run.call_args
    assert args[0] == ['git', 'rev-parse', '--short', 'HEAD']
    assert kwargs['check'] is True
    assert kwargs['cwd'] == version_module._REPO_ROOT


def test_read_sha_propagates_git_failure():
    """If git is unavailable the endpoint should fail loudly rather than mask the SHA."""
    with patch.object(
        version_module.subprocess,
        'run',
        side_effect=subprocess.CalledProcessError(returncode=128, cmd=['git']),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            version_module._read_sha()
