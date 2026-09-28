from django.urls import path

from .views import RecipeListView, RecipeDetailView, RecipeSubmitView

urlpatterns = [
    path('', RecipeListView.as_view(), name='recipe-list'),
    path('submit/', RecipeSubmitView.as_view(), name='recipe-submit'),
    path('<uuid:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
]
