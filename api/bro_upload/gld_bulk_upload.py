import logging
import time
from typing import TypeVar

import polars as pl

from api import models as api_models
from api.bro_upload.upload_datamodels import (
    GLDAddition,
    TimeValuePair,
)

logger = logging.getLogger(__name__)


T = TypeVar("T", bound="api_models.UploadFile")


def _convert_and_check_df(df: pl.DataFrame) -> pl.DataFrame:
    # Set columns to the right name
    df.columns = [
        "time",
        "value",
        "statusQualityControl",
        "censorReason",
        "censoringLimitvalue",
    ]
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

    def process(self) -> None:
        # Step 1: open the files and transform to a pd df
        try:
            measurements_df: pl.DataFrame = csv_or_excel_to_df(
                self.measurement_tvp_file
            )
            self.bulk_upload_instance.progress = 10.00
            self.bulk_upload_instance.save()
        except Exception as e:
            self.bulk_upload_instance.log = f"Failed to open the files: {e}"
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()
            return

        # Minimal validation / correction of the data
        assert len(measurements_df) > 0, "There is no data in the file"

        # Convert to standard format
        measurements_df = _convert_and_check_df(measurements_df)
        self.bulk_upload_instance.progress = 20.00
        self.bulk_upload_instance.save()

        # Step 2: Prepare data for uploadtask per row
        uploadtask_metadata = {
            "qualityRegime": self.bulk_upload_instance.metadata["qualityRegime"],
            "requestReference": self.bulk_upload_instance.metadata["requestReference"],
        }

        measurement_tvps: list[TimeValuePair] = [
            TimeValuePair(**row) for row in measurements_df.iter_rows(named=True)
        ]

        uploadtask_sourcedocument_data: GLDAddition = create_gld_sourcedocs_data(
            measurement_tvps, self.bulk_upload_instance.metadata
        )

        uploadtask_sourcedocument_data_dict = (
            uploadtask_sourcedocument_data.model_dump()
        )

        upload_task = api_models.UploadTask.objects.create(
            data_owner=self.bulk_upload_instance.data_owner,
            bro_domain="GLD",
            project_number=self.bulk_upload_instance.project_number,
            registration_type="GLD_Addition",
            request_type="registration",
            metadata=uploadtask_metadata,
            sourcedocument_data=uploadtask_sourcedocument_data_dict,
        )

        self.bulk_upload_instance.progress = 50.00
        self.bulk_upload_instance.save()

        # Wait while the GLD_Addition is being processed
        time.sleep(10)
        upload_task.refresh_from_db()

        if upload_task.status in ["COMPLETED", "FAILED"]:
            self.bulk_upload_instance.progress = 100.00

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


def csv_or_excel_to_df(file_instance: T) -> pl.DataFrame:
    """Reads out csv or excel files and returns a pandas df."""
    filetype = file_instance.file.name.split(".")[-1].lower()

    if filetype == "csv":
        df = pl.read_csv(file_instance.file, has_header=True, ignore_errors=False)
    elif filetype in ["xls", "xlsx"]:
        df = pl.read_excel(file_instance.file, has_header=True, ignore_errors=False)
    else:
        raise ValueError(
            "Unsupported file type. Only CSV and Excel files are supported."
        )
    return df


def _convert_resulttime_to_date(result_time: str) -> str:
    """Converts the result datetime to a date str

    From 2024-01-01T00:00:00Z to 2024-01-01
    """
    return result_time.split("T")[0]


def create_gld_sourcedocs_data(
    measurement_tvps: list[TimeValuePair], metadata: dict[str, any]
) -> GLDAddition:
    """Creates a GLDAddition (the pydantic model), based on a row of the merged df of the GLD bulk upload input."""
    sourcedocs_data_dict = {
        "date": _convert_resulttime_to_date(metadata["resultTime"]),
        "validationStatus": metadata["validationStatus"],
        "investigatorKvk": metadata["investigatorKvk"],
        "observationType": metadata["observationType"],
        "evaluationProcedure": metadata["evaluationProcedure"],
        "measurementInstrumentType": metadata["measurementInstrumentType"],
        "processReference": metadata["processReference"],
        "beginPosition": metadata["beginPosition"],
        "endPosition": metadata["endPosition"],
        "resultTime": metadata["resultTime"],
        "timeValuePairs": measurement_tvps,
    }

    if metadata["airPressureCompensationType"]:
        sourcedocs_data_dict.update(
            {"airPressureCompensationType": metadata["airPressureCompensationType"]}
        )

    sourcedocs_data = GLDAddition(**sourcedocs_data_dict)

    return sourcedocs_data
