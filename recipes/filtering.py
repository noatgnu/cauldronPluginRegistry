from .models import Recipe, Tag


def visible_recipes(user):
    queryset = Recipe.objects.all()
    if not user.is_staff:
        queryset = queryset.filter(status='approved')
    return queryset


def apply_recipe_filters(queryset, params):
    category_name = params.get('category__name')
    if category_name:
        queryset = queryset.filter(category__name=category_name)

    author_name = params.get('author__name')
    if author_name:
        queryset = queryset.filter(author__name=author_name)

    tag_name = params.get('tag')
    if tag_name:
        queryset = queryset.filter(tags__name=tag_name)

    return queryset.distinct()


def recipe_filter_options(queryset):
    categories = list(
        queryset.exclude(category__isnull=True)
        .order_by('category__name')
        .values_list('category__name', flat=True)
        .distinct()
    )
    authors = list(
        queryset.exclude(author__isnull=True)
        .order_by('author__name')
        .values_list('author__name', flat=True)
        .distinct()
    )
    tags = list(
        Tag.objects.filter(recipes__in=queryset)
        .order_by('name')
        .values_list('name', flat=True)
        .distinct()
    )

    return {
        'categories': categories,
        'authors': authors,
        'tags': tags,
    }
