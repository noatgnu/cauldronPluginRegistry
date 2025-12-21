from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import PluginViewSet, AuthorViewSet, CategoryViewSet, PluginSubmissionViewSet
from .views import PluginListView, PluginDetailView, home_view, CustomLoginView, logout_view, PluginSubmitView

router = DefaultRouter()
router.register(r'plugins', PluginViewSet, basename='plugin')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'submit', PluginSubmissionViewSet, basename='submit')

urlpatterns = [
    path('', home_view, name='api-root'),
    path('browse/', PluginListView.as_view(), name='plugin-list'),
    path('browse/<str:pk>/', PluginDetailView.as_view(), name='plugin-detail'),
    path('submit/', PluginSubmitView.as_view(), name='plugin-submit'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', include(router.urls)),
]
