from django.contrib import admin

from .models import GeographyTask, MapAsset, MapSubmission


@admin.register(MapAsset)
class MapAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'published', 'updated_at')
    list_filter = ('published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')


@admin.register(GeographyTask)
class GeographyTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'scenario', 'map_asset', 'published')
    list_filter = ('published', 'scenario__simulation_type')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'instructions')


@admin.register(MapSubmission)
class MapSubmissionAdmin(admin.ModelAdmin):
    list_display = ('task', 'session', 'user', 'score', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('task__title', 'user__username')

# Register your models here.
