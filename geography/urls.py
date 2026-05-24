from django.urls import path

from . import views

app_name = 'geography'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/start-default/', views.start_default_project, name='start_default_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/workspace/', views.workspace, name='workspace'),
    path('api/projects/<int:project_id>/save/', views.save_project_json, name='api_project_save'),
    path('api/projects/<int:project_id>/features/', views.features, name='api_features'),
    path('api/features/<int:feature_id>/update/', views.feature_update, name='api_feature_update'),
    path('api/features/<int:feature_id>/delete/', views.feature_delete, name='api_feature_delete'),
    path('api/features/<int:feature_id>/photos/', views.feature_photo_upload, name='api_feature_photo_upload'),
    path('api/features/<int:feature_id>/notes/', views.feature_note_add, name='api_feature_note_add'),
    path('api/features/<int:feature_id>/report-pdf/', views.feature_report_pdf, name='api_feature_report_pdf'),
    path('api/features/<int:feature_id>/ai/explain/', views.ai_explain_feature, name='api_ai_explain_feature'),
    path(
        'api/features/<int:feature_id>/ai/questions/',
        views.ai_generate_feature_questions,
        name='api_ai_generate_feature_questions',
    ),
    path(
        'api/projects/<int:project_id>/ai/generate-feature-json/',
        views.ai_generate_feature_json,
        name='api_generate_feature_json',
    ),
    path(
        'api/features/<int:feature_id>/public-context/',
        views.public_feature_context,
        name='api_public_feature_context',
    ),
    path('api/features/<int:feature_id>/chat/start/', views.chat_start, name='api_chat_start'),
    path('api/chats/<int:chat_id>/send/', views.chat_send, name='api_chat_send'),
    path('api/chats/<int:chat_id>/messages/', views.chat_messages, name='api_chat_messages'),
    path('api/chats/<int:chat_id>/export-txt/', views.chat_export_txt, name='api_chat_export_txt'),
    path('api/chats/<int:chat_id>/study-notes/', views.chat_study_notes, name='api_chat_study_notes'),
    path('api/projects/<int:project_id>/ai/check/', views.ai_check_project, name='api_ai_check_project'),
    path(
        'api/projects/<int:project_id>/ai/revision-sheet/',
        views.ai_revision_sheet,
        name='api_ai_revision_sheet',
    ),
]
