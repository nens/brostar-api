# Generated by Django 5.0.4 on 2025-03-05 07:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gmw", "0018_remove_gmw_nr_of_intermediate_events_alter_event_gmw_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gmw",
            name="nitg_code",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
