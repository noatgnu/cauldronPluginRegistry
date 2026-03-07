import tempfile
import os

import git
import yaml
import markdown
import re

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    Author,
    Category,
    Plugin,
    UserProfile,
    Runtime,
    Input,
    Output,
    PluginEnvVariable,
    Execution,
    Plot,
    Annotation,
    Example,
    RepositorySSHKey,
)


admin.site.site_header = "Cauldron Plugin Registry"
admin.site.site_title = "Plugin Registry Admin"
admin.site.index_title = "Plugin Management"


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class RuntimeInline(admin.StackedInline):
    model = Runtime
    extra = 0
    max_num = 1
    fields = ('environments', 'entrypoint', 'docker')


class InputInline(admin.TabularInline):
    model = Input
    extra = 0
    fields = ('name', 'label', 'type', 'required', 'default')
    show_change_link = True


class OutputInline(admin.TabularInline):
    model = Output
    extra = 0
    fields = ('name', 'path', 'type', 'format')
    show_change_link = True


class PluginEnvVariableInline(admin.TabularInline):
    model = PluginEnvVariable
    extra = 0
    fields = ('name', 'label', 'type', 'required', 'default')
    show_change_link = True


class ExecutionInline(admin.StackedInline):
    model = Execution
    extra = 0
    max_num = 1


class PlotInline(admin.TabularInline):
    model = Plot
    extra = 0
    fields = ('plot_id', 'name', 'type', 'component', 'dataSource')
    show_change_link = True


class AnnotationInline(admin.StackedInline):
    model = Annotation
    extra = 0
    max_num = 1


class ExampleInline(admin.StackedInline):
    model = Example
    extra = 0
    max_num = 1


def sync_plugin_components(plugin, plugin_data):
    """Sync all plugin components from plugin data."""
    runtime_info = plugin_data.get('runtime', {})
    Runtime.objects.filter(plugin=plugin).delete()
    if runtime_info:
        Runtime.objects.create(
            plugin=plugin,
            environments=runtime_info.get('environments', []),
            entrypoint=runtime_info.get('entrypoint', ''),
            docker=runtime_info.get('docker')
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
            accept=inp.get('accept', ''),
            multiple=inp.get('multiple', False),
            sourceFile=inp.get('sourceFile', ''),
            min=inp.get('min'),
            max=inp.get('max'),
            step=inp.get('step'),
            options=inp.get('options'),
            optionsFromFile=inp.get('optionsFromFile', ''),
            groups=inp.get('groups'),
            groupsFromFile=inp.get('groupsFromFile', ''),
            visibleWhen=inp.get('visibleWhen'),
            disableAnnotationManagement=inp.get('disableAnnotationManagement', False),
            tableColumns=inp.get('tableColumns')
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

    Execution.objects.filter(plugin=plugin).delete()
    if execution_info:
        Execution.objects.create(
            plugin=plugin,
            argsMapping=execution_info.get('argsMapping'),
            outputDir=execution_info.get('outputDir', ''),
            requirements=execution_info.get('requirements')
        )

    Plot.objects.filter(plugin=plugin).delete()
    plots_data = plugin_data.get('plots', [])
    for plot in plots_data:
        Plot.objects.create(
            plugin=plugin,
            plot_id=plot.get('id', ''),
            name=plot.get('name', ''),
            type=plot.get('type', ''),
            component=plot.get('component', ''),
            dataSource=plot.get('dataSource', ''),
            config=plot.get('config'),
            customization=plot.get('customization')
        )

    Annotation.objects.filter(plugin=plugin).delete()
    annotation_data = plugin_data.get('annotation')
    if annotation_data:
        Annotation.objects.create(
            plugin=plugin,
            samplesFrom=annotation_data.get('samplesFrom', ''),
            annotationFile=annotation_data.get('annotationFile', '')
        )

    Example.objects.filter(plugin=plugin).delete()
    example_data = plugin_data.get('example')
    if example_data:
        Example.objects.create(
            plugin=plugin,
            enabled=example_data.get('enabled', False),
            values=example_data.get('values')
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


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'id', 'version', 'status', 'author', 'category',
        'short_commit', 'repo_link', 'input_count', 'output_count', 'updated_at'
    )
    list_filter = ('status', 'category', 'author', 'diagram_enabled', 'citation_enabled', 'requires_authentication')
    list_editable = ('status',)
    search_fields = ('id', 'name', 'description', 'author__name', 'repository')
    ordering = ('-updated_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = [check_updates, sync_to_latest, approve_plugins, reject_plugins, set_pending]

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'name', 'description', 'version', 'icon')
        }),
        ('Classification', {
            'fields': ('author', 'category', 'subcategory', 'status')
        }),
        ('Repository', {
            'fields': ('repository', 'commit_hash', 'recommended_commit', 'latest_stable_tag', 'requires_authentication')
        }),
        ('Features', {
            'fields': ('diagram_enabled', 'citation_enabled'),
            'classes': ('collapse',)
        }),
        ('Ownership', {
            'fields': ('submitted_by',),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('readme',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
    inlines = [RuntimeInline, InputInline, OutputInline, PluginEnvVariableInline, ExecutionInline, PlotInline, AnnotationInline, ExampleInline]

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'approved': '#28a745',
            'pending': '#ffc107',
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.status.upper()
        )

    @admin.display(description='Commit')
    def short_commit(self, obj):
        if obj.commit_hash:
            return format_html(
                '<code style="background: #f4f4f4; padding: 2px 6px; border-radius: 3px;">{}</code>',
                obj.commit_hash[:7]
            )
        return "-"

    @admin.display(description='Repository')
    def repo_link(self, obj):
        if obj.repository:
            return format_html(
                '<a href="{}" target="_blank" title="{}">🔗 Open</a>',
                obj.repository, obj.repository
            )
        return "-"

    @admin.display(description='Inputs')
    def input_count(self, obj):
        count = obj.inputs.count()
        return format_html('<span style="color: #007bff;">{}</span>', count)

    @admin.display(description='Outputs')
    def output_count(self, obj):
        count = obj.outputs.count()
        return format_html('<span style="color: #28a745;">{}</span>', count)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'plugin_count')
    search_fields = ('name', 'email')

    @admin.display(description='Plugins')
    def plugin_count(self, obj):
        return obj.plugin_set.count()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'plugin_count')
    search_fields = ('name', 'description')

    @admin.display(description='Plugins')
    def plugin_count(self, obj):
        return obj.plugin_set.count()


@admin.register(Input)
class InputAdmin(admin.ModelAdmin):
    list_display = ('name', 'plugin', 'type', 'required', 'label')
    list_filter = ('type', 'required', 'plugin')
    search_fields = ('name', 'label', 'plugin__name')


@admin.register(Output)
class OutputAdmin(admin.ModelAdmin):
    list_display = ('name', 'plugin', 'type', 'format', 'path')
    list_filter = ('type', 'format', 'plugin')
    search_fields = ('name', 'path', 'plugin__name')


@admin.register(Runtime)
class RuntimeAdmin(admin.ModelAdmin):
    list_display = ('plugin', 'entrypoint', 'environment_list', 'has_docker')
    list_filter = ('environments',)
    search_fields = ('plugin__name', 'entrypoint')

    @admin.display(description='Environments')
    def environment_list(self, obj):
        if obj.environments:
            return ', '.join(obj.environments)
        return '-'

    @admin.display(description='Docker', boolean=True)
    def has_docker(self, obj):
        return bool(obj.docker)


@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    list_display = ('plugin', 'outputDir', 'has_requirements', 'has_args_mapping')
    search_fields = ('plugin__name',)

    @admin.display(description='Requirements', boolean=True)
    def has_requirements(self, obj):
        return bool(obj.requirements)

    @admin.display(description='Args Mapping', boolean=True)
    def has_args_mapping(self, obj):
        return bool(obj.argsMapping)


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'plugin', 'type', 'component', 'dataSource')
    list_filter = ('type', 'plugin')
    search_fields = ('name', 'plugin__name', 'plot_id')


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('plugin', 'samplesFrom', 'annotationFile')
    search_fields = ('plugin__name',)


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ('plugin', 'enabled')
    list_filter = ('enabled',)
    search_fields = ('plugin__name',)


@admin.register(RepositorySSHKey)
class RepositorySSHKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'repository_url', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'repository_url')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Key Info', {
            'fields': ('user', 'repository_url')
        }),
        ('Credentials', {
            'fields': ('ssh_private_key', 'passphrase'),
            'classes': ('collapse',),
            'description': 'SSH credentials are encrypted at rest.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(PluginEnvVariable)
class PluginEnvVariableAdmin(admin.ModelAdmin):
    list_display = ('name', 'plugin', 'type', 'required', 'label')
    list_filter = ('type', 'required', 'plugin')
    search_fields = ('name', 'label', 'plugin__name')
