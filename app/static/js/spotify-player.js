/**
 * Spotify Web Playback SDK Integration
 * Handles player initialization, state management, and UI updates
 */

const SpotifyPlayer = (function() {
    // State
    let player = null;
    let deviceId = null;
    let currentState = null;
    let isExpanded = false;
    let pollInterval = null;

    // DOM Elements (cached after init)
    let elements = {};

    // ASCII progress bar characters
    const PROGRESS_FILLED = '\u2501';  // ━
    const PROGRESS_EMPTY = '\u2500';   // ─

    /**
     * Initialize the player bar UI and SDK
     */
    function init() {
        cacheElements();
        attachEventListeners();
        loadSavedPreferences();

        // Load Spotify SDK
        if (!window.Spotify) {
            loadSpotifySDK();
        } else {
            initializePlayer();
        }

        // Start polling for playback state
        startStatePolling();
    }

    /**
     * Cache DOM element references
     */
    function cacheElements() {
        elements = {
            playerBar: document.getElementById('player-bar'),
            expandToggle: document.getElementById('player-expand-toggle'),
            albumArt: document.getElementById('player-album-art'),
            trackName: document.getElementById('player-track-name'),
            artistName: document.getElementById('player-artist-name'),
            albumName: document.getElementById('player-album-name'),
            prevBtn: document.getElementById('player-prev'),
            playPauseBtn: document.getElementById('player-play-pause'),
            nextBtn: document.getElementById('player-next'),
            progressBar: document.getElementById('player-progress-bar'),
            progressFill: document.getElementById('player-progress-fill'),
            currentTime: document.getElementById('player-current-time'),
            totalTime: document.getElementById('player-total-time'),
            volumeSlider: document.getElementById('player-volume'),
            volumeValue: document.getElementById('player-volume-value'),
            shuffleBtn: document.getElementById('player-shuffle'),
            repeatBtn: document.getElementById('player-repeat'),
            devicesBtn: document.getElementById('player-devices'),
            devicesDropdown: document.getElementById('player-devices-dropdown'),
            devicesList: document.getElementById('player-devices-list'),
            connectMessage: document.getElementById('player-connect-message'),
            playerContent: document.getElementById('player-content')
        };
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        // Expand/collapse toggle
        if (elements.expandToggle) {
            elements.expandToggle.addEventListener('click', toggleExpanded);
        }

        // Playback controls
        if (elements.prevBtn) elements.prevBtn.addEventListener('click', previous);
        if (elements.playPauseBtn) elements.playPauseBtn.addEventListener('click', togglePlayPause);
        if (elements.nextBtn) elements.nextBtn.addEventListener('click', next);

        // Progress bar seeking
        if (elements.progressBar) {
            elements.progressBar.addEventListener('click', handleSeek);
        }

        // Volume control
        if (elements.volumeSlider) {
            elements.volumeSlider.addEventListener('input', handleVolumeChange);
        }

        // Shuffle and repeat
        if (elements.shuffleBtn) elements.shuffleBtn.addEventListener('click', toggleShuffle);
        if (elements.repeatBtn) elements.repeatBtn.addEventListener('click', cycleRepeat);

        // Devices dropdown
        if (elements.devicesBtn) {
            elements.devicesBtn.addEventListener('click', toggleDevicesDropdown);
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (elements.devicesDropdown &&
                !elements.devicesDropdown.contains(e.target) &&
                !elements.devicesBtn.contains(e.target)) {
                elements.devicesDropdown.classList.remove('active');
            }
        });
    }

    /**
     * Load Spotify SDK script
     */
    function loadSpotifySDK() {
        window.onSpotifyWebPlaybackSDKReady = initializePlayer;

        const script = document.createElement('script');
        script.src = 'https://sdk.scdn.co/spotify-player.js';
        script.async = true;
        document.body.appendChild(script);
    }

    /**
     * Initialize Spotify Player instance
     */
    async function initializePlayer() {
        try {
            const tokenResponse = await fetch('/projects/spotify/api/token');
            const tokenData = await tokenResponse.json();

            if (!tokenData.access_token) {
                showConnectMessage('Authentication required');
                return;
            }

            player = new Spotify.Player({
                name: 'Personal Site Player',
                getOAuthToken: async cb => {
                    const response = await fetch('/projects/spotify/api/token');
                    const data = await response.json();
                    cb(data.access_token);
                },
                volume: getSavedVolume()
            });

            // Error handling
            player.addListener('initialization_error', ({ message }) => {
                console.error('Initialization error:', message);
                showConnectMessage('Player initialization failed');
            });

            player.addListener('authentication_error', ({ message }) => {
                console.error('Authentication error:', message);
                showConnectMessage('Authentication error - please reconnect');
            });

            player.addListener('account_error', ({ message }) => {
                console.error('Account error:', message);
                showConnectMessage('Spotify Premium required');
            });

            player.addListener('playback_error', ({ message }) => {
                console.error('Playback error:', message);
            });

            // Ready
            player.addListener('ready', ({ device_id }) => {
                console.log('Player ready with device ID:', device_id);
                deviceId = device_id;
                hideConnectMessage();
                loadDevices();
            });

            // Not ready
            player.addListener('not_ready', ({ device_id }) => {
                console.log('Player not ready:', device_id);
                showConnectMessage('Player disconnected');
            });

            // State changes
            player.addListener('player_state_changed', state => {
                if (state) {
                    currentState = state;
                    updateUI(state);
                }
            });

            // Connect
            const connected = await player.connect();
            if (!connected) {
                showConnectMessage('Failed to connect');
            }

        } catch (error) {
            console.error('Player init error:', error);
            showConnectMessage('Failed to initialize player');
        }
    }

    /**
     * Start polling for playback state (for external device changes)
     */
    function startStatePolling() {
        pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/projects/spotify/api/playback-state');
                if (response.status === 401) {
                    console.warn('Playback polling: authentication expired');
                    showConnectMessage('Session expired - please reconnect');
                    clearInterval(pollInterval);
                    return;
                }
                if (!response.ok) return;
                const state = await response.json();
                if (state && state.item) {
                    updateUIFromAPIState(state);
                }
            } catch (error) {
                console.error('Playback polling error:', error);
            }
        }, 3000);
    }

    /**
     * Update UI from SDK state
     */
    function updateUI(state) {
        if (!state || !state.track_window) return;

        const track = state.track_window.current_track;
        if (!track) return;

        // Update track info
        if (elements.trackName) elements.trackName.textContent = track.name;
        if (elements.artistName) elements.artistName.textContent = track.artists.map(a => a.name).join(', ');
        if (elements.albumName) elements.albumName.textContent = track.album.name;

        // Update album art
        if (elements.albumArt && track.album.images.length > 0) {
            elements.albumArt.src = track.album.images[0].url;
            elements.albumArt.style.display = 'block';
        }

        // Update play/pause button
        updatePlayPauseButton(!state.paused);

        // Update progress
        updateProgress(state.position, state.duration);

        // Update shuffle/repeat
        if (elements.shuffleBtn) {
            elements.shuffleBtn.classList.toggle('active', state.shuffle);
        }
        if (elements.repeatBtn) {
            updateRepeatButton(state.repeat_mode);
        }

        // Show player content
        if (elements.playerContent) elements.playerContent.style.display = 'flex';
        if (elements.connectMessage) elements.connectMessage.style.display = 'none';
    }

    /**
     * Update UI from API state (for external devices)
     */
    function updateUIFromAPIState(state) {
        if (!state || !state.item) return;

        const track = state.item;

        // Update track info
        if (elements.trackName) elements.trackName.textContent = track.name;
        if (elements.artistName) elements.artistName.textContent = track.artists.map(a => a.name).join(', ');
        if (elements.albumName) elements.albumName.textContent = track.album.name;

        // Update album art
        if (elements.albumArt && track.album.images.length > 0) {
            elements.albumArt.src = track.album.images[0].url;
            elements.albumArt.style.display = 'block';
        }

        // Update play/pause button
        updatePlayPauseButton(state.is_playing);

        // Update progress
        updateProgress(state.progress_ms, track.duration_ms);

        // Update shuffle/repeat
        if (elements.shuffleBtn) {
            elements.shuffleBtn.classList.toggle('active', state.shuffle_state);
        }
        if (elements.repeatBtn) {
            const repeatMap = { 'off': 0, 'context': 1, 'track': 2 };
            updateRepeatButton(repeatMap[state.repeat_state] || 0);
        }

        // Show player content
        if (elements.playerContent) elements.playerContent.style.display = 'flex';
        if (elements.connectMessage) elements.connectMessage.style.display = 'none';
    }

    /**
     * Update play/pause button state
     */
    function updatePlayPauseButton(isPlaying) {
        if (!elements.playPauseBtn) return;
        elements.playPauseBtn.textContent = isPlaying ? '\u275A\u275A' : '\u25B6';
        elements.playPauseBtn.setAttribute('aria-label', isPlaying ? 'Pause' : 'Play');
    }

    /**
     * Update repeat button state
     */
    function updateRepeatButton(mode) {
        if (!elements.repeatBtn) return;
        elements.repeatBtn.classList.remove('active', 'repeat-one');
        if (mode === 1) {
            elements.repeatBtn.classList.add('active');
            elements.repeatBtn.textContent = '\u21BB';
        } else if (mode === 2) {
            elements.repeatBtn.classList.add('active', 'repeat-one');
            elements.repeatBtn.textContent = '\u21BB1';
        } else {
            elements.repeatBtn.textContent = '\u21BB';
        }
    }

    /**
     * Update progress bar and time display
     */
    function updateProgress(position, duration) {
        if (!duration) return;

        const percent = (position / duration) * 100;

        // Update fill bar
        if (elements.progressFill) {
            elements.progressFill.style.width = percent + '%';
        }

        // Update time displays
        if (elements.currentTime) {
            elements.currentTime.textContent = formatTime(position);
        }
        if (elements.totalTime) {
            elements.totalTime.textContent = formatTime(duration);
        }
    }

    /**
     * Format milliseconds to mm:ss
     */
    function formatTime(ms) {
        const seconds = Math.floor(ms / 1000);
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return mins + ':' + secs.toString().padStart(2, '0');
    }

    /**
     * Toggle expanded/collapsed state
     */
    function toggleExpanded() {
        isExpanded = !isExpanded;
        if (elements.playerBar) {
            elements.playerBar.classList.toggle('expanded', isExpanded);
        }
        if (elements.expandToggle) {
            elements.expandToggle.textContent = isExpanded ? '\u25BC' : '\u25B2';
        }
        localStorage.setItem('spotify_player_expanded', isExpanded);
    }

    /**
     * Toggle play/pause
     */
    async function togglePlayPause() {
        if (player && currentState) {
            await player.togglePlay();
        } else {
            // Use API for external devices
            const state = await fetchPlaybackState();
            if (state && state.is_playing) {
                await apiRequest('/api/pause', 'POST');
            } else {
                await apiRequest('/api/play', 'POST');
            }
        }
    }

    /**
     * Skip to next track
     */
    async function next() {
        if (player && currentState) {
            await player.nextTrack();
        } else {
            await apiRequest('/api/next', 'POST');
        }
    }

    /**
     * Skip to previous track
     */
    async function previous() {
        if (player && currentState) {
            await player.previousTrack();
        } else {
            await apiRequest('/api/previous', 'POST');
        }
    }

    /**
     * Handle progress bar click for seeking
     */
    async function handleSeek(e) {
        const rect = elements.progressBar.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        const duration = currentState ? currentState.duration : 0;

        if (duration) {
            const position = Math.floor(percent * duration);
            if (player && currentState) {
                await player.seek(position);
            } else {
                await apiRequest('/api/seek', 'POST', { position_ms: position });
            }
        }
    }

    /**
     * Handle volume slider change
     */
    async function handleVolumeChange(e) {
        const volume = parseInt(e.target.value) / 100;
        if (elements.volumeValue) {
            elements.volumeValue.textContent = Math.round(volume * 100) + '%';
        }
        localStorage.setItem('spotify_player_volume', volume);

        if (player) {
            await player.setVolume(volume);
        } else {
            await apiRequest('/api/volume', 'POST', { volume_percent: Math.round(volume * 100) });
        }
    }

    /**
     * Toggle shuffle
     */
    async function toggleShuffle() {
        const newState = !elements.shuffleBtn.classList.contains('active');
        elements.shuffleBtn.classList.toggle('active', newState);
        await apiRequest('/api/shuffle', 'POST', { state: newState });
    }

    /**
     * Cycle through repeat modes
     */
    async function cycleRepeat() {
        const states = ['off', 'context', 'track'];
        let currentIndex = 0;

        if (elements.repeatBtn.classList.contains('repeat-one')) {
            currentIndex = 2;
        } else if (elements.repeatBtn.classList.contains('active')) {
            currentIndex = 1;
        }

        const nextIndex = (currentIndex + 1) % 3;
        const nextState = states[nextIndex];

        updateRepeatButton(nextIndex);
        await apiRequest('/api/repeat', 'POST', { state: nextState });
    }

    /**
     * Toggle devices dropdown
     */
    async function toggleDevicesDropdown() {
        const isActive = elements.devicesDropdown.classList.toggle('active');
        if (isActive) {
            await loadDevices();
        }
    }

    /**
     * Load available devices
     */
    async function loadDevices() {
        try {
            const response = await fetch('/projects/spotify/api/devices');
            const data = await response.json();
            renderDevicesList(data.devices || []);
        } catch (error) {
            console.error('Failed to load devices:', error);
        }
    }

    /**
     * Render devices list
     */
    function renderDevicesList(devices) {
        if (!elements.devicesList) return;

        if (devices.length === 0) {
            elements.devicesList.textContent = 'No devices found';
            return;
        }

        // Clear existing content
        elements.devicesList.textContent = '';

        devices.forEach(device => {
            const item = document.createElement('div');
            item.className = 'device-item' + (device.is_active ? ' active' : '');

            const indicator = document.createElement('span');
            indicator.className = 'device-indicator';
            indicator.textContent = device.is_active ? '\u25CF' : '\u25CB';

            const name = document.createElement('span');
            name.className = 'device-name';
            name.textContent = device.name;

            const type = document.createElement('span');
            type.className = 'device-type';
            type.textContent = getDeviceTypeLabel(device.type);

            item.appendChild(indicator);
            item.appendChild(name);
            item.appendChild(type);

            item.addEventListener('click', () => transferToDevice(device.id));
            elements.devicesList.appendChild(item);
        });
    }

    /**
     * Get device type label
     */
    function getDeviceTypeLabel(type) {
        const labels = {
            'Computer': '[computer]',
            'Smartphone': '[phone]',
            'Speaker': '[speaker]',
            'TV': '[tv]',
            'AVR': '[avr]',
            'STB': '[stb]',
            'AudioDongle': '[dongle]',
            'GameConsole': '[game]',
            'CastVideo': '[cast]',
            'CastAudio': '[cast]',
            'Automobile': '[car]',
            'Unknown': '[device]'
        };
        return labels[type] || '[device]';
    }

    /**
     * Transfer playback to a device
     */
    async function transferToDevice(targetDeviceId) {
        try {
            await apiRequest('/api/transfer', 'POST', { device_id: targetDeviceId });
            elements.devicesDropdown.classList.remove('active');
            await loadDevices();
        } catch (error) {
            console.error('Failed to transfer playback:', error);
        }
    }

    /**
     * Play a specific track
     */
    async function playTrack(trackUri) {
        await apiRequest('/api/play', 'POST', {
            uris: [trackUri],
            device_id: deviceId
        });
    }

    /**
     * Show connect message
     */
    function showConnectMessage(message) {
        if (elements.connectMessage) {
            elements.connectMessage.textContent = message || 'Connect to enable playback';
            elements.connectMessage.style.display = 'flex';
        }
        if (elements.playerContent) {
            elements.playerContent.style.display = 'none';
        }
    }

    /**
     * Hide connect message
     */
    function hideConnectMessage() {
        if (elements.connectMessage) {
            elements.connectMessage.style.display = 'none';
        }
        if (elements.playerContent) {
            elements.playerContent.style.display = 'flex';
        }
    }

    /**
     * Fetch current playback state from API
     */
    async function fetchPlaybackState() {
        try {
            const response = await fetch('/projects/spotify/api/playback-state');
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    /**
     * Make API request
     */
    async function apiRequest(endpoint, method, body) {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        const response = await fetch('/projects/spotify' + endpoint, options);
        if (!response.ok) {
            console.error('API request failed:', endpoint, response.status);
            return { error: true, status: response.status };
        }
        if (response.status === 204) return {};
        return response.json();
    }

    /**
     * Load saved preferences
     */
    function loadSavedPreferences() {
        // Expanded state
        const savedExpanded = localStorage.getItem('spotify_player_expanded');
        if (savedExpanded === 'true') {
            isExpanded = true;
            if (elements.playerBar) elements.playerBar.classList.add('expanded');
            if (elements.expandToggle) elements.expandToggle.textContent = '\u25BC';
        }

        // Volume
        const savedVolume = getSavedVolume();
        if (elements.volumeSlider) {
            elements.volumeSlider.value = savedVolume * 100;
        }
        if (elements.volumeValue) {
            elements.volumeValue.textContent = Math.round(savedVolume * 100) + '%';
        }
    }

    /**
     * Get saved volume (0-1)
     */
    function getSavedVolume() {
        const saved = localStorage.getItem('spotify_player_volume');
        return saved ? parseFloat(saved) : 0.5;
    }

    /**
     * Cleanup on page unload
     */
    function cleanup() {
        if (pollInterval) clearInterval(pollInterval);
        if (player) player.disconnect();
    }

    // Public API
    return {
        init: init,
        playTrack: playTrack,
        cleanup: cleanup
    };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', SpotifyPlayer.init);
} else {
    SpotifyPlayer.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', SpotifyPlayer.cleanup);
