# Generated by Django 5.0.1 on 2024-02-15 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_userprofile_bro_user_password_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="project_number",
            field=models.CharField(default="", max_length=20),
            preserve_default=False,
        ),
    ]
