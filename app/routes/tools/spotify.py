"""
Spotify Listening Trends Tool
Visualizes recently played tracks and top artists/tracks.
"""
import secrets

from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from app.routes.tools import router, register_tool
from app.services.spotify_helpers import spotify_oauth, require_oauth, spotify_request
from app.services.rate_limit import rate_limit
from app.templating import templates

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
    tokens = await spotify_oauth.exchange_code(code, redirect_uri)

    request.session['spotify_access_token'] = tokens.get('access_token')
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


@router.get('/spotify/api/recent', name='tools.spotify_recent',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def spotify_recent(request: Request):
    """API endpoint: Get recently played tracks."""
    require_oauth(request)
    data, status = await spotify_request(request, '/me/player/recently-played', {'limit': 50})
    if data is None:
        raise HTTPException(status_code=status, detail='Failed to fetch data')
    return data


@router.get('/spotify/api/top/{time_range}', name='tools.spotify_top',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def spotify_top(request: Request, time_range: str):
    """API endpoint: Get top tracks/artists."""
    require_oauth(request)
    if time_range not in ['short_term', 'medium_term', 'long_term']:
        time_range = 'medium_term'

    tracks_data, _ = await spotify_request(request, '/me/top/tracks', {
        'limit': 20,
        'time_range': time_range
    })

    artists_data, _ = await spotify_request(request, '/me/top/artists', {
        'limit': 10,
        'time_range': time_range
    })

    return {'tracks': tracks_data, 'artists': artists_data}


@router.get('/spotify/api/now-playing', name='tools.spotify_now_playing',
            dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))])
async def spotify_now_playing(request: Request):
    """API endpoint: Get currently playing track."""
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
async def spotify_genres(request: Request):
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


@router.get('/spotify/api/audio-features', name='tools.spotify_audio_features',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def spotify_audio_features(request: Request):
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


@router.get('/spotify/api/taste-evolution', name='tools.spotify_taste_evolution',
            dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def spotify_taste_evolution(request: Request):
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
