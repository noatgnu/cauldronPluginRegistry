from django.urls import path
from .views import PluginListView, PluginDetailView, PluginSubmitView

urlpatterns = [
    path('', PluginListView.as_view(), name='plugin-list'),
    path('<str:pk>/', PluginDetailView.as_view(), name='plugin-detail'),
    path('submit/', PluginSubmitView.as_view(), name='plugin-submit'),
]