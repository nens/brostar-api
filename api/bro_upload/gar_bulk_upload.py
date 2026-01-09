import logging
import os
import re
from typing import TypeVar

import pandas as pd
import polars as pl

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

logger = logging.getLogger("general")


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
        fieldwork_upload_file_uuid: str | None = None,
        lab_upload_file_uuid: str | None = None,
    ) -> None:
        self.bulk_upload_instance: api_models.BulkUpload = (
            api_models.BulkUpload.objects.get(uuid=bulk_upload_instance_uuid)
        )
        self.bulk_upload_instance.status = "PROCESSING"
        self.bulk_upload_instance.save()

        if fieldwork_upload_file_uuid:
            self.fieldwork_file: api_models.UploadFile = (
                api_models.UploadFile.objects.get(uuid=fieldwork_upload_file_uuid)
            )
        else:
            self.fieldwork_file = None

        if lab_upload_file_uuid:
            self.lab_file: api_models.UploadFile = api_models.UploadFile.objects.get(
                uuid=lab_upload_file_uuid
            )
        else:
            self.lab_file = None

    def _initialize_dataframes(self) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
        try:
            if self.fieldwork_file and self.fieldwork_file.file:
                fieldwork_df = csv_or_excel_to_df(self.fieldwork_file)
            else:
                fieldwork_df = pd.DataFrame()
            if self.lab_file and self.lab_file.file:
                lab_df = csv_or_excel_to_df(self.lab_file)
            else:
                lab_df = pd.DataFrame()

            self.bulk_upload_instance.progress = 10.00
            self.bulk_upload_instance.save()
            return fieldwork_df, lab_df
        except Exception as e:
            self.bulk_upload_instance.log = f"Failed to open the files: {e}"
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()
            return None, None

    def _process_fieldwork_and_lab_dfs(
        self, fieldwork_df: pd.DataFrame, lab_df: pd.DataFrame
    ) -> pd.DataFrame:
        try:
            # Rename headers
            required_fields = ["GMW BRO ID", "Datum bemonsterd", "Filternummer"]
            has_lab = True
            if all(field in fieldwork_df.columns for field in required_fields) and all(
                field in lab_df.columns for field in required_fields
            ):
                merged_df = merge_fieldwork_and_lab_dfs(fieldwork_df, lab_df)
            elif all(field in fieldwork_df.columns for field in required_fields):
                merged_df = fieldwork_df
                has_lab = False
            else:
                merged_df = lab_df

            fieldwork_df_rename_dict = {
                "GMW BRO ID": "bro_id",
                "Datum bemonsterd": "date",
                "Filternummer": "filter_num",
            }
            merged_df = rename_df_columns(merged_df, fieldwork_df_rename_dict)
            field_columns_exclude = [
                "NITG",
                "Putcode",
                "coördinaat",
                "Bijzonderheden",
                "MeetpuntId",
                "Projectcode lab",
                "Monsternummer lab",
            ]
            trimmed_df = remove_df_columns(merged_df, field_columns_exclude)

            # Pandas DF: create new column meetronde, which should only have the year of datum bemonsterd, as a string
            trimmed_df["Meetronde"] = trimmed_df["date"].dt.year.astype(str)

            assert len(trimmed_df) > 0, (
                "The combination of the lab and field files gave no resulting possible GARs"
            )

            self.bulk_upload_instance.progress = 20.00
            self.bulk_upload_instance.save(update_fields=["progress"])
            return trimmed_df, has_lab
        except Exception as e:
            logger.info(f"Failed to process GAR files: {e}")
            self.bulk_upload_instance.log = f"Failed to transform the files: {e}"
            self.bulk_upload_instance.progress = 20.00
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save(update_fields=["log", "progress", "status"])
            return None, None

    def process(self) -> None:
        # Step 1: open the files and transform to a pd df
        fieldwork_df, lab_df = self._initialize_dataframes()
        if fieldwork_df is None and lab_df is None:
            return

        logger.info("Initialized the dataframes.")

        # Step 2: transform the pandas files to a useable format
        trimmed_df, has_lab = self._process_fieldwork_and_lab_dfs(fieldwork_df, lab_df)
        if trimmed_df is None:
            return

        logger.info(f"Processed the dataframes. Has lab: {has_lab}")

        # Step 3: Prepare data for uploadtask per row
        uploadtask_metadata = {
            "qualityRegime": self.bulk_upload_instance.metadata["qualityRegime"],
            "deliveryAccountableParty": self.bulk_upload_instance.metadata[
                "deliveryAccountableParty"
            ],
            "requestReference": self.bulk_upload_instance.metadata["requestReference"],
        }

        progress_per_row = round((80 / len(trimmed_df)), 2)

        for _, row in trimmed_df.iterrows():
            logger.info(f"Processing GAR row: {row}")
            try:
                uploadtask_sourcedocument_data: GAR = create_gar_sourcesdocs_data(
                    row, self.bulk_upload_instance.metadata, has_lab
                )

                uploadtask_sourcedocument_data_dict = (
                    uploadtask_sourcedocument_data.model_dump(by_alias=True)
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
                self.bulk_upload_instance.save(update_fields=["progress"])
            except Exception as e:
                logger.info(f"Failed to upload GAR ({row.bro_id}) in bulk upload: {e}")
                self.bulk_upload_instance.progress += progress_per_row
                self.bulk_upload_instance.save(update_fields=["progress"])

        self.bulk_upload_instance.progress = 100.00
        self.bulk_upload_instance.status = "FINISHED"
        self.bulk_upload_instance.save(update_fields=["progress", "status"])


def csv_or_excel_to_df(file_instance: T) -> pd.DataFrame:
    """Reads out csv or excel files and returns a pandas df."""
    # Get the file extension more robustly
    _, ext = os.path.splitext(file_instance.file.name)
    filetype = ext.lstrip(".").lower().strip()

    logger.info(f"Reading file {file_instance.file.name} of type '{filetype}'")

    # Ensure file pointer is at the beginning
    if hasattr(file_instance.file, "seek"):
        file_instance.file.seek(0)
    if filetype == "csv":
        df = pd.read_csv(file_instance.file)
    elif filetype in ["xls", "xlsx"]:
        df = pd.read_excel(file_instance.file)
    else:
        raise ValueError(
            "Unsupported file type. Only CSV and Excel files are supported."
        )
    logger.info(f"For fileinstance {file_instance}, imported the following:")
    logger.info(df.head())
    return df


def rename_df_columns(df: pd.DataFrame, rename_dict: dict[str, str]) -> pd.DataFrame:
    return df.rename(columns=rename_dict)


def merge_fieldwork_and_lab_dfs(
    fieldwork_df: pd.DataFrame, lab_df: pd.DataFrame
) -> pd.DataFrame:
    """Merges the files into 1 big df.

    This filters out the location/date combinations that are only present in 1 file."""
    return pd.merge(
        fieldwork_df,
        lab_df,
        on=["GMW BRO ID", "Datum bemonsterd", "Filternummer"],
        how="inner",
    )


def remove_df_columns(
    df: pd.DataFrame, substrings_to_exclude: list[str]
) -> pd.DataFrame:
    substring_pattern = "|".join(substrings_to_exclude)
    return df.loc[:, ~df.columns.str.contains(substring_pattern)]


def create_gar_sourcesdocs_data(
    row: pd.Series, metadata: dict[str, any], has_lab: bool
) -> GAR:
    """Creates a GAR (the pydantic model), based on a row of the merged df of the GAR bulk upload input."""
    sourcedocs_data_dict = {
        "objectIdAccountableParty": f"{row['bro_id']}-{int(row['filter_num']):03d}-{int(row['Meetronde'])}",
        "qualityControlMethod": metadata["qualityControlMethod"],
        "gmwBroId": row["bro_id"],
        "tubeNumber": row["filter_num"],
        "fieldResearch": create_gar_field_research(row, metadata),
        "laboratoryAnalyses": create_gar_lab_analysis(row, metadata) if has_lab else [],
    }

    if "groundwaterMonitoringNets" in metadata:
        sourcedocs_data_dict["groundwaterMonitoringNets"] = metadata[
            "groundwaterMonitoringNets"
        ]

    sourcedocs_data = GAR(**sourcedocs_data_dict)
    return sourcedocs_data


def validate_time_format(time_str: str) -> bool:
    """Validate and normalize time string in HH:MM or H:MM format."""
    # Check basic format
    if not re.match(r"^\d{1,2}:\d{2}$", time_str):
        raise ValueError(f"Invalid time format: '{time_str}'. Expected HH:MM or H:MM")

    # Parse and validate actual time values
    try:
        hours, minutes = map(int, time_str.split(":"))

        # Validate ranges
        if not (0 <= hours <= 23):
            raise ValueError(f"Hours must be 0-23, got {hours}")
        if not (0 <= minutes <= 59):
            raise ValueError(f"Minutes must be 0-59, got {minutes}")

        # Normalize to HH:MM format
        return f"{hours:02d}:{minutes:02d}"

    except ValueError as e:
        raise ValueError(f"Invalid time: '{time_str}'. {str(e)}")


REQUIRED_COLUMNS = [
    "GMW BRO ID",
    "Filternummer",
    "Datum bemonsterd",
    "Tijdstip bemonsterd",
]

FIELD_RESEARCH_ITEMS = [
    "Pomptype",
    "Grondwaterstand > 50 cm verlaagd",
    "Filter belucht/ drooggevallen",
    "Slang hergebruikt",
    "Monster belucht",
    "Contaminatie door verbrandingsmotor",
    "Afwijking in meetapparatuur",
    "Hoofdkleur",
    "Bijkleur",
    "Kleursterkte",
    "Temperatuur moeilijk te bepalen",
    "Afwijkend gekoeld",
    "Inline filter afwijkend",
]


def create_gar_field_research(
    row: pd.Series, metadata: dict[str, any]
) -> FieldResearch:
    """Creates the FieldResearch pydantic model based on a row of the merged df of the GAR bulk upload input."""
    samplingdate = row["date"].strftime("%Y-%m-%d")
    sampling_time = row.get("Tijd bemonsterd", "12:00")
    # Check if time is in HH:MM format
    try:
        sampling_time = validate_time_format(sampling_time)
    except ValueError as e:
        print(f"Error: {e}")
        sampling_time = "12:00"  # Or handle the error appropriately

    # Ensure all required field research items are present
    # If any field has an empty string, set it to "onbekend"
    row.update(
        {
            item: "onbekend"
            for item in FIELD_RESEARCH_ITEMS
            if item not in row or row[item] == ""
        }
    )

    # potential measurement columns are everything except the required columns and field research items
    # Get columns to exclude
    columns_to_exclude = REQUIRED_COLUMNS + FIELD_RESEARCH_ITEMS

    # Only drop columns that actually exist in the row
    existing_columns_to_drop = [col for col in columns_to_exclude if col in row.index]
    measurement_row = row.drop(labels=existing_columns_to_drop)

    field_research_dict = {
        "samplingDateTime": f"{samplingdate}T{sampling_time}:00+00:00",
        "samplingOperator": metadata["samplingOperator"],
        "samplingStandard": metadata["samplingStandard"],
        "pumpType": row["Pomptype"][0].lower()
        + row["Pomptype"][1:],  # fixes upper cases
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
        "hoseReused": row["Slang hergebruikt"].strip(),
        "temperatureDifficultToMeasure": row["Temperatuur moeilijk te bepalen"],
        "fieldMeasurements": create_gar_field_measurements(measurement_row),
    }

    field_research = FieldResearch(**field_research_dict)

    return field_research


def create_gar_field_measurements(row: pd.Series) -> list[FieldMeasurement]:
    """For now, the config dict is hardcoded in this function.
    If the options for other organisations differ, this should be redesigned"""
    field_measurement_list = []

    curdir = os.path.dirname(os.path.abspath(__file__))
    df = pl.read_csv(os.path.join(curdir, "20260107_GARVarList.csv"), separator=";")

    for column in row:
        if column in df["aquocode"].to_list() and row[column] != "niet bepaald":
            parameter_details = df.filter(pl.col("aquocode") == column).to_dicts()[0]
            parameter = column
            parameter_dict = {
                "parameter": parameter_details["ID"],
                "unit": parameter_details["eenheid"],
                "fieldMeasurementValue": row[parameter],
                "qualityControlStatus": "onbeslist",
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
