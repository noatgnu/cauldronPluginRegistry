import pytest
from rest_framework.test import APIClient
from rest_framework import status
from plugins.models import Plugin, Author, Category, Runtime, Tag


@pytest.mark.django_db
class TestPluginFilters:
    def setup_method(self):
        self.client = APIClient()

        self.author_a = Author.objects.create(name='Author A')
        self.author_b = Author.objects.create(name='Author B')
        self.category_qc = Category.objects.create(name='quality-control')
        self.category_util = Category.objects.create(name='utilities')

        self.plugin_python = Plugin.objects.create(
            id='python-plugin', name='Python Plugin', version='1.0.0',
            author=self.author_a, category=self.category_qc,
            subcategory='reporting', status='approved',
            requires_authentication=True,
        )
        Runtime.objects.create(plugin=self.plugin_python, environments=['python'], entrypoint='run.py')
        tag = Tag.objects.create(name='proteomics')
        self.plugin_python.tags.add(tag)

        self.plugin_r = Plugin.objects.create(
            id='r-plugin', name='R Plugin', version='1.0.0',
            author=self.author_b, category=self.category_util,
            subcategory='analysis', status='approved',
            requires_authentication=False,
        )
        Runtime.objects.create(plugin=self.plugin_r, environments=['r'], entrypoint='run.R')

        self.plugin_pending = Plugin.objects.create(
            id='pending-plugin', name='Pending Plugin', version='1.0.0',
            author=self.author_a, category=self.category_qc,
            status='pending',
        )
        Runtime.objects.create(plugin=self.plugin_pending, environments=['python'], entrypoint='run.py')

    def test_filter_by_category(self):
        response = self.client.get('/api/plugins/', {'category__name': 'quality-control'})
        assert response.status_code == status.HTTP_200_OK
        ids = {p['id'] for p in response.data}
        assert ids == {'python-plugin'}

    def test_filter_by_subcategory(self):
        response = self.client.get('/api/plugins/', {'subcategory': 'analysis'})
        assert {p['id'] for p in response.data} == {'r-plugin'}

    def test_filter_by_language(self):
        response = self.client.get('/api/plugins/', {'language': 'r'})
        assert {p['id'] for p in response.data} == {'r-plugin'}

    def test_filter_by_tag(self):
        response = self.client.get('/api/plugins/', {'tag': 'proteomics'})
        assert {p['id'] for p in response.data} == {'python-plugin'}

    def test_diagram_citation_and_authentication_are_not_filterable(self):
        response = self.client.get('/api/plugins/', {
            'diagram_enabled': 'true', 'citation_enabled': 'true', 'requires_authentication': 'true',
        })
        assert {p['id'] for p in response.data} == {'python-plugin', 'r-plugin'}

    def test_pending_plugin_excluded_for_anonymous(self):
        response = self.client.get('/api/plugins/', {'language': 'python'})
        assert {p['id'] for p in response.data} == {'python-plugin'}

    def test_filter_options_scoped_to_approved(self):
        response = self.client.get('/api/plugins/filter_options/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert set(data['categories']) == {'quality-control', 'utilities'}
        assert set(data['subcategories']) == {'reporting', 'analysis'}
        assert set(data['authors']) == {'Author A', 'Author B'}
        assert set(data['tags']) == {'proteomics'}
        assert set(data['languages']) == {'python', 'r'}

    def test_django_list_page_filters_by_language(self):
        response = self.client.get('/plugins/', {'language': 'r'})
        assert response.status_code == status.HTTP_200_OK
        ids = {p.id for p in response.context['object_list']}
        assert ids == {'r-plugin'}

    def test_django_list_page_no_filter_returns_all_approved(self):
        response = self.client.get('/plugins/')
        ids = {p.id for p in response.context['object_list']}
        assert ids == {'python-plugin', 'r-plugin'}

    def test_django_list_page_exposes_filter_options_in_context(self):
        response = self.client.get('/plugins/')
        assert set(response.context['categories']) == {'quality-control', 'utilities'}
        assert set(response.context['languages']) == {'python', 'r'}
        assert set(response.context['tags']) == {'proteomics'}
