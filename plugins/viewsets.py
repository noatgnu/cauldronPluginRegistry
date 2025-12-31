import tempfile
import git
import yaml
import os
import stat

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Plugin, Author, Category, Runtime, Input, Output, PluginEnvVariable, RepositorySSHKey
from .serializers import PluginSerializer, AuthorSerializer, CategorySerializer, PluginSubmissionSerializer
from .permissions import IsOwnerOrAdmin

from django.conf import settings
import markdown
import re

def normalize_repo_url(repo_url):
    if repo_url.startswith('git@'):
        repo_url = repo_url.replace(':', '/', 1).replace('git@', 'ssh://git@')
    return repo_url

def check_repo_requires_auth(repo_url):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            git.Repo.clone_from(repo_url, temp_dir, depth=1)
            return False
    except git.exc.GitCommandError as e:
        error_message = str(e).lower()
        if any(keyword in error_message for keyword in ['authentication', 'permission denied', 'could not read', 'fatal: could not read from remote repository']):
            return True
        raise
    except Exception:
        raise

def setup_git_ssh_auth(repo_url, user):
    normalized_url = normalize_repo_url(repo_url)

    try:
        ssh_key = RepositorySSHKey.objects.filter(
            user=user,
            repository_url__in=[repo_url, normalized_url]
        ).first()

        if not ssh_key:
            alt_url = repo_url.replace('ssh://git@', 'git@').replace('/', ':', 1) if 'ssh://' in repo_url else repo_url
            ssh_key = RepositorySSHKey.objects.filter(
                user=user,
                repository_url=alt_url
            ).first()

        if ssh_key:
            ssh_key_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key')
            ssh_key_file.write(ssh_key.ssh_private_key)
            ssh_key_file.close()

            os.chmod(ssh_key_file.name, stat.S_IRUSR | stat.S_IWUSR)

            ssh_command = f'ssh -i {ssh_key_file.name} -o StrictHostKeyChecking=no'
            if ssh_key.passphrase:
                ssh_command = f'sshpass -p "{ssh_key.passphrase}" {ssh_command}'

            return ssh_command, ssh_key_file.name
    except Exception:
        pass

    return None, None

def cleanup_ssh_key_file(ssh_key_file_path):
    if ssh_key_file_path and os.path.exists(ssh_key_file_path):
        try:
            os.unlink(ssh_key_file_path)
        except Exception:
            pass

def get_primary_environment(runtime_info):
    environments = runtime_info.get('environments', [])
    if environments and len(environments) > 0:
        return environments[0]
    return ''

def generate_mermaid_diagram(script_path, runtime_info):
    if not os.path.exists(script_path):
        return ""

    try:
        with open(script_path, 'r') as f:
            content = f.read()
    except Exception:
        return ""

    lines = content.split('\n')
    steps = []

    primary_env = get_primary_environment(runtime_info)

    if primary_env == 'r':
        pattern = re.compile(r'message\(.*\[(\d+)/(\d+)\]\s*(.+?)["\')]')
    elif primary_env == 'python':
        pattern = re.compile(r'(?:print|logger\.info)\(.*\[(\d+)/(\d+)\]\s*(.+?)["\')]')
    else:
        return ""
        
    for line in lines:
        match = pattern.search(line.strip())
        if match:
            label = match.group(3).strip()
            if label and not label.startswith('='):
                steps.append(label)
                
    if not steps:
        return ""
        
    mermaid = ["```mermaid", "flowchart TD", "    Start([Start]) --> step1"]
    for i, label in enumerate(steps):
        step_id = f"step{i+1}"
        mermaid.append(f"    {step_id}[{label}]")
        if i < len(steps) - 1:
            mermaid.append(f"    {step_id} --> step{i+2}")
            
    mermaid.append(f"    step{len(steps)} --> End([End])")
    mermaid.append("```")
    
    return "\n## Workflow Diagram\n\n" + "\n".join(mermaid) + "\n"

def sync_plugin_components(plugin, plugin_data):
    # Runtime
    runtime_info = plugin_data.get('runtime', {})
    Runtime.objects.filter(plugin=plugin).delete()
    if runtime_info:
        Runtime.objects.create(
            plugin=plugin,
            environments=runtime_info.get('environments', []),
            entrypoint=runtime_info.get('entrypoint', '')
        )

    # Inputs
    Input.objects.filter(plugin=plugin).delete()
    inputs_data = plugin_data.get('inputs', [])
    for inp in inputs_data:
        Input.objects.create(
            plugin=plugin,
            name=inp.get('name', ''),
            label=inp.get('label', ''),
            type=inp.get('type', ''),
            required=inp.get('required', False),
            default=str(inp.get('default', '')) if inp.get('default') is not None else None,
            description=inp.get('description', ''),
            placeholder=inp.get('placeholder', ''),
            file_types=inp.get('file_types', []),
            multiple=inp.get('multiple', False),
            sourceFile=inp.get('sourceFile', ''),
            min=inp.get('min'),
            max=inp.get('max'),
            step=inp.get('step')
        )

    # Outputs
    Output.objects.filter(plugin=plugin).delete()
    outputs_data = plugin_data.get('outputs', [])
    for out in outputs_data:
        Output.objects.create(
            plugin=plugin,
            name=out.get('name', ''),
            path=out.get('path', ''),
            type=out.get('type', ''),
            description=out.get('description', ''),
            format=out.get('format', '')
        )

    # Env Variables
    PluginEnvVariable.objects.filter(plugin=plugin).delete()
    execution_info = plugin_data.get('execution', {})
    env_vars_data = execution_info.get('envVariables', [])
    for ev in env_vars_data:
        PluginEnvVariable.objects.create(
            plugin=plugin,
            name=ev.get('name', ''),
            label=ev.get('label', ''),
            type=ev.get('type', ''),
            required=ev.get('required', False),
            default=str(ev.get('default', '')) if ev.get('default') is not None else None,
            description=ev.get('description', ''),
            placeholder=ev.get('placeholder', ''),
            accept=ev.get('accept', ''),
            multiple=ev.get('multiple', False),
            sourceFile=ev.get('sourceFile', ''),
            min=ev.get('min'),
            max=ev.get('max'),
            step=ev.get('step')
        )

class PluginSubmissionViewSet(viewsets.ViewSet):
    serializer_class = PluginSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            repo_url = serializer.validated_data['repo_url']
            ssh_key_file_path = None
            requires_auth = False

            try:
                requires_auth = check_repo_requires_auth(repo_url)
            except Exception as e:
                pass

            try:
                ssh_command, ssh_key_file_path = setup_git_ssh_auth(repo_url, request.user)
                env = os.environ.copy()
                if ssh_command:
                    env['GIT_SSH_COMMAND'] = ssh_command

                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = git.Repo.clone_from(repo_url, temp_dir, env=env)
                    commit_hash = repo.head.commit.hexsha
                    
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
                    
                    initial_status = 'approved' if settings.AUTO_APPROVE_PLUGINS else 'pending'

                    # Handle Diagram Configuration
                    diagram_config = plugin_data.get('diagram', {})
                    diagram_enabled = diagram_config.get('enabled', False)
                    
                    readme_path = os.path.join(temp_dir, 'README.md')
                    raw_readme = ""
                    if os.path.exists(readme_path):
                        with open(readme_path, 'r') as f:
                            raw_readme = f.read()
                    
                    # Autogenerate diagram if enabled and not already in README
                    if diagram_enabled and "```mermaid" not in raw_readme:
                        runtime_info = plugin_data.get('runtime', {})
                        entrypoint = runtime_info.get('entrypoint')
                        if entrypoint and runtime_info:
                            script_path = os.path.join(temp_dir, entrypoint)
                            diagram_md = generate_mermaid_diagram(script_path, runtime_info)
                            raw_readme += diagram_md

                    readme_content = markdown.markdown(raw_readme, extensions=['fenced_code', 'tables'])

                    # Post-process mermaid blocks for frontend rendering
                    mermaid_pattern = re.compile(r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>')
                    readme_content = mermaid_pattern.sub(r'<pre class="mermaid">\1</pre>', readme_content)

                    # Check if plugin already exists
                    existing_plugin = Plugin.objects.filter(id=plugin_id).first()

                    plugin, created = Plugin.objects.update_or_create(
                        id=plugin_id,
                        defaults={
                            'name': plugin_info.get('name'),
                            'description': plugin_info.get('description'),
                            'version': plugin_info.get('version'),
                            'author': author,
                            'category': category,
                            'subcategory': plugin_info.get('subcategory'),
                            'icon': plugin_info.get('icon'),
                            'repository': repo_url,
                            'commit_hash': commit_hash,
                            'status': initial_status,
                            'readme': readme_content,
                            'diagram_enabled': diagram_enabled,
                            'requires_authentication': requires_auth,
                            'submitted_by': request.user if not existing_plugin else existing_plugin.submitted_by,
                        }
                    )
                    
                    sync_plugin_components(plugin, plugin_data)
                    
                    return Response(PluginSerializer(plugin).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

            except git.exc.GitCommandError as e:
                return Response({'error': f'Failed to clone repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                cleanup_ssh_key_file(ssh_key_file_path)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PluginViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PluginSerializer
    filterset_fields = ['name', 'category', 'author']
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Plugin.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='approved')
        return queryset

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def check_update(self, request, pk=None):
        plugin = self.get_object()
        if not plugin.repository:
            return Response({'error': 'Plugin has no repository URL.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                repo = git.Repo.clone_from(plugin.repository, temp_dir, depth=1)
                latest_commit = repo.head.commit.hexsha

                tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
                latest_tag = tags[0].name if tags else None

                recommended = plugin.recommended_commit if plugin.recommended_commit else latest_commit

                has_update = recommended != plugin.commit_hash

                return Response({
                    'plugin_id': plugin.id,
                    'current_commit': plugin.commit_hash,
                    'latest_commit': latest_commit,
                    'recommended_commit': recommended,
                    'latest_stable_tag': latest_tag,
                    'has_update': has_update,
                    'changelog_url': f"{plugin.repository}/compare/{plugin.commit_hash}...{recommended}" if has_update else None
                }, status=status.HTTP_200_OK)

        except git.exc.GitCommandError as e:
            return Response({'error': f'Failed to check repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def set_recommended_commit(self, request, pk=None):
        plugin = self.get_object()

        if not request.user.is_staff and plugin.submitted_by != request.user:
            return Response({'error': 'You do not have permission to modify this plugin'}, status=status.HTTP_403_FORBIDDEN)

        commit_hash = request.data.get('commit_hash')

        if not commit_hash:
            return Response({'error': 'commit_hash is required'}, status=status.HTTP_400_BAD_REQUEST)

        plugin.recommended_commit = commit_hash
        plugin.save()

        return Response({
            'plugin_id': plugin.id,
            'recommended_commit': plugin.recommended_commit
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def refresh(self, request, pk=None):
        plugin = self.get_object()

        if not request.user.is_staff and plugin.submitted_by != request.user:
            return Response({'error': 'You do not have permission to modify this plugin'}, status=status.HTTP_403_FORBIDDEN)

        if not plugin.repository:
            return Response({'error': 'Plugin has no repository URL.'}, status=status.HTTP_400_BAD_REQUEST)

        ssh_key_file_path = None
        try:
            ssh_command, ssh_key_file_path = setup_git_ssh_auth(plugin.repository, request.user)
            env = os.environ.copy()
            if ssh_command:
                env['GIT_SSH_COMMAND'] = ssh_command

            with tempfile.TemporaryDirectory() as temp_dir:
                repo = git.Repo.clone_from(plugin.repository, temp_dir, env=env)
                commit_hash = repo.head.commit.hexsha
                
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
                
                # Handle Diagram Configuration
                diagram_config = plugin_data.get('diagram', {})
                diagram_enabled = diagram_config.get('enabled', False)

                readme_path = os.path.join(temp_dir, 'README.md')
                raw_readme = ""
                if os.path.exists(readme_path):
                    with open(readme_path, 'r') as f:
                        raw_readme = f.read()

                # Autogenerate diagram if enabled and not already in README
                if diagram_enabled and "```mermaid" not in raw_readme:
                    runtime_info = plugin_data.get('runtime', {})
                    entrypoint = runtime_info.get('entrypoint')
                    if entrypoint and runtime_info:
                        script_path = os.path.join(temp_dir, entrypoint)
                        diagram_md = generate_mermaid_diagram(script_path, runtime_info)
                        raw_readme += diagram_md

                readme_content = markdown.markdown(raw_readme, extensions=['fenced_code', 'tables'])
                
                # Post-process mermaid blocks for frontend rendering
                mermaid_pattern = re.compile(r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>')
                readme_content = mermaid_pattern.sub(r'<pre class="mermaid">\1</pre>', readme_content)
                
                plugin.name = plugin_info.get('name')
                plugin.description = plugin_info.get('description')
                plugin.version = plugin_info.get('version')
                plugin.author = author
                plugin.category = category
                plugin.icon = plugin_info.get('icon')
                plugin.commit_hash = commit_hash
                plugin.readme = readme_content
                plugin.diagram_enabled = diagram_enabled
                plugin.save()
                
                sync_plugin_components(plugin, plugin_data)
                
                return Response(PluginSerializer(plugin).data, status=status.HTTP_200_OK)

        except git.exc.GitCommandError as e:
            return Response({'error': f'Failed to clone repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cleanup_ssh_key_file(ssh_key_file_path)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_plugins(self, request):
        plugins = Plugin.objects.filter(submitted_by=request.user)
        serializer = self.get_serializer(plugins, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def check_my_update(self, request, pk=None):
        plugin = self.get_object()

        if not request.user.is_staff and plugin.submitted_by != request.user:
            return Response({'error': 'You do not have permission to check updates for this plugin'}, status=status.HTTP_403_FORBIDDEN)

        if not plugin.repository:
            return Response({'error': 'Plugin has no repository URL.'}, status=status.HTTP_400_BAD_REQUEST)

        ssh_key_file_path = None
        try:
            ssh_command, ssh_key_file_path = setup_git_ssh_auth(plugin.repository, request.user)
            env = os.environ.copy()
            if ssh_command:
                env['GIT_SSH_COMMAND'] = ssh_command

            with tempfile.TemporaryDirectory() as temp_dir:
                repo = git.Repo.clone_from(plugin.repository, temp_dir, depth=1, env=env)
                latest_commit = repo.head.commit.hexsha

                tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
                latest_tag = tags[0].name if tags else None

                has_update = latest_commit != plugin.commit_hash

                return Response({
                    'plugin_id': plugin.id,
                    'current_commit': plugin.commit_hash,
                    'latest_commit': latest_commit,
                    'latest_stable_tag': latest_tag,
                    'has_update': has_update,
                    'recommended_commit': plugin.recommended_commit,
                }, status=status.HTTP_200_OK)

        except git.exc.GitCommandError as e:
            return Response({'error': f'Failed to check repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cleanup_ssh_key_file(ssh_key_file_path)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def sync_to_latest(self, request, pk=None):
        plugin = self.get_object()

        if not request.user.is_staff and plugin.submitted_by != request.user:
            return Response({'error': 'You do not have permission to sync this plugin'}, status=status.HTTP_403_FORBIDDEN)

        if not plugin.repository:
            return Response({'error': 'Plugin has no repository URL.'}, status=status.HTTP_400_BAD_REQUEST)

        ssh_key_file_path = None
        try:
            ssh_command, ssh_key_file_path = setup_git_ssh_auth(plugin.repository, request.user)
            env = os.environ.copy()
            if ssh_command:
                env['GIT_SSH_COMMAND'] = ssh_command

            with tempfile.TemporaryDirectory() as temp_dir:
                repo = git.Repo.clone_from(plugin.repository, temp_dir, env=env)
                latest_commit = repo.head.commit.hexsha

                tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
                latest_tag = tags[0].name if tags else None

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

                diagram_config = plugin_data.get('diagram', {})
                diagram_enabled = diagram_config.get('enabled', False)

                readme_path = os.path.join(temp_dir, 'README.md')
                raw_readme = ""
                if os.path.exists(readme_path):
                    with open(readme_path, 'r') as f:
                        raw_readme = f.read()

                if diagram_enabled and "```mermaid" not in raw_readme:
                    runtime_info = plugin_data.get('runtime', {})
                    entrypoint = runtime_info.get('entrypoint')
                    if entrypoint and runtime_info:
                        script_path = os.path.join(temp_dir, entrypoint)
                        diagram_md = generate_mermaid_diagram(script_path, runtime_info)
                        raw_readme += diagram_md

                readme_content = markdown.markdown(raw_readme, extensions=['fenced_code', 'tables'])

                mermaid_pattern = re.compile(r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>')
                readme_content = mermaid_pattern.sub(r'<pre class="mermaid">\1</pre>', readme_content)

                plugin.name = plugin_info.get('name')
                plugin.description = plugin_info.get('description')
                plugin.version = plugin_info.get('version')
                plugin.author = author
                plugin.category = category
                plugin.icon = plugin_info.get('icon')
                plugin.commit_hash = latest_commit
                plugin.latest_stable_tag = latest_tag
                plugin.readme = readme_content
                plugin.diagram_enabled = diagram_enabled
                plugin.save()

                sync_plugin_components(plugin, plugin_data)

                return Response(PluginSerializer(plugin).data, status=status.HTTP_200_OK)

        except git.exc.GitCommandError as e:
            return Response({'error': f'Failed to sync repository: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            cleanup_ssh_key_file(ssh_key_file_path)


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