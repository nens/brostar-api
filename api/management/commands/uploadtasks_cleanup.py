import logging

from django.core.management.base import BaseCommand
from django.db.models import Subquery
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

            ## Get the IDs of the 1000 most recent tasks to keep
            recent_ids = (
                UploadTask.objects.filter(data_owner=org)
                .order_by("-created")
                .values_list("id", flat=True)[:1000]
            )

            # Now select tasks older than 30 days and NOT in the recent 1000
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            uploadtasks = uploadtasks.exclude(id__in=Subquery(recent_ids)).filter(
                created__lt=cutoff_date
            )

            logger.info(f"Deleting {uploadtasks.count()} tasks for {org.name}")
            uploadtasks.delete()
