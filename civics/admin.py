from django.contrib import admin

from .models import CivicsTurn, ParliamentaryCase, ParliamentaryProcedure


class ParliamentaryProcedureInline(admin.TabularInline):
    model = ParliamentaryProcedure
    extra = 0


@admin.register(ParliamentaryCase)
class ParliamentaryCaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'scenario', 'published', 'updated_at')
    list_filter = ('published', 'scenario__simulation_type')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    inlines = [ParliamentaryProcedureInline]


@admin.register(ParliamentaryProcedure)
class ParliamentaryProcedureAdmin(admin.ModelAdmin):
    list_display = ('title', 'case')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)


@admin.register(CivicsTurn)
class CivicsTurnAdmin(admin.ModelAdmin):
    list_display = ('session', 'sequence', 'role', 'speaker', 'motion_type', 'created_at')
    list_filter = ('motion_type', 'created_at')
    search_fields = ('content', 'speaker__username')

# Register your models here.
