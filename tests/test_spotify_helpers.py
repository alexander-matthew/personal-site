"""Tests for app/services/spotify_helpers.py."""
import httpx
import pytest
import respx
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.services.spotify_helpers import require_oauth, spotify_request


class FakeApp:
    """Minimal app stub with state containing shared HTTP client."""

    def __init__(self, http_client=None):
        self.state = MagicMock()
        self.state.http_client = http_client or MagicMock()


class FakeRequest:
    """Minimal request stub with a dict-backed session."""

    def __init__(self, session=None, http_client=None):
        self.session = session or {}
        self.app = FakeApp(http_client)


class TestRequireOAuth:

    def test_raises_401_when_no_token(self):
        request = FakeRequest()
        with pytest.raises(HTTPException) as exc_info:
            require_oauth(request)
        assert exc_info.value.status_code == 401

    def test_raises_401_when_token_is_none(self):
        request = FakeRequest({'spotify_access_token': None})
        with pytest.raises(HTTPException) as exc_info:
            require_oauth(request)
        assert exc_info.value.status_code == 401

    def test_passes_when_token_exists(self):
        request = FakeRequest({'spotify_access_token': 'valid_token'})
        require_oauth(request)  # should not raise


class TestSpotifyRequest:

    @respx.mock
    async def test_success_returns_data(self):
        async with httpx.AsyncClient() as client:
            request = FakeRequest({'spotify_access_token': 'tok123'}, http_client=client)
            respx.get("https://api.spotify.com/v1/me/player/recently-played").mock(
                return_value=httpx.Response(200, json={'items': [1, 2, 3]})
            )
            data, status = await spotify_request(request, '/me/player/recently-played')
            assert status == 200
            assert data == {'items': [1, 2, 3]}

    @respx.mock
    async def test_failure_returns_none(self):
        async with httpx.AsyncClient() as client:
            request = FakeRequest({'spotify_access_token': 'tok123'}, http_client=client)
            respx.get("https://api.spotify.com/v1/me/top/tracks").mock(
                return_value=httpx.Response(403, json={'error': 'forbidden'})
            )
            data, status = await spotify_request(request, '/me/top/tracks')
            assert data is None
            assert status == 403

    @respx.mock
    async def test_204_returns_empty_dict(self):
        async with httpx.AsyncClient() as client:
            request = FakeRequest({'spotify_access_token': 'tok123'}, http_client=client)
            respx.get("https://api.spotify.com/v1/me/player").mock(
                return_value=httpx.Response(204)
            )
            data, status = await spotify_request(request, '/me/player')
            assert data == {}
            assert status == 204

    async def test_no_token_returns_401(self):
        request = FakeRequest({})
        data, status = await spotify_request(request, '/me/player')
        assert data is None
        assert status == 401

    @respx.mock
    async def test_network_error_returns_503(self):
        async with httpx.AsyncClient() as client:
            request = FakeRequest({'spotify_access_token': 'tok123'}, http_client=client)
            respx.get("https://api.spotify.com/v1/me/player").mock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            data, status = await spotify_request(request, '/me/player')
            assert data is None
            assert status == 503

    @respx.mock
    async def test_timeout_returns_503(self):
        async with httpx.AsyncClient() as client:
            request = FakeRequest({'spotify_access_token': 'tok123'}, http_client=client)
            respx.get("https://api.spotify.com/v1/me/player").mock(
                side_effect=httpx.ReadTimeout("Read timed out")
            )
            data, status = await spotify_request(request, '/me/player')
            assert data is None
            assert status == 503

    @respx.mock
    async def test_post_method_works(self):
        async with httpx.AsyncClient() as client:
            request = FakeRequest({'spotify_access_token': 'tok123'}, http_client=client)
            respx.put("https://api.spotify.com/v1/me/player/play").mock(
                return_value=httpx.Response(204)
            )
            data, status = await spotify_request(
                request, '/me/player/play', method='PUT'
            )
            assert data == {}
            assert status == 204

    @respx.mock
    async def test_401_triggers_token_refresh(self):
        """On 401, spotify_request should attempt token refresh and retry."""
        async with httpx.AsyncClient() as client:
            request = FakeRequest({
                'spotify_access_token': 'expired_tok',
                'spotify_refresh_token': 'refresh_tok'
            }, http_client=client)
            # First call returns 401, second (after refresh) returns 200
            route = respx.get("https://api.spotify.com/v1/me/top/tracks")
            route.side_effect = [
                httpx.Response(401, json={'error': 'expired'}),
                httpx.Response(200, json={'items': ['track1']}),
            ]
            # Mock the token refresh endpoint
            respx.post("https://accounts.spotify.com/api/token").mock(
                return_value=httpx.Response(200, json={
                    'access_token': 'new_token',
                    'token_type': 'Bearer',
                })
            )
            data, status = await spotify_request(request, '/me/top/tracks')
            assert status == 200
            assert data == {'items': ['track1']}
            assert request.session['spotify_access_token'] == 'new_token'
