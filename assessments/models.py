from django.conf import settings
from django.db import models

from simulations.models import Scenario, SimulationSession, SimulationType


class Rubric(models.Model):
    simulation_type = models.ForeignKey(
        SimulationType,
        on_delete=models.CASCADE,
        related_name='rubrics',
        blank=True,
        null=True,
    )
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        related_name='rubrics',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=list, blank=True)
    scoring = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class EvaluationResult(models.Model):
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name='evaluation_results',
    )
    rubric = models.ForeignKey(Rubric, on_delete=models.PROTECT, related_name='results')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluation_results',
    )
    evaluator = models.CharField(max_length=120, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    feedback = models.TextField(blank=True)
    result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rubric} result for {self.user}'

# Create your models here.
