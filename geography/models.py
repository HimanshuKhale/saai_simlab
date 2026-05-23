from django.conf import settings
from django.db import models

from simulations.models import Scenario, SimulationSession


class MapAsset(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    asset_file = models.FileField(upload_to='maps/', blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class GeographyTask(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='geography_tasks')
    map_asset = models.ForeignKey(
        MapAsset,
        on_delete=models.PROTECT,
        related_name='tasks',
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)
    instructions = models.TextField(blank=True)
    objectives = models.JSONField(default=list, blank=True)
    configuration = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['scenario', 'title']
        constraints = [
            models.UniqueConstraint(fields=['scenario', 'slug'], name='unique_geography_task_slug')
        ]

    def __str__(self):
        return self.title


class MapSubmission(models.Model):
    task = models.ForeignKey(GeographyTask, on_delete=models.CASCADE, related_name='submissions')
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name='map_submissions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='map_submissions',
    )
    answer_data = models.JSONField(default=dict, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.task} submission by {self.user}'

# Create your models here.
