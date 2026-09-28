from django.contrib import admin, messages

from .models import Recipe, RecipeVersion


@admin.action(description="Approve selected recipes")
def approve_recipes(modeladmin, request, queryset):
    updated = queryset.update(status='approved')
    messages.success(request, f"{updated} recipes approved")


@admin.action(description="Reject selected recipes")
def reject_recipes(modeladmin, request, queryset):
    updated = queryset.update(status='rejected')
    messages.success(request, f"{updated} recipes rejected")


@admin.action(description="Set to pending")
def set_pending(modeladmin, request, queryset):
    updated = queryset.update(status='pending')
    messages.success(request, f"{updated} recipes set to pending")


class RecipeVersionInline(admin.TabularInline):
    model = RecipeVersion
    extra = 0
    readonly_fields = ('revision', 'created_at', 'submitted_by')
    fields = ('revision', 'changelog', 'submitted_by', 'created_at')
    ordering = ('-revision',)
    can_delete = False


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('label', 'id', 'status', 'author', 'category', 'submitted_by', 'updated_at')
    list_filter = ('status', 'category', 'author')
    list_editable = ('status',)
    search_fields = ('id', 'label', 'description', 'author__name')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = [approve_recipes, reject_recipes, set_pending]
    inlines = [RecipeVersionInline]
