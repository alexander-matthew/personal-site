"""
OAuth utilities for API integrations.
Supports authorization code flow for services like Spotify.
"""
import os
import base64
import requests
from flask import session, redirect, url_for
from functools import wraps


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
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        return f"{self.auth_url}?{query}"

    def exchange_code(self, code, redirect_uri):
        """Exchange authorization code for tokens."""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = requests.post(self.token_url, data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }, headers={
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        return response.json()

    def refresh_token(self, refresh_token):
        """Refresh access token."""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = requests.post(self.token_url, data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }, headers={
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        return response.json()


class SpotifyOAuth(OAuthClient):
    """Spotify-specific OAuth client."""

    def __init__(self):
        super().__init__(
            client_id=os.environ.get('SPOTIFY_CLIENT_ID', ''),
            client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET', ''),
            auth_url='https://accounts.spotify.com/authorize',
            token_url='https://accounts.spotify.com/api/token',
            scopes=['user-read-recently-played', 'user-top-read']
        )

    @property
    def is_configured(self):
        """Check if Spotify credentials are configured."""
        return bool(self.client_id and self.client_secret)


def require_oauth(provider):
    """Decorator to require OAuth authentication for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token_key = f'{provider}_access_token'
            if token_key not in session:
                return redirect(url_for(f'tools.{provider}_auth'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
