/**
 * Weather Engine - Core utilities for weather data handling
 */

const WeatherEngine = (function() {
    'use strict';

    // WMO Weather Code mappings
    const WMO_CODES = {
        0: { text: 'Clear sky', theme: 'sunny', icon: 'sun' },
        1: { text: 'Mainly clear', theme: 'sunny', icon: 'sun' },
        2: { text: 'Partly cloudy', theme: 'partlycloudy', icon: 'cloud-sun' },
        3: { text: 'Overcast', theme: 'cloudy', icon: 'cloud' },
        45: { text: 'Foggy', theme: 'foggy', icon: 'smog' },
        48: { text: 'Depositing rime fog', theme: 'foggy', icon: 'smog' },
        51: { text: 'Light drizzle', theme: 'rainy', icon: 'cloud-rain' },
        53: { text: 'Moderate drizzle', theme: 'rainy', icon: 'cloud-rain' },
        55: { text: 'Dense drizzle', theme: 'rainy', icon: 'cloud-showers-heavy' },
        56: { text: 'Freezing drizzle', theme: 'rainy', icon: 'cloud-rain' },
        57: { text: 'Dense freezing drizzle', theme: 'rainy', icon: 'cloud-showers-heavy' },
        61: { text: 'Slight rain', theme: 'rainy', icon: 'cloud-rain' },
        63: { text: 'Moderate rain', theme: 'rainy', icon: 'cloud-rain' },
        65: { text: 'Heavy rain', theme: 'stormy', icon: 'cloud-showers-heavy' },
        66: { text: 'Freezing rain', theme: 'rainy', icon: 'cloud-rain' },
        67: { text: 'Heavy freezing rain', theme: 'stormy', icon: 'cloud-showers-heavy' },
        71: { text: 'Slight snow', theme: 'snowy', icon: 'snowflake' },
        73: { text: 'Moderate snow', theme: 'snowy', icon: 'snowflake' },
        75: { text: 'Heavy snow', theme: 'snowy', icon: 'snowflake' },
        77: { text: 'Snow grains', theme: 'snowy', icon: 'snowflake' },
        80: { text: 'Slight rain showers', theme: 'rainy', icon: 'cloud-sun-rain' },
        81: { text: 'Moderate rain showers', theme: 'rainy', icon: 'cloud-rain' },
        82: { text: 'Violent rain showers', theme: 'stormy', icon: 'cloud-showers-heavy' },
        85: { text: 'Slight snow showers', theme: 'snowy', icon: 'snowflake' },
        86: { text: 'Heavy snow showers', theme: 'snowy', icon: 'snowflake' },
        95: { text: 'Thunderstorm', theme: 'stormy', icon: 'bolt' },
        96: { text: 'Thunderstorm with hail', theme: 'stormy', icon: 'bolt' },
        99: { text: 'Thunderstorm with heavy hail', theme: 'stormy', icon: 'bolt' }
    };

    /**
     * Get weather information from WMO code
     * @param {number} code - WMO weather code
     * @returns {object} Weather info with text, theme, and icon
     */
    function getWeatherInfo(code) {
        return WMO_CODES[code] || WMO_CODES[0];
    }

    /**
     * Get Font Awesome icon class for weather code
     * @param {number} code - WMO weather code
     * @returns {string} Font Awesome icon name (without 'fa-' prefix)
     */
    function getIconClass(code) {
        const info = getWeatherInfo(code);
        return info.icon;
    }

    /**
     * Get theme name for weather code
     * @param {number} code - WMO weather code
     * @returns {string} Theme name (sunny, cloudy, rainy, stormy, snowy, foggy)
     */
    function getTheme(code) {
        const info = getWeatherInfo(code);
        return info.theme;
    }

    /**
     * Get weather description text
     * @param {number} code - WMO weather code
     * @returns {string} Human-readable weather description
     */
    function getDescription(code) {
        const info = getWeatherInfo(code);
        return info.text;
    }

    /**
     * Format temperature with unit
     * @param {number} temp - Temperature value
     * @param {string} unit - 'C' for Celsius, 'F' for Fahrenheit
     * @returns {string} Formatted temperature string
     */
    function formatTemperature(temp, unit = 'C') {
        if (temp === null || temp === undefined) return '--';
        const value = Math.round(temp);
        return `${value}°${unit}`;
    }

    /**
     * Convert Celsius to Fahrenheit
     * @param {number} celsius - Temperature in Celsius
     * @returns {number} Temperature in Fahrenheit
     */
    function celsiusToFahrenheit(celsius) {
        return (celsius * 9/5) + 32;
    }

    /**
     * Convert Fahrenheit to Celsius
     * @param {number} fahrenheit - Temperature in Fahrenheit
     * @returns {number} Temperature in Celsius
     */
    function fahrenheitToCelsius(fahrenheit) {
        return (fahrenheit - 32) * 5/9;
    }

    /**
     * Get wind direction as compass point
     * @param {number} degrees - Wind direction in degrees
     * @returns {string} Compass direction (N, NE, E, etc.)
     */
    function getWindDirection(degrees) {
        if (degrees === null || degrees === undefined) return '--';
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                           'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        const index = Math.round(degrees / 22.5) % 16;
        return directions[index];
    }

    /**
     * Format wind speed with direction
     * @param {number} speed - Wind speed in km/h
     * @param {number} direction - Wind direction in degrees
     * @returns {string} Formatted wind string
     */
    function formatWind(speed, direction) {
        if (speed === null || speed === undefined) return '--';
        const dir = getWindDirection(direction);
        return `${Math.round(speed)} km/h ${dir}`;
    }

    /**
     * Get Beaufort scale description from wind speed
     * @param {number} speedKmh - Wind speed in km/h
     * @returns {object} Beaufort scale info with number and description
     */
    function getBeaufortScale(speedKmh) {
        const scales = [
            { max: 1, number: 0, description: 'Calm' },
            { max: 5, number: 1, description: 'Light air' },
            { max: 11, number: 2, description: 'Light breeze' },
            { max: 19, number: 3, description: 'Gentle breeze' },
            { max: 28, number: 4, description: 'Moderate breeze' },
            { max: 38, number: 5, description: 'Fresh breeze' },
            { max: 49, number: 6, description: 'Strong breeze' },
            { max: 61, number: 7, description: 'High wind' },
            { max: 74, number: 8, description: 'Gale' },
            { max: 88, number: 9, description: 'Strong gale' },
            { max: 102, number: 10, description: 'Storm' },
            { max: 117, number: 11, description: 'Violent storm' },
            { max: Infinity, number: 12, description: 'Hurricane' }
        ];

        for (const scale of scales) {
            if (speedKmh < scale.max) {
                return { number: scale.number, description: scale.description };
            }
        }
        return scales[scales.length - 1];
    }

    /**
     * Format date for display
     * @param {string} dateStr - ISO date string
     * @param {string} format - 'short' (Mon), 'medium' (Monday), 'full' (Monday, Jan 1)
     * @returns {string} Formatted date string
     */
    function formatDate(dateStr, format = 'short') {
        const date = new Date(dateStr);
        const options = {
            short: { weekday: 'short' },
            medium: { weekday: 'long' },
            full: { weekday: 'long', month: 'short', day: 'numeric' }
        };
        return date.toLocaleDateString('en-US', options[format] || options.short);
    }

    /**
     * Check if time is daytime (approximate)
     * @param {string} timeStr - ISO time string
     * @param {number} lat - Latitude
     * @returns {boolean} True if daytime
     */
    function isDaytime(timeStr, lat = 0) {
        const date = new Date(timeStr);
        const hour = date.getHours();
        // Simple approximation - could be improved with actual sunrise/sunset
        return hour >= 6 && hour < 20;
    }

    /**
     * Get UV index description
     * @param {number} uvIndex - UV index value
     * @returns {object} UV info with level and recommendation
     */
    function getUVInfo(uvIndex) {
        if (uvIndex < 3) {
            return { level: 'Low', recommendation: 'No protection needed' };
        } else if (uvIndex < 6) {
            return { level: 'Moderate', recommendation: 'Wear sunscreen' };
        } else if (uvIndex < 8) {
            return { level: 'High', recommendation: 'Seek shade during midday' };
        } else if (uvIndex < 11) {
            return { level: 'Very High', recommendation: 'Avoid sun exposure' };
        } else {
            return { level: 'Extreme', recommendation: 'Stay indoors' };
        }
    }

    /**
     * Calculate heat index (feels like temperature in humid conditions)
     * @param {number} tempC - Temperature in Celsius
     * @param {number} humidity - Relative humidity percentage
     * @returns {number} Heat index in Celsius
     */
    function calculateHeatIndex(tempC, humidity) {
        // Only relevant for temps above 27°C
        if (tempC < 27) return tempC;

        const tempF = celsiusToFahrenheit(tempC);
        const hi = -42.379 + 2.04901523 * tempF + 10.14333127 * humidity
            - 0.22475541 * tempF * humidity - 0.00683783 * tempF * tempF
            - 0.05481717 * humidity * humidity + 0.00122874 * tempF * tempF * humidity
            + 0.00085282 * tempF * humidity * humidity - 0.00000199 * tempF * tempF * humidity * humidity;

        return fahrenheitToCelsius(hi);
    }

    /**
     * Calculate wind chill (feels like temperature in cold/windy conditions)
     * @param {number} tempC - Temperature in Celsius
     * @param {number} windKmh - Wind speed in km/h
     * @returns {number} Wind chill in Celsius
     */
    function calculateWindChill(tempC, windKmh) {
        // Only relevant for temps below 10°C and winds above 4.8 km/h
        if (tempC > 10 || windKmh < 4.8) return tempC;

        const wc = 13.12 + 0.6215 * tempC - 11.37 * Math.pow(windKmh, 0.16)
            + 0.3965 * tempC * Math.pow(windKmh, 0.16);

        return wc;
    }

    /**
     * Find extreme from array of locations
     * @param {Array} locations - Array of location objects with weather data
     * @param {string} type - 'hottest', 'coldest', 'wettest', 'windiest'
     * @returns {object} Location with extreme value
     */
    function findExtreme(locations, type) {
        if (!locations || locations.length === 0) return null;

        switch (type) {
            case 'hottest':
                return locations.reduce((max, loc) =>
                    (loc.temp_max || -Infinity) > (max.temp_max || -Infinity) ? loc : max
                );
            case 'coldest':
                return locations.reduce((min, loc) =>
                    (loc.temp_min || Infinity) < (min.temp_min || Infinity) ? loc : min
                );
            case 'wettest':
                return locations.reduce((max, loc) =>
                    (loc.precipitation || 0) > (max.precipitation || 0) ? loc : max
                );
            case 'windiest':
                return locations.reduce((max, loc) =>
                    (loc.wind_speed || 0) > (max.wind_speed || 0) ? loc : max
                );
            default:
                return null;
        }
    }

    // Public API
    return {
        WMO_CODES,
        getWeatherInfo,
        getIconClass,
        getTheme,
        getDescription,
        formatTemperature,
        celsiusToFahrenheit,
        fahrenheitToCelsius,
        getWindDirection,
        formatWind,
        getBeaufortScale,
        formatDate,
        isDaytime,
        getUVInfo,
        calculateHeatIndex,
        calculateWindChill,
        findExtreme
    };
})();

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WeatherEngine;
}
