from flask import Blueprint, render_template, jsonify, request
from functools import wraps
import requests
import hashlib
import json
import os
from datetime import datetime, timedelta

bp = Blueprint('weather', __name__, url_prefix='/projects/weather')

# Simple file-based cache
CACHE_DIR = '/tmp/weather_cache'

def get_cache(key, ttl_seconds):
    """Get cached value if not expired."""
    cache_path = os.path.join(CACHE_DIR, f"{hashlib.md5(key.encode()).hexdigest()}.json")
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                if datetime.fromisoformat(data['expires']) > datetime.now():
                    return data['value']
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    return None

def set_cache(key, value, ttl_seconds):
    """Cache value with TTL."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{hashlib.md5(key.encode()).hexdigest()}.json")
    data = {
        'value': value,
        'expires': (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
    }
    with open(cache_path, 'w') as f:
        json.dump(data, f)

# WMO Weather Code mappings
WMO_CODES = {
    0: {'text': 'Clear sky', 'theme': 'sunny', 'icon': 'sun'},
    1: {'text': 'Mainly clear', 'theme': 'sunny', 'icon': 'sun'},
    2: {'text': 'Partly cloudy', 'theme': 'cloudy', 'icon': 'cloud-sun'},
    3: {'text': 'Overcast', 'theme': 'cloudy', 'icon': 'cloud'},
    45: {'text': 'Foggy', 'theme': 'foggy', 'icon': 'smog'},
    48: {'text': 'Depositing rime fog', 'theme': 'foggy', 'icon': 'smog'},
    51: {'text': 'Light drizzle', 'theme': 'rainy', 'icon': 'cloud-rain'},
    53: {'text': 'Moderate drizzle', 'theme': 'rainy', 'icon': 'cloud-rain'},
    55: {'text': 'Dense drizzle', 'theme': 'rainy', 'icon': 'cloud-showers-heavy'},
    56: {'text': 'Freezing drizzle', 'theme': 'rainy', 'icon': 'cloud-rain'},
    57: {'text': 'Dense freezing drizzle', 'theme': 'rainy', 'icon': 'cloud-showers-heavy'},
    61: {'text': 'Slight rain', 'theme': 'rainy', 'icon': 'cloud-rain'},
    63: {'text': 'Moderate rain', 'theme': 'rainy', 'icon': 'cloud-rain'},
    65: {'text': 'Heavy rain', 'theme': 'stormy', 'icon': 'cloud-showers-heavy'},
    66: {'text': 'Freezing rain', 'theme': 'rainy', 'icon': 'cloud-rain'},
    67: {'text': 'Heavy freezing rain', 'theme': 'stormy', 'icon': 'cloud-showers-heavy'},
    71: {'text': 'Slight snow', 'theme': 'snowy', 'icon': 'snowflake'},
    73: {'text': 'Moderate snow', 'theme': 'snowy', 'icon': 'snowflake'},
    75: {'text': 'Heavy snow', 'theme': 'snowy', 'icon': 'snowflake'},
    77: {'text': 'Snow grains', 'theme': 'snowy', 'icon': 'snowflake'},
    80: {'text': 'Slight rain showers', 'theme': 'rainy', 'icon': 'cloud-sun-rain'},
    81: {'text': 'Moderate rain showers', 'theme': 'rainy', 'icon': 'cloud-rain'},
    82: {'text': 'Violent rain showers', 'theme': 'stormy', 'icon': 'cloud-showers-heavy'},
    85: {'text': 'Slight snow showers', 'theme': 'snowy', 'icon': 'snowflake'},
    86: {'text': 'Heavy snow showers', 'theme': 'snowy', 'icon': 'snowflake'},
    95: {'text': 'Thunderstorm', 'theme': 'stormy', 'icon': 'bolt'},
    96: {'text': 'Thunderstorm with hail', 'theme': 'stormy', 'icon': 'bolt'},
    99: {'text': 'Thunderstorm with heavy hail', 'theme': 'stormy', 'icon': 'bolt'},
}

# Pre-defined extreme weather monitoring locations
EXTREME_LOCATIONS = [
    # Hot locations
    {'name': 'Death Valley, USA', 'lat': 36.5323, 'lon': -116.9325, 'region': 'california', 'type': 'hot'},
    {'name': 'Kuwait City, Kuwait', 'lat': 29.3759, 'lon': 47.9774, 'region': 'middle_east', 'type': 'hot'},
    {'name': 'Ahvaz, Iran', 'lat': 31.3183, 'lon': 48.6706, 'region': 'middle_east', 'type': 'hot'},
    {'name': 'Phoenix, USA', 'lat': 33.4484, 'lon': -112.0740, 'region': 'arizona', 'type': 'hot'},
    {'name': 'Dallol, Ethiopia', 'lat': 14.2417, 'lon': 40.2967, 'region': 'africa', 'type': 'hot'},
    {'name': 'Riyadh, Saudi Arabia', 'lat': 24.7136, 'lon': 46.6753, 'region': 'middle_east', 'type': 'hot'},
    {'name': 'Alice Springs, Australia', 'lat': -23.6980, 'lon': 133.8807, 'region': 'australia', 'type': 'hot'},
    {'name': 'Timbuktu, Mali', 'lat': 16.7666, 'lon': -3.0026, 'region': 'africa', 'type': 'hot'},
    # Cold locations
    {'name': 'Yakutsk, Russia', 'lat': 62.0355, 'lon': 129.6755, 'region': 'russia', 'type': 'cold'},
    {'name': 'Oymyakon, Russia', 'lat': 63.4608, 'lon': 142.7858, 'region': 'russia', 'type': 'cold'},
    {'name': 'Yellowknife, Canada', 'lat': 62.4540, 'lon': -114.3718, 'region': 'canada', 'type': 'cold'},
    {'name': 'Fairbanks, USA', 'lat': 64.8378, 'lon': -147.7164, 'region': 'alaska', 'type': 'cold'},
    {'name': 'Ulaanbaatar, Mongolia', 'lat': 47.8864, 'lon': 106.9057, 'region': 'asia', 'type': 'cold'},
    {'name': 'Harbin, China', 'lat': 45.8038, 'lon': 126.5350, 'region': 'asia', 'type': 'cold'},
    {'name': 'Norilsk, Russia', 'lat': 69.3558, 'lon': 88.1893, 'region': 'russia', 'type': 'cold'},
    {'name': 'Barrow, USA', 'lat': 71.2906, 'lon': -156.7886, 'region': 'alaska', 'type': 'cold'},
    # Wet locations
    {'name': 'Mawsynram, India', 'lat': 25.2970, 'lon': 91.5822, 'region': 'india', 'type': 'wet'},
    {'name': 'Cherrapunji, India', 'lat': 25.2700, 'lon': 91.7200, 'region': 'india', 'type': 'wet'},
    {'name': 'Quibdo, Colombia', 'lat': 5.6919, 'lon': -76.6583, 'region': 'south_america', 'type': 'wet'},
    {'name': 'Singapore', 'lat': 1.3521, 'lon': 103.8198, 'region': 'asia', 'type': 'wet'},
    {'name': 'Hilo, Hawaii', 'lat': 19.7074, 'lon': -155.0847, 'region': 'hawaii', 'type': 'wet'},
    {'name': 'Manaus, Brazil', 'lat': -3.1190, 'lon': -60.0217, 'region': 'south_america', 'type': 'wet'},
    {'name': 'Kuala Lumpur, Malaysia', 'lat': 3.1390, 'lon': 101.6869, 'region': 'asia', 'type': 'wet'},
    {'name': 'Lagos, Nigeria', 'lat': 6.5244, 'lon': 3.3792, 'region': 'africa', 'type': 'wet'},
    # Windy locations
    {'name': 'Mt Washington, USA', 'lat': 44.2706, 'lon': -71.3033, 'region': 'new_england', 'type': 'windy'},
    {'name': 'Cape Horn, Chile', 'lat': -55.9857, 'lon': -67.2742, 'region': 'south_america', 'type': 'windy'},
    {'name': 'Wellington, New Zealand', 'lat': -41.2865, 'lon': 174.7762, 'region': 'oceania', 'type': 'windy'},
    {'name': 'Punta Arenas, Chile', 'lat': -53.1638, 'lon': -70.9171, 'region': 'south_america', 'type': 'windy'},
    {'name': 'Reykjavik, Iceland', 'lat': 64.1466, 'lon': -21.9426, 'region': 'europe', 'type': 'windy'},
    {'name': 'Edinburgh, Scotland', 'lat': 55.9533, 'lon': -3.1883, 'region': 'europe', 'type': 'windy'},
    {'name': 'Chicago, USA', 'lat': 41.8781, 'lon': -87.6298, 'region': 'midwest', 'type': 'windy'},
    {'name': 'Oklahoma City, USA', 'lat': 35.4676, 'lon': -97.5164, 'region': 'midwest', 'type': 'windy'},
    # Storm-prone locations
    {'name': 'Miami, USA', 'lat': 25.7617, 'lon': -80.1918, 'region': 'florida', 'type': 'storm'},
    {'name': 'Houston, USA', 'lat': 29.7604, 'lon': -95.3698, 'region': 'texas', 'type': 'storm'},
    {'name': 'Tokyo, Japan', 'lat': 35.6762, 'lon': 139.6503, 'region': 'japan', 'type': 'storm'},
    {'name': 'Manila, Philippines', 'lat': 14.5995, 'lon': 120.9842, 'region': 'asia', 'type': 'storm'},
    {'name': 'Dhaka, Bangladesh', 'lat': 23.8103, 'lon': 90.4125, 'region': 'asia', 'type': 'storm'},
    {'name': 'New Orleans, USA', 'lat': 29.9511, 'lon': -90.0715, 'region': 'louisiana', 'type': 'storm'},
    {'name': 'Hong Kong', 'lat': 22.3193, 'lon': 114.1694, 'region': 'asia', 'type': 'storm'},
    {'name': 'Mumbai, India', 'lat': 19.0760, 'lon': 72.8777, 'region': 'india', 'type': 'storm'},
    # Major cities for general monitoring
    {'name': 'New York, USA', 'lat': 40.7128, 'lon': -74.0060, 'region': 'northeast', 'type': 'major'},
    {'name': 'London, UK', 'lat': 51.5074, 'lon': -0.1278, 'region': 'europe', 'type': 'major'},
    {'name': 'Paris, France', 'lat': 48.8566, 'lon': 2.3522, 'region': 'europe', 'type': 'major'},
    {'name': 'Los Angeles, USA', 'lat': 34.0522, 'lon': -118.2437, 'region': 'california', 'type': 'major'},
    {'name': 'Sydney, Australia', 'lat': -33.8688, 'lon': 151.2093, 'region': 'australia', 'type': 'major'},
    {'name': 'Dubai, UAE', 'lat': 25.2048, 'lon': 55.2708, 'region': 'middle_east', 'type': 'major'},
    {'name': 'Moscow, Russia', 'lat': 55.7558, 'lon': 37.6173, 'region': 'russia', 'type': 'major'},
    {'name': 'Beijing, China', 'lat': 39.9042, 'lon': 116.4074, 'region': 'asia', 'type': 'major'},
]

# Industry impact mappings by region
INDUSTRY_MAPPINGS = {
    'florida': {
        'name': 'Florida, USA',
        'industries': [
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Beach resorts, theme parks (Disney, Universal), cruise ports'},
            {'name': 'Citrus Agriculture', 'sensitivity': 'high', 'details': 'Oranges, grapefruits - frost and hurricane sensitive'},
            {'name': 'Shipping & Ports', 'sensitivity': 'high', 'details': 'Port Miami, Port Tampa Bay, Port Everglades'},
            {'name': 'Real Estate', 'sensitivity': 'medium', 'details': 'Coastal property values affected by storm risk'},
            {'name': 'Insurance', 'sensitivity': 'high', 'details': 'Property insurance rates tied to hurricane exposure'},
        ]
    },
    'texas': {
        'name': 'Texas, USA',
        'industries': [
            {'name': 'Oil & Gas', 'sensitivity': 'high', 'details': 'Gulf Coast refineries, offshore drilling, pipelines'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Cotton, cattle ranching, wheat - drought sensitive'},
            {'name': 'Manufacturing', 'sensitivity': 'medium', 'details': 'Electronics, aerospace, automotive'},
            {'name': 'Energy Grid', 'sensitivity': 'high', 'details': 'ERCOT grid vulnerable to extreme temperatures'},
            {'name': 'Shipping', 'sensitivity': 'high', 'details': 'Port of Houston, largest US port by tonnage'},
        ]
    },
    'california': {
        'name': 'California, USA',
        'industries': [
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Almonds, grapes, vegetables - drought and fire sensitive'},
            {'name': 'Technology', 'sensitivity': 'low', 'details': 'Silicon Valley - minimal direct weather impact'},
            {'name': 'Entertainment', 'sensitivity': 'medium', 'details': 'Film production, tourism - wildfires affect shoots'},
            {'name': 'Wine Industry', 'sensitivity': 'high', 'details': 'Napa, Sonoma - smoke taint from fires'},
            {'name': 'Ports', 'sensitivity': 'medium', 'details': 'LA/Long Beach - largest US container port'},
        ]
    },
    'midwest': {
        'name': 'US Midwest',
        'industries': [
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Corn, soybeans, wheat - flood and drought sensitive'},
            {'name': 'Manufacturing', 'sensitivity': 'medium', 'details': 'Auto industry, steel production'},
            {'name': 'Transportation', 'sensitivity': 'high', 'details': 'Mississippi River shipping, rail hubs'},
            {'name': 'Insurance', 'sensitivity': 'high', 'details': 'Tornado and hail damage claims'},
        ]
    },
    'northeast': {
        'name': 'US Northeast',
        'industries': [
            {'name': 'Finance', 'sensitivity': 'medium', 'details': 'Wall Street - extreme weather closures'},
            {'name': 'Transportation', 'sensitivity': 'high', 'details': 'Airports, rail - snow and ice disruptions'},
            {'name': 'Retail', 'sensitivity': 'medium', 'details': 'Shopping affected by blizzards'},
            {'name': 'Energy', 'sensitivity': 'high', 'details': 'Heating demand spikes in winter'},
        ]
    },
    'louisiana': {
        'name': 'Louisiana, USA',
        'industries': [
            {'name': 'Oil & Gas', 'sensitivity': 'high', 'details': 'Offshore platforms, refineries'},
            {'name': 'Fishing & Seafood', 'sensitivity': 'high', 'details': 'Shrimp, oysters, crawfish'},
            {'name': 'Ports', 'sensitivity': 'high', 'details': 'Port of New Orleans, South Louisiana Port'},
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'New Orleans tourism, Mardi Gras'},
        ]
    },
    'middle_east': {
        'name': 'Middle East',
        'industries': [
            {'name': 'Oil & Gas', 'sensitivity': 'medium', 'details': 'Production generally weather-resistant'},
            {'name': 'Construction', 'sensitivity': 'high', 'details': 'Outdoor work halts in extreme heat'},
            {'name': 'Aviation', 'sensitivity': 'medium', 'details': 'Hub airports, some heat-related delays'},
            {'name': 'Desalination', 'sensitivity': 'medium', 'details': 'Water production critical in heat waves'},
        ]
    },
    'europe': {
        'name': 'Europe',
        'industries': [
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Seasonal travel affected by heat waves, floods'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Wine, olives, wheat - drought sensitive'},
            {'name': 'Energy', 'sensitivity': 'high', 'details': 'Nuclear cooling, renewable generation'},
            {'name': 'River Transport', 'sensitivity': 'high', 'details': 'Rhine shipping during low water'},
        ]
    },
    'asia': {
        'name': 'Asia',
        'industries': [
            {'name': 'Manufacturing', 'sensitivity': 'high', 'details': 'Factory flooding, supply chain disruption'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Rice, tea - monsoon dependent'},
            {'name': 'Shipping', 'sensitivity': 'high', 'details': 'Major ports affected by typhoons'},
            {'name': 'Electronics', 'sensitivity': 'high', 'details': 'Semiconductor fabs need stable conditions'},
        ]
    },
    'australia': {
        'name': 'Australia',
        'industries': [
            {'name': 'Mining', 'sensitivity': 'high', 'details': 'Flooding disrupts operations'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Cattle, wheat - drought and fire'},
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Great Barrier Reef, outback tours'},
            {'name': 'Wine', 'sensitivity': 'high', 'details': 'Smoke taint from bushfires'},
        ]
    },
    'india': {
        'name': 'India',
        'industries': [
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Monsoon-dependent crops, rice, cotton'},
            {'name': 'Manufacturing', 'sensitivity': 'medium', 'details': 'Factory disruptions during floods'},
            {'name': 'IT Services', 'sensitivity': 'low', 'details': 'Bangalore, Hyderabad - minimal impact'},
            {'name': 'Textiles', 'sensitivity': 'high', 'details': 'Cotton production, export logistics'},
        ]
    },
    'russia': {
        'name': 'Russia',
        'industries': [
            {'name': 'Oil & Gas', 'sensitivity': 'medium', 'details': 'Arctic operations, permafrost issues'},
            {'name': 'Mining', 'sensitivity': 'medium', 'details': 'Extreme cold operational challenges'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Wheat - short growing season'},
            {'name': 'Transportation', 'sensitivity': 'high', 'details': 'Northern Sea Route, rail'},
        ]
    },
    'south_america': {
        'name': 'South America',
        'industries': [
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Coffee, soybeans, beef'},
            {'name': 'Mining', 'sensitivity': 'medium', 'details': 'Copper, lithium extraction'},
            {'name': 'Hydropower', 'sensitivity': 'high', 'details': 'Drought affects generation'},
        ]
    },
    'africa': {
        'name': 'Africa',
        'industries': [
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Subsistence farming, cash crops'},
            {'name': 'Mining', 'sensitivity': 'medium', 'details': 'Gold, diamonds, rare earths'},
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Safari, wildlife tourism'},
        ]
    },
    'japan': {
        'name': 'Japan',
        'industries': [
            {'name': 'Manufacturing', 'sensitivity': 'high', 'details': 'Auto, electronics - typhoon/earthquake'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Rice - typhoon season'},
            {'name': 'Tourism', 'sensitivity': 'medium', 'details': 'Seasonal travel patterns'},
            {'name': 'Fishing', 'sensitivity': 'high', 'details': 'Major seafood industry'},
        ]
    },
    'hawaii': {
        'name': 'Hawaii, USA',
        'industries': [
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Beach resorts, volcano tours'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Coffee, macadamia, tropical fruits'},
            {'name': 'Military', 'sensitivity': 'medium', 'details': 'Pearl Harbor, Pacific Command'},
        ]
    },
    'new_england': {
        'name': 'New England, USA',
        'industries': [
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Fall foliage, ski resorts'},
            {'name': 'Fishing', 'sensitivity': 'high', 'details': 'Lobster, cod fishing'},
            {'name': 'Education', 'sensitivity': 'low', 'details': 'Universities - snow day closures'},
            {'name': 'Healthcare', 'sensitivity': 'medium', 'details': 'Major medical centers'},
        ]
    },
    'alaska': {
        'name': 'Alaska, USA',
        'industries': [
            {'name': 'Oil & Gas', 'sensitivity': 'high', 'details': 'North Slope, Trans-Alaska Pipeline'},
            {'name': 'Fishing', 'sensitivity': 'high', 'details': 'Salmon, crab fishing'},
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Cruises, wildlife viewing'},
            {'name': 'Mining', 'sensitivity': 'medium', 'details': 'Gold, zinc mining'},
        ]
    },
    'arizona': {
        'name': 'Arizona, USA',
        'industries': [
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Grand Canyon, desert resorts'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Cotton, citrus - water dependent'},
            {'name': 'Technology', 'sensitivity': 'medium', 'details': 'Semiconductor manufacturing'},
            {'name': 'Energy', 'sensitivity': 'high', 'details': 'Solar generation, cooling demand'},
        ]
    },
    'canada': {
        'name': 'Canada',
        'industries': [
            {'name': 'Oil & Gas', 'sensitivity': 'high', 'details': 'Oil sands, pipelines'},
            {'name': 'Forestry', 'sensitivity': 'high', 'details': 'Lumber, paper - wildfire risk'},
            {'name': 'Mining', 'sensitivity': 'medium', 'details': 'Gold, potash, uranium'},
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Wheat, canola - prairie drought'},
        ]
    },
    'oceania': {
        'name': 'Oceania',
        'industries': [
            {'name': 'Agriculture', 'sensitivity': 'high', 'details': 'Dairy, sheep, wine'},
            {'name': 'Tourism', 'sensitivity': 'high', 'details': 'Adventure tourism, film locations'},
            {'name': 'Geothermal Energy', 'sensitivity': 'low', 'details': 'Renewable generation'},
        ]
    },
}


@bp.route('/')
def index():
    """Main weather dashboard page."""
    return render_template('weather/index.html')


@bp.route('/api/geocode')
def api_geocode():
    """Convert city name to coordinates using Open-Meteo geocoding API."""
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({'error': 'City parameter required'}), 400

    cache_key = f"geocode:{city.lower()}"
    cached = get_cache(cache_key, 86400)
    if cached:
        return jsonify(cached)

    try:
        response = requests.get(
            'https://geocoding-api.open-meteo.com/v1/search',
            params={'name': city, 'count': 5, 'language': 'en', 'format': 'json'},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get('results'):
            return jsonify({'error': 'City not found'}), 404

        results = []
        for r in data['results']:
            results.append({
                'name': r.get('name'),
                'country': r.get('country'),
                'admin1': r.get('admin1'),  # State/province
                'lat': r.get('latitude'),
                'lon': r.get('longitude'),
                'timezone': r.get('timezone'),
            })

        result = {'results': results}
        set_cache(cache_key, result, 86400)
        return jsonify(result)

    except requests.RequestException as e:
        return jsonify({'error': f'Geocoding failed: {str(e)}'}), 500


@bp.route('/api/current')
def api_current():
    """Get current weather for coordinates."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'lat and lon parameters required'}), 400

    try:
        lat = round(float(lat), 2)
        lon = round(float(lon), 2)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    cache_key = f"current:{lat}:{lon}"
    cached = get_cache(cache_key, 600)  # 10 minute cache
    if cached:
        return jsonify(cached)

    try:
        response = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,precipitation',
                'timezone': 'auto',
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        current = data.get('current', {})
        weather_code = current.get('weather_code', 0)
        weather_info = WMO_CODES.get(weather_code, WMO_CODES[0])

        result = {
            'temperature': current.get('temperature_2m'),
            'feels_like': current.get('apparent_temperature'),
            'humidity': current.get('relative_humidity_2m'),
            'wind_speed': current.get('wind_speed_10m'),
            'wind_direction': current.get('wind_direction_10m'),
            'precipitation': current.get('precipitation'),
            'weather_code': weather_code,
            'weather_text': weather_info['text'],
            'weather_theme': weather_info['theme'],
            'weather_icon': weather_info['icon'],
            'timezone': data.get('timezone'),
            'time': current.get('time'),
        }

        set_cache(cache_key, result, 600)
        return jsonify(result)

    except requests.RequestException as e:
        return jsonify({'error': f'Weather fetch failed: {str(e)}'}), 500


@bp.route('/api/forecast')
def api_forecast():
    """Get 7-day forecast for coordinates."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'lat and lon parameters required'}), 400

    try:
        lat = round(float(lat), 2)
        lon = round(float(lon), 2)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    cache_key = f"forecast:{lat}:{lon}"
    cached = get_cache(cache_key, 1800)  # 30 minute cache
    if cached:
        return jsonify(cached)

    try:
        response = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': lat,
                'longitude': lon,
                'daily': 'temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max,precipitation_sum,wind_speed_10m_max',
                'timezone': 'auto',
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        daily = data.get('daily', {})
        days = []

        for i in range(len(daily.get('time', []))):
            weather_code = daily['weather_code'][i] if daily.get('weather_code') else 0
            weather_info = WMO_CODES.get(weather_code, WMO_CODES[0])

            days.append({
                'date': daily['time'][i],
                'temp_max': daily['temperature_2m_max'][i] if daily.get('temperature_2m_max') else None,
                'temp_min': daily['temperature_2m_min'][i] if daily.get('temperature_2m_min') else None,
                'weather_code': weather_code,
                'weather_text': weather_info['text'],
                'weather_icon': weather_info['icon'],
                'precipitation_probability': daily['precipitation_probability_max'][i] if daily.get('precipitation_probability_max') else None,
                'precipitation_sum': daily['precipitation_sum'][i] if daily.get('precipitation_sum') else None,
                'wind_speed_max': daily['wind_speed_10m_max'][i] if daily.get('wind_speed_10m_max') else None,
            })

        result = {'days': days, 'timezone': data.get('timezone')}
        set_cache(cache_key, result, 1800)
        return jsonify(result)

    except requests.RequestException as e:
        return jsonify({'error': f'Forecast fetch failed: {str(e)}'}), 500


@bp.route('/api/extremes/<horizon>')
def api_extremes(horizon):
    """Get extreme weather data for specified time horizon."""
    valid_horizons = ['today', 'tomorrow', '3day', '7day', 'season', 'year']
    if horizon not in valid_horizons:
        return jsonify({'error': f'Invalid horizon. Valid options: {valid_horizons}'}), 400

    # Cache TTL varies by horizon
    ttl_map = {
        'today': 1800,      # 30 min
        'tomorrow': 1800,   # 30 min
        '3day': 3600,       # 1 hour
        '7day': 7200,       # 2 hours
        'season': 21600,    # 6 hours
        'year': 21600,      # 6 hours
    }

    cache_key = f"extremes:{horizon}"
    cached = get_cache(cache_key, ttl_map[horizon])
    if cached:
        return jsonify(cached)

    # Fetch weather for all extreme monitoring locations
    extremes = {
        'hottest': None,
        'coldest': None,
        'wettest': None,
        'windiest': None,
        'horizon': horizon,
        'locations': []
    }

    for loc in EXTREME_LOCATIONS:
        try:
            if horizon in ['today', 'tomorrow']:
                # Use forecast API for near-term
                response = requests.get(
                    'https://api.open-meteo.com/v1/forecast',
                    params={
                        'latitude': loc['lat'],
                        'longitude': loc['lon'],
                        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code',
                        'timezone': 'auto',
                        'forecast_days': 2
                    },
                    timeout=5
                )
                if response.ok:
                    data = response.json()
                    daily = data.get('daily', {})
                    day_idx = 0 if horizon == 'today' else 1

                    if daily.get('temperature_2m_max') and len(daily['temperature_2m_max']) > day_idx:
                        weather_code = daily['weather_code'][day_idx] if daily.get('weather_code') else 0
                        weather_info = WMO_CODES.get(weather_code, WMO_CODES[0])

                        loc_data = {
                            'name': loc['name'],
                            'lat': loc['lat'],
                            'lon': loc['lon'],
                            'region': loc['region'],
                            'temp_max': daily['temperature_2m_max'][day_idx],
                            'temp_min': daily['temperature_2m_min'][day_idx],
                            'precipitation': daily['precipitation_sum'][day_idx] if daily.get('precipitation_sum') else 0,
                            'wind_speed': daily['wind_speed_10m_max'][day_idx] if daily.get('wind_speed_10m_max') else 0,
                            'weather_code': weather_code,
                            'weather_text': weather_info['text'],
                            'weather_icon': weather_info['icon'],
                        }
                        extremes['locations'].append(loc_data)

            elif horizon in ['3day', '7day']:
                # Use forecast API with more days
                days = 3 if horizon == '3day' else 7
                response = requests.get(
                    'https://api.open-meteo.com/v1/forecast',
                    params={
                        'latitude': loc['lat'],
                        'longitude': loc['lon'],
                        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code',
                        'timezone': 'auto',
                        'forecast_days': days
                    },
                    timeout=5
                )
                if response.ok:
                    data = response.json()
                    daily = data.get('daily', {})

                    if daily.get('temperature_2m_max'):
                        # Get max of the period
                        max_temp = max(daily['temperature_2m_max'])
                        min_temp = min(daily['temperature_2m_min'])
                        total_precip = sum(daily.get('precipitation_sum', [0]))
                        max_wind = max(daily.get('wind_speed_10m_max', [0]))

                        loc_data = {
                            'name': loc['name'],
                            'lat': loc['lat'],
                            'lon': loc['lon'],
                            'region': loc['region'],
                            'temp_max': max_temp,
                            'temp_min': min_temp,
                            'precipitation': total_precip,
                            'wind_speed': max_wind,
                        }
                        extremes['locations'].append(loc_data)

            else:  # season or year - use current/forecast as proxy
                response = requests.get(
                    'https://api.open-meteo.com/v1/forecast',
                    params={
                        'latitude': loc['lat'],
                        'longitude': loc['lon'],
                        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max',
                        'timezone': 'auto',
                        'forecast_days': 14
                    },
                    timeout=5
                )
                if response.ok:
                    data = response.json()
                    daily = data.get('daily', {})

                    if daily.get('temperature_2m_max'):
                        max_temp = max(daily['temperature_2m_max'])
                        min_temp = min(daily['temperature_2m_min'])
                        total_precip = sum(daily.get('precipitation_sum', [0]))
                        max_wind = max(daily.get('wind_speed_10m_max', [0]))

                        loc_data = {
                            'name': loc['name'],
                            'lat': loc['lat'],
                            'lon': loc['lon'],
                            'region': loc['region'],
                            'temp_max': max_temp,
                            'temp_min': min_temp,
                            'precipitation': total_precip,
                            'wind_speed': max_wind,
                        }
                        extremes['locations'].append(loc_data)

        except requests.RequestException:
            continue  # Skip failed locations

    # Find extremes from collected data
    if extremes['locations']:
        locs = extremes['locations']

        # Hottest
        hottest = max(locs, key=lambda x: x.get('temp_max', -999))
        extremes['hottest'] = {
            **hottest,
            'value': hottest.get('temp_max'),
            'unit': 'C',
            'label': 'Hottest'
        }

        # Coldest
        coldest = min(locs, key=lambda x: x.get('temp_min', 999))
        extremes['coldest'] = {
            **coldest,
            'value': coldest.get('temp_min'),
            'unit': 'C',
            'label': 'Coldest'
        }

        # Wettest
        wettest = max(locs, key=lambda x: x.get('precipitation', 0))
        extremes['wettest'] = {
            **wettest,
            'value': wettest.get('precipitation'),
            'unit': 'mm',
            'label': 'Wettest'
        }

        # Windiest
        windiest = max(locs, key=lambda x: x.get('wind_speed', 0))
        extremes['windiest'] = {
            **windiest,
            'value': windiest.get('wind_speed'),
            'unit': 'km/h',
            'label': 'Windiest'
        }

    set_cache(cache_key, extremes, ttl_map[horizon])
    return jsonify(extremes)


@bp.route('/api/industry/<region>')
def api_industry(region):
    """Get industry impact data for a region."""
    region = region.lower().replace('-', '_').replace(' ', '_')

    if region not in INDUSTRY_MAPPINGS:
        # Try to find partial match
        for key in INDUSTRY_MAPPINGS:
            if region in key or key in region:
                region = key
                break
        else:
            return jsonify({'error': 'Region not found', 'available': list(INDUSTRY_MAPPINGS.keys())}), 404

    return jsonify(INDUSTRY_MAPPINGS[region])
