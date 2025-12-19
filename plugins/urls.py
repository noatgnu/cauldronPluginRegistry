from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PluginViewSet, AuthorViewSet, CategoryViewSet, PluginSubmissionViewSet

router = DefaultRouter()
router.register(r'plugins', PluginViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'submit', PluginSubmissionViewSet, basename='submit')

urlpatterns = [
    path('', include(router.urls)),
]
