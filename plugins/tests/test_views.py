import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from plugins.models import Plugin

@pytest.mark.django_db
class TestAuth:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_get_token(self):
        response = self.client.post('/api-token-auth/', {'username': 'testuser', 'password': 'testpassword'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data

@pytest.mark.django_db
class TestPluginSubmission:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword', is_staff=True) # Make user staff
        self.token = Token.objects.get(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_submit_plugin_unauthenticated(self):
        self.client.force_authenticate(user=None, token=None) # Properly de-authenticate
        response = self.client.post('/api/submit/', {'repo_url': 'https://github.com/noatgnu/export_asap_plugin'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_plugin_success(self):
        response = self.client.post('/api/submit/', {'repo_url': 'https://github.com/noatgnu/export_asap_plugin'}, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] == 'export-asap'
        assert Plugin.objects.filter(id='export-asap').exists()

@pytest.mark.django_db
class TestPluginRefresh:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword', is_staff=True) # Make user staff
        self.token = Token.objects.get(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        # First, submit the plugin to have something to refresh
        response = self.client.post('/api/submit/', {'repo_url': 'https://github.com/noatgnu/export_asap_plugin'}, format='json')
        assert response.status_code == status.HTTP_201_CREATED # Ensure plugin was created
        self.plugin = Plugin.objects.get(id='export-asap')


    def test_refresh_plugin_unauthenticated(self):
        self.client.force_authenticate(user=None, token=None) # Properly de-authenticate
        response = self.client.post(f'/api/plugins/{self.plugin.id}/refresh/', format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_plugin_success(self):
        response = self.client.post(f'/api/plugins/{self.plugin.id}/refresh/', format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Export ASAP'

    def test_refresh_plugin_no_repo(self):
        self.plugin.repository = ''
        self.plugin.save()
        response = self.client.post(f'/api/plugins/{self.plugin.id}/refresh/', format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'has no repository URL' in response.data['error']


@pytest.mark.django_db
class TestBatchSubmission:
    def setup_method(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpassword',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpassword',
            is_staff=False
        )
        self.staff_token = Token.objects.get(user=self.staff_user)
        self.regular_token = Token.objects.get(user=self.regular_user)

    def test_batch_submit_unauthenticated(self):
        response = self.client.post(
            '/api/submit/batch_submit/',
            {'repo_urls': ['https://github.com/noatgnu/export_asap_plugin']},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_batch_submit_non_staff_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_token.key)
        response = self.client.post(
            '/api/submit/batch_submit/',
            {'repo_urls': ['https://github.com/noatgnu/export_asap_plugin']},
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'Staff access required' in response.data['error']

    def test_batch_submit_empty_list(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.staff_token.key)
        response = self.client.post(
            '/api/submit/batch_submit/',
            {'repo_urls': []},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_batch_submit_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.staff_token.key)
        response = self.client.post(
            '/api/submit/batch_submit/',
            {'repo_urls': ['https://github.com/noatgnu/export_asap_plugin']},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
        assert response.data['submitted'] == 1
        assert response.data['failed'] == 0
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['success'] is True
        assert response.data['results'][0]['plugin_id'] == 'export-asap'
        assert Plugin.objects.filter(id='export-asap').exists()

    def test_batch_submit_invalid_repo(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.staff_token.key)
        response = self.client.post(
            '/api/submit/batch_submit/',
            {'repo_urls': ['https://github.com/nonexistent/nonexistent_repo_12345']},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
        assert response.data['submitted'] == 0
        assert response.data['failed'] == 1
        assert response.data['results'][0]['success'] is False
