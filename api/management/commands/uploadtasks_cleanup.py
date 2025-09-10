import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Organisation, UploadTask

logger = logging.getLogger("general")


class Command(BaseCommand):
    """Temp command that is used during the development of the bulk upload module for GAR."""

    def handle(self, *args, **options):
        for org in Organisation.objects.all():
            logger.info(f"{org.name} - {org.kvk_number} - {org.uuid}")

            uploadtasks = UploadTask.objects.filter(data_owner=org)

            if uploadtasks.count() < 1000:
                logger.info(
                    f"Skipping {org.name} with only {uploadtasks.count()} tasks"
                )
                continue

            # Order by created date, newest first. At least keep the 1000 most recent tasks, delete anything older than 30 days that exceed 1000 tasks

            uploadtasks = uploadtasks.order_by("-created")[1000:]
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            uploadtasks = uploadtasks.filter(created__lt=cutoff_date)
            logger.info(f"Deleting {uploadtasks.count()} tasks for {org.name}")
            uploadtasks.delete()
