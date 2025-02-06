from django.core.management.base import BaseCommand

from api.bro_upload.gar_bulk_upload import GARBulkUploader


class Command(BaseCommand):
    """Temp command that is used during the development of the bulk upload module for GAR."""

    def handle(self, *args, **options):
        uploader = GARBulkUploader(
            bulk_upload_instance_uuid="ba8c6367-c2d6-45c5-adb1-07bd7456af38",
            fieldwork_upload_file_uuid="a79e9152-e332-4fb5-82f7-f43e696c691d",
            lab_upload_file_uuid="3f96e2ce-e7e6-490b-8a24-baf3de487548",
            bro_username="",
            bro_password="",
        )

        uploader.process()
