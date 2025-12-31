# Generated migration for plugin schema v2 support
# This migration completely removes deprecated fields and migrates to v2 schema

from django.db import migrations, models


def migrate_script_to_entrypoint(apps, schema_editor):
    Runtime = apps.get_model('plugins', 'Runtime')
    for runtime in Runtime.objects.filter(entrypoint__isnull=True):
        runtime.entrypoint = runtime.script or ''
        runtime.save()
    for runtime in Runtime.objects.filter(entrypoint=''):
        runtime.entrypoint = runtime.script or ''
        runtime.save()


def migrate_accept_to_file_types(apps, schema_editor):
    Input = apps.get_model('plugins', 'Input')
    for input_obj in Input.objects.all():
        if not input_obj.file_types or len(input_obj.file_types) == 0:
            if input_obj.accept:
                input_obj.file_types = [input_obj.accept]
                input_obj.save()


def migrate_type_to_environments(apps, schema_editor):
    Runtime = apps.get_model('plugins', 'Runtime')
    for runtime in Runtime.objects.all():
        if not runtime.environments or len(runtime.environments) == 0:
            if runtime.type == 'pythonWithR':
                runtime.environments = ['python', 'r']
            elif runtime.type:
                runtime.environments = [runtime.type]
            else:
                runtime.environments = []
            runtime.save()


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0013_plugin_tags'),
    ]

    operations = [
        # Step 1: Add new entrypoint field (temporary nullable)
        migrations.AddField(
            model_name='runtime',
            name='entrypoint',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        # Step 2: Add new file_types field
        migrations.AddField(
            model_name='input',
            name='file_types',
            field=models.JSONField(blank=True, null=True, default=list),
        ),
        # Step 3: Data migration - Copy script to entrypoint
        migrations.RunPython(
            migrate_script_to_entrypoint,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 4: Data migration - Convert accept to file_types
        migrations.RunPython(
            migrate_accept_to_file_types,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 5: Data migration - Convert type to environments
        migrations.RunPython(
            migrate_type_to_environments,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 6: Make entrypoint non-nullable now that data is migrated
        migrations.AlterField(
            model_name='runtime',
            name='entrypoint',
            field=models.CharField(max_length=255),
        ),
        # Step 7: Make environments non-nullable with default
        migrations.AlterField(
            model_name='runtime',
            name='environments',
            field=models.JSONField(default=list),
        ),
        # Step 8: Remove deprecated fields
        migrations.RemoveField(
            model_name='runtime',
            name='type',
        ),
        migrations.RemoveField(
            model_name='runtime',
            name='script',
        ),
        migrations.RemoveField(
            model_name='input',
            name='accept',
        ),
    ]
