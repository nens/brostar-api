import logging

from django.core.management.base import BaseCommand
from django.db.models import Subquery
from django.utils import timezone

from api.models import Organisation, UploadTask

logger = logging.getLogger("general")


class Command(BaseCommand):
    """Temp command that is used during the development of the bulk upload module for GAR."""

    def add_arguments(self, parser):
        """Add kvk as str option to command line."""
        parser.add_argument(
            "--kvk",
            type=str,
            help="KVK number of the organisation to process. If not provided, all organisations are processed. Length should be 8 characters.",
        )
        parser.add_argument(
            "--count",
            type=int,
            help="Number of tasks to keep for each organisation. If not provided, defaults to 1000.",
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        kvk = options.get("kvk")
        count = options.get("count", 1000)
        if kvk:
            organisations = Organisation.objects.filter(kvk_number=kvk)
        else:
            organisations = Organisation.objects.all()

        for org in organisations:
            logger.info(f"{org.name} - {org.kvk_number} - {org.uuid}")

            uploadtasks = UploadTask.objects.filter(data_owner=org)

            if uploadtasks.count() < count:
                logger.info(
                    f"Skipping {org.name} with only {uploadtasks.count()} tasks"
                )
                continue

            ## Get the IDs of the 1000 most recent tasks to keep
            recent_ids = (
                UploadTask.objects.filter(data_owner=org)
                .order_by("-created")
                .values_list("uuid", flat=True)[:count]
            )

            # Now select tasks older than 30 days and NOT in the recent 1000
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            uploadtasks = uploadtasks.exclude(uuid__in=Subquery(recent_ids)).filter(
                created__lt=cutoff_date
            )

            logger.info(f"Deleting {uploadtasks.count()} tasks for {org.name}")
            uploadtasks.delete()
