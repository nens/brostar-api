import datetime
import logging
import time
import zipfile
from typing import TypeVar

import polars as pl

from api import models as api_models
from api.bro_upload.upload_datamodels import (
    TimeValuePair,
)

logger = logging.getLogger(__name__)


T = TypeVar("T", bound="api_models.UploadFile")


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
    return df


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
        bro_username: str,
        bro_password: str,
    ) -> None:
        self.bulk_upload_instance: api_models.BulkUpload = (
            api_models.BulkUpload.objects.get(uuid=bulk_upload_instance_uuid)
        )
        self.bulk_upload_instance.status = "PROCESSING"
        self.bulk_upload_instance.save()

        self.measurement_tvp_file: api_models.UploadFile = (
            api_models.UploadFile.objects.get(uuid=measurement_tvp_file_uuid)
        )

        self.bro_username: str = bro_username
        self.bro_password: str = bro_password

    def deliver_one_addition(self, bro_id: str, current_measurements_df: pl.DataFrame):
        uploadtask_metadata = self.bulk_upload_instance.metadata
        uploadtask_metadata["broId"] = bro_id
        uploadtask_metadata["requestReference"] += (
            f"{bro_id} {uploadtask_metadata['qualityRegime']}"  # Maybe still change this
        )

        current_measurements_df = current_measurements_df.sort("time")
        logger.warning(current_measurements_df)

        time = current_measurements_df.select("time")
        begin_position = time.item(0, 0)
        end_position = time.item(-1, 0)

        if len(begin_position) == 19:
            begin_position = datetime.datetime.strptime(
                begin_position, "%Y-%m-%dT%H:%M:%S"
            )
        elif len(begin_position) > 19:
            begin_position = datetime.datetime.strptime(
                begin_position, "%Y-%m-%dT%H:%M:%S%z"
            ).astimezone(datetime.UTC)
        else:
            raise ValueError(
                f"Time has incorrect format, use: YYYY-mm-ddTHH:MM:SS+-Timezone. Not: {begin_position}."
            )

        if len(end_position) == 19:
            end_position = datetime.datetime.strptime(end_position, "%Y-%m-%dT%H:%M:%S")
        elif len(end_position) > 19:
            end_position = datetime.datetime.strptime(
                end_position, "%Y-%m-%dT%H:%M:%S%z"
            ).astimezone(datetime.UTC)
        else:
            raise ValueError(
                f"Time has incorrect format, use: YYYY-mm-ddTHH:MM:SS+-Timezone. Not: {end_position}."
            )

        validation_status = self.bulk_upload_instance.sourcedocument_data.get(
            "validationStatus", None
        )
        if validation_status == "volledigBeoordeeld":
            result_time = end_position + datetime.timedelta(days=1)
        else:
            result_time = end_position

        measurement_tvps: list[dict] = [
            TimeValuePair(**row).model_dump()
            for row in current_measurements_df.iter_rows(named=True)
        ]

        self.bulk_upload_instance.sourcedocument_data.update(
            {
                "beginPosition": begin_position.isoformat(sep="T", timespec="seconds"),
                "endPosition": end_position.isoformat(sep="T", timespec="seconds"),
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
            request_type="registration",
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
        self.bulk_upload_instance.progress = 20.00
        self.bulk_upload_instance.save()

        # BRO-Ids
        bro_ids = all_measurements_df.to_series(0).unique()
        progress = 80 / (
            len(bro_ids) * 2
        )  # amount of progress per steps, per bro_id two steps.
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

            if upload_task.status == "COMPLETED":
                self.bulk_upload_instance.status = "FINISHED"

            elif upload_task.status == "FAILED":
                self.bulk_upload_instance.status = "FAILED"
                self.bulk_upload_instance.log += f"Upload logging: {upload_task.log}."

            else:
                self.bulk_upload_instance.status = "UNFINISHED"
                self.bulk_upload_instance.log += (
                    "After 10 seconds the upload is not yet finished."
                )

        self.bulk_upload_instance.save()


def file_to_df(file_instance: T) -> pl.DataFrame:
    """Reads out csv or excel files and returns a pandas df."""
    filetype = file_instance.file.name.split(".")[-1].lower()

    if filetype == "csv":
        df = pl.read_csv(
            file_instance.file,
            has_header=True,
            ignore_errors=False,
            truncate_ragged_lines=True,
        )
    elif filetype in ["xls", "xlsx"]:
        df = pl.read_excel(
            file_instance.file,
            has_header=True,
        )
    elif filetype == "zip":
        with zipfile.ZipFile(file_instance.file) as z:
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            if not csv_files:
                raise ValueError("No CSV files found in the zip archive.")

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
    sourcedocument_data.update(
        {
            "date": _convert_resulttime_to_date(sourcedocument_data["resultTime"]),
            "validationStatus": sourcedocument_data.get("validationStatus", None),
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
