from django.conf import settings
from django.db import models

from simulations.models import Role, Scenario, SimulationSession


class ParliamentaryCase(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='parliamentary_cases')
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(fields=['scenario', 'slug'], name='unique_parliamentary_case_slug')
        ]

    def __str__(self):
        return self.title


class ParliamentaryProcedure(models.Model):
    case = models.ForeignKey(
        ParliamentaryCase,
        on_delete=models.CASCADE,
        related_name='procedures',
    )
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    rules = models.JSONField(default=list, blank=True)
    steps = models.JSONField(default=list, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['case', 'title']
        constraints = [
            models.UniqueConstraint(fields=['case', 'slug'], name='unique_procedure_slug_per_case')
        ]

    def __str__(self):
        return self.title


class CivicsTurn(models.Model):
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name='civics_turns')
    procedure = models.ForeignKey(
        ParliamentaryProcedure,
        on_delete=models.SET_NULL,
        related_name='turns',
        blank=True,
        null=True,
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, related_name='civics_turns', blank=True, null=True)
    speaker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='civics_turns',
        blank=True,
        null=True,
    )
    sequence = models.PositiveIntegerField(default=1)
    motion_type = models.CharField(max_length=80, blank=True)
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'sequence']
        constraints = [
            models.UniqueConstraint(fields=['session', 'sequence'], name='unique_civics_turn_sequence')
        ]

    def __str__(self):
        return f'{self.session_id} turn {self.sequence}'

# Create your models here.
