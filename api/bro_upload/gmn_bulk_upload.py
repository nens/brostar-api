import logging
import zipfile
from datetime import datetime
from typing import TypeVar

import polars as pl

from api import models as api_models

logger = logging.getLogger("general")


T = TypeVar("T", bound="api_models.UploadFile")


def convert_eventdate_column(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert the eventDate column (5th column) from Excel integer format to YYYY-MM-DD date format.

    Args:
        df: Polars DataFrame with eventDate column

    Returns:
        DataFrame with eventDate converted to proper date type (YYYY-MM-DD)
    """
    EXCEL_EPOCH = datetime(1899, 12, 30)

    # Check if eventDate exists and needs conversion
    if "eventDate" not in df.columns:
        raise ValueError("Column 'eventDate' not found in DataFrame")

    # Check if it's already a date/datetime type
    if df["eventDate"].dtype in [pl.Date, pl.Datetime]:
        # Already converted, just ensure it's Date type for YYYY-MM-DD format
        return df.with_columns(pl.col("eventDate").cast(pl.Date))

    # Check if it's numeric (Excel integer/float format)
    if df["eventDate"].dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]:
        # Convert from Excel integer to date
        df = df.with_columns(
            (pl.lit(EXCEL_EPOCH) + pl.duration(days=pl.col("eventDate").cast(pl.Int64)))
            .cast(pl.Date)  # Cast to Date for YYYY-MM-DD format
            .alias("eventDate")
        )
        df = df.with_columns(
            pl.col("eventDate")
            .dt.to_string("%Y-%m-%d")
            .alias("eventDate")  # Convert to string format YYYY-MM-DD
        )
        return df

    # If it's string type, try to parse it
    if df["eventDate"].dtype == pl.String:
        df = df.with_columns(
            pl.col("eventDate").str.to_date().alias("eventDate")
        )  # Determine format based on content
        df = df.with_columns(
            pl.col("eventDate")
            .dt.to_string("%Y-%m-%d")
            .alias("eventDate")  # Convert to string format YYYY-MM-DD
        )
        return df

    # If we get here, unsupported type
    raise ValueError(f"Unsupported dtype for eventDate: {df['eventDate'].dtype}")


def _convert_and_check_df(df: pl.DataFrame) -> pl.DataFrame:
    column_names = df.columns.copy()

    # Columns 0 to 5 should have the following names
    new_names = [
        "eventType",
        "measuringPointCode",
        "gmwBroId",
        "tubeNumber",
        "eventDate",
    ]

    # Replace up to the number of existing columns
    updated_names = new_names[: len(column_names)]

    # Append the remaining original column names if any
    updated_names.extend(column_names[len(updated_names) :])

    # Set the new column names
    df.columns = updated_names

    # Convert eventDate column
    df = convert_eventdate_column(df)

    return df


def determine_event_type(event_type: str) -> str:
    """Take a bunch of letters and tries to distinguish any of the 3 options (small LLM?)"""
    lowered_event = event_type.lower()
    mp = ["add", "toevoegen", "meetpunt"]
    mpe = ["end", "eind", "date", "datum"]
    tfr = ["reference", "referentie", "verwijzing", "tube", "buis"]

    if any(keyword in lowered_event for keyword in mpe):
        return "GMN_MeasuringPointEndDate"
    elif any(keyword in lowered_event for keyword in tfr):
        return "GMN_TubeReference"
    elif any(keyword in lowered_event for keyword in mp):
        return "GMN_MeasuringPoint"
    else:
        raise ValueError("Niet in staat het bericht-type te achterhalen: ")


def check_date_string(date_string: str) -> str:
    """Make sure the date is correctly formatted."""
    date_parts = date_string.split("-")
    for index, part in enumerate(date_parts):
        if index > 2:
            raise ValueError(
                f"Datum moet voldoen aan YYYY-MM-DD formaat. {date_string}"
            )
        elif index == 0 and not (len(part) == 4 or len(part) == 0):
            raise ValueError(
                f"Datum moet voldoen aan YYYY-MM-DD formaat. {date_string}"
            )
        elif index > 0 and len(part) != 2:
            raise ValueError(
                f"Datum moet voldoen aan YYYY-MM-DD formaat. {date_string}"
            )

    return date_string


class GMNBulkUploader:
    """Handles the upload process for bulk GMN data.

    Takes in the bulk_upload_instance_uuid and the uploaded files.
    Then orchestrates the whole transormation process of the files,
    and the creation of seperate uploadtasks.
    Keeps track of the process in the BulkUpload instance.
    """

    def __init__(
        self,
        bulk_upload_instance_uuid: str,
        measuringpoint_file_uuid: str,
    ) -> None:
        self.bulk_upload_instance: api_models.BulkUpload = (
            api_models.BulkUpload.objects.get(uuid=bulk_upload_instance_uuid)
        )
        self.bulk_upload_instance.status = "PROCESSING"
        self.bulk_upload_instance.save()

        self.measuringpoint_file_uuid: api_models.UploadFile = (
            api_models.UploadFile.objects.get(uuid=measuringpoint_file_uuid)
        )

    def deliver_one_uploadtask(
        self,
        event_type: str,
        measuring_point_code: str,
        gmw_bro_id: str,
        tube_number: int,
        event_date: str,
    ):
        registration_type = determine_event_type(event_type)
        uploadtask_metadata = self.bulk_upload_instance.metadata
        uploadtask_metadata["requestReference"] = (
            f"{event_type}_{measuring_point_code}_{event_date}"  # Maybe still change this
        )

        uploadtask_sourcedocument_dict = {
            "eventDate": event_date,
            "measuringPointCode": measuring_point_code,
            "broId": gmw_bro_id,
            "tubeNumber": tube_number,
        }

        upload_task = api_models.UploadTask.objects.create(
            data_owner=self.bulk_upload_instance.data_owner,
            bro_domain="GMN",
            project_number=self.bulk_upload_instance.project_number,
            registration_type=registration_type,
            request_type="registration",
            metadata=uploadtask_metadata,
            sourcedocument_data=uploadtask_sourcedocument_dict,
        )
        return upload_task

    def process(self) -> None:
        # Step 1: open the files and transform to a pd df
        try:
            monitoringnet_adjustments_df: pl.DataFrame = file_to_df(
                self.measuringpoint_file_uuid
            )
            self.bulk_upload_instance.progress = 10.00
            self.bulk_upload_instance.save()
        except Exception as e:
            self.bulk_upload_instance.log = f"Failed to open the files: {e}"
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()
            return

        # Minimal validation / correction of the data
        assert len(monitoringnet_adjustments_df) > 0, "There is no data in the file"

        # Convert to standard format
        monitoringnet_adjustments_df = _convert_and_check_df(
            monitoringnet_adjustments_df
        )
        self.bulk_upload_instance.progress = 20.00
        self.bulk_upload_instance.save()
        print(monitoringnet_adjustments_df)
        # BRO-Ids
        nr_of_rows = len(monitoringnet_adjustments_df.rows())
        progress = (
            80 / nr_of_rows
        )  # amount of progress per steps, per bro_id two steps.

        upload_tasks = []

        # Convert

        for row in monitoringnet_adjustments_df.iter_rows(named=True):
            event_date = (
                check_date_string(row["eventDate"])
                if isinstance(row["eventDate"], str)
                else row["eventDate"].isoformat()
            )
            upload_task = self.deliver_one_uploadtask(
                event_type=row["eventType"],
                measuring_point_code=row["measuringPointCode"],
                gmw_bro_id=row["gmwBroId"],
                tube_number=row["tubeNumber"],
                event_date=event_date,  # Should accept multiple formats and convert this to YYYY-MM-DD
            )
            upload_tasks.append(upload_task)
            self.bulk_upload_instance.progress += progress / 2
            self.bulk_upload_instance.log = f"Created {len(upload_tasks)} upload tasks."
            self.bulk_upload_instance.save()

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
            file_instance.file.path,
            has_header=True,
        )
    elif filetype == "zip":
        with zipfile.ZipFile(file_instance.file) as z:
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            xls_files = [f for f in z.namelist() if f.lower().endswith(".xls")]
            xlsx_files = [f for f in z.namelist() if f.lower().endswith(".xlsx")]
            excel_files = xlsx_files + xls_files
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
                        pl.read_excel(
                            file,
                            has_header=True,
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
