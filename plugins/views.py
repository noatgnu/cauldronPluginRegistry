from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from .models import Plugin, UserProfile
from .forms import PluginSubmitForm
from .viewsets import PluginSubmissionViewSet

def home_view(request):
    return render(request, 'home.html')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

def logout_view(request):
    logout(request)
    return redirect('home')

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'plugins/user_profile.html'
    fields = ['orcid']
    success_url = '/profile/'

    def get_object(self):
        return self.request.user.userprofile

class UserPluginListView(LoginRequiredMixin, ListView):
    model = Plugin
    template_name = 'plugins/user_plugin_list.html'

    def get_queryset(self):
        return Plugin.objects.filter(submitted_by=self.request.user)

class PluginSubmitView(LoginRequiredMixin, FormView):
    template_name = 'plugins/plugin_submit.html'
    form_class = PluginSubmitForm
    success_url = '/plugins/'

    def form_valid(self, form):
        submission_viewset = PluginSubmissionViewSet()
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/api/submit/', {'repo_url': form.cleaned_data['repo_url']})
        request.user = self.request.user
        response = submission_viewset.create(request)

        if response.status_code >= 400:
            form.add_error('repo_url', response.data.get('error', 'An unknown error occurred.'))
            return self.form_invalid(form)

        return super().form_valid(form)


class PluginListView(ListView):
    model = Plugin
    template_name = 'plugins/plugin_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='approved')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

class PluginDetailView(DetailView):
    model = Plugin
    template_name = 'plugins/plugin_detail.html'
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='approved')
        return queryset