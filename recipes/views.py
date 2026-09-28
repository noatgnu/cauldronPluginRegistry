import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.test import RequestFactory
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from .diagram import generate_recipe_overview_diagram
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
        version = self.object.latest_version()
        stages = version.data.get('stages') if version and version.data else None
        context['diagram'] = generate_recipe_overview_diagram(stages or [])
        return context


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
