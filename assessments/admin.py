from django.contrib import admin

from .models import EvaluationResult, Rubric


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'simulation_type', 'scenario', 'published', 'updated_at')
    list_filter = ('published', 'simulation_type')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'rubric', 'user', 'score', 'created_at')
    list_filter = ('rubric', 'created_at')
    search_fields = ('session__scenario__title', 'user__username', 'feedback')

# Register your models here.
