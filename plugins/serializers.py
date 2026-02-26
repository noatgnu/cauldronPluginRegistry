from rest_framework import serializers
from .models import Plugin, Author, Category, Tag, Runtime, Input, Output, PluginEnvVariable, Execution, Plot, Annotation, Example

class PluginSubmissionSerializer(serializers.Serializer):
    repo_url = serializers.URLField()


class BulkPluginSubmissionSerializer(serializers.Serializer):
    """Serializer for bulk plugin submission (staff only)."""
    repo_urls = serializers.ListField(
        child=serializers.URLField(),
        min_length=1,
        max_length=10
    )

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
    class Meta:
        model = Runtime
        fields = '__all__'

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


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = '__all__'


class PlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plot
        fields = '__all__'


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = '__all__'


class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Example
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
    execution = ExecutionSerializer(read_only=True)
    plots = PlotSerializer(many=True, read_only=True)
    annotation = AnnotationSerializer(read_only=True)
    example = ExampleSerializer(read_only=True)

    class Meta:
        model = Plugin
        fields = '__all__'
