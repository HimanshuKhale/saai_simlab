STUDENT_WARNING = 'AI explanations are study assistance. Verify with textbook/teacher.'


def source_metadata(
    *,
    project_feature_data=False,
    student_notes=False,
    external_public_api=False,
    model_general_knowledge=True,
    sources_used=None,
    uncertainty='This is a deterministic fallback response.',
):
    return {
        'sources_used': sources_used or [],
        'source_basis': {
            'project_feature_data': project_feature_data,
            'student_notes': student_notes,
            'external_public_api': external_public_api,
            'model_general_knowledge': model_general_knowledge,
        },
        'uncertainty': uncertainty,
        'student_warning': STUDENT_WARNING,
    }


def _feature_label(feature):
    return feature.name or feature.get_feature_type_display()


def explain_feature(feature):
    category = feature.category or 'map feature'
    notes = feature.exam_notes or feature.importance_notes or feature.social_studies_notes
    explanation = f'{_feature_label(feature)} is marked as a {category}.'
    if notes:
        explanation = f'{explanation} Key note: {notes[:240]}'
    return {
        'title': f'Explain {_feature_label(feature)}',
        'summary': explanation,
        'explanation': explanation,
        'detailed_explanation': explanation,
        'physical_geography': 'Review the location, shape, direction, scale, and nearby physical features.',
        'human_geography': 'Connect the feature to settlement, transport, resources, or regional planning where relevant.',
        'economic_importance': feature.importance_notes or 'Add economic importance after checking textbook or class notes.',
        'historical_or_civics_connection': feature.social_studies_notes or 'Add a social studies connection if the feature affects people, governance, or development.',
        'exam_note': feature.exam_notes or 'Write a concise ICSE-style note for revision.',
        'common_mistakes': ['Do not treat approximate placement as exact.', 'Check spelling and map orientation.'],
        'related_features_to_add': [],
        'questions': generate_feature_questions(feature)['questions'],
        'confidence': 'low',
        'map_skill_tip': 'Check placement, scale, direction, and nearby related features before finalising the mark.',
        **source_metadata(
            project_feature_data=True,
            student_notes=bool(notes),
            uncertainty='Fallback explanation based only on saved map data and notes.',
        ),
    }


def generate_feature_questions(feature):
    label = _feature_label(feature)
    category = feature.category or feature.get_feature_type_display().lower()
    return {
        'questions': [
            {
                'question': f'Locate and label {label} on the given map.',
                'answer_hint': f'Use the saved {category} geometry and label placement.',
                'marks': 1,
            },
            {
                'question': f'Give one geographical importance of {label}.',
                'answer_hint': feature.importance_notes or 'Mention location, connectivity, resources, or settlement value.',
                'marks': 2,
            },
            {
                'question': f'Connect {label} with a social studies concept.',
                'answer_hint': feature.social_studies_notes or 'Relate it to population, transport, economy, governance, or environment.',
                'marks': 2,
            },
        ],
        **source_metadata(
            project_feature_data=True,
            student_notes=bool(feature.importance_notes or feature.exam_notes or feature.social_studies_notes),
            uncertainty='Fallback questions generated from saved feature fields.',
        ),
    }


def generate_feature_json(project, payload):
    name = payload.get('name') or payload.get('feature_name') or 'Draft feature'
    feature_type = payload.get('feature_type') or 'point'
    force_type = payload.get('force_type') or payload.get('category') or ''
    warnings = [
        'Precise geometry was not generated. Place or edit points manually on the map.',
    ]
    return {
        'name': name,
        'feature_type': feature_type,
        'force_type': force_type,
        'geometry': {'points': []},
        'geometry_accuracy': 'manual_required',
        'style': payload.get('style_preferences') or {},
        'short_note': f'Draft feature for {project.title}.',
        'detailed_note': payload.get('description', '')[:600],
        'importance': '',
        'exam_note': 'Add verified textbook-aligned exam notes before final use.',
        'social_studies_connection': '',
        'tags': [],
        'ai_summary': 'Fallback draft created without precise geometry.',
        'ai_questions': [],
        'confidence': 'low',
        'warnings': warnings,
        **source_metadata(
            project_feature_data=True,
            student_notes=False,
            model_general_knowledge=False,
            uncertainty='Fallback draft; geometry requires manual placement.',
        ),
    }


def chat_reply(chat_session, user_message):
    feature = chat_session.feature
    feature_name = feature.name if feature else chat_session.project.title
    return {
        'assistant_message': (
            f'I can help you study {feature_name}. Based on saved map data, start by checking location, '
            'importance, related features, and likely ICSE-style questions.'
        ),
        'payload': {
            'confidence': 'low',
            **source_metadata(
                project_feature_data=True,
                student_notes=bool(feature and (feature.importance_notes or feature.exam_notes)),
                uncertainty='Fallback chat response; no live model was used.',
            ),
        },
    }


def study_notes_from_chat(chat_session):
    feature = chat_session.feature
    title = f'Study Notes: {feature.name}' if feature else f'Study Notes: {chat_session.project.title}'
    notes_json = {
        'summary': f'Revision notes for {feature.name if feature else chat_session.project.title}.',
        'key_concepts': ['location', 'map marking', 'importance', 'related features'],
        'feature_explanation': feature.exam_notes if feature else chat_session.project.description,
        'physical_geography_points': [],
        'human_economic_geography_points': [],
        'social_studies_connections': [],
        'important_terms': [],
        'exam_questions': [],
        'short_answer_practice': [],
        'long_answer_practice': [],
        'revision_checklist': ['Verify facts with textbook/teacher.', 'Check map placement and labels.'],
        **source_metadata(
            project_feature_data=True,
            student_notes=bool(feature and (feature.importance_notes or feature.exam_notes)),
            uncertainty='Fallback study notes generated from saved chat context.',
        ),
    }
    notes_text = (
        f'{title}\n\nSummary\n{notes_json["summary"]}\n\nRevision checklist\n'
        '- Verify facts with textbook/teacher.\n- Check map placement and labels.'
    )
    return {'title': title, 'notes_text': notes_text, 'notes_json': notes_json}


def check_project(project):
    features = list(project.features.all())
    feature_count = len(features)
    missing_items = []
    if feature_count == 0:
        missing_items.append('Add at least one marked feature.')
    if not project.calibration_json:
        missing_items.append('Complete map calibration for stronger measurement accuracy.')
    if not any(feature.exam_notes for feature in features):
        missing_items.append('Add exam notes to at least one feature.')
    score_hint = min(100, 35 + feature_count * 10)
    if missing_items:
        score_hint = max(20, score_hint - len(missing_items) * 10)
    return {
        'summary': f'{project.title} has {feature_count} saved feature(s).',
        'findings': [
            'Feature data, notes, and calibration were checked with deterministic placeholder logic.',
            'Review category filters and labels before export.',
        ],
        'missing_items': missing_items,
        'score_hint': score_hint,
        'confidence': 'low',
        **source_metadata(
            project_feature_data=True,
            student_notes=any(
                feature.importance_notes or feature.exam_notes or feature.social_studies_notes
                for feature in features
            ),
            uncertainty='Fallback project check from saved feature counts and notes.',
        ),
    }


def generate_revision_sheet(project):
    features = list(project.features.all()[:12])
    return {
        'title': f'Revision Sheet: {project.title}',
        'key_features': [
            {
                'name': feature.name,
                'type': feature.get_feature_type_display(),
                'category': feature.category,
                'importance': feature.importance_notes,
            }
            for feature in features
        ],
        'exam_notes': [
            feature.exam_notes
            for feature in features
            if feature.exam_notes
        ],
        'quick_questions': [
            f'Why is {feature.name} important on this map?'
            for feature in features[:5]
        ],
        'confidence': 'low',
        **source_metadata(
            project_feature_data=True,
            student_notes=any(feature.exam_notes for feature in features),
            uncertainty='Fallback revision sheet based on saved features.',
        ),
    }
