import logging
import time
from typing import TypeVar

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.query import QuerySet

from api.bro_upload import config
from api.bro_upload import upload_datamodels as datamodels
from api.models import Organisation, UploadFile, UploadTask
from gar import models as gar_models
from gmw import models as gmw_models

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=models.Model)


class Command(BaseCommand):
    """This command helps to upload GAR data based on DAWACO exports.
    In order to run the command:
        - Create an organisation for the client
        - Import their GMW and GAR data
        - Check if the gmw_bro_id's that are found in the GAR data are present in the database after the GMW import
            - If so, continue
            - If not, check which organisation owns the GMWs. Import their GMWs as well, but keep the data owner the clients organisation.
        - Save the dawaco gar data export file as Upload File in the django admin, and save the uuid (easiest is to place it directly in the script)
        - Check some of the hardcoded data (find by ctrl+f "# hardcoded") and check whether they work for your case.
        - Run this command.
    """

    help = "Uploads GAR data based on DAWACO exports."

    def handle(self, *args, **options):
        # INPUT DATA
        organisation_uuid = "4253c513-d845-40a5-afd3-0c55b1e64165"  # hardcoded
        gar_data_file_uuid = "ca483e58-40ce-40f0-91df-5b58ccd1e225"  # hardcoded
        field_research_data_uuid = "3bd84329-5711-45a0-8d78-54e782aad88f"  # hardcoded
        project_number = 1  # hardcoded

        # Get instances
        organisation_instance = get_django_instance(Organisation, organisation_uuid)
        gar_data_file_instance = get_django_instance(UploadFile, gar_data_file_uuid)
        field_data_file_instance = get_django_instance(
            UploadFile, field_research_data_uuid
        )

        # Read csv file
        dawaco_gar_data_df = read_csv_file(gar_data_file_instance, delimiter=";")
        field_data_df = read_csv_file(field_data_file_instance, delimiter=";")
        field_data_df["tube_number"] = field_data_df["tube_number"].astype(str)

        # Transform df
        gar_df = transform_gar_data(dawaco_gar_data_df)

        # Get all current BRO GARs
        gar_queryset: QuerySet[gar_models.GAR] = gar_models.GAR.objects.filter(
            data_owner=organisation_instance,
        )

        # Filter gar_df
        filtered_gar_df = filter_out_delivered_gars(gar_df, gar_queryset)

        # Group df per part that should result in 1 GAR uploadtask.
        grouped_gar_df = group_gar_df(filtered_gar_df)

        grouped_gar_df.apply(
            handle_gar_delivery,
            organisation_instance,
            project_number,
            field_data_df,
        )


def get_django_instance(model: type[T], uuid: str) -> T:
    """Returns the django instance of a given model based on the uuid"""
    try:
        return model.objects.get(uuid=uuid)
    except model.DoesNotExist:
        logger.error(f"{model.__name__} with UUID {uuid} does not exist.")
        raise


def read_csv_file(upload_file_instance: UploadFile, delimiter: str) -> pd.DataFrame:
    """Reads an UploadFile file and returns it as df"""
    try:
        return pd.read_csv(upload_file_instance.file.path, delimiter=delimiter)
    except OSError as e:
        logger.error(f"Failed to read file: {upload_file_instance.file.path} - {e}")
        raise


def transform_gar_data(df: pd.DataFrame) -> pd.DataFrame:
    """Handles the required transformation of the raw dawaco csv"""
    try:
        # Date column to datetime type
        df["Resultaatdatum"] = pd.to_datetime(df["Resultaatdatum"])

        # Splitting the 'Meetobject.lokaalid' column into two
        df[["nitg_code", "tube_number"]] = df["Meetobject.lokaalid"].str.split(
            "_", expand=True
        )

        # merging 2 columns
        df["parameter"] = np.where(
            df["Parameter.code"].fillna("") == "",
            df["Grootheid.code"],
            df["Parameter.code"],
        )

        # Removing leading zeros from 'tube_number'
        df["tube_number"] = df["tube_number"].str.lstrip("0")

        # Drop abundant columns
        df = df.drop(
            columns=[
                "Namespace",
                "Identificatie",
                "Meetwaarde.lokaalid",
                "Meetpunt.identificatie",
                "Monster.identificatie",
                "Begindatum",
                "Begintijd",
                "Einddatum",
                "Eindtijd",
                "Meetobject.lokaalid",
                "Grootheid.code",
                "Parameter.code",
            ]
        )

        return df
    except Exception as e:
        logger.error(f"Failed to transform gar csv file: - {e}")
        raise


def filter_out_delivered_gars(
    df: pd.DataFrame, gar_queryset: QuerySet[gar_models.GAR]
) -> pd.DataFrame:
    """Filters out the rows that have allready been delivered to the bro"""
    try:
        for gar in gar_queryset:
            df = df[
                ~(
                    (df["nitg_code"] == str(gar.gmw_nitg_code))
                    & (df["tube_number"] == str(gar.tube_number))
                    & (df["Resultaatdatum"] == pd.to_datetime(gar.lab_analysis_date))
                )
            ]

        return df
    except Exception as e:
        logger.error(f"Failed to filter gar csv file: - {e}")
        raise


def group_gar_df(df: pd.DataFrame) -> pd.DataFrame:
    """Groups the df per GAR. Each group is later on used to deliver 1 GAR message."""
    try:
        df = df.groupby(
            [
                "nitg_code",
                "tube_number",
                "Resultaatdatum",
            ]
        )
        return df
    except Exception as e:
        logger.error(f"Failed to group gar csv file: - {e}")
        raise


def handle_gar_delivery(
    gar_df: pd.DataFrame,
    organisation_instance: T,
    project_number: int,
    field_data_df: pd.DataFrame,
) -> None:
    """This apply function handles the delivery of a single GAR delivery."""

    # In order to not kill the BRO:
    time.sleep(10)

    uploadtask_metadata = {
        "qualityRegime": "IMBRO/A",  # hardcoded
        "requestReference": "dawaco_export_gar_data_bulk_upload_brostar",  # hardcoded
    }

    uploadtask_sourcedocument_data: datamodels.GAR = setup_gar_sourcedocs_data(
        gar_df,
        field_data_df,
    )

    if not uploadtask_sourcedocument_data:
        # Something went wrong during the creation of the sourcedosdata (check logging).
        # Skipping this one.
        return

    uploadtask_sourcedocument_data_dict = uploadtask_sourcedocument_data.model_dump()

    UploadTask.objects.create(
        data_owner=organisation_instance,
        bro_domain="GAR",
        project_number=project_number,
        registration_type="GAR",
        request_type="registration",
        metadata=uploadtask_metadata,
        sourcedocument_data=uploadtask_sourcedocument_data_dict,
    )


def setup_gar_sourcedocs_data(
    df: pd.DataFrame,
    field_data_df: pd.DataFrame,
) -> datamodels.GAR | None:
    """Creates a pydantic GAR instance, based on the data from a grouped df."""
    nitg_code = df["nitg_code"].iloc[0]
    tube_number = df["tube_number"].iloc[0]
    samplingdate = df["Resultaatdatum"].iloc[0]

    field_data = df[df["LocatieTypeWaardeBepaling.id"] == 2]
    lab_data = df[df["LocatieTypeWaardeBepaling.id"] == 1]

    gmw_objects = gmw_models.GMW.objects.filter(nitg_code=nitg_code)
    if gmw_objects.count() == 1:
        bro_id = gmw_objects.first().bro_id

    if gmw_objects.count() == 0:
        logger.error(f"No GMW found for {nitg_code}.")
        return None
    else:
        rivm_gmw = gmw_objects.order_by("owner").first()
        bro_id = rivm_gmw.bro_id
        logger.info(f"Double GMWS found for {nitg_code}. Using RIVM GMW.")

    sourcedocs_data_dict = {
        "objectIdAccountableParty": f"{nitg_code}_{tube_number}",
        "qualityControlMethod": "qCProtocolProvinciesEnRIVMv2021",  # hardcoded
        "gmwBroId": bro_id,
        "tubeNumber": tube_number,
        "fieldResearch": setup_field_research_data(
            field_data, field_data_df, samplingdate, nitg_code, tube_number
        ),
        "laboratoryAnalyses": setup_lab_data(lab_data, samplingdate),
    }

    sourcedocs_data = datamodels.GAR(**sourcedocs_data_dict)

    return sourcedocs_data


def convert_date_format(date: pd.Timestamp, target_format: str) -> str:
    return date.strftime(target_format)


def setup_field_research_data(
    field_data: pd.DataFrame,
    field_data_df: pd.DataFrame,
    samplingdate: pd.Timestamp,
    nitg_code: str,
    tube_number: str,
) -> datamodels.FieldResearch:
    """Fills the fieldResearch part of the GAR, using the pydantic model FieldResearch."""

    field_research_dict = {
        "samplingDateTime": samplingdate,
        "samplingStandard": "onbekend",  # hardcoded
        "pumpType": "onbekend",  # hardcoded
        "abnormalityInCooling": "onbekend",  # hardcoded
        "abnormalityInDevice": "onbekend",  # hardcoded
        "pollutedByEngine": "onbekend",  # hardcoded
        "filterAerated": "onbekend",  # hardcoded
        "groundWaterLevelDroppedTooMuch": "onbekend",  # hardcoded
        "abnormalFilter": "onbekend",  # hardcoded
        "sampleAerated": "onbekend",  # hardcoded
        "hoseReused": "onbekend",  # hardcoded
        "temperatureDifficultToMeasure": "onbekend",  # hardcoded
        "fieldMeasurements": setup_gar_field_measurements(field_data),
    }

    samplingdate_converted = convert_date_format(samplingdate, "%-d-%-m-%Y")

    # Filter the field_data_df to check whether a row is present for the provided combination of data
    row = field_data_df[
        (field_data_df["samplingdate"] == samplingdate_converted)
        & (field_data_df["nitg_code"] == nitg_code)
        & (field_data_df["tube_number"] == tube_number)
    ]

    if not row.empty:
        row_data = row.iloc[0]
        field_research_dict["samplingStandard"] = "NTA8017v2016"
        field_research_dict["pumpType"] = (
            row_data["pumpType"] if not pd.isna(row_data["pumpType"]) else "onbekend"
        )
        field_research_dict["abnormalityInCooling"] = (
            row_data["abnormalityInCooling"]
            if not pd.isna(row_data["abnormalityInCooling"])
            else "onbekend"
        )
        field_research_dict["abnormalityInDevice"] = (
            row_data["abnormalityInDevice"]
            if not pd.isna(row_data["abnormalityInDevice"])
            else "onbekend"
        )
        field_research_dict["pollutedByEngine"] = (
            row_data["pollutedByEngine"]
            if not pd.isna(row_data["pollutedByEngine"])
            else "onbekend"
        )
        field_research_dict["filterAerated"] = (
            row_data["filterAerated"]
            if not pd.isna(row_data["filterAerated"])
            else "onbekend"
        )
        field_research_dict["groundWaterLevelDroppedTooMuch"] = (
            row_data["groundWaterLevelDroppedTooMuch"]
            if not pd.isna(row_data["groundWaterLevelDroppedTooMuch"])
            else "onbekend"
        )
        field_research_dict["abnormalFilter"] = (
            row_data["abnormalFilter"]
            if not pd.isna(row_data["abnormalFilter"])
            else "onbekend"
        )
        field_research_dict["sampleAerated"] = (
            row_data["sampleAerated"]
            if not pd.isna(row_data["sampleAerated"])
            else "onbekend"
        )
        field_research_dict["hoseReused"] = (
            row_data["hoseReused"]
            if not pd.isna(row_data["hoseReused"])
            else "onbekend"
        )
        field_research_dict["temperatureDifficultToMeasure"] = (
            row_data["temperatureDifficultToMeasure"]
            if not pd.isna(row_data["temperatureDifficultToMeasure"])
            else "onbekend"
        )

    field_research = datamodels.FieldResearch(**field_research_dict)

    return field_research


def setup_gar_field_measurements(
    field_data: pd.DataFrame,
) -> list[datamodels.FieldMeasurement] | None:
    """Fills the fieldMeasurements part of the field reasearch of a GAR."""
    if field_data.empty:
        return None
    else:
        field_measurement_list = []

        for index, row in field_data.iterrows():
            parameter_key = row["parameter"]
            parameter_info = config.DAWACO_GAR_FIELD_DATA_MAPPING.get(parameter_key)

            field_measurement_dict = {
                "parameter": parameter_info["parameter_id"],
                "unit": parameter_info["unit"],
                "fieldMeasurementValue": row["Numeriekewaarde"],
                "qualityControlStatus": "onbekend",  # hardcoded
            }

            field_measurement = datamodels.FieldMeasurement(**field_measurement_dict)
            field_measurement_list.append(field_measurement)

        return field_measurement_list


def setup_lab_data(
    lab_data: pd.DataFrame, samplingdate: pd.Timestamp
) -> list[datamodels.LaboratoryAnalysis] | None:
    """Fills the laboratoryAnalyses part of the GAR."""
    if lab_data.empty:
        return None
    else:
        lab_analysis = {
            "analysisProcesses": setup_analysis_processes(lab_data, samplingdate),
        }

        return [datamodels.LaboratoryAnalysis(**lab_analysis)]


def setup_analysis_processes(
    lab_data: pd.DataFrame, samplingdate: pd.Timestamp
) -> list[datamodels.AnalysisProcess]:
    """Fills the analysisProcesses data of a LaboratoryAnalysis."""
    analysis_process_dict = {
        "date": samplingdate,
        "analyticalTechnique": "AAS",  # hardcoded
        "valuationMethod": "CIW",  # hardcoded
        "analyses": setup_analyses(lab_data),
    }

    analysis_process = datamodels.AnalysisProcess(**analysis_process_dict)

    return [analysis_process]


def setup_analyses(lab_data: pd.DataFrame) -> list[datamodels.Analysis]:
    """Fills the analysis data of a AnalysisProcess."""
    analyses_list = []

    for index, row in lab_data.iterrows():
        try:
            parameter = config.DAWACO_GAR_LAB_DATA_MAPPING[row["parameter"]]
            if parameter == "CONCTTE":
                # Parameter unknown
                continue
        except KeyError:
            logger.error(f"Cant find parameter_id for: {row['parameter']}")
            continue

        limit_symbol = (
            None if pd.isna(row.get("Limietsymbool")) else str(row["Limietsymbool"])
        )
        rapportage_grenswaarde = (
            None
            if pd.isna(row.get("Rapportagegrenswaarde"))
            else str(row["Rapportagegrenswaarde"])
        )

        analysis_dict = {
            "parameter": parameter,
            "unit": row["Eenheid.code"],
            "analysisMeasurementValue": row["Numeriekewaarde"],
            "limitSymbol": limit_symbol,
            "reportingLimit": rapportage_grenswaarde,
            "qualityControlStatus": "onbekend",  # hardcoded
        }

        analysis = datamodels.Analysis(**analysis_dict)
        analyses_list.append(analysis)

    return analyses_list
