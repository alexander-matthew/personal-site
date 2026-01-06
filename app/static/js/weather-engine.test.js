/**
 * Weather Engine Tests
 */

const WeatherEngine = require('./weather-engine.js');

describe('WeatherEngine', () => {
    describe('getWeatherInfo', () => {
        test('returns correct info for clear sky (code 0)', () => {
            const info = WeatherEngine.getWeatherInfo(0);
            expect(info).toEqual({
                text: 'Clear sky',
                theme: 'sunny',
                icon: 'sun'
            });
        });

        test('returns correct info for thunderstorm (code 95)', () => {
            const info = WeatherEngine.getWeatherInfo(95);
            expect(info).toEqual({
                text: 'Thunderstorm',
                theme: 'stormy',
                icon: 'bolt'
            });
        });

        test('returns default for unknown code', () => {
            const info = WeatherEngine.getWeatherInfo(999);
            expect(info.theme).toBe('sunny');
        });
    });

    describe('getIconClass', () => {
        test('returns sun for clear sky', () => {
            expect(WeatherEngine.getIconClass(0)).toBe('sun');
        });

        test('returns snowflake for snow', () => {
            expect(WeatherEngine.getIconClass(71)).toBe('snowflake');
        });

        test('returns bolt for thunderstorm', () => {
            expect(WeatherEngine.getIconClass(95)).toBe('bolt');
        });
    });

    describe('getTheme', () => {
        test('returns sunny for clear codes', () => {
            expect(WeatherEngine.getTheme(0)).toBe('sunny');
            expect(WeatherEngine.getTheme(1)).toBe('sunny');
        });

        test('returns rainy for rain codes', () => {
            expect(WeatherEngine.getTheme(61)).toBe('rainy');
            expect(WeatherEngine.getTheme(63)).toBe('rainy');
        });

        test('returns stormy for severe weather', () => {
            expect(WeatherEngine.getTheme(65)).toBe('stormy');
            expect(WeatherEngine.getTheme(95)).toBe('stormy');
        });

        test('returns snowy for snow codes', () => {
            expect(WeatherEngine.getTheme(71)).toBe('snowy');
            expect(WeatherEngine.getTheme(75)).toBe('snowy');
        });
    });

    describe('formatTemperature', () => {
        test('formats Celsius correctly', () => {
            expect(WeatherEngine.formatTemperature(25, 'C')).toBe('25°C');
            expect(WeatherEngine.formatTemperature(0, 'C')).toBe('0°C');
            expect(WeatherEngine.formatTemperature(-10, 'C')).toBe('-10°C');
        });

        test('formats Fahrenheit correctly', () => {
            expect(WeatherEngine.formatTemperature(77, 'F')).toBe('77°F');
        });

        test('rounds to nearest integer', () => {
            expect(WeatherEngine.formatTemperature(25.7, 'C')).toBe('26°C');
            expect(WeatherEngine.formatTemperature(25.3, 'C')).toBe('25°C');
        });

        test('handles null/undefined', () => {
            expect(WeatherEngine.formatTemperature(null)).toBe('--');
            expect(WeatherEngine.formatTemperature(undefined)).toBe('--');
        });
    });

    describe('celsiusToFahrenheit', () => {
        test('converts correctly', () => {
            expect(WeatherEngine.celsiusToFahrenheit(0)).toBe(32);
            expect(WeatherEngine.celsiusToFahrenheit(100)).toBe(212);
            expect(WeatherEngine.celsiusToFahrenheit(-40)).toBe(-40);
        });
    });

    describe('fahrenheitToCelsius', () => {
        test('converts correctly', () => {
            expect(WeatherEngine.fahrenheitToCelsius(32)).toBe(0);
            expect(WeatherEngine.fahrenheitToCelsius(212)).toBe(100);
            expect(WeatherEngine.fahrenheitToCelsius(-40)).toBe(-40);
        });
    });

    describe('getWindDirection', () => {
        test('returns correct compass directions', () => {
            expect(WeatherEngine.getWindDirection(0)).toBe('N');
            expect(WeatherEngine.getWindDirection(90)).toBe('E');
            expect(WeatherEngine.getWindDirection(180)).toBe('S');
            expect(WeatherEngine.getWindDirection(270)).toBe('W');
        });

        test('handles intermediate directions', () => {
            expect(WeatherEngine.getWindDirection(45)).toBe('NE');
            expect(WeatherEngine.getWindDirection(135)).toBe('SE');
            expect(WeatherEngine.getWindDirection(225)).toBe('SW');
            expect(WeatherEngine.getWindDirection(315)).toBe('NW');
        });

        test('handles null/undefined', () => {
            expect(WeatherEngine.getWindDirection(null)).toBe('--');
            expect(WeatherEngine.getWindDirection(undefined)).toBe('--');
        });
    });

    describe('getBeaufortScale', () => {
        test('returns calm for very low winds', () => {
            const result = WeatherEngine.getBeaufortScale(0);
            expect(result.number).toBe(0);
            expect(result.description).toBe('Calm');
        });

        test('returns strong gale for 75 km/h', () => {
            const result = WeatherEngine.getBeaufortScale(75);
            expect(result.number).toBe(9);
            expect(result.description).toBe('Strong gale');
        });

        test('returns hurricane for extreme winds', () => {
            const result = WeatherEngine.getBeaufortScale(150);
            expect(result.number).toBe(12);
            expect(result.description).toBe('Hurricane');
        });
    });

    describe('formatDate', () => {
        test('formats short date (weekday abbreviation)', () => {
            const result = WeatherEngine.formatDate('2024-01-15', 'short');
            // Should be a short weekday (Mon, Tue, etc.) - check it's a short string
            expect(result.length).toBeLessThanOrEqual(4);
            expect(typeof result).toBe('string');
        });

        test('formats medium date (full weekday)', () => {
            const result = WeatherEngine.formatDate('2024-01-15', 'medium');
            // Should be a full weekday name
            expect(result.length).toBeGreaterThan(4);
            expect(typeof result).toBe('string');
        });

        test('formats full date (weekday, month, day)', () => {
            const result = WeatherEngine.formatDate('2024-01-15', 'full');
            // Should contain both weekday and month info
            expect(result.length).toBeGreaterThan(8);
            expect(typeof result).toBe('string');
        });
    });

    describe('getUVInfo', () => {
        test('returns low for UV < 3', () => {
            const result = WeatherEngine.getUVInfo(2);
            expect(result.level).toBe('Low');
        });

        test('returns high for UV 6-8', () => {
            const result = WeatherEngine.getUVInfo(7);
            expect(result.level).toBe('High');
        });

        test('returns extreme for UV >= 11', () => {
            const result = WeatherEngine.getUVInfo(12);
            expect(result.level).toBe('Extreme');
        });
    });

    describe('calculateHeatIndex', () => {
        test('returns same temp for cool temperatures', () => {
            const result = WeatherEngine.calculateHeatIndex(20, 50);
            expect(result).toBe(20);
        });

        test('increases for hot and humid conditions', () => {
            const result = WeatherEngine.calculateHeatIndex(35, 80);
            expect(result).toBeGreaterThan(35);
        });
    });

    describe('calculateWindChill', () => {
        test('returns same temp for warm temperatures', () => {
            const result = WeatherEngine.calculateWindChill(15, 20);
            expect(result).toBe(15);
        });

        test('decreases for cold and windy conditions', () => {
            const result = WeatherEngine.calculateWindChill(-5, 30);
            expect(result).toBeLessThan(-5);
        });

        test('returns same temp for low winds', () => {
            const result = WeatherEngine.calculateWindChill(0, 2);
            expect(result).toBe(0);
        });
    });

    describe('findExtreme', () => {
        const locations = [
            { name: 'A', temp_max: 30, temp_min: 20, precipitation: 10, wind_speed: 50 },
            { name: 'B', temp_max: 45, temp_min: -10, precipitation: 200, wind_speed: 30 },
            { name: 'C', temp_max: 25, temp_min: 5, precipitation: 50, wind_speed: 100 }
        ];

        test('finds hottest location', () => {
            const result = WeatherEngine.findExtreme(locations, 'hottest');
            expect(result.name).toBe('B');
            expect(result.temp_max).toBe(45);
        });

        test('finds coldest location', () => {
            const result = WeatherEngine.findExtreme(locations, 'coldest');
            expect(result.name).toBe('B');
            expect(result.temp_min).toBe(-10);
        });

        test('finds wettest location', () => {
            const result = WeatherEngine.findExtreme(locations, 'wettest');
            expect(result.name).toBe('B');
            expect(result.precipitation).toBe(200);
        });

        test('finds windiest location', () => {
            const result = WeatherEngine.findExtreme(locations, 'windiest');
            expect(result.name).toBe('C');
            expect(result.wind_speed).toBe(100);
        });

        test('returns null for empty array', () => {
            expect(WeatherEngine.findExtreme([], 'hottest')).toBeNull();
        });

        test('returns null for invalid type', () => {
            expect(WeatherEngine.findExtreme(locations, 'invalid')).toBeNull();
        });
    });
});
