import json

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.test.utils import override_settings

from recipes.models import Recipe, RecipeVersion

from .test_recipes import sample_recipe_data


@pytest.mark.django_db
class TestRecipeDownload:
    def setup_method(self):
        self.recipe = Recipe.objects.create(label='Downloadable Recipe', status='approved')
        RecipeVersion.objects.create(recipe=self.recipe, revision=2, data=sample_recipe_data('Downloadable Recipe'))

    def get(self, is_staff=False):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            if is_staff:
                staff = User.objects.create_user(username='staff', password='pw', is_staff=True)
                client.force_login(staff)
            return client.get(f'/recipes/{self.recipe.pk}/download/')

    def test_returns_the_latest_version_data_as_an_attachment(self):
        response = self.get()

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        assert response['Content-Disposition'] == 'attachment; filename="downloadable-recipe.json"'
        assert json.loads(response.content) == sample_recipe_data('Downloadable Recipe')

    def test_anonymous_cannot_download_a_pending_recipe(self):
        pending = Recipe.objects.create(label='Pending Recipe', status='pending')
        RecipeVersion.objects.create(recipe=pending, revision=1, data=sample_recipe_data('Pending Recipe'))

        with override_settings(ALLOWED_HOSTS=['testserver']):
            response = Client().get(f'/recipes/{pending.pk}/download/')

        assert response.status_code == 404

    def test_staff_can_download_a_pending_recipe(self):
        pending = Recipe.objects.create(label='Pending Recipe', status='pending')
        RecipeVersion.objects.create(recipe=pending, revision=1, data=sample_recipe_data('Pending Recipe'))

        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            staff = User.objects.create_user(username='staff2', password='pw', is_staff=True)
            client.force_login(staff)
            response = client.get(f'/recipes/{pending.pk}/download/')

        assert response.status_code == 200

    def test_404_for_a_recipe_with_no_versions(self):
        empty = Recipe.objects.create(label='No Versions', status='approved')

        with override_settings(ALLOWED_HOSTS=['testserver']):
            response = Client().get(f'/recipes/{empty.pk}/download/')

        assert response.status_code == 404

    def test_detail_page_links_to_the_download_view(self):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            response = Client().get(f'/recipes/{self.recipe.pk}/')

        assert f'/recipes/{self.recipe.pk}/download/' in response.content.decode()
