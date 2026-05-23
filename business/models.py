from django.conf import settings
from django.db import models

from simulations.models import Role, Scenario, SimulationSession


class BusinessScenario(models.Model):
    scenario = models.OneToOneField(
        Scenario,
        on_delete=models.CASCADE,
        related_name='business_detail',
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    negotiation_variables = models.JSONField(default=dict, blank=True)
    documents_required = models.JSONField(default=list, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class BusinessAgentProfile(models.Model):
    business_scenario = models.ForeignKey(
        BusinessScenario,
        on_delete=models.CASCADE,
        related_name='agent_profiles',
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, related_name='business_profiles', blank=True, null=True)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    objectives = models.JSONField(default=list, blank=True)
    constraints = models.JSONField(default=dict, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['business_scenario', 'name']
        constraints = [
            models.UniqueConstraint(fields=['business_scenario', 'slug'], name='unique_business_agent_slug')
        ]

    def __str__(self):
        return self.name


class BusinessDocument(models.Model):
    business_scenario = models.ForeignKey(
        BusinessScenario,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name='business_documents',
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='business_documents',
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=180)
    document_type = models.CharField(max_length=80)
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

# Create your models here.
