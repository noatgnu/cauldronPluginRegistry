# Generated migration for plugin schema v2 support
# This migration completely removes deprecated fields and migrates to v2 schema

from django.db import migrations, models


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
        migrations.RunSQL(
            sql='''
                UPDATE plugins_runtime
                SET entrypoint = COALESCE(script, '')
                WHERE entrypoint IS NULL OR entrypoint = '';
            ''',
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Step 4: Data migration - Convert accept to file_types
        migrations.RunSQL(
            sql='''
                UPDATE plugins_input
                SET file_types = json_array(COALESCE(accept, ''))
                WHERE (file_types IS NULL OR json_array_length(file_types) = 0)
                AND accept IS NOT NULL AND accept != '';
            ''',
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Step 5: Data migration - Convert type to environments
        migrations.RunSQL(
            sql='''
                UPDATE plugins_runtime
                SET environments = CASE
                    WHEN type = 'pythonWithR' THEN json_array('python', 'r')
                    WHEN type IS NOT NULL AND type != '' THEN json_array(type)
                    ELSE json_array()
                END
                WHERE environments IS NULL OR json_array_length(environments) = 0;
            ''',
            reverse_sql=migrations.RunSQL.noop,
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
