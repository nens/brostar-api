import logging

from gpd.models import GPD, Report, VolumeSeries

logger = logging.getLogger(__name__)


def create_gpd(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create a GPD record."""
    GPD.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "delivery_accountable_party": metadata.get("deliveryAccountableParty"),
            "quality_regime": metadata.get("qualityRegime"),
        },
    )
    logger.info(f"Successfully created/updated GPD bro_id={bro_id}.")


def create_gpd_report(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create a Report with its VolumeSeries records for an existing GPD."""
    try:
        gpd = GPD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GPD.DoesNotExist:
        logger.info(f"GPD not found for bro_id={bro_id}, owner={data_owner}")
        return

    volume_series_data = sourcedocument_data.get("volumeSeries", [])

    # Derive begin/end date of the report from the enclosed volume series
    begin_dates = [
        vs.get("beginDate") for vs in volume_series_data if vs.get("beginDate")
    ]
    end_dates = [vs.get("endDate") for vs in volume_series_data if vs.get("endDate")]
    report_begin = min(begin_dates) if begin_dates else None
    report_end = max(end_dates) if end_dates else None

    report, _ = Report.objects.update_or_create(
        gpd=gpd,
        report_id=sourcedocument_data.get("reportId"),
        data_owner=data_owner,
        defaults={
            "method": sourcedocument_data.get("method", "onbekend"),
            "begin_date": report_begin,
            "end_date": report_end,
            "groundwater_usage_facility_bro_id": sourcedocument_data.get(
                "groundwaterUsageFacilityBroId", ""
            ),
        },
    )

    for vs in volume_series_data:
        VolumeSeries.objects.update_or_create(
            report=report,
            water_in_out=vs.get("waterInOut"),
            temperature=vs.get("temperature", "onbekend"),
            begin_date=vs.get("beginDate"),
            end_date=vs.get("endDate"),
            data_owner=data_owner,
            defaults={
                "volume": vs.get("volume", 0.0),
            },
        )

    logger.info(
        f"Successfully created/updated report {sourcedocument_data.get('reportId')} for GPD bro_id={bro_id}."
    )
