from django.contrib import admin

from .models import Character, Role, Scenario, SimulationEvent, SimulationSession, SimulationType


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0


class CharacterInline(admin.TabularInline):
    model = Character
    extra = 0


@admin.register(SimulationType)
class SimulationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'published', 'order', 'updated_at')
    list_filter = ('published',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'simulation_type', 'difficulty', 'published', 'updated_at')
    list_filter = ('simulation_type', 'published', 'difficulty')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'summary', 'description')
    inlines = [RoleInline, CharacterInline]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'scenario', 'max_players')
    list_filter = ('scenario__simulation_type',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'scenario', 'role')
    list_filter = ('scenario__simulation_type',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


class SimulationEventInline(admin.TabularInline):
    model = SimulationEvent
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(SimulationSession)
class SimulationSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'scenario', 'user', 'selected_role', 'status', 'started_at')
    list_filter = ('status', 'simulation_type', 'scenario')
    search_fields = ('scenario__title', 'user__username')
    readonly_fields = ('started_at', 'created_at', 'updated_at')
    inlines = [SimulationEventInline]


@admin.register(SimulationEvent)
class SimulationEventAdmin(admin.ModelAdmin):
    list_display = ('session', 'sequence', 'event_type', 'actor_role', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('message', 'session__scenario__title')

# Register your models here.
