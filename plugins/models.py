from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Plugin(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    version = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    icon = models.CharField(max_length=255, blank=True, null=True)
    repository = models.URLField(blank=True, null=True)
    readme = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class PluginTag(models.Model):
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('plugin', 'tag')

class Runtime(models.Model):
    plugin = models.OneToOneField(Plugin, on_delete=models.CASCADE, related_name='runtime')
    type = models.CharField(max_length=50)
    script = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.plugin.name} - {self.type}"

class Input(models.Model):
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='inputs')
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    required = models.BooleanField(default=False)
    default = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    accept = models.CharField(max_length=255, blank=True, null=True)
    multiple = models.BooleanField(default=False)
    sourceFile = models.CharField(max_length=255, blank=True, null=True)
    min = models.FloatField(blank=True, null=True)
    max = models.FloatField(blank=True, null=True)
    step = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.name

class Output(models.Model):
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='outputs')
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name