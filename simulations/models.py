from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SimulationType(TimestampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=64, blank=True)
    published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('scenario_list', kwargs={'simulation_type_slug': self.slug})


class Scenario(TimestampedModel):
    simulation_type = models.ForeignKey(
        SimulationType,
        on_delete=models.PROTECT,
        related_name='scenarios',
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)
    summary = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=50, blank=True)
    estimated_minutes = models.PositiveIntegerField(default=45)
    objectives = models.JSONField(default=list, blank=True)
    variables = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['simulation_type__order', 'title']
        constraints = [
            models.UniqueConstraint(
                fields=['simulation_type', 'slug'],
                name='unique_scenario_slug_per_simulation_type',
            )
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'scenario_detail',
            kwargs={
                'simulation_type_slug': self.simulation_type.slug,
                'scenario_slug': self.slug,
            },
        )


class Role(TimestampedModel):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True)
    objectives = models.JSONField(default=list, blank=True)
    initial_state = models.JSONField(default=dict, blank=True)
    max_players = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['scenario', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['scenario', 'slug'],
                name='unique_role_slug_per_scenario',
            )
        ]

    def __str__(self):
        return f'{self.scenario}: {self.name}'


class Character(TimestampedModel):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='characters')
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        related_name='characters',
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)
    persona = models.JSONField(default=dict, blank=True)
    configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['scenario', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['scenario', 'slug'],
                name='unique_character_slug_per_scenario',
            )
        ]

    def __str__(self):
        return self.name


class SimulationSession(TimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    simulation_type = models.ForeignKey(
        SimulationType,
        on_delete=models.PROTECT,
        related_name='sessions',
    )
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name='sessions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulation_sessions',
    )
    selected_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='sessions',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    current_state = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.scenario} session for {self.user}'

    def save(self, *args, **kwargs):
        if self.scenario_id and not self.simulation_type_id:
            self.simulation_type = self.scenario.simulation_type
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('session_detail', kwargs={'session_id': self.pk})


class SimulationEvent(models.Model):
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name='events',
    )
    sequence = models.PositiveIntegerField(default=0)
    event_type = models.CharField(max_length=80)
    actor_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='events',
    )
    actor_character = models.ForeignKey(
        Character,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='events',
    )
    message = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'sequence', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'sequence'],
                name='unique_event_sequence_per_session',
            )
        ]

    def __str__(self):
        return f'{self.session_id} #{self.sequence}: {self.event_type}'

    def save(self, *args, **kwargs):
        if not self.sequence and self.session_id:
            last_event = self.session.events.order_by('-sequence').first()
            self.sequence = (last_event.sequence + 1) if last_event else 1
        super().save(*args, **kwargs)

# Create your models here.
