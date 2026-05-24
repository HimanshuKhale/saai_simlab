from django.conf import settings
from django.core.management.base import BaseCommand
from pathlib import Path

from geography.defaults import (
    DEFAULT_INDIA_MAP_ASSET_PATH,
    DEFAULT_INDIA_MAP_METADATA,
    DEFAULT_INDIA_MAP_SLUG,
    DEFAULT_INDIA_MAP_TITLE,
    default_india_calibration_json,
    default_india_project_json,
)
from geography.models import MapAsset


class Command(BaseCommand):
    help = 'Seed default Geography Map Lab assets.'

    def handle(self, *args, **options):
        media_file = Path(settings.MEDIA_ROOT) / DEFAULT_INDIA_MAP_ASSET_PATH
        asset, created = MapAsset.objects.update_or_create(
            slug=DEFAULT_INDIA_MAP_SLUG,
            defaults={
                'title': DEFAULT_INDIA_MAP_TITLE,
                'description': 'Political Map of India for ICSE Class X Geography Map Lab.',
                'asset_file': DEFAULT_INDIA_MAP_ASSET_PATH if media_file.exists() else '',
                'asset_type': MapAsset.AssetType.PRACTICE,
                'region': 'India',
                'grade_level': 'Class X',
                'subject': 'Geography',
                'board': 'ICSE',
                'metadata': DEFAULT_INDIA_MAP_METADATA,
                'default_project_json': default_india_project_json(),
                'default_calibration_json': default_india_calibration_json(),
                'published': True,
            },
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} {asset.title}.'))
        if not media_file.exists():
            self.stdout.write(
                self.style.WARNING(
                    'Please upload POLMAP_ENGLISH-2026_page-0001.jpg through Django admin or place it in media/maps/.'
                )
            )
