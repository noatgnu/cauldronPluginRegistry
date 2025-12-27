from rest_framework import serializers
from .models import Plugin, Author, Category, Tag, Runtime, Input, Output, PluginEnvVariable

class PluginSubmissionSerializer(serializers.Serializer):
    repo_url = serializers.URLField()

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class RuntimeSerializer(serializers.ModelSerializer):
    normalized_environments = serializers.SerializerMethodField()

    class Meta:
        model = Runtime
        fields = '__all__'

    def get_normalized_environments(self, obj):
        return obj.get_environments()

class InputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Input
        fields = '__all__'

class OutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Output
        fields = '__all__'

class PluginEnvVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginEnvVariable
        fields = '__all__'

class PluginUpdateInfoSerializer(serializers.Serializer):
    plugin_id = serializers.CharField()
    current_commit = serializers.CharField()
    latest_commit = serializers.CharField()
    recommended_commit = serializers.CharField()
    latest_stable_tag = serializers.CharField(allow_null=True)
    has_update = serializers.BooleanField()
    changelog_url = serializers.URLField(allow_null=True)

class PluginSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True, read_only=True)
    runtime = RuntimeSerializer()
    inputs = InputSerializer(many=True)
    outputs = OutputSerializer(many=True)
    env_variables = PluginEnvVariableSerializer(many=True)

    class Meta:
        model = Plugin
        fields = '__all__'
