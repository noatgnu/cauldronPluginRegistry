from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0008_plugin_commit_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='plugin',
            name='recommended_commit',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='plugin',
            name='latest_stable_tag',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
