import datetime
import logging
import time
import uuid
import zipfile
from typing import TypeVar

import polars as pl
import pytz

from api import models as api_models
from api.bro_upload.upload_datamodels import (
    TimeValuePair,
)

logger = logging.getLogger("general")


T = TypeVar("T", bound="api_models.UploadFile")
amsterdam_tz = pytz.timezone("Europe/Amsterdam")


def _convert_and_check_df(df: pl.DataFrame) -> pl.DataFrame:
    column_names = df.columns.copy()

    # Columns 0 to 5 should have the following names
    new_names = [
        "bro_id",
        "time",
        "value",
        "statusQualityControl",
        "censorReason",
        "censoringLimitvalue",
    ]

    # Replace up to the number of existing columns
    updated_names = new_names[: len(column_names)]

    # Append the remaining original column names if any
    updated_names.extend(column_names[len(updated_names) :])

    # Set the new column names
    df.columns = updated_names

    df = df.with_columns(
        pl.col("statusQualityControl").str.to_lowercase().alias("statusQualityControl"),
        pl.col("censorReason").str.to_lowercase().alias("censorReason"),
    )

    if df.dtypes[1] == pl.String:
        df = df.with_columns(pl.col("time").str.to_datetime())

    df = df.with_columns(
        pl.when(pl.col("censorReason").str.contains("kleiner"))
        .then(pl.lit("kleinerDanLimietwaarde"))
        .when(pl.col("censorReason").str.contains("groter"))
        .then(pl.lit("groterDanLimietwaarde"))
        .otherwise(pl.col("censorReason"))  # Keeps original value if no match
        .alias("censorReason")  # Overwrites the existing column
    )

    return df


def str_to_datetime(time_value: str | datetime.datetime):
    if isinstance(time_value, datetime.datetime):
        return time_value
    if len(time_value) == 19:
        return _convert_timenaive(time_value)
    elif len(time_value) > 19:
        return _convert_time(time_value)
    else:
        raise ValueError("Incorrect time format.")


def _convert_timenaive(datetime_str: str) -> datetime.datetime:
    if datetime_str.__contains__("T"):
        return datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
    elif datetime_str.__contains__(" "):
        return datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    else:
        raise ValueError("Incorrect time format.")


def _convert_time(datetime_str: str) -> datetime.datetime:
    if datetime_str.__contains__("T"):
        return datetime.datetime.strptime(
            datetime_str, "%Y-%m-%dT%H:%M:%S%z"
        ).astimezone(amsterdam_tz)
    elif datetime_str.__contains__(" "):
        return datetime.datetime.strptime(
            datetime_str, "%Y-%m-%d %H:%M:%S%z"
        ).astimezone(amsterdam_tz)
    else:
        raise ValueError("Incorrect time format.")


class GLDBulkUploader:
    """Handles the upload process for bulk GAR data.

    Takes in the bulk_upload_instance_uuid and the uploaded files.
    Then orchestrates the whole transormation process of the files,
    and the creation of seperate uploadtasks.
    Keeps track of the process in the BulkUpload instance.
    """

    def __init__(
        self,
        bulk_upload_instance_uuid: str,
        measurement_tvp_file_uuid: str,
    ) -> None:
        self.bulk_upload_instance: api_models.BulkUpload = (
            api_models.BulkUpload.objects.get(uuid=bulk_upload_instance_uuid)
        )
        self.bulk_upload_instance.status = "PROCESSING"
        self.bulk_upload_instance.progress = 5
        self.bulk_upload_instance.save()

        self.measurement_tvp_file: api_models.UploadFile = (
            api_models.UploadFile.objects.get(uuid=measurement_tvp_file_uuid)
        )

    def deliver_one_addition(self, bro_id: str, current_measurements_df: pl.DataFrame):
        uploadtask_metadata = self.bulk_upload_instance.metadata
        uploadtask_metadata["broId"] = bro_id
        uploadtask_metadata["requestReference"] += (
            f"{bro_id} {uploadtask_metadata['qualityRegime']}"  # Maybe still change this
        )
        # Convert naive datetime to Dutch timezone (Europe/Amsterdam)
        current_measurements_df = current_measurements_df.with_columns(
            pl.col("time").dt.replace_time_zone(
                "Europe/Amsterdam", ambiguous="earliest", non_existent="null"
            )
        )
        current_measurements_df = (
            current_measurements_df.with_columns(
                pl.col("time").dt.strftime("%Y-%m-%dT%H:%M:%S%:z")
            )
            .sort("time")
            .drop_nulls(subset="time")
        )

        time = current_measurements_df.select("time")
        begin_position = time.item(0, 0)
        end_position = time.item(-1, 0)

        begin_position = str_to_datetime(begin_position)
        end_position = str_to_datetime(end_position)

        validation_status = self.bulk_upload_instance.sourcedocument_data.get(
            "statusQualityControl",
            None,  # should be validationStatus, update in front-end
        )
        if validation_status == "volledigBeoordeeld":
            result_time = end_position + datetime.timedelta(days=1)
        else:
            result_time = end_position

        measurement_tvps: list[dict] = [
            TimeValuePair(**row).model_dump(by_alias=True)
            for row in current_measurements_df.iter_rows(named=True)
        ]

        self.bulk_upload_instance.sourcedocument_data.update(
            {
                "beginPosition": begin_position.date().strftime("%Y-%m-%d"),
                "endPosition": end_position.date().strftime("%Y-%m-%d"),
                "resultTime": result_time.isoformat(sep="T", timespec="seconds"),
            }
        )

        uploadtask_sourcedocument_dict: dict = create_gld_sourcedocs_data(
            measurement_tvps, self.bulk_upload_instance.sourcedocument_data
        )

        upload_task = api_models.UploadTask.objects.create(
            data_owner=self.bulk_upload_instance.data_owner,
            bro_domain="GLD",
            project_number=self.bulk_upload_instance.project_number,
            registration_type="GLD_Addition",
            request_type=self.bulk_upload_instance.request_type,
            metadata=uploadtask_metadata,
            sourcedocument_data=uploadtask_sourcedocument_dict,
        )
        return upload_task

    def process(self) -> None:
        # Step 1: open the files and transform to a pd df
        try:
            all_measurements_df: pl.DataFrame = file_to_df(self.measurement_tvp_file)
            self.bulk_upload_instance.progress = 10.00
            self.bulk_upload_instance.save()
        except Exception as e:
            self.bulk_upload_instance.log = f"Failed to open the files: {e}"
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()
            return

        # Minimal validation / correction of the data
        assert len(all_measurements_df) > 0, "There is no data in the file"

        # Convert to standard format
        all_measurements_df = _convert_and_check_df(all_measurements_df)

        # BRO-Ids
        bro_ids = all_measurements_df.to_series(0).unique()
        progress = 80 / (
            len(bro_ids)
        )  # amount of progress per steps, per bro_id two steps.
        self.bulk_upload_instance.progress = 20.00
        self.bulk_upload_instance.log = f"Nr BroIds: {len(bro_ids)}, Nr of Measurements: {all_measurements_df.count().item(0, 0)}. \n"
        self.bulk_upload_instance.save()
        for bro_id in bro_ids:
            # Step 2: Prepare data for uploadtask per row
            current_measurements_df = all_measurements_df.filter(
                pl.col("bro_id").eq(bro_id)
            )

            upload_task = self.deliver_one_addition(bro_id, current_measurements_df)

            time.sleep(10)
            upload_task.refresh_from_db()

            # Wait while the GLD_Addition is being processed
            if upload_task.status in ["COMPLETED", "FAILED"]:
                self.bulk_upload_instance.progress += progress

            elif upload_task.status == "FAILED":
                self.bulk_upload_instance.status = "FAILED"
                self.bulk_upload_instance.log += f"Upload logging: {upload_task.log}.\n"

            else:
                self.bulk_upload_instance.status = "UNFINISHED"
                self.bulk_upload_instance.log += (
                    "After 10 seconds the upload is not yet finished."
                )

            self.bulk_upload_instance.save()

        if self.bulk_upload_instance.progress >= 100:
            self.bulk_upload_instance.status = "COMPLETED"
            self.bulk_upload_instance.save()


def file_to_df(file_instance: T) -> pl.DataFrame:
    """Reads out csv or excel files and returns a pandas df."""
    filetype = file_instance.file.name.split(".")[-1].lower()
    if filetype == "csv":
        df = pl.read_csv(
            file_instance.file.path,
            has_header=True,
            ignore_errors=False,
            truncate_ragged_lines=True,
        )
    elif filetype in ["xls", "xlsx"]:
        df = pl.read_excel(
            source=file_instance.file.path,
        )
    elif filetype == "zip":
        with zipfile.ZipFile(file_instance.file) as z:
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            xls_files = [f for f in z.namelist() if f.lower().endswith(".xls")]
            xlsx_files = [f for f in z.namelist() if f.lower().endswith(".xlsx")]
            excel_files = xlsx_files.extend(xls_files)
            if not csv_files or not excel_files:
                raise ValueError("No CSV or Excel files found in the zip archive.")

            # Read all CSV files into Polars DataFrames
            dfs = []
            for csv_file in csv_files:
                with z.open(csv_file) as file:
                    dfs.append(
                        pl.read_csv(
                            file,
                            has_header=True,
                            ignore_errors=False,
                            truncate_ragged_lines=True,
                        )
                    )

            for excel in excel_files:
                with z.open(excel) as file:
                    dfs.append(
                        pl.read_csv(
                            file,
                            has_header=True,
                            ignore_errors=False,
                            truncate_ragged_lines=True,
                        )
                    )

            # Combine all DataFrames into one, or return a list if separate DataFrames are desired
            df = pl.concat(dfs)
    else:
        raise ValueError(
            "Unsupported file type. Only CSV and Excel, or ZIP files are supported."
        )
    return df


def _convert_resulttime_to_date(result_time: str) -> str:
    """Converts the result datetime to a date str

    From 2024-01-01T00:00:00Z to 2024-01-01
    """
    return result_time.split("T")[0]


def create_gld_sourcedocs_data(
    measurement_tvps: list[TimeValuePair], sourcedocument_data: dict
) -> dict:
    """Creates a GLDAddition (the pydantic model), based on a row of the merged df of the GLD bulk upload input."""
    observation_id = sourcedocument_data.get("observationId")
    if observation_id in ["", None]:
        observation_id = f"_{uuid.uuid4()}"

    sourcedocument_data.update(
        {
            "observationId": observation_id,
            "observationProcessId": f"_{uuid.uuid4()}",
            "measurementTimeseriesId": f"_{uuid.uuid4()}",
            "date": _convert_resulttime_to_date(
                sourcedocument_data.get("resultTime", "1900-01-01T00:00:00Z")
            ),
            "validationStatus": sourcedocument_data.get(
                "validationStatus",
                sourcedocument_data.get("statusQualityControl", None),
            ),
            "investigatorKvk": sourcedocument_data.get("investigatorKvk", None),
            "observationType": sourcedocument_data.get("observationType", None),
            "evaluationProcedure": sourcedocument_data.get("evaluationProcedure", None),
            "measurementInstrumentType": sourcedocument_data.get(
                "measurementInstrumentType"
            ),
            "processReference": sourcedocument_data.get("processReference", None),
            "beginPosition": sourcedocument_data.get("beginPosition", None),
            "endPosition": sourcedocument_data.get("endPosition", None),
            "resultTime": sourcedocument_data.get("resultTime", None),
            "timeValuePairs": measurement_tvps,
        }
    )

    if sourcedocument_data["airPressureCompensationType"]:
        sourcedocument_data.update(
            {
                "airPressureCompensationType": sourcedocument_data[
                    "airPressureCompensationType"
                ]
            }
        )

    return sourcedocument_data
