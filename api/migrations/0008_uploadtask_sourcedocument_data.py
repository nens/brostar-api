# Generated by Django 5.0.1 on 2024-02-14 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_uploadtask"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadtask",
            name="sourcedocument_data",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="Sourcedocument data"
            ),
        ),
    ]