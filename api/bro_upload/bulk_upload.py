from api import models as api_models
from api.bro_upload import utils


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
        # Step 1; open the files and transform to a pd df
        try:
            fieldwork_df = utils.csv_or_excel_to_df(self.fieldwork_file)
            lab_df = utils.csv_or_excel_to_df(self.lab_file)

            self.bulk_upload_instance.progress = 10.00
            self.bulk_upload_instance.save()
        except Exception as e:
            self.bulk_upload_instance.log = e
            self.bulk_upload_instance.status = "FAILED"
            self.bulk_upload_instance.save()

        print(fieldwork_df)
        print(lab_df)
