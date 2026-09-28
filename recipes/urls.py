from django.urls import path

from .views import (
    RecipeDetailView, RecipeDiagramView, RecipeDownloadView, RecipeListView, RecipeSubmitView,
    UserRecipeListView,
)

urlpatterns = [
    path('', RecipeListView.as_view(), name='recipe-list'),
    path('submit/', RecipeSubmitView.as_view(), name='recipe-submit'),
    path('my-recipes/', UserRecipeListView.as_view(), name='user-recipe-list'),
    path('<uuid:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('<uuid:pk>/download/', RecipeDownloadView.as_view(), name='recipe-download'),
    path('<uuid:pk>/diagram/', RecipeDiagramView.as_view(), name='recipe-diagram'),
]
