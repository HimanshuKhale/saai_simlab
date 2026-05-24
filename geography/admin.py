from django.contrib import admin

from .models import (
    GeographyAIInteraction,
    GeographyTask,
    MapAsset,
    MapFeature,
    MapFeatureNote,
    MapFeaturePhoto,
    MapProject,
    MapSubmission,
)


@admin.register(MapAsset)
class MapAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'asset_type', 'grade_level', 'has_asset_file', 'published', 'updated_at')
    list_filter = ('published', 'asset_type', 'grade_level')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')

    @admin.display(boolean=True, description='Asset file')
    def has_asset_file(self, obj):
        return bool(obj.asset_file)


@admin.register(GeographyTask)
class GeographyTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'scenario', 'map_asset', 'published')
    list_filter = ('published', 'scenario__simulation_type')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'instructions')


@admin.register(MapProject)
class MapProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'map_asset', 'scenario', 'status', 'updated_at')
    list_filter = ('status', 'map_asset', 'scenario')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MapFeature)
class MapFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'feature_type', 'category', 'updated_at')
    list_filter = ('feature_type', 'category', 'icse_force')
    search_fields = (
        'name',
        'category',
        'importance_notes',
        'exam_notes',
        'social_studies_notes',
        'project__title',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MapFeaturePhoto)
class MapFeaturePhotoAdmin(admin.ModelAdmin):
    list_display = ('feature', 'uploaded_by', 'caption', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('feature__name', 'caption', 'uploaded_by__username')


@admin.register(MapFeatureNote)
class MapFeatureNoteAdmin(admin.ModelAdmin):
    list_display = ('feature', 'note_type', 'author', 'updated_at')
    list_filter = ('note_type', 'created_at')
    search_fields = ('feature__name', 'body', 'author__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GeographyAIInteraction)
class GeographyAIInteractionAdmin(admin.ModelAdmin):
    list_display = ('action', 'project', 'feature', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('project__title', 'feature__name', 'user__username')


@admin.register(MapSubmission)
class MapSubmissionAdmin(admin.ModelAdmin):
    list_display = ('task', 'project', 'session', 'user', 'score', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('task__title', 'project__title', 'user__username')

# Register your models here.
