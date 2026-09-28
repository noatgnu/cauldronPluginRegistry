import uuid

from django.contrib.auth.models import User
from django.db import models

from plugins.models import Author, Category, Tag


class Recipe(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, through='RecipeTag', related_name='recipes', blank=True)

    def __str__(self):
        return self.label

    def latest_version(self):
        return self.versions.order_by('-revision').first()


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('recipe', 'tag')


class RecipeVersion(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='versions')
    revision = models.PositiveIntegerField()
    data = models.JSONField()
    changelog = models.TextField(blank=True, null=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('recipe', 'revision')
        ordering = ['-revision']

    def __str__(self):
        return f"{self.recipe.label} rev {self.revision}"
