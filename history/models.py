from django.conf import settings
from django.db import models

from simulations.models import Character, Scenario, SimulationSession


class HistoricalWorld(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='historical_worlds')
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    timeline = models.JSONField(default=list, blank=True)
    setting = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(fields=['scenario', 'slug'], name='unique_historical_world_slug')
        ]

    def __str__(self):
        return self.title


class HistoricalCharacterProfile(models.Model):
    world = models.ForeignKey(
        HistoricalWorld,
        on_delete=models.CASCADE,
        related_name='character_profiles',
    )
    character = models.ForeignKey(
        Character,
        on_delete=models.SET_NULL,
        related_name='historical_profiles',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    profile = models.JSONField(default=dict, blank=True)
    goals = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['world', 'name']
        constraints = [
            models.UniqueConstraint(fields=['world', 'slug'], name='unique_historical_profile_slug')
        ]

    def __str__(self):
        return self.name


class DecisionJournal(models.Model):
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name='decision_journals',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='decision_journals',
    )
    character_profile = models.ForeignKey(
        HistoricalCharacterProfile,
        on_delete=models.SET_NULL,
        related_name='decision_journals',
        blank=True,
        null=True,
    )
    decision_text = models.TextField()
    state_snapshot = models.JSONField(default=dict, blank=True)
    consequences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Decision by {self.user} in {self.session}'

# Create your models here.
