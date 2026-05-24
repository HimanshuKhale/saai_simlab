import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods, require_POST

from . import ai_services, external_data, llm_services
from .forms import MapProjectForm
from .models import (
    GeographyAIInteraction,
    GeographyChatMessage,
    GeographyChatSession,
    GeographyStudyNote,
    GeographyTask,
    MapAsset,
    MapFeature,
    MapFeatureNote,
    MapFeaturePhoto,
    MapProject,
)


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _owner_project(request, project_id):
    queryset = MapProject.objects.all() if request.user.is_staff else MapProject.objects.filter(owner=request.user)
    return get_object_or_404(queryset, pk=project_id)


def _review_project(request, project_id):
    project = get_object_or_404(MapProject, pk=project_id)
    if project.owner != request.user and not request.user.is_staff:
        raise PermissionDenied
    return project


def _owner_feature(request, feature_id):
    queryset = MapFeature.objects.select_related('project')
    if not request.user.is_staff:
        queryset = queryset.filter(project__owner=request.user)
    return get_object_or_404(queryset, pk=feature_id)


def _owner_chat(request, chat_id):
    queryset = GeographyChatSession.objects.select_related('project', 'feature', 'user')
    if not request.user.is_staff:
        queryset = queryset.filter(project__owner=request.user)
    return get_object_or_404(queryset, pk=chat_id)


def _bad_json(message, status=400):
    return JsonResponse({'ok': False, 'error': message}, status=status)


def _feature_payload(feature):
    return {
        'id': feature.id,
        'project_id': feature.project_id,
        'name': feature.name,
        'feature_type': feature.feature_type,
        'category': feature.category,
        'icse_force': feature.icse_force,
        'force_type': feature.icse_force,
        'geometry': feature.geometry,
        'style': feature.style,
        'properties': feature.properties,
        'importance_notes': feature.importance_notes,
        'exam_notes': feature.exam_notes,
        'social_studies_notes': feature.social_studies_notes,
        'tags': feature.tags,
        'order': feature.order,
        'photos': [
            {
                'id': photo.id,
                'url': photo.image.url,
                'caption': photo.caption,
                'created_at': photo.created_at.isoformat(),
            }
            for photo in feature.photos.all()
        ],
        'notes': [
            {
                'id': note.id,
                'note_type': note.note_type,
                'body': note.body,
                'tags': note.tags,
                'created_at': note.created_at.isoformat(),
            }
            for note in feature.notes.all()
        ],
        'created_at': feature.created_at.isoformat(),
        'updated_at': feature.updated_at.isoformat(),
    }


def _set_feature_fields(feature, payload):
    scalar_fields = (
        'name',
        'feature_type',
        'category',
        'icse_force',
        'force_type',
        'importance_notes',
        'exam_notes',
        'social_studies_notes',
    )
    json_fields = ('geometry', 'style', 'properties', 'tags')
    for field in scalar_fields:
        if field in payload:
            target_field = 'icse_force' if field == 'force_type' else field
            setattr(feature, target_field, payload.get(field) or '')
    for field in json_fields:
        if field in payload:
            value = payload.get(field)
            setattr(feature, field, value if value is not None else ([] if field == 'tags' else {}))
    if 'order' in payload:
        feature.order = payload.get('order') or 0


@login_required
def dashboard(request):
    recent_projects = MapProject.objects.filter(owner=request.user).select_related('map_asset')[:5]
    map_assets = MapAsset.objects.filter(published=True).order_by('title')[:6]
    return render(
        request,
        'geography/map_dashboard.html',
        {
            'recent_projects': recent_projects,
            'map_assets': map_assets,
        },
    )


@login_required
def project_list(request):
    projects = MapProject.objects.filter(owner=request.user).select_related('map_asset', 'scenario')
    return render(request, 'geography/map_project_list.html', {'projects': projects})


@login_required
def project_create(request):
    initial = {}
    asset_id = request.GET.get('asset')
    task_id = request.GET.get('task')
    if asset_id:
        initial['map_asset'] = asset_id
    if task_id:
        initial['task'] = task_id
        task = GeographyTask.objects.filter(pk=task_id).first()
        if task:
            initial['scenario'] = task.scenario_id
            initial['map_asset'] = task.map_asset_id

    if request.method == 'POST':
        form = MapProjectForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            if project.map_asset:
                project.project_json = project.map_asset.default_project_json or {}
                project.calibration_json = project.map_asset.default_calibration_json or {}
            project.save()
            messages.success(request, 'Map project created.')
            return redirect('geography:workspace', project_id=project.id)
    else:
        form = MapProjectForm(user=request.user, initial=initial)
    return render(request, 'geography/map_project_create.html', {'form': form})


@login_required
def workspace(request, project_id):
    project = _owner_project(request, project_id)
    map_config = {
        'projectId': project.id,
        'projectTitle': project.title,
        'mapImageUrl': project.map_image_url,
        'initialProjectJson': project.project_json,
        'calibrationJson': project.calibration_json,
        'csrfToken': get_token(request),
        'apiUrls': {
            'saveProject': reverse('geography:api_project_save', kwargs={'project_id': project.id}),
            'features': reverse('geography:api_features', kwargs={'project_id': project.id}),
            'checkProject': reverse('geography:api_ai_check_project', kwargs={'project_id': project.id}),
            'revisionSheet': reverse('geography:api_ai_revision_sheet', kwargs={'project_id': project.id}),
            'updateFeatureTemplate': reverse('geography:api_feature_update', kwargs={'feature_id': 0}),
            'deleteFeatureTemplate': reverse('geography:api_feature_delete', kwargs={'feature_id': 0}),
            'uploadPhotoTemplate': reverse('geography:api_feature_photo_upload', kwargs={'feature_id': 0}),
            'addNoteTemplate': reverse('geography:api_feature_note_add', kwargs={'feature_id': 0}),
            'explainFeatureTemplate': reverse('geography:api_ai_explain_feature', kwargs={'feature_id': 0}),
            'generateQuestionsTemplate': reverse(
                'geography:api_ai_generate_feature_questions',
                kwargs={'feature_id': 0},
            ),
            'publicContextTemplate': reverse('geography:api_public_feature_context', kwargs={'feature_id': 0}),
            'startChatTemplate': reverse('geography:api_chat_start', kwargs={'feature_id': 0}),
            'chatMessagesTemplate': reverse('geography:api_chat_messages', kwargs={'chat_id': 0}),
            'chatSendTemplate': reverse('geography:api_chat_send', kwargs={'chat_id': 0}),
            'chatExportTemplate': reverse('geography:api_chat_export_txt', kwargs={'chat_id': 0}),
            'chatStudyNotesTemplate': reverse('geography:api_chat_study_notes', kwargs={'chat_id': 0}),
            'generateFeatureJson': reverse(
                'geography:api_generate_feature_json',
                kwargs={'project_id': project.id},
            ),
        },
    }
    return render(request, 'geography/map_workspace.html', {'project': project, 'map_config': map_config})


@login_required
def project_detail(request, project_id):
    project = _review_project(request, project_id)
    features = project.features.prefetch_related('photos', 'notes')
    interactions = project.ai_interactions.select_related('feature', 'user')[:20]
    return render(
        request,
        'geography/map_project_detail.html',
        {
            'project': project,
            'features': features,
            'interactions': interactions,
        },
    )


@login_required
@require_POST
def save_project_json(request, project_id):
    project = _owner_project(request, project_id)
    payload = _json_body(request)
    if payload is None:
        return HttpResponseBadRequest('Invalid JSON.')
    project.project_json = payload.get('project_json', {})
    if 'calibration_json' in payload:
        project.calibration_json = payload.get('calibration_json') or {}
    project.save(update_fields=['project_json', 'calibration_json', 'updated_at'])
    return JsonResponse({'ok': True, 'project_id': project.id, 'updated_at': project.updated_at.isoformat()})


@login_required
@require_http_methods(['GET', 'POST'])
def features(request, project_id):
    project = _owner_project(request, project_id)
    if request.method == 'GET':
        queryset = project.features.prefetch_related('photos', 'notes')
        return JsonResponse({'features': [_feature_payload(feature) for feature in queryset]})

    payload = _json_body(request)
    if payload is None:
        return HttpResponseBadRequest('Invalid JSON.')
    feature = MapFeature(project=project, name=payload.get('name') or 'Untitled feature')
    _set_feature_fields(feature, payload)
    feature.save()
    return JsonResponse({'ok': True, 'feature': _feature_payload(feature)}, status=201)


@login_required
@require_http_methods(['PATCH', 'POST'])
def feature_update(request, feature_id):
    feature = _owner_feature(request, feature_id)
    payload = _json_body(request)
    if payload is None:
        return HttpResponseBadRequest('Invalid JSON.')
    _set_feature_fields(feature, payload)
    feature.save()
    return JsonResponse({'ok': True, 'feature': _feature_payload(feature)})


@login_required
@require_POST
def feature_delete(request, feature_id):
    feature = _owner_feature(request, feature_id)
    feature.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def feature_photo_upload(request, feature_id):
    feature = _owner_feature(request, feature_id)
    image = request.FILES.get('image')
    if image is None:
        return HttpResponseBadRequest('Image is required.')
    photo = MapFeaturePhoto.objects.create(
        feature=feature,
        uploaded_by=request.user,
        image=image,
        caption=request.POST.get('caption', ''),
    )
    return JsonResponse(
        {
            'ok': True,
            'photo': {
                'id': photo.id,
                'url': photo.image.url,
                'caption': photo.caption,
                'created_at': photo.created_at.isoformat(),
            },
        },
        status=201,
    )


@login_required
@require_POST
def feature_note_add(request, feature_id):
    feature = _owner_feature(request, feature_id)
    payload = _json_body(request)
    if payload is None:
        return HttpResponseBadRequest('Invalid JSON.')
    body = payload.get('body', '').strip()
    if not body:
        return HttpResponseBadRequest('Note body is required.')
    note = MapFeatureNote.objects.create(
        feature=feature,
        author=request.user,
        note_type=payload.get('note_type') or MapFeatureNote.NoteType.GENERAL,
        body=body,
        tags=payload.get('tags') or [],
    )
    return JsonResponse(
        {
            'ok': True,
            'note': {
                'id': note.id,
                'note_type': note.note_type,
                'body': note.body,
                'tags': note.tags,
                'created_at': note.created_at.isoformat(),
            },
        },
        status=201,
    )


def _record_ai(project, user, action, response, feature=None, questions=None):
    return GeographyAIInteraction.objects.create(
        project=project,
        feature=feature,
        user=user,
        action=action,
        input_json={'project_id': project.id, 'feature_id': feature.id if feature else None},
        response_json=response,
        questions_json=questions or [],
    )


def _chat_payload(chat):
    return {
        'id': chat.id,
        'project_id': chat.project_id,
        'feature_id': chat.feature_id,
        'title': chat.title,
        'scope': chat.scope,
        'created_at': chat.created_at.isoformat(),
        'updated_at': chat.updated_at.isoformat(),
    }


def _message_payload(message):
    return {
        'id': message.id,
        'role': message.role,
        'content': message.content,
        'payload': message.payload,
        'created_at': message.created_at.isoformat(),
    }


@login_required
@require_POST
def ai_explain_feature(request, feature_id):
    feature = _owner_feature(request, feature_id)
    response = llm_services.explain_selected_feature_with_llm(feature, feature.project)
    interaction = _record_ai(
        feature.project,
        request.user,
        GeographyAIInteraction.Action.EXPLAIN_FEATURE,
        response,
        feature=feature,
    )
    return JsonResponse({'ok': True, 'interaction_id': interaction.id, 'explanation': response})


@login_required
@require_POST
def ai_generate_feature_questions(request, feature_id):
    feature = _owner_feature(request, feature_id)
    explanation = llm_services.explain_selected_feature_with_llm(feature, feature.project, include_external_data=False)
    response = {
        'questions': explanation.get('questions') or ai_services.generate_feature_questions(feature)['questions'],
        'confidence': explanation.get('confidence', 'low'),
        'warnings': explanation.get('warnings', []),
        'sources_used': explanation.get('sources_used', []),
        'source_basis': explanation.get('source_basis', {}),
        'uncertainty': explanation.get('uncertainty', ''),
        'student_warning': explanation.get('student_warning', ai_services.STUDENT_WARNING),
    }
    interaction = _record_ai(
        feature.project,
        request.user,
        GeographyAIInteraction.Action.GENERATE_QUESTIONS,
        response,
        feature=feature,
        questions=response['questions'],
    )
    return JsonResponse({'ok': True, 'interaction_id': interaction.id, 'questions': response['questions']})


@login_required
@require_POST
def ai_check_project(request, project_id):
    project = _owner_project(request, project_id)
    response = ai_services.check_project(project)
    interaction = _record_ai(project, request.user, GeographyAIInteraction.Action.CHECK_PROJECT, response)
    return JsonResponse(
        {
            'ok': True,
            'interaction_id': interaction.id,
            'findings': response['findings'],
            'missing_items': response['missing_items'],
            'score_hint': response['score_hint'],
            'summary': response['summary'],
        }
    )


@login_required
@require_POST
def ai_revision_sheet(request, project_id):
    project = _owner_project(request, project_id)
    response = llm_services.summarize_project_with_llm(project)
    interaction = _record_ai(project, request.user, GeographyAIInteraction.Action.REVISION_SHEET, response)
    return JsonResponse({'ok': True, 'interaction_id': interaction.id, 'revision_sheet': response})


@login_required
@require_POST
def ai_generate_feature_json(request, project_id):
    project = _owner_project(request, project_id)
    payload = _json_body(request)
    if payload is None:
        return _bad_json('Invalid JSON.')
    description = (payload.get('description') or '')[:llm_services.MAX_GENERATE_PROMPT_LENGTH]
    response = llm_services.generate_feature_json_with_llm(
        project,
        user_request=description,
        feature_type=payload.get('feature_type') or 'point',
        feature_name=payload.get('name') or 'Draft feature',
        description=description,
    )
    if payload.get('force_type') and not response.get('force_type'):
        response['force_type'] = payload['force_type']
    if payload.get('style_preferences') and not response.get('style'):
        response['style'] = payload['style_preferences']
    interaction = _record_ai(
        project,
        request.user,
        GeographyAIInteraction.Action.GENERATE_FEATURE_JSON,
        response,
    )
    warnings = response.get('warnings', [])
    return JsonResponse(
        {
            'ok': True,
            'interaction_id': interaction.id,
            'feature_json': response,
            'warnings': warnings,
            'can_import': True,
        }
    )


@login_required
@require_http_methods(['GET'])
def public_feature_context(request, feature_id):
    feature = _owner_feature(request, feature_id)
    context = external_data.get_public_feature_context(feature)
    context.update(
        ai_services.source_metadata(
            project_feature_data=True,
            external_public_api=True,
            model_general_knowledge=False,
            sources_used=['Nominatim/OpenStreetMap', 'REST Countries', 'Open-Meteo'],
            uncertainty='Public API data may be incomplete or unavailable.',
        )
    )
    _record_ai(
        feature.project,
        request.user,
        GeographyAIInteraction.Action.PUBLIC_CONTEXT,
        context,
        feature=feature,
    )
    return JsonResponse({'ok': True, 'public_context': context})


@login_required
@require_POST
def chat_start(request, feature_id):
    feature = _owner_feature(request, feature_id)
    payload = _json_body(request)
    if payload is None:
        return _bad_json('Invalid JSON.')
    scope = payload.get('scope') or GeographyChatSession.Scope.FEATURE
    if scope not in GeographyChatSession.Scope.values:
        scope = GeographyChatSession.Scope.FEATURE
    chat = GeographyChatSession.objects.create(
        project=feature.project,
        feature=feature if scope == GeographyChatSession.Scope.FEATURE else None,
        user=request.user,
        scope=scope,
        context_snapshot=llm_services.feature_context(feature, include_external_data=False),
    )
    return JsonResponse({'ok': True, 'chat_session': _chat_payload(chat), 'chat_session_id': chat.id}, status=201)


@login_required
@require_POST
def chat_send(request, chat_id):
    chat = _owner_chat(request, chat_id)
    payload = _json_body(request)
    if payload is None:
        return _bad_json('Invalid JSON.')
    message = (payload.get('message') or '').strip()
    if not message:
        return _bad_json('Message is required.')
    if len(message) > llm_services.MAX_CHAT_MESSAGE_LENGTH:
        return _bad_json(f'Message must be {llm_services.MAX_CHAT_MESSAGE_LENGTH} characters or fewer.')
    user_message = GeographyChatMessage.objects.create(
        chat_session=chat,
        role=GeographyChatMessage.Role.USER,
        content=message,
    )
    reply = llm_services.chat_about_feature_with_llm(chat, message)
    assistant_message = GeographyChatMessage.objects.create(
        chat_session=chat,
        role=GeographyChatMessage.Role.ASSISTANT,
        content=reply['assistant_message'],
        payload=reply.get('payload') or {},
    )
    _record_ai(
        chat.project,
        request.user,
        GeographyAIInteraction.Action.CHAT,
        {'assistant_message': assistant_message.content, 'payload': assistant_message.payload},
        feature=chat.feature,
    )
    chat.save(update_fields=['updated_at'])
    return JsonResponse(
        {
            'ok': True,
            'user_message': _message_payload(user_message),
            'assistant_message': assistant_message.content,
            'assistant_message_record': _message_payload(assistant_message),
            'payload': assistant_message.payload,
        }
    )


@login_required
@require_http_methods(['GET'])
def chat_messages(request, chat_id):
    chat = _owner_chat(request, chat_id)
    return JsonResponse(
        {
            'ok': True,
            'chat_session': _chat_payload(chat),
            'messages': [_message_payload(message) for message in chat.messages.all()],
        }
    )


@login_required
@require_http_methods(['GET'])
def chat_export_txt(request, chat_id):
    chat = _owner_chat(request, chat_id)
    feature_name = chat.feature.name if chat.feature else 'None'
    lines = [
        'SAAI Geography AI Chat',
        f'Project: {chat.project.title}',
        f'Feature: {feature_name}',
        f'Created: {chat.created_at}',
        '',
    ]
    for message in chat.messages.all():
        label = 'AI' if message.role == GeographyChatMessage.Role.ASSISTANT else message.role.upper()
        lines.extend([f'{label}:', message.content, ''])
    response = HttpResponse('\n'.join(lines), content_type='text/plain')
    filename = f'geography-chat-{slugify(chat.title) or chat.id}.txt'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_POST
def chat_study_notes(request, chat_id):
    chat = _owner_chat(request, chat_id)
    result = llm_services.convert_chat_to_study_notes_with_llm(chat)
    study_note = GeographyStudyNote.objects.create(
        chat_session=chat,
        project=chat.project,
        feature=chat.feature,
        user=request.user,
        title=result['title'],
        notes_text=result['notes_text'],
        notes_json=result['notes_json'],
    )
    _record_ai(
        chat.project,
        request.user,
        GeographyAIInteraction.Action.STUDY_NOTES,
        result['notes_json'],
        feature=chat.feature,
    )
    return JsonResponse(
        {
            'ok': True,
            'study_note': {
                'id': study_note.id,
                'title': study_note.title,
                'notes_text': study_note.notes_text,
                'notes_json': study_note.notes_json,
            },
        },
        status=201,
    )
