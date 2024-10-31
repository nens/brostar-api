# Generated by Django 5.0.4 on 2024-10-31 09:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gmw", "0013_monitoringtube_sediment_sump_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="monitoringtube",
            name="screen_protection",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="gmw",
            name="ground_level_position",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="gmw",
            name="owner",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="gmw",
            name="well_stability",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="monitoringtube",
            name="sediment_sump_length",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="monitoringtube",
            name="tube_top_diameter",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
