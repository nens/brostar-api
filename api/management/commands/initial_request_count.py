import logging

from django.core.management.base import BaseCommand

from api.models import Organisation, UploadTask

logger = logging.getLogger("general")


class Command(BaseCommand):
    """Temp command that is used during the development of the bulk upload module for GAR."""

    def handle(self, *args, **options):
        for org in Organisation.objects.all():
            logger.info(f"{org.name} - {org.kvk_number} - {org.uuid}")

            uploadtasks = UploadTask.objects.filter(data_owner=org, status="COMPLETED")

            if org.request_count < uploadtasks.count():
                org.request_count = uploadtasks.count()
                org.save(update_fields=["request_count"])
                logger.info(
                    f"Updated request_count for {org.name} to {org.request_count}"
                )
