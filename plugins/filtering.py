from .models import Plugin, Runtime, Tag

BOOLEAN_FILTER_FIELDS = ('diagram_enabled', 'citation_enabled', 'requires_authentication')


def visible_plugins(user):
    queryset = Plugin.objects.all()
    if not user.is_staff:
        queryset = queryset.filter(status='approved')
    return queryset


def apply_plugin_filters(queryset, params):
    category_name = params.get('category__name')
    if category_name:
        queryset = queryset.filter(category__name=category_name)

    author_name = params.get('author__name')
    if author_name:
        queryset = queryset.filter(author__name=author_name)

    subcategory = params.get('subcategory')
    if subcategory:
        queryset = queryset.filter(subcategory=subcategory)

    tag_name = params.get('tag')
    if tag_name:
        queryset = queryset.filter(tags__name=tag_name)

    language = params.get('language')
    if language:
        matching_plugin_ids = [
            runtime.plugin_id
            for runtime in Runtime.objects.only('plugin_id', 'environments')
            if language in (runtime.environments or [])
        ]
        queryset = queryset.filter(id__in=matching_plugin_ids)

    for flag in BOOLEAN_FILTER_FIELDS:
        raw_value = params.get(flag)
        if raw_value:
            queryset = queryset.filter(**{flag: raw_value.lower() in ('1', 'true', 'yes')})

    return queryset.distinct()


def plugin_filter_options(queryset):
    categories = list(
        queryset.exclude(category__isnull=True)
        .order_by('category__name')
        .values_list('category__name', flat=True)
        .distinct()
    )
    subcategories = list(
        queryset.exclude(subcategory='')
        .order_by('subcategory')
        .values_list('subcategory', flat=True)
        .distinct()
    )
    authors = list(
        queryset.exclude(author__isnull=True)
        .order_by('author__name')
        .values_list('author__name', flat=True)
        .distinct()
    )
    tags = list(
        Tag.objects.filter(plugins__in=queryset)
        .order_by('name')
        .values_list('name', flat=True)
        .distinct()
    )
    languages = set()
    for environments in Runtime.objects.filter(plugin__in=queryset).values_list('environments', flat=True):
        languages.update(environments or [])

    return {
        'categories': categories,
        'subcategories': subcategories,
        'authors': authors,
        'tags': tags,
        'languages': sorted(languages),
    }
