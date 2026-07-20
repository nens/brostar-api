"""Rename BHR-P/BHR-GT/SFR registration type keys to match XML source-document element names.

Old → New mapping:
  BHR-P  → BHR_P
  BHR-G  → BHR_G
  BHR-GT → BHR_GT_CompleteReport_V1
  SFR    → SFR_CompleteReport_V1
"""

from django.db import migrations, models

RENAMES = [
    ("BHR-P", "BHR_P"),
    ("BHR-G", "BHR_G"),
    ("BHR-GT", "BHR_GT_CompleteReport_V1"),
    ("SFR", "SFR_CompleteReport_V1"),
]

REGISTRATION_TYPE_CHOICES = [
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
    ("GMW_SubsequentAdditionalSurvey", "GMW_SubsequentAdditionalSurvey"),
    ("GMW_TubeStatus", "GMW_TubeStatus"),
    ("GMW_WellHeadProtector", "GMW_WellHeadProtector"),
    ("GAR", "GAR"),
    ("GLD_StartRegistration", "GLD_StartRegistration"),
    ("GLD_Addition", "GLD_Addition"),
    ("GLD_Closure", "GLD_Closure"),
    ("FRD_StartRegistration", "FRD_StartRegistration"),
    ("FRD_GEM_MeasurementConfiguration", "FRD_GEM_MeasurementConfiguration"),
    ("FRD_GEM_Measurement", "FRD_GEM_Measurements"),
    ("FRD_EMM_InstrumentConfiguration", "FRD_EMM_InstrumentConfiguration"),
    ("FRD_EMM_Measurement", "FRD_EMM_Measurement"),
    ("FRD_Closure", "FRD_Closure"),
    ("CPT", "CPT"),
    ("BHR_P", "BHR_P"),
    ("BHR_G", "BHR_G"),
    ("BHR_GT_CompleteReport_V1", "BHR_GT_CompleteReport_V1"),
    ("SFR_CompleteReport_V1", "SFR_CompleteReport_V1"),
    ("GUF_StartRegistration", "GUF_StartRegistration"),
    ("GUF_NewLicense", "GUF_NewLicense"),
    ("GUF_ExpandedRealisedInstallation", "GUF_ExpandedRealisedInstallation"),
    ("GUF_WellFunction", "GUF_WellFunction"),
    ("GUF_Height", "GUF_Height"),
    ("GUF_Closure", "GUF_Closure"),
    ("GUF_AddRealisedInstallation", "GUF_AddRealisedInstallation"),
    ("GUF_ClosureRealisedPart", "GUF_ClosureRealisedPart"),
    ("GPD_StartRegistration", "GPD_StartRegistration"),
    ("GPD_AddReport", "GPD_AddReport"),
    ("GPD_EndRegistration", "GPD_EndRegistration"),
    ("RAW_XML_UPLOAD", "RAW_XML_UPLOAD"),
]


def rename_forward(apps, schema_editor):
    UploadTask = apps.get_model("api", "UploadTask")
    for old, new in RENAMES:
        UploadTask.objects.filter(registration_type=old).update(registration_type=new)


def rename_backward(apps, schema_editor):
    UploadTask = apps.get_model("api", "UploadTask")
    for old, new in RENAMES:
        UploadTask.objects.filter(registration_type=new).update(registration_type=old)


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0062_objectimporttask"),
    ]

    operations = [
        migrations.RunPython(rename_forward, rename_backward),
        migrations.AlterField(
            model_name="uploadtask",
            name="registration_type",
            field=models.CharField(
                blank=False,
                max_length=235,
                choices=REGISTRATION_TYPE_CHOICES,
            ),
        ),
    ]
