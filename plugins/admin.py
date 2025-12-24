from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Author,
    Category,
    Plugin,
    UserProfile
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'status', 'author', 'category')
    list_filter = ('status', 'category', 'author')
    list_editable = ('status',)

admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Plugin, PluginAdmin)
