"""
Spotify Listening Trends
Visualizes recently played tracks and top artists/tracks.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
import requests
import os

bp = Blueprint('spotify', __name__, url_prefix='/projects/spotify')


class SpotifyOAuth:
    """Simple Spotify OAuth handler."""

    def __init__(self):
        self.client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        self.client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        self.scope = (
            'user-read-recently-played '
            'user-top-read '
            'user-read-currently-playing '
            'user-read-playback-state '
            'user-modify-playback-state '
            'streaming'
        )

    @property
    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def get_auth_url(self, redirect_uri):
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': self.scope,
        }
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'https://accounts.spotify.com/authorize?{query}'

    def exchange_code(self, code, redirect_uri):
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
        )
        return response.json() if response.ok else {}

    def refresh_token(self, refresh_token):
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
        )
        return response.json() if response.ok else {}


spotify_oauth = SpotifyOAuth()


def require_oauth(f):
    """Decorator to require Spotify OAuth."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'spotify_access_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated


@bp.route('/')
def index():
    """Spotify dashboard main page."""
    is_authenticated = 'spotify_access_token' in session
    is_configured = spotify_oauth.is_configured
    return render_template('spotify/index.html',
                           is_authenticated=is_authenticated,
                           is_configured=is_configured)


@bp.route('/auth')
def auth():
    """Initiate Spotify OAuth flow."""
    redirect_uri = url_for('spotify.callback', _external=True)
    auth_url = spotify_oauth.get_auth_url(redirect_uri)
    return redirect(auth_url)


@bp.route('/callback')
def callback():
    """Handle Spotify OAuth callback."""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return redirect(url_for('spotify.index'))

    redirect_uri = url_for('spotify.callback', _external=True)
    tokens = spotify_oauth.exchange_code(code, redirect_uri)

    session['spotify_access_token'] = tokens.get('access_token')
    session['spotify_refresh_token'] = tokens.get('refresh_token')

    return redirect(url_for('spotify.index'))


@bp.route('/logout')
def logout():
    """Clear Spotify session."""
    session.pop('spotify_access_token', None)
    session.pop('spotify_refresh_token', None)
    return redirect(url_for('spotify.index'))


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
        new_token = _refresh_spotify_token()
        if new_token:
            response = requests.get(
                f'https://api.spotify.com/v1{endpoint}',
                params=params,
                headers={'Authorization': f'Bearer {new_token}'}
            )

    return response.json() if response.ok else None, response.status_code


@bp.route('/api/recent')
@require_oauth
def api_recent():
    """API endpoint: Get recently played tracks."""
    data, status = _spotify_request('/me/player/recently-played', {'limit': 50})
    if data is None:
        return jsonify({'error': 'Failed to fetch data'}), status
    return jsonify(data)


@bp.route('/api/top/<time_range>')
@require_oauth
def api_top(time_range):
    """API endpoint: Get top tracks/artists."""
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


@bp.route('/api/genres')
@require_oauth
def api_genres():
    """API endpoint: Get genre breakdown from top artists."""
    artists_data, _ = _spotify_request('/me/top/artists', {
        'limit': 50,
        'time_range': 'medium_term'
    })

    if not artists_data or 'items' not in artists_data:
        return jsonify({'genres': []})

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

    return jsonify({'genres': genres})


@bp.route('/api/audio-features')
@require_oauth
def api_audio_features():
    """API endpoint: Get average audio features from top tracks."""
    tracks_data, _ = _spotify_request('/me/top/tracks', {
        'limit': 50,
        'time_range': 'medium_term'
    })

    if not tracks_data or 'items' not in tracks_data:
        return jsonify({'features': None})

    track_ids = [track['id'] for track in tracks_data['items']]

    features_data, _ = _spotify_request('/audio-features', {
        'ids': ','.join(track_ids)
    })

    if not features_data or 'audio_features' not in features_data:
        return jsonify({'features': None})

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


@bp.route('/api/taste-evolution')
@require_oauth
def api_taste_evolution():
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


# ===============================================
# Playback API Endpoints
# ===============================================

@bp.route('/api/token')
@require_oauth
def api_token():
    """Return access token for Web Playback SDK."""
    token = session.get('spotify_access_token')
    return jsonify({'access_token': token})


@bp.route('/api/playback-state')
@require_oauth
def api_playback_state():
    """Get current playback state."""
    data, status = _spotify_request('/me/player')
    if data is None:
        return jsonify({'is_playing': False, 'item': None}), 200
    return jsonify(data)


@bp.route('/api/devices')
@require_oauth
def api_devices():
    """Get available devices."""
    data, status = _spotify_request('/me/player/devices')
    if data is None:
        return jsonify({'devices': []}), status
    return jsonify(data)


@bp.route('/api/transfer', methods=['POST'])
@require_oauth
def api_transfer():
    """Transfer playback to a device."""
    token = session.get('spotify_access_token')
    device_id = request.json.get('device_id')

    response = requests.put(
        'https://api.spotify.com/v1/me/player',
        json={'device_ids': [device_id], 'play': True},
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code == 204:
        return jsonify({'success': True})
    return jsonify({'error': 'Transfer failed'}), response.status_code


@bp.route('/api/play', methods=['POST'])
@require_oauth
def api_play():
    """Start or resume playback."""
    token = session.get('spotify_access_token')
    data = request.json or {}

    params = {}
    if data.get('device_id'):
        params['device_id'] = data['device_id']

    body = {}
    if data.get('uris'):
        body['uris'] = data['uris']
    elif data.get('context_uri'):
        body['context_uri'] = data['context_uri']
        if data.get('offset'):
            body['offset'] = data['offset']

    response = requests.put(
        'https://api.spotify.com/v1/me/player/play',
        params=params if params else None,
        json=body if body else None,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Play failed'}), response.status_code


@bp.route('/api/pause', methods=['POST'])
@require_oauth
def api_pause():
    """Pause playback."""
    token = session.get('spotify_access_token')
    device_id = (request.json or {}).get('device_id')

    params = {'device_id': device_id} if device_id else None

    response = requests.put(
        'https://api.spotify.com/v1/me/player/pause',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Pause failed'}), response.status_code


@bp.route('/api/next', methods=['POST'])
@require_oauth
def api_next():
    """Skip to next track."""
    token = session.get('spotify_access_token')
    device_id = (request.json or {}).get('device_id')

    params = {'device_id': device_id} if device_id else None

    response = requests.post(
        'https://api.spotify.com/v1/me/player/next',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Skip failed'}), response.status_code


@bp.route('/api/previous', methods=['POST'])
@require_oauth
def api_previous():
    """Skip to previous track."""
    token = session.get('spotify_access_token')
    device_id = (request.json or {}).get('device_id')

    params = {'device_id': device_id} if device_id else None

    response = requests.post(
        'https://api.spotify.com/v1/me/player/previous',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Previous failed'}), response.status_code


@bp.route('/api/seek', methods=['POST'])
@require_oauth
def api_seek():
    """Seek to position in track."""
    token = session.get('spotify_access_token')
    data = request.json or {}
    position_ms = data.get('position_ms', 0)
    device_id = data.get('device_id')

    params = {'position_ms': position_ms}
    if device_id:
        params['device_id'] = device_id

    response = requests.put(
        'https://api.spotify.com/v1/me/player/seek',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Seek failed'}), response.status_code


@bp.route('/api/volume', methods=['POST'])
@require_oauth
def api_volume():
    """Set volume level."""
    token = session.get('spotify_access_token')
    data = request.json or {}
    volume_percent = data.get('volume_percent', 50)
    device_id = data.get('device_id')

    params = {'volume_percent': volume_percent}
    if device_id:
        params['device_id'] = device_id

    response = requests.put(
        'https://api.spotify.com/v1/me/player/volume',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Volume failed'}), response.status_code


@bp.route('/api/shuffle', methods=['POST'])
@require_oauth
def api_shuffle():
    """Toggle shuffle."""
    token = session.get('spotify_access_token')
    data = request.json or {}
    state = data.get('state', True)
    device_id = data.get('device_id')

    params = {'state': str(state).lower()}
    if device_id:
        params['device_id'] = device_id

    response = requests.put(
        'https://api.spotify.com/v1/me/player/shuffle',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Shuffle failed'}), response.status_code


@bp.route('/api/repeat', methods=['POST'])
@require_oauth
def api_repeat():
    """Set repeat mode (off, context, track)."""
    token = session.get('spotify_access_token')
    data = request.json or {}
    state = data.get('state', 'off')  # off, context, track
    device_id = data.get('device_id')

    params = {'state': state}
    if device_id:
        params['device_id'] = device_id

    response = requests.put(
        'https://api.spotify.com/v1/me/player/repeat',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code in [204, 202]:
        return jsonify({'success': True})
    return jsonify({'error': 'Repeat failed'}), response.status_code
