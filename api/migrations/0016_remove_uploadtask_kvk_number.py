# Generated by Django 5.0.1 on 2024-02-21 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_alter_userprofile_bro_user_password_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="uploadtask",
            name="kvk_number",
        ),
    ]
