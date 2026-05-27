import logging
import os
import re
from collections import defaultdict
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


_REPORTING_LIMIT_COLUMN_RE = re.compile(r"^\s*Rapportagegrens\s+(.+?)\s+\(.*\)\s*$")
_ANALYSIS_DATE_COLUMN_RE = re.compile(r"^\s*Analysedatum\s+(.+?)\s+\(.*\)\s*$")
_MEASUREMENT_VALUE_COLUMN_RE = re.compile(r"^\s*(.+?)\s+\(.*\)\s*$")
_OLD_FORMAT_TRIGGER_HEADERS = {"Zuurstof (mg/l)"}


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", "", str(value)).lower()


def _is_missing_measurement_value(value: object) -> bool:
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "niet bepaald"}:
        return True
    return False


def _resolve_field_measurement_columns(
    row: pd.Series,
) -> tuple[dict[str, str], dict[str, str]]:
    """Map parameter names to source columns, preferring *_field over unsuffixed columns.

    *_lab columns are ignored for field measurements.
    Suffixes are stripped before regex matching to correctly identify parameters.
    """
    columns_by_base_name: dict[str, str] = {}
    normalized_columns: dict[str, str] = {}

    for column in row.index.tolist():
        column_str = str(column)
        if column_str.endswith("_lab"):
            continue

        base_name = column_str[:-6] if column_str.endswith("_field") else column_str
        is_field_column = column_str.endswith("_field")

        if base_name not in columns_by_base_name or is_field_column:
            columns_by_base_name[base_name] = column_str

        normalized_base_name = _normalize_header(base_name)
        if normalized_base_name not in normalized_columns or is_field_column:
            normalized_columns[normalized_base_name] = column_str

    return columns_by_base_name, normalized_columns


def _resolve_lab_analysis_columns(
    row: pd.Series,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Map lab parameter names to source columns, preferring *_lab over unsuffixed.

    *_field columns are ignored for lab analyses to avoid field/lab interference.
    Suffixes are stripped before regex matching to correctly identify parameters.
    """
    value_columns_by_parameter: dict[str, str] = {}
    reporting_limit_columns_by_parameter: dict[str, str] = {}
    analysis_date_columns_by_parameter: dict[str, str] = {}

    for column in row.index:
        column_str = str(column)
        is_lab_column = column_str.endswith("_lab")

        if column_str.endswith("_field"):
            continue

        # Strip suffix before applying regex to correctly identify parameter names
        base_column = column_str[:-4] if is_lab_column else column_str

        reporting_limit_match = _REPORTING_LIMIT_COLUMN_RE.match(base_column)
        if reporting_limit_match:
            parameter = reporting_limit_match.group(1)
            if parameter not in reporting_limit_columns_by_parameter or is_lab_column:
                reporting_limit_columns_by_parameter[parameter] = column_str
            continue

        analysis_date_match = _ANALYSIS_DATE_COLUMN_RE.match(base_column)
        if analysis_date_match:
            parameter = analysis_date_match.group(1)
            if parameter not in analysis_date_columns_by_parameter or is_lab_column:
                analysis_date_columns_by_parameter[parameter] = column_str
            continue

        measurement_match = _MEASUREMENT_VALUE_COLUMN_RE.match(base_column)
        if measurement_match:
            parameter = measurement_match.group(1)
            if parameter not in value_columns_by_parameter or is_lab_column:
                value_columns_by_parameter[parameter] = column_str

    return (
        value_columns_by_parameter,
        reporting_limit_columns_by_parameter,
        analysis_date_columns_by_parameter,
    )


def _build_lab_parameters_by_process() -> dict[
    tuple[str, str], list[tuple[str, int, str]]
]:
    grouped_parameters: dict[tuple[str, str], list[tuple[str, int, str]]] = defaultdict(
        list
    )
    for parameter in config.LAB_PARAMETER_OPTIONS:
        process_key = (parameter["analyticalTechnique"], parameter["validationMethod"])
        grouped_parameters[process_key].append(
            (parameter["code"], parameter["parameter_id"], parameter["unit"])
        )

    return dict(grouped_parameters)


LAB_PARAMETERS_BY_PROCESS = _build_lab_parameters_by_process()


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
            required_fields_field = ["GMW BRO ID", "Datum bemonsterd", "Filternummer"]
            required_fields_lab = ["GMW BRO ID", "Datum bemonsterd", "Filternummer"]
            has_lab = True
            if all(
                field in fieldwork_df.columns for field in required_fields_field
            ) and all(field in lab_df.columns for field in required_fields_lab):
                merged_df = merge_fieldwork_and_lab_dfs(fieldwork_df, lab_df)
            elif all(field in fieldwork_df.columns for field in required_fields_field):
                merged_df = fieldwork_df
                has_lab = False
            else:
                merged_df = lab_df

            logger.info(f"has lab: {has_lab}")

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
            logger.info(
                f"Trimmed the dataframe to the following columns: {trimmed_df.columns.tolist()}"
            )
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
        logger.info(fieldwork_df.columns.tolist())
        logger.info(lab_df.columns.tolist())
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
        left=fieldwork_df,
        right=lab_df,
        left_on=["GMW BRO ID", "Datum bemonsterd", "Filternummer"],
        right_on=["GMW BRO ID", "Datum bemonsterd", "Filternummer"],
        how="inner",
        suffixes=("_field", "_lab"),
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

    # Get columns to exclude for measurements
    columns_to_exclude = REQUIRED_COLUMNS + FIELD_RESEARCH_ITEMS
    existing_columns_to_drop = [col for col in columns_to_exclude if col in row.index]
    measurement_row = row.drop(labels=existing_columns_to_drop)

    # Start with required fields
    field_research_dict = {
        "samplingDateTime": f"{samplingdate}T{sampling_time}:00+00:00",
        "fieldMeasurements": create_gar_field_measurements(measurement_row),
    }

    # Add optional fields only if present in row
    optional_fields = {
        "samplingOperator": metadata.get("samplingOperator"),
        "samplingStandard": metadata.get("samplingStandard"),
        "pumpType": row.get("Pomptype"),
        "primaryColour": row.get("Hoofdkleur"),
        "secondaryColour": row.get("Bijkleur"),
        "colourStrength": row.get("Kleursterkte"),
        "abnormalityInCooling": row.get("Afwijkend gekoeld"),
        "abnormalityInDevice": row.get("Afwijking in meetapparatuur"),
        "pollutedByEngine": row.get("Contaminatie door verbrandingsmotor"),
        "filterAerated": row.get("Filter belucht/ drooggevallen"),
        "groundWaterLevelDroppedTooMuch": row.get("Grondwaterstand > 50 cm verlaagd"),
        "abnormalFilter": row.get("Inline filter afwijkend"),
        "sampleAerated": row.get("Monster belucht"),
        "hoseReused": row.get("Slang hergebruikt"),
        "temperatureDifficultToMeasure": row.get("Temperatuur moeilijk te bepalen"),
    }

    # Only add fields that have non-None values
    for key, value in optional_fields.items():
        if value is not None and value != "":
            # Special handling for pumpType to fix casing
            if key == "pumpType" and isinstance(value, str) and len(value) > 0:
                value = value[0].lower() + value[1:]
            # Special handling for hoseReused to strip whitespace
            elif key == "hoseReused" and isinstance(value, str):
                value = value.strip()

            field_research_dict[key] = value

    field_research = FieldResearch(**field_research_dict)
    return field_research


def create_gar_field_measurements(row: pd.Series) -> list[FieldMeasurement]:
    """For now, the config dict is hardcoded in this function.
    If the options for other organisations differ, this should be redesigned"""
    field_measurement_list = []

    curdir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"column names: {row.index.tolist()}")

    columns_by_base_name, _ = _resolve_field_measurement_columns(row)
    logger.info(f"columns by base name: {columns_by_base_name}")
    has_old_format_trigger = any(
        trigger in columns_by_base_name for trigger in _OLD_FORMAT_TRIGGER_HEADERS
    )

    if has_old_format_trigger:
        logger.info("Using old format parameter config from hardcoded dict.")
        # Old format from Provincie Noord-Brabant
        df = pl.DataFrame(config.FIELD_PARAMETER_OPTIONS)
    else:
        logger.info("Using new format parameter config from CSV file.")
        df = pl.read_csv(os.path.join(curdir, "20260107_GARVarList.csv"), separator=";")
        df = df.rename({"aquocode": "code", "ID": "parameter_id", "eenheid": "unit"})

    for param in columns_by_base_name.keys():
        logger.info(f"Checking parameter '{param}' against config options.")

        parameter = df.filter(pl.col("code") == param).select("parameter_id", "unit")
        if parameter.height == 0:
            logger.warning(
                f"Parameter '{param}' not found in config, skipping this parameter."
            )
            continue

        parameter = parameter.row(0, named=True)
        source_column = columns_by_base_name.get(param)
        value = row[source_column]
        if _is_missing_measurement_value(value):
            logger.warning(
                f"Skipping missing value for parameter '{parameter['parameter_id']}' in column '{source_column}'"
            )
            continue

        parameter_dict = {
            "parameter": parameter["parameter_id"],
            "unit": parameter["unit"],
            "fieldMeasurementValue": value,
            "qualityControlStatus": "onbeslist",
        }
        logger.info(
            f"Created field measurement dict for parameter '{parameter['parameter_id']}': {parameter_dict}"
        )

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


def create_analysis_process(row: pd.Series) -> list[AnalysisProcess]:  # noqa C901
    analysis_processes = []

    (
        value_columns_by_parameter,
        reporting_limit_columns_by_parameter,
        analysis_date_columns_by_parameter,
    ) = _resolve_lab_analysis_columns(row)

    for (technique, method), parameters in LAB_PARAMETERS_BY_PROCESS.items():
        analyses = []
        process_date = None

        for parameter, parameter_id, unit in parameters:
            value_column = value_columns_by_parameter.get(parameter)
            if not value_column:
                continue

            date_column = analysis_date_columns_by_parameter.get(parameter)
            if not date_column:
                continue

            date_value = row.get(date_column)
            if pd.isna(date_value) or date_value == "":
                continue

            value = row[value_column]
            reporting_limit_column = reporting_limit_columns_by_parameter.get(parameter)
            reporting_limit = (
                row[reporting_limit_column] if reporting_limit_column else None
            )

            if pd.api.types.is_number(value) and pd.notna(value):
                analysis_dict = {
                    "parameter": parameter_id,
                    "unit": unit,
                    "analysisMeasurementValue": value,
                    "reportingLimit": reporting_limit,
                    "qualityControlStatus": "onbeslist",
                }
                analyses.append(Analysis(**analysis_dict))
                if process_date is None:
                    process_date = date_value
            elif value in ["<", "GT"]:
                analysis_dict = {
                    "parameter": parameter_id,
                    "unit": unit,
                    "reportingLimit": reporting_limit,
                    "limitSymbol": "LT" if value == "<" else value,
                    "qualityControlStatus": "onbeslist",
                }
                analyses.append(Analysis(**analysis_dict))
                if process_date is None:
                    process_date = date_value

        if analyses and process_date is not None:
            analysis_process_dict = {
                "date": process_date,
                "analyticalTechnique": technique,
                "valuationMethod": method,
                "analyses": analyses,
            }
            analysis_processes.append(AnalysisProcess(**analysis_process_dict))

    return analysis_processes
