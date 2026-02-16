"""Tests for app/services/oauth.py."""
import os
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

import httpx
import pytest
import respx

from app.services.oauth import OAuthClient, SpotifyOAuth


class TestOAuthClient:

    def _make_client(self):
        return OAuthClient(
            client_id='test_id',
            client_secret='test_secret',
            auth_url='https://auth.example.com/authorize',
            token_url='https://auth.example.com/token',
            scopes=['scope1', 'scope2'],
        )

    def test_get_auth_url_contains_required_params(self):
        client = self._make_client()
        url = client.get_auth_url('https://app.example.com/callback')
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params['client_id'] == ['test_id']
        assert params['response_type'] == ['code']
        assert params['redirect_uri'] == ['https://app.example.com/callback']
        assert params['scope'] == ['scope1 scope2']

    def test_get_auth_url_includes_state_when_provided(self):
        client = self._make_client()
        url = client.get_auth_url('https://app.example.com/callback', state='abc123')
        params = parse_qs(urlparse(url).query)
        assert params['state'] == ['abc123']

    def test_get_auth_url_omits_state_when_none(self):
        client = self._make_client()
        url = client.get_auth_url('https://app.example.com/callback')
        params = parse_qs(urlparse(url).query)
        assert 'state' not in params

    @respx.mock
    async def test_exchange_code_success(self):
        client = self._make_client()
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(200, json={
                'access_token': 'new_access',
                'refresh_token': 'new_refresh',
                'token_type': 'Bearer',
            })
        )
        tokens = await client.exchange_code('auth_code', 'https://app.example.com/callback')
        assert tokens['access_token'] == 'new_access'
        assert tokens['refresh_token'] == 'new_refresh'

    @respx.mock
    async def test_exchange_code_failure_returns_empty_dict(self):
        client = self._make_client()
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(400, json={'error': 'invalid_grant'})
        )
        tokens = await client.exchange_code('bad_code', 'https://app.example.com/callback')
        assert tokens == {}

    @respx.mock
    async def test_refresh_token_success(self):
        client = self._make_client()
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(200, json={
                'access_token': 'refreshed_token',
                'token_type': 'Bearer',
            })
        )
        tokens = await client.refresh_token('old_refresh')
        assert tokens['access_token'] == 'refreshed_token'

    @respx.mock
    async def test_refresh_token_failure_returns_empty_dict(self):
        client = self._make_client()
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(401, json={'error': 'invalid_token'})
        )
        tokens = await client.refresh_token('bad_refresh')
        assert tokens == {}

    def test_auth_header_is_base64_encoded(self):
        client = self._make_client()
        import base64
        expected = base64.b64encode(b"test_id:test_secret").decode()
        assert client._auth_header() == expected


class TestSpotifyOAuth:

    def test_is_configured_true_when_both_set(self):
        with patch.dict(os.environ, {
            'SPOTIFY_CLIENT_ID': 'id123',
            'SPOTIFY_CLIENT_SECRET': 'secret456',
        }):
            client = SpotifyOAuth()
            assert client.is_configured is True

    def test_is_configured_false_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove both env vars
            os.environ.pop('SPOTIFY_CLIENT_ID', None)
            os.environ.pop('SPOTIFY_CLIENT_SECRET', None)
            client = SpotifyOAuth()
            assert client.is_configured is False

    def test_scopes_include_playback(self):
        with patch.dict(os.environ, {
            'SPOTIFY_CLIENT_ID': 'id',
            'SPOTIFY_CLIENT_SECRET': 'secret',
        }):
            client = SpotifyOAuth()
            assert 'streaming' in client.scopes
            assert 'user-read-recently-played' in client.scopes
