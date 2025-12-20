from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PluginViewSet, AuthorViewSet, CategoryViewSet, PluginSubmissionViewSet, api_root

router = DefaultRouter()
router.register(r'plugins', PluginViewSet, basename='plugin')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'submit', PluginSubmissionViewSet, basename='submit')

urlpatterns = [
    path('', include(router.urls)),
]
