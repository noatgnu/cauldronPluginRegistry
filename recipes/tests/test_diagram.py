import pytest
from django.test import Client
from django.test.utils import override_settings

from recipes.diagram import generate_recipe_diagram
from recipes.models import Recipe, RecipeVersion

from .test_recipes import sample_recipe_data


class TestGenerateRecipeDiagramCollapsed:
    def test_empty_stages_returns_empty_string(self):
        assert generate_recipe_diagram([], {}, []) == ''

    def test_renders_a_node_per_stage(self):
        diagram = generate_recipe_diagram(sample_recipe_data()['stages'], {}, [])
        assert diagram.startswith('flowchart TD')
        assert 'S0["Stage 1: wide-to-long v1.0.0"]' in diagram
        assert 'S1["Stage 2: long-to-wide v1.0.0"]' in diagram

    def test_renders_a_binding_edge(self):
        diagram = generate_recipe_diagram(sample_recipe_data()['stages'], {}, [])
        assert 'S0 -->|"long_data"| S1' in diagram

    def test_ignores_stages_with_no_bindings(self):
        stages = [{'pluginId': 'solo', 'pluginVersion': '1.0.0', 'params': {}, 'bindings': {}}]
        diagram = generate_recipe_diagram(stages, {}, [])
        assert '-->' not in diagram

    def test_escapes_double_quotes_in_labels(self):
        stages = [{'pluginId': 'weird"plugin', 'pluginVersion': '', 'params': {}, 'bindings': {}}]
        diagram = generate_recipe_diagram(stages, {}, [])
        assert 'weird#quot;plugin' in diagram
        assert 'weird"plugin' not in diagram.replace('#quot;', '')

    def test_defaults_to_no_expansion_when_omitted(self):
        diagram = generate_recipe_diagram(sample_recipe_data()['stages'], {})
        assert 'subgraph' not in diagram


@pytest.mark.django_db
class TestRecipeDetailDiagram:
    def setup_method(self):
        self.recipe = Recipe.objects.create(label='Diagram Recipe', status='approved')
        RecipeVersion.objects.create(recipe=self.recipe, revision=1, data=sample_recipe_data('Diagram Recipe'))

    def test_detail_page_embeds_the_collapsed_diagram_source(self):
        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            response = client.get(f'/recipes/{self.recipe.pk}/')
        assert response.status_code == 200
        body = response.content.decode()
        assert 'id="recipe-diagram-source"' in body
        assert 'S0 --&gt;|&quot;long_data&quot;| S1' in body
        assert 'subgraph' not in body

    def test_detail_page_omits_diagram_block_with_no_stages(self):
        empty_recipe = Recipe.objects.create(label='No Stages', status='approved')
        RecipeVersion.objects.create(recipe=empty_recipe, revision=1, data={'version': 1, 'label': 'No Stages', 'stages': []})
        with override_settings(ALLOWED_HOSTS=['testserver']):
            client = Client()
            response = client.get(f'/recipes/{empty_recipe.pk}/')
        assert response.status_code == 200
        assert 'id="recipe-diagram-source"' not in response.content.decode()
