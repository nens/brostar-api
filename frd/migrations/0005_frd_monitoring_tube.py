import django.db.models.deletion
from django.db import migrations, models


def populate_monitoring_tube_fk(apps, schema_editor):
    """Populate monitoring_tube FK from gmw_bro_id + tube_number"""
    FRD = apps.get_model("frd", "FRD")
    MonitoringTube = apps.get_model("gmw", "MonitoringTube")
    _ = apps.get_model("gmw", "GMW")

    # Build lookup: {(bro_id, tube_number): MonitoringTube}
    tube_lookup = {}
    for tube in MonitoringTube.objects.select_related("gmw").all():
        key = (tube.gmw.bro_id, tube.tube_number)
        tube_lookup[key] = tube

    updated = 0
    orphaned = 0

    for frd in FRD.objects.all():
        key = (frd.gmw_bro_id, frd.tube_number)
        tube = tube_lookup.get(key)

        if tube:
            frd.monitoring_tube = tube
            frd.save(update_fields=["monitoring_tube"])
            updated += 1
        else:
            orphaned += 1
            print(f"WARNING: No tube found for {frd.gmw_bro_id} tube {frd.tube_number}")

    print(
        f"Linked {updated} formation resistance dossiers to tubes, {orphaned} orphaned"
    )


def reverse_populate(apps, schema_editor):
    """Reverse migration - clear the FK"""
    FRD = apps.get_model("frd", "FRD")
    FRD.objects.update(monitoring_tube=None)


class Migration(migrations.Migration):
    dependencies = [
        ("frd", "0004_alter_frd_internal_id"),
        ("gmw", "0022_alter_gmw_internal_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="frd",
            name="monitoring_tube",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="formation_resistance_dossiers",
                to="gmw.monitoringtube",
            ),
        ),
        # Populate FK from existing gmw_bro_id + tube_number
        migrations.RunPython(populate_monitoring_tube_fk, reverse_populate),
    ]
