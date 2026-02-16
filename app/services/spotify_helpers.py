"""
Shared Spotify helpers used by both the main spotify blueprint
and the tools/spotify blueprint.
"""
import logging

import httpx
from fastapi import Request, HTTPException

from app.services.oauth import SpotifyOAuth, OAuthError

logger = logging.getLogger(__name__)

spotify_oauth = SpotifyOAuth()


def require_oauth(request: Request):
    """Check that Spotify OAuth token exists in session."""
    if not request.session.get('spotify_access_token'):
        raise HTTPException(status_code=401, detail='Not authenticated')


async def refresh_spotify_token(request: Request):
    """Refresh Spotify access token if we have a refresh token."""
    refresh_tok = request.session.get('spotify_refresh_token')
    if not refresh_tok:
        return None
    try:
        tokens = await spotify_oauth.refresh_token(refresh_tok)
    except OAuthError:
        logger.warning("Failed to refresh Spotify token")
        return None
    if 'access_token' in tokens:
        request.session['spotify_access_token'] = tokens['access_token']
        return tokens['access_token']
    return None


async def spotify_request(request: Request, endpoint, params=None,
                          method='GET', json_body=None):
    """Make a Spotify API request with automatic token refresh."""
    token = request.session.get('spotify_access_token')
    if not token:
        return None, 401

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(
                method,
                f'https://api.spotify.com/v1{endpoint}',
                params=params,
                json=json_body,
                headers={'Authorization': f'Bearer {token}'}
            )

            if response.status_code == 401:
                new_token = await refresh_spotify_token(request)
                if new_token:
                    response = await client.request(
                        method,
                        f'https://api.spotify.com/v1{endpoint}',
                        params=params,
                        json=json_body,
                        headers={'Authorization': f'Bearer {new_token}'}
                    )

            if response.status_code == 204:
                return {}, 204

            data = response.json() if response.is_success else None
            return (data, response.status_code)
    except httpx.HTTPError as exc:
        logger.error("Spotify API request failed: %s %s - %s", method, endpoint, exc)
        return None, 503
