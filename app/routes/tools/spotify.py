"""
Spotify Listening Trends Tool
Registers under /tools/spotify with its own OAuth redirect URLs.
Delegates shared API logic to the main spotify routes.
"""
import secrets

import logging

from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from app.routes.tools import router, register_tool
from app.routes.spotify import (
    api_recent, api_top, api_genres, api_taste_evolution,
)
from app.services.oauth import OAuthError
from app.services.spotify_helpers import spotify_oauth, require_oauth, spotify_request
from app.services.rate_limit import rate_limit
from app.templating import templates

logger = logging.getLogger(__name__)

# Register this tool with the framework
register_tool({
    'id': 'spotify',
    'name': 'Spotify Listening Trends',
    'description': 'Visualize your listening habits with charts and stats',
    'icon': 'music',
    'tags': ['API', 'Charts', 'Music'],
    'requires_auth': True,
})


@router.get('/spotify', name='tools.spotify_index')
async def spotify_index(request: Request):
    """Spotify tool main page."""
    is_authenticated = 'spotify_access_token' in request.session
    is_configured = spotify_oauth.is_configured
    return templates.TemplateResponse(request, 'tools/spotify/index.html',
                                      {'is_authenticated': is_authenticated,
                                       'is_configured': is_configured})


@router.get('/spotify/auth', name='tools.spotify_auth',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def spotify_auth(request: Request):
    """Initiate Spotify OAuth flow."""
    redirect_uri = str(request.url_for('tools.spotify_callback'))
    state = secrets.token_urlsafe(32)
    request.session['spotify_oauth_state'] = state
    auth_url = spotify_oauth.get_auth_url(redirect_uri, state=state)
    return RedirectResponse(url=auth_url, status_code=302)


@router.get('/spotify/callback', name='tools.spotify_callback',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def spotify_callback(request: Request):
    """Handle Spotify OAuth callback."""
    code = request.query_params.get('code')
    error = request.query_params.get('error')
    state = request.query_params.get('state')

    if error:
        return RedirectResponse(url=str(request.url_for('tools.spotify_index')), status_code=302)

    # Validate CSRF state
    expected_state = request.session.pop('spotify_oauth_state', None)
    if not state or state != expected_state:
        raise HTTPException(status_code=403, detail='OAuth state mismatch')

    redirect_uri = str(request.url_for('tools.spotify_callback'))
    try:
        tokens = await spotify_oauth.exchange_code(
            code, redirect_uri, http_client=request.app.state.http_client
        )
    except OAuthError:
        logger.warning("OAuth token exchange failed during tools callback")
        return RedirectResponse(url=str(request.url_for('tools.spotify_index')), status_code=302)

    request.session['spotify_access_token'] = tokens['access_token']
    request.session['spotify_refresh_token'] = tokens.get('refresh_token')

    return RedirectResponse(url=str(request.url_for('tools.spotify_index')), status_code=302)


@router.get('/spotify/logout', name='tools.spotify_logout',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def spotify_logout(request: Request):
    """Clear Spotify session."""
    request.session.pop('spotify_access_token', None)
    request.session.pop('spotify_refresh_token', None)
    request.session.pop('spotify_oauth_state', None)
    return RedirectResponse(url=str(request.url_for('tools.spotify_index')), status_code=302)


# -----------------------------------------------
# API endpoints: delegate to main spotify routes
# -----------------------------------------------

@router.get('/spotify/api/recent', name='tools.spotify_recent',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def tools_spotify_recent(request: Request):
    return await api_recent(request)


@router.get('/spotify/api/top/{time_range}', name='tools.spotify_top',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def tools_spotify_top(request: Request, time_range: str):
    return await api_top(request, time_range)


@router.get('/spotify/api/now-playing', name='tools.spotify_now_playing',
            dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))])
async def spotify_now_playing(request: Request):
    """API endpoint: Get currently playing track (tools-only endpoint)."""
    require_oauth(request)
    data, status = await spotify_request(request, '/me/player/currently-playing')

    if status == 204 or data is None:
        return {'is_playing': False}

    if not data.get('item'):
        return {'is_playing': False}

    track = data['item']
    return {
        'is_playing': data.get('is_playing', False),
        'track': {
            'name': track.get('name'),
            'artist': track['artists'][0]['name'] if track.get('artists') else 'Unknown',
            'album': track.get('album', {}).get('name'),
            'image': track.get('album', {}).get('images', [{}])[0].get('url'),
            'duration_ms': track.get('duration_ms', 0),
            'progress_ms': data.get('progress_ms', 0),
        }
    }


@router.get('/spotify/api/genres', name='tools.spotify_genres',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def tools_spotify_genres(request: Request):
    return await api_genres(request)


@router.get('/spotify/api/taste-evolution', name='tools.spotify_taste_evolution',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def tools_spotify_taste_evolution(request: Request):
    return await api_taste_evolution(request)
