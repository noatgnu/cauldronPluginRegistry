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
admin.site.register(Plugin)
admin.site.register(Tag)
admin.site.register(PluginTag)
admin.site.register(Runtime)
admin.site.register(Input)
admin.site.register(Output)