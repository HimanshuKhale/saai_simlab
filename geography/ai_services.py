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
        'explanation': explanation,
        'map_skill_tip': 'Check placement, scale, direction, and nearby related features before finalising the mark.',
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
        ]
    }


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
    }
