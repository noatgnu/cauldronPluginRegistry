import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.test.utils import override_settings

from recipes.models import Recipe, RecipeVersion

from .test_recipes import sample_recipe_data


@pytest.mark.django_db
class TestUserRecipeListView:
    def setup_method(self):
        self.user = User.objects.create_user(username='recipeowner', password='pw')
        self.other_user = User.objects.create_user(username='someoneelse', password='pw')

        self.mine = Recipe.objects.create(label='My Recipe', status='pending', submitted_by=self.user)
        RecipeVersion.objects.create(recipe=self.mine, revision=1, data=sample_recipe_data('My Recipe'))

        self.not_mine = Recipe.objects.create(label='Someone Else Recipe', status='approved', submitted_by=self.other_user)
        RecipeVersion.objects.create(recipe=self.not_mine, revision=1, data=sample_recipe_data('Someone Else Recipe'))

    def test_lists_only_the_current_user_recipes(self):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            client.login(username='recipeowner', password='pw')
            response = client.get('/recipes/my-recipes/')

        assert response.status_code == 200
        assert 'recipes/user_recipe_list.html' in [t.name for t in response.templates]
        labels = {r.label for r in response.context['object_list']}
        assert labels == {'My Recipe'}

    def test_redirects_to_login_when_unauthenticated(self):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            response = Client().get('/recipes/my-recipes/')

        assert response.status_code == 302
        assert '/login/' in response.url

    def test_shows_a_pending_recipe_the_user_owns_even_though_it_is_not_yet_approved(self):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            client.login(username='recipeowner', password='pw')
            response = client.get('/recipes/my-recipes/')

        assert response.status_code == 200
        assert 'My Recipe' in response.content.decode()
