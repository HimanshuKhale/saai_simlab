from django.conf import settings
from django.db import models

from simulations.models import Scenario, SimulationSession


class MapAsset(models.Model):
    class AssetType(models.TextChoices):
        PRACTICE = 'practice', 'Practice map'
        TOPOSHEET = 'toposheet', 'Toposheet'
        OUTLINE = 'outline', 'Outline map'
        CUSTOM = 'custom', 'Custom'

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    asset_file = models.FileField(upload_to='maps/', blank=True)
    asset_type = models.CharField(
        max_length=30,
        choices=AssetType.choices,
        default=AssetType.PRACTICE,
    )
    region = models.CharField(max_length=120, blank=True)
    grade_level = models.CharField(max_length=60, blank=True)
    subject = models.CharField(max_length=120, blank=True)
    board = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    default_project_json = models.JSONField(default=dict, blank=True)
    default_calibration_json = models.JSONField(default=dict, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class MapProject(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        IN_REVIEW = 'in_review', 'In review'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='geography_map_projects',
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    map_asset = models.ForeignKey(
        MapAsset,
        on_delete=models.SET_NULL,
        related_name='projects',
        blank=True,
        null=True,
    )
    custom_map_image = models.ImageField(upload_to='geography/project_maps/', blank=True)
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.SET_NULL,
        related_name='map_projects',
        blank=True,
        null=True,
    )
    task = models.ForeignKey(
        'GeographyTask',
        on_delete=models.SET_NULL,
        related_name='map_projects',
        blank=True,
        null=True,
    )
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.SET_NULL,
        related_name='map_projects',
        blank=True,
        null=True,
    )
    project_json = models.JSONField(default=dict, blank=True)
    calibration_json = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    @property
    def map_image_url(self):
        if self.custom_map_image:
            return self.custom_map_image.url
        if self.map_asset and self.map_asset.asset_file:
            return self.map_asset.asset_file.url
        return ''


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


class MapFeature(models.Model):
    class FeatureType(models.TextChoices):
        POINT = 'point', 'Point'
        LINE = 'line', 'Line'
        POLYGON = 'polygon', 'Polygon'
        LABEL = 'label', 'Label'
        MEASURE = 'measure', 'Measure'

    project = models.ForeignKey(MapProject, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=180)
    feature_type = models.CharField(
        max_length=30,
        choices=FeatureType.choices,
        default=FeatureType.POINT,
    )
    category = models.CharField(max_length=80, blank=True)
    icse_force = models.CharField(max_length=80, blank=True)
    geometry = models.JSONField(default=dict, blank=True)
    style = models.JSONField(default=dict, blank=True)
    properties = models.JSONField(default=dict, blank=True)
    importance_notes = models.TextField(blank=True)
    exam_notes = models.TextField(blank=True)
    social_studies_notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class MapFeaturePhoto(models.Model):
    feature = models.ForeignKey(MapFeature, on_delete=models.CASCADE, related_name='photos')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='geography_feature_photos',
    )
    image = models.ImageField(upload_to='geography/feature_photos/')
    caption = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Photo for {self.feature}'


class MapFeatureNote(models.Model):
    class NoteType(models.TextChoices):
        GENERAL = 'general', 'General'
        IMPORTANCE = 'importance', 'Importance'
        EXAM = 'exam', 'Exam'
        SOCIAL_STUDIES = 'social_studies', 'Social studies'

    feature = models.ForeignKey(MapFeature, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='geography_feature_notes',
    )
    note_type = models.CharField(
        max_length=30,
        choices=NoteType.choices,
        default=NoteType.GENERAL,
    )
    body = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_note_type_display()} note for {self.feature}'


class GeographyAIInteraction(models.Model):
    class Action(models.TextChoices):
        EXPLAIN_FEATURE = 'explain_feature', 'Explain feature'
        GENERATE_QUESTIONS = 'generate_questions', 'Generate questions'
        GENERATE_FEATURE_JSON = 'generate_feature_json', 'Generate feature JSON'
        CHAT = 'chat', 'Chat'
        STUDY_NOTES = 'study_notes', 'Study notes'
        PUBLIC_CONTEXT = 'public_context', 'Public context'
        CHECK_PROJECT = 'check_project', 'Check project'
        REVISION_SHEET = 'revision_sheet', 'Revision sheet'

    project = models.ForeignKey(MapProject, on_delete=models.CASCADE, related_name='ai_interactions')
    feature = models.ForeignKey(
        MapFeature,
        on_delete=models.SET_NULL,
        related_name='ai_interactions',
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='geography_ai_interactions',
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    input_json = models.JSONField(default=dict, blank=True)
    response_json = models.JSONField(default=dict, blank=True)
    questions_json = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_action_display()} for {self.project}'


class GeographyChatSession(models.Model):
    class Scope(models.TextChoices):
        FEATURE = 'feature', 'Feature'
        PROJECT = 'project', 'Project'
        GENERAL = 'general', 'General'

    project = models.ForeignKey(MapProject, on_delete=models.CASCADE, related_name='chat_sessions')
    feature = models.ForeignKey(
        MapFeature,
        on_delete=models.SET_NULL,
        related_name='chat_sessions',
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='geography_chat_sessions',
    )
    title = models.CharField(max_length=180, blank=True)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.FEATURE)
    context_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or 'Geography AI Chat'

    def save(self, *args, **kwargs):
        if not self.title:
            if self.scope == self.Scope.FEATURE and self.feature_id:
                self.title = f'Chat: {self.feature.name}'
            elif self.scope == self.Scope.PROJECT:
                self.title = f'Project Chat: {self.project.title}'
            else:
                self.title = 'Geography AI Chat'
        super().save(*args, **kwargs)


class GeographyChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'
        TOOL = 'tool', 'Tool'

    chat_session = models.ForeignKey(
        GeographyChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.get_role_display()} message in {self.chat_session}'


class GeographyStudyNote(models.Model):
    chat_session = models.ForeignKey(
        GeographyChatSession,
        on_delete=models.SET_NULL,
        related_name='study_notes',
        blank=True,
        null=True,
    )
    project = models.ForeignKey(MapProject, on_delete=models.CASCADE, related_name='study_notes')
    feature = models.ForeignKey(
        MapFeature,
        on_delete=models.SET_NULL,
        related_name='study_notes',
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='geography_study_notes',
    )
    title = models.CharField(max_length=180)
    notes_text = models.TextField()
    notes_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class MapSubmission(models.Model):
    task = models.ForeignKey(GeographyTask, on_delete=models.CASCADE, related_name='submissions')
    project = models.ForeignKey(
        MapProject,
        on_delete=models.SET_NULL,
        related_name='submissions',
        blank=True,
        null=True,
    )
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
