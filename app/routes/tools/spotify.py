"""
Spotify Listening Trends Tool
Visualizes recently played tracks and top artists/tracks.
"""
from flask import render_template, redirect, url_for, session, request, jsonify
import requests

from app.routes.tools import bp, register_tool
from app.services.oauth import SpotifyOAuth, require_oauth
from app.services.rate_limit import rate_limit

# Register this tool with the framework
register_tool({
    'id': 'spotify',
    'name': 'Spotify Listening Trends',
    'description': 'Visualize your listening habits with charts and stats',
    'icon': 'music',
    'tags': ['API', 'Charts', 'Music'],
    'requires_auth': True,
})

spotify_oauth = SpotifyOAuth()


@bp.route('/spotify')
def spotify_index():
    """Spotify tool main page."""
    is_authenticated = 'spotify_access_token' in session
    is_configured = spotify_oauth.is_configured
    return render_template('tools/spotify/index.html',
                           is_authenticated=is_authenticated,
                           is_configured=is_configured)


@bp.route('/spotify/auth')
def spotify_auth():
    """Initiate Spotify OAuth flow."""
    redirect_uri = url_for('tools.spotify_callback', _external=True)
    auth_url = spotify_oauth.get_auth_url(redirect_uri)
    return redirect(auth_url)


@bp.route('/spotify/callback')
def spotify_callback():
    """Handle Spotify OAuth callback."""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return redirect(url_for('tools.spotify_index'))

    redirect_uri = url_for('tools.spotify_callback', _external=True)
    tokens = spotify_oauth.exchange_code(code, redirect_uri)

    session['spotify_access_token'] = tokens.get('access_token')
    session['spotify_refresh_token'] = tokens.get('refresh_token')

    return redirect(url_for('tools.spotify_index'))


@bp.route('/spotify/logout')
def spotify_logout():
    """Clear Spotify session."""
    session.pop('spotify_access_token', None)
    session.pop('spotify_refresh_token', None)
    return redirect(url_for('tools.spotify_index'))


def _refresh_spotify_token():
    """Refresh Spotify access token if we have a refresh token."""
    refresh_token = session.get('spotify_refresh_token')
    if not refresh_token:
        return None
    tokens = spotify_oauth.refresh_token(refresh_token)
    if 'access_token' in tokens:
        session['spotify_access_token'] = tokens['access_token']
        return tokens['access_token']
    return None


def _spotify_request(endpoint, params=None):
    """Make a Spotify API request with automatic token refresh."""
    token = session.get('spotify_access_token')
    if not token:
        return None, 401

    response = requests.get(
        f'https://api.spotify.com/v1{endpoint}',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code == 401:
        # Token expired, try refresh
        new_token = _refresh_spotify_token()
        if new_token:
            response = requests.get(
                f'https://api.spotify.com/v1{endpoint}',
                params=params,
                headers={'Authorization': f'Bearer {new_token}'}
            )

    return response.json() if response.ok else None, response.status_code


@bp.route('/spotify/api/recent')
@require_oauth('spotify')
@rate_limit(max_requests=30, window_seconds=60)
def spotify_recent():
    """API endpoint: Get recently played tracks."""
    data, status = _spotify_request('/me/player/recently-played', {'limit': 50})
    if data is None:
        return jsonify({'error': 'Failed to fetch data'}), status
    return jsonify(data)


@bp.route('/spotify/api/top/<time_range>')
@require_oauth('spotify')
@rate_limit(max_requests=30, window_seconds=60)
def spotify_top(time_range):
    """API endpoint: Get top tracks/artists."""
    # time_range: short_term (4 weeks), medium_term (6 months), long_term (years)
    if time_range not in ['short_term', 'medium_term', 'long_term']:
        time_range = 'medium_term'

    tracks_data, _ = _spotify_request('/me/top/tracks', {
        'limit': 20,
        'time_range': time_range
    })

    artists_data, _ = _spotify_request('/me/top/artists', {
        'limit': 10,
        'time_range': time_range
    })

    return jsonify({
        'tracks': tracks_data,
        'artists': artists_data
    })


@bp.route('/spotify/api/now-playing')
@require_oauth('spotify')
@rate_limit(max_requests=60, window_seconds=60)
def spotify_now_playing():
    """API endpoint: Get currently playing track."""
    data, status = _spotify_request('/me/player/currently-playing')

    if status == 204 or data is None:
        # Nothing playing
        return jsonify({'is_playing': False})

    if not data.get('item'):
        return jsonify({'is_playing': False})

    track = data['item']
    return jsonify({
        'is_playing': data.get('is_playing', False),
        'track': {
            'name': track.get('name'),
            'artist': track['artists'][0]['name'] if track.get('artists') else 'Unknown',
            'album': track.get('album', {}).get('name'),
            'image': track.get('album', {}).get('images', [{}])[0].get('url'),
            'duration_ms': track.get('duration_ms', 0),
            'progress_ms': data.get('progress_ms', 0),
        }
    })


@bp.route('/spotify/api/genres')
@require_oauth('spotify')
@rate_limit(max_requests=30, window_seconds=60)
def spotify_genres():
    """API endpoint: Get genre breakdown from top artists."""
    artists_data, _ = _spotify_request('/me/top/artists', {
        'limit': 50,
        'time_range': 'medium_term'
    })

    if not artists_data or 'items' not in artists_data:
        return jsonify({'genres': []})

    # Count genre occurrences
    genre_counts = {}
    for artist in artists_data['items']:
        for genre in artist.get('genres', []):
            genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Sort by count and take top 8
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    total = sum(count for _, count in sorted_genres)

    genres = [
        {'name': genre, 'count': count, 'percent': round(count / total * 100) if total > 0 else 0}
        for genre, count in sorted_genres
    ]

    return jsonify({'genres': genres})


@bp.route('/spotify/api/audio-features')
@require_oauth('spotify')
@rate_limit(max_requests=30, window_seconds=60)
def spotify_audio_features():
    """API endpoint: Get average audio features from top tracks."""
    tracks_data, _ = _spotify_request('/me/top/tracks', {
        'limit': 50,
        'time_range': 'medium_term'
    })

    if not tracks_data or 'items' not in tracks_data:
        return jsonify({'features': None})

    # Get track IDs
    track_ids = [track['id'] for track in tracks_data['items']]

    # Fetch audio features for all tracks
    features_data, _ = _spotify_request('/audio-features', {
        'ids': ','.join(track_ids)
    })

    if not features_data or 'audio_features' not in features_data:
        return jsonify({'features': None})

    # Calculate averages for key features
    feature_keys = ['danceability', 'energy', 'acousticness', 'valence', 'instrumentalness', 'liveness']
    totals = {key: 0 for key in feature_keys}
    count = 0

    for features in features_data['audio_features']:
        if features:
            count += 1
            for key in feature_keys:
                totals[key] += features.get(key, 0)

    if count == 0:
        return jsonify({'features': None})

    averages = {key: round(totals[key] / count * 100) for key in feature_keys}

    return jsonify({'features': averages})


@bp.route('/spotify/api/taste-evolution')
@require_oauth('spotify')
@rate_limit(max_requests=30, window_seconds=60)
def spotify_taste_evolution():
    """API endpoint: Compare top artists across time periods."""
    periods = ['short_term', 'medium_term', 'long_term']
    period_labels = {'short_term': '4 Weeks', 'medium_term': '6 Months', 'long_term': 'All Time'}

    evolution = {}

    for period in periods:
        artists_data, _ = _spotify_request('/me/top/artists', {
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

    return jsonify(evolution)
