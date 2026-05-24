import logging
from hashlib import sha256

from django.conf import settings
from django.core.cache import cache

try:
    import requests
except ImportError:
    requests = None


logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 60 * 60 * 24
REQUEST_TIMEOUT = 4


def _empty_context(warning):
    return {'data': {}, 'warnings': [warning]}


def _cache_key(prefix, *parts):
    raw = ':'.join(str(part) for part in parts)
    return f'geo:{prefix}:{sha256(raw.encode("utf-8")).hexdigest()}'


def _get_json(cache_key, url, params=None, headers=None):
    if not getattr(settings, 'GEOGRAPHY_EXTERNAL_DATA_ENABLED', True):
        return _empty_context('External public geography data is disabled.')
    if requests is None:
        return _empty_context('Requests is not installed; external data skipped.')

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = requests.get(url, params=params or {}, headers=headers or {}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        result = {'data': response.json(), 'warnings': []}
    except Exception as exc:
        logger.info('External geography API failed: %s', exc)
        result = {'data': {}, 'warnings': ['External public geography data could not be loaded.']}
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return result


def reverse_geocode(lat, lng):
    return _get_json(
        _cache_key('reverse', lat, lng),
        'https://nominatim.openstreetmap.org/reverse',
        params={'format': 'jsonv2', 'lat': lat, 'lon': lng, 'zoom': 10},
        headers={'User-Agent': 'SAAI-SimLab-Geography/1.0'},
    )


def geocode_place_name(name, country_hint='India'):
    query = f'{name}, {country_hint}' if country_hint else name
    return _get_json(
        _cache_key('geocode', query),
        'https://nominatim.openstreetmap.org/search',
        params={'format': 'jsonv2', 'q': query, 'limit': 3},
        headers={'User-Agent': 'SAAI-SimLab-Geography/1.0'},
    )


def get_country_info(country_code_or_name):
    return _get_json(
        _cache_key('country', country_code_or_name),
        f'https://restcountries.com/v3.1/name/{country_code_or_name}',
        params={'fields': 'name,capital,region,subregion,population,area,flags'},
    )


def get_climate_context(lat, lng):
    return _get_json(
        _cache_key('climate', lat, lng),
        'https://api.open-meteo.com/v1/forecast',
        params={
            'latitude': lat,
            'longitude': lng,
            'current': 'temperature_2m,precipitation,wind_speed_10m',
        },
    )


def _first_geo_point(feature):
    points = (feature.geometry or {}).get('points') or []
    for point in points:
        geo = point.get('geo') if isinstance(point, dict) else None
        if geo and geo.get('lat') is not None and geo.get('lng') is not None:
            return geo['lat'], geo['lng']
    return None, None


def get_public_feature_context(feature):
    warnings = []
    lat, lng = _first_geo_point(feature)
    context = {
        'reverse_geocode': {},
        'climate': {},
        'country': {},
        'warnings': warnings,
    }
    if lat is None or lng is None:
        warnings.append('No latitude/longitude found on the feature geometry.')
        geocode = geocode_place_name(feature.name)
        context['geocode'] = geocode['data']
        warnings.extend(geocode['warnings'])
        return context

    reverse = reverse_geocode(lat, lng)
    climate = get_climate_context(lat, lng)
    country = get_country_info('India')
    context['reverse_geocode'] = reverse['data']
    context['climate'] = climate['data']
    context['country'] = country['data']
    warnings.extend(reverse['warnings'])
    warnings.extend(climate['warnings'])
    warnings.extend(country['warnings'])
    return context
