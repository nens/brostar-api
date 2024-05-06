import logging
from typing import TypeVar

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.query import QuerySet

from api.models import Organisation, UploadFile
from gar.models import GAR

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
        - Save the parameter mapping csv file (also provided by RHDHV) also as upload file. Save the uuid
        - Run this command.
    """

    help = "Uploads GAR data based on DAWACO exports."

    def handle(self, *args, **options):
        organisation_uuid = "49c39ce8-3df8-4fe7-847f-33a647e100d0"
        gar_data_file_uuid = "25293571-991b-4eec-b991-03cd61c3c9f3"
        # parameter_mapping_uuid = "90a4cc27-87e3-4d6b-8d8e-21dd4bc5af33"

        # Get instances
        organisation_instance = get_django_instance(Organisation, organisation_uuid)
        gar_data_file_instance = get_django_instance(UploadFile, gar_data_file_uuid)
        # parameter_mapping_file_instance = get_django_instance(
        #     UploadFile, parameter_mapping_uuid
        # )

        # Read csv files
        dawaco_gar_data_df = read_csv_file(gar_data_file_instance, delimiter=";")
        # parameter_mapping_df = read_csv_file(
        #     parameter_mapping_file_instance, delimiter=";"
        # )

        # Transform df
        gar_df = transform_gar_data(dawaco_gar_data_df)

        # Get all current BRO GARs
        gar_queryset: QuerySet[GAR] = GAR.objects.filter(
            data_owner=organisation_instance,
        )

        # Filter gar_df
        filtered_gar_df = filter_out_delivered_gars(gar_df, gar_queryset)

        print(filtered_gar_df)


def get_django_instance(model: type[T], uuid: str) -> T:
    try:
        return model.objects.get(uuid=uuid)
    except model.DoesNotExist:
        logger.error(f"{model.__name__} with UUID {uuid} does not exist.")
        raise


def read_csv_file(upload_file_instance: UploadFile, delimiter: str) -> pd.DataFrame:
    try:
        return pd.read_csv(upload_file_instance.file.path, delimiter=delimiter)
    except OSError as e:
        logger.error(f"Failed to read file: {upload_file_instance.file.path} - {e}")
        raise


def transform_gar_data(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # Date column to datetime type
        df["Resultaatdatum"] = pd.to_datetime(df["Resultaatdatum"])

        # Splitting the 'Meetobject.lokaalid' column into two
        df[["nitg_code", "tube_number"]] = df["Meetobject.lokaalid"].str.split(
            "_", expand=True
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
            ]
        )

        return df
    except Exception as e:
        logger.error(f"Failed to transform gar csv file: - {e}")
        raise


def filter_out_delivered_gars(
    df: pd.DataFrame, gar_queryset: QuerySet[GAR]
) -> pd.DataFrame:
    try:
        for gar in gar_queryset:
            df = df[
                ~(
                    (df["nitg_code"] == gar.gmw_nitg_code)
                    & (df["tube_number"] == gar.tube_number)
                    & (df["Resultaatdatum"] == gar.lab_analysis_date)
                )
            ]

        return df
    except Exception as e:
        logger.error(f"Failed to filter gar csv file: - {e}")
        raise
