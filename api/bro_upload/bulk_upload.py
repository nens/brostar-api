import logging
import re
import time
from typing import TypeVar

import pandas as pd

from api import models as api_models
from api.bro_upload import config
from api.bro_upload.upload_datamodels import (
    GAR,
    Analysis,
    AnalysisProcess,
    FieldMeasurement,
    FieldResearch,
    LaboratoryAnalysis,
)

logger = logging.getLogger(__name__)


T = TypeVar("T", bound="api_models.UploadFile")


class GARBulkUploader:
    """Handles the upload process for bulk GAR data.

    Takes in the bulk_upload_instance_uuid and the uploaded files.
    Then orchestrates the whole transormation process of the files,
    and the creation of seperate uploadtasks.
    Keeps track of the process in the BulkUpload instance.
    """

    def __init__(
        self,
        bulk_upload_instance_uuid: str,
        fieldwork_upload_file_uuid: str,
        lab_upload_file_uuid: str,
        bro_username: str,
        bro_password: str,
    ) -> None:
        self.bulk_upload_instance: api_models.BulkUpload = (
            api_models.BulkUpload.objects.get(uuid=bulk_upload_instance_uuid)
        )
        self.bulk_upload_instance.status = "PROCESSING"
        self.bulk_upload_instance.save()

        self.fieldwork_file: api_models.UploadFile = api_models.UploadFile.objects.get(
            uuid=fieldwork_upload_file_uuid
        )
        self.lab_file: api_models.UploadFile = api_models.UploadFile.objects.get(
            uuid=lab_upload_file_uuid
        )

        self.bro_username: str = bro_username
        self.bro_password: str = bro_password

    def process(self) -> None:
        # Step 1: open the files and transform to a pd df
        try:
            fieldwork_df = csv_or_excel_to_df(self.fieldwork_file)
            lab_df = csv_or_excel_to_df(self.lab_file)

            self.bulk_upload_instance.progress = 10.00
            self.bulk_upload_instance.save()
        except Exception as e:
            self.bulk_upload_instance.log = e
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()

        # Step 2: transform the pandas files to a useable format
        try:
            # Rename headers
            fieldwork_df_rename_dict = {
                "BRO-ID": "bro_id",
                "Datum bemonsterd": "date",
                "Filter nr": "filter_num",
            }
            fieldwork_df = rename_df_columns(fieldwork_df, fieldwork_df_rename_dict)
            lab_df_rename_dict = {
                "GMW BRO ID": "bro_id",
                "Datum veldwerk": "date",
                "filter/buisnr": "filter_num",
            }
            lab_df = rename_df_columns(lab_df, lab_df_rename_dict)

            # Merge the 2 dfs
            merged_df = merge_fieldwork_and_lab_dfs(fieldwork_df, lab_df)

            # Remove some useless columns
            substrings_to_exclude = [
                "NITG",
                "Putcode",
                "Bijzonderheden",
                "coördinaat",
                "MeetpuntId",
                "Projectcode lab",
                "Monsternummer lab",
            ]
            trimmed_df = remove_df_columns(merged_df, substrings_to_exclude)

            self.bulk_upload_instance.progress = 20.00
            self.bulk_upload_instance.save()

        except Exception as e:
            self.bulk_upload_instance.log = e
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()

        # Step 3: Prepare data for uploadtask per row
        uploadtask_metadata = {
            "qualityRegime": self.bulk_upload_instance.metadata["qualityRegime"],
            "requestReference": self.bulk_upload_instance.metadata["requestReference"],
        }

        progress_per_row = round((80 / len(trimmed_df)), 2)

        for index, row in trimmed_df.iterrows():
            try:
                uploadtask_sourcedocument_data: GAR = create_gar_sourcesdocs_data(
                    row, self.bulk_upload_instance.metadata
                )

                uploadtask_sourcedocument_data_dict = (
                    uploadtask_sourcedocument_data.model_dump()
                )

                api_models.UploadTask.objects.create(
                    data_owner=self.bulk_upload_instance.data_owner,
                    bro_domain="GAR",
                    project_number=self.bulk_upload_instance.project_number,
                    registration_type="GAR",
                    request_type="registration",
                    metadata=uploadtask_metadata,
                    sourcedocument_data=uploadtask_sourcedocument_data_dict,
                )

                self.bulk_upload_instance.progress += progress_per_row
                self.bulk_upload_instance.save()
            except Exception as e:
                logger.warning(
                    f"Failed to upload GAR ({row.bro_id}) in bulk upload: {e}"
                )
                self.bulk_upload_instance.progress += progress_per_row
                self.bulk_upload_instance.save()
                # Skipping this row as it failed.
                continue
            finally:
                # Give your BRO some rest mate
                time.sleep(10)

        self.bulk_upload_instance.progress = 100.00
        self.bulk_upload_instance.status = "FINISHED"
        self.bulk_upload_instance.save()


def csv_or_excel_to_df(file_instance: T) -> pd.DataFrame:
    """Reads out csv or excel files and returns a pandas df."""
    filetype = file_instance.file.name.split(".")[-1].lower()

    if filetype == "csv":
        df = pd.read_csv(file_instance.file)
    elif filetype in ["xls", "xlsx"]:
        df = pd.read_excel(file_instance.file)
    else:
        raise ValueError(
            "Unsupported file type. Only CSV and Excel files are supported."
        )
    return df


def rename_df_columns(df: pd.DataFrame, rename_dict: dict[str, str]) -> pd.DataFrame:
    return df.rename(columns=rename_dict)


def merge_fieldwork_and_lab_dfs(
    fieldwork_df: pd.DataFrame, lab_df: pd.DataFrame
) -> pd.DataFrame:
    """Merges the files into 1 big df.

    This filters out the location/date combinations that are only present in 1 file."""
    return pd.merge(
        fieldwork_df, lab_df, on=["bro_id", "date", "filter_num"], how="inner"
    )


def remove_df_columns(
    df: pd.DataFrame, substrings_to_exclude: list[str]
) -> pd.DataFrame:
    substring_pattern = "|".join(substrings_to_exclude)
    return df.loc[:, ~df.columns.str.contains(substring_pattern)]


def create_gar_sourcesdocs_data(row: pd.Series, metadata: dict[str, any]) -> GAR:
    """Creates a GAR (the pydantic model), based on a row of the merged df of the GAR bulk upload input."""
    sourcedocs_data_dict = {
        "objectIdAccountableParty": f"{row['bro_id']}-{int(row['Meetronde'])}",
        "qualityControlMethod": metadata["qualityControlMethod"],
        "gmwBroId": row["bro_id"],
        "tubeNumber": row["filter_num"],
        "fieldResearch": create_gar_field_research(row, metadata),
        "laboratoryAnalyses": create_gar_lab_analysis(row, metadata),
    }

    if "groundwaterMonitoringNets" in metadata:
        sourcedocs_data_dict["groundwaterMonitoringNets"] = metadata[
            "groundwaterMonitoringNets"
        ]

    sourcedocs_data = GAR(**sourcedocs_data_dict)

    return sourcedocs_data


def create_gar_field_research(
    row: pd.Series, metadata: dict[str, any]
) -> FieldResearch:
    """Creates the FieldResearch pydantic model based on a row of the merged df of the GAR bulk upload input."""
    samplingdate = row["date"].strftime("%Y-%m-%d")

    field_research_dict = {
        "samplingDateTime": f"{samplingdate}T00:00:00+00:00",
        "samplingOperator": metadata["samplingOperator"],
        "samplingStandard": metadata["samplingStandard"],
        "pumpType": row["Pomptype"],
        "primaryColour": row["Hoofdkleur"],
        "secondaryColour": row["Bijkleur"],
        "colourStrength": row["Kleursterkte"],
        "abnormalityInCooling": row["Afwijkend gekoeld"],
        "abnormalityInDevice": row["Afwijking in meetapparatuur"],
        "pollutedByEngine": row["Contaminatie door verbrandingsmotor"],
        "filterAerated": row["Filter belucht/ drooggevallen"],
        "groundWaterLevelDroppedTooMuch": row["Grondwaterstand > 50 cm verlaagd"],
        "abnormalFilter": row["Inline filter afwijkend"],
        "sampleAerated": row["Monster belucht"],
        "hoseReused": row["Slang hergebruikt"],
        "temperatureDifficultToMeasure": row["Temperatuur moeilijk te bepalen"],
        "fieldMeasurements": create_gar_field_measurements(row),
    }

    field_research = FieldResearch(**field_research_dict)

    return field_research


def create_gar_field_measurements(row: pd.Series) -> list[FieldMeasurement]:
    """For now, the config dict is hardcoded in this function.
    If the options for other organisations differ, this should be redesigned"""
    field_measurement_list = []

    for parameter, details in config.FIELD_PARAMETER_OPTIONS.items():
        if parameter in row and row[parameter] != "niet bepaald":
            parameter_dict = {
                "parameter": details["parameter_id"],
                "unit": details["unit"],
                "fieldMeasurementValue": row[parameter],
                "qualityControlStatus": "onbekend",
            }

        field_measurement = FieldMeasurement(**parameter_dict)
        field_measurement_list.append(field_measurement)

    return field_measurement_list


def create_gar_lab_analysis(
    row: pd.Series, metadata: dict[str, any]
) -> list[LaboratoryAnalysis]:
    """Creates the LaboratoryAnalysis pydantic model based on a row of the merged df of the GAR bulk upload input."""
    lab_analysis = {
        "responsibleLaboratoryKvk": metadata["responsibleLaboratoryKvk"],
        "analysisProcesses": create_analysis_process(row),
    }

    return [LaboratoryAnalysis(**lab_analysis)]


def create_analysis_process(row: pd.Series) -> list[AnalysisProcess]:
    analysis_processes = []

    for parameter, details in config.LAB_PARAMETER_OPTIONS.items():
        value_column_pattern = rf"^\s*{parameter}\s+\(.*\)\s*$"
        value_column = next(
            (col for col in row.index if re.search(value_column_pattern, col)), None
        )

        if value_column and pd.notna(row[value_column]):
            reporting_limit_column_pattern = (
                rf"^\s*Rapportagegrens\s+{parameter}\s+\(.*\)\s*$"
            )
            reporting_limit_column = next(
                (
                    col
                    for col in row.index
                    if re.search(reporting_limit_column_pattern, col)
                ),
                None,
            )

            date_column_pattern = rf"^\s*Analysedatum\s+{parameter}\s+\(.*\)\s*$"
            date_column = next(
                (col for col in row.index if re.search(date_column_pattern, col)), None
            )

            analysis_dict = {
                "parameter": details["parameter_id"],
                "unit": details["unit"],
                "analysisMeasurementValue": row[value_column],
                "reportingLimit": row[reporting_limit_column],
                "qualityControlStatus": "onbeslist",
            }
            analysis = Analysis(**analysis_dict)

            analysis_process_dict = {
                "date": row[date_column],
                "analyticalTechnique": details["analyticalTechnique"],
                "valuationMethod": details["validationMethod"],
                "analyses": [analysis],
            }

            analysis_process = AnalysisProcess(**analysis_process_dict)
            analysis_processes.append(analysis_process)

    return analysis_processes
