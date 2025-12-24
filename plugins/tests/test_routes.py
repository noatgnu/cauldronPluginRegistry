import pytest
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.test import APIClient
from rest_framework import status
from plugins.models import Plugin, Author, Category, UserProfile

@pytest.mark.django_db
class TestPublicRoutes:
    def setup_method(self):
        self.client = Client()
        self.author = Author.objects.create(name="Test Author")
        self.category = Category.objects.create(name="Test Category")
        self.plugin = Plugin.objects.create(
            id="test-plugin",
            name="Test Plugin",
            description="A test plugin",
            version="1.0.0",
            author=self.author,
            category=self.category,
            status='approved'
        )

    def test_home_page(self):
        response = self.client.get('/')
        assert response.status_code == status.HTTP_200_OK
        assert 'home.html' in [t.name for t in response.templates]

    def test_login_page(self):
        response = self.client.get('/login/')
        assert response.status_code == status.HTTP_200_OK
        assert 'registration/login.html' in [t.name for t in response.templates]

    def test_plugin_list_page(self):
        response = self.client.get('/plugins/')
        assert response.status_code == status.HTTP_200_OK
        assert 'plugins/plugin_list.html' in [t.name for t in response.templates]

    def test_plugin_detail_page(self):
        response = self.client.get(f'/plugins/{self.plugin.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'plugins/plugin_detail.html' in [t.name for t in response.templates]

    def test_plugin_detail_page_pending_returns_404_for_public(self):
        self.plugin.status = 'pending'
        self.plugin.save()
        response = self.client.get(f'/plugins/{self.plugin.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_logout_redirect(self):
        response = self.client.get('/logout/')
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == '/'

    def test_admin_login_page(self):
        response = self.client.get('/admin/login/')
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestProtectedRoutes:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        # UserProfile is created by signal
        self.client.login(username='testuser', password='testpassword')

    def test_plugin_submit_page_authenticated(self):
        response = self.client.get('/plugins/submit/')
        assert response.status_code == status.HTTP_200_OK
        assert 'plugins/plugin_submit.html' in [t.name for t in response.templates]

    def test_user_profile_page_authenticated(self):
        response = self.client.get('/plugins/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert 'plugins/user_profile.html' in [t.name for t in response.templates]

    def test_user_plugin_list_page_authenticated(self):
        response = self.client.get('/plugins/my-plugins/')
        assert response.status_code == status.HTTP_200_OK
        assert 'plugins/user_plugin_list.html' in [t.name for t in response.templates]

    def test_plugin_submit_page_unauthenticated(self):
        self.client.logout()
        response = self.client.get('/plugins/submit/')
        assert response.status_code == status.HTTP_302_FOUND  # Redirect to login
        assert '/login/' in response.url

@pytest.mark.django_db
class TestAPIRoutes:
    def setup_method(self):
        self.client = APIClient()
        self.author = Author.objects.create(name="API Author")
        self.category = Category.objects.create(name="API Category")
        self.plugin = Plugin.objects.create(
            id="api-plugin",
            name="API Plugin",
            description="An API test plugin",
            version="1.0.0",
            author=self.author,
            category=self.category,
            status='approved'
        )

    def test_api_plugin_list(self):
        response = self.client.get('/api/plugins/')
        assert response.status_code == status.HTTP_200_OK

    def test_api_plugin_detail(self):
        response = self.client.get(f'/api/plugins/{self.plugin.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.plugin.id

    def test_api_author_list(self):
        response = self.client.get('/api/authors/')
        assert response.status_code == status.HTTP_200_OK

    def test_api_category_list(self):
        response = self.client.get('/api/categories/')
        assert response.status_code == status.HTTP_200_OK
