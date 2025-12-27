from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Plugin, UserProfile, RepositorySSHKey
from .forms import PluginSubmitForm, SSHKeyForm
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
        request.data = request.POST
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

class SSHKeyListView(LoginRequiredMixin, ListView):
    model = RepositorySSHKey
    template_name = 'plugins/ssh_key_list.html'
    context_object_name = 'ssh_keys'

    def get_queryset(self):
        return RepositorySSHKey.objects.filter(user=self.request.user)

class SSHKeyCreateView(LoginRequiredMixin, CreateView):
    model = RepositorySSHKey
    form_class = SSHKeyForm
    template_name = 'plugins/ssh_key_form.html'
    success_url = reverse_lazy('ssh-key-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'SSH key added successfully!')
        return super().form_valid(form)

class SSHKeyDeleteView(LoginRequiredMixin, DeleteView):
    model = RepositorySSHKey
    template_name = 'plugins/ssh_key_confirm_delete.html'
    success_url = reverse_lazy('ssh-key-list')

    def get_queryset(self):
        return RepositorySSHKey.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'SSH key deleted successfully!')
        return super().delete(request, *args, **kwargs)