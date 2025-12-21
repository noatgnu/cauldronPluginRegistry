from django.contrib import admin
from .models import (
    Author,
    Category,
    Plugin,
    Tag,
    PluginTag,
    Runtime,
    Input,
    Output,
)

admin.site.register(Author)
admin.site.register(Category)
class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'status', 'author', 'category')
    list_filter = ('status', 'category', 'author')
    list_editable = ('status',)

admin.site.register(Plugin, PluginAdmin)
admin.site.register(Tag)
admin.site.register(PluginTag)
admin.site.register(Runtime)
admin.site.register(Input)
admin.site.register(Output)