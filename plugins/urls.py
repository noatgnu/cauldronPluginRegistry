from django.urls import path
from .views import (
    PluginListView, PluginDetailView, PluginSubmitView, BulkPluginSubmitView,
    UserProfileView, UserPluginListView, SSHKeyListView,
    SSHKeyCreateView, SSHKeyDeleteView
)

urlpatterns = [
    path('', PluginListView.as_view(), name='plugin-list'),
    path('submit/', PluginSubmitView.as_view(), name='plugin-submit'),
    path('bulk-submit/', BulkPluginSubmitView.as_view(), name='plugin-bulk-submit'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('my-plugins/', UserPluginListView.as_view(), name='user-plugin-list'),
    path('ssh-keys/', SSHKeyListView.as_view(), name='ssh-key-list'),
    path('ssh-keys/add/', SSHKeyCreateView.as_view(), name='ssh-key-create'),
    path('ssh-keys/<int:pk>/delete/', SSHKeyDeleteView.as_view(), name='ssh-key-delete'),
    path('<str:pk>/', PluginDetailView.as_view(), name='plugin-detail'),
]