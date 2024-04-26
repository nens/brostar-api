from typing import TypeVar

import pandas as pd

from api import models as api_models

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

            print(merged_df)

        except Exception as e:
            self.bulk_upload_instance.log = e
            self.bulk_upload_instance.status = "FAILED"
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
