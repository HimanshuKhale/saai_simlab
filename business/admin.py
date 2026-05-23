from django.contrib import admin

from .models import BusinessAgentProfile, BusinessDocument, BusinessScenario


class BusinessAgentProfileInline(admin.TabularInline):
    model = BusinessAgentProfile
    extra = 0


@admin.register(BusinessScenario)
class BusinessScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'scenario', 'published', 'updated_at')
    list_filter = ('published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')
    inlines = [BusinessAgentProfileInline]


@admin.register(BusinessAgentProfile)
class BusinessAgentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_scenario', 'role')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(BusinessDocument)
class BusinessDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'business_scenario', 'document_type', 'user', 'updated_at')
    list_filter = ('document_type', 'updated_at')
    search_fields = ('title', 'content')

# Register your models here.
