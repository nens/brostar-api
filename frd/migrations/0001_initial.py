# Generated by Django 5.0.4 on 2024-05-27 08:58

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("api", "0042_alter_uploadtask_registration_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="FRD",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("bro_id", models.CharField(max_length=18)),
                (
                    "delivery_accountable_party",
                    models.CharField(max_length=8, null=True),
                ),
                ("quality_regime", models.CharField(max_length=100, null=True)),
                ("gmw_bro_id", models.CharField(max_length=100, null=True)),
                ("tube_number", models.CharField(max_length=100, null=True)),
                ("research_first_date", models.DateField(blank=True, null=True)),
                ("research_last_date", models.DateField(blank=True, null=True)),
                (
                    "data_owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="api.organisation",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "FRD's",
            },
        ),
    ]
