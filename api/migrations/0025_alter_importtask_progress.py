# Generated by Django 5.0.1 on 2024-03-26 13:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0024_importtask_progress"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importtask",
            name="progress",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
