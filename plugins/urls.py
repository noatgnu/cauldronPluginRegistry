from django.urls import path
from .views import PluginListView, PluginDetailView, PluginSubmitView, CustomLoginView, logout_view

app_name = 'plugins'

urlpatterns = [
    path('', PluginListView.as_view(), name='plugin-list'),
    path('<str:pk>/', PluginDetailView.as_view(), name='plugin-detail'),
    path('submit/', PluginSubmitView.as_view(), name='plugin-submit'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
