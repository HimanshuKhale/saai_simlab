import json
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import MapFeature, MapFeatureNote, MapFeaturePhoto, MapProject


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class GeographyMapLabTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username='student', password='pass12345')
        self.other_user = user_model.objects.create_user(username='other', password='pass12345')
        self.project = MapProject.objects.create(owner=self.user, title='India practice')
        self.feature = MapFeature.objects.create(
            project=self.project,
            name='Narmada River',
            feature_type=MapFeature.FeatureType.LINE,
            category='river',
            geometry={'points': [{'x': 10, 'y': 20}, {'x': 30, 'y': 40}]},
            exam_notes='West flowing river.',
        )

    def login(self):
        self.client.login(username='student', password='pass12345')

    def test_authenticated_user_can_create_map_project(self):
        self.login()
        response = self.client.post(
            reverse('geography:project_create'),
            {
                'title': 'Custom project',
                'description': 'Practice map',
            },
        )
        project = MapProject.objects.get(title='Custom project')
        self.assertEqual(project.owner, self.user)
        self.assertRedirects(response, reverse('geography:workspace', kwargs={'project_id': project.id}))

    def test_unauthenticated_user_is_redirected_from_project_pages(self):
        urls = [
            reverse('geography:project_list'),
            reverse('geography:project_create'),
            reverse('geography:workspace', kwargs={'project_id': self.project.id}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response['Location'])

    def test_owner_can_access_workspace(self):
        self.login()
        response = self.client.get(reverse('geography:workspace', kwargs={'project_id': self.project.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'India practice')

    def test_non_owner_cannot_access_workspace(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.get(reverse('geography:workspace', kwargs={'project_id': self.project.id}))
        self.assertEqual(response.status_code, 404)

    def test_save_project_json_updates_project(self):
        self.login()
        payload = {
            'project_json': {'features': [{'name': 'A'}]},
            'calibration_json': {'mode': 'four_point'},
        }
        response = self.client.post(
            reverse('geography:api_project_save', kwargs={'project_id': self.project.id}),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.project_json, payload['project_json'])
        self.assertEqual(self.project.calibration_json, payload['calibration_json'])

    def test_feature_create_update_delete_works_for_owner(self):
        self.login()
        create_response = self.client.post(
            reverse('geography:api_features', kwargs={'project_id': self.project.id}),
            data=json.dumps(
                {
                    'name': 'Bhopal',
                    'feature_type': 'point',
                    'category': 'city',
                    'geometry': {'points': [{'x': 50, 'y': 45}]},
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(create_response.status_code, 201)
        feature_id = create_response.json()['feature']['id']

        update_response = self.client.post(
            reverse('geography:api_feature_update', kwargs={'feature_id': feature_id}),
            data=json.dumps({'name': 'Bhopal City', 'importance_notes': 'State capital.'}),
            content_type='application/json',
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()['feature']['name'], 'Bhopal City')

        delete_response = self.client.post(
            reverse('geography:api_feature_delete', kwargs={'feature_id': feature_id}),
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(MapFeature.objects.filter(pk=feature_id).exists())

    def test_non_owner_cannot_use_feature_api(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.post(
            reverse('geography:api_feature_update', kwargs={'feature_id': self.feature.id}),
            data=json.dumps({'name': 'Changed'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_photo_upload_works_with_test_image(self):
        self.login()
        image = SimpleUploadedFile(
            'map.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
            content_type='image/gif',
        )
        response = self.client.post(
            reverse('geography:api_feature_photo_upload', kwargs={'feature_id': self.feature.id}),
            data={'image': image, 'caption': 'Field photo'},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(MapFeaturePhoto.objects.count(), 1)
        self.assertEqual(response.json()['photo']['caption'], 'Field photo')

    def test_note_create_works(self):
        self.login()
        response = self.client.post(
            reverse('geography:api_feature_note_add', kwargs={'feature_id': self.feature.id}),
            data=json.dumps({'note_type': 'exam', 'body': 'Remember direction of flow.'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(MapFeatureNote.objects.count(), 1)

    def test_ai_placeholder_endpoints_return_json(self):
        self.login()
        explain_response = self.client.post(
            reverse('geography:api_ai_explain_feature', kwargs={'feature_id': self.feature.id}),
        )
        questions_response = self.client.post(
            reverse('geography:api_ai_generate_feature_questions', kwargs={'feature_id': self.feature.id}),
        )
        check_response = self.client.post(
            reverse('geography:api_ai_check_project', kwargs={'project_id': self.project.id}),
        )
        revision_response = self.client.post(
            reverse('geography:api_ai_revision_sheet', kwargs={'project_id': self.project.id}),
        )
        self.assertEqual(explain_response.status_code, 200)
        self.assertIn('explanation', explain_response.json())
        self.assertEqual(questions_response.status_code, 200)
        self.assertIn('questions', questions_response.json())
        self.assertEqual(check_response.status_code, 200)
        self.assertIn('score_hint', check_response.json())
        self.assertEqual(revision_response.status_code, 200)
        self.assertIn('revision_sheet', revision_response.json())

    def test_project_detail_page_loads(self):
        self.login()
        response = self.client.get(reverse('geography:project_detail', kwargs={'project_id': self.project.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Narmada River')
