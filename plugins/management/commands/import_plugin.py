import os
import yaml
from django.core.management.base import BaseCommand
from plugins.models import Plugin, Author, Category, Runtime, Input, Output


class Command(BaseCommand):
    help = 'Import a plugin from a plugin.yaml file'

    def add_arguments(self, parser):
        parser.add_argument('plugin_yaml_path', type=str, help='Path to the plugin.yaml file')

    def handle(self, *args, **options):
        yaml_path = options['plugin_yaml_path']

        if not os.path.exists(yaml_path):
            self.stdout.write(self.style.ERROR(f'File not found: {yaml_path}'))
            return

        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        plugin_data = data.get('plugin', {})
        plugin_id = plugin_data.get('id')

        if not plugin_id:
            self.stdout.write(self.style.ERROR('Plugin ID not found in YAML'))
            return

        author_name = plugin_data.get('author', 'CauldronGO Team')
        author, _ = Author.objects.get_or_create(name=author_name)

        category_name = plugin_data.get('category', 'utilities')
        category, _ = Category.objects.get_or_create(name=category_name)

        plugin, created = Plugin.objects.update_or_create(
            id=plugin_id,
            defaults={
                'name': plugin_data.get('name', plugin_id),
                'description': plugin_data.get('description', ''),
                'version': plugin_data.get('version', '1.0.0'),
                'author': author,
                'category': category,
                'subcategory': plugin_data.get('subcategory'),
                'icon': plugin_data.get('icon'),
                'status': 'approved',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created plugin: {plugin.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated plugin: {plugin.name}'))

        runtime_data = data.get('runtime', {})
        Runtime.objects.update_or_create(
            plugin=plugin,
            defaults={
                'environments': runtime_data.get('environments', []),
                'entrypoint': runtime_data.get('entrypoint', ''),
            }
        )

        Input.objects.filter(plugin=plugin).delete()
        for input_data in data.get('inputs', []):
            Input.objects.create(
                plugin=plugin,
                name=input_data.get('name'),
                label=input_data.get('label'),
                type=input_data.get('type'),
                required=input_data.get('required', False),
                default=input_data.get('default'),
                description=input_data.get('description'),
                placeholder=input_data.get('placeholder'),
                file_types=input_data.get('accept', '').split(',') if input_data.get('accept') else [],
                multiple=input_data.get('multiple', False),
                sourceFile=input_data.get('sourceFile'),
                min=input_data.get('min'),
                max=input_data.get('max'),
                step=input_data.get('step'),
            )

        Output.objects.filter(plugin=plugin).delete()
        for output_data in data.get('outputs', []):
            Output.objects.create(
                plugin=plugin,
                name=output_data.get('name'),
                path=output_data.get('path'),
                type=output_data.get('type'),
                description=output_data.get('description'),
                format=output_data.get('format'),
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully imported plugin {plugin.name} with {plugin.inputs.count()} inputs and {plugin.outputs.count()} outputs'))
