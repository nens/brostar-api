# Generated by Django 5.0.4 on 2024-05-21 15:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0040_alter_uploadfile_bulk_upload"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="request_count",
            field=models.IntegerField(default=0),
        ),
    ]