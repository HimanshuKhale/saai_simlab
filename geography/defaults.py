DEFAULT_INDIA_MAP_SLUG = 'india-political-map-2026'
DEFAULT_INDIA_MAP_TITLE = 'India Political Map 2026'
DEFAULT_INDIA_MAP_FILE = 'POLMAP_ENGLISH-2026_page-0001.jpg'
DEFAULT_INDIA_MAP_ASSET_PATH = f'maps/{DEFAULT_INDIA_MAP_FILE}'

CALIBRATION_DEFAULT_INDIA_APPROX = 'default_india_approx'
CALIBRATION_UNCALIBRATED = 'uncalibrated'
CALIBRATION_FOUR_POINT_FUTURE = 'four_point_calibrated_future'

DEFAULT_INDIA_CALIBRATION_WARNING = (
    'Approximate India calibration active. Coordinates are for learning and may not be survey-accurate.'
)
UNCALIBRATED_WARNING = (
    'Custom map is in annotation mode. Latitude/longitude is unavailable until calibration is added in a future/advanced version.'
)
FOUR_POINT_WARNING = (
    'Advanced approximate calibration works best only for proportional maps. Distorted/non-scale images may produce inaccurate coordinates.'
)

DEFAULT_INDIA_MAP_BOUNDS = {
    'minLng': 68.1,
    'maxLng': 97.4,
    'minLat': 6.7,
    'maxLat': 37.1,
    'imageContentBox': {
        'xMin': 2.5,
        'xMax': 97.5,
        'yMin': 2.5,
        'yMax': 95.0,
    },
}

DEFAULT_INDIA_MAP_METADATA = {
    'default': True,
    'board': 'ICSE',
    'grade': 'Class X',
    'subject': 'Geography',
    'map_kind': 'political',
    'source_file': DEFAULT_INDIA_MAP_FILE,
    'calibration_mode': CALIBRATION_DEFAULT_INDIA_APPROX,
    'region': 'India',
}


def default_india_project_json():
    return {
        'schema': 'saai.geography.project.v1',
        'project_metadata': {
            'board': 'ICSE',
            'grade': 'Class X',
            'subject': 'Geography',
            'map_title': DEFAULT_INDIA_MAP_TITLE,
        },
        'map_metadata': DEFAULT_INDIA_MAP_METADATA,
        'calibration_mode': CALIBRATION_DEFAULT_INDIA_APPROX,
        'calibration_warning': DEFAULT_INDIA_CALIBRATION_WARNING,
        'features': [],
    }


def default_india_calibration_json():
    return {
        'mode': CALIBRATION_DEFAULT_INDIA_APPROX,
        'bounds': DEFAULT_INDIA_MAP_BOUNDS,
        'warning': DEFAULT_INDIA_CALIBRATION_WARNING,
    }


def uncalibrated_project_json():
    return {
        'schema': 'saai.geography.project.v1',
        'calibration_mode': CALIBRATION_UNCALIBRATED,
        'calibration_warning': UNCALIBRATED_WARNING,
        'features': [],
    }


def uncalibrated_calibration_json():
    return {
        'mode': CALIBRATION_UNCALIBRATED,
        'warning': UNCALIBRATED_WARNING,
    }


def calibration_warning_for(mode):
    if mode == CALIBRATION_DEFAULT_INDIA_APPROX:
        return DEFAULT_INDIA_CALIBRATION_WARNING
    if mode == CALIBRATION_FOUR_POINT_FUTURE:
        return FOUR_POINT_WARNING
    return UNCALIBRATED_WARNING
