from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from plugins.models import Author, Category

from .filtering import apply_recipe_filters, recipe_filter_options, visible_recipes
from .models import Recipe, RecipeVersion
from .serializers import RecipeSerializer, RecipeSubmissionSerializer


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecipeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['label', 'description', 'author__name', 'category__name']
    ordering_fields = ['label', 'updated_at', 'created_at']
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = visible_recipes(self.request.user)
        return apply_recipe_filters(queryset, self.request.query_params)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def filter_options(self, request):
        return Response(recipe_filter_options(visible_recipes(request.user)))

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_recipes(self, request):
        queryset = Recipe.objects.filter(submitted_by=request.user)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class RecipeSubmissionViewSet(viewsets.ViewSet):
    serializer_class = RecipeSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = serializer.validated_data
        recipe_id = validated.get('recipe_id')

        existing_recipe = None
        if recipe_id:
            existing_recipe = Recipe.objects.filter(id=recipe_id).first()
            if existing_recipe is not None and existing_recipe.submitted_by_id not in (None, request.user.id):
                return Response(
                    {'error': 'you do not own this recipe'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        author = None
        author_name = validated.get('author') or request.user.get_full_name() or request.user.username
        if author_name:
            author, _ = Author.objects.get_or_create(name=author_name)

        category = None
        category_name = validated.get('category')
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)

        defaults = {
            'label': validated['label'],
            'description': validated.get('description', ''),
            'category': category,
            'status': 'approved' if getattr(settings, 'AUTO_APPROVE_RECIPES', False) else 'pending',
            'submitted_by': request.user if existing_recipe is None else existing_recipe.submitted_by,
        }
        if author is not None:
            defaults['author'] = author

        if existing_recipe is not None:
            for key, value in defaults.items():
                setattr(existing_recipe, key, value)
            existing_recipe.save()
            recipe = existing_recipe
            created = False
        else:
            recipe = Recipe.objects.create(id=recipe_id, **defaults) if recipe_id else Recipe.objects.create(**defaults)
            created = True

        last_revision = recipe.versions.order_by('-revision').first()
        next_revision = (last_revision.revision + 1) if last_revision else 1
        RecipeVersion.objects.create(
            recipe=recipe,
            revision=next_revision,
            data=validated['data'],
            changelog=validated.get('changelog', ''),
            submitted_by=request.user,
        )

        return Response(
            RecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
