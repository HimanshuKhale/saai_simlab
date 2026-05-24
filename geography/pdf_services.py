from datetime import datetime
from io import BytesIO

from . import ai_services

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
except ImportError:
    A4 = None


def _first_geo(feature):
    for point in (feature.geometry or {}).get('points') or []:
        geo = point.get('geo') if isinstance(point, dict) else None
        if geo:
            return geo
    return {}


def _latest_ai_explanation(feature):
    interaction = feature.ai_interactions.filter(action='explain_feature').first()
    if interaction:
        return interaction.response_json
    return ai_services.explain_feature(feature)


def _plain_pdf_fallback(text):
    escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    content = f'BT /F1 11 Tf 40 800 Td ({escaped[:2500]}) Tj ET'
    return (
        b'%PDF-1.4\n'
        b'1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n'
        b'2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n'
        b'3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n'
        b'4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n'
        + f'5 0 obj << /Length {len(content)} >> stream\n'.encode('ascii')
        + content.encode('latin-1', errors='ignore')
        + b'\nendstream endobj\nxref\n0 6\n0000000000 65535 f \ntrailer << /Root 1 0 R >>\n%%EOF\n'
    )


def _paragraph(story, styles, title, value):
    if value:
        story.append(Paragraph(f'<b>{title}</b>', styles['Heading4']))
        story.append(Paragraph(str(value).replace('\n', '<br/>'), styles['BodyText']))
        story.append(Spacer(1, 8))


def build_feature_report_pdf(feature):
    project = feature.project
    geo = _first_geo(feature)
    ai = _latest_ai_explanation(feature)
    questions = ai.get('possible_questions') or ai.get('questions') or []
    text_summary = (
        f'SAAI Geography Map Lab\nProject: {project.title}\nFeature: {feature.name}\n'
        'AI-assisted study material. Verify with textbook/teacher.'
    )
    if A4 is None:
        return _plain_pdf_fallback(text_summary)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f'Feature Report: {feature.name}')
    styles = getSampleStyleSheet()
    story = [
        Paragraph('SAAI Geography Map Lab', styles['Title']),
        Paragraph('Feature Report', styles['Heading2']),
        Paragraph(f'Generated: {datetime.now():%Y-%m-%d %H:%M}', styles['BodyText']),
        Spacer(1, 10),
    ]
    _paragraph(story, styles, 'Project title', project.title)
    _paragraph(story, styles, 'Map asset', project.map_asset.title if project.map_asset else 'Custom map')
    _paragraph(story, styles, 'Feature name', feature.name)
    _paragraph(story, styles, 'Feature type/category', f'{feature.feature_type} / {feature.category or feature.icse_force}')
    if geo:
        _paragraph(
            story,
            styles,
            'Approximate latitude/longitude',
            f'{geo.get("lat")}, {geo.get("lng")} ({geo.get("accuracy", "unknown accuracy")})',
        )
        _paragraph(story, styles, 'Coordinate warning', geo.get('warning'))
    _paragraph(story, styles, 'Importance', feature.importance_notes)
    _paragraph(story, styles, 'Exam note', feature.exam_notes)
    _paragraph(story, styles, 'Social studies connection', feature.social_studies_notes)
    _paragraph(story, styles, 'AI summary', ai.get('summary') or ai.get('explanation'))
    _paragraph(story, styles, 'AI detailed explanation', ai.get('detailed_explanation'))
    if questions:
        _paragraph(
            story,
            styles,
            'AI possible questions',
            '<br/>'.join(
                question.get('question', str(question)) if isinstance(question, dict) else str(question)
                for question in questions
            ),
        )
    for note in feature.notes.all():
        _paragraph(story, styles, f'User note: {note.get_note_type_display()}', note.body)
    for photo in feature.photos.all():
        _paragraph(story, styles, 'Photo caption', photo.caption or 'No caption')
        _paragraph(story, styles, 'Photo source', photo.source)
        try:
            story.append(Image(photo.image.path, width=220, height=150))
            story.append(Spacer(1, 8))
        except Exception:
            _paragraph(story, styles, 'Photo', photo.image.name)
    _paragraph(
        story,
        styles,
        'Verification warning',
        'AI-assisted study material. Verify with textbook/teacher.',
    )
    doc.build(story)
    return buffer.getvalue()
