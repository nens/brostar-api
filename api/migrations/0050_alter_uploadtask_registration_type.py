# Generated by Django 5.0.4 on 2024-10-31 09:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0049_alter_inviteuser_nens_auth_client_invitation"),
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
                    ("GMW_ElectrodeStatus", "GMW_ElectrodeStatus"),
                    ("GMW_GroundLevel", "GMW_GroundLevel"),
                    ("GMW_GroundLevelMeasuring", "GMW_GroundLevelMeasuring"),
                    ("GMW_Insertion", "GMW_Insertion"),
                    ("GMW_Lengthening", "GMW_Lengthening"),
                    ("GMW_Shortening", "GMW_Shortening"),
                    ("GMW_Positions", "GMW_Positions"),
                    ("GMW_PositionsMeasuring", "GMW_PositionsMeasuring"),
                    ("GMW_Shift", "GMW_Shift"),
                    ("GMW_Maintainer", "GMW_Maintainer"),
                    ("GMW_Owner", "GMW_Owner"),
                    ("GMW_Removal", "GMW_Removal"),
                    ("GMW_TubeStatus", "GMW_TubeStatus"),
                    ("GMW_WellHeadProtector", "GMW_WellHeadProtector"),
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
