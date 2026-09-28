import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.test.utils import override_settings

from plugins.models import Plugin
from recipes.models import Recipe, RecipeVersion

from .test_recipes import sample_recipe_data


@pytest.mark.django_db
class TestRecipeDetailPluginLinks:
    def setup_method(self):
        self.recipe = Recipe.objects.create(label='Linked Recipe', status='approved')
        RecipeVersion.objects.create(recipe=self.recipe, revision=1, data=sample_recipe_data('Linked Recipe'))

    def get(self, is_staff=False):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            if is_staff:
                staff = User.objects.create_user(username='staff', password='pw', is_staff=True)
                client.force_login(staff)
            return client.get(f'/recipes/{self.recipe.pk}/')

    def test_links_to_a_plugin_that_exists_and_is_approved(self):
        Plugin.objects.create(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', status='approved')

        response = self.get()

        assert response.status_code == 200
        assert f'href="/plugins/wide-to-long/"' in response.content.decode()

    def test_does_not_link_to_a_plugin_that_is_not_in_the_registry(self):
        response = self.get()

        assert response.status_code == 200
        body = response.content.decode()
        assert 'href="/plugins/wide-to-long/"' not in body
        assert '<code>wide-to-long</code>' in body

    def test_does_not_link_to_a_pending_plugin_for_an_anonymous_viewer(self):
        Plugin.objects.create(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', status='pending')

        response = self.get()

        assert response.status_code == 200
        assert 'href="/plugins/wide-to-long/"' not in response.content.decode()

    def test_links_to_a_pending_plugin_for_a_staff_viewer(self):
        Plugin.objects.create(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', status='pending')

        response = self.get(is_staff=True)

        assert response.status_code == 200
        assert 'href="/plugins/wide-to-long/"' in response.content.decode()
