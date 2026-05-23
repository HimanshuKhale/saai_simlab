from django.contrib import admin

from .models import DecisionJournal, HistoricalCharacterProfile, HistoricalWorld


class HistoricalCharacterProfileInline(admin.TabularInline):
    model = HistoricalCharacterProfile
    extra = 0


@admin.register(HistoricalWorld)
class HistoricalWorldAdmin(admin.ModelAdmin):
    list_display = ('title', 'scenario', 'published', 'updated_at')
    list_filter = ('published', 'scenario__simulation_type')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    inlines = [HistoricalCharacterProfileInline]


@admin.register(HistoricalCharacterProfile)
class HistoricalCharacterProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'world', 'character')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(DecisionJournal)
class DecisionJournalAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'character_profile', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('decision_text', 'user__username')

# Register your models here.
