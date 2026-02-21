"""
OAuth utilities for API integrations.
Supports authorization code flow for services like Spotify.
"""
import os
import base64
from urllib.parse import urlencode

import logging

import httpx

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Raised when an OAuth token exchange or refresh fails."""
    pass


class OAuthClient:
    """Base OAuth 2.0 client."""

    def __init__(self, client_id, client_secret, auth_url, token_url, scopes):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.scopes = scopes

    def get_auth_url(self, redirect_uri, state=None):
        """Generate authorization URL."""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
        }
        if state:
            params['state'] = state
        return f"{self.auth_url}?{urlencode(params)}"

    def _auth_header(self):
        return base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

    async def exchange_code(self, code, redirect_uri, *, http_client: httpx.AsyncClient):
        """Exchange authorization code for tokens. Raises OAuthError on failure."""
        response = await http_client.post(self.token_url, data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }, headers={
            'Authorization': f'Basic {self._auth_header()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        if response.is_success:
            return response.json()
        logger.error("OAuth exchange_code failed: %s", response.status_code)
        raise OAuthError(f"Token exchange failed with status {response.status_code}")

    async def refresh_token(self, refresh_token, *, http_client: httpx.AsyncClient):
        """Refresh access token. Raises OAuthError on failure."""
        response = await http_client.post(self.token_url, data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }, headers={
            'Authorization': f'Basic {self._auth_header()}',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        if response.is_success:
            return response.json()
        logger.error("OAuth refresh_token failed: %s", response.status_code)
        raise OAuthError(f"Token refresh failed with status {response.status_code}")


class SpotifyOAuth(OAuthClient):
    """Spotify-specific OAuth client."""

    def __init__(self):
        super().__init__(
            client_id=os.environ.get('SPOTIFY_CLIENT_ID', ''),
            client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET', ''),
            auth_url='https://accounts.spotify.com/authorize',
            token_url='https://accounts.spotify.com/api/token',
            scopes=[
                'user-read-recently-played',
                'user-top-read',
                'user-read-currently-playing',
                'user-read-playback-state',
                'user-modify-playback-state',
                'streaming',
                'playlist-modify-private',
            ]
        )

    @property
    def is_configured(self):
        """Check if Spotify credentials are configured."""
        return bool(self.client_id and self.client_secret)
