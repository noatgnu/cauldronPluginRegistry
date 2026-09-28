from rest_framework import serializers

from plugins.serializers import AuthorSerializer, CategorySerializer, TagSerializer
from .models import Recipe, RecipeVersion


class RecipeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeVersion
        fields = ['revision', 'data', 'changelog', 'created_at']


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True, read_only=True)
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'label', 'description', 'author', 'category', 'tags', 'status', 'created_at', 'updated_at', 'latest_version']

    def get_latest_version(self, obj):
        version = obj.latest_version()
        if version is None:
            return None
        return RecipeVersionSerializer(version).data


class RecipeSubmissionSerializer(serializers.Serializer):
    recipe_id = serializers.UUIDField(required=False, allow_null=True)
    label = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    author = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    changelog = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField()

    def validate_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('data must be a JSON object')
        if 'version' not in value:
            raise serializers.ValidationError('data.version is required')
        stages = value.get('stages')
        if not isinstance(stages, list) or len(stages) == 0:
            raise serializers.ValidationError('data.stages must be a non-empty array')
        for stage in stages:
            if not isinstance(stage, dict) or not stage.get('pluginId'):
                raise serializers.ValidationError('every stage must have a pluginId')
        return value
