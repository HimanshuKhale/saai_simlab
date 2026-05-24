import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from . import ai_services
from .forms import MapProjectForm
from .models import (
    GeographyAIInteraction,
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
    return get_object_or_404(MapProject, pk=project_id, owner=request.user)


def _review_project(request, project_id):
    project = get_object_or_404(MapProject, pk=project_id)
    if project.owner != request.user and not request.user.is_staff:
        raise PermissionDenied
    return project


def _owner_feature(request, feature_id):
    return get_object_or_404(MapFeature.objects.select_related('project'), pk=feature_id, project__owner=request.user)


def _feature_payload(feature):
    return {
        'id': feature.id,
        'project_id': feature.project_id,
        'name': feature.name,
        'feature_type': feature.feature_type,
        'category': feature.category,
        'icse_force': feature.icse_force,
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
        'importance_notes',
        'exam_notes',
        'social_studies_notes',
    )
    json_fields = ('geometry', 'style', 'properties', 'tags')
    for field in scalar_fields:
        if field in payload:
            setattr(feature, field, payload.get(field) or '')
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


@login_required
@require_POST
def ai_explain_feature(request, feature_id):
    feature = _owner_feature(request, feature_id)
    response = ai_services.explain_feature(feature)
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
    response = ai_services.generate_feature_questions(feature)
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
    response = ai_services.generate_revision_sheet(project)
    interaction = _record_ai(project, request.user, GeographyAIInteraction.Action.REVISION_SHEET, response)
    return JsonResponse({'ok': True, 'interaction_id': interaction.id, 'revision_sheet': response})
