# Generated by Django 5.0.4 on 2024-12-17 14:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0050_alter_uploadtask_registration_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="bulkupload",
            name="sourcedocument_data",
            field=models.JSONField(default=dict, verbose_name="Sourcedocument data"),
        ),
        migrations.AlterField(
            model_name="bulkupload",
            name="bulk_upload_type",
            field=models.CharField(
                choices=[("GAR", "GAR"), ("GLD", "GLD")],
                default=None,
                help_text="Determines which process/task to start.",
                max_length=3,
            ),
        ),
    ]