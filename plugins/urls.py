from django.urls import path
from .views import PluginListView, PluginDetailView, PluginSubmitView, UserProfileView, UserPluginListView

app_name = 'plugins'

urlpatterns = [
    path('', PluginListView.as_view(), name='plugin-list'),
    path('<str:pk>/', PluginDetailView.as_view(), name='plugin-detail'),
    path('submit/', PluginSubmitView.as_view(), name='plugin-submit'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('my-plugins/', UserPluginListView.as_view(), name='user-plugin-list'),
]