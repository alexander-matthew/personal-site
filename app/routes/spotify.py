"""
Spotify Listening Trends
Visualizes recently played tracks and top artists/tracks.
"""
import logging
import secrets

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.services.oauth import OAuthError
from app.services.spotify_helpers import spotify_oauth, require_oauth, spotify_request
from app.services.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/projects/spotify')


@router.get('/', name='spotify.index')
async def index(request: Request):
    """Spotify dashboard main page."""
    is_authenticated = bool(request.session.get('spotify_access_token'))
    is_configured = spotify_oauth.is_configured
    return templates.TemplateResponse(request, 'spotify/index.html',
                                      {'is_authenticated': is_authenticated,
                                       'is_configured': is_configured})


@router.get('/auth', name='spotify.auth',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def auth(request: Request):
    """Initiate Spotify OAuth flow."""
    redirect_uri = str(request.url_for('spotify.callback'))
    state = secrets.token_urlsafe(32)
    request.session['spotify_oauth_state'] = state
    auth_url = spotify_oauth.get_auth_url(redirect_uri, state=state)
    return RedirectResponse(url=auth_url, status_code=302)


@router.get('/callback', name='spotify.callback',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def callback(request: Request):
    """Handle Spotify OAuth callback."""
    code = request.query_params.get('code')
    error = request.query_params.get('error')
    state = request.query_params.get('state')

    if error:
        return RedirectResponse(url=str(request.url_for('spotify.index')), status_code=302)

    # Validate CSRF state
    expected_state = request.session.pop('spotify_oauth_state', None)
    if not state or state != expected_state:
        raise HTTPException(status_code=403, detail='OAuth state mismatch')

    redirect_uri = str(request.url_for('spotify.callback'))
    try:
        tokens = await spotify_oauth.exchange_code(code, redirect_uri)
    except OAuthError:
        logger.warning("OAuth token exchange failed during callback")
        return RedirectResponse(url=str(request.url_for('spotify.index')), status_code=302)

    request.session['spotify_access_token'] = tokens['access_token']
    request.session['spotify_refresh_token'] = tokens.get('refresh_token')

    return RedirectResponse(url=str(request.url_for('spotify.index')), status_code=302)


@router.get('/logout', name='spotify.logout',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def logout(request: Request):
    """Clear Spotify session."""
    request.session.pop('spotify_access_token', None)
    request.session.pop('spotify_refresh_token', None)
    request.session.pop('spotify_oauth_state', None)
    return RedirectResponse(url=str(request.url_for('spotify.index')), status_code=302)


@router.get('/api/recent', name='spotify.api_recent',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_recent(request: Request):
    """API endpoint: Get recently played tracks."""
    require_oauth(request)
    data, status = await spotify_request(request, '/me/player/recently-played', {'limit': 50})
    if data is None:
        raise HTTPException(status_code=status, detail='Failed to fetch data')
    return data


@router.get('/api/top/{time_range}', name='spotify.api_top',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_top(request: Request, time_range: str):
    """API endpoint: Get top tracks/artists."""
    require_oauth(request)
    if time_range not in ['short_term', 'medium_term', 'long_term']:
        time_range = 'medium_term'

    tracks_data, tracks_status = await spotify_request(request, '/me/top/tracks', {
        'limit': 20,
        'time_range': time_range
    })

    artists_data, artists_status = await spotify_request(request, '/me/top/artists', {
        'limit': 10,
        'time_range': time_range
    })

    if tracks_data is None and artists_data is None:
        raise HTTPException(status_code=tracks_status, detail='Failed to fetch data')

    return {'tracks': tracks_data, 'artists': artists_data}


@router.get('/api/genres', name='spotify.api_genres',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_genres(request: Request):
    """API endpoint: Get genre breakdown from top artists."""
    require_oauth(request)
    artists_data, _ = await spotify_request(request, '/me/top/artists', {
        'limit': 50,
        'time_range': 'medium_term'
    })

    if not artists_data or 'items' not in artists_data:
        return {'genres': []}

    genre_counts = {}
    for artist in artists_data['items']:
        for genre in artist.get('genres', []):
            genre_counts[genre] = genre_counts.get(genre, 0) + 1

    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    total = sum(count for _, count in sorted_genres)

    genres = [
        {'name': genre, 'count': count, 'percent': round(count / total * 100) if total > 0 else 0}
        for genre, count in sorted_genres
    ]

    return {'genres': genres}


@router.get('/api/audio-features', name='spotify.api_audio_features',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_audio_features(request: Request):
    """API endpoint: Get average audio features from top tracks."""
    require_oauth(request)
    tracks_data, _ = await spotify_request(request, '/me/top/tracks', {
        'limit': 50,
        'time_range': 'medium_term'
    })

    if not tracks_data or 'items' not in tracks_data:
        return {'features': None}

    track_ids = [track['id'] for track in tracks_data['items']]

    features_data, _ = await spotify_request(request, '/audio-features', {
        'ids': ','.join(track_ids)
    })

    if not features_data or 'audio_features' not in features_data:
        return {'features': None}

    feature_keys = ['danceability', 'energy', 'acousticness', 'valence', 'instrumentalness', 'liveness']
    totals = {key: 0 for key in feature_keys}
    count = 0

    for features in features_data['audio_features']:
        if features:
            count += 1
            for key in feature_keys:
                totals[key] += features.get(key, 0)

    if count == 0:
        return {'features': None}

    averages = {key: round(totals[key] / count * 100) for key in feature_keys}

    return {'features': averages}


@router.get('/api/taste-evolution', name='spotify.api_taste_evolution',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_taste_evolution(request: Request):
    """API endpoint: Compare top artists across time periods."""
    require_oauth(request)
    periods = ['short_term', 'medium_term', 'long_term']
    period_labels = {'short_term': '4 Weeks', 'medium_term': '6 Months', 'long_term': 'All Time'}

    evolution = {}

    for period in periods:
        artists_data, _ = await spotify_request(request, '/me/top/artists', {
            'limit': 5,
            'time_range': period
        })

        if artists_data and 'items' in artists_data:
            evolution[period] = {
                'label': period_labels[period],
                'artists': [
                    {
                        'name': artist['name'],
                        'image': artist['images'][-1]['url'] if artist.get('images') else None,
                        'genres': artist.get('genres', [])[:2]
                    }
                    for artist in artists_data['items']
                ]
            }
        else:
            evolution[period] = {'label': period_labels[period], 'artists': []}

    return evolution


# ===============================================
# Playback API Endpoints
# ===============================================

@router.get('/api/token', name='spotify.api_token',
            dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))])
async def api_token(request: Request):
    """Return access token for Web Playback SDK."""
    require_oauth(request)
    token = request.session.get('spotify_access_token')
    return {'access_token': token}


@router.get('/api/playback-state', name='spotify.api_playback_state',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_playback_state(request: Request):
    """Get current playback state."""
    require_oauth(request)
    data, status = await spotify_request(request, '/me/player')
    if status == 204:
        return {'is_playing': False, 'item': None}
    if data is None:
        raise HTTPException(status_code=status, detail='Failed to fetch playback state')
    return data


@router.get('/api/devices', name='spotify.api_devices',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_devices(request: Request):
    """Get available devices."""
    require_oauth(request)
    data, status = await spotify_request(request, '/me/player/devices')
    if data is None:
        raise HTTPException(status_code=status, detail='Failed to fetch devices')
    return data


async def _get_json_body(request: Request):
    """Safely parse JSON body, returning empty dict if body is empty."""
    body = await request.body()
    if not body:
        return {}
    return await request.json()


@router.post('/api/transfer', name='spotify.api_transfer',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_transfer(request: Request):
    """Transfer playback to a device."""
    require_oauth(request)
    body = await _get_json_body(request)
    device_id = body.get('device_id')
    if not device_id:
        raise HTTPException(status_code=400, detail='device_id is required')

    data, status = await spotify_request(
        request, '/me/player', method='PUT',
        json_body={'device_ids': [device_id], 'play': True}
    )
    if status in [204, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Transfer failed')


@router.post('/api/play', name='spotify.api_play',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_play(request: Request):
    """Start or resume playback."""
    require_oauth(request)
    body = await _get_json_body(request)

    params = {}
    if body.get('device_id'):
        params['device_id'] = body['device_id']

    json_body = {}
    if body.get('uris'):
        json_body['uris'] = body['uris']
    elif body.get('context_uri'):
        json_body['context_uri'] = body['context_uri']
        if body.get('offset'):
            json_body['offset'] = body['offset']

    data, status = await spotify_request(
        request, '/me/player/play', params=params if params else None,
        method='PUT', json_body=json_body if json_body else None
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Play failed')


@router.post('/api/pause', name='spotify.api_pause',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_pause(request: Request):
    """Pause playback."""
    require_oauth(request)
    body = await _get_json_body(request)
    device_id = body.get('device_id')

    params = {'device_id': device_id} if device_id else None

    data, status = await spotify_request(
        request, '/me/player/pause', params=params, method='PUT'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Pause failed')


@router.post('/api/next', name='spotify.api_next',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_next(request: Request):
    """Skip to next track."""
    require_oauth(request)
    body = await _get_json_body(request)
    device_id = body.get('device_id')

    params = {'device_id': device_id} if device_id else None

    data, status = await spotify_request(
        request, '/me/player/next', params=params, method='POST'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Skip failed')


@router.post('/api/previous', name='spotify.api_previous',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_previous(request: Request):
    """Skip to previous track."""
    require_oauth(request)
    body = await _get_json_body(request)
    device_id = body.get('device_id')

    params = {'device_id': device_id} if device_id else None

    data, status = await spotify_request(
        request, '/me/player/previous', params=params, method='POST'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Previous failed')


@router.post('/api/seek', name='spotify.api_seek',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_seek(request: Request):
    """Seek to position in track."""
    require_oauth(request)
    body = await _get_json_body(request)
    position_ms = body.get('position_ms', 0)
    if not isinstance(position_ms, int) or position_ms < 0:
        raise HTTPException(status_code=400, detail='position_ms must be a non-negative integer')
    device_id = body.get('device_id')

    params = {'position_ms': position_ms}
    if device_id:
        params['device_id'] = device_id

    data, status = await spotify_request(
        request, '/me/player/seek', params=params, method='PUT'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Seek failed')


@router.post('/api/volume', name='spotify.api_volume',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_volume(request: Request):
    """Set volume level."""
    require_oauth(request)
    body = await _get_json_body(request)
    volume_percent = body.get('volume_percent', 50)
    if not isinstance(volume_percent, int) or not (0 <= volume_percent <= 100):
        raise HTTPException(status_code=400, detail='volume_percent must be 0-100')
    device_id = body.get('device_id')

    params = {'volume_percent': volume_percent}
    if device_id:
        params['device_id'] = device_id

    data, status = await spotify_request(
        request, '/me/player/volume', params=params, method='PUT'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Volume failed')


@router.post('/api/shuffle', name='spotify.api_shuffle',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_shuffle(request: Request):
    """Toggle shuffle."""
    require_oauth(request)
    body = await _get_json_body(request)
    state = body.get('state', True)
    device_id = body.get('device_id')

    params = {'state': str(state).lower()}
    if device_id:
        params['device_id'] = device_id

    data, status = await spotify_request(
        request, '/me/player/shuffle', params=params, method='PUT'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Shuffle failed')


@router.post('/api/repeat', name='spotify.api_repeat',
             dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def api_repeat(request: Request):
    """Set repeat mode (off, context, track)."""
    require_oauth(request)
    body = await _get_json_body(request)
    state = body.get('state', 'off')
    if state not in ('off', 'context', 'track'):
        raise HTTPException(status_code=400, detail='state must be off, context, or track')
    device_id = body.get('device_id')

    params = {'state': state}
    if device_id:
        params['device_id'] = device_id

    data, status = await spotify_request(
        request, '/me/player/repeat', params=params, method='PUT'
    )
    if status in [204, 202, 200]:
        return {'success': True}
    raise HTTPException(status_code=status, detail='Repeat failed')
