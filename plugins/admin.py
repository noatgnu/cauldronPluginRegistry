import tempfile
import os

import git
import yaml
import markdown
import re

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Author,
    Category,
    Plugin,
    UserProfile,
    Runtime,
    Input,
    Output,
    PluginEnvVariable
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


def sync_plugin_components(plugin, plugin_data):
    """Sync plugin components (runtime, inputs, outputs, env vars) from plugin data."""
    runtime_info = plugin_data.get('runtime', {})
    Runtime.objects.filter(plugin=plugin).delete()
    if runtime_info:
        Runtime.objects.create(
            plugin=plugin,
            environments=runtime_info.get('environments', []),
            entrypoint=runtime_info.get('entrypoint', '')
        )

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


def get_primary_environment(runtime_info):
    """Get the primary environment from runtime info."""
    environments = runtime_info.get('environments', [])
    if environments and len(environments) > 0:
        return environments[0]
    return ''


def generate_mermaid_diagram(script_path, runtime_info):
    """Generate mermaid diagram from script."""
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


@admin.action(description="Check for updates")
def check_updates(modeladmin, request, queryset):
    """Check for updates on selected plugins."""
    has_updates = 0
    up_to_date = 0
    failed = 0

    for plugin in queryset:
        if not plugin.repository:
            messages.warning(request, f"{plugin.name}: No repository URL")
            failed += 1
            continue

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                repo = git.Repo.clone_from(plugin.repository, temp_dir, depth=1)
                latest_commit = repo.head.commit.hexsha

                recommended = plugin.recommended_commit if plugin.recommended_commit else latest_commit
                has_update = recommended != plugin.commit_hash

                if has_update:
                    has_updates += 1
                    current = plugin.commit_hash[:7] if plugin.commit_hash else "none"
                    latest = recommended[:7]
                    messages.info(request, f"{plugin.name}: Update available ({current} → {latest})")
                else:
                    up_to_date += 1

        except git.exc.GitCommandError as e:
            messages.error(request, f"{plugin.name}: Git error - {str(e)[:100]}")
            failed += 1
        except Exception as e:
            messages.error(request, f"{plugin.name}: Error - {str(e)[:100]}")
            failed += 1

    messages.success(
        request,
        f"Check complete: {has_updates} with updates, {up_to_date} up to date, {failed} failed"
    )


@admin.action(description="Sync to latest commit")
def sync_to_latest(modeladmin, request, queryset):
    """Sync selected plugins to their latest commits."""
    synced = 0
    failed = 0

    for plugin in queryset:
        if not plugin.repository:
            messages.warning(request, f"{plugin.name}: No repository URL")
            failed += 1
            continue

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                repo = git.Repo.clone_from(plugin.repository, temp_dir)
                latest_commit = repo.head.commit.hexsha

                tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
                latest_tag = tags[0].name if tags else None

                plugin_yaml_path = os.path.join(temp_dir, 'plugin.yaml')
                if not os.path.exists(plugin_yaml_path):
                    messages.error(request, f"{plugin.name}: plugin.yaml not found")
                    failed += 1
                    continue

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

                citation_config = plugin_data.get('citation', {})
                citation_enabled = citation_config.get('enabled', False)

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

                old_commit = plugin.commit_hash[:7] if plugin.commit_hash else "none"
                plugin.name = plugin_info.get('name', plugin.name)
                plugin.description = plugin_info.get('description', plugin.description)
                plugin.version = plugin_info.get('version', plugin.version)
                plugin.author = author
                plugin.category = category
                plugin.icon = plugin_info.get('icon')
                plugin.commit_hash = latest_commit
                plugin.latest_stable_tag = latest_tag
                plugin.readme = readme_content
                plugin.diagram_enabled = diagram_enabled
                plugin.citation_enabled = citation_enabled
                plugin.save()

                sync_plugin_components(plugin, plugin_data)

                synced += 1
                messages.info(request, f"{plugin.name}: Synced ({old_commit} → {latest_commit[:7]})")

        except git.exc.GitCommandError as e:
            messages.error(request, f"{plugin.name}: Git error - {str(e)[:100]}")
            failed += 1
        except Exception as e:
            messages.error(request, f"{plugin.name}: Error - {str(e)[:100]}")
            failed += 1

    messages.success(request, f"Sync complete: {synced} synced, {failed} failed")


@admin.action(description="Approve selected plugins")
def approve_plugins(modeladmin, request, queryset):
    """Approve selected plugins."""
    updated = queryset.update(status='approved')
    messages.success(request, f"{updated} plugins approved")


@admin.action(description="Reject selected plugins")
def reject_plugins(modeladmin, request, queryset):
    """Reject selected plugins."""
    updated = queryset.update(status='rejected')
    messages.success(request, f"{updated} plugins rejected")


@admin.action(description="Set to pending")
def set_pending(modeladmin, request, queryset):
    """Set selected plugins to pending status."""
    updated = queryset.update(status='pending')
    messages.success(request, f"{updated} plugins set to pending")


class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'status', 'author', 'category', 'short_commit', 'has_repository')
    list_filter = ('status', 'category', 'author')
    list_editable = ('status',)
    search_fields = ('name', 'description', 'author__name')
    actions = [check_updates, sync_to_latest, approve_plugins, reject_plugins, set_pending]

    @admin.display(description='Commit')
    def short_commit(self, obj):
        if obj.commit_hash:
            return obj.commit_hash[:7]
        return "-"

    @admin.display(description='Has Repo', boolean=True)
    def has_repository(self, obj):
        return bool(obj.repository)


admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Plugin, PluginAdmin)
