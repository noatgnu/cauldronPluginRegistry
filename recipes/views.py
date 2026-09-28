import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.test import RequestFactory
from django.utils.text import slugify
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from plugins.models import Plugin

from .diagram import generate_recipe_diagram
from .filtering import apply_recipe_filters, recipe_filter_options, visible_recipes
from .forms import RecipeSubmitForm
from .models import Recipe
from .viewsets import RecipeSubmissionViewSet


class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'

    def get_queryset(self):
        queryset = visible_recipes(self.request.user)
        queryset = apply_recipe_filters(queryset, self.request.GET)
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(label__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(recipe_filter_options(visible_recipes(self.request.user)))
        context['selected'] = {
            'q': self.request.GET.get('q', ''),
            'category__name': self.request.GET.get('category__name', ''),
            'tag': self.request.GET.get('tag', ''),
        }
        return context


def _recipe_stages(recipe):
    version = recipe.latest_version()
    return (version.data.get('stages') if version and version.data else []) or []


def _visible_plugin_lookup(stages, user):
    plugin_ids = {stage.get('pluginId') for stage in stages if stage.get('pluginId')}
    visible_plugins = Plugin.objects.filter(id__in=plugin_ids)
    if not user.is_staff:
        visible_plugins = visible_plugins.filter(status='approved')
    return {plugin.id: plugin for plugin in visible_plugins}


def _parse_expand_param(raw):
    indices = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            indices.append(int(part))
    return indices


class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='approved')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stages = _recipe_stages(self.object)
        plugin_lookup = _visible_plugin_lookup(stages, self.request.user)
        context['linked_plugin_ids'] = set(plugin_lookup.keys())
        context['diagram'] = generate_recipe_diagram(stages, plugin_lookup, [])
        return context


class RecipeDiagramView(DetailView):
    model = Recipe

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='approved')
        return queryset

    def get(self, request, *args, **kwargs):
        recipe = self.get_object()
        stages = _recipe_stages(recipe)
        plugin_lookup = _visible_plugin_lookup(stages, self.request.user)
        expanded_indices = _parse_expand_param(request.GET.get('expand', ''))
        diagram = generate_recipe_diagram(stages, plugin_lookup, expanded_indices)
        return HttpResponse(diagram, content_type='text/plain')


class RecipeDownloadView(DetailView):
    model = Recipe

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='approved')
        return queryset

    def get(self, request, *args, **kwargs):
        recipe = self.get_object()
        version = recipe.latest_version()
        if not version:
            raise Http404('This recipe has no versions to download.')

        filename = slugify(recipe.label) or 'recipe'
        response = JsonResponse(version.data)
        response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        return response


class UserRecipeListView(LoginRequiredMixin, ListView):
    model = Recipe
    template_name = 'recipes/user_recipe_list.html'

    def get_queryset(self):
        return Recipe.objects.filter(submitted_by=self.request.user)


class RecipeSubmitView(LoginRequiredMixin, FormView):
    template_name = 'recipes/recipe_submit.html'
    form_class = RecipeSubmitForm
    success_url = '/recipes/'

    def form_valid(self, form):
        try:
            data = json.loads(form.cleaned_data['data'])
        except ValueError as exc:
            form.add_error('data', f'Invalid JSON: {exc}')
            return self.form_invalid(form)

        tags = [t.strip() for t in form.cleaned_data.get('tags', '').split(',') if t.strip()]

        submission_viewset = RecipeSubmissionViewSet()
        factory = RequestFactory()
        request = factory.post('/api/recipe-submit/', {})
        request.user = self.request.user
        request.data = {
            'label': form.cleaned_data['label'],
            'description': form.cleaned_data.get('description', ''),
            'author': form.cleaned_data.get('author', ''),
            'category': form.cleaned_data.get('category', ''),
            'tags': tags,
            'data': data,
        }
        response = submission_viewset.create(request)

        if response.status_code >= 400:
            form.add_error(None, str(response.data))
            return self.form_invalid(form)

        return super().form_valid(form)
