import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from plugins.models import Author, Category, Tag
from recipes.models import Recipe, RecipeVersion


def sample_recipe_data(label='Sample'):
    return {
        'version': 1,
        'label': label,
        'stages': [
            {'pluginId': 'wide-to-long', 'pluginVersion': '1.0.0', 'params': {}, 'bindings': {}},
            {
                'pluginId': 'long-to-wide',
                'pluginVersion': '1.0.0',
                'params': {},
                'bindings': {'input_file': {'stage': 0, 'output': 'long_data'}},
            },
        ],
    }


@pytest.mark.django_db
class TestRecipeVisibilityAndFiltering:
    def setup_method(self):
        self.client = APIClient()
        self.author_a = Author.objects.create(name='Author A')
        self.category_qc = Category.objects.create(name='quality-control')
        self.tag = Tag.objects.create(name='proteomics')

        self.approved = Recipe.objects.create(
            label='Approved Recipe', author=self.author_a, category=self.category_qc, status='approved',
        )
        self.approved.tags.add(self.tag)
        RecipeVersion.objects.create(recipe=self.approved, revision=1, data=sample_recipe_data())

        self.pending = Recipe.objects.create(label='Pending Recipe', status='pending')
        RecipeVersion.objects.create(recipe=self.pending, revision=1, data=sample_recipe_data('Pending'))

    def test_anonymous_sees_only_approved(self):
        response = self.client.get('/api/recipes/')
        assert response.status_code == status.HTTP_200_OK
        labels = {r['label'] for r in response.data}
        assert labels == {'Approved Recipe'}

    def test_staff_sees_pending_too(self):
        staff = User.objects.create_user(username='staff', password='pw', is_staff=True)
        self.client.force_authenticate(user=staff)
        response = self.client.get('/api/recipes/')
        labels = {r['label'] for r in response.data}
        assert labels == {'Approved Recipe', 'Pending Recipe'}

    def test_filter_by_category(self):
        response = self.client.get('/api/recipes/', {'category__name': 'quality-control'})
        assert {r['label'] for r in response.data} == {'Approved Recipe'}

    def test_filter_by_tag(self):
        response = self.client.get('/api/recipes/', {'tag': 'proteomics'})
        assert {r['label'] for r in response.data} == {'Approved Recipe'}

    def test_filter_options_scoped_to_approved(self):
        response = self.client.get('/api/recipes/filter_options/')
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data['categories']) == {'quality-control'}
        assert set(response.data['tags']) == {'proteomics'}

    def test_detail_includes_latest_version_data(self):
        response = self.client.get(f'/api/recipes/{self.approved.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['latest_version']['revision'] == 1
        assert response.data['latest_version']['data']['label'] == 'Sample'

    def test_pending_recipe_detail_hidden_from_anonymous(self):
        response = self.client.get(f'/api/recipes/{self.pending.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRecipeSubmission:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='submitter', password='pw')

    def test_submission_requires_authentication(self):
        response = self.client.post('/api/recipe-submit/', {
            'label': 'New Recipe', 'data': sample_recipe_data(),
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submission_creates_recipe_and_first_version(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/recipe-submit/', {
            'label': 'New Recipe', 'category': 'preprocessing', 'tags': ['proteomics'],
            'data': sample_recipe_data(),
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED, response.data
        recipe = Recipe.objects.get(label='New Recipe')
        assert recipe.submitted_by == self.user
        assert recipe.category.name == 'preprocessing'
        assert recipe.latest_version().revision == 1

    def test_resubmission_bumps_revision_and_preserves_owner(self):
        self.client.force_authenticate(user=self.user)
        first = self.client.post('/api/recipe-submit/', {
            'label': 'Iterative Recipe', 'data': sample_recipe_data('v1'),
        }, format='json')
        recipe_id = first.data['id']

        other_user = User.objects.create_user(username='other', password='pw')
        self.client.force_authenticate(user=other_user)
        blocked = self.client.post('/api/recipe-submit/', {
            'recipe_id': recipe_id, 'label': 'Iterative Recipe', 'data': sample_recipe_data('v2'),
        }, format='json')
        assert blocked.status_code == status.HTTP_403_FORBIDDEN

        self.client.force_authenticate(user=self.user)
        second = self.client.post('/api/recipe-submit/', {
            'recipe_id': recipe_id, 'label': 'Iterative Recipe', 'data': sample_recipe_data('v2'),
        }, format='json')
        assert second.status_code == status.HTTP_200_OK, second.data

        recipe = Recipe.objects.get(id=recipe_id)
        assert recipe.submitted_by == self.user
        assert recipe.versions.count() == 2
        assert recipe.latest_version().revision == 2
        assert recipe.latest_version().data['label'] == 'v2'

    def test_submission_rejects_missing_plugin_id(self):
        self.client.force_authenticate(user=self.user)
        bad_data = sample_recipe_data()
        del bad_data['stages'][0]['pluginId']
        response = self.client.post('/api/recipe-submit/', {
            'label': 'Bad Recipe', 'data': bad_data,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submission_rejects_empty_stages(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/recipe-submit/', {
            'label': 'Empty Recipe', 'data': {'version': 1, 'label': 'Empty', 'stages': []},
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pending_by_default_approved_when_auto_approve_enabled(self, settings):
        settings.AUTO_APPROVE_RECIPES = True
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/recipe-submit/', {
            'label': 'Auto Approved', 'data': sample_recipe_data(),
        }, format='json')
        assert response.data['status'] == 'approved'

    def test_pending_status_by_default(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/recipe-submit/', {
            'label': 'Default Status', 'data': sample_recipe_data(),
        }, format='json')
        assert response.data['status'] == 'pending'
