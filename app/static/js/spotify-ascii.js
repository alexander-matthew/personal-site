/**
 * Spotify ASCII Rendering Utilities
 * Renders data visualizations using ASCII block characters
 */

const SpotifyASCII = (function() {
    // ASCII block characters for density/fill
    const BLOCKS = {
        FULL: '\u2588',      // █
        LIGHT: '\u2591',     // ░
        MEDIUM: '\u2592',    // ▒
        DARK: '\u2593',      // ▓
        EMPTY: '\u00B7',     // ·
    };

    // Heatmap density characters (lowest to highest)
    const HEAT_CHARS = [BLOCKS.EMPTY, BLOCKS.LIGHT, BLOCKS.MEDIUM, BLOCKS.DARK, BLOCKS.FULL];

    /**
     * Render a horizontal ASCII bar
     * @param {number} percent - Value from 0-100
     * @param {number} width - Total width in characters (default 20)
     * @returns {string} ASCII bar string
     */
    function renderBar(percent, width = 20) {
        const filled = Math.round((percent / 100) * width);
        const empty = width - filled;
        return BLOCKS.FULL.repeat(filled) + BLOCKS.LIGHT.repeat(empty);
    }

    /**
     * Render a meter with brackets [████░░░░░░]
     * @param {number} percent - Value from 0-100
     * @param {number} width - Width inside brackets (default 10)
     * @returns {string} ASCII meter string
     */
    function renderMeter(percent, width = 10) {
        const filled = Math.round((percent / 100) * width);
        const empty = width - filled;
        return '[' + BLOCKS.FULL.repeat(filled) + BLOCKS.LIGHT.repeat(empty) + ']';
    }

    /**
     * Get heatmap character based on intensity
     * @param {number} value - Current value
     * @param {number} max - Maximum value
     * @returns {string} Single ASCII character
     */
    function getHeatChar(value, max) {
        if (value === 0 || max === 0) return HEAT_CHARS[0];
        const level = Math.min(4, Math.ceil((value / max) * 4));
        return HEAT_CHARS[level];
    }

    /**
     * Render a vertical bar chart row (for hourly activity)
     * Returns array of characters for one row (from top to bottom)
     * @param {number[]} values - Array of values
     * @param {number} maxHeight - Maximum height in rows
     * @returns {string[][]} 2D array [row][column] of characters
     */
    function renderVerticalChart(values, maxHeight = 8) {
        const max = Math.max(...values, 1);
        const rows = [];

        for (let row = maxHeight; row >= 1; row--) {
            const rowChars = values.map(val => {
                const height = Math.round((val / max) * maxHeight);
                return height >= row ? BLOCKS.FULL : ' ';
            });
            rows.push(rowChars);
        }

        return rows;
    }

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
     * Dispatch audio profile event for reactive background
     * @param {Object} features - Audio features object
     */
    function dispatchAudioProfile(features) {
        if (!features) return;

        window.dispatchEvent(new CustomEvent('audioProfileChange', {
            detail: {
                energy: features.energy || 50,
                danceability: features.danceability || 50,
                valence: features.valence || 50,
                acousticness: features.acousticness || 50,
                tempo: features.tempo || 120
            }
        }));
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
     * Render genre bars section
     * @param {Array} genres - Array of {name, percent} objects
     * @returns {string} HTML string
     */
    function renderGenreBars(genres) {
        if (!genres || genres.length === 0) {
            return '<div class="empty-state">No genre data available</div>';
        }

        return `
            <div class="ascii-bars">
                ${genres.map(genre => `
                    <div class="ascii-bar-row">
                        <span class="ascii-bar__label" title="${escapeHtml(genre.name)}">${escapeHtml(genre.name)}</span>
                        <span class="ascii-bar__blocks">${renderBar(genre.percent, 24)}</span>
                        <span class="ascii-bar__value">${genre.percent}%</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render audio profile panel
     * @param {Object} features - Audio features object with percentages
     * @returns {string} HTML string
     */
    function renderAudioProfile(features) {
        if (!features) {
            return '<div class="empty-state">No audio data available</div>';
        }

        const metrics = [
            { key: 'danceability', label: 'Danceability' },
            { key: 'energy', label: 'Energy' },
            { key: 'acousticness', label: 'Acousticness' },
            { key: 'valence', label: 'Valence' },
            { key: 'instrumentalness', label: 'Instrumental' },
            { key: 'liveness', label: 'Liveness' }
        ];

        // Dispatch event for reactive background
        dispatchAudioProfile(features);

        return `
            <div class="audio-profile">
                ${metrics.map(m => `
                    <div class="audio-profile__row">
                        <span class="audio-profile__label">${m.label}</span>
                        <span class="audio-profile__meter">${renderMeter(features[m.key] || 0, 16)}</span>
                        <span class="audio-profile__value">${features[m.key] || 0}%</span>
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
            <div class="patterns-grid">
                <div class="pattern-section">
                    <div class="pattern-section__title">By Day</div>
                    <div class="ascii-bars">
                        ${days.map((day, i) => {
                            const percent = (dayData[i] / maxDay) * 100;
                            return `
                                <div class="ascii-bar-row">
                                    <span class="ascii-bar__label">${day}</span>
                                    <span class="ascii-bar__blocks">${renderBar(percent, 20)}</span>
                                    <span class="ascii-bar__value">${dayData[i]}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                <div class="pattern-section">
                    <div class="pattern-section__title">Peak Hours</div>
                    <div class="peak-hours">
                        ${peakHours.slice(0, 3).map((peak, i) => `
                            <div class="peak-hour">
                                <span class="peak-hour__time">${String(peak.hour).padStart(2, '0')}:00</span>
                                <span class="peak-hour__info">
                                    <span class="peak-hour__count">${peak.count} tracks</span>
                                    ${i === 0 ? ' - Peak' : ` - #${i + 1}`}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render weekly heatmap
     * @param {Object} heatmapData - Object with "day-hour" keys and count values
     * @returns {string} HTML string
     */
    function renderHeatmap(heatmapData) {
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const maxCount = Math.max(...Object.values(heatmapData), 1);

        // Hour labels (every 3 hours)
        let headerHtml = '<div class="ascii-heatmap__header">';
        for (let h = 0; h < 24; h++) {
            if (h % 3 === 0) {
                headerHtml += `<span class="ascii-heatmap__hour">${h}</span>`;
            } else {
                headerHtml += `<span class="ascii-heatmap__hour"></span>`;
            }
        }
        headerHtml += '</div>';

        let rowsHtml = '';
        for (let d = 0; d < 7; d++) {
            let cellsHtml = '';
            for (let h = 0; h < 24; h++) {
                const count = heatmapData[`${d}-${h}`] || 0;
                const char = getHeatChar(count, maxCount);
                cellsHtml += `<span class="ascii-heatmap__cell" title="${count} track${count !== 1 ? 's' : ''}">${char}</span>`;
            }
            rowsHtml += `
                <div class="ascii-heatmap__row">
                    <span class="ascii-heatmap__day">${days[d]}</span>
                    <div class="ascii-heatmap__cells">${cellsHtml}</div>
                </div>
            `;
        }

        return `
            <div class="ascii-heatmap">
                ${headerHtml}
                ${rowsHtml}
            </div>
        `;
    }

    /**
     * Render vertical activity chart
     * @param {number[]} hourData - Array of 24 values (hours 0-23)
     * @returns {string} HTML string
     */
    function renderActivityChart(hourData) {
        const rows = renderVerticalChart(hourData, 8);

        let html = '<div class="ascii-chart">';

        rows.forEach(row => {
            html += '<div class="ascii-chart__row">';
            row.forEach(char => {
                html += `<span class="ascii-chart__bar">${char}</span>`;
            });
            html += '</div>';
        });

        // X-axis labels
        html += '<div class="ascii-chart__axis">';
        for (let h = 0; h < 24; h++) {
            if (h % 4 === 0) {
                html += `<span class="ascii-chart__label">${h}</span>`;
            } else {
                html += `<span class="ascii-chart__label"></span>`;
            }
        }
        html += '</div>';

        html += '</div>';
        return html;
    }

    /**
     * Render track list
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
            <div class="track-list">
                ${tracks.slice(0, limit).map((track, i) => `
                    <div class="track-item${playable ? ' track-item--playable' : ''}" ${playable ? `data-track-uri="${track.uri}"` : ''}>
                        <span class="track-item__rank">${String(i + 1).padStart(2, '0')}</span>
                        <img src="${track.album.images[2]?.url || ''}" alt="" class="track-item__cover">
                        <div class="track-item__info">
                            <div class="track-item__name">${escapeHtml(track.name)}</div>
                            <div class="track-item__artist">${escapeHtml(track.artists[0].name)}</div>
                        </div>
                        <span class="track-item__duration">${formatDuration(track.duration_ms)}</span>
                    </div>
                `).join('')}
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
            <div class="taste-evolution">
                ${periods.map(period => {
                    const periodData = data[period.key];
                    if (!periodData || !periodData.artists || periodData.artists.length === 0) {
                        return `
                            <div class="taste-period">
                                <div class="taste-period__label">${period.label}</div>
                                <div class="empty-state">No data</div>
                            </div>
                        `;
                    }
                    return `
                        <div class="taste-period">
                            <div class="taste-period__label">${period.label}</div>
                            <div class="taste-period__list">
                                ${periodData.artists.slice(0, 5).map((artist, i) => `
                                    <div class="taste-artist">
                                        <span class="taste-artist__rank">${i + 1}.</span>
                                        ${artist.image ? `<img src="${artist.image}" alt="" class="taste-artist__img">` : ''}
                                        <span class="taste-artist__name">${escapeHtml(artist.name)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    // Public API
    return {
        BLOCKS,
        renderBar,
        renderMeter,
        getHeatChar,
        renderVerticalChart,
        formatDuration,
        escapeHtml,
        dispatchAudioProfile,
        renderGenreBars,
        renderAudioProfile,
        renderListeningPatterns,
        renderHeatmap,
        renderActivityChart,
        renderTrackList,
        renderTasteEvolution
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpotifyASCII;
}
