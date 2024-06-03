# Generated by Django 5.0.4 on 2024-05-29 11:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0042_alter_uploadtask_registration_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uploadtask",
            name="registration_type",
            field=models.CharField(
                choices=[
                    ("GMN_StartRegistration", "GMN_StartRegistration"),
                    ("GMN_MeasuringPoint", "GMN_MeasuringPoint"),
                    ("GMN_MeasuringPointEndDate", "GMN_MeasuringPointEndDate"),
                    ("GMN_TubeReference", "GMN_TubeReference"),
                    ("GMN_Closure", "GMN_Closure"),
                    ("GMW_Construction", "GMW_Construction"),
                    ("GAR", "GAR"),
                    ("GLD_StartRegistration", "GLD_StartRegistration"),
                    ("GLD_Addition", "GLD_Addition"),
                    ("GLD_Closure", "GLD_Closure"),
                    ("FRD_StartRegistration", "FRD_StartRegistration"),
                    (
                        "FRD_GEM_MeasurementConfiguration",
                        "FRD_GEM_MeasurementConfiguration",
                    ),
                    ("FRD_GEM_Measurement", "GLD_CloFRD_GEM_Measurementsure"),
                    (
                        "FRD_EMM_InstrumentConfiguration",
                        "FRD_EMM_InstrumentConfiguration",
                    ),
                    ("FRD_EMM_Measurement", "FRD_EMM_Measurement"),
                    ("FRD_Closure", "FRD_Closure"),
                ],
                max_length=235,
            ),
        ),
    ]