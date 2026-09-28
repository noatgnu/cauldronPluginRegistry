import pytest
from django.test import Client
from django.test.utils import override_settings

from plugins.models import Plugin
from recipes.diagram import (
    _extract_plugin_step_diagram,
    _renamespace_step_lines,
    generate_recipe_diagram,
)
from recipes.models import Recipe, RecipeVersion

from .test_recipes import sample_recipe_data

STEP_DIAGRAM_README = (
    '<h1>Some Plugin</h1>\n'
    '<pre class="mermaid">flowchart TD\n'
    '    Start([Start]) --&gt; step1\n'
    '    step1[Load input]\n'
    '    step1 --&gt; step2\n'
    '    step2[Write output]\n'
    '    step2 --&gt; End([End])\n'
    '</pre>\n'
)


class TestExtractPluginStepDiagram:
    def test_none_without_a_plugin(self):
        assert _extract_plugin_step_diagram(None) is None

    def test_none_without_a_readme(self):
        plugin = Plugin(id='p', name='P', description='', version='1.0.0')
        assert _extract_plugin_step_diagram(plugin) is None

    def test_none_when_readme_has_no_mermaid_block(self):
        plugin = Plugin(id='p', name='P', description='', version='1.0.0', readme='<h1>No diagram here</h1>')
        assert _extract_plugin_step_diagram(plugin) is None

    def test_extracts_and_unescapes_the_diagram_body(self):
        plugin = Plugin(id='p', name='P', description='', version='1.0.0', readme=STEP_DIAGRAM_README)
        lines = _extract_plugin_step_diagram(plugin)
        assert lines is not None
        joined = '\n'.join(lines)
        assert 'flowchart TD' not in joined
        assert 'Start([Start]) --> step1' in joined
        assert 'step2 --> End([End])' in joined


class TestRenamespaceStepLines:
    def test_renames_ids_but_preserves_bracketed_labels(self):
        lines = [
            'Start([Start]) --> step1',
            'step1[Load input]',
            'step1 --> step2',
            'step2[Write output]',
            'step2 --> End([End])',
        ]
        renamed = _renamespace_step_lines(lines, 'S1_step_')
        joined = '\n'.join(renamed)

        assert 'S1_step_Start([Start])' in joined
        assert 'S1_step_step1[Load input]' in joined
        assert 'S1_step_step1 --> S1_step_step2' in joined
        assert 'S1_step_step2 --> S1_step_End([End])' in joined
        assert 'S1_step_Load' not in joined
        assert 'S1_step_input' not in joined


@pytest.mark.django_db
class TestGenerateRecipeDiagramExpanded:
    def test_stage_without_a_registry_plugin_gets_a_plain_anchor_node(self):
        stages = [{'pluginId': 'wide-to-long', 'pluginVersion': '1.0.0', 'params': {}, 'bindings': {}}]
        diagram = generate_recipe_diagram(stages, {}, [0])
        assert 'subgraph S0_group' in diagram
        assert 'S0("wide-to-long")' in diagram
        assert 'step' not in diagram

    def test_stage_with_a_plugin_diagram_nests_its_renamed_steps(self):
        plugin = Plugin(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', readme=STEP_DIAGRAM_README)
        stages = [{'pluginId': 'wide-to-long', 'pluginVersion': '1.0.0', 'params': {}, 'bindings': {}}]

        diagram = generate_recipe_diagram(stages, {'wide-to-long': plugin}, [0])

        assert 'S0_step_step1[Load input]' in diagram
        assert 'S0_step_step2[Write output]' in diagram

    def test_only_listed_stages_are_expanded(self):
        plugin = Plugin(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', readme=STEP_DIAGRAM_README)
        stages = [
            {'pluginId': 'wide-to-long', 'pluginVersion': '1.0.0', 'params': {}, 'bindings': {}},
            {
                'pluginId': 'long-to-wide',
                'pluginVersion': '1.0.0',
                'params': {},
                'bindings': {'input_file': {'stage': 0, 'output': 'long_data'}},
            },
        ]

        diagram = generate_recipe_diagram(stages, {'wide-to-long': plugin}, [0])

        assert 'subgraph S0_group' in diagram
        assert 'subgraph S1_group' not in diagram
        assert 'S1["Stage 2: long-to-wide v1.0.0"]' in diagram

    def test_edges_stay_labeled_even_when_a_stage_is_expanded(self):
        plugin = Plugin(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', readme=STEP_DIAGRAM_README)
        stages = [
            {'pluginId': 'wide-to-long', 'pluginVersion': '1.0.0', 'params': {}, 'bindings': {}},
            {
                'pluginId': 'long-to-wide',
                'pluginVersion': '1.0.0',
                'params': {},
                'bindings': {'input_file': {'stage': 0, 'output': 'long_data'}},
            },
        ]

        diagram = generate_recipe_diagram(stages, {'wide-to-long': plugin}, [0])

        assert 'S0 -->|"long_data"| S1' in diagram


@pytest.mark.django_db
class TestRecipeDiagramView:
    def setup_method(self):
        self.recipe = Recipe.objects.create(label='Expanded Recipe', status='approved')
        RecipeVersion.objects.create(recipe=self.recipe, revision=1, data=sample_recipe_data('Expanded Recipe'))

    def get(self, expand=None):
        url = f'/recipes/{self.recipe.pk}/diagram/'
        if expand is not None:
            url += f'?expand={expand}'
        with override_settings(ALLOWED_HOSTS=['testserver']):
            return Client().get(url)

    def test_defaults_to_fully_collapsed(self):
        response = self.get()
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        body = response.content.decode()
        assert 'subgraph' not in body
        assert 'S0["Stage 1: wide-to-long v1.0.0"]' in body

    def test_expands_only_the_requested_stage(self):
        response = self.get(expand='0')
        body = response.content.decode()
        assert 'subgraph S0_group' in body
        assert 'subgraph S1_group' not in body

    def test_falls_back_to_a_plain_anchor_when_no_plugin_has_a_diagram(self):
        Plugin.objects.create(id='wide-to-long', name='Wide to Long', description='', version='1.0.0', status='approved')
        response = self.get(expand='0')
        body = response.content.decode()
        assert 'S0("wide-to-long")' in body

    def test_nests_a_linked_plugins_step_diagram(self):
        Plugin.objects.create(
            id='wide-to-long', name='Wide to Long', description='', version='1.0.0',
            status='approved', readme=STEP_DIAGRAM_README,
        )
        response = self.get(expand='0')
        body = response.content.decode()
        assert 'S0_step_step1[Load input]' in body

    def test_does_not_expand_a_pending_plugins_step_diagram_for_an_anonymous_viewer(self):
        Plugin.objects.create(
            id='wide-to-long', name='Wide to Long', description='', version='1.0.0',
            status='pending', readme=STEP_DIAGRAM_README,
        )
        response = self.get(expand='0')
        body = response.content.decode()
        assert 'S0_step_step1' not in body

    def test_404_for_a_pending_recipe_as_an_anonymous_viewer(self):
        pending = Recipe.objects.create(label='Pending', status='pending')
        RecipeVersion.objects.create(recipe=pending, revision=1, data=sample_recipe_data('Pending'))
        with override_settings(ALLOWED_HOSTS=['testserver']):
            response = Client().get(f'/recipes/{pending.pk}/diagram/')
        assert response.status_code == 404
