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
        ...
