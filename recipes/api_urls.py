from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .viewsets import RecipeViewSet, RecipeSubmissionViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'recipe-submit', RecipeSubmissionViewSet, basename='recipe-submit')

urlpatterns = [
    path('', include(router.urls)),
]
