import tempfile
import git
import yaml
import os

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Plugin, Author, Category
from .serializers import PluginSerializer, AuthorSerializer, CategorySerializer, PluginSubmissionSerializer

class PluginSubmissionViewSet(viewsets.ViewSet):
    serializer_class = PluginSubmissionSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            repo_url = serializer.validated_data['repo_url']
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    git.Repo.clone_from(repo_url, temp_dir)
                    
                    plugin_yaml_path = os.path.join(temp_dir, 'plugin.yaml')
                    if not os.path.exists(plugin_yaml_path):
                        return Response({'error': 'plugin.yaml not found in the repository.'}, status=status.HTTP_400_BAD_REQUEST)

                    with open(plugin_yaml_path, 'r') as f:
                        plugin_data = yaml.safe_load(f)

                    plugin_info = plugin_data.get('plugin', {})
                    plugin_id = plugin_info.get('id')
                    if not plugin_id:
                        return Response({'error': 'Plugin ID not found in plugin.yaml.'}, status=status.HTTP_400_BAD_REQUEST)

                    author_name = plugin_info.get('author')
                    author = None
                    if author_name:
                        author, _ = Author.objects.get_or_create(name=author_name)

                    category_name = plugin_info.get('category')
                    category = None
                    if category_name:
                        category, _ = Category.objects.get_or_create(name=category_name)
                    
                    plugin, created = Plugin.objects.update_or_create(
                        id=plugin_id,
                        defaults={
                            'name': plugin_info.get('name'),
                            'description': plugin_info.get('description'),
                            'version': plugin_info.get('version'),
                            'author': author,
                            'category': category,
                            'icon': plugin_info.get('icon'),
                            'repository': repo_url,
                        }
                    )

                    return Response(PluginSerializer(plugin).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

            except git.exc.GitCommandError as e:
                return Response({'error': f'Failed to clone repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PluginViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plugin.objects.all()
    serializer_class = PluginSerializer
    filterset_fields = ['name', 'category', 'author']
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def refresh(self, request, pk=None):
        plugin = self.get_object()
        if not plugin.repository:
            return Response({'error': 'Plugin has no repository URL.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                git.Repo.clone_from(plugin.repository, temp_dir)
                
                plugin_yaml_path = os.path.join(temp_dir, 'plugin.yaml')
                if not os.path.exists(plugin_yaml_path):
                    return Response({'error': 'plugin.yaml not found in the repository.'}, status=status.HTTP_400_BAD_REQUEST)

                with open(plugin_yaml_path, 'r') as f:
                    plugin_data = yaml.safe_load(f)

                plugin_info = plugin_data.get('plugin', {})
                
                author_name = plugin_info.get('author')
                author = None
                if author_name:
                    author, _ = Author.objects.get_or_create(name=author_name)

                category_name = plugin_info.get('category')
                category = None
                if category_name:
                    category, _ = Category.objects.get_or_create(name=category_name)
                
                plugin.name = plugin_info.get('name')
                plugin.description = plugin_info.get('description')
                plugin.version = plugin_info.get('version')
                plugin.author = author
                plugin.category = category
                plugin.icon = plugin_info.get('icon')
                plugin.save()

                return Response(PluginSerializer(plugin).data, status=status.HTTP_200_OK)

        except git.exc.GitCommandError as e:
            return Response({'error': f'Failed to clone repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filterset_fields = ['name']
    permission_classes = [AllowAny]

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = ['name']
    permission_classes = [AllowAny]
