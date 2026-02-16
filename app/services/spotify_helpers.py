"""
Shared Spotify helpers used by both the main spotify blueprint
and the tools/spotify blueprint.
"""
import logging

import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

from app.services.oauth import SpotifyOAuth

spotify_oauth = SpotifyOAuth()


def require_oauth(request: Request):
    """Check that Spotify OAuth token exists in session."""
    if 'spotify_access_token' not in request.session:
        raise HTTPException(status_code=401, detail='Not authenticated')


async def refresh_spotify_token(request: Request):
    """Refresh Spotify access token if we have a refresh token."""
    refresh_tok = request.session.get('spotify_refresh_token')
    if not refresh_tok:
        return None
    tokens = await spotify_oauth.refresh_token(refresh_tok)
    if 'access_token' in tokens:
        request.session['spotify_access_token'] = tokens['access_token']
        return tokens['access_token']
    return None


async def spotify_request(request: Request, endpoint, params=None):
    """Make a Spotify API request with automatic token refresh."""
    token = request.session.get('spotify_access_token')
    if not token:
        return None, 401

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f'https://api.spotify.com/v1{endpoint}',
            params=params,
            headers={'Authorization': f'Bearer {token}'}
        )

        if response.status_code == 401:
            new_token = await refresh_spotify_token(request)
            if new_token:
                response = await client.get(
                    f'https://api.spotify.com/v1{endpoint}',
                    params=params,
                    headers={'Authorization': f'Bearer {new_token}'}
                )

    data = response.json() if response.is_success else None
    return (data, response.status_code)
