/**
 * Spotify Win98 Rendering Utilities
 * Renders data visualizations using Win98 HTML components
 */

const SpotifyASCII = (function() {
    /**
     * Format duration in mm:ss
     * @param {number} ms - Duration in milliseconds
     * @returns {string} Formatted duration
     */
    function formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Render a Win98 progress bar (chunked blue fill in sunken container)
     * @param {number} percent - Value from 0-100
     * @returns {string} HTML string
     */
    function renderProgressBar(percent) {
        return `<div class="w98-progress"><div class="w98-progress__fill" style="width: ${Math.round(percent)}%"></div></div>`;
    }

    /**
     * Render genre bars section
     * @param {Array} genres - Array of {name, percent} objects
     * @returns {string} HTML string
     */
    function renderGenreBars(genres) {
        if (!genres || genres.length === 0) {
            return '<div class="empty-state">No genre data available</div>';
        }

        return `
            <div class="w98-bar-list">
                ${genres.map(genre => `
                    <div class="w98-bar-row">
                        <span class="w98-bar-row__label" title="${escapeHtml(genre.name)}">${escapeHtml(genre.name)}</span>
                        ${renderProgressBar(genre.percent)}
                        <span class="w98-bar-row__value">${genre.percent}%</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render listening patterns (day bars + peak hours)
     * @param {number[]} dayData - Array of 7 values (Sun-Sat)
     * @param {Array} peakHours - Array of {hour, count} objects
     * @returns {string} HTML string
     */
    function renderListeningPatterns(dayData, peakHours) {
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const maxDay = Math.max(...dayData, 1);

        return `
            <div class="w98-patterns">
                <div class="w98-patterns__days">
                    <div style="font-weight: bold; margin-bottom: 4px;">By Day</div>
                    <div class="w98-bar-list">
                        ${days.map((day, i) => {
                            const percent = (dayData[i] / maxDay) * 100;
                            return `
                                <div class="w98-bar-row">
                                    <span class="w98-bar-row__label">${day}</span>
                                    ${renderProgressBar(percent)}
                                    <span class="w98-bar-row__value">${dayData[i]}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                <div class="w98-patterns__peaks">
                    <div style="font-weight: bold; margin-bottom: 4px;">Peak Hours</div>
                    <div class="w98-listview">
                        ${peakHours.slice(0, 5).map((peak, i) => `
                            <div class="w98-listview__item">
                                <span style="font-family: monospace; min-width: 40px;">${String(peak.hour).padStart(2, '0')}:00</span>
                                <span style="flex: 1;">${peak.count} tracks</span>
                                <span style="color: var(--win98-dark-gray);">${i === 0 ? 'Peak' : '#' + (i + 1)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render vertical activity chart as Win98 bar columns
     * @param {number[]} hourData - Array of 24 values (hours 0-23)
     * @returns {string} HTML string
     */
    function renderActivityChart(hourData) {
        const max = Math.max(...hourData, 1);

        return `
            <div class="w98-activity">
                <div class="w98-activity__bars">
                    ${hourData.map((val, h) => {
                        const pct = (val / max) * 100;
                        return `
                            <div class="w98-activity__col" title="${h}:00 - ${val} tracks">
                                <div class="w98-activity__bar-wrap">
                                    <div class="w98-activity__bar-fill" style="height: ${pct}%"></div>
                                </div>
                                <span class="w98-activity__label">${h % 4 === 0 ? h : ''}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render track list as Win98 listview
     * @param {Array} tracks - Array of track objects from Spotify API
     * @param {number} limit - Max tracks to show
     * @param {boolean} playable - Whether tracks should be clickable for playback
     * @returns {string} HTML string
     */
    function renderTrackList(tracks, limit = 8, playable = true) {
        if (!tracks || tracks.length === 0) {
            return '<div class="empty-state">No tracks found</div>';
        }

        return `
            <div class="w98-listview">
                ${tracks.slice(0, limit).map((track, i) => `
                    <div class="w98-listview__item${playable ? ' track-item--playable' : ''}" ${playable ? `data-track-uri="${track.uri}"` : ''}>
                        <span class="w98-listview__rank">${String(i + 1).padStart(2, '0')}</span>
                        <img src="${track.album.images[2]?.url || ''}" alt="" class="w98-listview__art">
                        <div class="w98-listview__info">
                            <div class="w98-listview__name">${escapeHtml(track.name)}</div>
                            <div class="w98-listview__sub">${escapeHtml(track.artists[0].name)}</div>
                        </div>
                        <span class="w98-listview__duration">${formatDuration(track.duration_ms)}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render artist list as Win98 listview with images and genre subtitle
     * @param {Array} artists - Array of artist objects from Spotify API
     * @param {number} limit - Max artists to show
     * @returns {string} HTML string
     */
    function renderArtistList(artists, limit = 10) {
        if (!artists || artists.length === 0) {
            return '<div class="empty-state">No artists found</div>';
        }

        return `
            <div class="w98-listview">
                ${artists.slice(0, limit).map((artist, i) => `
                    <div class="w98-listview__item">
                        <span class="w98-listview__rank">${String(i + 1).padStart(2, '0')}</span>
                        ${artist.images && artist.images.length > 0
                            ? `<img src="${artist.images[artist.images.length - 1].url}" alt="" class="w98-listview__art">`
                            : ''}
                        <div class="w98-listview__info">
                            <div class="w98-listview__name">${escapeHtml(artist.name)}</div>
                            <div class="w98-listview__sub">${escapeHtml((artist.genres || []).slice(0, 2).join(', ') || 'Unknown genre')}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Format a relative timestamp (e.g. "5 min ago")
     * @param {string} isoDate - ISO date string
     * @returns {string} Relative time string
     */
    function formatRelativeTime(isoDate) {
        const now = Date.now();
        const then = new Date(isoDate).getTime();
        const diffMs = now - then;
        const diffMin = Math.floor(diffMs / 60000);

        if (diffMin < 1) return 'just now';
        if (diffMin < 60) return `${diffMin} min ago`;
        const diffHr = Math.floor(diffMin / 60);
        if (diffHr < 24) return `${diffHr}h ago`;
        const diffDay = Math.floor(diffHr / 24);
        return `${diffDay}d ago`;
    }

    /**
     * Render recently played tracks as Win98 listview with relative timestamps
     * @param {Array} items - Array of recently played items from Spotify API
     * @param {number} limit - Max tracks to show
     * @returns {string} HTML string
     */
    function renderRecentTracks(items, limit = 10) {
        if (!items || items.length === 0) {
            return '<div class="empty-state">No recent tracks</div>';
        }

        return `
            <div class="w98-listview">
                ${items.slice(0, limit).map(item => {
                    const track = item.track;
                    return `
                        <div class="w98-listview__item track-item--playable" data-track-uri="${track.uri}">
                            <img src="${track.album.images[2]?.url || ''}" alt="" class="w98-listview__art">
                            <div class="w98-listview__info">
                                <div class="w98-listview__name">${escapeHtml(track.name)}</div>
                                <div class="w98-listview__sub">${escapeHtml(track.artists[0].name)}</div>
                            </div>
                            <span class="w98-listview__duration">${formatRelativeTime(item.played_at)}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    /**
     * Render taste evolution (top artists by time period)
     * @param {Object} data - Object with short_term, medium_term, long_term keys
     * @returns {string} HTML string
     */
    function renderTasteEvolution(data) {
        const periods = [
            { key: 'short_term', label: '4 Weeks' },
            { key: 'medium_term', label: '6 Months' },
            { key: 'long_term', label: 'All Time' }
        ];

        return `
            <div class="w98-evolution">
                ${periods.map(period => {
                    const periodData = data[period.key];
                    if (!periodData || !periodData.artists || periodData.artists.length === 0) {
                        return `
                            <div class="w98-evolution__period">
                                <div class="win98-groupbox">
                                    <span class="win98-groupbox-label">${period.label}</span>
                                    <div class="empty-state">No data</div>
                                </div>
                            </div>
                        `;
                    }
                    return `
                        <div class="w98-evolution__period">
                            <div class="win98-groupbox">
                                <span class="win98-groupbox-label">${period.label}</span>
                                <div class="w98-listview">
                                    ${periodData.artists.slice(0, 5).map((artist, i) => `
                                        <div class="w98-listview__item">
                                            <span class="w98-listview__rank">${i + 1}.</span>
                                            ${artist.image ? `<img src="${artist.image}" alt="" class="w98-listview__artist-img">` : ''}
                                            <span class="w98-listview__name">${escapeHtml(artist.name)}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    // Public API
    return {
        formatDuration,
        escapeHtml,
        renderGenreBars,
        renderListeningPatterns,
        renderActivityChart,
        renderTrackList,
        renderArtistList,
        renderRecentTracks,
        renderTasteEvolution
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpotifyASCII;
}
