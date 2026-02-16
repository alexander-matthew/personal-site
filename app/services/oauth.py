"""
OAuth utilities for API integrations.
Supports authorization code flow for services like Spotify.
"""
import os
import base64
from urllib.parse import urlencode

import httpx


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

    async def exchange_code(self, code, redirect_uri):
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.token_url, data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
            }, headers={
                'Authorization': f'Basic {self._auth_header()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            })
        return response.json() if response.is_success else {}

    async def refresh_token(self, refresh_token):
        """Refresh access token."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.token_url, data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }, headers={
                'Authorization': f'Basic {self._auth_header()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            })
        return response.json() if response.is_success else {}


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
            ]
        )

    @property
    def is_configured(self):
        """Check if Spotify credentials are configured."""
        return bool(self.client_id and self.client_secret)
